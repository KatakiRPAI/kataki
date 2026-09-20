"""A SillyTavern chat coming in: one JSONL file becomes one story.

The first line is the header — who was talking and when — and every line after it is a message:
`is_user` says which side said it, `mes` is what was said, and `swipes` are the other takes that
were generated at that point, with `swipe_id` saying which one was kept. All of that is already
the shape this engine keeps a story in, so a swipe becomes a take, and the kept one is the one
the story reads on.

Files written by SillyTavern's own converters (Ooba, Agnai, Kobold, Risu, CAI) say
`character_name: "unused"`, and files from Chub wrap every message as `{"message": "..."}`. Both
are read here the way SillyTavern itself reads them.

A chat names its people but describes none of them. So unless it is told which friends it is
about, it makes them: a chat is never a reason to write over someone who already exists.
"""

import json

from kataki import chat, library
from kataki.cards import BadCard

MAX_BYTES = 64 * 1024 * 1024  # a chat, not an archive
MAX_LINES = 50_000  # a story, not a corpus
MAX_TAKES = 64  # alternatives at one point in a story; a file offering more is not one
UNNAMED = "unused"  # what SillyTavern's converters write where a name would go


def _said(value) -> str | None:
    """The text of a message or a swipe. Chub wraps both in an object; SillyTavern unwraps it
    on the way in, so this does too."""
    if isinstance(value, dict):
        value = value.get("message")
    return value if isinstance(value, str) else None


def read(blob: bytes) -> tuple[dict, list[dict], int, int]:
    """(the header, the messages, how many lines were unreadable, how many never got read).
    A file that is only messages is fine; a file that is only a header is not a chat."""
    if len(blob) > MAX_BYTES:
        raise BadCard("that file is too big to be one chat (64 MB at most).")
    header: dict = {}
    lines: list[dict] = []
    broken = 0
    rows = blob.splitlines()
    for raw in rows[:MAX_LINES]:
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
            broken += 1
            continue
        if not isinstance(row, dict):
            broken += 1
        elif "mes" in row:
            lines.append(row)
        elif not header and not lines:
            header = row  # the first line, and it said nothing: it is the header
        else:
            broken += 1
    if not lines:
        raise BadCard("there is nothing in it that was said." if header else "that is not a chat.")
    return header, lines, broken, max(0, len(rows) - MAX_LINES)


def _named(header: dict, lines: list[dict], user: bool) -> str:
    """The name one side of the chat went by."""
    said = header.get("user_name" if user else "character_name")
    if isinstance(said, str) and said.strip() and said.strip() != UNNAMED:
        return said.strip()
    for m in lines:
        if bool(m.get("is_user")) is user and not m.get("is_system"):
            if isinstance(m.get("name"), str) and m["name"].strip():
                return m["name"].strip()
    return "You" if user else "Someone"


def _title(header: dict, lines: list[dict]) -> str:
    """What to call the story: who it was with, and the day it started."""
    who = _named(header, lines, user=False)
    when = header.get("create_date")
    day = when.split("@")[0].strip() if isinstance(when, str) and when.strip() else ""
    return f"{who} — {day}" if day else who


def _takes(m: dict) -> tuple[list[str], int]:
    """(every take at this point, which one the story reads on). The kept one is resolved
    before anything is dropped, so a blank swipe never shifts the choice onto its neighbour."""
    offered = m.get("swipes")
    offered = [_said(s) for s in offered] if isinstance(offered, list) else []
    mes = _said(m.get("mes"))

    at = m.get("swipe_id")  # a bool is an int in Python, and is not an index
    at = at if isinstance(at, int) and not isinstance(at, bool) else None
    chosen = mes if mes and mes.strip() else None
    if chosen is None and at is not None and 0 <= at < len(offered):
        chosen = offered[at]

    takes = [s for s in offered if s and s.strip()][:MAX_TAKES]
    if chosen and chosen not in takes:
        takes.append(chosen)  # what was kept is always one of the takes, wherever it came from
    return takes, takes.index(chosen) if chosen in takes else 0


def add(
    conn,
    blob: bytes,
    *,
    character_id: int | None = None,
    persona_id: int | None = None,
    title: str | None = None,
) -> dict:
    """Bring a chat in as a new story: what was made, and anything that could not be read.

    ponytail: a dozen statements and a couple of commits per line — 5000 messages take about
    four seconds, which is fine for something done once. Batch the inserts if that ever stops
    being true."""
    header, lines, broken, past = read(blob)
    notes = []
    if character_id is None:
        character_id = library.create_item(conn, "character", _named(header, lines, user=False))
        notes.append("the friend in this chat was not in the library, so she was made from it.")
    if persona_id is None:
        persona_id = library.create_item(
            conn, "character", _named(header, lines, user=True), data={"persona": True}
        )
        notes.append("so was the person you were playing.")

    story_id = library.create_story(
        conn,
        title or _title(header, lines),
        character_ids=[character_id],
        persona_id=persona_id,
        opening=False,  # the story starts where the file starts
    )
    hers, yours = (
        conn.execute(
            "SELECT id FROM entities WHERE story_id=? AND lib_item_id=?", (story_id, item)
        ).fetchone()["id"]
        for item in (character_id, persona_id)
    )
    scene_id = conn.execute(
        "SELECT id FROM scenes WHERE story_id=? ORDER BY id LIMIT 1", (story_id,)
    ).fetchone()["id"]

    # A group chat has more than one voice in it. Names are matched against the story's own
    # people first, so the friend you chose keeps her own lines whatever the file calls her.
    known = {
        r["name"].casefold(): r["id"]
        for r in conn.execute(
            "SELECT id, name FROM entities WHERE story_id=? AND is_ai=1 AND hidden=0", (story_id,)
        )
    }
    if isinstance(by := header.get("character_name"), str) and by.strip() not in ("", UNNAMED):
        known.setdefault(by.strip().casefold(), hers)  # the file's name for the friend you chose
    invented: list[str] = []

    def voice(name: str) -> int:
        if name.casefold() not in known:
            item = library.create_item(conn, "character", name)
            entity = library.add_to_story(conn, story_id, item)
            # and into the room: `add_to_story` only writes the person, not where they are
            with conn:
                conn.execute(
                    "INSERT INTO presence(scene_id, entity_id, present) VALUES(?, ?, 1)",
                    (scene_id, entity),
                )
            known[name.casefold()] = entity
            invented.append(name)
        return known[name.casefold()]

    made = takes = skipped = 0
    for m in lines:
        said, kept = _takes(m)
        if not said:
            skipped += 1
            continue
        # `is_system` is what SillyTavern marks when a line is kept out of the prompt — a notice,
        # or one somebody hid. It stays out of ours too, and it is still whoever said it.
        name = m.get("name") if isinstance(m.get("name"), str) and m["name"].strip() else None
        if m.get("is_user"):
            role, who = "user", yours
        elif m.get("is_system"):
            role, who = "assistant", None  # a notice the story made, in nobody's voice
        else:
            role, who = "assistant", voice(name.strip()) if name else hers

        first = chat.append_message(conn, story_id, role, said[0], speaker_id=who)
        ids = [first] + [chat.append_sibling(conn, first, other) for other in said[1:]]
        if m.get("is_system"):
            with conn:
                conn.execute(
                    f"UPDATE messages SET hidden=1 WHERE id IN ({','.join('?' * len(ids))})", ids
                )
        chat.set_leaf(conn, story_id, ids[kept])  # the take they kept is the one it reads on
        made += 1
        takes += len(ids) - 1

    if invented:
        notes.append(f"{', '.join(invented)} spoke in this chat and were made friends too.")
    if broken:
        notes.append(f"{broken} lines could not be read and were stepped over.")
    if skipped:
        notes.append(f"{skipped} lines had nothing in them.")
    if past:
        notes.append(f"this chat is longer than {MAX_LINES} lines; {past} of them stayed behind.")
    return {
        "story_id": story_id,
        "lines": made,
        "takes": takes,
        "skipped": skipped,
        "notes": notes,
    }
