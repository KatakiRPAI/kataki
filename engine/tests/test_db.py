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
