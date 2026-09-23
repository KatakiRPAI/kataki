"""One OpenAI-compatible client for every text backend.

Covers llama.cpp server, Ollama, LM Studio, KoboldCpp, vLLM, TabbyAPI, OpenRouter and the
HuggingFace Inference Providers router. Reasoning output never mixes with visible text:
it is yielded on its own `thought` channel whether the backend sends `reasoning_content`
or inline think tags.
"""

import json
import re
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any

import httpx2

Event = tuple[str, Any]  # ("thought" | "token", text) ... then ("done", {"usage": ...})
DEFAULT_THINK_TAGS = ("<think>", "</think>")
# A thinking model on a hosted provider: together caps a request that names no limit at 2048
# tokens, and Qwen3.5-9B thought for ~7k before a memory read, so it gets room for both (a job's
# own body wins). It also thinks at its own temperature: greedy decoding made its thinking loop
# ("Wait, `flags`:" 17 times) and never answer. Without thinking, neither applies.
THINKING_MAX_TOKENS = 16384
THINKING_TEMPERATURE = 0.6  # Qwen's recommended thinking-mode temperature


class LLMError(Exception):
    pass


@dataclass(frozen=True)
class Endpoint:
    """A resolved model role: where to send the request and how to drive the model."""

    base_url: str
    model: str
    api_key: str | None = None
    reasoning: bool = False  # effective kind: the user's override, else the probe result
    # body: merged verbatim into every request (samplers, id_slot, anything the backend takes)
    # thinking: default | enabled | disabled;  reasoning_effort;  think_tags: [open, close]
    params: dict = field(default_factory=dict)

    @property
    def think_tags(self) -> tuple[str, str]:
        return tuple(self.params.get("think_tags") or DEFAULT_THINK_TAGS)

    @property
    def thinks(self) -> bool:
        """Will this request produce thoughts? Thinking switched on counts even before the
        model's kind is known; switched off always wins."""
        thinking = self.params.get("thinking", "default")
        return thinking == "enabled" or (self.reasoning and thinking != "disabled")


class ThinkSplitter:
    """Routes inline think spans to the thought channel, even when a tag straddles chunks."""

    def __init__(
        self, open_tag: str = DEFAULT_THINK_TAGS[0], close_tag: str = DEFAULT_THINK_TAGS[1]
    ):
        self._tags = (open_tag, close_tag)
        self._thinking = False
        self._held = ""

    def feed(self, chunk: str) -> list[Event]:
        out: list[Event] = []
        buf, self._held = self._held + chunk, ""
        while buf:
            tag = self._tags[self._thinking]
            kind = "thought" if self._thinking else "token"
            at = buf.find(tag)
            if at >= 0:
                if at:
                    out.append((kind, buf[:at]))
                buf = buf[at + len(tag) :]
                self._thinking = not self._thinking
                continue
            # hold back a tail that could still grow into the tag
            sizes = range(min(len(tag) - 1, len(buf)), 0, -1)
            keep = next((n for n in sizes if tag.startswith(buf[-n:])), 0)
            if len(buf) > keep:
                out.append((kind, buf[: len(buf) - keep]))
            self._held = buf[len(buf) - keep :] if keep else ""
            break
        return out

    def flush(self) -> list[Event]:
        held, self._held = self._held, ""
        return [("thought" if self._thinking else "token", held)] if held else []


def _first_json_object(text: str, think_tags: tuple[str, str]) -> dict:
    open_tag, close_tag = map(re.escape, think_tags)
    text = re.sub(f"{open_tag}.*?{close_tag}", "", text, flags=re.DOTALL)
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text, match.start())
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("no JSON object in the output")


class LLM:
    def __init__(self, transport: httpx2.AsyncBaseTransport | None = None):
        # local prefill can be slow, so reads wait long; connects fail fast
        timeout = httpx2.Timeout(10.0, read=600.0)
        self._client = httpx2.AsyncClient(transport=transport, timeout=timeout)
        self._rejected: set[tuple[str, str, str]] = set()  # response_format types a backend refused

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _headers(api_key: str | None) -> dict:
        return {"Authorization": f"Bearer {api_key}"} if api_key else {}

    @staticmethod
    def _body(ep: Endpoint, messages: list[dict], **extra) -> dict:
        room = {"max_tokens": THINKING_MAX_TOKENS} if ep.thinks else {}
        body = {"model": ep.model, "messages": messages, **room, **extra}
        if (thinking := ep.params.get("thinking", "default")) != "default":
            body["chat_template_kwargs"] = {"enable_thinking": thinking == "enabled"}
        if effort := ep.params.get("reasoning_effort"):
            body["reasoning_effort"] = effort
        body.update(ep.params.get("body", {}))  # the user's raw JSON wins, verbatim
        return body

    async def _send(self, method: str, url: str, api_key: str | None, body: dict | None = None):
        try:
            r = await self._client.request(method, url, json=body, headers=self._headers(api_key))
        except httpx2.TransportError as e:
            raise LLMError(f"cannot reach {url}: {e}") from e
        return r

    @staticmethod
    def _check(r: httpx2.Response) -> None:
        if r.status_code >= 400:
            raise LLMError(f"{r.request.url} answered {r.status_code}: {r.text[:500]}")

    async def chat_stream(
        self, ep: Endpoint, messages: list[dict], **extra
    ) -> AsyncIterator[Event]:
        """Stream one reply. Closing the generator closes the connection, which stops generation.

        `extra` goes into the request body (e.g. stop=[...]); the role's own body params win.
        """
        url = f"{ep.base_url.rstrip('/')}/chat/completions"
        body = self._body(
            ep, messages, stream=True, stream_options={"include_usage": True}, **extra
        )
        splitter = ThinkSplitter(*ep.think_tags)
        usage = timings = None
        try:
            async with self._client.stream(
                "POST", url, json=body, headers=self._headers(ep.api_key)
            ) as r:
                if r.status_code >= 400:
                    await r.aread()
                    self._check(r)
                async for chunk in self._chunks(r, url):
                    usage = chunk.get("usage") or usage
                    timings = chunk.get("timings") or timings  # llama.cpp: cache hits live here
                    for choice in chunk.get("choices") or []:
                        delta = choice.get("delta") or {}
                        if thought := delta.get("reasoning_content") or delta.get("reasoning"):
                            yield ("thought", thought)
                        if content := delta.get("content"):
                            for event in splitter.feed(content):
                                yield event
        except httpx2.TransportError as e:
            raise LLMError(f"cannot reach {url}: {e}") from e
        for event in splitter.flush():
            yield event
        yield ("done", {"usage": usage, **({"timings": timings} if timings else {})})

    @staticmethod
    async def _chunks(r: httpx2.Response, url: str) -> AsyncIterator[dict]:
        """The JSON chunks of a server-sent event stream, until [DONE]."""
        async for line in r.aiter_lines():
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                return
            chunk = json.loads(data)
            if error := chunk.get("error"):
                raise LLMError(f"{url} failed mid-stream: {error.get('message', error)}")
            yield chunk

    async def _complete(
        self, ep: Endpoint, messages: list[dict], formats: list[dict | None]
    ) -> str:
        """One completion, stepping down the response_format ladder on refusal. Streamed, so a
        model that thinks for minutes never looks idle to a gateway (the HF router gives up on
        a request that runs past 120 s without streaming)."""
        url = f"{ep.base_url.rstrip('/')}/chat/completions"
        for fmt in formats:
            key = (ep.base_url, ep.model, fmt["type"] if fmt else "")
            if key in self._rejected:
                continue
            body = self._body(ep, messages, stream=True)
            # JSON tasks are deterministic, whatever the role's samplers say; thinking can't be
            body["temperature"] = THINKING_TEMPERATURE if ep.thinks else 0
            if fmt:
                body["response_format"] = fmt
            text, finish = [], None
            try:
                async with self._client.stream(
                    "POST", url, json=body, headers=self._headers(ep.api_key)
                ) as r:
                    if fmt and r.status_code in (400, 422):
                        self._rejected.add(key)  # this backend cannot do that format; stop asking
                        continue
                    if r.status_code >= 400:
                        await r.aread()
                        self._check(r)
                    async for chunk in self._chunks(r, url):
                        for choice in chunk.get("choices") or []:
                            text.append((choice.get("delta") or {}).get("content") or "")
                            finish = choice.get("finish_reason") or finish
            except httpx2.TransportError as e:
                raise LLMError(f"cannot reach {url}: {e}") from e
            if finish == "length":  # cut off: asking again pays again
                raise LLMError(
                    f"the model ran out of room ({body.get('max_tokens')} tokens) before it "
                    "finished answering"
                )
            return "".join(text)
        raise LLMError(f"{url} rejected every request form")  # unreachable: None is never skipped

    async def complete_json[T](
        self,
        ep: Endpoint,
        messages: list[dict],
        schema: dict,
        parse: Callable[[dict], T],
        name: str = "result",
    ) -> T:
        """Get one validated JSON object. `parse` validates and may raise ValueError."""
        strict = {
            "type": "json_schema",
            "json_schema": {"name": name, "schema": schema, "strict": True},
        }
        # grammar-constrained decoding fights think blocks, so a model that thinks starts lower
        formats = ([] if ep.thinks else [strict]) + [{"type": "json_object"}, None]
        error: Exception | None = None
        for _ in range(2):
            text = await self._complete(ep, messages, formats)
            try:
                return parse(_first_json_object(text, ep.think_tags))
            except ValueError as e:  # includes pydantic.ValidationError
                error = e
                fix = f"That output was invalid: {e}\nReply again with only the corrected JSON."
                messages = [
                    *messages,
                    {"role": "assistant", "content": text},
                    {"role": "user", "content": fix},
                ]
        raise LLMError(f"invalid JSON output after one retry: {error}")

    async def list_models(self, base_url: str, api_key: str | None) -> list[str]:
        r = await self._send("GET", f"{base_url.rstrip('/')}/models", api_key)
        self._check(r)
        return [m["id"] for m in r.json().get("data", [])]

    async def embed(self, ep: Endpoint, texts: list[str]) -> list[list[float]]:
        body = {"model": ep.model, "input": texts}
        r = await self._send("POST", f"{ep.base_url.rstrip('/')}/embeddings", ep.api_key, body)
        self._check(r)
        return [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]
