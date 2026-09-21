"""What a file would become, said before anything is made of it.

Bringing something in is not reversible in any way that matters — a card becomes a friend, a chat
becomes a story with its own memories. So every route that makes something has a reading of the
same file that makes nothing, and the app shows it first. This module only ever parses.

Two rules hold it together. Every count here is taken with the same predicate the import uses, so
the preview cannot promise what the import then drops. And nothing a file says about itself is
believed: a `.kataki` is written by a stranger, and a number in it is a number until it isn't.
"""

import codecs
import io
import json
import zipfile

from kataki import archive, cards, chats, lore
from kataki.cards import BadCard

ZIP = b"PK\x03\x04"
# The biggest thing any import route will take (a chat); read once, before anything is parsed,
# because the parse itself is the expensive part and it runs on the engine's one thread.
MAX_BYTES = chats.MAX_BYTES
# longest first: a UTF-32 LE mark begins with a UTF-16 LE one
BOMS = (
    codecs.BOM_UTF32_LE,
    codecs.BOM_UTF32_BE,
    codecs.BOM_UTF8,
    codecs.BOM_UTF16_LE,
    codecs.BOM_UTF16_BE,
)


def _count(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def _listed(names: list[str]) -> str:
    return f"{', '.join(names[:-1])} and {names[-1]}" if len(names) > 1 else names[0]


def _n(value) -> int:
    """A count out of a file we did not write. A bool is an int in Python, and is not a count."""
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _card(blob: bytes) -> dict:
    spec, version, data, files = cards.parse(blob)
    name = cards._text(data, "name") or cards._text(data, "nickname")
    if not name:
        raise BadCard("a character card must have a name.")
    what = [f"A friend called {name}."]
    notes: list[str] = []
    book = data.get("character_book")
    if isinstance(book, dict) and (kept := [e for e in lore.entries(book) if lore.keeps(e)]):
        what.append(f"{_count(len(kept), 'thing')} they know, kept as a lorebook.")
    # the same question `add` asks, so a picture the library would refuse is not promised here
    if cards.picture(data, files, notes) is not None:
        what.append("A portrait.")
    else:
        notes.append("This card brings no picture we can hold, so they will start as initials.")
    listed = data.get("tags")
    tags = (
        sorted({t.strip() for t in listed if isinstance(t, str) and t.strip()})
        if isinstance(listed, list)
        else []
    )
    if tags:
        what.append(f"Tags: {', '.join(tags)}.")
    notes.append("Bringing the same card in twice makes two friends, never one merged.")
    return {"kind": "card", "title": name, "spec": spec or "chara_card_v1", "what": what,
            "notes": notes, "needs_story": False, "version": version}  # fmt: skip


def _chat(blob: bytes) -> dict:
    header, lines, broken, past = chats.read(blob)
    # a line the adder would drop is not a line: it counts what would be made, not what was read
    kept = [m for m in lines if chats._takes(m)[0]]
    if not kept:
        raise BadCard("there are no lines in this file to bring in.")
    title = chats._title(header, lines)
    theirs = chats._named(header, lines, user=False)
    yours = chats._named(header, lines, user=True)
    retold = sum(1 for m in kept if len(chats._takes(m)[0]) > 1)
    # every other voice in the file is another friend made: a group chat is not two people
    others = list(
        dict.fromkeys(
            said
            for m in kept
            if not m.get("is_user")
            and isinstance(m.get("name"), str)
            and (said := m["name"].strip())
            and said.casefold() not in (theirs.casefold(), chats.UNNAMED)
        )
    )
    what = [
        f"A story called “{title}”.",
        f"{_count(len(kept), 'line')}, between {theirs} and {yours}.",
    ]
    if others:
        speak = (
            "also speaks, and is made a friend too"
            if len(others) == 1
            else ("also speak, and are made friends too")
        )
        what.append(f"{_listed(others)} {speak}.")
    if retold:
        what.append(f"{_count(retold, 'line')} with more than one take, kept as takes.")
    notes = []
    if len(lines) > len(kept):
        notes.append(f"{_count(len(lines) - len(kept), 'line')} are blank and will be left out.")
    if broken:
        notes.append(f"{_count(broken, 'line')} could not be read and will be left out.")
    if past:
        notes.append(f"This chat is longer than we read; {past} lines will stay behind.")
    notes.append("Say which friend and which persona it is about, or new friends are made.")
    return {"kind": "chat", "title": title, "what": what, "notes": notes, "needs_story": False}


def _lorebook(blob: bytes) -> dict:
    book = lore.read(blob)
    all_of_them = lore.entries(book)
    kept = [e for e in all_of_them if lore.keeps(e)]
    always = [e for e in kept if e["constant"]]
    what = [f"{_count(len(kept), 'thing')} a story would know."]
    if always:
        what.append(f"{_count(len(always), 'of them is', 'of them are')} always in the prompt.")
    notes = []
    if dropped := len(all_of_them) - len(kept):
        notes.append(
            f"{_count(dropped, 'entry', 'entries')} are switched off, empty, or have no word "
            "that could ever cue them, and stay out."
        )
    notes.append("Pick the story that learns it.")
    name = book.get("name") if isinstance(book.get("name"), str) else ""
    return {
        "kind": "lorebook",
        "title": name.strip() or "A lorebook",
        "what": what,
        "notes": notes,
        "needs_story": True,
    }


def _library(blob: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        said = archive._manifest(z)
    holds = said.get("holds") if isinstance(said.get("holds"), dict) else {}
    counted = [
        _count(_n(holds.get(key)), one, many)
        for key, one, many in (
            ("friends", "friend", "friends"),
            ("stories", "story", "stories"),
            ("memories", "memory", "memories"),
        )
    ]
    what = ["A whole library: " + ", ".join(counted) + "."]
    if pictures := _n(holds.get("pictures")):
        what.append(f"{_count(pictures, 'picture')}.")
    return {
        "kind": "kataki",
        "title": "A Kataki library",
        "what": what,
        "notes": [
            # what archive.REPLACED really does, in the words of the screens that own those rows
            "Your model servers, the model doing each job, your settings and your tags are "
            "replaced by this file's.",
            "Everything else here must already be empty: stories and friends are never merged.",
            "It says what it holds itself, and a file can be wrong about that.",
        ],
        "needs_story": False,
    }


def look(blob: bytes) -> dict:
    """What this file would become. Raises BadCard when it is nothing we know how to read."""
    if not blob:
        raise BadCard("that file is empty.")
    if len(blob) > MAX_BYTES:
        raise BadCard(f"that file is too big to bring in ({MAX_BYTES // 2**20} MB at most).")
    # A .kataki is a zip that says so; a CHARX is a zip that carries a card.json. Ask the zip.
    if blob[:4] == ZIP:
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                names = set(z.namelist())
            if "kataki.json" in names:
                return _library(blob)
        except archive.BadArchive as e:
            raise BadCard(str(e)) from None
        except cards.ZIP_TROUBLE as e:  # a member that will not open is not a crash
            raise BadCard(f"that library could not be read ({e}).") from None
        return _card(blob)
    if blob.startswith(cards.PNG_MAGIC):
        return _card(blob)
    # Past here it is text. Other apps write JSON with a byte-order mark, or as UTF-16; json
    # itself reads both, so the sniff has to look past the mark rather than at it.
    head = blob.lstrip()
    for mark in BOMS:
        if head.startswith(mark):
            head = head.removeprefix(mark).lstrip(b"\x00").lstrip()
            break
    if head[:1] not in (b"{", b"["):
        raise BadCard("that is not a card, a chat, a lorebook or a Kataki library.")
    try:
        whole = json.loads(blob)
        # a card that carries a book is still a card; a book on its own is a book
        if isinstance(whole, dict) and lore._book(whole) is not None:
            inner = whole.get("data") if isinstance(whole.get("data"), dict) else whole
            if not isinstance(inner, dict) or "entries" in inner:
                return _lorebook(blob)
    except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
        return _chat(blob)  # more than one object: the only shape that is
    try:
        return _card(blob)
    except BadCard:
        return _chat(blob)  # a single-line chat file is one object too
