"""How a character changes, slowly (docs/specs/2026-09-29-minds.md, slice 8; note 22 §1, §3 B2).

After a big skip the Between call she already makes grows a deep section: how she has come to
see the people closest to her, a line about herself, up to two candidate growth rings, each
citing the memories it rests on. Code gates every line mechanically (cited handles only, no new
names or numbers, hard length caps) and drops what fails with a warning. A ring enters as a seed
and takes hold only when later scenes bear it out; only then may it nudge one personality axis,
by a step code sets and caps, in this story only. Every row is a version (`supersedes_id`),
anchored like every minds table; the user accepts, rejects or locks with rows of their own.

ponytail: every constant here is an estimate from the research (note 12 §7, note 17 §6: "3
memories from 2 scenes", "±2 per step, ±10 per arc"); tune them on the probes, not by feel.
"""

import json
import re
import sqlite3

from kataki import chat, clock, db, features

RINGS = ("stance", "habit", "skill", "scar", "belief")
LINES = ("self", "relationship")
STATUSES = ("seed", "ring", "fading", "past", "rejected", "locked")
COUNTS = ("ring", "locked")  # the statuses whose trait nudge applies
TRAITS = {  # the direction the model may name -> (axis, sign); code sets the size
    "warmer": ("warmth", 1), "colder": ("warmth", -1),
    "bolder": ("dominance", 1), "meeker": ("dominance", -1),
    "franker": ("candor", 1), "more_guarded": ("candor", -1),
    "more_honest": ("honesty", 1), "less_honest": ("honesty", -1),
    "softer": ("yielding", 1), "firmer": ("yielding", -1),
    "calmer": ("volatility", -1), "touchier": ("volatility", 1),
}  # fmt: skip
STEP = 2  # ponytail: axis points one ring moves (note 12 §7: "±2 per axis per window")
CAP = 10  # ponytail: the most all rings together move one axis (note 12 §7: "±10 per arc")
WORDS = {"relationship": 25, "self": 80, "ring": 15}  # hard caps (note 22 §3)
SENTENCES = 6  # the self line
EVIDENCE, SCENES = 3, 2  # a ring rests on this many memories from this many scenes (note 17 §6)
NUMBERS = frozenset(
    "one two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty"
    " hundred thousand million once twice".split()
)
ME = frozenset({"i", "i'm", "i've", "i'd", "i'll"})


# --- the gate (note 14 §6): every item, before it becomes a row --------------------------------


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'’-]*|\d+", text)


def _new_name(line: str, allowed: set[str]) -> str | None:
    """A capitalised word that is not a sentence's first word, not "I", and not a name or word
    the call was shown: a new proper noun."""
    for sentence in re.split(r"(?<=[.!?:;—])\s+", line):
        for i, w in enumerate(_words(sentence.strip(" \"'“”‘’*("))):
            if i and w[0].isupper() and w.lower() not in ME and w.lower() not in allowed:
                return w
    return None


def _new_number(line: str, cited: str) -> str | None:
    """A digit or number word that is not in the memories the line cites."""
    have = {w.lower() for w in _words(cited)}
    return next((w for w in _words(line) if (w.isdigit() or w.lower() in NUMBERS)
                 and w.lower() not in have), None)  # fmt: skip


def gate(item: dict, kind: str, memories: dict[str, dict], people: dict[str, int],
         names: set[str]) -> str | None:  # fmt: skip
    """Why one item of the deep section may not become a row, or None when it passes. `kind`:
    "relationship", "self" or "ring"; `memories`: the handles it was shown ({"M31": {"id",
    "text", "scene"}}); `people`: its person handles; `names`: lower-case names in the story."""
    line = item.get("claim" if kind == "ring" else "line")
    sources = item.get("sources")
    if not isinstance(line, str) or not line.strip():
        return "it was empty"
    if not isinstance(sources, list) or not sources:
        return "it cited no source"
    if bad := [s for s in sources if s not in memories]:
        return f"it cited an unknown memory ({bad[0]})"
    if kind == "relationship" and item.get("about") not in people:
        return "it was about someone it was not shown"
    if len(line.split()) > WORDS[kind] or (
        kind == "self" and len(re.findall(r"[.!?]+(?:\s|$)", line.strip())) > SENTENCES
    ):
        return "it was too long"
    cited = " ".join(memories[s]["text"] for s in sources)
    if n := _new_number(line, cited):
        return f'it added a number ("{n}")'
    shown = {w.lower() for m in memories.values() for w in _words(m["text"])}
    if w := _new_name(line, names | shown):
        return f'it named someone or something her memories don\'t ("{w}")'
    if kind == "ring":
        seen = {s for s in sources}
        if len(seen) < EVIDENCE or len({memories[s]["scene"] for s in seen}) < SCENES:
            return "it had too little evidence (three memories from two scenes)"
    return None


# --- trait drift: code's, capped, reversible ------------------------------------------------------


def step(trait) -> dict | None:
    """The nudge a ring's direction carries: one axis, STEP points. None for none or unknown."""
    if trait not in TRAITS:
        return None
    axis, sign = TRAITS[trait]
    return {axis: sign * STEP}


def drift(rows: list[dict]) -> dict[str, int]:
    """What current rings add to each axis: rings and locked ones only, capped per axis."""
    out: dict[str, float] = {}
    for r in rows:
        if r["status"] in COUNTS and isinstance(r.get("trait_delta"), dict):
            for axis, d in r["trait_delta"].items():
                if isinstance(d, (int, float)) and not isinstance(d, bool):
                    out[axis] = out.get(axis, 0) + d
    return {a: int(max(-CAP, min(CAP, v))) for a, v in out.items() if v}


# --- rows -----------------------------------------------------------------------------------------


def _row(r: sqlite3.Row) -> dict:
    out = dict(r)
    for key in ("sources", "trait_delta"):
        try:
            out[key] = json.loads(r[key]) if r[key] else ([] if key == "sources" else None)
        except ValueError:
            out[key] = [] if key == "sources" else None
    return out


def live(conn: sqlite3.Connection, who: int, path: list) -> list[dict]:
    """Every live row of hers on this branch (the user's own, on a line of `path`, or on a live
    run), oldest first."""
    runs = db.live_runs(conn, path[-1]["story_id"], path[-1]["id"]) if path else set()
    where, args = db.anchor_filter(runs, {m["id"] for m in path})
    return [
        _row(r)
        for r in conn.execute(
            f"SELECT * FROM reflections WHERE knower_id=? AND {where} ORDER BY id", [who, *args]
        )
    ]


def current(conn: sqlite3.Connection, who: int, path: list) -> list[dict]:
    """Her reflections as they stand: live rows no live row supersedes, newest first."""
    rows = live(conn, who, path)
    gone = {r["supersedes_id"] for r in rows if r["supersedes_id"] is not None}
    return [r for r in reversed(rows) if r["id"] not in gone]


def write(conn, story_id: int, who: int, kind: str, text: str, sources: list[int], status: str,
          now: int, *, subject: int | None = None, delta: dict | None = None,
          supersedes: int | None = None, message_id: int | None = None,
          run_id: int | None = None) -> int:  # fmt: skip
    """One row, inside the caller's transaction."""
    return conn.execute(
        "INSERT INTO reflections(story_id, knower_id, kind, subject_id, text, sources, status,"
        " trait_delta, supersedes_id, story_time, message_id, run_id)"
        " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (story_id, who, kind, subject, text, json.dumps(sources), status,
         json.dumps(delta) if delta else None, supersedes, now, message_id, run_id),
    ).lastrowid  # fmt: skip


def again(conn, r: dict, status: str, now: int, message_id=None, run_id=None) -> int:
    """A new version of `r` with another status (inside the caller's transaction)."""
    return write(conn, r["story_id"], r["knower_id"], r["kind"], r["text"], r["sources"], status,
                 now, subject=r["subject_id"], delta=r["trait_delta"], supersedes=r["id"],
                 message_id=message_id, run_id=run_id)  # fmt: skip


ACTIONS = {"accept": "ring", "reject": "rejected", "lock": "locked"}


def act(conn: sqlite3.Connection, reflection_id: int, action: str) -> int:
    """The user's say (§6 rule 6): a new, unanchored version, so it holds on every branch. The
    row it supersedes is never touched. -> the new row's id."""
    if action not in ACTIONS:
        raise ValueError(f"unknown action {action!r}")
    r = conn.execute("SELECT * FROM reflections WHERE id=?", (reflection_id,)).fetchone()
    if r is None:
        raise KeyError(reflection_id)
    last = conn.execute(
        "SELECT MAX(story_time) FROM messages WHERE story_id=?", (r["story_id"],)
    ).fetchone()[0]
    with conn:
        return again(conn, _row(r), ACTIONS[action], max(last or 0, r["story_time"]))


def profile_drift(conn: sqlite3.Connection, who: int) -> dict[str, int]:
    """The capped drift her current rings give her on the active branch (inner.profile adds it).
    Cheap when she has no nudge at all (the usual case): one indexed query."""
    row = conn.execute(
        "SELECT story_id FROM reflections WHERE knower_id=? AND trait_delta IS NOT NULL LIMIT 1",
        (who,),
    ).fetchone()
    if row is None or not features.enabled(conn, "mind.growth"):
        return {}
    return drift(current(conn, who, chat.active_path(conn, row[0])))


def since(r: dict, epoch: int) -> str:
    return clock.label(r["story_time"], epoch)
