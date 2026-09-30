"""Billing (minds spec §4, §8.4; track B2): what each model call cost, exactly one row per call
that reached a provider, estimated when the provider never said."""

import asyncio
import contextlib
import functools
import json

import httpx2
import pytest

from kataki import db, library, turns, usage
from kataki.host import Host
from kataki.llm import Endpoint, LLMError

PRICES = {
    "rp-model": {"input": 1.0, "cached": 0.1, "output": 4.0},
    "kokoro": {"char": 4.0},
}
ASK = [{"role": "user", "content": "x" * 400}]


def metered(conn):
    return [
        dict(r)
        for r in conn.execute(
            "SELECT role, model, prompt_tokens, cached_tokens, completion_tokens, cost, estimated,"
            " usage_id FROM usage_log ORDER BY id"
        )
    ]


def set_prices(conn, prices=PRICES):
    conn.execute(
        "INSERT OR REPLACE INTO settings(key, value) VALUES('prices', ?)", (json.dumps(prices),)
    )


def ep(role="rp", model="rp-model"):
    return Endpoint("http://fake/v1", model, role=role)


def recording(backend, conn):
    llm = backend.llm
    llm.on_usage = functools.partial(usage.record, conn)
    return llm


# --- cost per row ------------------------------------------------------------------------------


def test_a_priced_call_stores_its_cost_cached_input_at_the_cached_price(conn):
    set_prices(conn)
    used = {
        "prompt_tokens": 1000,
        "completion_tokens": 100,
        "prompt_tokens_details": {"cached_tokens": 800},
    }
    row = usage.record(conn, ep(), used)
    # 200 fresh at $1/M + 800 cached at $0.1/M + 100 out at $4/M
    assert row["cost"] == pytest.approx((200 * 1.0 + 800 * 0.1 + 100 * 4.0) / 1e6)
    [stored] = metered(conn)
    assert stored["cost"] == pytest.approx(row["cost"]) and stored["usage_id"] == row["usage_id"]
    assert len(row["usage_id"]) == 32 and row["estimated"] is False


def test_cached_price_defaults_to_the_input_price(conn):
    set_prices(conn, {"rp-model": {"input": 2.0, "output": 0}})
    used = {"prompt_tokens": 10, "prompt_tokens_details": {"cached_tokens": 10}}
    assert usage.record(conn, ep(), used)["cost"] == pytest.approx(20 / 1e6)


def test_a_voice_row_is_priced_by_the_character(conn):
    set_prices(conn)
    row = usage.record(conn, ep("voice", "kokoro"), {"prompt_tokens": 250})
    assert row["cost"] == pytest.approx(250 * 4.0 / 1e6)


@pytest.mark.parametrize(
    "prices",
    [
        {},
        {"rp-model": "cheap"},
        {"rp-model": {"input": "x", "output": 1}},
        {"rp-model": {"output": 1}},
        {"rp-model": {"input": -1, "output": 1}},
        ["rp-model"],
    ],
)
def test_an_unpriced_or_malformed_model_costs_null_and_is_still_recorded(conn, prices):
    set_prices(conn, prices)
    assert usage.record(conn, ep(), {"prompt_tokens": 5})["cost"] is None
    assert len(metered(conn)) == 1


def test_the_hosts_price_table_wins(conn):
    set_prices(conn, {"rp-model": {"input": 0, "output": 0}})  # the user's own table
    sent = []
    host = Host(prices=lambda: PRICES, meter=sent.append)
    host.on_usage(conn, ep(), {"prompt_tokens": 1_000_000})
    assert sent[0]["cost"] == pytest.approx(1.0) and metered(conn)[0]["cost"] == pytest.approx(1.0)
    assert sent[0]["usage_id"] == metered(conn)[0]["usage_id"]


def test_a_broken_price_table_still_records_and_meters(conn):
    def broken():
        raise RuntimeError("catalogue down")

    sent = []
    Host(prices=broken, meter=sent.append).on_usage(conn, ep(), {"prompt_tokens": 3})
    assert sent[0]["cost"] is None and len(metered(conn)) == 1


def test_v18_prices_each_usage_row(tmp_path):
    path = tmp_path / "v17.db"
    old = db.connect(path)  # today's schema, then pretend it is v17 (usage_log without the columns)
    old.executescript(
        "DROP TABLE usage_log; CREATE TABLE usage_log("
        " id INTEGER PRIMARY KEY,"
        " story_id INTEGER REFERENCES stories ON DELETE SET NULL,"
        " role TEXT NOT NULL, model TEXT NOT NULL,"
        " prompt_tokens INTEGER NOT NULL DEFAULT 0, cached_tokens INTEGER NOT NULL DEFAULT 0,"
        " completion_tokens INTEGER NOT NULL DEFAULT 0,"
        " at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);"
        "INSERT INTO usage_log(role, model, prompt_tokens) VALUES('rp', 'm', 12);"
    )
    old.execute("PRAGMA user_version=17")
    old.commit()
    old.close()

    conn = db.connect(path)
    [row] = conn.execute("SELECT * FROM usage_log").fetchall()
    got = (row["prompt_tokens"], row["cost"], row["estimated"], row["usage_id"])
    assert got == (12, None, 0, None)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION == 18
    conn.close()


# --- exactly once per call that reached a provider --------------------------------------------


@pytest.mark.anyio
async def test_a_stopped_stream_is_metered_once_from_what_streamed(conn, backend):
    llm = recording(backend, conn)
    backend.say("abcdefghijklmnopqrstuvwxyz" * 4)  # streamed six characters at a time
    stream = llm.chat_stream(ep(), ASK)
    got = [await anext(stream), await anext(stream)]  # the user stops after two pieces
    await stream.aclose()
    assert [k for k, _ in got] == ["token", "token"]
    [row] = metered(conn)
    # 400 characters sent, 12 streamed: characters / 4
    assert (row["prompt_tokens"], row["completion_tokens"], row["estimated"]) == (100, 3, 1)


@pytest.mark.anyio
async def test_a_finished_stream_is_metered_once_with_the_providers_numbers(conn, backend):
    llm = recording(backend, conn)
    backend.say({"content": "Hi.", "usage": {"prompt_tokens": 7, "completion_tokens": 2}})
    stream = llm.chat_stream(ep(), ASK)
    async for kind, _ in stream:
        if kind == "done":
            break  # closing right at done must not meter it again
    await stream.aclose()
    got = [(r["prompt_tokens"], r["completion_tokens"], r["estimated"]) for r in metered(conn)]
    assert got == [(7, 2, 0)]


@pytest.mark.anyio
async def test_a_backend_that_never_reports_usage_is_estimated(conn, backend):
    llm = recording(backend, conn)
    sse = 'data: {"choices": [{"delta": {"content": "Hello there."}}]}\n\ndata: [DONE]\n\n'
    backend.say(httpx2.Response(200, text=sse))
    events = [e async for e in llm.chat_stream(ep(), ASK)]
    assert events[-1] == ("done", {"usage": None})  # the turn still sees what the provider said
    [row] = metered(conn)
    assert (row["prompt_tokens"], row["completion_tokens"], row["estimated"]) == (100, 3, 1)


@pytest.mark.anyio
async def test_a_stream_that_fails_midway_is_metered(conn, backend):
    llm = recording(backend, conn)
    sse = (
        'data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n'
        'data: {"error": {"message": "overloaded"}}\n\n'
    )
    backend.say(httpx2.Response(200, text=sse))
    with pytest.raises(LLMError):
        [e async for e in llm.chat_stream(ep(), ASK)]
    assert [r["estimated"] for r in metered(conn)] == [1]


@pytest.mark.anyio
async def test_a_refused_request_is_not_metered(conn, backend):
    llm = recording(backend, conn)
    backend.say(httpx2.Response(500, text="boom"))
    with pytest.raises(LLMError):
        [e async for e in llm.chat_stream(ep(), ASK)]
    assert metered(conn) == []


@pytest.mark.anyio
async def test_refused_samplers_then_the_retry_meter_once(conn, backend):
    llm = recording(backend, conn)
    backend.say(httpx2.Response(422, text="unknown field min_p"), "Hi.")
    [e async for e in llm.chat_stream(ep(), ASK, samplers={"min_p": 0.05})]
    assert len(backend.requests) == 2 and len(metered(conn)) == 1


@pytest.mark.anyio
async def test_a_busy_provider_asked_again_meters_once(conn, backend, monkeypatch):
    monkeypatch.setattr("kataki.llm.RETRY_AFTER", 0)
    llm = recording(backend, conn)
    backend.say(httpx2.Response(429, text="busy"), "Hi.")
    [e async for e in llm.chat_stream(ep(), ASK)]
    assert len(backend.requests) == 2 and len(metered(conn)) == 1


@pytest.mark.anyio
async def test_a_refused_format_then_the_step_down_meter_once(conn, backend):
    llm = recording(backend, conn)
    backend.say(httpx2.Response(400, text="no json_schema"), '{"x": 1}')
    await llm.complete_json(ep("utility"), ASK, {"type": "object"}, dict)
    assert len(backend.requests) == 2 and len(metered(conn)) == 1


@pytest.mark.anyio
async def test_a_parse_retry_is_a_second_call_and_meters_twice(conn, backend):
    llm = recording(backend, conn)
    backend.say("not json", '{"x": 1}')
    await llm.complete_json(ep("utility"), ASK, {"type": "object"}, dict)
    assert len(backend.requests) == 2 and len(metered(conn)) == 2


@pytest.mark.anyio
async def test_a_cut_off_completion_is_metered_before_it_fails(conn, backend):
    llm = recording(backend, conn)
    sse = (
        'data: {"choices": [{"delta": {"content": "{\\"x\\": "}, "finish_reason": "length"}]}\n\n'
        'data: {"choices": [], "usage": {"prompt_tokens": 50, "completion_tokens": 900}}\n\n'
        "data: [DONE]\n\n"
    )
    backend.say(httpx2.Response(200, text=sse))
    with pytest.raises(LLMError, match="ran out of room"):
        await llm.complete_json(ep("utility"), ASK, {"type": "object"}, dict)
    assert [(r["completion_tokens"], r["estimated"]) for r in metered(conn)] == [(900, 0)]


@pytest.mark.anyio
async def test_a_json_call_cancelled_mid_stream_is_metered(conn, backend):
    """A diary call cancelled by a reply (owed M5) may still bill: it is metered."""
    llm = recording(backend, conn)
    started, hold = asyncio.Event(), asyncio.Event()

    async def slow():
        yield b'data: {"choices": [{"delta": {"content": "{\\"x\\""}}]}\n\n'
        started.set()
        await hold.wait()

    backend.say(httpx2.Response(200, content=slow()))
    task = asyncio.ensure_future(llm.complete_json(ep("utility"), ASK, {"type": "object"}, dict))
    await started.wait()
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
    assert [r["estimated"] for r in metered(conn)] == [1]


@pytest.mark.anyio
async def test_an_embedding_without_usage_is_estimated(conn, backend):
    llm = recording(backend, conn)
    backend.say(httpx2.Response(200, json={"data": [{"index": 0, "embedding": [0.1]}]}))
    await llm.embed(ep("embed", "e"), ["y" * 40])
    [row] = metered(conn)
    assert (row["prompt_tokens"], row["estimated"]) == (10, 1)


@pytest.mark.anyio
async def test_a_dropped_take_is_metered(local_model, backend):
    conn = local_model
    names = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    story = library.create_story(
        conn, "s", character_ids=[names["Mira"], names["Tobin"]], persona_id=names["Aren"]
    )
    llm = recording(backend, conn)
    backend.say("You're right. I'm useless.", "Say that again.")
    [e async for e in turns.turn(conn, llm, story, "Mira, you're useless.")]
    assert len(backend.requests) == 2
    rows = [r for r in metered(conn) if r["role"] == "rp"]
    assert [r["estimated"] for r in rows] == [1, 0]  # the dropped take, then the kept one
