"""Library templates (characters, places, scenarios), tags, and starting a story from them.

An item's `data` is a JSON object. The engine reads `aliases`, `first_message` and
`example_dialogue`; the rest belongs to the app and the engine only stores it: `persona` and
`favourite` (bools), `pronouns` ("she" | "he" | "they"), `palette` ({bg: [from, to], ink}),
`portrait` and `image` (media names, see media.py).
"""

import json
import logging
import sqlite3

from kataki import cards, chat, goals, honesty

ITEM_FIELDS = ("name", "description", "private", "data")


def set_tags(conn: sqlite3.Connection, obj: str, obj_id: int, names: list[str]) -> None:
    conn.execute("DELETE FROM taggings WHERE obj=? AND obj_id=?", (obj, obj_id))
    for name in names:
        conn.execute("INSERT OR IGNORE INTO tags(name) VALUES(?)", (name,))
        conn.execute(
            "INSERT OR IGNORE INTO taggings(tag_id, obj, obj_id)"
            " SELECT id, ?, ? FROM tags WHERE name=?",
            (obj, obj_id, name),
        )


def get_tags(conn: sqlite3.Connection, obj: str, obj_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM tags JOIN taggings ON tag_id=tags.id"
        " WHERE obj=? AND obj_id=? ORDER BY name COLLATE NOCASE",
        (obj, obj_id),
    )
    return [r["name"] for r in rows]


def _item(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    tags = get_tags(conn, "lib_item", row["id"])
    return {**row, "data": json.loads(row["data"]), "tags": tags}


def create_item(
    conn: sqlite3.Connection,
    kind: str,
    name: str,
    description: str = "",
    private: str = "",
    data: dict | None = None,
    tags: list[str] | None = None,
) -> int:
    with conn:
        item_id = conn.execute(
            "INSERT INTO lib_items(kind, name, description, private, data) VALUES(?, ?, ?, ?, ?)",
            (kind, name, description, private, json.dumps(data or {})),
        ).lastrowid
        set_tags(conn, "lib_item", item_id, tags or [])
    return item_id


def get_item(conn: sqlite3.Connection, item_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM lib_items WHERE id=?", (item_id,)).fetchone()
    return _item(conn, row) if row else None


def list_items(conn: sqlite3.Connection, kind: str | None = None, tag: str | None = None) -> list:
    sql, args = "SELECT * FROM lib_items WHERE 1", []
    if kind:
        sql, args = sql + " AND kind=?", [*args, kind]
    if tag:
        sql += (
            " AND id IN (SELECT obj_id FROM taggings JOIN tags ON tags.id=tag_id"
            " WHERE obj='lib_item' AND name=?)"
        )
        args.append(tag)
    return [_item(conn, r) for r in conn.execute(sql + " ORDER BY name COLLATE NOCASE", args)]


def update_item(conn: sqlite3.Connection, item_id: int, **fields) -> None:
    tags = fields.pop("tags", None)
    if unknown := set(fields) - set(ITEM_FIELDS):
        raise ValueError(f"unknown field(s): {', '.join(sorted(unknown))}")
    if "data" in fields:
        fields["data"] = json.dumps(fields["data"])
    with conn:
        assignments = ", ".join(f"{name}=?" for name in fields)  # names are whitelisted above
        conn.execute(
            f"UPDATE lib_items SET {assignments}{', ' if fields else ''}"
            "updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (*fields.values(), item_id),
        )
        if tags is not None:
            set_tags(conn, "lib_item", item_id, tags)


def delete_item(conn: sqlite3.Connection, item_id: int) -> None:
    """Stories keep their copies: they only lose the link back to the library. A story that
    used the item as its plot keeps its premise (copied now if it didn't have one yet)."""
    with conn:
        conn.execute(
            "UPDATE stories SET scenario_id=NULL, overrides=json_insert(overrides, '$.premise',"
            " (SELECT description FROM lib_items WHERE id=?)) WHERE scenario_id=?",
            (item_id, item_id),
        )
        conn.execute("UPDATE entities SET lib_item_id=NULL WHERE lib_item_id=?", (item_id,))
        set_tags(conn, "lib_item", item_id, [])  # taggings are polymorphic, so no FK cascade
        conn.execute("DELETE FROM lib_items WHERE id=?", (item_id,))


def _instantiate(conn: sqlite3.Connection, story_id: int, item: dict, is_ai: bool) -> int:
    """Snapshot a template into the story. The story may diverge; library edits never reach it."""
    entity_id = conn.execute(
        "INSERT INTO entities(story_id, kind, name, description, private, examples, looks,"
        " lib_item_id, is_ai) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            story_id,
            item["kind"],
            item["name"],
            item["description"],
            item["private"],
            item["data"].get("example_dialogue") or "",
            item["data"].get("looks") or "",
            item["id"],
            is_ai,
        ),
    ).lastrowid
    for alias in {item["name"], *item["data"].get("aliases", [])}:
        # OR IGNORE: aliases are case-blind, so "Mira" and "MIRA" are one name, not a crash
        conn.execute(
            "INSERT OR IGNORE INTO aliases(entity_id, alias) VALUES(?, ?)", (entity_id, alias)
        )
    return entity_id


# The editor's words (F2 › Relationships) as the engine's relationship words; "never met" is none.
RELATIONSHIP = {
    "friend": "friend of",
    "fond": "fond of",
    "wary": "wary of",
    "rival": "rival of",
    "family": "family of",
}


def create_story(
    conn: sqlite3.Connection,
    title: str,
    character_ids: list[int] | tuple = (),
    place_id: int | None = None,
    persona_id: int | None = None,  # None = director mode: the user plays no one
    scenario_id: int | None = None,
    epoch_offset_min: int = 480,  # the clock at story time 0: Day 1, 08:00
    opening: bool = True,  # False: a story that already has its first line, as an import does
    first_message: str = "",  # how this story opens, typed when it starts; beats the plot's
) -> int:
    scenario = get_item(conn, scenario_id) if scenario_id is not None else None
    # The premise is copied too, so editing the plot in the library never rewrites this story.
    overrides = {"premise": scenario["description"]} if scenario else {}
    with conn:
        story_id = conn.execute(
            "INSERT INTO stories(title, scenario_id, overrides, epoch_offset_min)"
            " VALUES(?, ?, ?, ?)",
            (title, scenario_id, json.dumps(overrides), epoch_offset_min),
        ).lastrowid
        cast = [(get_item(conn, i), True) for i in character_ids]
        if persona_id is not None:
            cast.append((get_item(conn, persona_id), False))
        entity_ids = [_instantiate(conn, story_id, item, is_ai) for item, is_ai in cast]
        if persona_id is not None:
            conn.execute(
                "UPDATE stories SET persona_entity_id=? WHERE id=?", (entity_ids[-1], story_id)
            )

        # What a character's profile says they feel about someone else here starts the story
        # (the memory reader moves it on from there).
        by_item = {item["id"]: e for (item, _), e in zip(cast, entity_ids, strict=True)}
        for (item, _), src in zip(cast, entity_ids, strict=True):
            for r in item["data"].get("relationships") or []:
                dst = by_item.get(r.get("id"))
                if dst and dst != src and (rel := RELATIONSHIP.get(r.get("feels"))):
                    conn.execute(
                        "INSERT INTO edges(story_id, src_id, dst_id, rel, story_time) VALUES(?, ?, ?, ?, 0)",
                        (story_id, src, dst, rel),
                    )
        # ...and so do the secrets they keep (minds slice 4)
        try:  # a card's secrets never cost the story
            honesty.seed(
                conn, story_id, [(item, e) for (item, _), e in zip(cast, entity_ids, strict=True)]
            )
        except Exception as e:
            logging.getLogger(__name__).warning("secrets not seeded for story %s: %s", story_id, e)
        try:  # ...and what they want (minds slice 7)
            goals.seed(
                conn, story_id, [(item, e) for (item, _), e in zip(cast, entity_ids, strict=True)]
            )
        except Exception as e:
            logging.getLogger(__name__).warning("goals not seeded for story %s: %s", story_id, e)

        place_entity = None
        if place_id is not None:
            place_entity = _instantiate(conn, story_id, get_item(conn, place_id), False)
        scene_id = conn.execute(
            "INSERT INTO scenes(story_id, place_id, start_story_time) VALUES(?, ?, 0)",
            (story_id, place_entity),
        ).lastrowid
        for entity_id in entity_ids:
            conn.execute(
                "INSERT INTO presence(scene_id, entity_id, present) VALUES(?, ?, 1)",
                (scene_id, entity_id),
            )

        # The opening line (narrated): the one typed for this story, else the plot's, else the
        # first AI character's greeting (an imported card brings one).
        first = (
            None,
            first_message.strip() or (scenario and scenario["data"].get("first_message")),
        )
        if not first[1]:
            greeters = (
                (entity_id, item["data"].get("first_message"))
                for entity_id, (item, is_ai) in zip(entity_ids, cast, strict=True)
                if is_ai
            )
            first = next((g for g in greeters if g[1]), (None, None))
        if opening and first[1]:
            # An imported card says `{{user}}`; here we finally know who that is.
            player = next((item["name"] for item, is_ai in cast if not is_ai), "you")
            leaf = conn.execute(
                "INSERT INTO messages(story_id, role, speaker_id, text, story_time, scene_id)"
                " VALUES(?, 'assistant', ?, ?, 0, ?)",
                (story_id, first[0], cards.macros(first[1], user=player), scene_id),
            ).lastrowid
            conn.execute("UPDATE stories SET active_leaf_id=? WHERE id=?", (leaf, story_id))
    return story_id


def add_to_story(conn: sqlite3.Connection, story_id: int, item_id: int) -> int:
    """Bring a library character or place into a running story (once): its entity id."""
    found = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND lib_item_id=?", (story_id, item_id)
    ).fetchone()
    if found:
        return found["id"]
    item = get_item(conn, item_id)
    with conn:
        return _instantiate(conn, story_id, item, is_ai=item["kind"] == "character")


def add_memory(
    conn: sqlite3.Connection,
    story_id: int,
    detail: str,
    gist: str | None = None,
    importance: int = 5,
    kind: str = "fact",
    knower_ids: list[int] | tuple = (),
    entity_ids: list[int] | tuple = (),
    common: bool = False,
    pinned: bool = False,
    tags: list[str] | tuple = (),
) -> int:
    """A memory written by the user: true, dated now, known to `knower_ids` (or to everyone
    if `common`). `pinned` keeps it in the stable part of every prompt, like a lorebook entry.
    `tags` are words that cue it, indexed for recall the same way an extraction's are."""
    path = chat.active_path(conn, story_id)
    now = path[-1]["story_time"] if path else 0
    with conn:
        memory_id = conn.execute(
            "INSERT INTO memories(story_id, kind, story_time, detail, gist, importance, is_true,"
            " common, pinned, tags_text) VALUES(?, ?, ?, ?, ?, ?, 1, ?, ?, ?)",
            (
                story_id,
                kind,
                now,
                detail,
                gist or detail,
                importance,
                common,
                pinned,
                " ".join(tags),
            ),
        ).lastrowid
        set_tags(conn, "memory", memory_id, list(tags))
        for entity_id in entity_ids:
            conn.execute(
                "INSERT INTO memory_entities(memory_id, entity_id, role) VALUES(?, ?, 'subject')",
                (memory_id, entity_id),
            )
        for knower in knower_ids:
            conn.execute(
                "INSERT INTO knowledge(knower_id, memory_id, source, learned_story_time)"
                " VALUES(?, ?, 'innate', ?)",
                (knower, memory_id, now),
            )
    return memory_id


def merge_entities(conn: sqlite3.Connection, keep: int, drop: int) -> None:
    """Two entities turned out to be one. Everything that pointed at `drop` now points at
    `keep`, and its names become aliases of `keep`. `drop` is hidden, never deleted."""
    moves = [
        ("knowledge", "knower_id"),
        ("knowledge", "told_by_id"),
        ("memories", "asserted_by"),
        ("flags", "entity_id"),
        ("edges", "src_id"),
        ("edges", "dst_id"),
        ("presence", "entity_id"),
        ("messages", "speaker_id"),
        ("scenes", "place_id"),
        ("stories", "persona_entity_id"),
        ("opinions", "src_id"),
        ("opinions", "dst_id"),
        ("mind_states", "entity_id"),
        ("secrets", "owner_id"),
        ("seeds", "entity_id"),
        ("seeds", "about_id"),  # ponytail: conceal_from ids are JSON, not remapped (owed)
        ("recollections", "knower_id"),
        ("goals", "entity_id"),
        ("reflections", "knower_id"),
        ("reflections", "subject_id"),
    ]
    with conn:
        for table, column in moves:
            conn.execute(f"UPDATE {table} SET {column}=? WHERE {column}=?", (keep, drop))
        for table, column in (("memory_entities", "entity_id"), ("accesses", "knower_id")):
            # rows keep's copy already has would collide; the leftovers are those duplicates
            conn.execute(f"UPDATE OR IGNORE {table} SET {column}=? WHERE {column}=?", (keep, drop))
            conn.execute(f"DELETE FROM {table} WHERE {column}=?", (drop,))
        conn.execute(
            "INSERT OR IGNORE INTO aliases(entity_id, alias)"
            " SELECT ?, alias FROM aliases WHERE entity_id=?",
            (keep, drop),
        )
        conn.execute(
            "UPDATE OR IGNORE taggings SET obj_id=? WHERE obj='entity' AND obj_id=?", (keep, drop)
        )
        conn.execute("UPDATE entities SET hidden=1, merge_candidate_id=? WHERE id=?", (keep, drop))


# --- books: stories that belong together, in an order -------------------------------------------


def create_book(conn: sqlite3.Connection, title: str, blurb: str = "") -> int:
    with conn:
        cur = conn.execute("INSERT INTO books(title, blurb) VALUES(?, ?)", (title, blurb))
    return cur.lastrowid


def get_book(conn: sqlite3.Connection, book_id: int) -> dict | None:
    row = conn.execute(
        "SELECT b.*, (SELECT count(*) FROM stories WHERE book_id=b.id) AS stories"
        " FROM books b WHERE b.id=?",
        (book_id,),
    ).fetchone()
    return dict(row) if row else None


def list_books(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT b.*, (SELECT count(*) FROM stories WHERE book_id=b.id) AS stories"
        " FROM books b ORDER BY b.title COLLATE NOCASE"
    )
    return [dict(r) for r in rows]


def update_book(conn: sqlite3.Connection, book_id: int, **fields) -> None:
    keep = {k: v for k, v in fields.items() if k in ("title", "blurb") and v is not None}
    if not keep:
        return
    sets = ", ".join(f"{k}=?" for k in keep)
    with conn:
        conn.execute(f"UPDATE books SET {sets} WHERE id=?", [*keep.values(), book_id])


def delete_book(conn: sqlite3.Connection, book_id: int) -> None:
    """The book goes; its stories, places and plots stay, not filed anywhere. (`stories.book_id`
    has no key to cascade: the column is older than the table.)"""
    with conn:
        conn.execute("UPDATE stories SET book_id=NULL, book_order=0 WHERE book_id=?", (book_id,))
        conn.execute(
            "UPDATE lib_items SET data=json_remove(data, '$.links.book')"
            " WHERE json_extract(data, '$.links.book')=?",
            (book_id,),
        )
        conn.execute("DELETE FROM books WHERE id=?", (book_id,))


def set_book(conn: sqlite3.Connection, story_id: int, book_id: int | None) -> None:
    """Put a story in a book (at the end) or take it out of the one it is in."""
    if book_id is not None and get_book(conn, book_id) is None:
        raise ValueError(f"no book {book_id}")
    last = conn.execute(
        "SELECT coalesce(max(book_order), 0) FROM stories WHERE book_id=?", (book_id,)
    ).fetchone()[0]
    with conn:
        conn.execute(
            "UPDATE stories SET book_id=?, book_order=? WHERE id=?",
            (book_id, 0 if book_id is None else last + 1, story_id),
        )


def order_book(conn: sqlite3.Connection, book_id: int, story_ids: list[int]) -> None:
    """The order the stories read in; any the caller leaves out keep theirs, after these."""
    with conn:
        for i, story_id in enumerate(story_ids, start=1):
            conn.execute(
                "UPDATE stories SET book_order=? WHERE id=? AND book_id=?", (i, story_id, book_id)
            )


def book_stories(conn: sqlite3.Connection, book_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT id, title FROM stories WHERE book_id=? ORDER BY book_order, id", (book_id,)
    )
    return [dict(r) for r in rows]


# --- chapters: a stretch of one story's own lines -----------------------------------------------


def open_chapter(conn: sqlite3.Connection, story_id: int, title: str, from_message_id: int) -> int:
    """Start a chapter at a line. Whatever chapter was running ends at the line before it."""
    line = conn.execute(
        "SELECT id FROM messages WHERE id=? AND story_id=?", (from_message_id, story_id)
    ).fetchone()
    if line is None:
        raise ValueError(f"no line {from_message_id} in this story")
    # One beginning per line. A second chapter starting where one already does would run over it:
    # the one below closes chapters that began *earlier*, and there is no line before this to end.
    if conn.execute(
        "SELECT 1 FROM chapters WHERE story_id=? AND from_message_id=?", (story_id, from_message_id)
    ).fetchone():
        raise ValueError("a chapter already begins at that line")
    with conn:
        # Nothing may run over the new chapter: whatever covered this line now ends just before it,
        # whether it was still running or had been closed further along.
        conn.execute(
            "UPDATE chapters SET to_message_id="
            "(SELECT max(id) FROM messages WHERE story_id=? AND id<?)"
            " WHERE story_id=? AND from_message_id<?"
            " AND (to_message_id IS NULL OR to_message_id>=?)",
            (story_id, from_message_id, story_id, from_message_id, from_message_id),
        )
        # And the new one may not run over what already begins after it.
        ends = conn.execute(
            "SELECT max(id) FROM messages WHERE story_id=? AND id<"
            "(SELECT min(from_message_id) FROM chapters WHERE story_id=? AND from_message_id>?)",
            (story_id, story_id, from_message_id),
        ).fetchone()[0]
        cur = conn.execute(
            "INSERT INTO chapters(story_id, title, from_message_id, to_message_id) VALUES(?,?,?,?)",
            (story_id, title, from_message_id, ends),
        )
    return cur.lastrowid


def chapters(conn: sqlite3.Connection, story_id: int) -> list[dict]:
    """Every chapter of this story, in order. The last one is open unless it was closed: it runs
    to whatever the newest line is, and says so as it grows. A chapter counts the lines a reader
    can read — the story's own markers are not lines anybody said, and a take that was thrown
    away is not in the story at all — so the count follows the path the story is on."""
    rows = conn.execute(
        "SELECT * FROM chapters WHERE story_id=? ORDER BY from_message_id, id", (story_id,)
    ).fetchall()
    path = chat.active_path(conn, story_id)
    newest = path[-1]["id"] if path else None
    out = []
    for r in rows:
        ends = r["to_message_id"] or newest
        lines = sum(
            1
            for m in path
            if m["role"] != "system" and r["from_message_id"] <= m["id"] <= (ends or -1)
        )
        out.append({**dict(r), "open": r["to_message_id"] is None, "ends_at": ends, "lines": lines})
    return out


def close_chapter(conn: sqlite3.Connection, chapter_id: int, to_message_id: int | None) -> None:
    with conn:
        conn.execute("UPDATE chapters SET to_message_id=? WHERE id=?", (to_message_id, chapter_id))


def delete_chapter(conn: sqlite3.Connection, chapter_id: int) -> None:
    """The chapter goes; the one before it runs on into the space it left."""
    row = conn.execute("SELECT * FROM chapters WHERE id=?", (chapter_id,)).fetchone()
    if row is None:
        return
    with conn:
        conn.execute("DELETE FROM chapters WHERE id=?", (chapter_id,))
        before = conn.execute(
            "SELECT id FROM chapters WHERE story_id=? AND from_message_id<?"
            " ORDER BY from_message_id DESC LIMIT 1",
            (row["story_id"], row["from_message_id"]),
        ).fetchone()
        if before:
            conn.execute(
                "UPDATE chapters SET to_message_id=? WHERE id=?",
                (row["to_message_id"], before["id"]),
            )


def all_tags(conn: sqlite3.Connection) -> list[dict]:
    """Every tag the library shelves by, with how many friends and stories wear it. A memory's
    tags are cue words inside one story, not a shelf, so they are not offered here."""
    rows = conn.execute(
        "SELECT t.name,"
        " sum(g.obj='lib_item') AS items, sum(g.obj='story') AS stories"
        " FROM tags t JOIN taggings g ON g.tag_id=t.id"
        " WHERE g.obj IN ('lib_item','story')"
        " GROUP BY t.id ORDER BY t.name COLLATE NOCASE"
    )
    return [{"name": r["name"], "items": r["items"], "stories": r["stories"]} for r in rows]


# --- the same person, in more than one story ----------------------------------------------------


def same_person(conn: sqlite3.Connection, item_id: int) -> list[dict]:
    """Every story this library item plays in, and what that self holds there. Two entities are
    the same person when they came from the same item, or when one was adopted into it."""
    rows = conn.execute(
        "SELECT e.id AS entity_id, e.name, e.story_id, s.title AS story, e.is_ai,"
        " (SELECT count(*) FROM knowledge k WHERE k.knower_id=e.id) AS remembers"
        " FROM entities e JOIN stories s ON s.id=e.story_id"
        " WHERE e.hidden=0 AND (e.lib_item_id=? OR e.origin_entity_id IN"
        "   (SELECT id FROM entities WHERE lib_item_id=?))"
        " ORDER BY e.story_id",
        (item_id, item_id),
    )
    return [dict(r) for r in rows]


def adopt(conn: sqlite3.Connection, entity_id: int) -> int:
    """Make a library item out of someone the reader found, and point their story self at it, so
    they can walk into another story as themselves. Adopting twice is not two people."""
    e = conn.execute("SELECT * FROM entities WHERE id=?", (entity_id,)).fetchone()
    if e is None:
        raise ValueError(f"no entity {entity_id}")
    if e["lib_item_id"]:
        return e["lib_item_id"]
    aliases = [
        a["alias"]
        for a in conn.execute("SELECT alias FROM aliases WHERE entity_id=?", (entity_id,))
        if a["alias"] != e["name"]
    ]
    item_id = create_item(
        conn,
        e["kind"] if e["kind"] in ("character", "place") else "character",
        e["name"],
        description=e["description"] or e["summary"] or "",
        private=e["private"] or "",
        data={"aliases": aliases, "example_dialogue": e["examples"] or "", "looks": e["looks"]},
    )
    with conn:
        conn.execute("UPDATE entities SET lib_item_id=? WHERE id=?", (item_id, entity_id))
    return item_id


# --- story links: how two stories sit in each other's time ---------------------------------------


def link_stories(
    conn: sqlite3.Connection,
    from_story_id: int,
    to_story_id: int,
    kind: str = "continuation",
    offset_min: int = 0,
    note: str | None = None,
) -> int:
    """`from` looks back at `to`, `offset_min` minutes later. A story cannot look at itself."""
    if from_story_id == to_story_id:
        raise ValueError("a story cannot be linked to itself")
    for sid in (from_story_id, to_story_id):
        if conn.execute("SELECT 1 FROM stories WHERE id=?", (sid,)).fetchone() is None:
            raise ValueError(f"no story {sid}")
    with conn:
        cur = conn.execute(
            "INSERT OR REPLACE INTO story_links(from_story_id, to_story_id, kind, offset_min, note)"
            " VALUES(?, ?, ?, ?, ?)",
            (from_story_id, to_story_id, kind, offset_min, note),
        )
    return cur.lastrowid


def links_of(conn: sqlite3.Connection, story_id: int) -> list[dict]:
    """Both ways: what this story looks back at, and what looks back at it."""
    rows = conn.execute(
        "SELECT l.*, f.title AS from_title, t.title AS to_title FROM story_links l"
        " JOIN stories f ON f.id=l.from_story_id JOIN stories t ON t.id=l.to_story_id"
        " WHERE l.from_story_id=? OR l.to_story_id=? ORDER BY l.id",
        (story_id, story_id),
    )
    return [
        {**dict(r), "direction": "back" if r["from_story_id"] == story_id else "forward"}
        for r in rows
    ]


def unlink_stories(conn: sqlite3.Connection, link_id: int) -> None:
    with conn:
        conn.execute("DELETE FROM story_links WHERE id=?", (link_id,))


def _columns(conn: sqlite3.Connection, table: str, skip: set[str]) -> list[str]:
    return [c["name"] for c in conn.execute(f"PRAGMA table_info({table})") if c["name"] not in skip]


def branch_story(conn: sqlite3.Connection, message_id: int) -> int:
    """A new story that is this one up to `message_id`: its people, places, scenes and lines.
    What the memory reader made is not copied; it reads the copied lines again."""

    m = chat.get_message(conn, message_id)
    old = conn.execute("SELECT * FROM stories WHERE id=?", (m["story_id"],)).fetchone()
    path = chat.path_to(conn, message_id)
    on_path = {p["id"] for p in path}
    with conn:
        new = conn.execute(
            "INSERT INTO stories(title, scenario_id, epoch_offset_min, minutes_per_turn, overrides,"
            " book_id) VALUES(?, ?, ?, ?, ?, ?)",
            (f"{old['title']} · branch", old["scenario_id"], old["epoch_offset_min"],
             old["minutes_per_turn"], old["overrides"], old["book_id"]),
        ).lastrowid  # fmt: skip
        ent: dict[int, int] = {}
        cols = _columns(conn, "entities", {"id", "story_id", "run_id", "merge_candidate_id"})
        for e in conn.execute(
            "SELECT * FROM entities WHERE story_id=? AND run_id IS NULL", (old["id"],)
        ):
            ent[e["id"]] = conn.execute(
                f"INSERT INTO entities(story_id, {', '.join(cols)}) VALUES(?, {', '.join('?' * len(cols))})",
                (new, *(e[c] for c in cols)),
            ).lastrowid
            for a in conn.execute("SELECT alias FROM aliases WHERE entity_id=?", (e["id"],)):
                conn.execute(
                    "INSERT OR IGNORE INTO aliases(entity_id, alias) VALUES(?, ?)",
                    (ent[e["id"]], a["alias"]),
                )
        conn.execute(
            "UPDATE stories SET persona_entity_id=? WHERE id=?",
            (ent.get(old["persona_entity_id"]), new),
        )
        scenes: dict[int, int] = {}
        for s in conn.execute("SELECT * FROM scenes WHERE story_id=? ORDER BY id", (old["id"],)):
            if s["start_message_id"] is None or s["start_message_id"] in on_path:
                scenes[s["id"]] = conn.execute(
                    "INSERT INTO scenes(story_id, place_id, title, start_story_time, mood, media)"
                    " VALUES(?, ?, ?, ?, ?, ?)",
                    (
                        new,
                        ent.get(s["place_id"]),
                        s["title"],
                        s["start_story_time"],
                        s["mood"],
                        s["media"],
                    ),
                ).lastrowid
        msg: dict[int, int] = {}
        cols = _columns(
            conn, "messages", {"id", "story_id", "parent_id", "speaker_id", "scene_id", "audience"}
        )
        for p in path:
            audience = (
                json.loads(p["audience"]) if "audience" in p.keys() and p["audience"] else None
            )
            mapped = (
                None if audience is None else json.dumps([ent[a] for a in audience if a in ent])
            )
            msg[p["id"]] = conn.execute(
                f"INSERT INTO messages(story_id, parent_id, speaker_id, scene_id, audience, {', '.join(cols)})"
                f" VALUES(?, ?, ?, ?, ?, {', '.join('?' * len(cols))})",
                (new, msg.get(p["parent_id"]), ent.get(p["speaker_id"]), scenes.get(p["scene_id"]), mapped,
                 *(p[c] for c in cols)),
            ).lastrowid  # fmt: skip
        for old_id, new_id in scenes.items():
            start = conn.execute(
                "SELECT start_message_id FROM scenes WHERE id=?", (old_id,)
            ).fetchone()[0]
            if start is not None:
                conn.execute(
                    "UPDATE scenes SET start_message_id=? WHERE id=?", (msg[start], new_id)
                )
        for r in conn.execute(
            "SELECT p.* FROM presence p JOIN scenes s ON s.id=p.scene_id WHERE s.story_id=?",
            (old["id"],),
        ):
            if (
                r["scene_id"] in scenes
                and r["entity_id"] in ent
                and (r["message_id"] is None or r["message_id"] in on_path)
            ):
                conn.execute(
                    "INSERT INTO presence(scene_id, entity_id, message_id, present) VALUES(?, ?, ?, ?)",
                    (
                        scenes[r["scene_id"]],
                        ent[r["entity_id"]],
                        msg.get(r["message_id"]),
                        r["present"],
                    ),
                )
        conn.execute("UPDATE stories SET active_leaf_id=? WHERE id=?", (msg[message_id], new))
    return new


def become(conn: sqlite3.Connection, story_id: int, persona_id: int) -> int:
    """The story's entity for this library persona, brought in (and put in the current scene)
    if they aren't in it yet. Characters meet the new person from the next line."""
    row = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND lib_item_id=? AND is_ai=0",
        (story_id, persona_id),
    ).fetchone()
    if row:
        return row["id"]
    if (item := get_item(conn, persona_id)) is None:
        raise ValueError(f"no library item {persona_id}")
    with conn:
        entity_id = _instantiate(conn, story_id, item, False)
        scene = conn.execute("SELECT max(id) FROM scenes WHERE story_id=?", (story_id,)).fetchone()[
            0
        ]
        if scene is not None:
            conn.execute(
                "INSERT INTO presence(scene_id, entity_id, present) VALUES(?, ?, 1)",
                (scene, entity_id),
            )
    return entity_id
