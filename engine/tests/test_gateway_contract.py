"""The engine ↔ gateway contract (minds spec §8.4; track B6): a fake gateway drives two users
through a turn each. Each user's ledger is their own `usage_log`, to the micro-dollar; a refused
user reaches no model and no ledger; what the meter could not take, the outbox settles."""

import asyncio
import json
import sqlite3

import httpx2
from fastapi.testclient import TestClient

from kataki import library, usage
from test_hosted import PRICES, As, FakeGateway, service


def a_story(conn) -> int:
    mira = library.create_item(conn, "character", "Mira")
    aren = library.create_item(conn, "character", "Aren")
    return library.create_story(conn, "s", character_ids=[mira], persona_id=aren)


def last_event(text: str) -> tuple[str, dict]:
    kind, data = text.strip().split("\n\n")[-1].split("\n", 1)
    return kind.removeprefix("event: "), json.loads(data.removeprefix("data: "))


def their_rows(tmp_path, user) -> dict[str, int]:
    """usage_id → micro-dollars, priced from the user's own usage_log tokens."""
    conn = sqlite3.connect(tmp_path / "users" / user / "library.db")
    conn.row_factory = sqlite3.Row
    try:
        return {
            r["usage_id"]: usage.micros(PRICES, dict(r))
            for r in conn.execute("SELECT * FROM usage_log")
        }
    finally:
        conn.close()


def unsent(tmp_path, user) -> int:
    conn = sqlite3.connect(tmp_path / "users" / user / "library.db")
    try:
        return conn.execute("SELECT count(*) FROM usage_log WHERE metered != 1").fetchone()[0]
    finally:
        conn.close()


def test_two_users_a_turn_each_and_every_ledger_is_its_own_usage_log(tmp_path, backend):
    # alice's first bill cannot be taken; the next one is taken, but its answer is lost
    fake = FakeGateway(PRICES, broke={"carol"}, down=2, lose=1)
    app = service(tmp_path, fake, transport=httpx2.MockTransport(backend))
    stories = {user: a_story(app.open(user).conn) for user in ("alice", "bob", "carol")}
    backend.say("Hello, Aren.", "Evening, Aren.")
    with TestClient(app) as client:
        for user in ("alice", "bob"):
            r = client.post(f"/stories/{stories[user]}/turn", json={"text": "Hi."}, auth=As(user))
            assert last_event(r.text)[0] == "done"
        sent = len(backend.requests)
        r = client.post(f"/stories/{stories['carol']}/turn", json={"text": "Hi."}, auth=As("carol"))
        assert last_event(r.text)[1]["code"] == "NO_CREDIT"
        assert len(backend.requests) == sent  # the refusal reached no model
    assert "alice" not in fake.ledger  # its meter was down; the row waits in the outbox
    for user in ("alice", "bob"):  # the next open sends what waits, and nothing it already sent
        app.open(user)
        asyncio.run(app.close(user))

    (lost,) = fake.lost  # retried with the same usage_id: billed once, and marked sent
    assert fake.posts[lost] == 2
    assert all(n == 1 for u, n in fake.posts.items() if u not in (lost, *fake.ledger["alice"]))

    for user in ("alice", "bob"):
        mine = their_rows(tmp_path, user)
        assert mine and fake.ledger[user] == mine  # same calls, same micro-dollars
        assert all(isinstance(v, int) for v in mine.values())
        assert unsent(tmp_path, user) == 0
    assert not set(fake.ledger["alice"]) & set(fake.ledger["bob"])  # no call billed twice
    assert "carol" not in fake.ledger and their_rows(tmp_path, "carol") == {}
    assert set(fake.taken.values()) == {1}  # the engine never sends an acknowledged row again


def metered(tmp_path, user) -> dict[str, int]:
    conn = sqlite3.connect(tmp_path / "users" / user / "library.db")
    try:
        return dict(conn.execute("SELECT usage_id, metered FROM usage_log").fetchall())
    finally:
        conn.close()


def test_a_bill_whose_answer_was_lost_is_billed_once(tmp_path, backend):
    fake = FakeGateway(PRICES, lose=1)  # the gateway takes the row; its 504 is all we see
    app = service(tmp_path, fake, transport=httpx2.MockTransport(backend))
    story = a_story(app.open("alice").conn)
    backend.say("Hello, Aren.")
    with TestClient(app) as client:
        r = client.post(f"/stories/{story}/turn", json={"text": "Hi."}, auth=As("alice"))
        assert last_event(r.text)[0] == "done"
    app.open("alice")  # the outbox has nothing left to send
    asyncio.run(app.close("alice"))
    (uid,) = fake.lost
    assert fake.posts == {uid: 2} and fake.taken == {uid: 1}  # the retry carried the same id
    assert fake.ledger["alice"] == their_rows(tmp_path, "alice")  # one amount for it
    assert metered(tmp_path, "alice") == {uid: 1}


def test_past_the_daily_cap_a_turn_ends_with_daily_cap(tmp_path, backend):
    fake = FakeGateway(PRICES)
    app = service(tmp_path, fake, transport=httpx2.MockTransport(backend), daily_cap=0.0)
    story = a_story(app.open("alice").conn)
    with TestClient(app) as client:
        r = client.post(f"/stories/{story}/turn", json={"text": "Hi."}, auth=As("alice"))
    assert last_event(r.text) == ("error", {**last_event(r.text)[1], "code": "DAILY_CAP"})
    assert backend.requests == [] and fake.asked == []  # no model, no gateway
