"""One OpenAI-compatible client for every text backend.

Covers llama.cpp server, Ollama, LM Studio, KoboldCpp, vLLM, TabbyAPI, OpenRouter and the
HuggingFace Inference Providers router. Reasoning output never mixes with visible text:
it is yielded on its own `thought` channel whether the backend sends `reasoning_content`
or inline think tags.
"""

import asyncio
import contextlib
import json
import logging
import math
import re
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

import httpx2

from kataki import media

Event = tuple[str, Any]  # ("thought" | "token", text) ... then ("done", {"usage": ...})
DEFAULT_THINK_TAGS = ("<think>", "</think>")
# A thinking model on a hosted provider: together caps a request that names no limit at 2048
# tokens, and Qwen3.5-9B thought for ~7k before a memory read, so it gets room for both (a job's
# own body wins). It also thinks at its own temperature: greedy decoding made its thinking loop
# ("Wait, `flags`:" 17 times) and never answer. Without thinking, neither applies.
THINKING_MAX_TOKENS = 16384
RETRY_AFTER = 2.0  # seconds before asking a busy provider again; doubled each time
BUSY = (429, 502, 503)  # busy or briefly down: nothing was generated, so nothing is billed
TRIES = 3
THINKING_TEMPERATURE = 0.6  # Qwen's recommended thinking-mode temperature
SPELLED_OUT = (
    "Reply with one JSON object that follows this JSON schema exactly, field names and all:\n"
)


# note 15 §5, note 04: min-p plus DRY on every reply; XTC only where no fact has to come out
# right (it removes the likeliest tokens). Breakers keep chat formatting from counting as a loop.
ANTI_SLOP = {  # ponytail: community baselines (llama.cpp, text-generation-webui), untuned here
    "min_p": 0.05,
    "dry_multiplier": 0.8,
    "dry_base": 1.75,
    "dry_allowed_length": 2,
    "dry_sequence_breakers": ["\n", ":", '"', "*"],
}
XTC = {"xtc_probability": 0.5, "xtc_threshold": 0.1}
LOCAL = ("127.0.0.1", "localhost", "::1")


def anti_slop(ep: "Endpoint", xtc: bool = False) -> dict:
    """The anti-slop sampler preset for this endpoint's reply requests (minds spec §8.3 slice
    9), or {}. The role's `samplers` param: "anti-slop" on, "off" off, "auto" (default) on only
    for a model served from this machine (llama.cpp and KoboldCpp take all of it; an online
    provider may refuse keys it does not know)."""
    mode = ep.params.get("samplers", "auto")
    host = urlsplit(ep.base_url).hostname or ""
    if mode == "off" or (mode != "anti-slop" and host not in LOCAL):
        return {}
    return {**ANTI_SLOP, **(XTC if xtc else {})}


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
    role: str = ""  # which job asked (rp, utility, embed…): usage rows and online billing
    story_id: int | None = None  # the story it was for, if any

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
        # called with (endpoint, usage) after every call that reports usage: the desktop
        # records it in usage_log, Kataki online bills it (spec §4)
        self.on_usage: Callable[[Endpoint, dict], None] | None = None

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
    def _guess(messages: list[dict], streamed: int) -> dict:
        """What a call used when the provider never said (stopped, dropped, failed mid-way, or a
        backend that reports nothing): characters / 4 each way (track B2)."""
        sent = sum(len(str(m.get("content") or "")) for m in messages)
        return {
            "prompt_tokens": math.ceil(sent / 4),
            "completion_tokens": math.ceil(streamed / 4),
            "estimated": True,
        }

    def _used(self, ep: Endpoint, usage: dict | None) -> None:
        if usage and self.on_usage:
            try:
                self.on_usage(ep, usage)
            except Exception as e:  # the reply is already generated: never lose it to a meter
                # an online host that must fail closed does so in its own hook (track B3)
                logging.getLogger(__name__).warning("usage not recorded for %s: %s", ep.model, e)

    @staticmethod
    def _check(r: httpx2.Response) -> None:
        if r.status_code >= 400:
            raise LLMError(f"{r.request.url} answered {r.status_code}: {r.text[:500]}")

    async def chat_stream(
        self, ep: Endpoint, messages: list[dict], samplers: dict | None = None, **extra
    ) -> AsyncIterator[Event]:
        """Stream one reply. Closing the generator closes the connection, which stops generation.

        `extra` goes into the request body (e.g. stop=[...]); the role's own body params win.
        `samplers` (anti_slop) go in under both; a backend that refuses them (400/422) is asked
        again at once without them, and never sent them again.
        """
        url = f"{ep.base_url.rstrip('/')}/chat/completions"
        key = (ep.base_url, ep.model, "samplers")
        tries = [samplers, None] if samplers and key not in self._rejected else [None]
        refused = False
        splitter = ThinkSplitter(*ep.think_tags)
        usage = timings = None
        live = metered = False  # a request that got a 2xx is metered once, however it ends
        streamed = 0
        try:
            try:
                for extra_samplers in tries:
                    body = self._body(
                        ep, messages, stream=True, stream_options={"include_usage": True}, **extra
                    )
                    body = {**(extra_samplers or {}), **body}
                    async with self._stream(url, body, ep.api_key) as r:
                        if r.status_code >= 400:
                            await r.aread()
                            if extra_samplers and r.status_code in (400, 422):
                                refused = True  # the samplers, or something else? retry tells
                                continue
                            self._check(r)
                        if refused:  # only without them did it work: it refuses them, stop
                            self._rejected.add(key)
                        live = True
                        async for chunk in self._chunks(r, url):
                            usage = chunk.get("usage") or usage
                            timings = chunk.get("timings") or timings  # llama.cpp: cache hits
                            for choice in chunk.get("choices") or []:
                                delta = choice.get("delta") or {}
                                thought = delta.get("reasoning_content") or delta.get("reasoning")
                                if thought:
                                    streamed += len(thought)
                                    yield ("thought", thought)
                                if content := delta.get("content"):
                                    streamed += len(content)
                                    for event in splitter.feed(content):
                                        yield event
                    break
            except httpx2.TransportError as e:
                raise LLMError(f"cannot reach {url}: {e}") from e
            for event in splitter.flush():
                yield event
            metered = True
            self._used(ep, usage or self._guess(messages, streamed))
            yield ("done", {"usage": usage, **({"timings": timings} if timings else {})})
        finally:  # stopped, dropped for a retake, or failed mid-way: the final usage never came
            if live and not metered:
                self._used(ep, usage or self._guess(messages, streamed))

    @contextlib.asynccontextmanager
    async def _stream(self, url: str, body: dict, api_key: str | None):
        """A streamed POST. A provider that is busy or briefly unavailable (429/502/503: nothing
        was generated, so nothing is billed) is asked again after a moment, twice at most."""
        for attempt in range(TRIES):
            async with self._client.stream(
                "POST", url, json=body, headers=self._headers(api_key)
            ) as r:
                if attempt == TRIES - 1 or r.status_code not in BUSY:
                    yield r
                    return
                await r.aread()
            await asyncio.sleep(RETRY_AFTER * 2**attempt)

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
        self, ep: Endpoint, messages: list[dict], formats: list[dict | None], schema: dict
    ) -> str:
        """One completion, stepping down the response_format ladder on refusal. Streamed, so a
        model that thinks for minutes never looks idle to a gateway (the HF router gives up on
        a request that runs past 120 s without streaming)."""
        url = f"{ep.base_url.rstrip('/')}/chat/completions"
        # below the strict format the field names reach the model only as words: a thinking
        # Qwen3.8-27B left without them wrote "type" for "kind", and every item was dropped
        told = [*messages, {"role": "user", "content": SPELLED_OUT + json.dumps(schema)}]
        for fmt in formats:
            key = (ep.base_url, ep.model, fmt["type"] if fmt else "")
            if key in self._rejected:
                continue
            strict = bool(fmt) and fmt["type"] == "json_schema"
            body = self._body(
                ep,
                messages if strict else told,
                stream=True,
                stream_options={"include_usage": True},
            )
            # JSON tasks are deterministic, whatever the role's samplers say; thinking can't be
            body["temperature"] = THINKING_TEMPERATURE if ep.thinks else 0
            if fmt:
                body["response_format"] = fmt
            text, finish, usage, live = [], None, None, False
            try:
                async with self._stream(url, body, ep.api_key) as r:
                    if fmt and r.status_code in (400, 422):
                        self._rejected.add(key)  # this backend cannot do that format; stop asking
                        continue
                    if r.status_code >= 400:
                        await r.aread()
                        self._check(r)
                    live = True
                    async for chunk in self._chunks(r, url):
                        usage = chunk.get("usage") or usage
                        for choice in chunk.get("choices") or []:
                            text.append((choice.get("delta") or {}).get("content") or "")
                            finish = choice.get("finish_reason") or finish
            except httpx2.TransportError as e:
                raise LLMError(f"cannot reach {url}: {e}") from e
            finally:  # a request that ran is metered once: finished, cut off, failed or cancelled
                if live:
                    self._used(ep, usage or self._guess(body["messages"], len("".join(text))))
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
            text = await self._complete(ep, messages, formats, schema)
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

    async def speech(
        self,
        ep: Endpoint,
        text: str,
        voice: str,
        speed: float = 1.0,
        fmt: str = "mp3",
        instructions: str | None = None,
    ) -> bytes:
        """Speak `text` (minds slice 10): OpenAI's `POST /audio/speech`, which OpenAI, Together,
        Kokoro-FastAPI and Orpheus-FastAPI all take. Not metered here: the caller meters it
        (`meter`, as characters: speech is priced per character) once the audio is kept, so a
        render lost before it is saved is not billed and then billed again. No retry: it costs."""
        body = {"model": ep.model, "input": text, "voice": voice, "speed": speed}
        body["response_format"] = fmt
        if instructions:
            body["instructions"] = instructions
        body.update(ep.params.get("body", {}))  # the user's raw JSON wins, verbatim
        r = await self._send("POST", f"{ep.base_url.rstrip('/')}/audio/speech", ep.api_key, body)
        self._check(r)
        if media.sniff_audio(r.content) is None:
            raise LLMError(f"{ep.base_url} sent no audio: {r.content[:120]!r}")
        return r.content

    def meter(self, ep: Endpoint, usage: dict) -> None:
        """Record a call's usage the caller measured itself (speech: characters)."""
        self._used(ep, usage)

    async def list_models(self, base_url: str, api_key: str | None) -> list[str]:
        r = await self._send("GET", f"{base_url.rstrip('/')}/models", api_key)
        self._check(r)
        return [m["id"] for m in r.json().get("data", [])]

    async def embed(self, ep: Endpoint, texts: list[str]) -> list[list[float]]:
        body = {"model": ep.model, "input": texts}
        r = await self._send("POST", f"{ep.base_url.rstrip('/')}/embeddings", ep.api_key, body)
        self._check(r)
        said = r.json().get("usage")
        self._used(ep, said or self._guess([{"content": t} for t in texts], 0))
        return [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]
