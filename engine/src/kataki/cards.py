"""Character cards coming in: a PNG, a JSON file or a CHARX zip becomes a friend in the library.

V3 first (a `ccv3` tEXt chunk), then V2 (`chara`), then a flat V1 object; a CHARX is a zip with
`card.json` at its root and the pictures beside it. Both chunk kinds hold base64 of UTF-8 JSON.

Two rules run through all of it. **Nothing is overwritten**: every import makes a new friend, so
a name you already have becomes a second one rather than a silent merge. **Nothing is thrown
away**: what the engine has no field for is kept under `data["card"]`, so what came in can go
out again.

Macros: a card's `{{char}}` is a name this import knows, so it is written out here. `{{user}}` is
not — who is playing changes with the story — so it stays a macro and is resolved where the
player is known (the opening line at `library.create_story`, the prompt at `context.build`).

All stdlib: `struct` walks the PNG chunks, `zipfile` opens a CHARX, `json` and `base64` do the
rest. Nothing here trusts a size a file declares about itself.
"""

import base64
import binascii
import io
import json
import re
import struct
import zipfile
import zlib

from kataki import media

MAX_BYTES = 32 * 1024 * 1024  # a card with its pictures; anything larger is not a card
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
ASSET_CHUNK = "chara-ext-asset_:"
# Everything a hostile or merely broken archive throws on the way in. `BadCard` is a ValueError
# and is raised inside the same block, so bare ValueError must stay out of this.
ZIP_TROUBLE = (
    zipfile.BadZipFile,
    zlib.error,
    RuntimeError,  # an encrypted member
    NotImplementedError,  # a compression method this Python has no reader for
    EOFError,
    OSError,
    json.JSONDecodeError,
    UnicodeDecodeError,
    RecursionError,  # JSON nested twenty thousand deep
)
CHAR = re.compile(r"\{\{\s*char(?:name)?\s*\}\}|<char>|<bot>", re.I)
USER = re.compile(r"\{\{\s*user\s*\}\}|<user>", re.I)
EMBEDDED = "embeded://"  # the V3 spec's spelling, and it is not a typo here
# Everything the engine has no field of its own for, kept exactly as it came.
KEEP = (
    "creator",
    "character_version",
    "creator_notes",
    "creator_notes_multilingual",
    "system_prompt",
    "post_history_instructions",
    "alternate_greetings",
    "group_only_greetings",
    "source",
    "character_book",
    "extensions",
    "assets",
    "creation_date",
    "modification_date",
)


class BadCard(ValueError):
    """This file is not a character card, or not one that can be read."""


def macros(text: str, *, char: str | None = None, user: str | None = None) -> str:
    """Write out the card macros whose answer is known here, and leave the rest alone."""
    if char is not None:
        text = CHAR.sub(lambda _: char, text)
    if user is not None:
        text = USER.sub(lambda _: user, text)
    return text


def _chunks(blob: bytes) -> dict[str, bytes]:
    """The tEXt chunks of a PNG, by keyword. A chunk that runs past the end ends the walk."""
    out: dict[str, bytes] = {}
    at = len(PNG_MAGIC)
    while at + 8 <= len(blob):
        (size,) = struct.unpack(">I", blob[at : at + 4])
        kind, body = blob[at + 4 : at + 8], blob[at + 8 : at + 8 + size]
        if len(body) < size:
            break  # truncated file: keep what was whole
        if kind == b"tEXt" and b"\x00" in body:
            key, value = body.split(b"\x00", 1)
            out.setdefault(key.decode("latin-1"), value)
        at += size + 12
        if kind == b"IEND":
            break
    return out


def _b64(value: bytes) -> bytes | None:
    """Base64 that a messy card got wrong is one picture lost, never a failed import."""
    try:
        return base64.b64decode(value, validate=False)
    except (binascii.Error, ValueError):
        return None


def _member(z: zipfile.ZipFile, name: str, cap: int) -> bytes | None:
    """One file out of a zip, or None if it is missing or bigger than `cap`. Read through the
    stream rather than `z.read`, because a zip's own size header is not a thing to believe:
    a small archive can promise to become a very large one."""
    try:
        with z.open(name) as f:
            body = f.read(cap + 1)
    except KeyError:
        return None
    return None if len(body) > cap else body


def _wanted(z: zipfile.ZipFile, data: dict) -> dict[str, bytes]:
    """Only the files the card actually points at, and only while they fit between them: the
    rest of an archive is nothing this library needs to hold in memory."""
    out: dict[str, bytes] = {}
    room = MAX_BYTES
    for asset in data.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        uri = str(asset.get("uri") or "")
        for scheme in (EMBEDDED, "__asset:"):
            if uri.startswith(scheme) and (path := uri.removeprefix(scheme)) not in out:
                if (body := _member(z, path, min(media.MAX_BYTES, room))) is not None:
                    out[path] = body
                    room -= len(body)
    return out


def _decode(value: bytes) -> dict:
    try:
        return json.loads(base64.b64decode(value, validate=True))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as e:
        raise BadCard(f"the card in this file could not be read ({e}).") from None


def _unwrap(card: dict) -> tuple[str, str, dict]:
    """(spec, spec_version, the card's own fields). A V1 card is the fields themselves."""
    if not isinstance(card, dict):
        raise BadCard("the card in this file could not be read (not an object).")
    data = card.get("data")
    if isinstance(data, dict):
        return str(card.get("spec") or "chara_card_v2"), str(card.get("spec_version") or ""), data
    return "chara_card_v1", "", card


def parse(blob: bytes) -> tuple[str, str, dict, dict[str, bytes]]:
    """(spec, spec_version, the card, the files that travelled with it) from any of the three
    shapes a card comes in."""
    if len(blob) > MAX_BYTES:
        raise BadCard("that file is too big to be a character card (32 MB at most).")
    if blob.startswith(PNG_MAGIC):
        chunks = _chunks(blob)
        for key in ("ccv3", "chara"):  # V3 wins where a card carries both
            if key in chunks:
                spec, version, data = _unwrap(_decode(chunks[key]))
                assets = {
                    k.removeprefix(ASSET_CHUNK): body
                    for k, v in chunks.items()
                    if k.startswith(ASSET_CHUNK) and (body := _b64(v)) is not None
                }
                return spec, version, data, {"__self__": blob, **assets}
        raise BadCard("this PNG holds no character card.")
    if blob[:4] == b"PK\x03\x04":
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                raw = _member(z, "card.json", media.MAX_BYTES)
                if raw is None:
                    raise BadCard("a CHARX must have a card.json at its root that fits in memory.")
                spec, version, data = _unwrap(json.loads(raw))
                files = _wanted(z, data)
        except ZIP_TROUBLE as e:
            raise BadCard(f"the card in this file could not be read ({e}).") from None
        return spec, version, data, files
    try:
        spec, version, data = _unwrap(json.loads(blob))
    except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
        raise BadCard("that is not a PNG, a JSON card or a CHARX file.") from None
    return spec, version, data, {}


def _text(data: dict, key: str) -> str:
    value = data.get(key)
    return value.strip() if isinstance(value, str) else ""


def _fold(data: dict) -> str:
    """Description, personality and scenario as one card, in the engine's own bracket voice."""
    parts = [_text(data, "description")]
    for key, head in (("personality", "Personality"), ("scenario", "Scenario")):
        if body := _text(data, key):
            parts.append(f"[{head}]\n{body}")
    return "\n\n".join(p for p in parts if p)


def picture(data: dict, files: dict[str, bytes], notes: list[str] | None = None) -> bytes | None:
    """The picture this card points at, if the library can hold it: its `icon` asset if it names
    one, else the PNG itself. Decides, and saves nothing — so asking whether a card brings a
    portrait is the same question as taking it, not a second one that can disagree."""
    said = notes if notes is not None else []
    icons = [a for a in data.get("assets") or [] if isinstance(a, dict) and a.get("type") == "icon"]
    icons.sort(key=lambda a: a.get("name") != "main")  # the spec's main icon first
    for asset in icons:
        uri = str(asset.get("uri") or "")
        if uri.startswith(EMBEDDED):
            found = files.get(uri.removeprefix(EMBEDDED))
        elif uri.startswith("data:"):
            _, _, payload = uri.partition(",")
            found = _b64(payload.encode()) if payload else None
        elif uri.startswith("__asset:"):
            found = files.get(uri.removeprefix("__asset:"))
        elif uri == "ccdefault:":
            found = files.get("__self__")
        else:
            said.append(f"the picture at {uri} was left where it is; pictures are not fetched.")
            continue
        if not found:
            said.append(f"the picture at {uri} was not in this file.")
        elif media.sniff(found) and len(found) <= media.MAX_BYTES:
            return found
        else:
            said.append(f"the picture at {uri} is not an image this library can hold.")
    if blob := files.get("__self__"):
        if len(blob) > media.MAX_BYTES:
            said.append("this card's own picture is larger than the library will hold.")
        elif media.sniff(blob):
            return blob
    return None


def _portrait(conn, data: dict, files: dict[str, bytes], notes: list[str]) -> str | None:
    found = picture(data, files, notes)
    return media.save(conn, found, media.sniff(found)) if found else None


def add(conn, blob: bytes) -> dict:
    """Bring a card in as a new library character: the item, the spec it came as, and notes
    about anything kept but not used."""
    from kataki import library  # here, not above: the library writes out `{{user}}` with macros

    spec, version, data, files = parse(blob)
    nickname = _text(data, "nickname")
    name = _text(data, "name") or nickname
    if not name:
        raise BadCard("a character card must have a name.")

    notes: list[str] = []
    portrait = _portrait(conn, data, files, notes)

    def say(text: str) -> str:
        # V3: `{{char}}` is the nickname where there is one — "Miku", not "Hatsune Miku
        # (Vocaloid)" — and the name only when there is not. The item keeps the full name.
        return macros(text, char=nickname or name)

    kept = {k: data[k] for k in KEEP if data.get(k) not in (None, "", [], {})}
    if others := kept.get("alternate_greetings"):
        notes.append(f"{len(others)} other greetings were kept with the card.")
    if book := kept.get("character_book"):
        entries = book.get("entries") or [] if isinstance(book, dict) else []
        notes.append(f"a lorebook of {len(entries)} entries came with the card and was kept.")
    if not portrait:
        notes.append("this card brought no picture.")
    # a card in the wild may write its tags as one string; a string is iterable, and its letters
    # are not tags
    listed = data.get("tags")
    tags = sorted(
        {t.strip() for t in listed if isinstance(t, str) and t.strip()}
        if isinstance(listed, list)
        else ()
    )

    item_id = library.create_item(
        conn,
        "character",
        name,
        description=say(_fold(data)),
        data={
            "first_message": say(_text(data, "first_mes")),
            "example_dialogue": say(_text(data, "mes_example")),
            # aliases are case-blind in the schema, so "Mira" is not a second name for "MIRA"
            "aliases": [nickname] if nickname and nickname.casefold() != name.casefold() else [],
            **({"portrait": portrait} if portrait else {}),
            "card": {"spec": spec, "spec_version": version, **kept},
        },
        tags=tags,
    )
    return {"item": library.get_item(conn, item_id), "spec": spec, "notes": notes}
