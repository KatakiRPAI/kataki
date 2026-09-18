"""SQLite connection and schema migration."""

import sqlite3
from importlib.resources import files
from pathlib import Path

SCHEMA_VERSION = 1


def connect(path: str | Path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # ponytail: one shared connection; per-thread connections if lock contention ever shows up
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")  # per-connection, so every connect, not just migration
    if conn.execute("PRAGMA user_version").fetchone()[0] == 0:
        conn.executescript(files("kataki").joinpath("schema.sql").read_text(encoding="utf-8"))
        conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    return conn


def live_runs(conn: sqlite3.Connection, story_id: int) -> set[int]:
    """Runs whose rows count right now: finished ok, and extracted on the active branch.

    Every memory query filters on `run_id IS NULL OR run_id IN live_runs`, which is why a
    swipe or a branch switch never has to touch memory.
    """
    rows = conn.execute(
        "WITH RECURSIVE up(id, parent_id) AS ("
        " SELECT m.id, m.parent_id FROM messages m JOIN stories s ON s.active_leaf_id=m.id"
        " WHERE s.id=?"
        " UNION ALL SELECT m.id, m.parent_id FROM messages m JOIN up ON m.id=up.parent_id)"
        " SELECT r.id FROM extraction_runs r WHERE r.story_id=? AND r.status='ok'"
        " AND r.to_message_id IN (SELECT id FROM up)",
        (story_id, story_id),
    )
    return {r["id"] for r in rows}
