"""The HTTP API the desktop app uses, end to end against a scripted model."""

import json

import keyring
import pytest
from fastapi.testclient import TestClient

from kataki.server import create_app

AUTH = {"Authorization": "Bearer t"}


@pytest.fixture
def api(conn, backend):
    client = TestClient(create_app(conn, "t", llm=backend.llm, worker_delay=60), headers=AUTH)
    with client:
        yield client


def events(response):
    """Parse a server-sent event stream into [(event, data)]."""
    out = []
    for block in response.text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        out.append((lines["event"], json.loads(lines["data"])))
    return out


@pytest.fixture
def story(api):
    provider = api.post("/providers", json={"name": "local", "base_url": "http://fake/v1/"}).json()
    api.put("/roles/rp", json={"provider_id": provider["id"], "model": "rp-model"})
    ids = {
        name: api.post("/library", json={"kind": "character", "name": name}).json()["id"]
        for name in ("Mira", "Tobin", "Aren")
    }
    gull = api.post("/library", json={"kind": "place", "name": "The Gull"}).json()["id"]
    created = api.post(
        "/stories",
        json={
            "title": "Low Tide",
            "character_ids": [ids["Mira"], ids["Tobin"]],
            "place_id": gull,
            "persona_id": ids["Aren"],
        },
    )
    assert created.status_code == 201
    return created.json()["id"]


def cast(api, story):
    return {e["name"]: e for e in api.get(f"/stories/{story}/cast").json()["entities"]}


# --- providers, keys, roles ----------------------------------------------------------------


def test_api_keys_go_to_the_keychain_and_never_come_back(api):
    created = api.post(
        "/providers", json={"name": "OpenRouter", "base_url": "https://x/v1", "api_key": "sk-1"}
    ).json()
    assert created == {
        "id": created["id"],
        "name": "OpenRouter",
        "base_url": "https://x/v1",
        "has_key": True,
    }
    assert keyring.get_password("kataki", "OpenRouter") == "sk-1"
    assert "sk-1" not in api.get("/providers").text

    api.patch(f"/providers/{created['id']}", json={"name": "OR"})
    assert keyring.get_password("kataki", "OR") == "sk-1"  # the key follows a rename
    api.delete(f"/providers/{created['id']}")
    assert keyring.get_password("kataki", "OR") is None


def test_a_duplicate_provider_name_is_refused(api):
    api.post("/providers", json={"name": "local", "base_url": "http://a/v1"})
    assert (
        api.post("/providers", json={"name": "local", "base_url": "http://b/v1"}).status_code == 409
    )


def test_the_models_page_shows_where_every_role_gets_its_model(api, story):
    table = {r["role"]: r for r in api.get("/roles").json()}
    assert table["rp"]["effective_model"] == "rp-model"
    assert table["utility"]["inherited_from"] == "rp"


def test_probing_a_role_records_what_kind_of_model_it_is(api, story, backend):
    backend.say({"reasoning_content": "hmm", "content": "ok"})
    assert api.post("/roles/reasoning/probe").json() == {
        "role": "reasoning",
        "detected_kind": "reasoning",
    }
    table = {r["role"]: r for r in api.get("/roles").json()}
    assert table["rp"]["detected_kind"] == "reasoning"  # stored on the role that owns the model
    assert table["reasoning"]["effective_kind"] == "reasoning"


def test_listing_a_providers_models(api, backend):
    import httpx2

    backend.say(httpx2.Response(200, json={"data": [{"id": "a"}, {"id": "b"}]}))
    pid = api.post("/providers", json={"name": "local", "base_url": "http://fake/v1"}).json()["id"]
    assert api.get(f"/providers/{pid}/models").json() == {"models": ["a", "b"]}


def test_every_route_needs_the_token(conn, backend):
    with TestClient(create_app(conn, "t", llm=backend.llm)) as bare:
        assert bare.get("/stories").status_code == 401


# --- library ---------------------------------------------------------------------------------


def test_library_items_round_trip(api):
    item = api.post(
        "/library",
        json={
            "kind": "character",
            "name": "Mira",
            "data": {"aliases": ["the courier"]},
            "tags": ["guild"],
        },
    ).json()
    assert (
        api.patch(f"/library/{item['id']}", json={"description": "A courier."}).json()[
            "description"
        ]
        == "A courier."
    )
    assert [i["name"] for i in api.get("/library?tag=guild").json()] == ["Mira"]
    assert api.delete(f"/library/{item['id']}").status_code == 204
    assert api.get(f"/library/{item['id']}").status_code == 404


def test_deleting_a_character_a_story_uses_leaves_the_story_its_copy(api, story, conn):
    mira = next(i for i in api.get("/library").json() if i["name"] == "Mira")
    assert api.delete(f"/library/{mira['id']}").status_code == 204
    assert api.get(f"/library/{mira['id']}").status_code == 404
    assert "Mira" in cast(api, story)
    row = conn.execute("SELECT lib_item_id FROM entities WHERE name='Mira'").fetchone()
    assert row["lib_item_id"] is None


def test_a_story_cannot_be_made_from_missing_items(api):
    assert api.post("/stories", json={"title": "x", "character_ids": [999]}).status_code == 422


# --- playing ---------------------------------------------------------------------------------


def test_a_turn_streams_and_the_story_shows_it(api, story, backend):
    backend.say("The tide turned early.")
    streamed = events(api.post(f"/stories/{story}/turn", json={"text": "Evening, Mira."}))
    assert streamed[0][0] == "meta" and streamed[-1][0] == "done"
    assert "".join(d for e, d in streamed if e == "token") == "The tide turned early."

    shown = api.get(f"/stories/{story}/messages").json()
    assert [(m["speaker"], m["text"]) for m in shown] == [
        ("Aren", "Evening, Mira."),
        ("Mira", "The tide turned early."),
    ]
    assert shown[-1]["swipe"] == [1, 1] and shown[-1]["clock"] == "Day 1, 08:04"


def test_regenerate_then_swipe_back_and_forth(api, story, backend):
    backend.say("First.", "Second.")
    api.post(f"/stories/{story}/turn", json={"text": "Mira?"})
    api.post(f"/stories/{story}/regenerate")
    last = api.get(f"/stories/{story}/messages").json()[-1]
    assert (last["text"], last["swipe"]) == ("Second.", [2, 2])

    back = api.post(f"/stories/{story}/swipe", json={"message_id": last["id"], "step": -1}).json()
    assert (back[-1]["text"], back[-1]["swipe"]) == ("First.", [1, 2])


def test_the_user_can_pick_who_speaks(api, story, backend):
    backend.say("Tobin grunts.")
    tobin = cast(api, story)["Tobin"]["id"]
    api.post(f"/stories/{story}/turn", json={"text": "Anyone?", "speaker": tobin})
    assert api.get(f"/stories/{story}/messages").json()[-1]["speaker"] == "Tobin"


def test_editing_hiding_and_undoing_a_time_skip(api, story, backend):
    backend.say("Welcome back.")
    api.post(f"/stories/{story}/turn", json={"text": "Six years later, Aren returns."})
    user = api.get(f"/stories/{story}/messages").json()[0]
    assert user["skip_minutes"] == 6 * 365 * 1440

    undone = api.patch(f"/messages/{user['id']}", json={"skip_minutes": 0}).json()
    assert undone[0]["skip_minutes"] == 0 and undone[-1]["clock"] == "Day 1, 08:04"
    edited = api.patch(f"/messages/{user['id']}", json={"text": "Aren returns."}).json()
    assert (edited[0]["text"], edited[0]["edited"]) == ("Aren returns.", True)
    assert api.patch(f"/messages/{user['id']}", json={"hidden": True}).json()[0]["hidden"] is True


def test_people_come_and_go_and_scenes_change(api, story):
    tobin = cast(api, story)["Tobin"]["id"]
    after = api.post(
        f"/stories/{story}/presence", json={"entity_id": tobin, "present": False}
    ).json()
    assert {e["name"]: e["present"] for e in after["entities"]}["Tobin"] is False

    gull = cast(api, story)["The Gull"]["id"]
    scene = api.post(
        f"/stories/{story}/scene", json={"present": [tobin], "place_id": gull, "title": "Night"}
    )
    assert scene.status_code == 201
    present = {e["name"] for e in scene.json()["entities"] if e["present"]}
    assert present == {"Tobin"}
    assert api.get(f"/stories/{story}/messages").json()[-1]["text"] == "— Night —"


def test_a_library_character_joins_mid_story_and_a_scene_moves_to_a_new_place(api, story):
    dara = api.post("/library", json={"kind": "character", "name": "Dara"}).json()["id"]
    docks = api.post("/library", json={"kind": "place", "name": "The Docks"}).json()["id"]
    joined = {
        e["name"]: e
        for e in api.post(f"/stories/{story}/cast", json={"library_id": dara}).json()["entities"]
    }
    assert joined["Dara"]["present"] and joined["Dara"]["is_ai"]
    again = api.post(f"/stories/{story}/cast", json={"library_id": dara}).json()["entities"]
    assert [e["name"] for e in again].count("Dara") == 1  # joining twice is still one Dara

    scene = api.post(
        f"/stories/{story}/scene",
        json={"present": [joined["Dara"]["id"]], "library_place_id": docks},
    ).json()
    place = next(e for e in scene["entities"] if e["name"] == "The Docks")
    assert scene["scene"]["place_id"] == place["id"]
    assert api.get(f"/stories/{story}/messages").json()[-1]["text"] == "— The Docks —"


def test_a_turn_without_a_model_explains_what_to_set(api):
    mira = api.post("/library", json={"kind": "character", "name": "Mira"}).json()["id"]
    story = api.post("/stories", json={"title": "x", "character_ids": [mira]}).json()["id"]
    streamed = events(api.post(f"/stories/{story}/turn", json={"text": "hi"}))
    assert streamed == [("error", {"message": "No model is set for the 'rp' role yet."})]


# --- memory ------------------------------------------------------------------------------------


def test_reading_now_then_inspecting_what_a_character_knows(api, story, backend, conn):
    backend.say("Hm.")
    api.post(f"/stories/{story}/turn", json={"text": "Mira, the ledger is under the floorboard."})
    who = cast(api, story)
    memory = {
        "memories": [
            {"kind": "event", "detail": "Aren told Mira the ledger is under the floorboard.",
             "gist": "Aren told Mira where something was hidden.", "importance": 8, "line": 1,
             "participants": [{"ref": f"E{who['Aren']['id']}", "role": "actor"},
                              {"ref": f"E{who['Mira']['id']}", "role": "target"}]}
        ]
    }  # fmt: skip
    backend.say(json.dumps(memory))
    run = api.post(f"/stories/{story}/extract").json()["run"]
    assert run["status"] == "ok" and run["trigger"] == "manual"
    assert api.get(f"/stories/{story}/runs").json()[0]["id"] == run["id"]

    known = api.get(f"/stories/{story}/memories?knower={who['Mira']['id']}").json()
    assert [(m["detail"], m["source"], m["tier"]) for m in known] == [
        ("Aren told Mira the ledger is under the floorboard.", "witnessed", "sharp")
    ]
    everything = api.get(f"/stories/{story}/memories").json()
    assert set(everything[0]["knowers"]) == {
        who["Mira"]["id"],
        who["Aren"]["id"],
        who["Tobin"]["id"],
    }


def test_the_user_can_write_a_memory_and_pin_it(api, story):
    mira = cast(api, story)["Mira"]["id"]
    created = api.post(
        f"/stories/{story}/memories",
        json={"detail": "Mira owes the guild forty silver.", "knower_ids": [mira], "pinned": True},
    ).json()
    assert created["pinned"] == 1 and created["run_id"] is None
    hidden = api.patch(f"/memories/{created['id']}", json={"hidden": True}).json()
    assert hidden["hidden"] == 1


def test_merging_a_duplicate_moves_everything_and_hides_it(api, story, conn):
    mira = cast(api, story)["Mira"]["id"]
    dup = conn.execute(
        "INSERT INTO entities(story_id, kind, name) VALUES(?, 'character', 'The Courier')", (story,)
    ).lastrowid
    conn.execute("INSERT INTO aliases(entity_id, alias) VALUES(?, 'The Courier')", (dup,))
    conn.execute(
        "INSERT INTO flags(entity_id, key, value, story_time) VALUES(?, 'mood', 'tense', 0)", (dup,)
    )
    conn.commit()
    api.post("/entities/merge", json={"keep": mira, "drop": dup})
    entities = {e["id"]: e for e in api.get(f"/stories/{story}/entities").json()}
    assert "The Courier" in entities[mira]["aliases"]
    assert entities[mira]["flags"][0]["value"] == "tense"
    assert entities[dup]["hidden"] == 1


def test_the_last_prompt_is_there_to_inspect(api, story, backend):
    backend.say("Hm.")
    api.post(f"/stories/{story}/turn", json={"text": "Mira?"})
    ctx = api.get(f"/stories/{story}/context").json()
    assert ctx["prompt"][0]["role"] == "system"
    assert {s["name"] for s in ctx["sections"]} >= {"rules", "history", "memory"}
    assert ctx["message_id"] is not None and ctx["actual_tokens"] > 0


def test_closing_the_stream_stops_the_model_and_keeps_what_was_written(tmp_path):
    """Through the real HTTP stack: the user presses Stop, the renderer aborts the request."""
    import asyncio
    import socket
    import threading
    import time

    import httpx2
    import uvicorn

    from kataki import db, library
    from kataki.llm import LLM

    model_stopped = threading.Event()

    async def slow_reply():
        try:
            for word in ["One ", "two ", "three ", "four ", "five ", "six ", "seven "]:
                chunk = {"choices": [{"delta": {"content": word}}]}
                yield f"data: {json.dumps(chunk)}\n\n".encode()
                await asyncio.sleep(0.3)
            yield b"data: [DONE]\n\n"
        finally:
            model_stopped.set()

    def model(request):
        return httpx2.Response(
            200, content=slow_reply(), headers={"content-type": "text/event-stream"}
        )

    conn = db.connect(tmp_path / "l.db")
    conn.execute("INSERT INTO providers(id, name, base_url) VALUES(1, 'local', 'http://fake/v1')")
    conn.execute("INSERT INTO model_roles(role, provider_id, model) VALUES('rp', 1, 'm')")
    mira = library.create_item(conn, "character", "Mira")
    story = library.create_story(conn, "s", character_ids=[mira])
    app = create_app(conn, "t", llm=LLM(transport=httpx2.MockTransport(model)), worker_delay=60)

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    server = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{sock.getsockname()[1]}/stories/{story}/turn"
        seen = []
        with httpx2.Client(timeout=10) as client:
            for _ in range(50):
                if server.started:
                    break
                time.sleep(0.1)
            with client.stream("POST", url, json={"text": "Mira?"}, headers=AUTH) as response:
                for line in response.iter_lines():
                    if line.startswith("event: token"):
                        seen.append(line)
                    if len(seen) == 2:
                        break  # leaving the block closes the connection mid-reply
        assert model_stopped.wait(5), "the model kept generating after the client left"
        for _ in range(50):
            kept = conn.execute(
                "SELECT text, gen FROM messages WHERE role='assistant' ORDER BY id DESC"
            ).fetchone()
            if kept:
                break
            time.sleep(0.1)
        assert kept is not None and kept["text"].startswith("One two")
        assert json.loads(kept["gen"])["finish"] == "stopped"
    finally:
        server.should_exit = True
        thread.join(5)
