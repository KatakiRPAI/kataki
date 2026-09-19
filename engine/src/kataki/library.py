"""Library templates (characters, places, scenarios), tags, and starting a story from them.

An item's `data` is a JSON object. The engine reads `aliases`, `first_message` and
`example_dialogue`; the rest belongs to the app and the engine only stores it: `persona` and
`favourite` (bools), `pronouns` ("she" | "he" | "they"), `palette` ({bg: [from, to], ink}),
`portrait` and `image` (media names, see media.py).
"""

import json
import sqlite3

from kataki import chat

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
        "INSERT INTO entities(story_id, kind, name, description, private, examples, lib_item_id,"
        " is_ai) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
        (
            story_id,
            item["kind"],
            item["name"],
            item["description"],
            item["private"],
            item["data"].get("example_dialogue") or "",
            item["id"],
            is_ai,
        ),
    ).lastrowid
    for alias in {item["name"], *item["data"].get("aliases", [])}:
        conn.execute("INSERT INTO aliases(entity_id, alias) VALUES(?, ?)", (entity_id, alias))
    return entity_id


def create_story(
    conn: sqlite3.Connection,
    title: str,
    character_ids: list[int] | tuple = (),
    place_id: int | None = None,
    persona_id: int | None = None,  # None = director mode: the user plays no one
    scenario_id: int | None = None,
) -> int:
    scenario = get_item(conn, scenario_id) if scenario_id is not None else None
    # The premise is copied too, so editing the plot in the library never rewrites this story.
    overrides = {"premise": scenario["description"]} if scenario else {}
    with conn:
        story_id = conn.execute(
            "INSERT INTO stories(title, scenario_id, overrides) VALUES(?, ?, ?)",
            (title, scenario_id, json.dumps(overrides)),
        ).lastrowid
        cast = [(get_item(conn, i), True) for i in character_ids]
        if persona_id is not None:
            cast.append((get_item(conn, persona_id), False))
        entity_ids = [_instantiate(conn, story_id, item, is_ai) for item, is_ai in cast]
        if persona_id is not None:
            conn.execute(
                "UPDATE stories SET persona_entity_id=? WHERE id=?", (entity_ids[-1], story_id)
            )

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

        # The opening line: the scenario's (narrated), else the first AI character's greeting.
        opening = (None, scenario["data"].get("first_message")) if scenario else (None, None)
        if not opening[1]:
            greeters = (
                (entity_id, item["data"].get("first_message"))
                for entity_id, (item, is_ai) in zip(entity_ids, cast, strict=True)
                if is_ai
            )
            opening = next((g for g in greeters if g[1]), (None, None))
        if opening[1]:
            leaf = conn.execute(
                "INSERT INTO messages(story_id, role, speaker_id, text, story_time, scene_id)"
                " VALUES(?, 'assistant', ?, ?, 0, ?)",
                (story_id, opening[0], opening[1], scene_id),
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
) -> int:
    """A memory written by the user: true, dated now, known to `knower_ids` (or to everyone
    if `common`). `pinned` keeps it in the stable part of every prompt, like a lorebook entry."""
    path = chat.active_path(conn, story_id)
    now = path[-1]["story_time"] if path else 0
    with conn:
        memory_id = conn.execute(
            "INSERT INTO memories(story_id, kind, story_time, detail, gist, importance, is_true,"
            " common, pinned) VALUES(?, ?, ?, ?, ?, ?, 1, ?, ?)",
            (story_id, kind, now, detail, gist or detail, importance, common, pinned),
        ).lastrowid
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
