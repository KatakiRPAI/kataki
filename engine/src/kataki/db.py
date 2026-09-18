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
