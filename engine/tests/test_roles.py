import json

import httpx2
import pytest

from kataki import roles
from kataki.llm import LLM, Endpoint

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def keys(provider_name):
    return {"local": None, "cloud": "sk-cloud"}[provider_name]


@pytest.fixture
def lib(conn):
    conn.execute("INSERT INTO providers(id, name, base_url) VALUES(1, 'local', 'http://l/v1')")
    conn.execute("INSERT INTO providers(id, name, base_url) VALUES(2, 'cloud', 'https://c/v1')")
    return conn


def set_role(conn, role, provider_id=None, model=None, kind="auto", detected=None, params=None):
    conn.execute(
        "INSERT OR REPLACE INTO model_roles(role, provider_id, model, kind, detected_kind, params)"
        " VALUES(?, ?, ?, ?, ?, ?)",
        (role, provider_id, model, kind, detected, json.dumps(params or {})),
    )


# --- routing -------------------------------------------------------------------------


def test_a_configured_role_resolves_to_its_own_endpoint(lib):
    set_role(lib, "rp", 2, "big-rp", params={"body": {"min_p": 0.05}})
    ep = roles.resolve(lib, "rp", get_key=keys)
    assert ep == Endpoint(
        base_url="https://c/v1",
        model="big-rp",
        api_key="sk-cloud",
        params={"body": {"min_p": 0.05}},
        role="rp",
    )


def test_unset_roles_inherit_along_the_chain(lib):
    set_role(lib, "rp", 1, "rp-8b")
    for role in ("narrator", "utility", "reasoning"):  # reasoning -> utility -> rp
        assert roles.resolve(lib, role, get_key=keys).model == "rp-8b"

    set_role(lib, "utility", 1, "util-3b")
    assert roles.resolve(lib, "reasoning", get_key=keys).model == "util-3b"
    assert roles.resolve(lib, "narrator", get_key=keys).model == "rp-8b"


def test_nothing_configured_resolves_to_none(lib):
    assert roles.resolve(lib, "reasoning", get_key=keys) is None
    set_role(lib, "rp", 1, "rp-8b")
    assert roles.resolve(lib, "embed", get_key=keys) is None  # embed never inherits a chat model


def test_an_inheriting_role_keeps_its_own_params_over_the_parents(lib):
    # the 8 GB setup: one hybrid model, thinking off for rp, on for reasoning
    set_role(
        lib,
        "rp",
        1,
        "hybrid",
        detected="reasoning",
        params={"thinking": "disabled", "ctx_size": 8192},
    )
    set_role(lib, "reasoning", params={"thinking": "enabled"})

    rp = roles.resolve(lib, "rp", get_key=keys)
    reasoning = roles.resolve(lib, "reasoning", get_key=keys)
    assert (rp.model, rp.thinks) == ("hybrid", False)
    assert (reasoning.model, reasoning.thinks) == ("hybrid", True)
    assert reasoning.params["ctx_size"] == 8192


def test_kind_override_beats_the_probe_result(lib):
    set_role(lib, "rp", 1, "m", kind="auto", detected="reasoning")
    assert roles.resolve(lib, "rp", get_key=keys).reasoning is True
    set_role(lib, "rp", 1, "m", kind="standard", detected="reasoning")
    assert roles.resolve(lib, "rp", get_key=keys).reasoning is False
    set_role(lib, "rp", 1, "m", kind="reasoning", detected="standard")
    assert roles.resolve(lib, "rp", get_key=keys).reasoning is True


def test_a_story_can_override_a_role(lib):
    set_role(lib, "rp", 1, "rp-8b")
    overrides = {"roles": {"rp": {"provider_id": 2, "model": "horror-70b", "kind": "standard"}}}
    story = lib.execute(
        "INSERT INTO stories(title, overrides) VALUES('s', ?)", (json.dumps(overrides),)
    ).lastrowid

    assert roles.resolve(lib, "rp", story_id=story, get_key=keys).model == "horror-70b"
    assert roles.resolve(lib, "narrator", story_id=story, get_key=keys).model == "horror-70b"
    assert roles.resolve(lib, "rp", get_key=keys).model == "rp-8b"  # other stories untouched


def test_routing_table_shows_where_each_role_gets_its_model(lib):
    set_role(lib, "rp", 1, "rp-8b", detected="standard")
    table = {row["role"]: row for row in roles.routing(lib)}
    assert set(table) == {"rp", "narrator", "utility", "reasoning", "embed", "image", "music"}
    assert table["rp"]["inherited_from"] is None and table["rp"]["effective_model"] == "rp-8b"
    assert table["reasoning"]["inherited_from"] == "rp"
    assert table["reasoning"]["effective_kind"] == "standard"
    assert table["embed"]["effective_model"] is None


# --- kind probe ----------------------------------------------------------------------


def sse(*deltas):
    lines = [f"data: {json.dumps({'choices': [{'delta': d}]})}\n\n" for d in deltas]
    return "".join(lines) + "data: [DONE]\n\n"


async def probe(stream_text):
    llm = LLM(transport=httpx2.MockTransport(lambda req: httpx2.Response(200, text=stream_text)))
    return await roles.probe_kind(llm, Endpoint(base_url="http://x/v1", model="m"))


async def test_probe_detects_reasoning_content():
    assert await probe(sse({"reasoning_content": "thinking"}, {"content": "ok"})) == "reasoning"


async def test_probe_detects_inline_think_tags():
    assert await probe(sse({"content": "<think>hm</think>ok"})) == "reasoning"


async def test_probe_marks_plain_models_standard():
    assert await probe(sse({"content": "ok"})) == "standard"
