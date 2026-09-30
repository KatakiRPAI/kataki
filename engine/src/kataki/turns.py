"""One chat turn: who speaks, what they remember, the prompt, the reply.

Everything here is deterministic except the model call. A reply is kept when it finishes,
and also when it is stopped midway: a stopped reply keeps what was written.

Events: ("meta", {...}) first, then ("thought" | "token", text)..., then ("done", {...}) or
("error", {"message": ...}).
"""

import asyncio
import json
import logging
import re
import sqlite3
import time
from collections.abc import AsyncIterator, Callable
from contextlib import aclosing
from typing import Any

from kataki import (
    after,
    between,
    bonds,
    chat,
    clock,
    context,
    embed,
    extract,
    features,
    goals,
    honesty,
    images,
    inner,
    knobs,
    recollect,
    retrieve,
    roles,
    thought,
)
from kataki.llm import LLM, LLMError

Event = tuple[str, Any]
NARRATOR = "narrator"
MAX_STOPS = 4  # the most stop strings OpenAI-style APIs accept


def _story(conn: sqlite3.Connection, story_id: int) -> sqlite3.Row:
    return conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()


def _minute_of_day(story: sqlite3.Row, parent_time: int) -> int:
    """The clock just before a new message's own skip: one tick past its parent."""
    return (parent_time + story["minutes_per_turn"] + story["epoch_offset_min"]) % clock.DAY


def _cast(conn: sqlite3.Connection, story_id: int, path: list) -> list:
    """The AI characters in the scene at the end of this path."""
    scene_id = chat.scene_of(conn, story_id, path)
    present = chat.present_entities(conn, scene_id, path)
    return [e for e in present if e["is_ai"] and e["kind"] == "character"]


def _addressed(conn: sqlite3.Connection, text: str, ids: list[int]) -> int | None:
    """The character named first in the text (by any alias), if any."""
    return next(iter(chat.named(conn, text, ids)), None)


def select_speaker(conn: sqlite3.Connection, story_id: int, requested=None) -> int | None:
    """Who replies (None = the narrator). See `speaker_why`."""
    return speaker_why(conn, story_id, requested)[0]


def speaker_why(conn: sqlite3.Connection, story_id: int, requested=None) -> tuple[int | None, str]:
    """Who replies (None = the narrator), and why: the UI's pick wins ("picked", "narrator");
    else, among those who heard the user's line, whoever it addresses ("named"), else whoever
    spoke last ("last"). With no user line pending, or one nobody heard (a thought), the
    quietest character speaks ("quietest"), so continuing lets a group take turns; with no one
    here, the narrator ("alone"). No model call."""
    if requested == NARRATOR:
        return None, "narrator"
    if isinstance(requested, int):
        return requested, "picked"
    path = chat.active_path(conn, story_id)
    ids = [e["id"] for e in _cast(conn, story_id, path)]
    if not ids:
        return None, "alone"
    if path and path[-1]["role"] == "user":
        pending = path[-1]["id"]
        hearers = [e for e in ids if pending in chat.heard_by(conn, path, e)]
        if hearers:
            if named := _addressed(conn, path[-1]["text"], hearers):
                return named, "named"
            last = (m["speaker_id"] for m in reversed(path) if m["role"] == "assistant")
            return next((s for s in last if s in hearers), hearers[0]), "last"
    spoke_at = {m["speaker_id"]: i for i, m in enumerate(path) if m["role"] == "assistant"}
    return min(ids, key=lambda e: spoke_at.get(e, -1)), "quietest"


def _pressed(conn: sqlite3.Connection, story_id: int, speaker_id: int) -> set[int]:
    """Hazy memories this speaker was already shown last turn: the topic is being pressed."""
    row = conn.execute(
        "SELECT memories FROM context_log WHERE story_id=? AND speaker_id=? ORDER BY id DESC",
        (story_id, speaker_id),
    ).fetchone()
    if row is None:
        return set()
    shown = json.loads(row["memories"])
    return {m["memory_id"] for m in shown if m["tier"] == "hazy" and m["rendered"] != "dropped"}


def _recall_record(recalled: list, fix: dict | None, held: str) -> dict | None:
    """gen.recall (spec §8.3 slice 6): what her memory did in this reply, or None."""
    try:
        drift = [
            {**r.breakdown["drift"], "memory_id": r.memory_id}
            for r in recalled
            if r.breakdown.get("drift")
        ]
        cues = [r.memory_id for r in recalled if r.breakdown.get("cue")]
    except Exception:
        drift, cues = [], []
    if not (drift or cues or fix or held):
        return None
    return {"drift": drift, "cues": cues, "correction": fix and fix["record"], "hold": bool(held)}


def _agenda_ask(gen: dict, path: list) -> dict | None:
    """What the side call is asked about her agenda (slice 7): how the line she is answering took
    up the goal she raised before, or whether this reply brought up the one offered now."""
    if (got := gen.get("goal")) and path and got["line"] == path[-1]["id"]:
        return {"mode": "judge", **got}
    if said := gen.get("agenda"):
        return {"mode": "offer", **said}
    return None


def _shown_needs(path: list, who: int) -> list[str]:
    """The needs her last few replies were written with (their cooldown)."""
    mine = [m for m in path if m["role"] == "assistant" and m["speaker_id"] == who]
    out = []
    for m in mine[-inner.NEED_COOL :]:
        try:
            out.append((json.loads(m["gen"] or "{}").get("need") or {}).get("need"))
        except (ValueError, AttributeError):
            continue
    return out


def _mood_of(state: dict | None) -> float | None:
    """Her mood's valence for mood-congruent recall (slice 6), or None when unknown."""
    try:
        return float(state["mood"]["v"]) if state else None
    except (KeyError, TypeError, ValueError):
        return None


def _unsign(text: str, name: str) -> str:
    """Drop the speaker's own name left dangling after the last sentence ('...due. Mira'):
    small models sign off in the 'Name: line' shape of the history. A name inside a sentence
    stays."""
    # ... or signed like a letter ('... the crown." — Payton Lin'), or in asterisks ('*Payton*')
    names = "|".join(re.escape(n) for n in dict.fromkeys([name, *name.split()[:1]]) if n)
    pattern = rf"(?:(?<=[.!?\"”*…])\s+|\n+)(?:[—–-]\s*)?[*_]*(?:{names}):?[*_]*\s*$"
    return re.sub(pattern, "", _unnoted(text)).rstrip()


# a model that copies the prompt's memory notes into the story ("I type a quick thought to my
# own memory bank: [SHARP] Kai is my driver…") loses that whole paragraph from what is kept
NOTE = re.compile(r"\[(SHARP|HAZY)\]", re.I)


def _unnoted(text: str) -> str:
    kept = [p for p in re.split(r"(\n\s*\n)", text) if not NOTE.search(p)]
    return re.sub(r"\n{3,}", "\n\n", "".join(kept)).strip()


class _Prefix:
    """Drops a leading 'Mira:' the model may copy from the history's line format."""

    def __init__(self, name: str):
        self.prefix, self.held, self.done = f"{name}:".lower(), "", False

    def feed(self, text: str) -> str:
        if self.done:
            return text
        self.held += text
        probe = self.held.lstrip().lower()
        if probe.startswith(self.prefix):
            self.done = True
            rest = self.held.lstrip()[len(self.prefix) :].lstrip()
            self.held = ""
            return rest
        if self.prefix.startswith(probe):
            return ""  # could still turn out to be the prefix
        return self.flush()

    def flush(self) -> str:
        self.done = True
        held, self.held = self.held, ""
        return held


HOLD = 160  # ponytail: characters held back at most while the opening is checked
SENTENCE_END = re.compile(r"[.!?…]\s|\n")
LEAD = re.compile(r"^(?:\W*?\*[^*\n]{0,80}\*)?\W*")  # what bonds.OPENERS skips before the opening


class _Opener:
    """Holds a reply's first sentence back while the check is armed (bonds.armed), so an
    agreeing, apologising or assistant-style opening is caught before anyone sees it; and,
    when a thought came first (`watch`), an opening that says the thought aloud."""

    def __init__(self, armed: bool):
        self.armed, self.held, self.hit, self.dropped = armed, "", None, ""
        self.thinks, self.echo, self.watched = None, None, False

    def watch(self, early: dict | None) -> None:
        """Called once, just before the first visible word, with the thought written before it.
        The echo check rides on the opener check: the first sentence is held only when that one
        is already armed (holding it for the echo alone cost the first word ~3 s, slice 3
        latency probe); otherwise it streams at once and an echo is only recorded, no retake."""
        self.watched = True
        if early and early["thinks"] and not self.hit:
            self.thinks = early["thinks"]

    def feed(self, text: str) -> str:
        if self.hit:
            return ""
        if not self.armed:
            return text
        self.held += text
        body = self.held[LEAD.match(self.held).end() :]
        if len(self.held) < HOLD and not SENTENCE_END.search(body):
            return ""
        return self.flush()

    def flush(self) -> str:
        if self.hit or not self.armed:
            return ""
        self.armed = False
        held, self.held = self.held, ""
        self.hit = bonds.opener(held)
        if not self.hit and (echo := thought.echoed(self.thinks, held)):
            self.hit = self.echo = echo
        if self.hit:
            self.dropped = held  # kept aside, in case the second take fails
            return ""
        return held


def _early(thoughts: list[str], header: thought.Header, name: str, tags) -> dict | None:
    """The thought written before the reply's first word: in the tags, or caught at its start."""
    return thought.parse(thought.split("".join(thoughts), name, tags)[1] + header.caught, name)


def _watch(opener: "_Opener", thoughts: list[str], header: thought.Header, name: str, tags) -> None:
    """opener.watch(_early(...)), guarded: a failure costs only the echo check."""
    try:
        opener.watch(_early(thoughts, header, name, tags))
    except Exception as e:
        logging.getLogger(__name__).warning("echo check skipped: %s", e)
        opener.watched = True


async def _read_past_before_skip(
    conn: sqlite3.Connection, llm: LLM, story_id: int, get_key: Callable[[str], str | None]
) -> None:
    """Years pass before this reply, so the lines before them leave the verbatim window, and
    a line leaves only once memory has read it. Read them now rather than after the reply,
    or the reply would still see the old conversation word for word."""
    while any(m["skip_minutes"] >= context.BIG_SKIP for m in extract.pending(conn, story_id)[1:]):
        if (job := extract.due(conn, story_id, get_key)) is None:
            return
        run_id = await extract.read(conn, llm, story_id, *job)
        status = conn.execute("SELECT status FROM extraction_runs WHERE id=?", (run_id,))
        if (row := status.fetchone()) is None or row[0] != "ok":
            return  # the model can't read right now: reply anyway, the window stays whole


FACE = {
    "type": "object",
    "properties": {"expression": {"type": "string", "enum": list(images.EXPRESSIONS)}},
    "required": ["expression"],
    "additionalProperties": False,
}


def _face(data: dict) -> str:
    if (face := data.get("expression")) not in images.EXPRESSIONS:
        raise ValueError(f"expression must be one of {', '.join(images.EXPRESSIONS)}")
    return face


def _has_pack(conn: sqlite3.Connection, speaker_id: int) -> bool:
    row = conn.execute(
        "SELECT l.data FROM entities e JOIN lib_items l ON l.id = e.lib_item_id WHERE e.id=?",
        (speaker_id,),
    ).fetchone()
    return bool(row and json.loads(row["data"]).get("pack"))


async def _expression(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    speaker_id: int,
    message_id: int,
    name: str,
    text: str,
    get_key: Callable[[str], str | None],
) -> str | None:
    """Which of the speaker's sprites fits the line they just said (M3 spec §7.1): one small
    call to the memory reader's model, and only for someone who has sprites to show. A failure
    costs nothing but the face: they stay as they were."""
    if not _has_pack(conn, speaker_id):
        return None
    if (ep := roles.resolve(conn, "utility", story_id, get_key)) is None:
        return None
    ask = [
        {
            "role": "system",
            "content": f"Pick the facial expression {name} has while saying this line. Reply with "
            f'JSON only: {{"expression": one of {", ".join(images.EXPRESSIONS)}}}.',
        },
        {"role": "user", "content": text[-1500:]},
    ]
    try:
        face = await llm.complete_json(ep, ask, FACE, _face, name="expression")
    except LLMError:
        return None
    with conn:
        conn.execute("UPDATE messages SET expression=? WHERE id=?", (face, message_id))
    return face


async def _generate(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    parent_id: int | None,
    speaker_id: int | None,
    get_key: Callable[[str], str | None],
    why: str = "picked",  # why this speaker (speaker_why), kept for Backstage's Mind
) -> AsyncIterator[Event]:
    began = time.monotonic()
    ms = lambda since: round(1000 * (time.monotonic() - since))  # noqa: E731
    await _read_past_before_skip(conn, llm, story_id, get_key)
    role = "rp" if speaker_id is not None else "narrator"
    ep = roles.resolve(conn, role, story_id, get_key)
    if ep is None:
        yield ("error", {"message": f"No model is set for the '{role}' role yet."})
        return
    ep = knobs.thinking(conn, ep)  # Settings › Memory and thinking › Thinking
    ep = knobs.character_model(conn, speaker_id, ep, get_key)  # their own model, if they have one
    story = _story(conn, story_id)
    path = chat.path_to(conn, parent_id)
    try:  # time just passed: the life between scenes first, so the mind below starts from it
        between.at_skip(conn, story_id, path)
    except Exception as e:
        logging.getLogger(__name__).warning("between skipped for story %s: %s", story_id, e)
    names = dict(
        conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)).fetchall()
    )
    name = names.get(speaker_id)
    minds: dict[int, dict] = {}  # everyone here, as they feel after the latest line
    felt: list[str] = []  # the speaker's feeling rows of the mind block
    pending: dict[int, list[dict]] = {}  # ledger rows the latest line adds, kept with the reply
    ties: list[str] = []  # the speaker's relationship rows of the mind block
    stood: list[dict] = []  # the same, as the app shows them (gen.bonds, the Mind graph)
    try:  # the mind adds to a turn, it never stops one
        if features.enabled(conn, "mind.affect"):
            wants = features.enabled(conn, "mind.goals")  # slice 7: needs ride on the mood
            model = await asyncio.to_thread(embed.builtin)
            minds = inner.react(conn, story_id, path, model, needs=wants)
        if speaker_id in minds:
            felt = inner.lines(minds[speaker_id], inner.profile(conn, speaker_id))
    except Exception as e:
        logging.getLogger(__name__).warning("mind skipped for story %s: %s", story_id, e)
        minds, felt = {}, []
    try:
        bonds_on = features.enabled(conn, "mind.bonds")
    except Exception as e:
        logging.getLogger(__name__).warning("bonds setting unreadable: %s", e)
        bonds_on = False
    if bonds_on:
        try:
            pending = bonds.react(conn, story_id, path, await asyncio.to_thread(embed.builtin))
        except Exception as e:
            logging.getLogger(__name__).warning("bonds skipped for story %s: %s", story_id, e)
        if speaker_id is not None:
            try:  # a failed render costs the prompt lines, not the events (they are still saved)
                ties, stood = bonds.render(
                    conn, story_id, speaker_id, path, pending.get(speaker_id, [])
                )
            except Exception as e:
                logging.getLogger(__name__).warning("bonds not shown for story %s: %s", story_id, e)
    onmind = None  # the one thing from her time away that reaches this reply (slice 5)
    try:
        if speaker_id is not None and features.enabled(conn, "mind.offscreen"):
            user = names.get(story["persona_entity_id"])
            onmind = between.on_mind(conn, story_id, speaker_id, path, user)
    except Exception as e:
        logging.getLogger(__name__).warning("on-mind skipped for story %s: %s", story_id, e)
        onmind = None
    decide, check, hold = "", False, False  # the yield decision; check the opening; hold it back
    try:
        if speaker_id is not None and bonds_on:
            prof, state = inner.profile(conn, speaker_id), minds.get(speaker_id)
            now = path[-1]["story_time"] if path else 0
            grudge = any(b["grudge"] and b["you"] for b in stood)  # held against the user
            user = names.get(story["persona_entity_id"]) or "the other person"
            dial = knobs.dial(conn, speaker_id, "pushback", "realistic")
            scene_id = chat.scene_of(conn, story_id, path)
            decide = bonds.stance(state, prof, dial, grudge, user, scene_id, now)
            check = bonds.armed(state, prof, grudge, now)
            hold = check and knobs.setting(conn, "mind.level", "standard") != "lite"
    except Exception as e:
        logging.getLogger(__name__).warning("stance skipped for story %s: %s", story_id, e)
        decide, check, hold = "", False, False
    secret = None  # what she does about the truth this reply (slice 4), decided by code
    try:
        if speaker_id is not None and features.enabled(conn, "mind.secrets"):
            secret = honesty.read(conn, story_id, speaker_id, path, inner.profile(conn, speaker_id))
    except Exception as e:
        logging.getLogger(__name__).warning("secrets skipped for story %s: %s", story_id, e)
        secret = None
    if secret and secret["directive"]:
        decide = " ".join(p for p in (decide, secret["directive"]) if p)
    if onmind and onmind["directive"]:
        decide = " ".join(p for p in (decide, onmind["directive"]) if p)
    human = False  # slice 6: her memory's own effects (the repair of a slip, holding the line)
    repaired, held = None, ""
    try:
        human = speaker_id is not None and features.enabled(conn, "mind.recall")
        if human:
            repaired = recollect.repair(
                conn, speaker_id, path, names.get(story["persona_entity_id"])
            )
    except Exception as e:
        logging.getLogger(__name__).warning("repair skipped for story %s: %s", story_id, e)
        repaired = None
    if repaired and repaired["directive"]:
        decide = " ".join(p for p in (decide, repaired["directive"]) if p)
    agenda, judged, let_go = None, None, ""  # slice 7: what she wants, how the user answered it
    try:
        if speaker_id is not None and features.enabled(conn, "mind.goals"):
            judged = goals.judge(conn, speaker_id, path)
            busy = any(x and x["directive"] for x in (secret, onmind, repaired))
            last = path[-1] if path else None
            stirred = bool(pending.get(speaker_id)) or (
                last is not None and last["role"] == "user" and inner.sense(last["text"])
            )  # an emotional line is not the moment
            user = names.get(story["persona_entity_id"])
            if not busy and not stirred:
                agenda = goals.pick(conn, speaker_id, path, user)
            if not agenda:  # just dropped: she lets it be for a while
                let_go = goals.restraint(conn, speaker_id, path, user)
    except Exception as e:
        logging.getLogger(__name__).warning("goals skipped for story %s: %s", story_id, e)
        agenda = judged = None
        let_go = ""
    if let_go:
        decide = " ".join(p for p in (decide, let_go) if p)
    if agenda:
        decide = " ".join(p for p in (decide, agenda["directive"]) if p)
        if onmind and not onmind["directive"]:
            onmind = None  # one thing on her mind at a time (note 22 §4 row 5)
    mind_rows = [onmind["row"]] if onmind and onmind["row"] else []
    need = None  # slice 7: the one pressing need, as behaviour (note 22 §4 row 6)
    try:
        if speaker_id is not None and features.enabled(conn, "mind.goals"):
            now = path[-1]["story_time"] if path else 0
            minute = (now + story["epoch_offset_min"]) % clock.DAY
            prof = inner.profile(conn, speaker_id)
            need = inner.need_row(
                minds.get(speaker_id), prof, minute, _shown_needs(path, speaker_id)
            )
    except Exception as e:
        logging.getLogger(__name__).warning("needs skipped for story %s: %s", story_id, e)
        need = None
    if need:
        mind_rows.append(need["text"])
    try:
        inside = (
            inner.block(names.get(speaker_id, ""), ties + felt + mind_rows)
            if speaker_id is not None
            else ""
        )
    except Exception as e:
        logging.getLogger(__name__).warning("mind block skipped: %s", e)
        inside = ""
    guards = secret["guards"] if secret else []  # every secret kept from someone here
    guarding = bool(secret and secret["hot"])  # on the table: hold the reply by sentences
    try:
        lite = knobs.setting(conn, "mind.level", "standard") == "lite"
    except Exception:
        lite = True  # unreadable: no retake, code only
    think_why = None  # why the header was asked, for gen.trace.think
    try:
        voice = thought.mode(conn, ep, speaker_id)
        header_ask = ""
        if voice == "inline" and (
            reason := thought.why(
                conn,
                speaker_id,
                path,
                chat.scene_of(conn, story_id, path),
                check,
                bool(pending.get(speaker_id)),
                hot=bool(secret and secret["hot"]),
            )
        ):
            header_ask, think_why = thought.ask(name, ep.think_tags), reason
    except Exception as e:
        logging.getLogger(__name__).warning("thought skipped for story %s: %s", story_id, e)
        voice, header_ask = None, ""
    first = " ".join(p for p in (decide, header_ask) if p)

    trace: dict = {"why": why, "ms": {}, "think": think_why}
    if secret and secret["gate"]:
        trace["gate"] = secret["gate"]
    at = time.monotonic()
    built = context.build(
        conn, story_id, speaker_id, ep, leaf_id=parent_id, inside=inside, directive=first
    )
    trace["ms"]["prompt"] = ms(at)
    built_recalled: list = []
    if speaker_id is not None:
        heard = chat.heard_by(conn, path, speaker_id)  # a whisper to someone else cues nothing
        recent = "\n".join(m["text"] for m in [m for m in path if m["id"] in heard][-2:])
        trace["cue"] = recent[-600:]  # what recall searched with
        at = time.monotonic()
        recalled = retrieve.recall(
            conn,
            story_id,
            speaker_id,
            recent,
            window_start=built.window_start,
            pressed=_pressed(conn, story_id, speaker_id),
            leaf_id=parent_id,
            d=knobs.decay(conn, speaker_id),
            vector_ranks=(
                await embed.ranks_for(conn, llm, story_id, recent, get_key)
                if knobs.setting(conn, "memory.byMeaning", True)  # Settings › Recall by meaning
                else None
            ),
            mood=_mood_of(minds.get(speaker_id)),  # what she feels tilts what comes back
        )
        trace["ms"]["recall"] = ms(at)
        try:  # the user "corrects" what she clearly remembers: she keeps it
            busy = repaired and repaired["directive"]
            if human and not busy and not (secret and secret["hot"]):  # a lie is not a slip
                called = conn.execute(
                    "SELECT e.name FROM entities e WHERE e.story_id=? UNION"
                    " SELECT a.alias FROM aliases a JOIN entities e ON e.id=a.entity_id"
                    " WHERE e.story_id=?",
                    (story_id, story_id),
                )
                named = {w for (n,) in called for w in recollect._words(n)}
                user = names.get(story["persona_entity_id"])
                held = recollect.hold(path, recalled, user, named)
        except Exception as e:
            logging.getLogger(__name__).warning("hold skipped for story %s: %s", story_id, e)
            held = ""
        if held:
            decide = " ".join(p for p in (decide, held) if p)
            first = " ".join(p for p in (decide, header_ask) if p)
        if recalled:
            at = time.monotonic()
            built = context.build(
                conn,
                story_id,
                speaker_id,
                ep,
                recalled,
                leaf_id=parent_id,
                inside=inside,
                directive=first,
            )
            trace["ms"]["prompt"] += ms(at)
            built_recalled = list(recalled)
    log_id = context.log(conn, story_id, None, speaker_id, built)

    parent = chat.get_message(conn, parent_id) if parent_id else None
    then = parent["story_time"] if parent else 0  # the clock of the line being answered
    jump = parent["skip_minutes"] if parent else 0
    epoch = story["epoch_offset_min"]
    moments = json.loads(story["overrides"]).get("moments", [])
    yield (
        "meta",
        {
            "speaker": {"id": speaker_id, "name": name} if speaker_id is not None else None,
            "role": role,
            "model": ep.model,
            "thinks": ep.thinks,
            "parent_id": parent_id,
            # time that just passed, for the time-skip sequence: before it, and at this reply
            "skip": jump,
            "from_clock": clock.label(then - jump, epoch),
            "clock": clock.label(then + story["minutes_per_turn"], epoch),
            # the same two in the story's own words, for the time-skip card
            "from_date": clock.date(then - jump, epoch, moments),
            "date": clock.date(then + story["minutes_per_turn"], epoch, moments),
            # an effortful recall was rolled: the UI says "trying to remember"
            "strained": any(m.breakdown.get("effortful") is not None for m in built_recalled),
            "context": {
                "est_tokens": built.est_tokens,
                "budget": built.budget,
                "reserve": built.response_reserve,
                "sections": built.sections,
                "recalled": len(built.memories),
            },
        },
    )

    others = [e["id"] for e in _cast(conn, story_id, path) if e["id"] != speaker_id]
    who_else = [i for i in (story["persona_entity_id"], *others) if i in names]
    stops = [f"\n{names[i]}:" for i in who_else][:MAX_STOPS]

    parts, thoughts, done = [], [], {}
    prefix, opener, dropped = _Prefix(name or "Narrator"), _Opener(False), ""
    header, before = thought.Header(False, "", ep.think_tags), None
    guard = honesty.Guard([])
    finish, error, message_id, text, skip = "stopped", None, None, "", 0
    first_thought = first_token = first_word = None  # think_ms: first thought to first word
    asked = time.monotonic()
    try:
        for attempt in range(2):  # a second take only when the first opened like an assistant
            parts, thoughts, before = [], [], None  # before: thought pieces before the 1st word
            first_thought = first_token = first_word = None  # a retake times its own take
            prefix, opener = _Prefix(name or "Narrator"), _Opener(hold and not attempt)
            header = thought.Header(voice == "inline", name or "", ep.think_tags)
            try:  # on the table: by sentences, the cover in place; else by words, no cover
                unheld = [(keys, None) for keys, _ in guards]
                guard = honesty.Guard(guards if guarding else unheld, words=not guarding)
            except Exception as e:
                logging.getLogger(__name__).warning("leak check skipped: %s", e)
                guard = honesty.Guard([])
            stream = llm.chat_stream(
                ep, built.messages, stop=stops, max_tokens=built.response_reserve
            )
            async with aclosing(stream) as stream:
                async for kind, value in stream:
                    if kind == "thought":
                        first_thought = first_thought or time.monotonic()
                        thoughts.append(value)
                        yield ("thought", value)
                    elif kind == "token":
                        first_token = first_token or time.monotonic()
                        before = len(thoughts) if before is None else before
                        value = prefix.feed(header.feed(value))
                        first_word = first_word or (value and time.monotonic()) or None
                        if value and voice == "inline" and not attempt and not opener.watched:
                            _watch(opener, thoughts, header, name, ep.think_tags)
                        if value := guard.feed(opener.feed(value)):
                            parts.append(value)
                            yield ("token", value)
                        if opener.hit or guard.hit:
                            break  # closing the stream stops the model
                    else:
                        done = value
            cut = opener.hit or guard.hit
            rest = "" if cut else prefix.feed(header.flush()) + prefix.flush()
            if rest and voice == "inline" and not attempt and not opener.watched:
                _watch(opener, thoughts, header, name, ep.think_tags)
            if not cut and (rest := guard.feed(opener.feed(rest) + opener.flush()) + guard.flush()):
                parts.append(rest)
                yield ("token", rest)
            # the one retake, only when the secret was on the table and nothing was seen yet
            redo = guarding and guard.hit and not guard.shown and not attempt and not lite
            if guard.hit and not redo:  # said: the cover takes its place, and the reply ends
                again = (trace.get("leak") or {}).get("resampled", False)
                trace["leak"] = {"hit": guard.hit, "resampled": again, "covered": True}
                fix = honesty.cover_up(
                    guard.kept, guard.kept + guard.leaked, guard.cover, name or "They"
                )
                parts = [guard.kept, fix]  # by words, the leaking sentence's start goes too
                if fix:
                    yield ("token", fix)
            if not opener.hit and not redo:
                break
            # ponytail: the dropped take's thoughts were already streamed (no words were)
            dropped = opener.dropped
            if redo:  # it gave the secret away before a word was seen: the one retake
                trace["leak"] = {"hit": guard.hit, "resampled": True, "covered": False}
                dropped = honesty.cover_up("", guard.leaked, guard.cover, name or "They")
                stronger = honesty.STRONGER.format(name=name)
            elif opener.echo:  # it said its thought aloud: the same one retake, told to keep it in
                trace["echo"] = {"hit": opener.echo, "resampled": True}
                stronger = thought.STRONGER.format(name=name)
            else:
                trace["check"] = {"hit": opener.hit, "resampled": True}
                stronger = bonds.STRONGER.format(name=name)
            try:  # a failed stronger prompt costs the check, not the turn: keep the first take's
                retake = context.build(
                    conn,
                    story_id,
                    speaker_id,
                    ep,
                    built_recalled,
                    leaf_id=parent_id,
                    inside=inside,
                    directive=" ".join(p for p in (decide, stronger, header_ask) if p),
                )
                context.finish_log(conn, log_id, None, {})  # the dropped take's row is closed
                log_id, built = context.log(conn, story_id, None, speaker_id, retake), retake
            except Exception as e:
                logging.getLogger(__name__).warning("resample prompt skipped: %s", e)
        finish = "stop"
    except LLMError as e:
        finish, error = "error", str(e)
    finally:  # runs on finish, on error, and when the client stops the stream
        # stopped while held: keep it, in the order it was written (header, prefix, opener)
        tail = prefix.feed(header.flush()) + prefix.flush()
        text = ("".join(parts) + guard.held + opener.held + tail).strip()
        if not text and dropped:  # the second take failed or came back empty: keep the first
            text = dropped.strip()
        reasoning, heard = "".join(thoughts), []
        if voice == "inline":  # the header is the thought: never the reasoning, never the reply
            try:
                r, heard = thought.split(reasoning, name, ep.think_tags)
                t, late = thought.split(text, name, ep.think_tags)  # written after the reply
                heard += header.caught + late
                if not t and finish == "stop":  # a tag never closed: the reply was inside it
                    t, r = r, ""
                # a stop or an error mid-thought keeps nothing: no thought fragment as the reply
                reasoning, text = r, t
            except Exception as e:  # no thought; the reply stays as streamed
                logging.getLogger(__name__).warning("thought not read: %s", e)
                heard = []
        text = _unsign(text, name or "Narrator")
        if text and guards:  # whatever went unheld or unchecked: the saved reply keeps no secret
            try:
                kept, key = honesty.scrub(
                    text, guards if guarding else [(k, None) for k, _ in guards], name or "They"
                )
                if key:
                    text = kept
                    again = (trace.get("leak") or {}).get("resampled", False)
                    trace["leak"] = {"hit": key, "resampled": again, "covered": True}
            except Exception as e:
                logging.getLogger(__name__).warning("leak check skipped: %s", e)
        if text:
            if check and not hold and (hit := bonds.opener(text)):
                trace["check"] = {"hit": hit, "resampled": False}  # lite: noted, not retaken
            parent_time = chat.get_message(conn, parent_id)["story_time"] if parent_id else 0
            skip = clock.parse_skip(text, _minute_of_day(story, parent_time))
            gen = {
                "role": role,
                "model": ep.model,
                "finish": finish,
                "reasoning": reasoning or None,
                "usage": done.get("usage"),
            }
            try:
                if seen := thought.parse(heard, name or ""):  # Peek's thought; came first?
                    early = _early(thoughts[:before], header, name or "", ep.think_tags)
                    gen["thought"] = {**seen, "from": "before" if early else "after"}
                    if "echo" not in trace and (echo := thought.echoed(seen["thinks"], text)):
                        trace["echo"] = {"hit": echo, "resampled": False}  # past the 1st sentence
            except Exception as e:
                gen.pop("thought", None)
                logging.getLogger(__name__).warning("thought not kept: %s", e)
            if first_thought:  # stopped mid-thought: the thinking ran until now
                spent = round(1000 * ((first_token or time.monotonic()) - first_thought))
                if gen["reasoning"]:
                    gen["think_ms"] = spent
                else:  # only the header was thought: its time is the thought's, not reasoning's
                    trace["ms"]["thought"] = spent
            elif first_word and first_token and gen.get("thought", {}).get("from") == "before":
                trace["ms"]["thought"] = round(1000 * (first_word - first_token))  # plain header
            if first_token:
                trace["ms"]["first_token"] = round(1000 * (first_token - asked))
            trace["ms"]["reply"] = ms(asked)
            trace["ms"]["total"] = ms(began)
            gen["trace"] = trace
            try:
                if speaker_id in minds:
                    gen["mind"] = inner.public(minds[speaker_id], inner.profile(conn, speaker_id))
            except Exception as e:
                logging.getLogger(__name__).warning("mood not kept: %s", e)
            if stood:
                gen["bonds"] = stood
            if secret and secret["honest"]:
                gen["honest"] = secret["honest"]
            if onmind:
                gen["onmind"] = onmind["record"]
            try:
                if agenda:
                    gen["agenda"] = {**agenda["record"], "tried": goals.tried(text, agenda["cue"])}
                if judged:
                    gen["goal"] = judged
                if need:
                    gen["need"] = need
            except Exception as e:
                logging.getLogger(__name__).warning("goal not kept: %s", e)
            try:
                if human and (got := _recall_record(built_recalled, repaired, held)):
                    gen["recall"] = got
            except Exception as e:
                logging.getLogger(__name__).warning("recall not kept: %s", e)
            message_id = chat.add_child(
                conn, story_id, parent_id, "assistant", text, speaker_id, skip, gen
            )
            try:
                if minds:
                    inner.save(conn, minds, message_id)
            except Exception as e:
                logging.getLogger(__name__).warning("mind not saved: %s", e)
            try:
                if pending:
                    bonds.save(conn, story_id, pending, message_id)
            except Exception as e:
                logging.getLogger(__name__).warning("bonds not saved: %s", e)
            try:  # she said it right this time: her memory is back on the truth
                if repaired:
                    now_t = chat.get_message(conn, message_id)["story_time"]
                    recollect.settle(conn, speaker_id, repaired["record"], message_id, now_t)
            except Exception as e:
                logging.getLogger(__name__).warning("correction not kept: %s", e)
        context.finish_log(conn, log_id, message_id, done)
        if prompt_tokens := (done.get("usage") or {}).get("prompt_tokens"):
            chars = sum(len(m["content"]) for m in built.messages)
            context.calibrate(conn, ep.model, chars, prompt_tokens)

    if error:
        yield ("error", {"message": error, "message_id": message_id})
    elif message_id is None:
        yield ("error", {"message": "The model returned an empty reply."})
    else:
        now = chat.get_message(conn, message_id)["story_time"]
        face, side_face = None, False  # the reply is already on screen; its face follows later
        if speaker_id is not None:
            at = time.monotonic()
            if knobs.setting(conn, "mind.level", "standard") == "lite" and speaker_id in minds:
                if _has_pack(conn, speaker_id):  # lite: the face is what they show, no call
                    face = inner.face(minds[speaker_id])
                    with conn:
                        conn.execute(
                            "UPDATE messages SET expression=? WHERE id=?", (face, message_id)
                        )
            elif after.wanted(conn):  # standard: one side call reads the exchange, face and all
                got = await after.run(
                    conn,
                    llm,
                    story_id,
                    path,
                    speaker_id,
                    message_id,
                    text,
                    minds.get(speaker_id),
                    get_key,
                    afterthought=voice == "after",
                    agenda=_agenda_ask(gen, path),
                )
                # the side call may have replaced the mood, and written an afterthought
                saved = json.loads(chat.get_message(conn, message_id)["gen"])
                gen["mind"], gen["thought"] = saved.get("mind"), saved.get("thought")
                if got and _has_pack(conn, speaker_id):
                    face, side_face = got["face"], True
                    with conn:
                        conn.execute(
                            "UPDATE messages SET expression=? WHERE id=?", (face, message_id)
                        )
            else:
                face = await _expression(
                    conn, llm, story_id, speaker_id, message_id, name, text, get_key
                )
            if face and not side_face:  # the face time joins the trace
                with conn:
                    conn.execute(
                        "UPDATE messages SET gen=json_set(gen, '$.trace.ms.face', ?) WHERE id=?",
                        (ms(at), message_id),
                    )
        yield (
            "done",
            {
                "message_id": message_id,
                "text": text,
                "skip_minutes": skip,
                "clock": clock.label(now, story["epoch_offset_min"]),
                "date": clock.date(now, story["epoch_offset_min"], moments),
                "usage": done.get("usage"),
                "expression": face,
                "mood": gen.get("mind"),
                "thought": gen.get("thought"),
            },
        )


def _minute_now(conn: sqlite3.Connection, story: sqlite3.Row) -> int:
    leaf = story["active_leaf_id"]
    return _minute_of_day(story, chat.get_message(conn, leaf)["story_time"] if leaf else 0)


def read_skip(conn: sqlite3.Connection, story_id: int, words: str) -> int:
    """The minutes that pass in `words` ("the next morning"), read against the story's clock.
    Raises ValueError when no time can be read from them."""
    if not (minutes := clock.parse_skip(words, _minute_now(conn, _story(conn, story_id)))):
        raise ValueError(f"I can't tell how much time passes in “{words}”.")
    return minutes


def say(
    conn: sqlite3.Connection,
    story_id: int,
    text: str | None = None,
    audience: list[int] | None = None,
    skip: str | None = None,
    narrate: bool = False,  # the user tells it rather than their persona saying it
) -> int | None:
    """Write what the user adds, with no reply and no model call: their line (as the persona,
    or unattributed when directing or narrating), a pass of time, or both. Time comes from both
    the line ("six years later, Aren returns") and `skip` ("the next morning"). With only a pass
    of time, a marker line carries it: "— The next morning —". Returns the new message id, or
    None."""
    text, skip = (text or "").strip(), (skip or "").strip()
    if not text and not skip:
        return None
    story = _story(conn, story_id)
    passed = read_skip(conn, story_id, skip) if skip else 0
    if text:
        passed += clock.parse_skip(text, _minute_now(conn, story))
        persona = None if narrate else story["persona_entity_id"]
        return chat.append_message(conn, story_id, "user", text, persona, passed, audience)
    marker = skip.rstrip(".")
    return chat.append_message(
        conn, story_id, "system", f"— {marker[0].upper()}{marker[1:]} —", None, passed
    )


async def _ooc(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    question: str,
    kind: str,
    get_key: Callable[[str], str | None],
    parent_id: int | None = None,  # the question already asked (a retake of the answer)
) -> AsyncIterator[Event]:
    """A sincere out-of-character question, answered out of the fiction (spec §6 rule 3): "are
    you an AI" by the app, truthfully, with no call; anything else by the reply model as itself.
    Both lines are hidden, so no prompt, memory or character ever sees them.
    ponytail: each line still moves the story clock one tick, as any line does."""
    story = _story(conn, story_id)
    if parent_id is None:
        leaf = story["active_leaf_id"]
        persona = story["persona_entity_id"]
        parent_id = chat.add_child(
            conn, story_id, leaf, "user", question, persona, 0, {"ooc": True}
        )
        with conn:
            conn.execute("UPDATE messages SET hidden=1 WHERE id=?", (parent_id,))
    ep = roles.resolve(conn, "rp", story_id, get_key) if kind == "ooc" else None
    if kind == "ooc" and ep is None:
        yield ("error", {"message": "No model is set for the 'rp' role yet."})
        return
    yield (
        "meta",
        {"speaker": None, "role": "ooc", "ooc": True, "model": ep.model if ep else None,
         "thinks": False, "parent_id": parent_id},
    )  # fmt: skip
    text, usage = honesty.AI_ANSWER, None
    if ep is not None:
        path = [m for m in chat.path_to(conn, parent_id) if not m["hidden"]]
        names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)))
        lines = "\n".join(
            f"{names.get(m['speaker_id'], 'Narration')}: {m['text'][-400:]}" for m in path[-6:]
        )
        ask = [
            {"role": "system", "content": honesty.OOC_PROMPT},
            {
                "role": "user",
                "content": (f"[The story so far, for context]\n{lines}\n\n" if lines else "")
                + f"[The user's out-of-character question]\n{question}",
            },
        ]
        parts, done = [], {}
        try:
            async for what, value in llm.chat_stream(ep, ask, max_tokens=400):
                if what == "token":
                    parts.append(value)
                    yield ("token", value)
                elif what == "done":
                    done = value
        except LLMError as e:
            yield ("error", {"message": str(e)})
            return
        said, usage = "".join(parts).strip(), done.get("usage")
        text = said if said and not honesty.HUMAN.search(said) else honesty.AI_ANSWER
    else:
        yield ("token", text)
    gen = {"ooc": True, "role": "ooc", "model": ep.model if ep else None, "usage": usage}
    answer = chat.add_child(conn, story_id, parent_id, "assistant", text, None, 0, gen)
    with conn:
        conn.execute("UPDATE messages SET hidden=1 WHERE id=?", (answer,))
    now = chat.get_message(conn, answer)["story_time"]
    moments = json.loads(story["overrides"]).get("moments", [])
    yield (
        "done",
        {"message_id": answer, "text": text, "ooc": True, "skip_minutes": 0,
         "clock": clock.label(now, story["epoch_offset_min"]),
         "date": clock.date(now, story["epoch_offset_min"], moments), "usage": usage,
         "expression": None, "mood": None, "thought": None},
    )  # fmt: skip


def _is_ooc(conn: sqlite3.Connection, text: str | None) -> str | None:
    """honesty.ooc, when `mind.secrets` is on; a failure means the line goes to the story."""
    try:
        return honesty.ooc(text) if text and features.enabled(conn, "mind.secrets") else None
    except Exception as e:
        logging.getLogger(__name__).warning("ooc check skipped: %s", e)
        return None


async def turn(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    text: str | None = None,
    speaker: int | str | None = None,  # entity id, "narrator", or None to pick automatically
    get_key: Callable[[str], str | None] = roles.get_key,
    audience: list[int] | None = None,  # the user's line: None = everyone present, [] = a thought
    skip: str | None = None,  # time that passes first, in words: "the next morning"
    narrate: bool = False,  # the user's line is narration, not the persona speaking
) -> AsyncIterator[Event]:
    """The user says something (or nothing, to let the story continue) and someone replies."""
    if isinstance(speaker, int):  # asked by name: they must be here, or nothing is written
        path = chat.active_path(conn, story_id)
        if speaker not in {e["id"] for e in _cast(conn, story_id, path)}:
            row = conn.execute("SELECT name FROM entities WHERE id=?", (speaker,)).fetchone()
            name = row["name"] if row else "They"
            yield ("error", {"message": f"{name} isn't in the scene. Bring them in first."})
            return
    if not skip and (kind := _is_ooc(conn, text)):  # step 0: out of the fiction
        async with aclosing(_ooc(conn, llm, story_id, text.strip(), kind, get_key)) as events:
            async for event in events:
                yield event
        return
    try:
        say(conn, story_id, text, audience, skip, narrate)
    except ValueError as e:
        yield ("error", {"message": str(e)})
        return
    speaker_id, why = speaker_why(conn, story_id, speaker)
    parent = _story(conn, story_id)["active_leaf_id"]
    async with aclosing(_generate(conn, llm, story_id, parent, speaker_id, get_key, why)) as events:
        async for event in events:
            yield event


async def regenerate(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    get_key: Callable[[str], str | None] = roles.get_key,
) -> AsyncIterator[Event]:
    """Another take on the last reply, from the same prompt. It becomes a new swipe."""
    leaf_id = _story(conn, story_id)["active_leaf_id"]
    leaf = chat.get_message(conn, leaf_id) if leaf_id else None
    if leaf is None or leaf["role"] != "assistant":
        yield ("error", {"message": "Only a reply can be regenerated."})
        return
    if leaf["parent_id"] is None:
        yield ("error", {"message": "The opening line can't be regenerated. Edit it instead."})
        return
    if json.loads(leaf["gen"] or "{}").get("ooc"):  # an out-of-character answer: answer again
        asked = chat.get_message(conn, leaf["parent_id"])["text"]
        kind = honesty.ooc(asked) or "ooc"
        async with aclosing(
            _ooc(conn, llm, story_id, asked, kind, get_key, leaf["parent_id"])
        ) as events:
            async for event in events:
                yield event
        return
    async with aclosing(
        _generate(conn, llm, story_id, leaf["parent_id"], leaf["speaker_id"], get_key, "retake")
    ) as events:
        async for event in events:
            yield event


async def rewrite(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    message_id: int,
    text: str,
    get_key: Callable[[str], str | None] = roles.get_key,
) -> AsyncIterator[Event]:
    """Edit a line and play on from it: the edited line is a new take beside the old one, and a
    fresh reply follows it. The old line and everything after it stay, a take to flip back to."""
    m = chat.get_message(conn, message_id)
    if m is None or m["story_id"] != story_id or m["role"] == "system":
        yield ("error", {"message": "Only a line in this story can be rewritten."})
        return
    if not text.strip():
        yield ("error", {"message": "Write something, or hide the line instead."})
        return
    take = chat.append_sibling(conn, message_id, text.strip())
    chat.set_leaf(conn, story_id, take)
    speaker_id, why = speaker_why(conn, story_id)
    async with aclosing(_generate(conn, llm, story_id, take, speaker_id, get_key, why)) as events:
        async for event in events:
            yield event
