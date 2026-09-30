"""A whole library, out and back: the `.kataki` file."""

import io
import json
import sqlite3
import zipfile

import pytest
from fastapi.testclient import TestClient

from kataki import archive, chat, db, library, media, retrieve
from kataki.server import create_app

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture
def api(conn, backend):
    client = TestClient(create_app(conn, "t", llm=backend.llm, worker_delay=60))
    client.headers["Authorization"] = "Bearer t"
    with client:
        yield client


@pytest.fixture
def full(conn):
    """A library with something of everything in it."""
    face = media.save(conn, PNG, "png")
    mira = library.create_item(
        conn, "character", "Mira", "She keeps the ledger.", data={"portrait": face}, tags=["noir"]
    )
    aren = library.create_item(conn, "character", "Aren", "Late.", data={"persona": True})
    story = library.create_story(conn, "Low Tide", character_ids=[mira], persona_id=aren)
    chat.append_message(conn, story, "user", "Where was the ledger?")
    library.add_memory(
        conn,
        story,
        detail="Aren hid the guild ledger under the third floorboard.",
        gist="Aren hid the ledger.",
        common=True,
        tags=["ledger"],
    )
    book = library.create_book(conn, "The Harbour")
    library.set_book(conn, story, book)
    return {"story": story, "item": mira, "blob": face}


def dumped(conn, tmp_path) -> bytes:
    archive.dump(conn, tmp_path / "out.kataki")
    return (tmp_path / "out.kataki").read_bytes()


def entries(blob: bytes) -> set[str]:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        return set(z.namelist())


def counts(conn) -> dict:
    return {
        table: conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in ("lib_items", "stories", "messages", "memories", "taggings", "books")
    }


def test_the_library_goes_out_whole(conn, full, tmp_path):
    blob = dumped(conn, tmp_path)
    names = entries(blob)
    assert "kataki.json" in names and "library.db" in names
    assert f"blobs/{full['blob']}" in names

    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        manifest = json.loads(z.read("kataki.json"))
        assert manifest["kataki"] == 1 and manifest["schema_version"] == db.SCHEMA_VERSION
        assert manifest["holds"] == {"stories": 1, "friends": 2, "memories": 1, "pictures": 1}
        (tmp_path / "copy.db").write_bytes(z.read("library.db"))

    # the file inside is a real library, not a broken half-write
    copy = sqlite3.connect(tmp_path / "copy.db")
    assert copy.execute("SELECT title FROM stories").fetchone()[0] == "Low Tide"
    copy.close()


def test_and_comes_back_the_same(conn, full, tmp_path):
    blob = dumped(conn, tmp_path)
    was = counts(conn)

    fresh = db.connect(tmp_path / "other" / "library.db")
    made = archive.restore(fresh, blob)
    assert made["stories"] == 1 and made["pictures"] == 1
    assert counts(fresh) == was

    # the same ids, so everything that pointed at something still does
    assert fresh.execute("SELECT title FROM stories WHERE id=?", (full["story"],)).fetchone()[
        0
    ] == ("Low Tide")
    item = library.get_item(fresh, full["item"])
    assert item["name"] == "Mira" and item["tags"] == ["noir"]
    assert media.find(fresh, item["data"]["portrait"]).read_bytes() == PNG
    assert library.book_stories(fresh, 1)[0]["title"] == "Low Tide"
    fresh.close()


def test_what_she_remembers_is_still_findable(conn, full, tmp_path):
    """The memory index is built from the memories table by trigger, so a restore has to have
    rebuilt it — a copied index would be a copied file, and there is none here."""
    blob = dumped(conn, tmp_path)
    fresh = db.connect(tmp_path / "other" / "library.db")
    archive.restore(fresh, blob)

    mira = fresh.execute(
        "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (full["story"],)
    ).fetchone()["id"]
    got = retrieve.recall(fresh, full["story"], mira, "Where was the ledger?", noise=False)
    assert any("third floorboard" in r.text for r in got)
    fresh.close()


def test_it_will_not_be_poured_over_a_library_that_has_things_in_it(conn, full, tmp_path):
    blob = dumped(conn, tmp_path)
    other = db.connect(tmp_path / "other" / "library.db")
    library.create_item(other, "character", "Tobin")
    with pytest.raises(archive.BadArchive, match="empty"):
        archive.restore(other, blob)
    assert [i["name"] for i in library.list_items(other)] == ["Tobin"]  # nothing touched
    other.close()


def test_an_older_library_is_brought_up_to_date_on_the_way_in(conn, full, tmp_path):
    """A `.kataki` written by an older Kataki still opens: the migrations run on it first."""
    blob = dumped(conn, tmp_path)
    older = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(blob)) as z, zipfile.ZipFile(older, "w") as out:
        inner = tmp_path / "inner.db"
        inner.write_bytes(z.read("library.db"))
        old = sqlite3.connect(inner)  # migrations 7 to 15, exactly reversed: a real v6 library
        old.executescript(
            "DROP TABLE goals; DROP TABLE recollections; ALTER TABLE memories DROP COLUMN valence;"
            " ALTER TABLE memories DROP COLUMN alts; ALTER TABLE memories DROP COLUMN core_locked;"
            " ALTER TABLE entities DROP COLUMN looks;"
            " ALTER TABLE messages DROP COLUMN expression;"
            " DROP TABLE books; DROP TABLE chapters; DROP TABLE story_links;"
            " DROP TABLE seeds; DROP TABLE secrets; DROP TABLE opinions;"
            " DROP TABLE mind_states; DROP TABLE usage_log;"
            " DROP INDEX ix_ent_origin; ALTER TABLE stories DROP COLUMN book_order;"
            " PRAGMA user_version=6;"
        )
        old.commit()
        old.close()
        out.writestr("kataki.json", json.dumps({"kataki": 1, "schema_version": 6}))
        out.writestr("library.db", inner.read_bytes())

    fresh = db.connect(tmp_path / "other" / "library.db")
    assert archive.restore(fresh, older.getvalue())["stories"] == 1
    assert fresh.execute("SELECT count(*) FROM books").fetchone()[0] == 0  # the table is there
    assert fresh.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    fresh.close()


def test_a_library_from_a_newer_kataki_is_not_guessed_at(conn, full, tmp_path):
    blob = dumped(conn, tmp_path)
    newer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(blob)) as z, zipfile.ZipFile(newer, "w") as out:
        out.writestr("kataki.json", json.dumps({"kataki": 1, "schema_version": 99}))
        out.writestr("library.db", z.read("library.db"))
    fresh = db.connect(tmp_path / "other" / "library.db")
    with pytest.raises(archive.BadArchive, match="newer"):
        archive.restore(fresh, newer.getvalue())
    fresh.close()


def test_what_is_not_a_kataki_file_says_so(conn, tmp_path):
    fresh = db.connect(tmp_path / "other" / "library.db")
    empty = io.BytesIO()
    with zipfile.ZipFile(empty, "w") as z:
        z.writestr("readme.txt", "hello")
    for blob, says in [
        (b"not a zip at all", "not a .kataki"),
        (empty.getvalue(), "kataki.json"),
    ]:
        with pytest.raises(archive.BadArchive, match=says):
            archive.restore(fresh, blob)
    fresh.close()


def test_a_picture_that_is_not_one_does_not_get_in(conn, full, tmp_path):
    """Names come from a file someone else wrote: they are not paths to write to."""
    blob = dumped(conn, tmp_path)
    rude = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(blob)) as z, zipfile.ZipFile(rude, "w") as out:
        for name in z.namelist():
            out.writestr(name, z.read(name))
        out.writestr("blobs/../../escaped.png", PNG)
        out.writestr("blobs/not-a-hash.png", PNG)
        out.writestr("blobs/" + "a" * 64 + ".png", b"MZ this is not an image")

    fresh = db.connect(tmp_path / "other" / "library.db")
    made = archive.restore(fresh, rude.getvalue())
    assert made["pictures"] == 1  # only the real one
    assert sorted(p.name for p in media.folder(fresh).iterdir()) == [full["blob"]]
    assert not (tmp_path / "escaped.png").exists()
    fresh.close()


def test_the_round_trip_over_http(api, conn, full, tmp_path, backend):
    out = api.get("/export/library")
    assert out.status_code == 200
    assert out.headers["content-type"] == "application/zip"
    assert "kataki" in out.headers["content-disposition"]
    assert entries(out.content) >= {"kataki.json", "library.db"}

    fresh = db.connect(tmp_path / "other" / "library.db")
    client = TestClient(create_app(fresh, "t", llm=backend.llm, worker_delay=60))
    client.headers["Authorization"] = "Bearer t"
    with client as other:
        made = other.post("/import/kataki", content=out.content)
        assert made.status_code == 201 and made.json()["stories"] == 1
        assert [s["title"] for s in other.get("/stories").json()] == ["Low Tide"]
        assert other.post("/import/kataki", content=out.content).status_code == 422  # not empty
    fresh.close()


# --- what the review found: a file from anywhere, and a library mid-use ---------------------


def test_an_export_does_not_wait_for_a_write_that_never_finishes(conn, full, tmp_path):
    """SQLite's backup waits for the writers, and this connection is one of them: an unfinished
    write of our own would be a wait with no end to it, and the engine would never answer again."""
    conn.execute("UPDATE stories SET title='Half Written'")  # a transaction left open
    assert conn.in_transaction
    archive.dump(conn, tmp_path / "out.kataki")  # would hang forever before
    assert not conn.in_transaction
    with zipfile.ZipFile(tmp_path / "out.kataki") as z:
        (tmp_path / "copy.db").write_bytes(z.read("library.db"))
    copy = sqlite3.connect(tmp_path / "copy.db")
    assert copy.execute("SELECT title FROM stories").fetchone()[0] == "Half Written"
    copy.close()


def test_a_backup_lands_on_a_machine_that_has_only_been_set_up(conn, full, tmp_path):
    """The ordinary first run: add a provider, pick a model, then restore last night's backup.
    What the wizard wrote is replaced by the file's, and the keychain keeps the keys either way."""
    conn.execute("INSERT INTO providers(name, base_url) VALUES('local', 'http://x/v1')")
    conn.execute("INSERT INTO settings(key, value) VALUES('theme', '\"dark\"')")
    conn.commit()
    blob = dumped(conn, tmp_path)

    fresh = db.connect(tmp_path / "other" / "library.db")
    fresh.execute("INSERT INTO providers(name, base_url) VALUES('mine', 'http://y/v1')")
    fresh.execute("INSERT INTO settings(key, value) VALUES('theme', '\"light\"')")
    fresh.commit()

    assert archive.restore(fresh, blob)["stories"] == 1
    assert [p["name"] for p in fresh.execute("SELECT name FROM providers")] == ["local"]
    assert fresh.execute("SELECT value FROM settings WHERE key='theme'").fetchone()[0] == '"dark"'
    fresh.close()


def test_a_refused_import_leaves_the_machine_as_it_found_it(conn, full, tmp_path):
    """A library that does not hold together is not poured out halfway and then swept up."""
    blob = dumped(conn, tmp_path)
    broken = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(blob)) as z, zipfile.ZipFile(broken, "w") as out:
        inner = tmp_path / "broken.db"
        inner.write_bytes(z.read("library.db"))
        bad = sqlite3.connect(inner)
        bad.execute("PRAGMA foreign_keys=OFF")
        bad.execute(
            "INSERT INTO messages(story_id, role, text, story_time) VALUES(999,'user','x',0)"
        )
        bad.commit()
        bad.close()
        out.writestr("kataki.json", z.read("kataki.json"))
        out.writestr("library.db", inner.read_bytes())

    fresh = db.connect(tmp_path / "other" / "library.db")
    fresh.execute("INSERT INTO providers(name, base_url) VALUES('mine', 'http://y/v1')")
    fresh.commit()
    with pytest.raises(archive.BadArchive, match="does not hold together"):
        archive.restore(fresh, broken.getvalue())

    assert [p["name"] for p in fresh.execute("SELECT name FROM providers")] == ["mine"]
    assert fresh.execute("SELECT count(*) FROM stories").fetchone()[0] == 0
    assert fresh.execute("PRAGMA foreign_keys").fetchone()[0] == 1  # and the keys are back on
    fresh.close()


def test_a_library_with_a_story_in_it_is_still_refused(conn, full, tmp_path):
    blob = dumped(conn, tmp_path)
    other = db.connect(tmp_path / "other" / "library.db")
    library.create_item(other, "character", "Tobin")
    with pytest.raises(archive.BadArchive, match="lib_items"):
        archive.restore(other, blob)
    assert [i["name"] for i in library.list_items(other)] == ["Tobin"]
    other.close()


def test_a_library_db_that_says_it_is_small_and_is_not(conn, tmp_path):
    """A zip is a promise about a file, not the file."""
    bomb = io.BytesIO()
    with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("kataki.json", json.dumps({"kataki": 1, "schema_version": db.SCHEMA_VERSION}))
        z.writestr("library.db", b"\0" * (16 * 1024 * 1024))
    assert len(bomb.getvalue()) < 100_000  # small on the wire

    fresh = db.connect(tmp_path / "other" / "library.db")
    archive.MAX_BYTES, was = 1 << 20, archive.MAX_BYTES
    try:
        with pytest.raises(archive.BadArchive, match="too big"):
            archive.restore(fresh, bomb.getvalue())
    finally:
        archive.MAX_BYTES = was
    fresh.close()


def test_a_manifest_that_is_half_a_gigabyte_of_nothing(conn, tmp_path):
    fat = io.BytesIO()
    with zipfile.ZipFile(fat, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("kataki.json", b" " * (archive.MAX_MANIFEST * 4))
        z.writestr("library.db", b"")
    fresh = db.connect(tmp_path / "other" / "library.db")
    with pytest.raises(archive.BadArchive, match="larger than one can be"):
        archive.restore(fresh, fat.getvalue())
    fresh.close()


def test_a_locked_or_broken_archive_is_a_bad_file_not_a_crash(conn, full, tmp_path):
    blob = dumped(conn, tmp_path)
    body = bytearray(blob)
    where = body.find(b"PK\x01\x02")
    body[6:8] = (1).to_bytes(2, "little")  # the encrypted bit, in the first local header
    body[where + 8 : where + 10] = (1).to_bytes(2, "little")  # and in the directory

    fresh = db.connect(tmp_path / "other" / "library.db")
    with pytest.raises(archive.BadArchive, match="not a .kataki"):
        archive.restore(fresh, bytes(body))
    fresh.close()


def test_a_library_that_is_not_one_at_all(conn, tmp_path):
    for inner, says in [
        (b"MZ\x90\x00 this is a program", "could not be opened"),
        (b"", "no library in this file"),  # an empty file is not an empty library
    ]:
        odd = io.BytesIO()
        with zipfile.ZipFile(odd, "w") as z:
            z.writestr("kataki.json", json.dumps({"kataki": 1, "schema_version": 1}))
            z.writestr("library.db", inner)
        fresh = db.connect(tmp_path / f"other{len(inner)}" / "library.db")
        with pytest.raises(archive.BadArchive, match=says):
            archive.restore(fresh, odd.getvalue())
        fresh.close()


def test_a_table_this_kataki_never_heard_of_is_not_a_place_to_write(conn, full, tmp_path):
    """The names of the tables come from our own library, never from the file's."""
    blob = dumped(conn, tmp_path)
    extra = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(blob)) as z, zipfile.ZipFile(extra, "w") as out:
        inner = tmp_path / "extra.db"
        inner.write_bytes(z.read("library.db"))
        odd = sqlite3.connect(inner)
        odd.execute('CREATE TABLE "holiday photos"(id INTEGER PRIMARY KEY)')
        odd.commit()
        odd.close()
        out.writestr("kataki.json", z.read("kataki.json"))
        out.writestr("library.db", inner.read_bytes())

    fresh = db.connect(tmp_path / "other" / "library.db")
    assert archive.restore(fresh, extra.getvalue())["stories"] == 1  # the rest still arrives
    assert not fresh.execute("SELECT 1 FROM sqlite_master WHERE name='holiday photos'").fetchone()
    fresh.close()


def test_a_junk_file_does_not_stay_open_behind_us(conn, tmp_path):
    """`db.connect` on something that is not a database must not leave the file held: on
    Windows nothing could then delete it."""
    junk = tmp_path / "junk.db"
    junk.write_bytes(b"MZ\x90\x00" * 64)
    with pytest.raises(sqlite3.DatabaseError):
        db.connect(junk)
    junk.unlink()  # would raise PermissionError on Windows if a handle were still open
