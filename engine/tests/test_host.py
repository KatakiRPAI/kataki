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
