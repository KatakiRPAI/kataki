"""One chat turn: who speaks, what they remember, the prompt, the reply.

Everything here is deterministic except the model call. A reply is kept when it finishes,
and also when it is stopped midway: a stopped reply keeps what was written.

Events: ("meta", {...}) first, then ("thought" | "token", text)..., then ("done", {...}) or
("error", {"message": ...}).
"""

import json
import re
import sqlite3
import time
from collections.abc import AsyncIterator, Callable
from contextlib import aclosing
from typing import Any

from kataki import chat, clock, context, embed, extract, images, retrieve, roles
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
    rows = conn.execute(
        f"SELECT entity_id, alias FROM aliases WHERE entity_id IN ({','.join('?' * len(ids))})",
        ids,
    )
    hits = [
        (m.start(), -len(r["alias"]), r["entity_id"])
        for r in rows
        if (m := re.search(rf"(?<!\w){re.escape(r['alias'])}(?!\w)", text, re.IGNORECASE))
    ]
    return min(hits)[2] if hits else None


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


def _unsign(text: str, name: str) -> str:
    """Drop the speaker's own name left dangling after the last sentence ('...due. Mira'):
    small models sign off in the 'Name: line' shape of the history. A name inside a sentence
    stays."""
    pattern = rf"(?:(?<=[.!?\"”*…])\s+|\n+){re.escape(name)}:?\s*$"
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
    row = conn.execute(
        "SELECT l.data FROM entities e JOIN lib_items l ON l.id = e.lib_item_id WHERE e.id=?",
        (speaker_id,),
    ).fetchone()
    if not row or not json.loads(row["data"]).get("pack"):
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
    story = _story(conn, story_id)
    path = chat.path_to(conn, parent_id)
    names = dict(
        conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)).fetchall()
    )

    trace: dict = {"why": why, "ms": {}}
    at = time.monotonic()
    built = context.build(conn, story_id, speaker_id, ep, leaf_id=parent_id)
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
            vector_ranks=await embed.ranks_for(conn, llm, story_id, recent, get_key),
        )
        trace["ms"]["recall"] = ms(at)
        if recalled:
            at = time.monotonic()
            built = context.build(conn, story_id, speaker_id, ep, recalled, leaf_id=parent_id)
            trace["ms"]["prompt"] += ms(at)
            built_recalled = list(recalled)
    log_id = context.log(conn, story_id, None, speaker_id, built)

    name = names.get(speaker_id)
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
    prefix = _Prefix(name or "Narrator")
    finish, error, message_id, text, skip = "stopped", None, None, "", 0
    first_thought = first_token = None  # for think_ms: from the first thought to the first word
    asked = time.monotonic()
    try:
        stream = llm.chat_stream(ep, built.messages, stop=stops, max_tokens=built.response_reserve)
        async with aclosing(stream) as stream:
            async for kind, value in stream:
                if kind == "thought":
                    first_thought = first_thought or time.monotonic()
                    thoughts.append(value)
                    yield ("thought", value)
                elif kind == "token":
                    first_token = first_token or time.monotonic()
                    if value := prefix.feed(value):
                        parts.append(value)
                        yield ("token", value)
                else:
                    done = value
        if rest := prefix.flush():
            parts.append(rest)
            yield ("token", rest)
        finish = "stop"
    except LLMError as e:
        finish, error = "error", str(e)
    finally:  # runs on finish, on error, and when the client stops the stream
        text = _unsign(("".join(parts) + prefix.flush()).strip(), name or "Narrator")
        if text:
            parent_time = chat.get_message(conn, parent_id)["story_time"] if parent_id else 0
            skip = clock.parse_skip(text, _minute_of_day(story, parent_time))
            gen = {
                "role": role,
                "model": ep.model,
                "finish": finish,
                "reasoning": "".join(thoughts) or None,
                "usage": done.get("usage"),
            }
            if first_thought:  # stopped mid-thought: the thinking ran until now
                gen["think_ms"] = round(1000 * ((first_token or time.monotonic()) - first_thought))
            if first_token:
                trace["ms"]["first_token"] = round(1000 * (first_token - asked))
            trace["ms"]["reply"] = ms(asked)
            trace["ms"]["total"] = ms(began)
            gen["trace"] = trace
            message_id = chat.add_child(
                conn, story_id, parent_id, "assistant", text, speaker_id, skip, gen
            )
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
        face = None  # the reply is already on screen; its face follows a moment later
        if speaker_id is not None:
            at = time.monotonic()
            face = await _expression(
                conn, llm, story_id, speaker_id, message_id, name, text, get_key
            )
            if face:  # the face call's time joins the trace
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
