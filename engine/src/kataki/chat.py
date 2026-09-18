"""The message tree. A story is a tree of messages; the active path is leaf -> root.

Swipes and regenerations are siblings, a branch is just another leaf, and nothing is ever
deleted. Memory rows follow the branch they were extracted on (see extract.py), so
switching leaf is free.
"""

import sqlite3

_UP = (
    "WITH RECURSIVE up(id, parent_id) AS ("
    " SELECT id, parent_id FROM messages WHERE id=?"
    " UNION ALL SELECT m.id, m.parent_id FROM messages m JOIN up ON m.id=up.parent_id) "
)


def _message(conn: sqlite3.Connection, message_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
    if row is None:
        raise ValueError(f"no message {message_id}")
    return row


def _set_active(conn: sqlite3.Connection, story_id: int, message_id: int) -> None:
    conn.execute("UPDATE stories SET active_leaf_id=? WHERE id=?", (message_id, story_id))


def active_path(conn: sqlite3.Connection, story_id: int) -> list[sqlite3.Row]:
    """Root -> leaf. Ids only grow along a path, so ordering by id is ordering by depth."""
    story = conn.execute("SELECT active_leaf_id FROM stories WHERE id=?", (story_id,)).fetchone()
    sql = _UP + "SELECT * FROM messages WHERE id IN (SELECT id FROM up) ORDER BY id"
    return conn.execute(sql, (story["active_leaf_id"],)).fetchall()


def append_message(
    conn: sqlite3.Connection,
    story_id: int,
    role: str,
    text: str,
    speaker_id: int | None = None,
    skip_minutes: int = 0,
) -> int:
    """Add a message under the active leaf. The story clock moves one tick, plus any skip."""
    with conn:
        story = conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()
        parent = _message(conn, story["active_leaf_id"]) if story["active_leaf_id"] else None
        scene = parent["scene_id"] if parent else None
        if scene is None:
            first = conn.execute(
                "SELECT id FROM scenes WHERE story_id=? ORDER BY id LIMIT 1", (story_id,)
            ).fetchone()
            scene = first["id"] if first else None
        now = (parent["story_time"] if parent else 0) + story["minutes_per_turn"] + skip_minutes
        message_id = conn.execute(
            "INSERT INTO messages"
            "(story_id, parent_id, role, speaker_id, text, story_time, skip_minutes, scene_id)"
            " VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (story_id, parent and parent["id"], role, speaker_id, text, now, skip_minutes, scene),
        ).lastrowid
        _set_active(conn, story_id, message_id)
    return message_id


def append_sibling(conn: sqlite3.Connection, message_id: int, text: str) -> int:
    """A swipe / regeneration: same place in the tree and on the clock, different text."""
    with conn:
        m = _message(conn, message_id)
        sibling = conn.execute(
            "INSERT INTO messages"
            "(story_id, parent_id, role, speaker_id, text, story_time, skip_minutes, scene_id)"
            " VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (
                m["story_id"],
                m["parent_id"],
                m["role"],
                m["speaker_id"],
                text,
                m["story_time"],
                m["skip_minutes"],
                m["scene_id"],
            ),
        ).lastrowid
        _set_active(conn, m["story_id"], sibling)
    return sibling


def sibling_position(conn: sqlite3.Connection, message_id: int) -> tuple[int, int]:
    """(index, count) among the alternatives at this point, for the swipe arrows. 1-based."""
    m = _message(conn, message_id)
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
    if _message(conn, message_id)["story_id"] != story_id:
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
        m = _message(conn, message_id)
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
