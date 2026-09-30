"""Kataki online's engine process (minds spec §4, §8.4; track B4, B5): many users, a library
each, who they are only from the gateway's signed headers."""

import asyncio

import httpx2
import pytest

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
