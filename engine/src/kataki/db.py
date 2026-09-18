"""SQLite connection and schema migration."""

import sqlite3
from importlib.resources import files
from pathlib import Path

SCHEMA_VERSION = 2
# version -> the SQL that brings a library up from the version before it; schema.sql is v1
MIGRATIONS = {
    2: "ALTER TABLE entities ADD COLUMN examples TEXT NOT NULL DEFAULT ''",  # example dialogue
}


def connect(path: str | Path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # ponytail: one shared connection; per-thread connections if lock contention ever shows up
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")  # per-connection, so every connect, not just migration
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version == 0:
        conn.executescript(files("kataki").joinpath("schema.sql").read_text(encoding="utf-8"))
        version = 1
    for target in range(version + 1, SCHEMA_VERSION + 1):
        conn.executescript(MIGRATIONS[target])
    conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    return conn


def live_runs(conn: sqlite3.Connection, story_id: int, leaf_id: int | None = None) -> set[int]:
    """Runs whose rows count right now: finished ok, and extracted on the branch that ends at
    `leaf_id` (default: the active leaf).

    Every memory query filters through `live_filter`, which is why a swipe or a branch
    switch never has to touch memory.
    """
    start = "SELECT id, parent_id FROM messages WHERE id=?"
    if leaf_id is None:
        start = "SELECT m.id, m.parent_id FROM messages m JOIN stories s ON s.active_leaf_id=m.id"
        start += " WHERE s.id=?"
    rows = conn.execute(
        f"WITH RECURSIVE up(id, parent_id) AS ({start}"
        " UNION ALL SELECT m.id, m.parent_id FROM messages m JOIN up ON m.id=up.parent_id)"
        " SELECT r.id FROM extraction_runs r WHERE r.story_id=? AND r.status='ok'"
        " AND r.to_message_id IN (SELECT id FROM up)",
        (story_id if leaf_id is None else leaf_id, story_id),
    )
    return {r["id"] for r in rows}


def live_filter(live: set[int], column: str = "run_id") -> tuple[str, list[int]]:
    """SQL condition + args: the row was written by the user, or by a live run."""
    if not live:
        return f"{column} IS NULL", []
    return f"({column} IS NULL OR {column} IN ({','.join('?' * len(live))}))", sorted(live)


def discard_run(conn: sqlite3.Connection, run_id: int) -> None:
    """Undo a run completely. FKs cascade everything except taggings, which are polymorphic."""
    with conn:
        for obj, table in (("memory", "memories"), ("entity", "entities")):
            conn.execute(
                f"DELETE FROM taggings WHERE obj=? AND obj_id IN"
                f" (SELECT id FROM {table} WHERE run_id=?)",
                (obj, run_id),
            )
        conn.execute("DELETE FROM extraction_runs WHERE id=?", (run_id,))
