import base64
import json

import httpx2
import pytest

from kataki import images
from kataki.images import ImageError, Images

pytestmark = pytest.mark.anyio

PNG = b"\x89PNG\r\n\x1a\n" + b"pixels"
MAPPING = {
    "inferenceProviderMapping": {
        "wavespeed": {"providerId": "ws/model", "status": "live"},
        "fal-ai": {"providerId": "fal-ai/model", "status": "live"},
        "together": {"providerId": "t/model", "status": "live"},  # a provider we don't speak
    }
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def fresh_mappings():
    images._mappings.clear()


class Fake:
    """A scripted Hub + router + CDN: `routes` maps a URL prefix to replies, used in order."""

    def __init__(self, routes: dict[str, list]):
        self.routes = routes
        self.requests: list[httpx2.Request] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        url = str(request.url)
        prefix = max((p for p in self.routes if url.startswith(p)), key=len)
        reply = (
            self.routes[prefix].pop(0) if len(self.routes[prefix]) > 1 else self.routes[prefix][0]
        )
        return reply if isinstance(reply, httpx2.Response) else httpx2.Response(200, json=reply)

    @property
    def client(self) -> Images:
        return Images("hf_key", transport=httpx2.MockTransport(self), poll=0)

    def body(self, i: int) -> dict:
        return json.loads(self.requests[i].content)


def hub(mapping=MAPPING):
    return {f"{images.HUB}/": [mapping]}


async def test_wavespeed_draw_polls_then_fetches_the_picture_without_the_key():
    ws = f"{images.ROUTER}/wavespeed"
    fake = Fake(
        {
            **hub(),
            f"{ws}/api/v3/ws/model": [
                {"data": {"urls": {"get": "https://api.wavespeed.ai/api/v3/predictions/7/result"}}}
            ],
            f"{ws}/api/v3/predictions/7/result": [
                {"data": {"status": "processing"}},
                {"data": {"status": "completed", "outputs": ["https://cdn.example/7.png"]}},
            ],
            "https://cdn.example/": [httpx2.Response(200, content=PNG)],
        }
    )
    assert await fake.client.draw("org/model", "a tavern", 1536, 864) == PNG
    assert fake.body(1) == {"prompt": "a tavern", "size": "1536*864"}
    assert [r.url.path for r in fake.requests[2:4]] == [
        "/wavespeed/api/v3/predictions/7/result"
    ] * 2
    assert fake.requests[1].headers["authorization"] == "Bearer hf_key"
    assert "authorization" not in fake.requests[-1].headers  # the CDN never sees the key
    assert "authorization" not in fake.requests[0].headers  # nor does the public Hub lookup


async def test_fal_edit_queues_and_reads_a_data_url_back():
    fal = f"{images.ROUTER}/fal-ai"
    out = "data:image/png;base64," + base64.b64encode(PNG).decode()
    fake = Fake(
        {
            **hub(),
            f"{fal}/fal-ai/model?_subdomain=queue": [
                {
                    "request_id": "r1",
                    "response_url": "https://queue.fal.run/fal-ai/model/requests/r1",
                }
            ],
            f"{fal}/fal-ai/model/requests/r1/status": [
                {"status": "IN_QUEUE"},
                {"status": "COMPLETED"},
            ],
            f"{fal}/fal-ai/model/requests/r1?": [{"images": [{"url": out}]}],
        }
    )
    assert await fake.client.edit("org/model", PNG, "smiling", provider="fal-ai") == PNG
    sent = fake.body(1)
    assert sent["prompt"] == "smiling"
    assert sent["image_urls"] == [sent["image_url"]] and sent["image_url"].startswith(
        "data:image/png;base64,"
    )


async def test_a_refusal_says_so_and_offers_the_other_provider():
    ws = f"{images.ROUTER}/wavespeed"
    fake = Fake(
        {
            **hub(),
            f"{ws}/api/v3/ws/model": [
                {"data": {"urls": {"get": "https://x/api/v3/predictions/8/result"}}}
            ],
            f"{ws}/api/v3/predictions/8/result": [
                {"data": {"status": "failed", "error": "NSFW content detected"}}
            ],
        }
    )
    with pytest.raises(ImageError) as e:
        await fake.client.draw("org/model", "x", 512, 512)
    assert e.value.refused and e.value.alt == "fal-ai"


async def test_fal_flagging_nsfw_is_a_refusal_not_a_black_picture():
    fal = f"{images.ROUTER}/fal-ai"
    fake = Fake(
        {
            **hub(),
            f"{fal}/fal-ai/model?_subdomain=queue": [
                {"request_id": "r", "response_url": "https://q/fal-ai/model/requests/r"}
            ],
            f"{fal}/fal-ai/model/requests/r/status": [{"status": "COMPLETED"}],
            f"{fal}/fal-ai/model/requests/r?": [
                {"images": [{"url": "https://cdn/black.png"}], "has_nsfw_concepts": [True]}
            ],
        }
    )
    with pytest.raises(ImageError) as e:
        await fake.client.cutout("org/model", PNG, provider="fal-ai")
    assert e.value.refused and e.value.alt == "wavespeed"


async def test_a_plain_failure_is_not_a_refusal():
    fake = Fake(
        {**hub(), f"{images.ROUTER}/wavespeed/": [httpx2.Response(402, text="out of credits")]}
    )
    with pytest.raises(ImageError) as e:
        await fake.client.draw("org/model", "x", 512, 512)
    assert not e.value.refused and "402" in str(e.value)


async def test_a_model_no_provider_we_speak_serves_is_an_error_before_any_spend():
    fake = Fake(
        hub(
            {
                "inferenceProviderMapping": {
                    "together": {"providerId": "t", "status": "live"},
                    "fal-ai": {"providerId": "f", "status": "error"},
                }
            }
        )
    )
    with pytest.raises(ImageError, match="not served"):
        await fake.client.draw("org/model", "x", 512, 512)
    assert len(fake.requests) == 1  # only the Hub lookup
