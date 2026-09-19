"""The message tree. A story is a tree of messages; the active path is leaf -> root.

Swipes and regenerations are siblings, a branch is just another leaf, and nothing is ever
deleted. Memory rows follow the branch they were extracted on (see extract.py), so
switching leaf is free.
"""

import json
import sqlite3

from kataki import db

_UP = (
    "WITH RECURSIVE up(id, parent_id) AS ("
    " SELECT id, parent_id FROM messages WHERE id=?"
    " UNION ALL SELECT m.id, m.parent_id FROM messages m JOIN up ON m.id=up.parent_id) "
)


def get_message(conn: sqlite3.Connection, message_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
    if row is None:
        raise ValueError(f"no message {message_id}")
    return row


def _set_active(conn: sqlite3.Connection, story_id: int, message_id: int) -> None:
    conn.execute("UPDATE stories SET active_leaf_id=? WHERE id=?", (message_id, story_id))


def path_to(conn: sqlite3.Connection, message_id: int | None) -> list[sqlite3.Row]:
    """Root -> message. Ids only grow along a path, so ordering by id is ordering by depth."""
    sql = _UP + "SELECT * FROM messages WHERE id IN (SELECT id FROM up) ORDER BY id"
    return conn.execute(sql, (message_id,)).fetchall()


def active_path(conn: sqlite3.Connection, story_id: int) -> list[sqlite3.Row]:
    story = conn.execute("SELECT active_leaf_id FROM stories WHERE id=?", (story_id,)).fetchone()
    return path_to(conn, story["active_leaf_id"])


def scene_of(conn: sqlite3.Connection, story_id: int, path: list) -> int | None:
    """The scene at the end of a path; before any message, the story's first scene."""
    if path and path[-1]["scene_id"] is not None:
        return path[-1]["scene_id"]
    first = conn.execute(
        "SELECT id FROM scenes WHERE story_id=? ORDER BY id LIMIT 1", (story_id,)
    ).fetchone()
    return first["id"] if first else None


# Presence rule, used everywhere: rows with no message are the scene's opening roster (the
# last one per entity wins); a row keyed to a message takes effect right AFTER that message,
# and only on the branch that message is on.


def present_entities(conn: sqlite3.Connection, scene_id: int | None, path: list) -> list:
    """Who is in the scene at the end of `path`."""
    rows = conn.execute(
        "SELECT p.id AS presence_id, p.entity_id, p.present, p.message_id, e.* FROM presence p"
        " JOIN entities e ON e.id=p.entity_id WHERE p.scene_id IS ? ORDER BY p.id",
        (scene_id,),
    ).fetchall()
    order = {m["id"]: i for i, m in enumerate(path)}
    state = {r["id"]: r for r in rows if r["message_id"] is None}
    keyed = [r for r in rows if r["message_id"] in order]
    for r in sorted(keyed, key=lambda r: (order[r["message_id"]], r["presence_id"])):
        state[r["id"]] = r
    return [r for r in state.values() if r["present"]]


def audience_of(message) -> list[int] | None:
    """Who a line was for: None = everyone present, a list = a whisper, [] = a thought."""
    return None if message["audience"] is None else json.loads(message["audience"])


def heard_by(conn: sqlite3.Connection, path: list, entity_id: int) -> set[int]:
    """The messages on this path that reached the entity: what they said, and what was said
    while they were there, unless it was whispered to someone else or only thought."""
    rows = conn.execute(
        "SELECT scene_id, message_id, present FROM presence WHERE entity_id=? ORDER BY id",
        (entity_id,),
    ).fetchall()
    opening = {r["scene_id"]: r["present"] for r in rows if r["message_id"] is None}
    changes = {r["message_id"]: r["present"] for r in rows if r["message_id"] is not None}
    heard, scene, here = set(), object(), False
    for m in path:
        if m["scene_id"] != scene:
            scene, here = m["scene_id"], bool(opening.get(m["scene_id"]))
        audience = audience_of(m)
        if m["speaker_id"] == entity_id or (here and (audience is None or entity_id in audience)):
            heard.add(m["id"])
        here = bool(changes.get(m["id"], here))
    return heard


def set_presence(conn: sqlite3.Connection, story_id: int, entity_id: int, present: bool) -> None:
    """Someone arrives or leaves now: the change takes effect after the current message."""
    path = active_path(conn, story_id)
    with conn:
        conn.execute(
            "INSERT INTO presence(scene_id, entity_id, message_id, present) VALUES(?, ?, ?, ?)",
            (scene_of(conn, story_id, path), entity_id, path[-1]["id"] if path else None, present),
        )


def _insert(
    conn, story_id, parent_id, role, speaker_id, text, story_time, skip, scene, gen, audience
):
    message_id = conn.execute(
        "INSERT INTO messages(story_id, parent_id, role, speaker_id, text, story_time,"
        " skip_minutes, scene_id, gen, audience) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (story_id, parent_id, role, speaker_id, text, story_time, skip, scene, gen, audience),
    ).lastrowid
    _set_active(conn, story_id, message_id)
    return message_id


def add_child(
    conn: sqlite3.Connection,
    story_id: int,
    parent_id: int | None,
    role: str,
    text: str,
    speaker_id: int | None = None,
    skip_minutes: int = 0,
    gen: dict | None = None,
    scene_id: int | None = None,  # default: the parent's scene
    audience: list[int] | None = None,  # None = everyone present; see audience_of
) -> int:
    """Add a message under `parent_id` and make it the active leaf. The story clock moves
    one tick past the parent, plus any skip."""
    with conn:
        story = conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()
        parent = get_message(conn, parent_id) if parent_id else None
        scene = scene_id or scene_of(conn, story_id, [parent] if parent else [])
        now = (parent["story_time"] if parent else 0) + story["minutes_per_turn"] + skip_minutes
        return _insert(
            conn,
            story_id,
            parent_id,
            role,
            speaker_id,
            text,
            now,
            skip_minutes,
            scene,
            json.dumps(gen) if gen else None,
            None if audience is None else json.dumps(audience),
        )


def append_message(
    conn: sqlite3.Connection,
    story_id: int,
    role: str,
    text: str,
    speaker_id: int | None = None,
    skip_minutes: int = 0,
    audience: list[int] | None = None,
) -> int:
    """Add a message under the active leaf."""
    leaf = conn.execute("SELECT active_leaf_id FROM stories WHERE id=?", (story_id,)).fetchone()
    return add_child(
        conn, story_id, leaf[0], role, text, speaker_id, skip_minutes, audience=audience
    )


def append_sibling(conn: sqlite3.Connection, message_id: int, text: str) -> int:
    """A swipe: same place in the tree and on the clock, different text."""
    with conn:
        m = get_message(conn, message_id)
        return _insert(
            conn,
            m["story_id"],
            m["parent_id"],
            m["role"],
            m["speaker_id"],
            text,
            m["story_time"],
            m["skip_minutes"],
            m["scene_id"],
            None,
            m["audience"],  # another take on a whisper is still a whisper
        )


def sibling_position(conn: sqlite3.Connection, message_id: int) -> tuple[int, int]:
    """(index, count) among the alternatives at this point, for the swipe arrows. 1-based."""
    m = get_message(conn, message_id)
    ids = [
        r["id"]
        for r in conn.execute(
            "SELECT id FROM messages WHERE story_id=? AND parent_id IS ? ORDER BY id",
            (m["story_id"], m["parent_id"]),
        )
    ]
    return ids.index(message_id) + 1, len(ids)


def set_leaf(conn: sqlite3.Connection, story_id: int, message_id: int) -> int:
    """Switch branch. Picking a message resumes at the newest leaf beneath it."""
    if get_message(conn, message_id)["story_id"] != story_id:
        raise ValueError(f"message {message_id} belongs to another story")
    leaf = message_id
    while child := conn.execute(
        "SELECT max(id) AS id FROM messages WHERE parent_id=?", (leaf,)
    ).fetchone()["id"]:
        leaf = child
    with conn:
        _set_active(conn, story_id, leaf)
    return leaf


def edit_message(conn: sqlite3.Connection, message_id: int, text: str) -> None:
    """Fix text in place: a typo must not fork the story. Runs that read it go stale."""
    with conn:
        m = get_message(conn, message_id)
        conn.execute(
            "UPDATE messages SET text=?, edited_at=CURRENT_TIMESTAMP WHERE id=?", (text, message_id)
        )
        runs = conn.execute(
            "SELECT id, to_message_id FROM extraction_runs"
            " WHERE story_id=? AND from_message_id<=? AND to_message_id>=?",
            (m["story_id"], message_id, message_id),
        ).fetchall()
        for run in runs:  # the id range is only a prefilter: the run must be on this branch
            covered = conn.execute(
                _UP + "SELECT 1 FROM up WHERE id=?", (run["to_message_id"], message_id)
            ).fetchone()
            if covered:
                conn.execute("UPDATE extraction_runs SET stale=1 WHERE id=?", (run["id"],))


def set_skip(conn: sqlite3.Connection, message_id: int, minutes: int) -> None:
    """Change how much story time a message skips (the clock controls, the undo chip).

    Everything after it moves by the difference. Memory extracted from that stretch is
    thrown away, because it was stamped with the old times; the worker re-reads it.
    """
    m = get_message(conn, message_id)
    delta = minutes - m["skip_minutes"]
    if not delta:
        return
    down = (
        "WITH RECURSIVE down(id) AS (SELECT ?"
        " UNION ALL SELECT m.id FROM messages m JOIN down ON m.parent_id=down.id) "
    )
    with conn:
        conn.execute("UPDATE messages SET skip_minutes=? WHERE id=?", (minutes, message_id))
        conn.execute(
            down + "UPDATE messages SET story_time=story_time+? WHERE id IN (SELECT id FROM down)",
            (message_id, delta),
        )
        conn.execute(
            down + "UPDATE accesses SET story_time=story_time+?"
            " WHERE message_id IN (SELECT id FROM down)",
            (message_id, delta),
        )
        stale = conn.execute(
            down + "SELECT id FROM extraction_runs WHERE to_message_id IN (SELECT id FROM down)",
            (message_id,),
        ).fetchall()
    for run in stale:
        db.discard_run(conn, run["id"])


def new_scene(
    conn: sqlite3.Connection,
    story_id: int,
    present: list[int],
    place_id: int | None = None,
    title: str | None = None,
) -> int:
    """Cut to a new scene. It starts with a marker line in the story, so it belongs to this
    branch like any message, and `present` is its opening roster."""
    place = conn.execute("SELECT name FROM entities WHERE id=?", (place_id,)).fetchone()
    label = title or (place["name"] if place else "A new scene")
    leaf = conn.execute("SELECT active_leaf_id FROM stories WHERE id=?", (story_id,)).fetchone()[0]
    with conn:
        scene_id = conn.execute(
            "INSERT INTO scenes(story_id, place_id, title, start_story_time) VALUES(?, ?, ?, 0)",
            (story_id, place_id, title),
        ).lastrowid
        for entity_id in present:
            conn.execute(
                "INSERT INTO presence(scene_id, entity_id, present) VALUES(?, ?, 1)",
                (scene_id, entity_id),
            )
    marker = add_child(conn, story_id, leaf, "system", f"— {label} —", scene_id=scene_id)
    with conn:
        conn.execute(
            "UPDATE scenes SET start_message_id=?, start_story_time="
            "(SELECT story_time FROM messages WHERE id=?) WHERE id=?",
            (marker, marker, scene_id),
        )
    return scene_id
