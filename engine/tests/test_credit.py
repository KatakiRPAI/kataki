"""The credit gate (minds spec §4, §8.4; track B3): online, a call the balance cannot cover is
refused before it is sent, and every caller says NO_CREDIT cleanly. The desktop never refuses."""

import json

import httpx2
import pytest
from fastapi.testclient import TestClient

from kataki import after, between, chat, extract, library, turns
from kataki.host import OnlineHost
from kataki.llm import DailyCap, Endpoint, NoCredit
from kataki.server import create_app

PRICES = {"rp-model": {"input": 1.0, "output": 2.0}, "kokoro": {"char": 4.0}}
ASK = [{"role": "user", "content": "x" * 400}]
MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 64


def ep(role="rp", model="rp-model"):
    return Endpoint("http://fake/v1", model, role=role)


def refusing(backend):
    llm = backend.llm
    llm.allow = lambda ep, ask: False
    return llm


def online(allow=lambda ep, estimate: True, meter=None):
    return OnlineHost(
        get_key=lambda name: None,
        meter=meter or (lambda row: None),
        allow=allow,
        channel=lambda: "alpha",
        prices=lambda: PRICES,
    )


def a_story(conn):
    mira = library.create_item(conn, "character", "Mira")
    aren = library.create_item(conn, "character", "Aren")
    return library.create_story(conn, "s", character_ids=[mira], persona_id=aren)


def events(text: str) -> list[tuple[str, dict]]:
    out = []
    for block in text.strip().split("\n\n"):
        kind, data = block.split("\n", 1)
        out.append((kind.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return out


# --- the one choke point ---------------------------------------------------------------------


@pytest.mark.anyio
async def test_a_refused_reply_is_never_sent(backend):
    with pytest.raises(NoCredit) as refused:
        [e async for e in refusing(backend).chat_stream(ep(), ASK)]
    assert refused.value.code == "NO_CREDIT" and backend.requests == []


@pytest.mark.anyio
async def test_a_refused_json_call_is_never_sent(backend):
    with pytest.raises(NoCredit):
        await refusing(backend).complete_json(ep("utility"), ASK, {"type": "object"}, dict)
    assert backend.requests == []


@pytest.mark.anyio
async def test_a_refused_embedding_is_never_sent(backend):
    with pytest.raises(NoCredit):
        await refusing(backend).embed(ep("embed", "e"), ["hello"])
    assert backend.requests == []


@pytest.mark.anyio
async def test_refused_speech_is_never_sent(backend):
    with pytest.raises(NoCredit):
        await refusing(backend).speech(ep("voice", "kokoro"), "Evening.", "af_heart")
    assert backend.requests == []


@pytest.mark.anyio
async def test_the_gate_is_asked_before_each_actual_request(backend):
    """A refused format's step-down is a second request: the gate is asked again for it."""
    asked = []
    llm = backend.llm
    llm.allow = lambda ep, ask: asked.append(ask) or True
    backend.say(httpx2.Response(400, text="no json_schema"), '{"x": 1}')
    await llm.complete_json(ep("utility"), ASK, {"type": "object"}, dict)
    assert len(asked) == len(backend.requests) == 2


def test_the_host_gets_a_dollar_estimate(local_model, backend):
    conn = local_model
    seen = []
    llm = backend.llm
    create_app(conn, "t", llm, host=online(allow=lambda ep, est: seen.append((ep.role, est)) or 1))
    backend.say("Hi.")

    import asyncio

    async def go():
        return [e async for e in llm.chat_stream(ep(), ASK, max_tokens=500)]

    asyncio.run(go())
    # 400 characters in (/4 = 100 tokens at $1/M), max_tokens 500 out at $2/M
    assert seen == [("rp", pytest.approx((100 * 1.0 + 500 * 2.0) / 1e6))]


def test_an_unpriced_call_is_refused_online_and_never_sent(local_model, backend):
    """A model with no price cannot be billed, so online it is not run (the host never sees an
    estimate of None)."""
    seen = []
    llm = backend.llm
    create_app(local_model, "t", llm, host=online(allow=lambda ep, est: seen.append(est) or 1))

    import asyncio

    with pytest.raises(NoCredit):
        asyncio.run(llm.embed(ep("embed", "unlisted"), ["x"]))
    assert seen == [] and backend.requests == []


def test_online_a_roles_raw_json_cannot_change_what_is_billed(local_model, backend):
    """Online, a role's body params may tune the sampler, never the model, the count, the
    usage report or the length the gate priced."""
    llm = backend.llm
    create_app(local_model, "t", llm, host=online())
    body = {
        "model": "pricey",
        "n": 8,
        "stream_options": {"include_usage": False},
        "max_tokens": None,
        "temperature": 0.3,
        "min_p": 0.05,
    }
    backend.say("Hi.")

    import asyncio

    async def go():
        rp = Endpoint("http://fake/v1", "rp-model", role="rp", params={"body": body})
        return [e async for e in llm.chat_stream(rp, ASK, max_tokens=500)]

    asyncio.run(go())
    sent = backend.requests[0]
    assert (sent["model"], sent["max_tokens"], sent["temperature"], sent["min_p"]) == (
        "rp-model",
        500,
        0.3,
        0.05,
    )
    assert "n" not in sent and sent["stream_options"] == {"include_usage": True}


def test_the_online_gate_fails_closed():
    def down(ep, estimate):
        raise ConnectionError("gateway unreachable")

    assert online(allow=down).allow(ep(), 0.01) is False
    assert online(allow=lambda ep, est: 0).allow(ep(), 0.01) is False


def test_the_desktop_never_refuses(conn, backend):
    llm = backend.llm
    create_app(conn, "t", llm)
    assert llm.allow is None  # no gate code runs at all


# --- every caller says so --------------------------------------------------------------------


@pytest.fixture
def broke(local_model, backend):
    """An online app whose account has no credit left."""
    app = create_app(local_model, "t", backend.llm, worker_delay=60, host=online(lambda e, x: 0))
    client = TestClient(app)
    client.headers["Authorization"] = "Bearer t"
    with client:
        yield client


def test_a_refused_reply_says_no_credit_and_saves_no_reply(local_model, broke, backend):
    story = a_story(local_model)
    r = broke.post(f"/stories/{story}/turn", json={"text": "Hi, Mira."})
    kind, data = events(r.text)[-1]
    assert (kind, data["code"]) == ("error", "NO_CREDIT")
    assert backend.requests == []
    path = chat.active_path(local_model, story)
    assert [m["role"] for m in path][-1] == "user"  # the user's line stays; no reply


@pytest.mark.anyio
async def test_a_refused_side_call_keeps_the_reply(local_model, backend, side_call):
    conn = local_model
    story = a_story(conn)
    llm = backend.llm
    asked = []
    # the reply is covered, the side call after it is not
    llm.allow = lambda ep, ask: asked.append(ep.role) or ep.role == "rp"
    backend.say("Hello.")
    got = [e async for e in turns.turn(conn, llm, story, "Hi, Mira.")]
    assert got[-1][0] == "done" and len(backend.requests) == 1
    assert chat.active_path(conn, story)[-1]["text"] == "Hello."
    assert after.wanted(conn) and "utility" in asked  # the side call was due, and refused


def test_a_json_route_answers_402(broke):
    r = broke.post("/library/draft", json={"words": "a tired lighthouse keeper"})
    assert r.status_code == 402
    assert r.json()["code"] == r.json()["detail"]["code"] == "NO_CREDIT"


def test_a_refused_memory_read_leaves_its_lines_unread(local_model, broke):
    conn = local_model
    story = a_story(conn)
    for i in range(8):
        chat.append_message(conn, story, "user" if i % 2 else "assistant", f"Line {i}.", None)
    waiting = len(extract.pending(conn, story))
    r = broke.post(f"/stories/{story}/extract")
    assert r.status_code == 402 and r.json()["code"] == "NO_CREDIT"
    assert conn.execute("SELECT count(*) FROM extraction_runs").fetchone()[0] == 0
    assert len(extract.pending(conn, story)) == waiting  # read again once there is credit


@pytest.mark.anyio
async def test_the_worker_stops_at_a_refusal_and_fails_nothing(local_model, backend):
    conn = local_model
    story = a_story(conn)
    for i in range(30):
        chat.append_message(conn, story, "user" if i % 2 else "assistant", f"Line {i}.", None)
    assert extract.due(conn, story) is not None  # a read is due
    llm = refusing(backend)
    worker = extract.Worker(conn, llm, delay=0)
    await worker._work(story)  # no exception escapes the background task
    assert conn.execute("SELECT count(*) FROM extraction_runs").fetchone()[0] == 0
    assert backend.requests == []


@pytest.mark.anyio
async def test_a_refused_diary_call_stays_owed(local_model, backend):
    conn = local_model
    cards = {n: library.create_item(conn, "character", n) for n in ("Mira", "Aren")}
    story = library.create_story(conn, "s", character_ids=[cards["Mira"]], persona_id=cards["Aren"])
    chat.append_message(conn, story, "user", "I have to go.", None)
    turns.say(conn, story, skip="two days later")
    run = between.at_skip(conn, story, chat.active_path(conn, story))
    [(run_id, who)] = between.todo(conn, story)
    with pytest.raises(NoCredit):
        await between.think(conn, refusing(backend), story, run_id, who)
    assert between.todo(conn, story) == [(run, who)]  # pending, not failed


def test_voice_answers_402(local_model, broke, backend):
    conn = local_model
    conn.execute("INSERT INTO providers(id, name, base_url) VALUES(2, 'tts', 'http://tts/v1')")
    conn.execute("INSERT INTO model_roles(role, provider_id, model) VALUES('voice', 2, 'kokoro')")
    conn.execute("INSERT INTO settings(key, value) VALUES('voice.on', 'true')")
    story = a_story(conn)
    mira = conn.execute("SELECT id FROM entities WHERE name='Mira'").fetchone()[0]
    line = chat.add_child(conn, story, None, "user", "Evening.", None)
    reply = chat.add_child(conn, story, line, "assistant", '"Evening."', mira, 0, {})
    r = broke.post(f"/messages/{reply}/voice")
    assert r.status_code == 402 and backend.requests == []


def test_prices_are_the_services_online(broke):
    r = broke.put("/settings", json={"prices": {"rp-model": {"input": 0, "output": 0}}})
    assert r.status_code == 403
    assert "prices" not in broke.get("/settings").json()


def test_prices_are_the_users_on_the_desktop(conn):
    client = TestClient(create_app(conn, "t"))
    r = client.put("/settings", json={"prices": PRICES}, headers={"Authorization": "Bearer t"})
    assert r.status_code == 200 and r.json()["prices"] == PRICES


# --- the daily cap (B5): refused like NO_CREDIT, said with its own code ------------------------


def over_the_cap(ep, estimate):
    raise DailyCap("You have reached today's spending limit.")


@pytest.fixture
def capped(local_model, backend):
    app = create_app(local_model, "t", backend.llm, worker_delay=60, host=online(over_the_cap))
    client = TestClient(app)
    client.headers["Authorization"] = "Bearer t"
    with client:
        yield client


def test_the_daily_cap_is_a_refusal_with_its_own_code():
    assert issubclass(DailyCap, NoCredit) and DailyCap.code == "DAILY_CAP"
    with pytest.raises(DailyCap):  # not turned into a plain "no" by the fail-closed wrapper
        online(allow=over_the_cap).allow(ep(), 0.01)


def test_the_daily_cap_says_so_on_every_surface(local_model, capped, backend):
    story = a_story(local_model)
    kind, data = events(capped.post(f"/stories/{story}/turn", json={"text": "Hi."}).text)[-1]
    assert (kind, data["code"]) == ("error", "DAILY_CAP")
    r = capped.post("/library/draft", json={"words": "a tired lighthouse keeper"})
    assert r.status_code == 402 and r.json()["code"] == "DAILY_CAP"
    for i in range(8):
        chat.append_message(local_model, story, "user" if i % 2 else "assistant", f"L{i}.", None)
    r = capped.post(f"/stories/{story}/extract")
    assert r.status_code == 402 and r.json()["detail"]["code"] == "DAILY_CAP"
    assert backend.requests == []
