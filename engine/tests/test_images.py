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
        if callable(reply):
            reply = reply(request)
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


# --- the app's door: POST /library/{id}/draw ------------------------------------------------


def drawing_app(conn, backend, fake: Fake, base_url=f"{images.ROUTER}/v1"):
    from fastapi.testclient import TestClient

    from kataki.server import create_app

    app = create_app(
        conn, "t", llm=backend.llm, worker_delay=60, image_transport=httpx2.MockTransport(fake)
    )
    client = TestClient(app, headers={"Authorization": "Bearer t"})
    hf = client.post(
        "/providers", json={"name": "HuggingFace", "base_url": base_url, "api_key": "hf_k"}
    )
    client.put("/roles/image", json={"provider_id": hf.json()["id"], "model": "org/model"})
    return client


def ws_draw(reply):
    ws = f"{images.ROUTER}/wavespeed"
    return Fake(
        {
            **hub(),
            f"{ws}/api/v3/ws/model": [
                {"data": {"urls": {"get": "https://x/api/v3/predictions/9/result"}}}
            ],
            f"{ws}/api/v3/predictions/9/result": [reply],
            "https://cdn.example/": [httpx2.Response(200, content=PNG)],
        }
    )


def test_drawing_a_place_keeps_the_picture_as_its_image(conn, backend):
    fake = ws_draw({"data": {"status": "completed", "outputs": ["https://cdn.example/9.png"]}})
    api = drawing_app(conn, backend, fake)
    gull = api.post(
        "/library",
        json={
            "kind": "place",
            "name": "The Gull",
            "description": "A harbour tavern.",
            "data": {"palette": {"ink": "#fff"}},
        },
    ).json()
    drawn = api.post(f"/library/{gull['id']}/draw", json={})
    assert drawn.status_code == 200
    data = drawn.json()["data"]
    assert data["palette"] == {"ink": "#fff"}  # the rest of the item's data is kept
    assert api.get(f"/media/{data['image']}").content == PNG
    prompt = fake.body(1)["prompt"]
    assert "An empty interior, seen from inside. A harbour tavern." in prompt
    assert "Gull" not in prompt  # a place called "The Gull" would come with a gull
    assert data["history"] == []  # nothing replaced yet
    assert fake.requests[1].headers["authorization"] == "Bearer hf_k"

    again = api.post(f"/library/{gull['id']}/draw", json={}).json()["data"]
    assert again["image"] == data["image"] and again["history"] == []  # same bytes, same picture


def test_the_suv_is_drawn_from_inside_and_no_era_is_imposed():
    # "the inside of a black SUV" came back as a beaten-up car in a desert, under a prompt
    # that began "Medieval fantasy concept art" and called it a deserted outdoor place
    prompt = images.place_prompt(
        {"name": "The Car", "description": "the inside of a black SUV, tinted windows."}
    )
    assert prompt.startswith("Realistic painterly environment art")
    assert "An empty interior, seen from inside. the inside of a black SUV" in prompt
    assert "medieval" not in prompt.lower() and "deserted" not in prompt


def test_a_redraw_keeps_the_old_picture_and_its_faces_to_go_back_to():
    data = {"portrait": "a.png", "packs": {"a.png": {"from": "a.png", "sprites": {}}, "z.png": {}}}
    now = images.with_picture(data, "portrait", "b.png")
    assert now["portrait"] == "b.png" and now["history"] == ["a.png"]
    assert set(now["packs"]) == {"a.png"}  # a pack of a picture no longer kept is let go
    back = images.with_picture(now, "portrait", "a.png")
    assert back["history"] == ["b.png"]  # going back keeps the newer one too


def test_a_refused_place_says_why_and_which_provider_to_try(conn, backend):
    fake = ws_draw({"data": {"status": "failed", "error": "content policy violation"}})
    api = drawing_app(conn, backend, fake)
    gull = api.post("/library", json={"kind": "place", "name": "The Gull"}).json()
    r = api.post(f"/library/{gull['id']}/draw", json={})
    assert r.status_code == 502
    assert r.json()["detail"] == {
        "message": "content policy violation",
        "refused": True,
        "alt": "fal-ai",
    }
    assert "image" not in api.get(f"/library/{gull['id']}").json()["data"]


def test_drawing_needs_a_huggingface_image_job_and_something_drawable(conn, backend):
    fake = Fake({})
    api = drawing_app(conn, backend, fake, base_url="http://localhost:8080/v1")
    gull = api.post("/library", json={"kind": "place", "name": "The Gull"}).json()
    assert api.post(f"/library/{gull['id']}/draw", json={}).status_code == 409
    plot = api.post("/library", json={"kind": "scenario", "name": "The Ledger"}).json()
    assert api.post(f"/library/{plot['id']}/draw", json={}).status_code == 422
    assert fake.requests == []  # nothing was spent


def test_a_place_outdoors_is_drawn_deserted_not_as_a_room():
    prompt = images.place_prompt(
        {"name": "The Lighthouse", "description": "A lighthouse on a windy headland."}
    )
    assert "A deserted, unoccupied place. A lighthouse on a windy headland." in prompt
    assert "room" not in prompt and "The Lighthouse" not in prompt
    assert "A deserted" in images.place_prompt({"name": "Harbour Market", "description": ""})


# --- a character's look ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "words",
    [
        "a 16-year-old runaway",
        "a teenager with a grudge",
        "aged 12, small for it",
        "a little girl",
        "She is 15 years old.",
        "a child of the docks",
    ],
)
def test_a_character_who_sounds_underage_is_never_drawn(words):
    assert images.minor({"name": "X", "description": words, "private": ""})


@pytest.mark.parametrize(
    "words",
    ["a 23-year-old courier", "she is 34 years old", "eighteen and fearless", "a kidnapper"],
)
def test_adults_are_drawn(words):
    assert not images.minor({"name": "X", "description": words, "private": None})


def everything_works():
    ws = f"{images.ROUTER}/wavespeed"
    return Fake(
        {
            **hub(),
            f"{ws}/api/v3/ws/model": [
                {"data": {"urls": {"get": "https://x/api/v3/predictions/1/result"}}}
            ],
            f"{ws}/api/v3/predictions/1/result": [
                {"data": {"status": "completed", "outputs": ["https://cdn.example/1.png"]}}
            ],
            "https://cdn.example/": [httpx2.Response(200, content=PNG)],
        }
    )


def mira(api, **data):
    body = {
        "kind": "character",
        "name": "Mira",
        "description": "A courier with a scar.",
        "data": data,
    }
    return api.post("/library", json=body).json()


def test_drawing_a_character_makes_her_portrait(conn, backend):
    fake = everything_works()
    api = drawing_app(conn, backend, fake)
    her = mira(api, pronouns="she")
    drawn = api.post(f"/library/{her['id']}/draw", json={}).json()
    assert api.get(f"/media/{drawn['data']['portrait']}").content == PNG
    assert fake.body(1)["size"] == "768*1024"
    prompt = fake.body(1)["prompt"]
    assert "An adult woman: A courier with a scar." in prompt and "medieval" not in prompt


def test_an_underage_character_is_refused_before_anything_is_spent(conn, backend):
    fake = everything_works()
    api = drawing_app(conn, backend, fake)
    kid = api.post(
        "/library", json={"kind": "character", "name": "Pip", "description": "A 12-year-old thief."}
    ).json()
    r = api.post(f"/library/{kid['id']}/draw", json={})
    assert r.status_code == 422 and "adults" in r.json()["detail"]
    assert fake.requests == []


def test_a_look_is_five_sprites_edited_from_the_portrait_and_cut_out(conn, backend):
    fake = everything_works()
    api = drawing_app(conn, backend, fake)
    sheet = api.post("/media", content=PNG).json()["name"]
    her = mira(api, pronouns="she", portrait=sheet)
    made = api.post(f"/library/{her['id']}/look", json={}).json()
    assert made["failed"] == {}
    pack = made["item"]["data"]["pack"]
    assert pack["from"] == sheet and list(pack["sprites"]) == list(images.EXPRESSIONS)
    posts = [json.loads(r.content) for r in fake.requests if r.method == "POST"]
    edits = [b for b in posts if "prompt" in b]
    assert len(edits) == 5 and len(posts) == 10  # an edit and a cutout each
    assert all(b["images"][0].startswith("data:image/png;base64,") for b in edits)  # from the sheet
    assert "The same adult woman as in the picture" in edits[0]["prompt"]


def test_one_refused_expression_keeps_the_others_and_says_why(conn, backend):
    fake = everything_works()
    ws = f"{images.ROUTER}/wavespeed/api/v3/ws/model"
    ok = fake.routes[ws][0]
    fake.routes[ws] = [
        lambda r: httpx2.Response(400, text="content policy") if b"wary" in r.content else ok
    ]
    api = drawing_app(conn, backend, fake)
    her = mira(api, portrait=api.post("/media", content=PNG).json()["name"])
    made = api.post(f"/library/{her['id']}/look", json={}).json()
    assert set(made["item"]["data"]["pack"]["sprites"]) == {
        "neutral",
        "smiling",
        "surprised",
        "doubtful",
    }
    assert made["failed"]["wary"]["refused"] is True and made["failed"]["wary"]["alt"] == "fal-ai"


def test_redrawing_one_keeps_the_rest_unless_the_portrait_changed(conn, backend):
    fake = everything_works()
    api = drawing_app(conn, backend, fake)
    old = api.post("/media", content=PNG).json()["name"]
    her = mira(
        api, portrait=old, pack={"from": old, "sprites": {"neutral": "n.png", "wary": "w.png"}}
    )
    one = api.post(f"/library/{her['id']}/look", json={"expressions": ["wary"]}).json()["item"]
    assert one["data"]["pack"]["sprites"]["neutral"] == "n.png"
    assert one["data"]["pack"]["sprites"]["wary"] != "w.png"
    new = api.post("/media", content=PNG + b"new").json()["name"]
    api.patch(f"/library/{her['id']}", json={"data": {**one["data"], "portrait": new}})
    fresh = api.post(f"/library/{her['id']}/look", json={"expressions": ["smiling"]}).json()["item"]
    assert fresh["data"]["pack"] == {
        "from": new,
        "sprites": {"smiling": fresh["data"]["pack"]["sprites"]["smiling"]},
    }


def test_a_look_needs_a_portrait_and_a_real_expression(conn, backend):
    fake = everything_works()
    api = drawing_app(conn, backend, fake)
    bare = mira(api)
    assert api.post(f"/library/{bare['id']}/look", json={}).status_code == 422
    her = mira(api, portrait=api.post("/media", content=PNG).json()["name"])
    assert api.post(f"/library/{her['id']}/look", json={"expressions": ["smug"]}).status_code == 422
    assert fake.requests == []


def test_try_on_the_other_provider_goes_there(conn, backend):
    fal = f"{images.ROUTER}/fal-ai"
    fake = Fake(
        {
            **hub(),
            f"{fal}/fal-ai/model?_subdomain=queue": [
                {"request_id": "r", "response_url": "https://q/fal-ai/model/requests/r"}
            ],
            f"{fal}/fal-ai/model/requests/r/status": [{"status": "COMPLETED"}],
            f"{fal}/fal-ai/model/requests/r?": [{"images": [{"url": "https://cdn.example/r.png"}]}],
            "https://cdn.example/": [httpx2.Response(200, content=PNG)],
        }
    )
    api = drawing_app(conn, backend, fake)
    gull = api.post("/library", json={"kind": "place", "name": "The Gull"}).json()
    assert api.post(f"/library/{gull['id']}/draw", json={"provider": "fal-ai"}).status_code == 200
    assert fake.requests[1].url.path == "/fal-ai/fal-ai/model"
    assert fake.body(1)["image_size"] == {"width": 1536, "height": 864}


def test_going_back_to_an_earlier_portrait_brings_its_faces_back(conn, backend):
    api = drawing_app(conn, backend, Fake({}))
    old, new = (api.post("/media", content=PNG + bytes([n])).json()["name"] for n in (1, 2))
    old_pack = {"from": old, "sprites": {"neutral": "n.png"}}
    her = mira(
        api, portrait=new, history=[old], pack={"from": new, "sprites": {}}, packs={old: old_pack}
    )
    back = api.post(f"/library/{her['id']}/picture", json={"name": old}).json()["data"]
    assert back["portrait"] == old and back["history"] == [new] and back["pack"] == old_pack
    assert (
        api.post(f"/library/{her['id']}/picture", json={"name": "stranger.png"}).status_code == 422
    )
