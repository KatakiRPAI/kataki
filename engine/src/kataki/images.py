"""Pictures from HuggingFace Inference Providers, over plain HTTPS (M3 spec §7).

Three calls, bytes in and bytes out: `draw` (words -> picture), `edit` (a sheet + words ->
picture) and `cutout` (picture -> transparent PNG). The Hub says which providers serve a model
and under which id; each provider has its own request shape and its own way of making you
wait, and both go through the HF router with the user's HF key. Nothing here retries: every
call costs money, so a failure goes back to whoever clicked.
"""

import asyncio
import base64
import re
import time
from urllib.parse import urlparse

import httpx2

from kataki import media

ROUTER = "https://router.huggingface.co"
HUB = "https://huggingface.co/api/models"
PROVIDERS = ("wavespeed", "fal-ai")  # the ones this file speaks; the first live one is used
DEADLINE = 240.0  # seconds a picture may take before we give up waiting (it may still be billed)
# how providers word "we won't draw that"
REFUSAL = re.compile(r"nsfw|safety|content.?polic|moderat|inappropriate|not allowed", re.I)

_mappings: dict[str, dict[str, str]] = {}  # model -> {provider: provider's own id}, per process


class ImageError(Exception):
    def __init__(self, message: str, refused: bool = False, alt: str | None = None):
        super().__init__(message)
        self.refused = refused  # the provider declined the content, as opposed to failing
        self.alt = alt  # another provider that serves this model, to offer as a retry


def data_url(data: bytes) -> str:
    mime = media.TYPES.get(media.sniff(data) or "", "image/png")
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


class Images:
    def __init__(
        self, api_key: str, transport: httpx2.AsyncBaseTransport | None = None, poll: float = 0.5
    ):
        self._key = api_key
        self._poll = poll
        self._client = httpx2.AsyncClient(
            transport=transport, timeout=httpx2.Timeout(10.0, read=120.0)
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, url: str, body: dict | None = None, auth: bool = True):
        # the key goes to the router only, never to the CDN a finished picture is served from
        headers = {"Authorization": f"Bearer {self._key}"} if auth else {}
        try:
            r = await self._client.request(method, url, json=body, headers=headers)
        except httpx2.TransportError as e:
            raise ImageError(f"cannot reach {urlparse(url).netloc}: {e}") from e
        if r.status_code >= 400:
            raise ImageError(
                f"{r.status_code}: {r.text[:300]}", refused=bool(REFUSAL.search(r.text))
            )
        return r

    async def _route(self, model: str, provider: str | None) -> tuple[str, str, str | None]:
        """(provider, the provider's id for the model, another provider that could do it)."""
        if model not in _mappings:
            r = await self._request(
                "GET", f"{HUB}/{model}?expand[]=inferenceProviderMapping", auth=False
            )
            found = r.json().get("inferenceProviderMapping") or {}
            _mappings[model] = {
                p: m["providerId"]
                for p, m in found.items()
                if p in PROVIDERS and m.get("status") == "live"
            }
        live = [p for p in PROVIDERS if p in _mappings[model]]
        if provider not in live:
            if provider or not live:
                raise ImageError(
                    f"{model} is not served by {provider or 'wavespeed or fal'} on HuggingFace."
                )
            provider = live[0]
        alt = next((p for p in live if p != provider), None)
        return provider, _mappings[model][provider], alt

    async def _run(self, model: str, provider: str | None, wavespeed: dict, fal: dict) -> bytes:
        provider, pid, alt = await self._route(model, provider)
        try:
            if provider == "wavespeed":
                return await self._wavespeed(pid, wavespeed)
            return await self._fal(pid, fal)
        except ImageError as e:
            e.alt = alt
            raise

    async def _wait(self, started: float) -> None:
        if time.monotonic() - started > DEADLINE:
            raise ImageError(f"no picture after {DEADLINE:.0f} s; gave up waiting")
        await asyncio.sleep(self._poll)

    async def _wavespeed(self, pid: str, body: dict) -> bytes:
        base = f"{ROUTER}/wavespeed"
        r = await self._request("POST", f"{base}/api/v3/{pid}", body)
        result = base + urlparse(r.json()["data"]["urls"]["get"]).path
        started = time.monotonic()
        while True:
            task = (await self._request("GET", result)).json().get("data", {})
            if task.get("status") == "completed":
                if any(task.get("has_nsfw_contents") or []):
                    raise ImageError("the provider flagged this picture as NSFW", refused=True)
                return (await self._request("GET", task["outputs"][0], auth=False)).content
            if task.get("status") == "failed":
                error = task.get("error") or "the provider could not make this picture"
                raise ImageError(error, refused=bool(REFUSAL.search(error)))
            await self._wait(started)

    async def _fal(self, pid: str, body: dict) -> bytes:
        base, queue = f"{ROUTER}/fal-ai", "?_subdomain=queue"
        r = (await self._request("POST", f"{base}/{pid}{queue}", body)).json()
        path = urlparse(r["response_url"]).path
        status, started = f"{base}{path}/status{queue}", time.monotonic()
        while (await self._request("GET", status)).json().get("status") != "COMPLETED":
            await self._wait(started)
        out = (await self._request("GET", f"{base}{path}{queue}")).json()
        if any(out.get("has_nsfw_concepts") or []):
            raise ImageError("the provider flagged this picture as NSFW", refused=True)
        url = (out.get("images") or [out.get("image") or {}])[0].get("url")
        if not url:
            raise ImageError(f"the provider sent no picture: {str(out)[:300]}")
        if url.startswith("data:"):
            return base64.b64decode(url.split(",", 1)[1])
        return (await self._request("GET", url, auth=False)).content

    async def draw(
        self, model: str, prompt: str, width: int, height: int, provider: str | None = None
    ) -> bytes:
        return await self._run(
            model,
            provider,
            wavespeed={"prompt": prompt, "size": f"{width}*{height}"},
            fal={"prompt": prompt, "image_size": {"width": width, "height": height}},
        )

    async def edit(
        self, model: str, image: bytes, prompt: str, provider: str | None = None
    ) -> bytes:
        url = data_url(image)
        return await self._run(
            model,
            provider,
            wavespeed={"prompt": prompt, "images": [url]},
            fal={"prompt": prompt, "image_url": url, "image_urls": [url]},
        )

    async def cutout(self, model: str, image: bytes, provider: str | None = None) -> bytes:
        url = data_url(image)
        return await self._run(
            model, provider, wavespeed={"image": url}, fal={"image_url": url, "sync_mode": True}
        )
