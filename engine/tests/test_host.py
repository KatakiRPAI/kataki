"""The Host seam (minds spec §4, §8.4, track B1): the desktop is today's engine; the online host
takes every answer from the service."""

import pytest
from fastapi.testclient import TestClient

from kataki import features, library
from kataki.host import LocalHost, OnlineHost
from kataki.server import create_app

TOKEN = "t0k"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


def online(**kw) -> OnlineHost:
    return OnlineHost(
        get_key=kw.get("get_key", lambda name: None),
        meter=kw.get("meter", lambda row: None),
        allow=kw.get("allow", lambda ep, estimate: True),
        channel=kw.get("channel", lambda: "beta"),
        prices=kw.get("prices", dict),
    )


def test_the_desktop_host_is_todays_engine(conn, monkeypatch):
    monkeypatch.setenv("KATAKI_CHANNEL", "beta")
    body = TestClient(create_app(conn, TOKEN)).get("/health", headers=AUTH).json()
    assert (body["host"], body["channel"]) == ("desktop", "beta")
    host = LocalHost()
    assert (host.name, host.local_routes, host.allow, host.meter) == ("desktop", True, None, None)


def test_an_online_host_reports_itself_and_its_accounts_channel(conn, monkeypatch):
    monkeypatch.setenv("KATAKI_CHANNEL", "alpha")  # the build's channel does not count online
    client = TestClient(create_app(conn, TOKEN, host=online(channel=lambda: "stable")))
    body = client.get("/health", headers=AUTH).json()
    assert (body["host"], body["channel"]) == ("online", "stable")
    listed = client.get("/features", headers=AUTH).json()
    assert listed["channel"] == "stable"
    assert not listed["features"]["mind.affect"]["on"]  # an alpha feature is off on stable


def test_an_unknown_channel_errs_toward_stable(conn):
    client = TestClient(create_app(conn, TOKEN, host=online(channel=lambda: "gamma")))
    assert client.get("/health", headers=AUTH).json()["channel"] == "stable"


def test_the_channel_is_the_hosts_only_inside_its_requests(conn):
    TestClient(create_app(conn, TOKEN, host=online(channel=lambda: "stable"))).get(
        "/health", headers=AUTH
    )
    assert features.CURRENT.get() is None  # nothing leaks out to the next caller


@pytest.mark.parametrize(
    "method, path",
    [
        ("get", "/providers"),
        ("post", "/providers"),
        ("patch", "/providers/1"),
        ("delete", "/providers/1"),
        ("get", "/providers/detect"),
        ("get", "/providers/1/models"),
        ("get", "/storage"),
        ("get", "/backups"),
        ("post", "/backups"),
        ("post", "/backups/x/restore"),
    ],
)
def test_local_only_routes_are_not_there_online(conn, tmp_path, method, path):
    app = create_app(conn, TOKEN, host=online(), db_path=tmp_path / "library.db")
    r = getattr(TestClient(app), method)(path, headers=AUTH)
    assert r.status_code == 404


def test_local_routes_stay_on_the_desktop(conn, tmp_path):
    client = TestClient(create_app(conn, TOKEN, db_path=tmp_path / "library.db"))
    assert client.get("/providers", headers=AUTH).status_code == 200
    assert client.get("/backups", headers=AUTH).status_code == 200


def test_keys_come_from_the_host(local_model):
    conn = local_model
    asked = []
    host = online(get_key=lambda name: asked.append(name) or "service-key")
    client = TestClient(create_app(conn, TOKEN, host=host))
    client.get("/roles", headers=AUTH)
    assert host.get_key("local") == "service-key"
    assert "local" in asked


def test_a_turn_under_a_beta_host_sees_beta(local_model, backend, monkeypatch):
    conn = local_model
    monkeypatch.setenv("KATAKI_CHANNEL", "alpha")
    seen = []
    real = features.enabled
    monkeypatch.setattr(
        features, "enabled", lambda c, n, chan=None: seen.append(features.channel()) or real(c, n)
    )
    mira = library.create_item(conn, "character", "Mira")
    aren = library.create_item(conn, "character", "Aren")
    story = library.create_story(conn, "s", character_ids=[mira], persona_id=aren)
    backend.say("Hello.")
    app = create_app(conn, TOKEN, backend.llm, host=online(channel=lambda: "beta"))
    with TestClient(app) as client:
        r = client.post(f"/stories/{story}/turn", json={"text": "Hi."}, headers=AUTH)
    assert "event: done" in r.text
    assert seen and set(seen) == {"beta"}


# --- the review's holes: nothing a user sends online can re-route the service ---------------


def crafted(tmp_path) -> bytes:
    """A .kataki whose provider has the service's name and someone else's address."""
    from kataki import archive, db

    theirs = db.connect(tmp_path / "theirs" / "library.db")
    theirs.execute("INSERT INTO providers(id, name, base_url) VALUES(1, 'hf', 'http://evil/v1')")
    theirs.execute("INSERT INTO model_roles(role, provider_id, model) VALUES('rp', 1, 'x')")
    theirs.execute("INSERT INTO settings(key, value) VALUES('prices', '{}')")
    theirs.execute("INSERT INTO usage_log(role, model, cost) VALUES('rp', 'x', -5)")
    theirs.commit()
    archive.dump(theirs, tmp_path / "evil.kataki")
    theirs.close()
    return (tmp_path / "evil.kataki").read_bytes()


def rows(conn, sql: str) -> list[tuple]:
    return [tuple(r) for r in conn.execute(sql)]


def service(conn):
    conn.execute("INSERT INTO providers(id, name, base_url) VALUES(1, 'hf', 'http://svc/v1')")
    conn.execute("INSERT INTO model_roles(role, provider_id, model) VALUES('rp', 1, 'rp-model')")
    conn.execute("INSERT INTO usage_log(role, model) VALUES('rp', 'rp-model')")
    conn.commit()


def test_an_import_online_cannot_touch_the_services_routing_or_its_ledger(conn, tmp_path):
    service(conn)
    client = TestClient(create_app(conn, TOKEN, host=online()))
    assert client.post("/import/kataki", content=crafted(tmp_path), headers=AUTH).status_code == 201
    assert rows(conn, "SELECT base_url FROM providers") == [("http://svc/v1",)]
    assert rows(conn, "SELECT model FROM model_roles") == [("rp-model",)]
    assert conn.execute("SELECT count(*) FROM settings WHERE key='prices'").fetchone()[0] == 0
    assert rows(conn, "SELECT model, cost FROM usage_log") == [("rp-model", None)]


def test_an_import_on_the_desktop_still_brings_everything_back(conn, tmp_path):
    conn.execute("INSERT INTO providers(id, name, base_url) VALUES(1, 'hf', 'http://mine/v1')")
    conn.commit()
    client = TestClient(create_app(conn, TOKEN))
    assert client.post("/import/kataki", content=crafted(tmp_path), headers=AUTH).status_code == 201
    assert rows(conn, "SELECT base_url FROM providers") == [("http://evil/v1",)]
    assert conn.execute("SELECT count(*) FROM settings WHERE key='prices'").fetchone()[0] == 1
    assert conn.execute("SELECT count(*) FROM usage_log").fetchone()[0] == 1
