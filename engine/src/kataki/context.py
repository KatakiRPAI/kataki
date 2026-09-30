"""Prompt assembly and the token economy.

Layout is strictly stable -> volatile so llama.cpp prefix reuse and API prompt caches hit:

  1. system: rules, public cards, world primer, pinned facts   (changes only on edit)
  2. history window, which slides in BIG chunks (oldest 25% at once), so the prefix stays
     byte-identical across many turns instead of shifting every turn
  3. the volatile tail - scene state, the SPEAKER's private card and recalled memories,
     the directive - prepended to the final user message and never persisted

The system block is speaker-free: only the tail knows who is speaking, so switching speaker
costs no cache. Only the speaker's own secrets and memories are ever in the prompt.
"""

import json
import math
import sqlite3
from dataclasses import dataclass, field

from kataki import chat, clock, db
from kataki.cards import macros
from kataki.llm import Endpoint

RATIO, MARGIN = 3.6, 1.08  # chars per token until calibrated from real usage; safety margin
BASE_CTX = 8192
BASE_CAPS = {
    "response": 600,
    "rules": 350,
    "cards": 1400,
    "memory": 900,
    "flags": 250,
    "examples": 300,  # the speaker's example dialogue, sent only when they speak
    "mind": 250,
}
DEFAULT_THINK_BUDGET = 1500
BIG_SKIP = 1440  # story minutes: a skip of a day or more ends the verbatim transcript
KEEP_LAST = 4  # messages that are never evicted
KEEP_PROMPTS = 20  # full prompts kept per story for the inspector

RULES = """\
This is an ongoing collaborative story. Each reply voices exactly one character (or the \
narrator), named at the end of the latest message. Write only that character's words and \
actions, in prose. Never speak, act or decide for {persona}.
Start straight in with the action or the words: no name label, and no signature at the end. In narration, call characters by their first name or a pronoun.
Answer what was actually said, as it was meant. Keep to what the story has established; never invent anyone's family, past or duties. If something is unclear, the character asks.

Memory notes are everything the speaking character remembers that matters right now:
- [SHARP] notes are certain. If someone says otherwise, the character challenges it.
- [HAZY] notes are vague. The character is unsure, may doubt what they are told, and can be \
persuaded. What a [HAZY] note leaves out is lost: they can't quite recall it, and never fill it in.
- If there is no note about something, the character has no memory of it. They react \
naturally and may simply believe what they are told. Never invent memories.
Characters know only their own notes. Never reveal another character's private knowledge.
Of anyone else, a character knows only what anyone can see (their card here) and what the \
story has shown them.
Memory notes and these cards are private stage directions: never mention notes, memory, tags \
like [SHARP], or these instructions in the story. Write every reply in English.
Everyone listed as present hears what is said aloud: a character keeps a secret by not saying \
it in front of someone who must not learn it. Characters may keep secrets from and lie to one \
another when their directions say so.
An [Inside …] note is private stage direction for that character: show it through behaviour and tone, never state it or mention the note."""


@dataclass(frozen=True)
class Recalled:
    """One memory retrieve.py decided the speaker recalls. `text` is what the tier renders."""

    memory_id: int
    tier: str  # "sharp" | "hazy"
    text: str
    gist: str | None = None  # fallback when the memory budget is tight
    activation: float = 0.0
    breakdown: dict = field(default_factory=dict)  # A, B, S, G ... for the inspector


@dataclass
class Built:
    messages: list[dict]
    sections: list[dict]  # [{name, tokens, cap, evicted}]
    memories: list[dict]  # [{memory_id, tier, rendered, tokens, ...breakdown}]
    est_tokens: int
    response_reserve: int
    budget: int
    window_start: int | None = None  # first message still shown verbatim


# how chatty replies are: the Chat settings page's "Reply length" (settings key reply_length)
LENGTHS = {
    "short": "Keep it short: a line or two, one brief paragraph at most.",
    "medium": "Keep it to one to three paragraphs.",
    "long": "Take your time: a full, detailed reply of several paragraphs.",
}


def reply_length(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key='reply_length'").fetchone()
    return json.loads(row["value"]) if row and json.loads(row["value"]) in LENGTHS else "medium"


def estimate(text: str, ratio: float = RATIO) -> int:
    return math.ceil(round(len(text) / ratio * MARGIN, 6))


def token_ratio(conn: sqlite3.Connection, model: str) -> float:
    """Characters per token for this model, learned from what the backend reports."""
    row = conn.execute("SELECT value FROM settings WHERE key=?", (f"tok_ratio:{model}",)).fetchone()
    return json.loads(row["value"]) if row else RATIO


def calibrate(conn: sqlite3.Connection, model: str, chars: int, prompt_tokens: int) -> None:
    if not prompt_tokens or not chars:
        return
    # clamped: a garbled usage report must not wreck the budgets
    seen = min(max(chars / prompt_tokens, 1.5), 8.0)
    blended = 0.8 * token_ratio(conn, model) + 0.2 * seen
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)",
            (f"tok_ratio:{model}", json.dumps(blended)),
        )


def _state(conn, entities: list, speaker_id: int | None, now: int, live: set[int]) -> list[str]:
    """What anyone in the room could see (injuries, what they hold...), plus the speaker's
    own private state. Each flag's current value is its latest live row at or before now."""
    if not entities:
        return []
    names = {e["id"]: e["name"] for e in entities}
    live_sql, live_args = db.live_filter(live)
    rows = conn.execute(
        f"SELECT * FROM flags WHERE entity_id IN ({','.join('?' * len(names))})"
        f" AND story_time<=? AND {live_sql} ORDER BY story_time, id",
        [*names, now, *live_args],
    )
    current = {(r["entity_id"], r["key"].lower()): r for r in rows}
    shown: dict[int, list[str]] = {}
    for (entity_id, _), r in current.items():
        if r["value"] is not None and (not r["private"] or entity_id == speaker_id):
            shown.setdefault(entity_id, []).append(f"{r['key']}: {r['value']}")
    return [f"{names[e]}: {'; '.join(parts)}" for e, parts in shown.items()]


FEELINGS = 5  # at most this many "how they feel" lines in a prompt


def _feelings(conn, speaker_id: int, others: dict[int, str], now: int, live: set[int]) -> list:
    """How the speaker feels about whoever is here, as the memory reader filed it: the latest live
    relationship to each, unless it has ended. -> [(edge id, line)]"""
    live_sql, live_args = db.live_filter(live)
    latest = {}
    for e in conn.execute(
        f"SELECT * FROM edges WHERE src_id=? AND story_time<=? AND {live_sql} ORDER BY id",
        [speaker_id, now, *live_args],
    ):
        if e["dst_id"] in others:
            latest[e["dst_id"]] = e
    return [
        (e["id"], f"- {e['rel']} {others[e['dst_id']]}" + (f" ({e['note']})" if e["note"] else ""))
        for e in latest.values()
        if not e["ended"]
    ][:FEELINGS]


def _clip(text: str, cap: int, ratio: float) -> tuple[str, int]:
    """Whole lines from the top that fit the cap: (text, 1 if anything was cut, else 0)."""
    if not text or estimate(text, ratio) <= cap:
        return text, 0
    kept: list[str] = []
    for line in text.splitlines():
        if estimate("\n".join([*kept, line]), ratio) > cap:
            break
        kept.append(line)
    if not kept:  # one enormous line: cut it
        kept = [text[: int(cap * ratio / MARGIN)]]
    return "\n".join(kept), 1


def _system(conn, story, persona, present, place, player: str) -> tuple[str, str]:
    rules = RULES.format(persona=persona["name"] if persona else "the user")
    # An imported card writes `{{user}}` for whoever is playing; here that is known.
    # what anyone can see; who each of them is goes only into their own prompt (the tail)
    cards = [f"## {e['name']}\n{macros(e['looks'] or '', user=player)}".strip() for e in present]
    if place:
        cards.append(f"## Place: {place['name']}\n{place['description'] or ''}".strip())
    # The premise the story started with; stories from before it was copied read the plot live.
    premise = json.loads(story["overrides"]).get("premise")
    if premise is None and story["scenario_id"]:
        scenario = conn.execute(
            "SELECT description FROM lib_items WHERE id=?", (story["scenario_id"],)
        ).fetchone()
        premise = scenario and scenario["description"]
    if premise:
        cards.insert(0, f"## Scenario\n{premise}")
    pinned = conn.execute(
        "SELECT detail FROM memories WHERE story_id=? AND pinned=1 AND hidden=0 ORDER BY id",
        (story["id"],),
    ).fetchall()
    if pinned:
        cards.append("## Established facts\n" + "\n".join(f"- {p['detail']}" for p in pinned))
    return rules, "\n\n".join(cards)


def _line(message, names: dict[int, str], narrator: bool = False) -> str:
    name = names.get(message["speaker_id"])
    audience = chat.audience_of(message)
    if audience:  # a whisper: the narrator only knows it happened
        to = " and ".join(names.get(i, "someone") for i in audience)
        if narrator:
            return f"{name or 'Someone'} whispers to {to}."
        name = f"{name or 'Someone'} (whispering to {to})"
    return f"{name}: {message['text']}" if name else message["text"]


def _window(
    conn, story, path: list, lines: list[str], cap: int, ratio: float, after_skip: int = 0
) -> tuple[int, int]:
    """Where the verbatim window starts. It moves rarely and far, and is remembered per story
    as a message id, so it means the same thing for every speaker and every branch.

    `after_skip` is a hard floor: nothing from before a long time skip is shown verbatim."""
    overrides = json.loads(story["overrides"])
    floor = max(len(lines) - KEEP_LAST, 0)
    start = next((i for i, m in enumerate(path) if m["id"] >= overrides.get("history_from", 0)), 0)
    cut = start = min(start, floor)  # a shorter branch clamps it
    sizes = [estimate(line, ratio) for line in lines]
    while sum(sizes[cut:]) > cap and cut < floor:
        cut = min(cut + max(1, (len(lines) - cut) // 4), floor)
    cut = max(cut, after_skip)
    if cut > start:
        overrides["history_from"] = path[cut]["id"]
        with conn:
            conn.execute(
                "UPDATE stories SET overrides=? WHERE id=?", (json.dumps(overrides), story["id"])
            )
    return cut, sum(sizes[cut:])


def _fit_memories(recalled: list[Recalled], cap: int, ratio: float) -> tuple[list[str], list, int]:
    lines, report, used = [], [], 0
    for m in sorted(recalled, key=lambda m: m.activation, reverse=True):
        label = m.tier.upper()
        choices = [("detail" if m.tier == "sharp" else "gist", f"- [{label}] {m.text}")]
        if m.tier == "sharp" and m.gist:
            choices.append(("gist", f"- [HAZY] {m.gist}"))  # degrade before dropping
        rendered, cost = "dropped", 0
        for how, line in choices:
            if used + (tokens := estimate(line, ratio)) <= cap:
                lines.append(line)
                rendered, cost, used = how, tokens, used + tokens
                break
        report.append(
            {"memory_id": m.memory_id, "tier": m.tier, "rendered": rendered, "tokens": cost}
            | m.breakdown
        )
    return lines, report, used


def build(
    conn: sqlite3.Connection,
    story_id: int,
    speaker_id: int | None,  # None = the narrator
    ep: Endpoint,
    recalled: list[Recalled] | tuple = (),
    directive: str = "",
    inside: str = "",
    leaf_id: int | None = None,  # build as of this message (a regenerate); default: active leaf
) -> Built:
    story = conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()
    ratio = token_ratio(conn, ep.model)
    ctx = ep.params.get("ctx_size", BASE_CTX)
    caps = {name: int(tokens * ctx / BASE_CTX) for name, tokens in BASE_CAPS.items()}
    think = ep.params.get("think_budget_tokens", DEFAULT_THINK_BUDGET) if ep.thinks else 0
    reserve = caps["response"] + think

    full = chat.path_to(conn, leaf_id) if leaf_id else chat.active_path(conn, story_id)
    path = [m for m in full if not m["hidden"]]
    live = db.live_runs(conn, story_id, leaf_id)
    scene_id = chat.scene_of(conn, story_id, path)
    scene = conn.execute("SELECT * FROM scenes WHERE id IS ?", (scene_id,)).fetchone()
    present = chat.present_entities(conn, scene_id, path)
    names = {e["entity_id"]: e["name"] for e in present}
    names |= {
        r["id"]: r["name"]
        for r in conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,))
    }
    persona = next((e for e in present if e["entity_id"] == story["persona_entity_id"]), None)
    place = (
        conn.execute("SELECT * FROM entities WHERE id=?", (scene["place_id"],)).fetchone()
        if scene and scene["place_id"]
        else None
    )
    speaker = next((e for e in present if e["entity_id"] == speaker_id), None)
    # Who `{{user}}` means, from the story rather than the room: the player is the player even
    # in a scene their character has stepped out of.
    player = names.get(story["persona_entity_id"]) or "the user"

    # 1-2. the stable system block
    # No scene summaries here: they are written by an all-seeing reader, and this block is
    # shared by every speaker. What a character knows of the past comes from their own memory.
    rules, cards = _system(conn, story, persona, present, place, player)
    system = "\n\n".join(part for part in (rules, cards) if part)

    # 3. history: whatever is left after the fixed blocks and the tail's reserved room.
    # A character only sees what reached them (chat.heard_by); the narrator sees everything
    # said aloud, that a whisper happened but not its words, and no thoughts at all.
    if speaker_id is not None:
        heard = chat.heard_by(conn, path, speaker_id)
        shown = [m for m in path if m["id"] in heard]
    else:
        shown = [m for m in path if chat.audience_of(m) != []]
    lines = [_line(m, names, narrator=speaker_id is None) for m in shown]
    # the tail's room is reserved whoever speaks, so the history window never moves with them
    tail_room = caps["memory"] + caps["flags"] + caps["examples"] + caps["mind"]
    history_cap = ctx - reserve - estimate(system, ratio) - tail_room
    # After a long time skip, what came before is memory, not a transcript: once those lines
    # have been read into memory, they leave the window, and recalling them means decay.
    ends = conn.execute(
        f"SELECT to_message_id FROM extraction_runs WHERE trigger!='between'"
        f" AND id IN ({','.join('?' * len(live))})",
        sorted(live),
    ).fetchall()
    read_to = max((r[0] for r in ends), default=0)
    after_skip = max(
        (
            i
            for i, m in enumerate(shown)
            if i and m["skip_minutes"] >= BIG_SKIP and shown[i - 1]["id"] <= read_to
        ),
        default=0,
    )
    cut, history_tokens = _window(conn, story, shown, lines, max(history_cap, 0), ratio, after_skip)

    messages: list[dict] = [{"role": "system", "content": system}]

    def add(role: str, content: str) -> None:
        if messages[-1]["role"] == role:  # many chat templates reject two turns in a row
            messages[-1]["content"] += "\n\n" + content
        else:
            messages.append({"role": role, "content": content})

    window = [
        ("assistant" if m["role"] == "assistant" else "user", line)
        for m, line in zip(shown[cut:], lines[cut:], strict=True)
    ]
    # a pending user line is held back: the tail goes directly in front of it, never inside it
    pending = window.pop()[1] if window and window[-1][0] == "user" else "(Continue the scene.)"
    for role, line in window:
        add(role, line)

    # 4. the volatile tail
    now = path[-1]["story_time"] if path else 0
    where = f"{place['name']} · " if place else ""
    state = [
        f"[Scene] {where}{clock.label(now, story['epoch_offset_min'])}"
        f" · present: {', '.join(e['name'] for e in present) or 'no one'}"
    ]
    seen, used = [], 0
    for line in _state(conn, [*present, *([place] if place else [])], speaker_id, now, live):
        if (used := used + estimate(line, ratio)) > caps["flags"]:
            break
        seen.append(line)
    if seen:
        state.append("[State]\n" + "\n".join(seen))
    memory_lines, report, memory_tokens = _fit_memories(list(recalled), caps["memory"], ratio)
    who = speaker["name"] if speaker else "the narrator"
    if speaker and speaker["description"]:
        state.append(f"[Who {who} is]\n{macros(speaker['description'], user=player)}")
    if speaker and speaker["private"]:
        state.append(f"[Only {who} knows]\n{speaker['private']}")
    felt = []
    if speaker:  # the narrator voices no one's feelings
        here = {e["entity_id"]: e["name"] for e in present if e["entity_id"] != speaker_id}
        felt = _feelings(conn, speaker_id, here, now, live)
        if felt:
            state.append(f"[How {who} feels]\n" + "\n".join(line for _, line in felt))
    talks = macros(speaker["examples"], user=player) if speaker else ""
    examples, clipped = _clip(talks, caps["examples"], ratio)
    if examples:
        state.append(f"[How {who} talks]\n{examples}")
    if memory_lines:
        state.append(f"[{who} remembers]\n" + "\n".join(memory_lines))
    mind_text, mind_clipped = _clip(inside, caps["mind"], ratio)
    if mind_text:
        state.append(mind_text)
    directive = f"{LENGTHS[reply_length(conn)]} {directive}".strip()
    if speaker:
        state.append(f"[Directive] Reply only as {who}, in English only. {directive}".strip())
    else:
        state.append(
            "[Directive] Reply only as the narrator, in English only: describe what happens and "
            f"what can be perceived. Voice no character's private thoughts. {directive}".strip()
        )
    tail = "\n".join(state)
    # Inside the final user turn, not a trailing system message: those break Mistral and Gemma.
    add("user", f"{tail}\n\n{pending}")

    sections = [
        {"name": "rules", "tokens": estimate(rules, ratio), "cap": caps["rules"], "evicted": 0},
        {"name": "cards", "tokens": estimate(cards, ratio), "cap": caps["cards"], "evicted": 0},
        {"name": "history", "tokens": history_tokens, "cap": max(history_cap, 0), "evicted": cut},
        {
            "name": "memory",
            "tokens": memory_tokens,
            "cap": caps["memory"],
            "evicted": sum(m["rendered"] == "dropped" for m in report),
        },
        {
            "name": "examples",
            "tokens": estimate(examples, ratio) if examples else 0,
            "cap": caps["examples"],
            "evicted": clipped,
        },
        {
            "name": "mind",
            "tokens": estimate(mind_text, ratio) if mind_text else 0,
            "cap": caps["mind"],
            "evicted": mind_clipped,
        },
        {
            "name": "tail",
            "tokens": estimate(tail, ratio),
            "cap": tail_room,
            "evicted": 0,
            "feelings": [edge_id for edge_id, _ in felt],  # what the Mind draws gold
        },
    ]
    total = sum(estimate(m["content"], ratio) for m in messages)
    start = shown[cut]["id"] if cut < len(shown) else None
    return Built(messages, sections, report, total, reserve, ctx, start)


def log(
    conn: sqlite3.Connection, story_id: int, message_id: int | None, speaker_id, built: Built
) -> int:
    """One row per turn: the inspector's token meter, resolved prompt and recall breakdown."""
    with conn:
        log_id = conn.execute(
            "INSERT INTO context_log"
            "(story_id, message_id, speaker_id, budget, sections, memories, prompt, est_tokens)"
            " VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (
                story_id,
                message_id,
                speaker_id,
                built.budget,
                json.dumps(built.sections),
                json.dumps(built.memories),
                json.dumps(built.messages, ensure_ascii=False),
                built.est_tokens,
            ),
        ).lastrowid
        conn.execute(
            "UPDATE context_log SET prompt=NULL WHERE story_id=? AND id NOT IN"
            " (SELECT id FROM context_log WHERE story_id=? ORDER BY id DESC LIMIT ?)",
            (story_id, story_id, KEEP_PROMPTS),
        )
    return log_id


def finish_log(conn: sqlite3.Connection, log_id: int, message_id: int | None, done: dict) -> None:
    """After the reply: which message it produced, and what the backend really counted."""
    usage = done.get("usage") or {}
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
    if cached is None:
        cached = (done.get("timings") or {}).get("cache_n")  # llama.cpp reports it here
    with conn:
        conn.execute(
            "UPDATE context_log SET message_id=?, actual_tokens=?, cached_tokens=? WHERE id=?",
            (message_id, usage.get("prompt_tokens"), cached, log_id),
        )
