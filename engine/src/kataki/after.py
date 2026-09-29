"""One small labelling call after the reply (docs/specs/2026-09-29-minds.md §3; note 22 §2
step 12): what the speaker felt, what was done to them and by whom, the stance they took,
whether they gave way, and the face they said it with. It replaces the face call, so a
character with sprites costs no extra call. Closed lists only: the model labels, code decides
what the labels do.

Standard and premium only; lite reads all of it by rules. Anything that goes wrong costs only
this call: the turn keeps what the rules read (`gen.after = "skipped"`).
"""

import json
import logging
import sqlite3
import time
from collections.abc import Callable

from kataki import bonds, chat, features, images, inner, knobs, roles
from kataki.llm import LLM

PROMPT = """\
You label one exchange from a roleplay for the app that keeps the character's mind. Use only \
the values the schema allows.
Judge felt and events from THE LINE ONLY (the one marked as the line to judge); the lines \
before it are context, and the character's reply is NOT evidence for either. Ordinary talk, \
greetings, questions and small talk do nothing: for those return events [] and felt as calm, \
intensity 1. Only label an event the line itself clearly does.
- felt: how that line made the character feel (not how they felt already, and not a feeling \
that only carries on from before). intensity: 1 a little, 2 clearly, 3 very. about: the \
handle of the person it is about, or null. cause: at most 12 words.
- events: at most 3 things another person did to the character in that line only, never in \
earlier ones: that person's handle (target), what it was (type) and how much (intensity \
1-3). An apology is apology_sincere only if it owns what was done; otherwise apology_hollow. \
Leave it empty when the line did nothing new.
From the character's reply only (not for felt or events):
- position: a stance the character took or kept in the reply (at most 12 words; firm 1-3), \
or null.
- yielded: true only if the character gave in on a position, or to what someone pushed for.
- face: the character's facial expression while saying the reply."""
REPEAT_MIN = (
    60  # ponytail: the same event toward the same person within this many story minutes is an echo
)
FELT = {1: 0.3, 2: 0.6, 3: 0.9}  # ponytail: intensity words -> the affect core's 0-1


def wanted(conn: sqlite3.Connection) -> bool:
    """Standard and premium ask the side call; lite reads everything by rules (spec §3)."""
    level = knobs.setting(conn, "mind.level", "standard")
    return features.enabled(conn, "mind.bonds") and level != "lite"


def schema(handles: list[str]) -> dict:
    """The labels, every list closed: feelings, events, faces, and only the people here."""
    level = {"type": "integer", "enum": [1, 2, 3]}
    return {
        "type": "object",
        "properties": {
            "felt": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "enum": list(inner.FEEL)},
                    "intensity": level,
                    "about": {"type": ["string", "null"], "enum": [*handles, None]},
                    "cause": {"type": "string"},
                },
                "required": ["label", "intensity", "about", "cause"],
                "additionalProperties": False,
            },
            "events": {
                "type": "array",
                "maxItems": 3 if handles else 0,
                "items": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "enum": handles or ["none"]},
                        "type": {"type": "string", "enum": list(bonds.EVENTS)},
                        "intensity": level,
                    },
                    "required": ["target", "type", "intensity"],
                    "additionalProperties": False,
                },
            },
            "position": {
                "anyOf": [
                    {"type": "null"},
                    {
                        "type": "object",
                        "properties": {"text": {"type": "string"}, "firm": level},
                        "required": ["text", "firm"],
                        "additionalProperties": False,
                    },
                ]
            },
            "yielded": {"type": "boolean"},
            "face": {"type": "string", "enum": list(images.EXPRESSIONS)},
        },
        "required": ["felt", "events", "position", "yielded", "face"],
        "additionalProperties": False,
    }


def _level(x) -> bool:
    return type(x) is int and 1 <= x <= 3


def _word(x, allowed) -> bool:
    return isinstance(x, str) and x in allowed


def read(data: dict, handles: list[str]) -> dict:
    """Validate the labels. Unusable as a whole (no feeling from the list, no face) raises
    ValueError, so the model is asked once more; a bad event is only dropped."""
    felt = data.get("felt")
    if not isinstance(felt, dict) or not _word(felt.get("label"), inner.FEEL):
        raise ValueError(f"felt.label must be one of {', '.join(inner.FEEL)}")
    if not _level(felt.get("intensity")):
        raise ValueError("felt.intensity must be 1, 2 or 3")
    if not _word(data.get("face"), images.EXPRESSIONS):
        raise ValueError(f"face must be one of {', '.join(images.EXPRESSIONS)}")
    events = data.get("events") if isinstance(data.get("events"), list) else []
    pos = data.get("position")
    text = pos.get("text") if isinstance(pos, dict) else None
    return {
        "felt": {
            "label": felt["label"],
            "intensity": felt["intensity"],
            "about": felt.get("about") if _word(felt.get("about"), handles) else None,
            "cause": str(felt.get("cause") or "")[:80],
        },
        "events": [
            {"target": e["target"], "type": e["type"], "intensity": e["intensity"]}
            for e in events[:3]
            if isinstance(e, dict)
            and _word(e.get("target"), handles)
            and _word(e.get("type"), bonds.EVENTS)
            and _level(e.get("intensity"))
        ],
        "position": (
            {"text": text.strip()[:80], "firm": pos["firm"]}
            if isinstance(text, str) and text.strip() and _level(pos.get("firm"))
            else None
        ),
        "yielded": data.get("yielded") is True,
        "face": data["face"],
    }


def _scene(conn: sqlite3.Connection, story_id: int, path: list, speaker_id: int) -> dict:
    """Who the call may name, and the line the speaker answered (only if it reached them)."""
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)))
    persona = conn.execute(
        "SELECT persona_entity_id FROM stories WHERE id=?", (story_id,)
    ).fetchone()[0]
    scene_id = chat.scene_of(conn, story_id, path)
    here = [e["id"] for e in chat.present_entities(conn, scene_id, path) if e["id"] != speaker_id]
    last = path[-1] if path and path[-1]["speaker_id"] != speaker_id else None
    if last is not None and last["id"] not in chat.heard_by(conn, path, speaker_id):
        last = None  # a whisper to someone else, or a thought: not something done to them
    before = path[-3:-1] if last is not None else []  # context only: at most 2 lines before it
    return {
        "names": names,
        "persona": persona,
        "scene_id": scene_id,
        "here": here,
        "last": last,
        "before": before,
    }


async def _ask(
    conn, llm: LLM, story_id: int, speaker_id: int, reply: str, seen: dict, get_key
) -> dict | None:
    if (ep := roles.resolve(conn, "utility", story_id, get_key)) is None:
        return None
    names, last = seen["names"], seen["last"]
    handles = [f"E{i}" for i in seen["here"]]
    people = "; ".join(
        f"E{i} = {names[i]}" + (" (the user)" if i == seen["persona"] else "") for i in seen["here"]
    )
    name = names[speaker_id]
    line = (
        f"{names.get(last['speaker_id'], 'Narration')}: {last['text'][-1200:]}"
        if last is not None
        else "(nothing new)"
    )
    context = "".join(
        f"{names.get(m['speaker_id'], 'Narration')}: {m['text'][-400:]}\n" for m in seen["before"]
    )
    ask = [
        {"role": "system", "content": PROMPT},
        {
            "role": "user",
            "content": f"The character: {name}. People here: {people or 'no one else'}.\n\n"
            + (f"[Earlier lines, context only]\n{context}\n" if context else "")
            + f"[The line to judge: what did THIS line do to {name}?]\n{line}\n\n"
            f"[{name}'s reply: for position, yielded and face only]\n{reply[-1500:]}",
        },
    ]
    return await llm.complete_json(
        ep, ask, schema(handles), lambda d: read(d, handles), name="after"
    )


def _apply(
    conn, story_id: int, path: list, speaker_id: int, message_id: int, got: dict, state, seen
) -> None:
    """What the labels do, decided by code: the feeling into the affect core, the ground they
    held or gave into their state, and the events into the ledger in place of the rules'."""
    now = path[-1]["story_time"] if path else 0
    prof, felt = inner.profile(conn, speaker_id), got["felt"]
    last = seen["last"]
    # Only a user line is something that just happened; the model's label of the character's
    # own reply otherwise echoes the mood the reply was written from (spec §3, note 22 C8).
    fresh = last is not None and last["role"] == "user"
    rows, new, taken, seen_ev = bonds.ledger(conn, speaker_id, path), [], 0, set()
    dial = knobs.dial(conn, speaker_id, "relationships", "realistic")
    if dial not in bonds.HARSH:  # a stray value must never break a turn
        dial = "realistic"
    for e in got["events"] if fresh else []:
        dst = int(e["target"][1:])
        if (dst, e["type"]) in seen_ev or any(
            r["dst_id"] == dst and r["event"] == e["type"] and now - r["story_time"] < REPEAT_MIN
            for r in rows
        ):
            continue  # said twice, or already held from a moment ago: the echo of an old line
        seen_ev.add((dst, e["type"]))
        taken += 1
        if felt["about"] == e["target"] and felt["cause"]:
            cause = felt["cause"]
        elif last["speaker_id"] == dst:
            cause = inner.said(seen["names"][dst], last["text"])
        else:
            cause = e["type"].replace("_", " ")
        new += bonds.apply(
            rows + new, dst, e["type"], e["intensity"], cause, now, seen["scene_id"], prof, dial
        )
    ruled = conn.execute(
        "SELECT COUNT(*) FROM opinions WHERE src_id=? AND message_id=?", (speaker_id, message_id)
    ).fetchone()[0]
    felt_now = fresh and (taken or ruled)  # a feeling with no event behind it is the echo
    if state is not None and (felt_now or got["position"] or got["yielded"]):  # moods are on
        st = state
        if felt_now:  # re-read the line from before the rules appraised it: felt once, not twice
            before = inner.current(conn, speaker_id, path, prof) or inner.fresh(prof, now)
            cause = felt["cause"] or "that exchange"
            st = inner.tick(before, now, prof)
            st = inner.regulate(
                inner.feel(st, felt["label"], FELT[felt["intensity"]], cause, prof), prof
            )
        st = bonds.took(st, got["position"], got["yielded"], seen["scene_id"], now)
        with conn:  # this reply's row is replaced, not added to
            conn.execute(
                "DELETE FROM mind_states WHERE entity_id=? AND message_id=?",
                (speaker_id, message_id),
            )
            inner.save(conn, {speaker_id: st}, message_id)
            conn.execute(  # the reply shows the mood just saved, not the rules' first read
                "UPDATE messages SET gen=json_set(gen, '$.mind', json(?)) WHERE id=?",
                (json.dumps(inner.public(st, prof)), message_id),
            )
    if taken:  # else the rules' rows for this line (if any) stay
        bonds.replace(conn, story_id, speaker_id, message_id, new)


async def run(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    path: list,  # the branch up to the line that was answered (not the reply)
    speaker_id: int,
    message_id: int,  # the reply
    reply: str,
    state: dict | None,  # the speaker's state before the reply (None: moods are off)
    get_key: Callable[[str], str | None],
) -> dict | None:
    """The side call for one reply, applied. -> the labels, or None when it was skipped.
    ponytail: inline after the reply, before `done`, as the face call ran; move it to a
    preemptible worker if `done` arriving 1-3 s after the last token shows in the metrics."""
    at, got = time.monotonic(), None
    try:
        seen = _scene(conn, story_id, path, speaker_id)
        got = await _ask(conn, llm, story_id, speaker_id, reply, seen, get_key)
        if got is not None:
            _apply(conn, story_id, path, speaker_id, message_id, got, state, seen)
    except Exception as e:  # never a turn's undoing: the rules' reading stays
        logging.getLogger(__name__).warning("side call skipped for story %s: %s", story_id, e)
        got = None
    try:
        with conn:
            conn.execute(
                "UPDATE messages SET gen=json_set(gen, '$.after', json(?), '$.trace.ms.after', ?)"
                " WHERE id=?",
                (json.dumps(got or "skipped"), round(1000 * (time.monotonic() - at)), message_id),
            )
    except Exception as e:
        logging.getLogger(__name__).warning("side call not recorded: %s", e)
    return got
