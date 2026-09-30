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

from kataki import chat, db

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
    """A new version of `goal` with `change` applied, anchored on a message or a run. Inside the
    caller's transaction."""
    g = {**goal, **change}
    return conn.execute(
            "INSERT INTO goals(story_id, entity_id, key, tier, text, cue, priority, progress,"
            " status, tactic, deflections, story_time, message_id, run_id)"
            " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (g["story_id"], g["entity_id"], g["key"], g["tier"], g["text"], json.dumps(g["cue"]),
             g["priority"], round(min(1.0, max(0.0, g["progress"])), 3), g["status"], g["tactic"],
             g["deflections"], now, message_id, run_id),
    ).lastrowid  # fmt: skip


# --- the agenda (note 22 §2 step 7f; §4 row 5) --------------------------------------------------

EVERY = 4  # ponytail: at most one offer every this many of her replies
DROP = 2  # dodged this many times in a row, a goal goes dormant (note 17 §2)
REST = 12 * 60  # ponytail: story minutes a dormant goal rests before it can come back
STEP = 0.25  # ponytail: progress when the user takes it up
LULL = 6  # a line this short with no question is a lull
ASKED = re.compile(
    r"\b(what'?s new|what is new|what'?s up|how are you|how'?ve you been|how have you been"
    r"|what have you been (?:up to|doing)|how was your (?:day|week|morning|night|weekend)"
    r"|anything new|what'?s on your mind|what are you up to|how'?s (?:it going|life|things))\b",
    re.IGNORECASE,
)
PURSUED = ("need", "fear")  # kept, never offered: she does not know she is after them


def tried(text: str, cue: list[str]) -> bool:
    """Whether a line names the goal's topic (a cue word, or its plural)."""
    if not cue:
        return False
    return re.search(rf"\b(?:{'|'.join(map(re.escape, cue))})(?:e?s)?\b", text, re.I) is not None


def opening(text: str, cue: list[str]) -> str | None:
    """Whether the user's line leaves room to bring a goal up: it touches the goal's topic, it
    asks what is new with her, or it is a lull. None: answer it and nothing else."""
    if tried(text, cue):
        return "topic"
    if ASKED.search(text):
        return "asked"
    if len(text.split()) <= LULL and "?" not in text:
        return "lull"
    return None


def _gen(m) -> dict:
    try:
        return json.loads(m["gen"] or "{}")
    except (ValueError, TypeError):
        return {}


def _mine(path: list, who: int) -> list:
    return [m for m in path if m["role"] == "assistant" and m["speaker_id"] == who]


def directive(g: dict, user: str, resurfaced: bool) -> str:
    """The decision for [Directive]: words only, answer first, once, let it go if dodged."""
    if resurfaced:
        return (
            f"Something still on your mind: {g['text']}. You let it drop before, and {user}'s"
            f" line gives you an opening to try again: answer {user} first, then bring it up"
            f" once, lightly. If {user} dodges it again, let it go."
        )
    return (
        f"Something you want: {g['text']}. {user}'s line gives you an opening: answer {user}"
        f" first, then bring it up once, lightly, in your own words. If {user} doesn't take it"
        " up, let it go for now."
    )


def pick(conn: sqlite3.Connection, who: int, path: list, user: str | None) -> dict | None:
    """Step 7f: at most one goal for her agenda this reply, only at an opening in the user's
    line, at most once every EVERY of her replies; a dormant goal only once it has rested.
    -> {"directive", "record", "cue"} or None."""
    if not path or path[-1]["role"] != "user":
        return None
    if path[-1]["id"] not in chat.heard_by(conn, path, who):
        return None  # a whisper to someone else, or a thought: no opening for her
    mine = _mine(path, who)
    offers = [i for i, m in enumerate(mine) if _gen(m).get("agenda")]
    if offers and len(mine) - offers[-1] < EVERY:
        return None
    text, now = path[-1]["text"], path[-1]["story_time"]
    best = None
    for g in live(conn, who, path):
        if g["key"] in PURSUED or g["status"] not in ("active", "dormant"):
            continue
        if g["status"] == "dormant" and now - g["story_time"] < REST:
            continue
        if (why := opening(text, g["cue"])) is None:
            continue
        rank = (why == "topic", g["priority"])
        if best is None or rank > best[0]:
            best = (rank, g, why)
    if best is None:
        return None
    _, g, why = best
    back = g["status"] == "dormant"
    return {
        "directive": directive(g, user or "them", back),
        "record": {"goal": g["id"], "key": g["key"], "text": g["text"], "why": why,
                   "resurfaced": back, "tried": None},
        "cue": g["cue"],
    }  # fmt: skip


OUTCOMES = ("deflected", "progressed", "done")


def _moved(g: dict, outcome: str) -> dict:
    """What an answer does to a goal: a dodge counts (two in a row: dormant), taking it up resets
    the dodges and moves it on, done ends it."""
    if outcome == "deflected":
        n = g["deflections"] + 1
        return {"deflections": n, "status": "dormant" if n >= DROP else g["status"]}
    if outcome == "progressed":
        return {"deflections": 0, "status": "active", "progress": g["progress"] + STEP}
    return {"deflections": 0, "status": "done", "progress": 1.0}


def _answered(path: list, who: int) -> tuple | None:
    """Her latest raise on this path that she tried, and the user's line that answered it, while
    she has not spoken since: (record, the line) or None."""
    mine = _mine(path, who)
    if not mine or not (said := _gen(mine[-1]).get("agenda")) or not said.get("tried"):
        return None
    ids = [m["id"] for m in path]
    after = path[ids.index(mine[-1]["id"]) + 1 :]
    line = next((m for m in after if m["role"] == "user"), None)
    return (said, line) if line is not None else None


def _judge(conn, who: int, path: list, said: dict, line, outcome: str, by: str) -> dict | None:
    """Write (or rewrite) the judgment of `line` for the goal `said` raised, anchored on it."""
    with conn:  # a retake or a relabel replaces the reading of that line, never adds to it
        conn.execute(
            "DELETE FROM goals WHERE entity_id=? AND key=? AND message_id=?",
            (who, said["key"], line["id"]),
        )
    upto = path[: [m["id"] for m in path].index(line["id"]) + 1]
    g = next((g for g in live(conn, who, upto) if g["key"] == said["key"]), None)
    if g is None:
        return None
    with conn:
        write(conn, g, line["id"], None, line["story_time"], **_moved(g, outcome))
    return {"goal": g["id"], "key": g["key"], "text": g["text"], "outcome": outcome, "by": by,
            "line": line["id"]}  # fmt: skip


def judge(conn: sqlite3.Connection, who: int, path: list) -> dict | None:
    """Step 13's goal counters, read from the rules before her next reply: did the user's line
    after her raise take it up (names its topic) or dodge it? -> gen.goal, or None."""
    got = _answered(path, who)
    if got is None:
        return None
    said, line = got
    g = next((g for g in live(conn, who, path) if g["key"] == said["key"]), None)
    if g is None:
        return None
    outcome = "progressed" if tried(line["text"], g["cue"]) else "deflected"
    return _judge(conn, who, path, said, line, outcome, "rules")


def relabel(conn: sqlite3.Connection, who: int, path: list, judged: dict, outcome: str) -> dict:
    """The side call's reading of the answer, in place of the rules'. -> the new gen.goal."""
    line = next(m for m in path if m["id"] == judged["line"])
    return _judge(conn, who, path, judged, line, outcome, "side") or judged


# --- between scenes (note 22 §3: goal_changes, at most one per skip) -----------------------------

CHANGES = ("progressed", "stalled", "done", "dropped", "revived")


def handles(conn: sqlite3.Connection, who: int, path: list) -> dict[str, dict]:
    """The goals the diary call may move: the ones she pursues, still open. {"G14": goal}."""
    return {
        f"G{g['id']}": g
        for g in live(conn, who, path)
        if g["key"] not in PURSUED and g["status"] in ("active", "dormant")
    }


def change(conn, g: dict, how: str, tactic: str | None, message_id: int, run_id: int, now: int):
    """One goal moved by the time that passed, written on the skip's run."""
    moved = {
        "progressed": {"progress": g["progress"] + STEP, "status": "active", "deflections": 0},
        "done": {"progress": 1.0, "status": "done", "deflections": 0},
        "dropped": {"status": "dropped"},
        "revived": {"status": "active", "deflections": 0},
    }.get(how, {})
    if not moved and not tactic:
        return None
    return write(
        conn, g, message_id, run_id, now, **moved, **({"tactic": tactic} if tactic else {})
    )
