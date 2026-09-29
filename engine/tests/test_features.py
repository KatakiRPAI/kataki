"""Which features are on: stage vs channel, and the user's own switch."""

import pytest

from kataki import features


@pytest.fixture
def staged(monkeypatch):
    monkeypatch.setattr(features, "FEATURES", {"a": "alpha", "b": "beta", "s": "stable"})


def on(conn, chan):
    return {name for name in features.FEATURES if features.enabled(conn, name, chan)}


def test_each_channel_gets_its_stage_and_everything_past_it(conn, staged):
    assert on(conn, "alpha") == {"a", "b", "s"}
    assert on(conn, "beta") == {"b", "s"}
    assert on(conn, "stable") == {"s"}


def test_the_user_can_switch_off_anywhere_and_on_early_except_on_stable(conn, staged):
    conn.execute("INSERT INTO settings(key, value) VALUES('features.s', 'false')")
    conn.execute("INSERT INTO settings(key, value) VALUES('features.a', 'true')")
    assert on(conn, "beta") == {"a", "b"}
    assert on(conn, "stable") == set()


def test_the_channel_comes_from_the_build(monkeypatch):
    monkeypatch.setenv("KATAKI_CHANNEL", "beta")
    assert features.channel() == "beta"
    monkeypatch.setenv("KATAKI_CHANNEL", "nonsense")
    assert features.channel() == "stable"  # an unknown value errs toward the safe side
    monkeypatch.delenv("KATAKI_CHANNEL")
    assert features.channel() == "alpha"  # a source checkout sees everything


def test_listing_says_stage_and_state(conn, staged):
    listed = features.listing(conn, "beta")
    assert listed["channel"] == "beta"
    assert listed["features"]["a"] == {"stage": "alpha", "on": False}


def test_the_api_lists_features(conn):
    from fastapi.testclient import TestClient

    from kataki.server import create_app

    client = TestClient(create_app(conn, "t"), headers={"Authorization": "Bearer t"})
    body = client.get("/features").json()
    assert body["features"]["mind.affect"]["stage"] == "alpha"
    assert client.get("/health").json()["host"] == "desktop"
