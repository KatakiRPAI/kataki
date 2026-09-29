"""Backups (K12): full copies of the library beside it, in `backups/`, made in the background.

A restore can't swap the file under an open connection, so it is asked for now and done at the
next start, before the library opens; what was there is backed up first, so it can be undone.
"""

import json
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path

KEEP = {"7": 7, "30": 30, "all": None}
EVERY = {"daily": 86_400, "weekly": 7 * 86_400}
PENDING = "restore-pending"


def folder(db_path: Path) -> Path:
    return db_path.parent / "backups"


def make(conn: sqlite3.Connection, db_path: Path, keep: str = "7") -> dict:
    """Copy the library as it is now (SQLite's own backup, so a write in progress is safe)."""
    folder(db_path).mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = folder(db_path) / f"library-{stamp}.db"
    dest = sqlite3.connect(target)
    try:
        conn.backup(dest)
    finally:
        dest.close()
    prune(db_path, keep)
    return describe(target)


def describe(p: Path) -> dict:
    st = p.stat()
    return {
        "name": p.name,
        "bytes": st.st_size,
        "at": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
    }


def listing(db_path: Path) -> list[dict]:
    """Newest first."""
    if not folder(db_path).exists():
        return []
    return [describe(p) for p in sorted(folder(db_path).glob("library-*.db"), reverse=True)]


def prune(db_path: Path, keep: str) -> None:
    limit = KEEP.get(keep, 7)
    if limit is None:
        return
    for p in sorted(folder(db_path).glob("library-*.db"), reverse=True)[limit:]:
        p.unlink(missing_ok=True)


def due(db_path: Path, every: str) -> bool:
    """Whether the automatic backup should run now."""
    if every not in EVERY:
        return False
    newest = listing(db_path)
    return (
        not newest
        or time.time() - (folder(db_path) / newest[0]["name"]).stat().st_mtime > EVERY[every]
    )


def request_restore(db_path: Path, name: str) -> None:
    source = folder(db_path) / name
    if source.parent != folder(db_path) or not source.is_file():
        raise FileNotFoundError(name)
    (db_path.parent / PENDING).write_text(json.dumps({"name": name}))


def apply_pending(db_path: Path) -> bool:
    """At start, before the library opens: finish a restore that was asked for."""
    marker = db_path.parent / PENDING
    if not marker.exists():
        return False
    name = json.loads(marker.read_text())["name"]
    source = folder(db_path) / name
    if source.is_file():
        if db_path.exists():  # what was there is kept, so restoring can be undone
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copy2(db_path, folder(db_path) / f"library-{stamp}-before-restore.db")
        for extra in (
            db_path.with_name(db_path.name + "-wal"),
            db_path.with_name(db_path.name + "-shm"),
        ):
            extra.unlink(missing_ok=True)
        shutil.copy2(source, db_path)
    marker.unlink()
    return True
