import json

import httpx2
import pytest

from kataki.llm import LLM, Endpoint, LLMError, ThinkSplitter

pytestmark = pytest.mark.anyio

EP = Endpoint(base_url="http://x/v1", api_key="k", model="m")


@pytest.fixture
def anyio_backend():
    return "asyncio"


def sse(*deltas, usage=None):
    events = [{"choices": [{"delta": d}]} for d in deltas]
    if usage:
        events.append({"choices": [], "usage": usage})
    return "".join(f"data: {json.dumps(e)}\n\n" for e in events) + "data: [DONE]\n\n"


def completion(content):
    return httpx2.Response(200, json={"choices": [{"message": {"content": content}}]})


class Recorder:
    """A fake backend: replies from a script and remembers every request body."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.requests: list[httpx2.Request] = []
        self.bodies: list[dict] = []

    def __call__(self, request):
        self.requests.append(request)
        self.bodies.append(json.loads(request.content) if request.content else {})
        reply = self.replies.pop(0)
        return reply(self.bodies[-1]) if callable(reply) else reply

    @property
    def llm(self):
        return LLM(transport=httpx2.MockTransport(self))


async def collect(stream):
    return [event async for event in stream]


# --- streaming -----------------------------------------------------------------------


async def test_stream_yields_tokens_then_done_with_usage():
    usage = {"prompt_tokens": 120, "completion_tokens": 2}
    backend = Recorder(
        httpx2.Response(200, text=sse({"content": "Hel"}, {"content": "lo"}, usage=usage))
    )
    events = await collect(backend.llm.chat_stream(EP, [{"role": "user", "content": "hi"}]))
    assert events == [("token", "Hel"), ("token", "lo"), ("done", {"usage": usage})]


async def test_reasoning_content_goes_to_the_thought_channel():
    backend = Recorder(
        httpx2.Response(200, text=sse({"reasoning_content": "hmm"}, {"content": "Hello"}))
    )
    events = await collect(backend.llm.chat_stream(EP, []))
    assert events[:2] == [("thought", "hmm"), ("token", "Hello")]


async def test_inline_think_tags_split_across_deltas_never_leak_into_tokens():
    deltas = [{"content": c} for c in ("<thi", "nk>the secret</th", "ink>Hel", "lo")]
    backend = Recorder(httpx2.Response(200, text=sse(*deltas)))
    events = await collect(backend.llm.chat_stream(EP, []))
    tokens = "".join(text for kind, text in events if kind == "token")
    thoughts = "".join(text for kind, text in events if kind == "thought")
    assert (tokens, thoughts) == ("Hello", "the secret")


async def test_request_carries_auth_messages_and_body_params_verbatim():
    ep = Endpoint(
        base_url="http://x/v1",
        api_key="k",
        model="m",
        params={"body": {"min_p": 0.05, "dry_multiplier": 0.8, "id_slot": 0}},
    )
    backend = Recorder(httpx2.Response(200, text=sse({"content": "x"})))
    msgs = [{"role": "user", "content": "hi"}]
    await collect(backend.llm.chat_stream(ep, msgs))

    request, body = backend.requests[0], backend.bodies[0]
    assert str(request.url) == "http://x/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer k"
    assert body["model"] == "m" and body["messages"] == msgs and body["stream"] is True
    assert (body["min_p"], body["dry_multiplier"], body["id_slot"]) == (0.05, 0.8, 0)


async def test_thinking_disabled_is_requested_through_the_chat_template():
    ep = Endpoint(base_url="http://x/v1", model="m", params={"thinking": "disabled"})
    backend = Recorder(httpx2.Response(200, text=sse({"content": "x"})))
    await collect(backend.llm.chat_stream(ep, []))
    assert backend.bodies[0]["chat_template_kwargs"] == {"enable_thinking": False}
    assert "authorization" not in backend.requests[0].headers  # no key, no header


async def test_http_error_raises_with_status_and_body():
    backend = Recorder(httpx2.Response(503, text="model is loading"))
    with pytest.raises(LLMError, match="503.*model is loading"):
        await collect(backend.llm.chat_stream(EP, []))


async def test_error_event_inside_a_200_stream_raises():
    body = sse({"content": "Hel"}).replace(
        "data: [DONE]", 'data: {"error": {"message": "rate limited"}}'
    )
    backend = Recorder(httpx2.Response(200, text=body))
    with pytest.raises(LLMError, match="rate limited"):
        await collect(backend.llm.chat_stream(EP, []))


async def test_unreachable_server_raises_llmerror_naming_the_url():
    def refuse(request):
        raise httpx2.ConnectError("connection refused")

    llm = LLM(transport=httpx2.MockTransport(refuse))
    with pytest.raises(LLMError, match="http://x/v1"):
        await collect(llm.chat_stream(EP, []))


# --- JSON tasks ----------------------------------------------------------------------

SCHEMA = {"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"]}


def parse_n(data):
    if not isinstance(data.get("n"), int):
        raise ValueError("n must be an integer")
    return data["n"]


async def test_json_task_asks_for_the_schema_first():
    backend = Recorder(completion('{"n": 7}'))
    assert await backend.llm.complete_json(EP, [], SCHEMA, parse_n) == 7
    fmt = backend.bodies[0]["response_format"]
    assert fmt["type"] == "json_schema" and fmt["json_schema"]["schema"] == SCHEMA
    assert backend.bodies[0]["temperature"] == 0


async def test_json_task_steps_down_when_the_backend_rejects_response_format():
    rejected = httpx2.Response(400, text="response_format not supported")
    backend = Recorder(rejected, rejected, completion('Sure! {"n": 3} hope that helps'))
    assert await backend.llm.complete_json(EP, [], SCHEMA, parse_n) == 3
    formats = [b.get("response_format", {}).get("type") for b in backend.bodies]
    assert formats == ["json_schema", "json_object", None]


async def test_think_wrapped_json_is_stripped_before_parsing():
    backend = Recorder(completion('<think>maybe {"n": 1}?</think>{"n": 2}'))
    assert await backend.llm.complete_json(EP, [], SCHEMA, parse_n) == 2


async def test_invalid_output_is_retried_once_with_the_error_then_gives_up():
    backend = Recorder(completion('{"n": "seven"}'), completion("still not json"))
    with pytest.raises(LLMError, match="invalid JSON output"):
        await backend.llm.complete_json(EP, [{"role": "user", "content": "go"}], SCHEMA, parse_n)
    assert len(backend.bodies) == 2
    assert "n must be an integer" in backend.bodies[1]["messages"][-1]["content"]


async def test_reasoning_model_that_keeps_thinking_skips_grammar_constrained_mode():
    ep = Endpoint(base_url="http://x/v1", model="m", reasoning=True)
    backend = Recorder(completion('<think>let me see</think>{"n": 5}'))
    assert await backend.llm.complete_json(ep, [], SCHEMA, parse_n) == 5
    assert backend.bodies[0]["response_format"] == {"type": "json_object"}


async def test_reasoning_model_with_thinking_off_may_use_the_schema():
    ep = Endpoint(
        base_url="http://x/v1", model="m", reasoning=True, params={"thinking": "disabled"}
    )
    backend = Recorder(completion('{"n": 5}'))
    await backend.llm.complete_json(ep, [], SCHEMA, parse_n)
    assert backend.bodies[0]["response_format"]["type"] == "json_schema"


# --- models and embeddings -----------------------------------------------------------


async def test_list_models_returns_ids():
    backend = Recorder(httpx2.Response(200, json={"data": [{"id": "a"}, {"id": "b"}]}))
    assert await backend.llm.list_models("http://x/v1", "k") == ["a", "b"]
    assert str(backend.requests[0].url) == "http://x/v1/models"


async def test_embed_returns_vectors_in_input_order():
    data = [{"index": 1, "embedding": [0.2]}, {"index": 0, "embedding": [0.1]}]
    backend = Recorder(httpx2.Response(200, json={"data": data}))
    assert await backend.llm.embed(EP, ["first", "second"]) == [[0.1], [0.2]]
    assert backend.bodies[0] == {"model": "m", "input": ["first", "second"]}


# --- the splitter on its own ---------------------------------------------------------


def test_splitter_releases_text_that_only_looked_like_a_tag():
    s = ThinkSplitter()
    out = s.feed("a <th") + s.feed("umb up") + s.flush()
    assert "".join(t for k, t in out if k == "token") == "a <thumb up"
    assert all(k == "token" for k, _ in out)


def test_splitter_supports_custom_tags_and_unterminated_thoughts():
    s = ThinkSplitter("[[", "]]")
    out = s.feed("hi [[plan") + s.feed("ning") + s.flush()
    assert out == [("token", "hi "), ("thought", "plan"), ("thought", "ning")]
