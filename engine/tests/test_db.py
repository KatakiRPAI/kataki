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
    old.commit()
    old.close()

    conn = db.connect(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    assert conn.execute("SELECT title FROM stories").fetchone()[0] == "kept"
    columns = {c["name"] for c in conn.execute("PRAGMA table_info(entities)")}
    assert "examples" in columns
    conn.close()
