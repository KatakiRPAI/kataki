import sqlite3

from fastapi.testclient import TestClient

from kataki import backups, db
from kataki.server import create_app


def test_a_backup_is_made_listed_and_restored_at_the_next_start(tmp_path, backend):
    path = tmp_path / "library.db"
    conn = db.connect(path)
    api = TestClient(
        create_app(conn, "t", llm=backend.llm, worker_delay=60, db_path=path),
        headers={"Authorization": "Bearer t"},
    )
    with api:
        api.post("/library", json={"kind": "character", "name": "Mira"})
        made = api.post("/backups").json()
        assert made["name"].startswith("library-") and made["bytes"] > 0
        api.post("/library", json={"kind": "character", "name": "Tobin"})
        assert [b["name"] for b in api.get("/backups").json()] == [made["name"]]
        assert api.post("/backups/nope.db/restore").status_code == 404
        assert api.post(f"/backups/{made['name']}/restore").status_code == 202
    conn.close()
    assert backups.apply_pending(path)
    names = [r[0] for r in sqlite3.connect(path).execute("SELECT name FROM lib_items")]
    assert names == ["Mira"]  # back to the backup
    assert any("before-restore" in b["name"] for b in backups.listing(path))  # and undoable


def test_old_backups_go_past_the_number_kept(tmp_path):
    conn = db.connect(tmp_path / "library.db")
    for i in range(3):
        (backups.folder(tmp_path / "library.db")).mkdir(exist_ok=True)
        (backups.folder(tmp_path / "library.db") / f"library-2026010{i}-000000.db").write_bytes(
            b"x"
        )
    backups.prune(tmp_path / "library.db", "7")
    assert len(backups.listing(tmp_path / "library.db")) == 3
    KEEP = backups.KEEP
    KEEP["2"] = 2
    backups.prune(tmp_path / "library.db", "2")
    assert [b["name"] for b in backups.listing(tmp_path / "library.db")] == [
        "library-20260102-000000.db",
        "library-20260101-000000.db",
    ]
    conn.close()


def test_storage_says_where_the_library_lives(tmp_path, backend):
    path = tmp_path / "library.db"
    conn = db.connect(path)
    api = TestClient(
        create_app(conn, "t", llm=backend.llm, worker_delay=60, db_path=path),
        headers={"Authorization": "Bearer t"},
    )
    with api:
        png = b"\x89PNG\r\n\x1a\n" + b"\0" * 64
        api.post("/media", content=png, headers={"content-type": "image/png"})
        got = api.get("/storage").json()
        places = {s["what"]: s for s in got["places"]}
    assert places["library"]["path"] == str(tmp_path.resolve()) and places["library"]["bytes"] > 0
    assert places["pictures"]["bytes"] == len(png)
    assert places["backups"]["bytes"] == 0 and 0 < got["free"] <= got["total"] and got["drive"]
    conn.close()


def test_backups_rotate_by_age_whatever_their_names(tmp_path):
    import os
    import time

    db_path = tmp_path / "library.db"
    folder = backups.folder(db_path)
    folder.mkdir()
    now = time.time()
    for name, age_days in [
        ("library-before-v10-from-v9.db", 10),
        ("library-20260101-000000.db", 1),
        ("library-20250101-000000.db", 5),
    ]:
        f = folder / name
        f.write_bytes(b"x")
        os.utime(f, (now - age_days * 86_400,) * 2)
    assert backups.listing(db_path)[0]["name"] == "library-20260101-000000.db"
    assert not backups.due(db_path, "weekly")  # judged by the 1-day-old dated one
    backups.prune(db_path, "7")
    assert len(backups.listing(db_path)) == 3
    backups.KEEP["2"] = 2
    try:
        backups.prune(db_path, "2")
    finally:
        del backups.KEEP["2"]
    assert [b["name"] for b in backups.listing(db_path)] == [
        "library-20260101-000000.db",
        "library-20250101-000000.db",
    ]
