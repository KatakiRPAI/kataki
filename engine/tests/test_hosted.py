"""Kataki online's engine process (minds spec §4, §8.4; track B4, B5): many users, a library
each, who they are only from the gateway's signed headers."""

import asyncio
import json
import time
from pathlib import Path

import httpx2
import pytest
import uvicorn
from fastapi.testclient import TestClient

from kataki import __main__ as cli
from kataki import chat, db, extract, hosted, library, usage
from kataki.llm import LLM, DailyCap, Endpoint
from kataki.server import create_app

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


# --- kataki serve --hosted: a library per user, opened on demand ---------------------------------

PRICES = {"rp-model": {"input": 0.3, "cached": 0.03, "output": 1.2}}


def catalogue(tmp_path) -> Path:
    """The service's own routing and prices, as a library file the operator built."""
    path = tmp_path / "catalogue.db"
    if not path.exists():
        c = db.connect(path)
        c.execute("INSERT INTO providers(id, name, base_url) VALUES(1, 'svc', 'http://fake/v1')")
        c.execute("INSERT INTO model_roles(role, provider_id, model) VALUES('rp', 1, 'rp-model')")
        c.execute("INSERT INTO settings(key, value) VALUES('prices', ?)", (json.dumps(PRICES),))
        c.commit()
        c.close()
    return path


def service(tmp_path, fake=None, transport=None, **kw) -> hosted.Hosted:
    return hosted.Hosted(
        tmp_path / "users",
        SECRET,
        (fake or FakeGateway(PRICES)).client(),
        catalogue(tmp_path),
        transport=transport,
        get_key=lambda name: "service-key",
        **{"worker_delay": 60, **kw},
    )


def now_signed(user="alice", channel="beta") -> dict:
    return signed(user, channel, at=int(time.time()))


def test_a_signed_request_opens_that_users_library(tmp_path):
    with TestClient(service(tmp_path)) as client:
        body = client.get("/health", headers=now_signed()).json()
    assert (body["host"], body["channel"]) == ("online", "beta")
    assert (tmp_path / "users" / "alice" / "library.db").exists()


def test_an_unsigned_request_opens_nothing(tmp_path):
    with TestClient(service(tmp_path)) as client:
        assert client.get("/health", headers={"x-kataki-user": "alice"}).status_code == 401
        forged = {**now_signed(), "x-kataki-user": "bob", "Authorization": "Bearer anything"}
        assert client.get("/health", headers=forged).status_code == 401
    assert not (tmp_path / "users").exists()


def test_each_user_sees_only_their_own_library(tmp_path):
    with TestClient(service(tmp_path)) as client:
        made = {"kind": "character", "name": "Mira"}
        assert client.post("/library", json=made, headers=now_signed("alice")).status_code == 201
        assert client.get("/library", headers=now_signed("bob")).json() == []
        mine = client.get("/library", headers=now_signed("alice")).json()
        assert [i["name"] for i in mine] == ["Mira"]


def test_the_services_catalogue_is_in_every_library(tmp_path):
    app = service(tmp_path)
    with TestClient(app) as client:
        client.get("/health", headers=now_signed())
        conn = app.opened("alice").conn
        conn.execute("UPDATE providers SET base_url='http://mine/v1'")  # the user's own edit
        conn.commit()
        assert client.get("/providers", headers=now_signed()).status_code == 404  # local-only
        assert client.post("/library/1/draw", headers=now_signed()).status_code == 404  # pictures
    with TestClient(app) as client:  # opened again: the service's routing is back
        client.get("/health", headers=now_signed())
        conn = app.opened("alice").conn
        assert [tuple(r) for r in conn.execute("SELECT name, base_url FROM providers")] == [
            ("svc", "http://fake/v1")
        ]


def test_past_the_limit_the_least_recent_library_closes(tmp_path):
    app = service(tmp_path, max_open=1)
    with TestClient(app) as client:
        client.post("/library", json={"kind": "character", "name": "Mira"}, headers=now_signed())
        client.get("/health", headers=now_signed("bob"))
        assert app.opened("alice") is None and app.opened("bob") is not None
        assert len(client.get("/library", headers=now_signed()).json()) == 1  # still there


@pytest.mark.anyio
async def test_the_sweep_closes_idle_libraries_and_empties_the_outbox(tmp_path):
    fake = FakeGateway(PRICES)
    app = service(tmp_path, fake, idle=0)
    lib = app.open("alice")
    lib.conn.execute("INSERT INTO usage_log(role, model, usage_id) VALUES('rp', 'rp-model', 'u9')")
    lib.conn.commit()
    lib.busy = 1  # a request in flight: never closed under it
    await app.sweep()
    assert app.opened("alice") is lib and list(fake.ledger["alice"]) == ["u9"]
    lib.busy = 0
    await app.sweep()
    assert app.opened("alice") is None


def twelve_lines(conn) -> int:
    mira = library.create_item(conn, "character", "Mira")
    aren = library.create_item(conn, "character", "Aren")
    story = library.create_story(conn, "s", character_ids=[mira], persona_id=aren)
    for i in range(12):
        chat.append_message(conn, story, "user" if i % 2 else "assistant", f"Line {i}.", None)
    return story


@pytest.mark.anyio
async def test_closing_a_library_pauses_its_background_read(tmp_path):
    gate, seen = asyncio.Event(), []
    app = service(tmp_path, transport=held(gate, seen), worker_delay=0)
    lib = app.open("alice")
    story = twelve_lines(lib.conn)
    waiting = len(extract.pending(lib.conn, story))
    lib.app.state.worker.poke(story)
    for _ in range(100):
        await asyncio.sleep(0.01)
        if seen:
            break
    assert seen  # the read is in flight
    await app.close("alice")
    assert lib.app.state.worker._task.cancelled()
    lib = app.open("alice")  # the paused read left nothing behind; it is read again later
    assert lib.conn.execute("SELECT count(*) FROM extraction_runs").fetchone()[0] == 0
    assert len(extract.pending(lib.conn, story)) == waiting
    await app.close("alice")


@pytest.mark.anyio
async def test_the_daily_cap_refuses_before_the_gateway_is_asked(tmp_path):
    fake = FakeGateway(PRICES)
    app = service(tmp_path, fake, daily_cap=0.01)
    lib = app.open("alice")
    rp = Endpoint("http://fake/v1", "rp-model", role="rp")
    assert lib.host.allow(rp, 0.004)
    lib.conn.execute("INSERT INTO usage_log(role, model, cost) VALUES('rp', 'rp-model', 0.008)")
    lib.conn.commit()
    with pytest.raises(DailyCap):
        lib.host.allow(rp, 0.004)
    assert fake.asked == ["alice"]  # the refusal never reached the gateway
    await app.close("alice")


def test_the_desktop_never_reads_the_gateways_headers(conn):
    client = TestClient(create_app(conn, "t0k"))
    assert client.get("/health", headers=now_signed()).status_code == 401


def test_the_cli_binds_to_this_machine_and_needs_its_secrets(tmp_path, monkeypatch):
    ran = {}
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: ran.update(kw, app=app))
    args = ["serve", "--hosted", "--root", str(tmp_path / "users")]
    args += ["--catalogue", str(catalogue(tmp_path)), "--gateway", "http://gw"]
    monkeypatch.delenv("KATAKI_GATEWAY_SECRET", raising=False)
    monkeypatch.setenv("KATAKI_GATEWAY_KEY", "k")
    with pytest.raises(SystemExit):
        cli.main(args)
    monkeypatch.setenv("KATAKI_GATEWAY_SECRET", "s")
    cli.main(args)
    assert ran["host"] == "127.0.0.1" and isinstance(ran["app"], hosted.Hosted)
    cli.main([*args, "--bind", "0.0.0.0"])
    assert ran["host"] == "0.0.0.0"
