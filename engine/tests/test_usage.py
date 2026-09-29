"""Every model call leaves one usage row: role, model, tokens."""

import functools

import pytest

from kataki import chat, library, roles, turns, usage
from kataki.llm import Endpoint

pytestmark = pytest.mark.anyio


def rows(conn):
    return [
        tuple(r)
        for r in conn.execute(
            "SELECT story_id, role, model, prompt_tokens, completion_tokens FROM usage_log"
        )
    ]


async def test_a_reply_is_recorded_with_its_story_and_role(local_model, backend):
    conn = local_model
    mira = library.create_item(conn, "character", "Mira")
    aren = library.create_item(conn, "character", "Aren")
    story = library.create_story(conn, "s", character_ids=[mira], persona_id=aren)
    llm = backend.llm
    llm.on_usage = functools.partial(usage.record, conn)
    backend.say({"content": "Hello.", "usage": {"prompt_tokens": 120, "completion_tokens": 3}})

    [event async for event in turns.turn(conn, llm, story, "Hi, Mira.")]

    assert rows(conn) == [(story, "rp", "rp-model", 120, 3)]


async def test_a_json_call_is_recorded_too(conn, backend):
    llm = backend.llm
    seen = []
    llm.on_usage = lambda ep, used: seen.append((ep.role, used["completion_tokens"]))
    backend.say({"content": '{"x": 1}', "usage": {"prompt_tokens": 9, "completion_tokens": 4}})
    ep = Endpoint("http://fake/v1", "u", role="utility")

    await llm.complete_json(ep, [{"role": "user", "content": "x"}], {"type": "object"}, dict)

    assert seen == [("utility", 4)]


def test_resolve_stamps_the_role_and_story(local_model):
    ep = roles.resolve(local_model, "utility", 7)
    assert (ep.role, ep.story_id) == ("utility", 7)


async def test_a_failing_usage_hook_never_costs_the_reply(local_model, backend):
    conn = local_model
    mira = library.create_item(conn, "character", "Mira")
    aren = library.create_item(conn, "character", "Aren")
    story = library.create_story(conn, "s", character_ids=[mira], persona_id=aren)
    llm = backend.llm

    def broken(ep, used):
        raise RuntimeError("meter down")

    llm.on_usage = broken
    backend.say({"content": "Hello.", "usage": {"prompt_tokens": 1, "completion_tokens": 1}})

    events = [event async for event in turns.turn(conn, llm, story, "Hi, Mira.")]

    assert any(e[0] == "done" for e in events)
    assert "Hello." in [m["text"] for m in chat.active_path(conn, story)]
