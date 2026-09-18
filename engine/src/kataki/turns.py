"""One chat turn: who speaks, what they remember, the prompt, the reply.

Everything here is deterministic except the model call. A reply is kept when it finishes,
and also when it is stopped midway: a stopped reply keeps what was written.

Events: ("meta", {...}) first, then ("thought" | "token", text)..., then ("done", {...}) or
("error", {"message": ...}).
"""

import json
import re
import sqlite3
from collections.abc import AsyncIterator, Callable
from contextlib import aclosing
from typing import Any

from kataki import chat, clock, context, embed, extract, retrieve, roles
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
    """Who replies (None = the narrator). The UI's pick wins; else whoever the user's line
    addresses; else whoever spoke last. With no user line pending, the quietest character
    speaks, so continuing lets a group take turns. No model call."""
    if requested == NARRATOR:
        return None
    if isinstance(requested, int):
        return requested
    path = chat.active_path(conn, story_id)
    ids = [e["id"] for e in _cast(conn, story_id, path)]
    if not ids:
        return None
    if path and path[-1]["role"] == "user":
        if named := _addressed(conn, path[-1]["text"], ids):
            return named
        last = (m["speaker_id"] for m in reversed(path) if m["role"] == "assistant")
        return next((s for s in last if s in ids), ids[0])
    spoke_at = {m["speaker_id"]: i for i, m in enumerate(path) if m["role"] == "assistant"}
    return min(ids, key=lambda e: spoke_at.get(e, -1))


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
    return re.sub(pattern, "", text).rstrip()


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


async def _generate(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    parent_id: int | None,
    speaker_id: int | None,
    get_key: Callable[[str], str | None],
) -> AsyncIterator[Event]:
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

    built = context.build(conn, story_id, speaker_id, ep, leaf_id=parent_id)
    if speaker_id is not None:
        recent = "\n".join(m["text"] for m in path[-2:])
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
        if recalled:
            built = context.build(conn, story_id, speaker_id, ep, recalled, leaf_id=parent_id)
    log_id = context.log(conn, story_id, None, speaker_id, built)

    name = names.get(speaker_id)
    yield (
        "meta",
        {
            "speaker": {"id": speaker_id, "name": name} if speaker_id is not None else None,
            "role": role,
            "model": ep.model,
            "thinks": ep.thinks,
            "parent_id": parent_id,
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
    try:
        stream = llm.chat_stream(ep, built.messages, stop=stops, max_tokens=built.response_reserve)
        async with aclosing(stream) as stream:
            async for kind, value in stream:
                if kind == "thought":
                    thoughts.append(value)
                    yield ("thought", value)
                elif kind == "token":
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
        yield (
            "done",
            {
                "message_id": message_id,
                "text": text,
                "skip_minutes": skip,
                "clock": clock.label(now, story["epoch_offset_min"]),
                "usage": done.get("usage"),
            },
        )


async def turn(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    text: str | None = None,
    speaker: int | str | None = None,  # entity id, "narrator", or None to pick automatically
    get_key: Callable[[str], str | None] = roles.get_key,
) -> AsyncIterator[Event]:
    """The user says something (or nothing, to let the story continue) and someone replies."""
    story = _story(conn, story_id)
    if text and text.strip():
        leaf = story["active_leaf_id"]
        parent_time = chat.get_message(conn, leaf)["story_time"] if leaf else 0
        skip = clock.parse_skip(text, _minute_of_day(story, parent_time))
        chat.append_message(conn, story_id, "user", text.strip(), story["persona_entity_id"], skip)
    speaker_id = select_speaker(conn, story_id, speaker)
    parent = _story(conn, story_id)["active_leaf_id"]
    async with aclosing(_generate(conn, llm, story_id, parent, speaker_id, get_key)) as events:
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
        _generate(conn, llm, story_id, leaf["parent_id"], leaf["speaker_id"], get_key)
    ) as events:
        async for event in events:
            yield event
