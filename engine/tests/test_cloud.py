"""Cloud save (cloud.py): the desktop links itself to an account, sends its library up and
brings it down, against a stand-in for the gateway's cloud routes."""

import json
import shutil

import httpx2
import keyring
import pytest
from fastapi.testclient import TestClient

from kataki import archive, backups, cloud, db, library
from kataki.server import create_app

AT = "https://online.test"
AUTH = {"Authorization": "Bearer t"}


class FakeCloud:
    """The gateway's side: one code, one token, snapshots with revisions."""

    def __init__(self):
        self.approved = False
        self.snapshots: list[dict] = []  # {"revision", "body", "holds", "device"}
        self.linked = True
        self.broke = False  # past the free limit with no credit

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        path = request.url.path
        if path == "/api/device/start":
            return httpx2.Response(
                200, json={"code": "ABCD2345", "secret": "s3", "url": f"{AT}/app/?link=ABCD2345"}
            )
        if path == "/api/device/poll":
            if json.loads(request.content)["secret"] != "s3":
                return httpx2.Response(410)
            return (
                httpx2.Response(200, json={"token": "kd_tok"})
                if self.approved
                else httpx2.Response(202)
            )
        if request.headers.get("authorization") != "Bearer kd_tok" or not self.linked:
            return httpx2.Response(401, json={"code": "UNLINKED"})
        newest = self.snapshots[-1] if self.snapshots else None
        shown = newest and {k: newest[k] for k in ("revision", "holds", "device")}
        if path == "/api/cloud" and request.method == "GET":
            return httpx2.Response(200, json={"account": "Qais", "snapshot": shown})
        if path == "/api/cloud" and request.method == "PUT":
            q = request.url.params
            if not q.get("force") and int(q["base"]) != (newest["revision"] if newest else 0):
                return httpx2.Response(409, json={"snapshot": shown})
            if self.broke:
                return httpx2.Response(402, json={"over": ["stories"], "free": {"stories": 5}})
            made = {
                "revision": (newest["revision"] if newest else 0) + 1,
                "body": request.content,
                "holds": json.loads(q["holds"]),
                "device": "this one",
            }
            self.snapshots.append(made)
            return httpx2.Response(
                200, json={"snapshot": {k: made[k] for k in ("revision", "holds", "device")}}
            )
        if path == "/api/cloud/download":
            if not newest:
                return httpx2.Response(404)
            return httpx2.Response(
                200, content=newest["body"], headers={"x-kataki-revision": str(newest["revision"])}
            )
        if path == "/api/cloud/device":
            self.linked = False
            return httpx2.Response(200, json={"ok": True})
        return httpx2.Response(404)


@pytest.fixture
def fake(monkeypatch):
    fake = FakeCloud()
    monkeypatch.setattr(cloud, "TRANSPORT", httpx2.MockTransport(fake))
    monkeypatch.setenv("KATAKI_ONLINE", AT + "/")
    return fake


@pytest.fixture
def api(tmp_path, backend):
    path = tmp_path / "lib" / "library.db"
    path.parent.mkdir()
    conn = db.connect(path)
    app = create_app(conn, "t", llm=backend.llm, worker_delay=60, db_path=path)
    with TestClient(app, headers=AUTH) as client:
        client.conn, client.path = conn, path
        yield client


def link(api, fake):
    made = api.post("/cloud/connect").json()
    assert made == {"url": f"{AT}/app/?link=ABCD2345", "code": "ABCD2345"}  # never the secret
    assert api.post("/cloud/poll").json() == {"state": "waiting"}
    fake.approved = True
    assert api.post("/cloud/poll").json() == {"state": "linked"}
    assert keyring.get_password("kataki-cloud", AT) == "kd_tok"  # in the keychain, not the library


def test_a_kataki_with_no_cloud_says_so(api, monkeypatch):
    monkeypatch.delenv("KATAKI_ONLINE", raising=False)
    assert api.get("/cloud").json() == {"available": False}
    assert api.post("/cloud/upload").status_code == 404


def test_linking_then_up_and_down(api, fake):
    assert api.get("/cloud").json()["connected"] is False
    assert api.post("/cloud/upload").status_code == 409  # not linked yet
    link(api, fake)

    mira = library.create_item(api.conn, "character", "Mira")
    library.create_item(api.conn, "place", "The Gull")
    library.create_item(api.conn, "scenario", "Low tide")
    library.create_story(api.conn, "The first story", [mira])
    seen = api.get("/cloud").json()
    assert (seen["connected"], seen["account"], seen["snapshot"], seen["base"]) == (
        True,
        "Qais",
        None,
        0,
    )
    assert seen["local"] == {"stories": 1, "characters": 1, "places": 1, "plots": 1}

    sent = api.post("/cloud/upload").json()
    assert sent["snapshot"]["revision"] == 1
    assert sent["snapshot"]["holds"] == seen["local"]  # what the limit will count
    assert api.get("/cloud").json()["base"] == 1

    # another computer moved the cloud on: this one is told, and nothing is overwritten
    fake.snapshots.append({**fake.snapshots[0], "revision": 2, "device": "Laptop"})
    clash = api.post("/cloud/upload").json()
    assert clash == {"conflict": {"revision": 2, "holds": seen["local"], "device": "Laptop"}}
    assert len(fake.snapshots) == 2
    assert api.post("/cloud/upload?force=true").json()["snapshot"]["revision"] == 3  # "replace it"

    # down: nothing changes now; the copy waits beside the backups for the next start
    library.create_story(api.conn, "Written after the upload", [mira])
    got = api.post("/cloud/download").json()
    assert got == {"restart": True, "revision": 3}
    assert api.conn.execute("SELECT count(*) FROM stories").fetchone()[0] == 2
    # the next start, with nothing open: played out on a copy of the folder
    later = api.path.parent.parent / "later" / "library.db"
    shutil.copytree(api.path.parent, later.parent, ignore=shutil.ignore_patterns("*-wal", "*-shm"))
    assert backups.apply_pending(later) is True
    restored = db.connect(later)
    assert [r["title"] for r in restored.execute("SELECT title FROM stories")] == [
        "The first story"
    ]
    restored.close()
    kept = [b["name"] for b in backups.listing(later)]
    assert any("before-restore" in name for name in kept)  # what was here can be had back


def test_what_comes_down_must_be_a_library(api, fake):
    link(api, fake)
    fake.snapshots.append({"revision": 1, "body": b"not a zip at all", "holds": {}, "device": "x"})
    assert api.post("/cloud/download").status_code == 422
    assert not (api.path.parent / backups.PENDING).exists()  # nothing is swapped in
    assert not list(backups.folder(api.path).glob("*from-cloud*"))


def test_unlinked_from_the_website_the_token_is_forgotten(api, fake):
    link(api, fake)
    fake.linked = False
    assert api.get("/cloud").json()["connected"] is False
    assert keyring.get_password("kataki-cloud", AT) is None


def test_disconnecting_tells_the_service_and_forgets_the_token(api, fake):
    link(api, fake)
    assert api.post("/cloud/disconnect").json() == {"connected": False}
    assert fake.linked is False
    assert keyring.get_password("kataki-cloud", AT) is None


def test_an_empty_cloud_has_nothing_to_bring_down(api, fake):
    link(api, fake)
    assert api.post("/cloud/download").json() == {"nothing": True}
    with pytest.raises(archive.BadArchive):  # and the helper it leans on still refuses rubbish
        archive.restore(api.conn, b"rubbish")


def test_past_the_free_limit_with_no_credit_it_says_why(api, fake):
    link(api, fake)
    fake.broke = True
    said = api.post("/cloud/upload").json()
    assert said == {"needs_credit": {"over": ["stories"], "free": {"stories": 5}}}
    assert fake.snapshots == []
