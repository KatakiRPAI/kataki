"""Images people add to the library (portraits, places), stored beside the library database.

A file is named by the SHA-256 of its bytes, so the same image is stored once and a valid name
can only ever point at one file in one folder. Only PNG, JPEG, GIF and WebP are accepted, judged
by their first bytes: SVG is not, because it can carry script.
"""

import hashlib
import os
import re
import sqlite3
import tempfile
from pathlib import Path

MAX_BYTES = 20 * 1024 * 1024  # PORTRAIT_TOO_LARGE: "PNG, JPG or WEBP, up to 20 MB"
TYPES = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}
# a reply's voice (minds slice 10): served like images, never taken as an upload
AUDIO = {"mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg", "flac": "audio/flac"}
TYPES |= AUDIO
NAME = re.compile(r"[0-9a-f]{64}\.(png|jpg|gif|webp|mp3|wav|ogg|flac)")


def sniff(data: bytes) -> str | None:
    """The image format from its magic bytes, or None."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def sniff_audio(data: bytes) -> str | None:
    """The audio format a speech server sent, from its first bytes, or None."""
    if data.startswith(b"ID3") or (len(data) > 1 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0):
        return "mp3"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if data.startswith(b"OggS"):
        return "ogg"
    if data.startswith(b"fLaC"):
        return "flac"
    return None


def folder(conn: sqlite3.Connection) -> Path:
    """`blobs/` next to the library database file."""
    main = next(row for row in conn.execute("PRAGMA database_list") if row[1] == "main")
    return Path(main[2]).parent / "blobs"


def save(conn: sqlite3.Connection, data: bytes, ext: str) -> str:
    """Store the bytes (once) and return their name. Written to a temp file and moved into
    place, so a crash never leaves half an image under a real name.
    ponytail: nothing sweeps images no item uses any more; add a sweep if libraries grow big."""
    name = f"{hashlib.sha256(data).hexdigest()}.{ext}"
    target = folder(conn) / name
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=target.parent, suffix=".part")
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, target)
    return name


def find(conn: sqlite3.Connection, name: str) -> Path | None:
    """The stored file for a name, or None for anything that isn't one."""
    if not NAME.fullmatch(name):
        return None
    path = folder(conn) / name
    return path if path.is_file() else None
