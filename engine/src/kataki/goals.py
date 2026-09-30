"""What a character wants (docs/specs/2026-09-29-minds.md, slice 7; note 22 §1-§2, note 17 §2).

The card's `want` (and any listed `goals`) are goals she pursues; her `need` and `fear` are kept
but never pursued (she does not know she is after them). Each goal is a line of versions per
`key` in `goals`, anchored like every minds table, so swipes and branches swap them. At a natural
opening code may put one goal on her agenda (in [Directive]); the user's answer is judged, and a
goal dodged twice goes dormant until it has rested. Zero model calls; the side call may relabel.

ponytail: every constant here is an estimate from the research (note 17 §2: "once per N turns",
"two deflections"); tune them on the probes (evals/probes.py P10), not by feel.
"""

import json
import logging
import re
import sqlite3

from kataki import db

TIERS = ("ambition", "project", "today")
STATUSES = ("active", "dormant", "done", "failed", "dropped")
STOP = frozenset(
    "the and for with that this from into onto about again away back been being come comes could"
    " does done down each even ever from gets give goes going have having here just keep know"
    " like make more most much must need needs never once only other over really said same see"
    " seen she her him his they them their then there these those thing things very want wants"
    " was were what when where which while who whom why will with would you your get got let"
    " yet not but can all any too its it's our out off one own".split()
)


def cues(text: str, names: set[str] = frozenset()) -> list[str]:
    """The words that put a goal on the table: its content words, without small words and
    people's names. ponytail: words only, no embedder (a reworded topic can miss)."""
    words = re.findall(r"[a-z]+", text.lower())
    out = [w for w in words if len(w) >= 3 and w not in STOP and w not in names]
    return list(dict.fromkeys(out))


def _text(value) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _listed(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [w.strip().lower() for w in value if isinstance(w, str) and w.strip()]


def seed(conn: sqlite3.Connection, story_id: int, cast: list[tuple[dict, int]]) -> None:
    """Each card's `want`, `need`, `fear` and `goals` into the new story, as the user's own rows
    (no anchor). Inside the caller's transaction. A malformed entry is skipped, never fatal."""
    names = {
        w
        for (n,) in conn.execute("SELECT name FROM entities WHERE story_id=?", (story_id,))
        for w in re.findall(r"[a-z]+", n.lower())
    }
    for item, who in cast:
        mind = item["data"].get("mind")
        if not isinstance(mind, dict):
            continue
        want = mind.get("want")
        wanted = [
            ("want", _text(want.get("text")) if isinstance(want, dict) else _text(want),
             _listed(want.get("cue")) if isinstance(want, dict) else [], "project", 0.7, "active"),
            ("need", _text(mind.get("need")), [], "ambition", 0.5, "dormant"),
            ("fear", _text(mind.get("fear")), [], "ambition", 0.5, "dormant"),
        ]  # fmt: skip
        listed = mind.get("goals") if isinstance(mind.get("goals"), list) else []
        for n, g in enumerate(
            (g for g in listed if isinstance(g, dict) and _text(g.get("text"))), 1
        ):
            p = g.get("priority")
            ok = isinstance(p, (int, float)) and not isinstance(p, bool) and 0 <= p <= 1
            tier = g.get("tier") if g.get("tier") in TIERS else "project"
            wanted.append((f"g{n}", _text(g["text"]), _listed(g.get("cue")), tier,
                           p if ok else 0.5, "active"))  # fmt: skip
        for key, text, cue, tier, priority, status in wanted:
            if not text:
                continue
            try:
                conn.execute(
                    "INSERT INTO goals(story_id, entity_id, key, tier, text, cue, priority, status,"
                    " story_time) VALUES(?, ?, ?, ?, ?, ?, ?, ?, 0)",
                    (story_id, who, key, tier, text, json.dumps(cue or cues(text, names)),
                     priority, status),
                )  # fmt: skip
            except Exception as e:
                logging.getLogger(__name__).warning("goal %s skipped for %s: %s", key, who, e)


def _row(r: sqlite3.Row) -> dict:
    out = dict(r)
    try:
        out["cue"] = json.loads(r["cue"]) if r["cue"] else []
    except ValueError:
        out["cue"] = []
    return out


def live(conn: sqlite3.Connection, who: int, path: list) -> list[dict]:
    """Her goals on this branch: the latest live version of each key (written by the user, on a
    line of `path`, or by a live run), by story time. Oldest key first."""
    runs = db.live_runs(conn, path[-1]["story_id"], path[-1]["id"]) if path else set()
    where, args = db.anchor_filter(runs, {m["id"] for m in path})
    now = path[-1]["story_time"] if path else 0
    rows = conn.execute(
        f"SELECT * FROM goals WHERE entity_id=? AND story_time<=? AND {where}"
        " ORDER BY story_time, id",
        [who, now, *args],
    ).fetchall()
    latest: dict[str, dict] = {}
    for r in rows:
        latest[r["key"]] = _row(r)  # a key keeps its first place; its value is the newest
    return list(latest.values())


def write(conn: sqlite3.Connection, goal: dict, message_id: int | None, run_id: int | None,
          now: int, **change) -> int:  # fmt: skip
    """A new version of `goal` with `change` applied, anchored on a message or a run."""
    g = {**goal, **change}
    with conn:
        return conn.execute(
            "INSERT INTO goals(story_id, entity_id, key, tier, text, cue, priority, progress,"
            " status, tactic, deflections, story_time, message_id, run_id)"
            " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (g["story_id"], g["entity_id"], g["key"], g["tier"], g["text"], json.dumps(g["cue"]),
             g["priority"], round(min(1.0, max(0.0, g["progress"])), 3), g["status"], g["tactic"],
             g["deflections"], now, message_id, run_id),
        ).lastrowid  # fmt: skip
