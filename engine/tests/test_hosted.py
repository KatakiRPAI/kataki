"""Kataki online's engine process (minds spec §4, §8.4; track B4, B5): many users, a library
each, who they are only from the gateway's signed headers."""

import asyncio
import json

import httpx2
import pytest

from kataki import hosted, usage
from kataki.llm import LLM, Endpoint

EMBED = Endpoint("http://fake/v1", "e", role="embed")


def held(gate: asyncio.Event, seen: list):
    """A provider that answers only once `gate` is set, counting the requests it has."""

    async def handler(request):
        seen.append(request.url.path)
        await gate.wait()
        return httpx2.Response(200, json={"data": [{"index": 0, "embedding": [1.0]}]})

    return httpx2.MockTransport(handler)


@pytest.mark.anyio
@pytest.mark.parametrize("max_calls, in_flight", [(1, 1), (None, 2)])
async def test_one_users_calls_in_flight_are_capped(max_calls, in_flight):
    gate, seen = asyncio.Event(), []
    llm = LLM(held(gate, seen), max_calls=max_calls)
    calls = [asyncio.create_task(llm.embed(EMBED, ["x"])) for _ in range(2)]
    for _ in range(5):
        await asyncio.sleep(0)
    assert len(seen) == in_flight  # past the cap a call waits; it is not refused
    gate.set()
    assert [len(v) for v in await asyncio.gather(*calls)] == [1, 1]


# --- who is asking: the gateway's signed headers ---------------------------------------------

SECRET = b"s3cret"
NOW = 1_800_000_000


def signed(user="alice", channel="beta", at=NOW, secret=SECRET) -> dict:
    return {
        "x-kataki-user": user,
        "x-kataki-channel": channel,
        "x-kataki-time": str(at),
        "x-kataki-sig": hosted.sign(secret, user, channel, at),
    }


def test_a_signed_request_says_who_and_which_channel():
    assert hosted.who(SECRET, signed(), NOW + 5) == ("alice", "beta")


@pytest.mark.parametrize(
    "headers",
    [
        {},  # unsigned
        {**signed(), "x-kataki-user": "bob"},  # someone else's signature
        {**signed(), "x-kataki-channel": "alpha"},  # a channel it was not given
        signed(secret=b"guess"),
        signed(at=NOW - 61),  # stale: a replay
        signed(at=NOW + 61),
        {**signed(), "x-kataki-time": "soon"},
        signed(user="../bob"),  # signed, but it names a folder: never trusted to
        signed(user=""),
    ],
)
def test_anything_else_is_nobody(headers):
    assert hosted.who(SECRET, headers, NOW) is None


# --- the gateway client -----------------------------------------------------------------------


class FakeGateway:
    """The service's side of §8.4, in-process: a balance per user and a ledger."""

    def __init__(self, prices=None, broke=(), down=0):
        self.prices, self.broke, self.down = prices or {}, set(broke), down
        self.asked: list[str] = []
        self.ledger: dict[str, dict[str, int]] = {}  # user → usage_id → micro-dollars
        self.auth: set[str] = set()

    def __call__(self, request):
        self.auth.add(request.headers.get("authorization"))
        if request.url.path == "/allow":
            user = request.url.params["user"]
            self.asked.append(user)
            return httpx2.Response(200, json={"ok": user not in self.broke})
        if self.down:
            self.down -= 1
            return httpx2.Response(503)
        row = json.loads(request.content)
        spent = usage.micros(self.prices, row)
        self.ledger.setdefault(row["user"], {})[row["usage_id"]] = spent  # idempotent
        return httpx2.Response(200, json={})

    def client(self, clock=lambda: 0.0) -> hosted.Gateway:
        return hosted.Gateway("http://gw", "gw-key", httpx2.MockTransport(self), clock=clock)


def test_allow_is_asked_once_per_ten_seconds_per_user():
    now = [0.0]
    fake = FakeGateway(broke={"bob"})
    gw = fake.client(lambda: now[0])
    assert gw.allow("alice", 0.01) and gw.allow("alice", 0.01)
    assert not gw.allow("bob", 0.01)
    now[0] = 10.5
    assert gw.allow("alice", 0.01)
    assert fake.asked == ["alice", "bob", "alice"]
    assert fake.auth == {"Bearer gw-key"}


def test_a_gateway_that_cannot_answer_raises():
    gw = hosted.Gateway("http://gw", "k", httpx2.MockTransport(lambda r: httpx2.Response(500)))
    with pytest.raises(httpx2.HTTPError):
        gw.allow("alice", 0.01)


def row(n=1):
    return {
        "usage_id": f"u{n}",
        "story_id": None,
        "role": "rp",
        "model": "m",
        "prompt_tokens": 10,
        "cached_tokens": 0,
        "completion_tokens": 5,
        "cost": 0.0,
        "estimated": False,
    }


def test_the_meter_is_tried_twice_then_raises():
    fake = FakeGateway(down=1)
    fake.client().meter("alice", row())  # one 503, then taken
    assert list(fake.ledger["alice"]) == ["u1"]
    with pytest.raises(httpx2.HTTPError):
        FakeGateway(down=2).client().meter("alice", row())


def test_the_outbox_sends_what_the_meter_could_not(conn):
    for n in (1, 2, 3):
        conn.execute(
            "INSERT INTO usage_log(role, model, prompt_tokens, usage_id, metered)"
            " VALUES('rp', 'm', 10, ?, ?)",
            (f"u{n}", int(n == 1)),
        )
    conn.commit()
    down = FakeGateway(down=2)  # u2 cannot be sent: it stops there, u3 waits behind it
    assert down.client().resend("alice", conn) == 0
    fake = FakeGateway()
    assert fake.client().resend("alice", conn) == 2
    assert list(fake.ledger["alice"]) == ["u2", "u3"]
    assert conn.execute("SELECT count(*) FROM usage_log WHERE metered=0").fetchone()[0] == 0
