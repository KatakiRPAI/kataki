import json
import sqlite3

import pytest

from kataki import db

TABLES = {
    "providers", "model_roles", "settings", "lib_items", "stories", "messages", "scenes",
    "presence", "entities", "aliases", "tags", "taggings", "flags", "edges", "memories",
    "memory_entities", "memories_fts", "knowledge", "accesses", "embeddings", "summaries",
    "extraction_runs", "context_log",
}  # fmt: skip


def _rows(cursor):
    return [tuple(r) for r in cursor]  # sqlite3.Row never compares equal to a tuple


def _story(conn):
    return conn.execute("INSERT INTO stories(title) VALUES('s')").lastrowid


def _memory(conn, story_id, detail, run_id=None):
    return conn.execute(
        "INSERT INTO memories(story_id, kind, story_time, detail, gist, run_id)"
        " VALUES(?, 'event', 0, ?, 'gist', ?)",
        (story_id, detail, run_id),
    ).lastrowid


def test_connect_creates_every_table(conn):
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert TABLES <= names


def test_connect_enables_wal_and_foreign_keys(conn):
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_reconnect_keeps_data_and_schema_version(tmp_path):
    path = tmp_path / "library.db"
    first = db.connect(path)
    _story(first)
    first.commit()
    first.close()

    second = db.connect(path)
    assert second.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    assert second.execute("SELECT count(*) FROM stories").fetchone()[0] == 1
    assert second.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_memory_text_is_searchable_through_fts(conn):
    sid = _story(conn)
    mid = _memory(conn, sid, "Tobin betrayed the guild at the docks")
    hits = _rows(conn.execute("SELECT rowid FROM memories_fts WHERE memories_fts MATCH 'betray'"))
    assert hits == [(mid,)]  # porter stemming: betray matches betrayed


def test_deleting_a_run_wipes_everything_it_derived(conn):
    sid = _story(conn)
    run = conn.execute(
        "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger)"
        " VALUES(?, 1, 5, 'cadence')",
        (sid,),
    ).lastrowid
    _memory(conn, sid, "derived by the run", run_id=run)
    kept = _memory(conn, sid, "authored by the user")

    conn.execute("DELETE FROM extraction_runs WHERE id=?", (run,))

    assert _rows(conn.execute("SELECT id FROM memories")) == [(kept,)]
    assert (
        conn.execute(
            "SELECT count(*) FROM memories_fts WHERE memories_fts MATCH 'derived'"
        ).fetchone()[0]
        == 0
    )


def test_a_memory_is_reinforced_at_most_once_per_scene(conn):
    sid = _story(conn)
    mid = _memory(conn, sid, "x")
    scene = conn.execute(
        "INSERT INTO scenes(story_id, start_story_time) VALUES(?, 0)", (sid,)
    ).lastrowid
    sql = (
        "INSERT OR IGNORE INTO accesses"
        "(knower_id, memory_id, scene_id, kind, story_time, sharp, weight)"
        " VALUES(1, ?, ?, 'recall', ?, 0, 0.5)"
    )
    for t in (10, 20, 30):
        conn.execute(sql, (mid, scene, t))
    assert _rows(conn.execute("SELECT story_time FROM accesses")) == [(10,)]


def test_role_names_are_constrained(conn):
    conn.execute("INSERT INTO model_roles(role) VALUES('reasoning')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO model_roles(role) VALUES('chef')")


def test_json_columns_keep_a_bare_number_as_text(conn):
    # a column declared JSON gets NUMERIC affinity in SQLite and would turn '3.5' into 3.5
    conn.execute("INSERT INTO settings(key, value) VALUES('ratio', '3.5')")
    assert conn.execute("SELECT typeof(value) FROM settings").fetchone()[0] == "text"
    json_columns = [
        (t, c["name"])
        for (t,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for c in conn.execute(f"PRAGMA table_info({t})")
        if c["type"].upper() == "JSON"
    ]
    assert json_columns == []


def test_an_older_library_is_migrated_forward_without_losing_anything(tmp_path):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)  # a library from before any migration: schema v1 as shipped
    old.executescript((db.files("kataki") / "schema.sql").read_text(encoding="utf-8"))
    old.execute("PRAGMA user_version=1")
    old.execute("INSERT INTO stories(title) VALUES('kept')")
    old.execute(
        "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger)"
        " VALUES(1, 5, 7, 'cadence')"
    )
    old.execute(  # read from the story: its line is the end of the run's window
        "INSERT INTO memories(story_id, kind, story_time, detail, gist, to_message_id, run_id)"
        " VALUES(1, 'event', 0, 'd', 'g', 7, 1)"
    )
    old.execute(  # written by the user: no line
        "INSERT INTO memories(story_id, kind, story_time, detail, gist)"
        " VALUES(1, 'fact', 0, 'f', 'f')"
    )
    old.commit()
    old.close()

    conn = db.connect(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    assert conn.execute("SELECT title FROM stories").fetchone()[0] == "kept"
    tables = {t["name"] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"books", "chapters", "story_links"} <= tables  # v7
    story = conn.execute("SELECT book_id, book_order FROM stories").fetchone()
    assert (story["book_id"], story["book_order"]) == (None, 0)
    columns = {c["name"] for c in conn.execute("PRAGMA table_info(entities)")}
    assert "examples" in columns
    story = conn.execute("SELECT pinned, seen_run_id FROM stories").fetchone()  # v3
    assert (story["pinned"], story["seen_run_id"]) == (0, 0)
    columns = {c["name"] for c in conn.execute("PRAGMA table_info(messages)")}
    assert "audience" in columns  # v4
    columns = {c["name"] for c in conn.execute("PRAGMA table_info(presence)")}
    assert "run_id" in columns  # v5
    lines = conn.execute("SELECT message_id, contradicts_id FROM memories ORDER BY id")
    assert [tuple(r) for r in lines] == [(7, None), (None, None)]  # v6, backfilled
    conn.close()


def test_a_library_gains_books_chapters_and_links(tmp_path):
    """M2's hierarchy: a book holds stories, a chapter is a range of one story's own lines, and
    a link says how two stories sit in each other's time."""
    conn = db.connect(tmp_path / "m2.db")
    conn.execute(
        "INSERT INTO books(title, blurb) VALUES('The Gull Years', 'Everything at the bar')"
    )
    book = conn.execute("SELECT id FROM books").fetchone()["id"]
    conn.execute("INSERT INTO stories(title, book_id, book_order) VALUES('One', ?, 1)", (book,))
    conn.execute("INSERT INTO stories(title, book_id, book_order) VALUES('Two', ?, 2)", (book,))
    first, second = (r["id"] for r in conn.execute("SELECT id FROM stories ORDER BY id"))
    conn.execute(
        "INSERT INTO chapters(story_id, title, from_message_id) VALUES(?, 'The secret', 3)",
        (first,),
    )
    conn.execute(
        "INSERT INTO story_links(from_story_id, to_story_id, kind, offset_min, note)"
        " VALUES(?, ?, 'continuation', 3153600, 'six years on')",
        (second, first),
    )
    conn.commit()

    assert [r["title"] for r in conn.execute("SELECT title FROM stories ORDER BY book_order")] == [
        "One",
        "Two",
    ]
    chapter = conn.execute("SELECT * FROM chapters").fetchone()
    assert (chapter["title"], chapter["from_message_id"], chapter["to_message_id"]) == (
        "The secret",
        3,
        None,  # still being written
    )
    link = conn.execute("SELECT * FROM story_links").fetchone()
    assert (link["kind"], link["offset_min"]) == ("continuation", 3153600)
    # one link of a kind between two stories, and only the three kinds
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO story_links(from_story_id, to_story_id, kind)"
            " VALUES(?, ?, 'continuation')",
            (second, first),
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO story_links(from_story_id, to_story_id, kind) VALUES(?, ?, 'sequel')",
            (first, second),
        )
    # a story takes its chapters and links with it
    conn.execute("DELETE FROM stories WHERE id=?", (first,))
    conn.commit()
    assert conn.execute("SELECT count(*) FROM chapters").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM story_links").fetchone()[0] == 0


def test_a_library_from_a_newer_kataki_is_refused_and_left_alone(tmp_path):
    path = tmp_path / "new.db"
    newer = sqlite3.connect(path)
    newer.execute(f"PRAGMA user_version={db.SCHEMA_VERSION + 1}")
    newer.commit()
    newer.close()

    with pytest.raises(db.LibraryTooNew):
        db.connect(path)

    check = sqlite3.connect(path)
    assert check.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION + 1
    check.close()


def test_an_older_library_is_copied_before_it_is_migrated(tmp_path):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript((db.files("kataki") / "schema.sql").read_text(encoding="utf-8"))
    old.execute("PRAGMA user_version=1")
    old.execute("INSERT INTO stories(title) VALUES('kept')")
    old.commit()
    old.close()

    db.connect(path).close()

    [copy] = (tmp_path / "backups").glob("library-before-*.db")
    assert copy.name == f"library-before-v{db.SCHEMA_VERSION}-from-v1.db"
    saved = sqlite3.connect(copy)
    assert saved.execute("PRAGMA user_version").fetchone()[0] == 1
    assert saved.execute("SELECT title FROM stories").fetchone()[0] == "kept"
    saved.close()


def test_a_new_library_needs_no_copy(tmp_path):
    db.connect(tmp_path / "fresh.db").close()
    assert not (tmp_path / "backups").exists()


# migration 14, exactly reversed, so a test can stand a library at an earlier version
UNDO_V16 = "DROP TABLE IF EXISTS reflections;"
UNDO_V15 = UNDO_V16 + "DROP TABLE IF EXISTS goals;"
UNDO_V14 = UNDO_V15 + (
    "DROP TABLE IF EXISTS recollections; ALTER TABLE memories DROP COLUMN valence;"
    " ALTER TABLE memories DROP COLUMN alts; ALTER TABLE memories DROP COLUMN core_locked;"
)


def test_v10_adds_minds_and_usage(tmp_path):
    path = tmp_path / "v9.db"
    old = db.connect(path)  # today's schema, then pretend it is v9 without the new tables
    old.executescript(
        UNDO_V14 + "DROP TABLE IF EXISTS seeds; DROP TABLE IF EXISTS secrets;"
        " DROP TABLE IF EXISTS opinions; DROP TABLE IF EXISTS mind_states;"
        " DROP TABLE IF EXISTS usage_log;"
    )
    old.execute("PRAGMA user_version=9")
    old.commit()
    old.close()

    conn = db.connect(path)
    tables = {t["name"] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"mind_states", "usage_log"} <= tables
    conn.close()


def _msg(conn, story_id, parent_id, text):
    return conn.execute(
        "INSERT INTO messages(story_id, parent_id, role, text, story_time) VALUES(?, ?, 'user', ?, 0)",
        (story_id, parent_id, text),
    ).lastrowid


def test_anchored_rows_follow_the_branch(conn):
    story = _story(conn)
    root = _msg(conn, story, None, "root")
    kept = _msg(conn, story, root, "this take")
    other = _msg(conn, story, root, "another take")
    conn.execute("UPDATE stories SET active_leaf_id=? WHERE id=?", (kept, story))
    entity = conn.execute(
        "INSERT INTO entities(story_id, kind, name) VALUES(?, 'character', 'Mira')", (story,)
    ).lastrowid
    for anchor in (kept, other, None):
        conn.execute(
            "INSERT INTO mind_states(entity_id, story_time, state, message_id) VALUES(?, 0, ?, ?)",
            (entity, json.dumps({"anchor": anchor}), anchor),
        )

    live = db.live_messages(conn, story)
    assert live == {root, kept}
    where, args = db.anchor_filter(set(), live)
    seen = [
        json.loads(r["state"])["anchor"]
        for r in conn.execute(f"SELECT state FROM mind_states WHERE {where} ORDER BY id", args)
    ]
    assert seen == [kept, None]  # the other take's row is not on this branch


def test_v11_adds_the_relationship_ledger(tmp_path):
    path = tmp_path / "v10.db"
    old = db.connect(path)  # today's schema, then pretend it is v10 without the ledger
    old.executescript(
        UNDO_V14
        + "DROP TABLE IF EXISTS seeds; DROP TABLE IF EXISTS secrets; DROP TABLE IF EXISTS opinions;"
    )
    old.execute("PRAGMA user_version=10")
    old.commit()
    old.close()

    conn = db.connect(path)
    story = _story(conn)
    a, b = (
        conn.execute(
            "INSERT INTO entities(story_id, kind, name) VALUES(?, 'character', ?)", (story, n)
        ).lastrowid
        for n in ("Mira", "Aren")
    )
    conn.execute(
        "INSERT INTO opinions(story_id, src_id, dst_id, dim, value, kind, story_time)"
        " VALUES(?, ?, ?, 'trust', -8, 'sticky', 0)",
        (story, a, b),
    )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO opinions(story_id, src_id, dst_id, dim, value, kind, story_time)"
            " VALUES(?, ?, ?, 'love', 1, 'decay', 0)",
            (story, a, b),
        )
    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    conn.close()


def test_v12_adds_secrets(tmp_path):
    path = tmp_path / "v11.db"
    old = db.connect(path)  # today's schema, then pretend it is v11 without secrets
    old.executescript(UNDO_V14 + "DROP TABLE IF EXISTS seeds; DROP TABLE IF EXISTS secrets;")
    old.execute("PRAGMA user_version=11")
    old.commit()
    old.close()

    conn = db.connect(path)
    story = _story(conn)
    mira = conn.execute(
        "INSERT INTO entities(story_id, kind, name) VALUES(?, 'character', 'Mira')", (story,)
    ).lastrowid
    conn.execute(
        "INSERT INTO secrets(story_id, owner_id, text, keys, motive, cover, story_time)"
        " VALUES(?, ?, 'It was her brother''s', '[\"brother\"]', 'protect_self', 'Gran''s', 0)",
        (story, mira),
    )
    row = conn.execute("SELECT * FROM secrets").fetchone()
    assert (row["conceal_from"], row["stakes"], row["sincere"]) == ('"all"', 0.5, 0)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO secrets(story_id, owner_id, text, motive, story_time)"
            " VALUES(?, ?, 'x', 'spite', 0)",
            (story, mira),
        )
    conn.execute("DELETE FROM stories WHERE id=?", (story,))
    assert conn.execute("SELECT COUNT(*) FROM secrets").fetchone()[0] == 0
    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    conn.close()


def test_v13_adds_seeds(tmp_path):
    path = tmp_path / "v12.db"
    old = db.connect(path)  # today's schema, then pretend it is v12 without seeds
    old.executescript(UNDO_V14 + "DROP TABLE IF EXISTS seeds;")
    old.execute("PRAGMA user_version=12")
    old.commit()
    old.close()

    conn = db.connect(path)
    story = _story(conn)
    mira = conn.execute(
        "INSERT INTO entities(story_id, kind, name) VALUES(?, 'character', 'Mira')", (story,)
    ).lastrowid
    run = conn.execute(
        "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger, status)"
        " VALUES(?, 0, 1, 'between', 'ok')",
        (story,),
    ).lastrowid
    for kind in ("worry", "news", "preoccupation"):
        conn.execute(
            "INSERT INTO seeds(story_id, entity_id, kind, text, weight, story_time, run_id)"
            " VALUES(?, ?, ?, 'whether he calls', 0.6, 0, ?)",
            (story, mira, kind, run),
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO seeds(story_id, entity_id, kind, text, weight, story_time)"
            " VALUES(?, ?, 'grudge', 'x', 1, 0)",
            (story, mira),
        )
    db.discard_run(conn, run)
    assert conn.execute("SELECT COUNT(*) FROM seeds").fetchone()[0] == 0
    conn.execute(
        "INSERT INTO seeds(story_id, entity_id, kind, text, weight, story_time)"
        " VALUES(?, ?, 'plan', 'x', 1, 0)",
        (story, mira),
    )
    conn.execute("DELETE FROM stories WHERE id=?", (story,))
    assert conn.execute("SELECT COUNT(*) FROM seeds").fetchone()[0] == 0
    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    conn.close()


def test_v14_adds_recollections_and_memory_columns(tmp_path):
    path = tmp_path / "v13.db"
    old = db.connect(path)  # today's schema, then pretend it is v13
    old.executescript(UNDO_V14)
    story = _story(old)
    kept = old.execute(  # a memory from before: it keeps its words, and gains the new columns
        "INSERT INTO memories(story_id, kind, story_time, detail, gist, importance, is_true)"
        " VALUES(?, 'event', 0, 'They met on Thursday.', 'They met.', 5, 1)",
        (story,),
    ).lastrowid
    old.execute("PRAGMA user_version=13")
    old.commit()
    old.close()

    conn = db.connect(path)
    m = conn.execute("SELECT * FROM memories WHERE id=?", (kept,)).fetchone()
    assert (m["detail"], m["valence"], m["alts"], m["core_locked"]) == (
        "They met on Thursday.",
        None,
        None,
        0,
    )
    mira = conn.execute(
        "INSERT INTO entities(story_id, kind, name) VALUES(?, 'character', 'Mira')", (story,)
    ).lastrowid
    line = _msg(conn, story, None, "when did we meet?")
    for basis in ("alt", "retelling", "recount", "user"):
        conn.execute(
            "INSERT INTO recollections(knower_id, memory_id, basis, text, story_time, message_id)"
            " VALUES(?, ?, ?, 'They met on Tuesday.', 0, ?)",
            (mira, kept, basis, line),
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO recollections(knower_id, memory_id, basis, text, story_time)"
            " VALUES(?, ?, 'dream', 'x', 0)",
            (mira, kept),
        )
    conn.execute("DELETE FROM messages WHERE id=?", (line,))  # the line it hung on goes: so do they
    assert conn.execute("SELECT COUNT(*) FROM recollections").fetchone()[0] == 0
    conn.execute(
        "INSERT INTO recollections(knower_id, memory_id, basis, text, story_time)"
        " VALUES(?, ?, 'user', 'x', 0)",
        (mira, kept),
    )
    conn.execute("DELETE FROM memories WHERE id=?", (kept,))
    assert conn.execute("SELECT COUNT(*) FROM recollections").fetchone()[0] == 0
    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    conn.close()


def test_v15_adds_goals(tmp_path):
    path = tmp_path / "v14.db"
    old = db.connect(path)  # today's schema, then pretend it is v14
    old.executescript(UNDO_V15)
    story = _story(old)
    old.execute("PRAGMA user_version=14")
    old.commit()
    old.close()

    conn = db.connect(path)
    mira = conn.execute(
        "INSERT INTO entities(story_id, kind, name) VALUES(?, 'character', 'Mira')", (story,)
    ).lastrowid
    line = _msg(conn, story, None, "what do you want?")
    for tier, status in (("ambition", "dormant"), ("project", "active"), ("today", "done")):
        conn.execute(
            "INSERT INTO goals(story_id, entity_id, key, tier, text, priority, status, story_time,"
            " message_id) VALUES(?, ?, 'want', ?, 'see the boat', 0.7, ?, 0, ?)",
            (story, mira, tier, status, line),
        )
    row = conn.execute("SELECT * FROM goals LIMIT 1").fetchone()
    assert (row["cue"], row["progress"], row["deflections"], row["tactic"]) == ("", 0, 0, None)
    for tier, status in (("dream", "active"), ("project", "paused")):
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO goals(story_id, entity_id, key, tier, text, priority, status,"
                " story_time) VALUES(?, ?, 'x', ?, 'x', 0.5, ?, 0)",
                (story, mira, tier, status),
            )
    conn.execute("DELETE FROM messages WHERE id=?", (line,))  # the line they hung on goes
    assert conn.execute("SELECT COUNT(*) FROM goals").fetchone()[0] == 0
    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    conn.close()


def test_v16_adds_reflections(tmp_path):
    path = tmp_path / "v15.db"
    old = db.connect(path)  # today's schema, then pretend it is v15
    old.executescript(UNDO_V16)
    story = _story(old)
    old.execute("PRAGMA user_version=15")
    old.commit()
    old.close()

    conn = db.connect(path)
    mira = conn.execute(
        "INSERT INTO entities(story_id, kind, name) VALUES(?, 'character', 'Mira')", (story,)
    ).lastrowid
    line = _msg(conn, story, None, "eight days later")
    run = conn.execute(
        "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger, status)"
        " VALUES(?, 0, ?, 'between', 'ok')",
        (story, line),
    ).lastrowid
    for kind, status in (("habit", "seed"), ("self", "ring"), ("scar", "locked")):
        conn.execute(
            "INSERT INTO reflections(story_id, knower_id, kind, text, sources, status, story_time,"
            " run_id, message_id) VALUES(?, ?, ?, 'learned to ask for help', '[31]', ?, 0, ?, ?)",
            (story, mira, kind, status, run, line),
        )
    row = conn.execute("SELECT * FROM reflections LIMIT 1").fetchone()
    assert (row["strength"], row["trait_delta"], row["supersedes_id"]) == (0.5, None, None)
    for kind, status in (("mood", "seed"), ("habit", "maybe")):
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO reflections(story_id, knower_id, kind, text, sources, status,"
                " story_time) VALUES(?, ?, ?, 'x', '[]', ?, 0)",
                (story, mira, kind, status),
            )
    conn.execute("DELETE FROM extraction_runs WHERE id=?", (run,))  # the skip's job is undone
    assert conn.execute("SELECT COUNT(*) FROM reflections").fetchone()[0] == 0
    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION == 16
    conn.close()
