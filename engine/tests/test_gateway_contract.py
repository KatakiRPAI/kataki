"""The engine ↔ gateway contract (minds spec §8.4; track B6): a fake gateway drives two users
through a turn each. Each user's ledger is their own `usage_log`, to the micro-dollar; a refused
user reaches no model and no ledger; what the meter could not take, the outbox settles."""

import asyncio
import json
import sqlite3

import httpx2
from fastapi.testclient import TestClient

from kataki import library, usage
from test_hosted import PRICES, FakeGateway, now_signed, service


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


def test_two_users_a_turn_each_and_every_ledger_is_its_own_usage_log(tmp_path, backend):
    fake = FakeGateway(PRICES, broke={"carol"}, down=2)  # alice's first bill cannot be taken
    app = service(tmp_path, fake, transport=httpx2.MockTransport(backend))
    stories = {user: a_story(app.open(user).conn) for user in ("alice", "bob", "carol")}
    backend.say("Hello, Aren.", "Evening, Aren.")
    with TestClient(app) as client:
        for user in ("alice", "bob"):
            r = client.post(
                f"/stories/{stories[user]}/turn", json={"text": "Hi."}, headers=now_signed(user)
            )
            assert last_event(r.text)[0] == "done"
        sent = len(backend.requests)
        r = client.post(
            f"/stories/{stories['carol']}/turn", json={"text": "Hi."}, headers=now_signed("carol")
        )
        assert last_event(r.text)[1]["code"] == "NO_CREDIT"
        assert len(backend.requests) == sent  # the refusal reached no model
    assert "alice" not in fake.ledger  # its meter was down; the row waits in the outbox
    app.open("alice")  # the next open sends it
    asyncio.run(app.close("alice"))

    for user in ("alice", "bob"):
        mine = their_rows(tmp_path, user)
        assert mine and fake.ledger[user] == mine  # same calls, same micro-dollars
        assert all(isinstance(v, int) for v in mine.values())
    assert not set(fake.ledger["alice"]) & set(fake.ledger["bob"])  # no call billed twice
    assert "carol" not in fake.ledger and their_rows(tmp_path, "carol") == {}
