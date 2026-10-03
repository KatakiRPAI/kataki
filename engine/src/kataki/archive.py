"""The whole library, out and back: a `.kataki` file.

It is a zip holding three things: `library.db` (a real copy, taken with SQLite's own backup so
the file is never half-written), `blobs/` (every picture, still named by its bytes), and
`kataki.json`, which says what schema the database inside was written against.

Coming back, it is poured into a library with **no story and nobody in it**. Two libraries do
not merge: every row in here points at another by its id, and renumbering a whole library to fit
beside another one is a different and much larger thing than a backup. So the ids come back
exactly as they went. What a first run writes before there is any story — the provider, the
model roles, the settings — is replaced by the file's, because restoring a backup is how those
are meant to arrive; the keys themselves live in the machine's own keychain and are not in here.

A `.kataki` is a file from anywhere, so nothing in it is believed: not the sizes it declares,
not the names in it, and not the tables it says it has.
"""

import hashlib
import io
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from kataki import __version__, cards, db, media

FORMAT = 1
MAX_BYTES = 4 * 1024 * 1024 * 1024  # a library, not a disk — the file, and the db inside it
MAX_MANIFEST = 64 * 1024  # a manifest is four fields
# fts5 keeps its index in tables of its own, and the triggers on `memories` rebuild it as the
# rows arrive. Copying them would be laying an index over the one being built from the data.
DERIVED = ("memories_fts",)
# What a first run writes before there is any library: the backup's copy wins over this one's.
REPLACED = ("providers", "model_roles", "settings", "tags")
# Online, these are the service's (a provider named like the service's with another address would
# be sent the service's key): an import leaves them as they are, whatever the file holds.
MANAGED = ("providers", "model_roles", "settings", "usage_log")
# ...but of `settings` only these keys are the service's; the rest (the profile card, every
# preference) are the person's, and an import brings them.
SERVICE_SETTINGS = ("prices",)


class BadArchive(ValueError):
    """This file is not a .kataki, or not one that can be poured out here."""


def _tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
        " AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [r[0] for r in rows if not r[0].startswith(DERIVED)]


def _pictures_of(conn: sqlite3.Connection) -> list[Path]:
    blobs = media.folder(conn)
    if not blobs.is_dir():
        return []
    return sorted(  # voice audio is a cache (slice 10): made again on request, never exported
        p
        for p in blobs.iterdir()
        if p.is_file() and media.NAME.fullmatch(p.name) and p.suffix[1:] not in media.AUDIO
    )


def _holds(conn: sqlite3.Connection) -> dict:
    def n(sql: str) -> int:
        return conn.execute(sql).fetchone()[0]

    return {
        "stories": n("SELECT count(*) FROM stories"),
        "friends": n("SELECT count(*) FROM lib_items WHERE kind='character'"),
        "memories": n("SELECT count(*) FROM memories"),
        "pictures": len(_pictures_of(conn)),
    }


def dump(conn: sqlite3.Connection, target: str | Path) -> dict:
    """Write the library to `target` as a `.kataki`, and say what went into it."""
    # SQLite's backup waits for the writers to finish, and this connection is one of them: an
    # unfinished write of our own would be a wait with no end to it.
    conn.commit()
    manifest = {
        "kataki": FORMAT,
        "schema_version": db.SCHEMA_VERSION,
        "engine": __version__,
        "holds": _holds(conn),
    }
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "library.db"
        out = sqlite3.connect(copy)
        try:
            conn.backup(out)
        finally:
            out.close()
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("kataki.json", json.dumps(manifest, indent=2))
            z.write(copy, "library.db")
            for picture in _pictures_of(conn):
                z.write(picture, f"blobs/{picture.name}")
    return manifest


def _read(z: zipfile.ZipFile, name: str, cap: int) -> bytes | None:
    """One member, through the stream and no further than `cap`: what a zip says about its own
    size is what a zip says."""
    try:
        with z.open(name) as f:
            body = f.read(cap + 1)
    except KeyError:
        return None
    if len(body) > cap:
        raise BadArchive(f"the {name} in this file is far larger than one can be.")
    return body


def _manifest(z: zipfile.ZipFile) -> dict:
    raw = _read(z, "kataki.json", MAX_MANIFEST)
    if raw is None:
        raise BadArchive("there is no kataki.json in this file, so it is not a library.")
    try:
        said = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
        raise BadArchive("the kataki.json in this file could not be read.") from None
    if not isinstance(said, dict) or said.get("kataki") != FORMAT:
        raise BadArchive("this file says it is not a .kataki this Kataki knows.")
    try:
        version = int(said.get("schema_version") or 0)
    except (TypeError, ValueError):
        raise BadArchive("the kataki.json in this file could not be read.") from None
    if version > db.SCHEMA_VERSION:
        raise BadArchive("this library was written by a newer Kataki; update Kataki first.")
    return said


def _extract(z: zipfile.ZipFile, name: str, target: Path) -> None:
    """Copy a member out, counting as it goes: a small zip can promise a very large file."""
    try:
        source = z.open(name)
    except KeyError:
        raise BadArchive("there is no library in this file.") from None
    written = 0
    with source, open(target, "wb") as w:
        while chunk := source.read(1 << 20):
            written += len(chunk)
            if written > MAX_BYTES:
                raise BadArchive("the library in this file is too big to be one.")
            w.write(chunk)
    if not written:  # an empty file is not a database, whatever SQLite would make of it
        raise BadArchive("there is no library in this file.")


def _pictures(conn: sqlite3.Connection, z: zipfile.ZipFile) -> int:
    """Every picture that is one. A name in someone else's file is not a path to write to: it
    is checked against what a name can be, and then against the bytes it claims to be."""
    kept = 0
    for name in z.namelist():
        if not name.startswith("blobs/"):
            continue
        short = name.removeprefix("blobs/")
        if not media.NAME.fullmatch(short):
            continue
        with z.open(name) as f:
            body = f.read(media.MAX_BYTES + 1)
        if len(body) > media.MAX_BYTES or (ext := media.sniff(body)) is None:
            continue
        if f"{hashlib.sha256(body).hexdigest()}.{ext}" != short:
            continue  # a name can only ever point at one file, and this is not it
        media.save(conn, body, ext)
        kept += 1
    return kept


def _room_for_it(conn: sqlite3.Connection, tables: list[str]) -> None:
    """Refuse unless this library is one a backup can be poured into: nothing of its own but
    what a first run writes."""
    busy = [
        table
        for table in tables
        if table not in REPLACED
        and conn.execute(f'SELECT 1 FROM main."{table}" LIMIT 1').fetchone()
    ]
    if busy:
        raise BadArchive(
            "a library can only be poured into an empty one, and this one already holds"
            f" things ({', '.join(busy[:3])})."
        )


def restore(conn: sqlite3.Connection, blob: bytes, keep: tuple[str, ...] = ()) -> dict:
    """Pour a `.kataki` into this library, which must have no story of its own. What arrived.
    Tables in `keep` are left exactly as they are here (online: MANAGED)."""
    if len(blob) > MAX_BYTES:
        raise BadArchive("that file is too big to be a library.")

    with tempfile.TemporaryDirectory() as tmp:
        incoming = Path(tmp) / "library.db"
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                _manifest(z)
                _extract(z, "library.db", incoming)

                # Older is fine: the migrations run on it where it lies, before a row is read
                # out, so what is copied is always this schema.
                try:
                    opened = db.connect(incoming)
                except sqlite3.DatabaseError as e:
                    raise BadArchive(f"the library in this file could not be opened ({e}).") from (
                        None
                    )
                try:
                    theirs = set(_tables(opened))
                finally:
                    opened.close()

                # Drive the copy off our own tables, never the stranger's: an extra table in
                # there is nothing here, and a missing one is a library that is not whole.
                ours = [t for t in _tables(conn) if t not in keep]
                if missing := [t for t in ours if t not in theirs]:
                    raise BadArchive(
                        f"the library in this file has no {missing[0]}, so it is not a library."
                    )
                _room_for_it(conn, ours)
                _copy(conn, incoming, ours, settings_too="settings" in keep)
                pictures = _pictures(conn, z)
        except BadArchive:
            raise
        except cards.ZIP_TROUBLE as e:
            raise BadArchive(f"that is not a .kataki file ({e}).") from None
        except sqlite3.Error as e:
            raise BadArchive(f"the library in this file could not be read ({e}).") from None

    return _holds(conn) | {"pictures": pictures}


def _copy(
    conn: sqlite3.Connection, incoming: Path, tables: list[str], settings_too: bool = False
) -> None:
    """Every row, in one transaction: either the whole library arrives or none of it does.
    Keys are off while it lands — half a library never satisfies its own references — and
    checked in full before the commit."""
    conn.commit()  # `foreign_keys` is a no-op inside a transaction, so nothing may be open
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("ATTACH DATABASE ? AS incoming", (str(incoming),))
    try:
        with conn:
            for table in (t for t in REPLACED if t in tables):
                conn.execute(f'DELETE FROM main."{table}"')
            for table in tables:
                conn.execute(f'INSERT INTO main."{table}" SELECT * FROM incoming."{table}"')
            if settings_too:  # online: the person's settings, never the service's keys
                held = ", ".join("?" * len(SERVICE_SETTINGS))
                conn.execute(
                    "INSERT OR REPLACE INTO main.settings SELECT * FROM incoming.settings"
                    f" WHERE key NOT IN ({held})",
                    SERVICE_SETTINGS,
                )
            if broken := conn.execute("PRAGMA foreign_key_check").fetchall():
                # raised inside the transaction, so it is rolled back and nothing is left here
                raise BadArchive(
                    f"the library in this file does not hold together ({len(broken)} rows point"
                    " at rows that are not there)."
                )
    finally:
        conn.execute("DETACH DATABASE incoming")
        conn.execute("PRAGMA foreign_keys=ON")
