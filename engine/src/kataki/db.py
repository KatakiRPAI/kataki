"""SQLite connection and schema migration."""

import sqlite3
from importlib.resources import files
from pathlib import Path

SCHEMA_VERSION = 10
# version -> the SQL that brings a library up from the version before it; schema.sql is v1
MIGRATIONS = {
    2: "ALTER TABLE entities ADD COLUMN examples TEXT NOT NULL DEFAULT ''",  # example dialogue
    3: (  # the Sky: pinned stories, and the newest memory read the user has seen
        "ALTER TABLE stories ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0;"
        "ALTER TABLE stories ADD COLUMN seen_run_id INTEGER NOT NULL DEFAULT 0;"
    ),
    # who a line was for: NULL = everyone present, a JSON list = a whisper, [] = a thought
    4: "ALTER TABLE messages ADD COLUMN audience TEXT",
    # presence the memory reader found goes when its run does, so a reread can't duplicate it
    5: (
        "ALTER TABLE presence ADD COLUMN"
        " run_id INTEGER REFERENCES extraction_runs ON DELETE CASCADE"
    ),
    6: (  # the exact line a memory came from, and what a claim contradicts
        "ALTER TABLE memories ADD COLUMN message_id INTEGER;"
        "ALTER TABLE memories ADD COLUMN contradicts_id INTEGER;"
        "UPDATE memories SET message_id = to_message_id WHERE run_id IS NOT NULL;"
    ),
    7: (  # the library: books, chapters, and how two stories sit in each other's time
        "ALTER TABLE stories ADD COLUMN book_order INTEGER NOT NULL DEFAULT 0;"
        "CREATE TABLE books("
        " id INTEGER PRIMARY KEY, title TEXT NOT NULL, blurb TEXT NOT NULL DEFAULT '',"
        " created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);"
        "CREATE TABLE chapters("
        " id INTEGER PRIMARY KEY,"
        " story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,"
        " title TEXT NOT NULL, from_message_id INTEGER NOT NULL, to_message_id INTEGER,"
        " created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);"
        "CREATE INDEX ix_chapters ON chapters(story_id, from_message_id);"
        "CREATE TABLE story_links("
        " id INTEGER PRIMARY KEY,"
        " from_story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,"
        " to_story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,"
        " kind TEXT NOT NULL CHECK(kind IN('continuation','shared_universe','reference')),"
        " offset_min INTEGER NOT NULL DEFAULT 0, note TEXT,"
        " UNIQUE(from_story_id, to_story_id, kind));"
        "CREATE INDEX ix_ent_origin ON entities(origin_entity_id);"
    ),
    8: "ALTER TABLE messages ADD COLUMN expression TEXT",  # the face a line is said with (M3 §7)
    # what anyone can see of someone; who they are (description) stays in their own prompt
    9: "ALTER TABLE entities ADD COLUMN looks TEXT NOT NULL DEFAULT ''",
    10: (  # minds (docs/specs/2026-09-29-minds.md): how each character feels, anchored on the
        # message or run that wrote it; and what every model call used, in both products
        "CREATE TABLE mind_states("
        " id INTEGER PRIMARY KEY,"
        " entity_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,"
        " story_time INTEGER NOT NULL, state TEXT NOT NULL,"
        " message_id INTEGER REFERENCES messages ON DELETE CASCADE,"
        " run_id INTEGER REFERENCES extraction_runs ON DELETE CASCADE);"
        "CREATE INDEX ix_mind_states ON mind_states(entity_id, story_time);"
        "CREATE TABLE usage_log("
        " id INTEGER PRIMARY KEY,"
        " story_id INTEGER REFERENCES stories ON DELETE SET NULL,"
        " role TEXT NOT NULL, model TEXT NOT NULL,"
        " prompt_tokens INTEGER NOT NULL DEFAULT 0, cached_tokens INTEGER NOT NULL DEFAULT 0,"
        " completion_tokens INTEGER NOT NULL DEFAULT 0,"
        " at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);"
        "CREATE INDEX ix_usage_story ON usage_log(story_id);"
    ),
}


class LibraryTooNew(Exception):
    """The library was written by a newer Kataki. Opening it here could undo a migration it
    already has, so it is left exactly as it is."""


def _copy_before_migrating(conn: sqlite3.Connection, path: Path, version: int) -> None:
    """A copy of the library as it was, beside it, before any migration touches it. It lands in
    the backups folder, so Settings › Backups lists it and can restore it."""
    folder = Path(path).parent / "backups"
    folder.mkdir(parents=True, exist_ok=True)
    dest = sqlite3.connect(folder / f"library-before-v{SCHEMA_VERSION}-from-v{version}.db")
    try:
        conn.backup(dest)
    finally:
        dest.close()


def connect(path: str | Path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # ponytail: one shared connection; per-thread connections if lock contention ever shows up
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")  # the first read of the file, and so the first
        conn.execute("PRAGMA foreign_keys=ON")  # per-connection, not just per migration
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise LibraryTooNew(
                f"This library is from a newer Kataki (schema {version}; this one reads up to"
                f" {SCHEMA_VERSION}). Update Kataki to open it."
            )
        if version == 0:
            conn.executescript(files("kataki").joinpath("schema.sql").read_text(encoding="utf-8"))
            version = 1
        elif version < SCHEMA_VERSION:
            _copy_before_migrating(conn, Path(path), version)
        for target in range(version + 1, SCHEMA_VERSION + 1):
            conn.executescript(MIGRATIONS[target])
        conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    except BaseException:
        conn.close()  # a library that cannot be opened is not a file left open
        raise
    return conn


def _path_cte(story_id: int, leaf_id: int | None) -> tuple[str, list[int]]:
    """A recursive CTE `up(id, parent_id)`: the branch that ends at `leaf_id` (default: the
    story's active leaf), leaf to root."""
    start = "SELECT id, parent_id FROM messages WHERE id=?"
    if leaf_id is None:
        start = "SELECT m.id, m.parent_id FROM messages m JOIN stories s ON s.active_leaf_id=m.id"
        start += " WHERE s.id=?"
    cte = (
        f"WITH RECURSIVE up(id, parent_id) AS ({start}"
        " UNION ALL SELECT m.id, m.parent_id FROM messages m JOIN up ON m.id=up.parent_id)"
    )
    return cte, [story_id if leaf_id is None else leaf_id]


def live_runs(conn: sqlite3.Connection, story_id: int, leaf_id: int | None = None) -> set[int]:
    """Runs whose rows count right now: finished ok, and extracted on the branch that ends at
    `leaf_id` (default: the active leaf).

    Every memory query filters through `live_filter`, which is why a swipe or a branch
    switch never has to touch memory.
    """
    cte, args = _path_cte(story_id, leaf_id)
    rows = conn.execute(
        f"{cte} SELECT r.id FROM extraction_runs r WHERE r.story_id=? AND r.status='ok'"
        " AND r.to_message_id IN (SELECT id FROM up)",
        (*args, story_id),
    )
    return {r["id"] for r in rows}


def live_messages(conn: sqlite3.Connection, story_id: int, leaf_id: int | None = None) -> set[int]:
    """The messages on the branch that ends at `leaf_id` (default: the active leaf)."""
    cte, args = _path_cte(story_id, leaf_id)
    return {r["id"] for r in conn.execute(f"{cte} SELECT id FROM up", args)}


def anchor_filter(runs: set[int], messages: set[int]) -> tuple[str, list[int]]:
    """SQL condition + args for rows anchored the minds way (spec §3): written by the user (no
    anchor), by a message on this branch, or by a live run. A swipe or branch switch therefore
    swaps the whole mind with no code of its own."""
    parts, args = ["(message_id IS NULL AND run_id IS NULL)"], []
    if messages:
        parts.append(f"message_id IN ({','.join('?' * len(messages))})")
        args += sorted(messages)
    if runs:
        parts.append(f"run_id IN ({','.join('?' * len(runs))})")
        args += sorted(runs)
    return "(" + " OR ".join(parts) + ")", args


def live_filter(live: set[int], column: str = "run_id") -> tuple[str, list[int]]:
    """SQL condition + args: the row was written by the user, or by a live run."""
    if not live:
        return f"{column} IS NULL", []
    return f"({column} IS NULL OR {column} IN ({','.join('?' * len(live))}))", sorted(live)


def discard_run(conn: sqlite3.Connection, run_id: int) -> None:
    """Undo a run completely."""
    with conn:
        delete_run(conn, run_id)


def delete_run(conn: sqlite3.Connection, run_id: int) -> None:
    """`discard_run` inside the caller's transaction. FKs cascade everything except taggings,
    which are polymorphic."""
    for obj, table in (("memory", "memories"), ("entity", "entities")):
        conn.execute(
            f"DELETE FROM taggings WHERE obj=? AND obj_id IN"
            f" (SELECT id FROM {table} WHERE run_id=?)",
            (obj, run_id),
        )
    conn.execute("DELETE FROM extraction_runs WHERE id=?", (run_id,))
