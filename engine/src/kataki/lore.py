"""Lorebooks coming in: a character's own book, a `lorebook_v3` file, or a SillyTavern World
Info export, all landing as what a story already has a place for.

A `constant` entry is in every prompt wherever it came from, so here it is a **pinned** fact: it
lives in the stable block `context.build` writes once, and is never recalled on top of that.
Every other entry waits for its keywords, which is exactly what a memory's tags are: the words
that cued it in the other app are the words that cue it here.

Everything lands as common knowledge (the world, not one character's secret) written by the
user, so it is live on every branch and nothing an extraction run does can take it away.
"""

import json
import re

from kataki import cards, library
from kataki.cards import BadCard

IMPORTANCE = 6  # someone wrote this down on purpose, so a little above the middle
GIST = 120  # a hazy render is a glance at the fact, not the fact
# A V3 entry may carry decorators in its content: `@@depth 4`, and `@@@fallback` right after one.
# They are instructions to the app, not prose, and the spec says to take them out of the content
# before it ever reaches a prompt.
DECORATOR = re.compile(r"^@@@?([A-Za-z_]+)(?:[ \t].*)?$")


def _decorated(content: str) -> tuple[str, set[str]]:
    """(the prose, the decorators it carried). Two of them say something this engine already
    has a field for; the rest are dropped, which the spec allows and the prompt requires."""
    kept, found = [], set()
    for line in content.splitlines():
        if mark := DECORATOR.match(line.strip()):
            found.add(mark[1].lower())
        else:
            kept.append(line)
    return "\n".join(kept).strip(), found


def _book(thing, depth: int = 0) -> dict | None:
    """A Lorebook wherever it is hiding: alone, under `spec: lorebook_v3`, or inside a card.
    A card wraps its book one or two deep, so anything deeper than a handful is a file built to
    run us out of stack rather than a book."""
    if not isinstance(thing, dict) or depth > 8:
        return None
    if isinstance(thing.get("entries"), list | dict):
        return thing
    for key in ("data", "character_book"):
        if (found := _book(thing.get(key), depth + 1)) is not None:
            return found
    return None


def keeps(entry: dict) -> bool:
    """Whether this entry would become something a story knows. It has to be switched on, have
    words to say, and have some way to be cued: a key, the author's memo, or being always there.
    `add` below decides by this, and so does the preview, so the two can never disagree."""
    return bool(
        entry["enabled"]
        and entry["content"]
        and (entry["keys"] or entry["label"] or entry["constant"])
    )


def read(blob: bytes) -> dict:
    """The lorebook in a file: a JSON book, a card of any shape, or a card's PNG or CHARX."""
    thing: object
    if blob.startswith(cards.PNG_MAGIC) or blob[:4] == b"PK\x03\x04":
        _, _, thing, _ = cards.parse(blob)  # a card in a picture or a zip: take its book
    else:
        try:
            thing = json.loads(blob)
        except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
            raise BadCard("that is not a lorebook, a card or a World Info file.") from None
    book = _book(thing)
    if book is None or not entries(book):
        raise BadCard("there are no entries in this file to bring in.")
    return book


def entries(book: dict) -> list[dict]:
    """Every entry, in V3's words. SillyTavern keys its entries by uid and names its fields its
    own way (`key`, `disable`, `order`); the two say the same things."""
    raw = book.get("entries")
    listed = list(raw.values()) if isinstance(raw, dict) else list(raw or [])
    out = []
    for e in listed:
        if not isinstance(e, dict):
            continue
        keys = e.get("keys") if isinstance(e.get("keys"), list) else e.get("key")
        if isinstance(keys, str):
            keys = keys.split(",")  # a book that wrote its keys as one line, as some do
        elif not isinstance(keys, list):
            keys = []
        content, marks = _decorated(e["content"] if isinstance(e.get("content"), str) else "")
        # `@@activate` is the decorator spelling of `constant`, and `@@dont_activate` of off
        on = bool(e.get("enabled", not e.get("disable", False)))  # V3 says one, SillyTavern the
        out.append(  # other; a book that says neither is on
            {
                "keys": [k.strip() for k in keys if isinstance(k, str) and k.strip()],
                "content": content,
                "label": next(
                    (
                        e[k].strip()
                        for k in ("comment", "name")
                        if isinstance(e.get(k), str) and e[k].strip()
                    ),
                    "",
                ),
                "constant": bool(e.get("constant")) or "activate" in marks,
                "enabled": on and not ("dont_activate" in marks and "activate" not in marks),
            }
        )
    return out


def _gist(entry: dict) -> str:
    """What a hazy glance at this fact gives back: its opening, on one line. Not the author's
    label — "the tavern" is a good word to be cued by and a poor thing to remember."""
    said = " ".join(entry["content"].split())
    if len(said) <= GIST:
        return said
    return said[:GIST].rsplit(" ", 1)[0] + "…"


def add(conn, story_id: int, book: dict, *, char: str | None = None) -> dict:
    """Write a book into a story. Nothing merges: a book brought in twice is there twice, the
    same as every other import, because two facts that read alike may still be two facts."""
    # `{{char}}` is whoever's book this is, else the story's first character; `{{user}}` is the
    # player, and stays a macro in a story nobody is playing in.
    first = conn.execute(
        "SELECT name FROM entities WHERE story_id=? AND kind='character' AND is_ai=1"
        " AND hidden=0 ORDER BY id LIMIT 1",
        (story_id,),
    ).fetchone()
    player = conn.execute(
        "SELECT e.name FROM entities e JOIN stories s ON s.persona_entity_id=e.id WHERE s.id=?",
        (story_id,),
    ).fetchone()
    said = {
        "char": char or (first["name"] if first else None),
        # nobody is playing in a director's story, and the macro must still go: nothing
        # downstream resolves it, so a fact would say `{{user}}` to the model forever
        "user": player["name"] if player else "the user",
    }

    made = pinned = 0
    skipped, off = [], 0
    for entry in entries(book):
        if not entry["enabled"]:
            off += 1
            continue
        # the keys are words in the story, so they take the story's names too; the author's memo
        # is only a cue where there is no other ("do not delete (bridge)" is a note to a person)
        keys = [cards.macros(k, **said) for k in entry["keys"]]
        keys = list(dict.fromkeys(keys or ([entry["label"]] if entry["label"] else [])))
        if not keeps(entry):
            # no words, or no way to ever cue it: it would sit in the library saying nothing
            skipped.append(entry["label"] or _gist(entry) or "(an empty entry)")
            continue
        library.add_memory(
            conn,
            story_id,
            detail=cards.macros(entry["content"], **said),
            gist=cards.macros(_gist(entry), **said),
            importance=IMPORTANCE,
            common=True,
            pinned=entry["constant"],
            tags=keys,
        )
        made += 1
        pinned += entry["constant"]

    notes = []
    if off:
        notes.append(f"{off} entries were switched off where they came from and were left out.")
    if skipped:
        notes.append(f"{len(skipped)} entries had nothing to say, or no word that could cue them.")
    return {"made": made, "pinned": pinned, "skipped": skipped, "notes": notes}


def of_item(item: dict) -> dict | None:
    """The book an imported friend carries, if they carry one. `data` is the app's to write, so
    nothing in here is a shape this can count on."""
    card = item["data"].get("card") if isinstance(item.get("data"), dict) else None
    book = _book(card.get("character_book")) if isinstance(card, dict) else None
    return book if book is not None and entries(book) else None
