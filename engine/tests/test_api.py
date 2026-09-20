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


# --- stories as the Sky lists them -----------------------------------------------------------


def test_the_story_list_shows_each_story_with_its_people_place_and_last_line(api, story, backend):
    backend.say("*frowns* The lighthouse?")
    api.post(f"/stories/{story}/turn", json={"text": "Evening, Mira."})
    tobin = cast(api, story)["Tobin"]["id"]
    api.post(f"/stories/{story}/presence", json={"entity_id": tobin, "present": False})

    [entry] = api.get("/stories").json()
    ids = {name: e["id"] for name, e in cast(api, story).items()}
    lib = {i["name"]: i["id"] for i in api.get("/library").json()}
    assert entry["id"] == story and entry["title"] == "Low Tide" and entry["pinned"] is False
    assert entry["messages"] == 2 and entry["last_at"] and entry["created_at"]
    assert (entry["clock"], entry["minute_of_day"]) == ("Day 1, 08:04", 484)
    assert entry["persona"] == {"id": ids["Aren"], "name": "Aren", "lib_item_id": lib["Aren"]}
    assert entry["place"] == {
        "id": ids["The Gull"],
        "name": "The Gull",
        "lib_item_id": lib["The Gull"],
    }
    assert entry["cast"] == [
        {"id": ids["Mira"], "name": "Mira", "lib_item_id": lib["Mira"], "present": True},
        {"id": ids["Tobin"], "name": "Tobin", "lib_item_id": lib["Tobin"], "present": False},
    ]
    assert entry["last_line"] == {"speaker": "Mira", "text": "*frowns* The lighthouse?"}


def test_pinned_stories_come_first_then_the_most_recently_played(api, story, backend):
    mira = next(i["id"] for i in api.get("/library").json() if i["name"] == "Mira")
    older = api.post("/stories", json={"title": "Older", "character_ids": [mira]}).json()["id"]
    newer = api.post("/stories", json={"title": "Newer", "character_ids": [mira]}).json()["id"]
    backend.say("Back again.")
    api.post(f"/stories/{story}/turn", json={"text": "Mira?"})  # Low Tide was played last
    assert [s["title"] for s in api.get("/stories").json()] == ["Low Tide", "Newer", "Older"]

    assert api.patch(f"/stories/{older}", json={"pinned": True}).json()["pinned"] is True
    assert [s["title"] for s in api.get("/stories").json()] == ["Older", "Low Tide", "Newer"]
    assert [s["last_line"] for s in api.get("/stories").json()][2] is None
    assert newer


def test_a_story_can_start_at_any_time_of_day_and_says_where_its_clock_began(api):
    mira = api.post("/library", json={"kind": "character", "name": "Mira"}).json()["id"]
    dusk = api.post(
        "/stories", json={"title": "Dusk", "character_ids": [mira], "epoch_offset_min": 1140}
    ).json()
    assert (dusk["clock"], dusk["minute_of_day"], dusk["story_time"]) == ("Day 1, 19:00", 1140, 0)
    assert dusk["start_clock"] == "Day 1, 19:00" and dusk["epoch_offset_min"] == 1140
    frost = api.post(
        "/stories", json={"title": "Frost", "character_ids": [mira], "epoch_offset_min": 1840}
    ).json()
    assert (frost["start_clock"], frost["minute_of_day"]) == ("Day 2, 06:40", 400)
    assert api.post("/stories", json={"title": "x", "epoch_offset_min": -5}).status_code == 422


def test_a_story_says_who_you_play_where_you_are_and_what_the_scene_is_called(api, story):
    gull = cast(api, story)["The Gull"]["id"]
    api.post(f"/stories/{story}/scene", json={"present": [], "place_id": gull, "title": "Night"})
    got = api.get(f"/stories/{story}").json()
    assert got["persona"]["name"] == "Aren" and got["place"]["name"] == "The Gull"
    assert got["scene_title"] == "Night" and got["pinned"] is False
    # the scene marker is a line, so it takes a turn's minutes; the start stays where it was
    assert (got["story_time"], got["clock"], got["start_clock"]) == (
        2,
        "Day 1, 08:02",
        "Day 1, 08:00",
    )


def test_seen_marks_the_newest_finished_read_and_leaves_one_still_running(api, story, conn):
    """A read that has not finished has written nothing yet, so seeing the story now must not
    swallow what it is about to write: leaving a scene while the reader works is the usual way
    out of one."""

    def run(upto, status):
        with conn:
            conn.execute(
                "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger,"
                " status) VALUES(?, 0, ?, 'manual', ?)",
                (story, upto, status),
            )
        return conn.execute("SELECT max(id) FROM extraction_runs").fetchone()[0]

    done = run(1, "ok")
    working = run(2, "running")
    assert api.post(f"/stories/{story}/seen").status_code == 204
    row = conn.execute("SELECT seen_run_id FROM stories WHERE id=?", (story,)).fetchone()
    assert row[0] == done < working
    assert api.post("/stories/999/seen").status_code == 404


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


def test_a_whisper_is_kept_with_its_line_and_foreign_listeners_are_refused(api, story, conn):
    mira = cast(api, story)["Mira"]["id"]
    assert (
        api.post(f"/stories/{story}/turn", json={"text": "psst", "audience": [9999]}).status_code
        == 422
    )
    api.post(f"/stories/{story}/turn", json={"text": "psst", "audience": [mira]})
    row = conn.execute("SELECT audience FROM messages WHERE text='psst'").fetchone()
    assert json.loads(row["audience"]) == [mira]


def test_a_line_can_be_added_without_asking_anyone_to_reply(api, story, backend):
    made = api.post(f"/stories/{story}/line", json={"text": "*sits down*"})
    assert made.status_code == 201 and made.json()[-1]["text"] == "*sits down*"
    assert backend.requests == []
    assert api.post(f"/stories/{story}/line", json={}).status_code == 422


def test_passing_time_alone_writes_a_marker_and_moves_the_clock(api, story, backend):
    marker = api.post(f"/stories/{story}/line", json={"skip": "six years later"}).json()[-1]
    assert (marker["role"], marker["text"], marker["skip_minutes"]) == (
        "system",
        "— Six years later —",
        3_153_600,
    )
    assert marker["clock"].startswith("Year 7") and backend.requests == []
    assert api.post(f"/stories/{story}/line", json={"skip": "whenever"}).status_code == 422


def test_a_thought_is_a_line_for_no_one(api, story):
    said = api.post(f"/stories/{story}/line", json={"text": "I don't trust him.", "audience": []})
    assert said.json()[-1]["audience"] == [] and said.json()[-1]["think_ms"] is None


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


def test_the_cast_lists_only_real_arrivals_and_departures_and_one_can_be_undone(api, story):
    tobin = cast(api, story)["Tobin"]["id"]
    api.post(f"/stories/{story}/line", json={"text": "Tobin, a round from the bar?"})
    api.post(f"/stories/{story}/presence", json={"entity_id": tobin, "present": False})
    api.post(f"/stories/{story}/presence", json={"entity_id": tobin, "present": False})  # no-op
    api.post(f"/stories/{story}/line", json={"text": "*waits*"})
    back = api.post(f"/stories/{story}/presence", json={"entity_id": tobin, "present": True})
    changes = back.json()["changes"]
    assert [(c["entity_id"], c["present"], c["found"]) for c in changes] == [
        (tobin, False, False),
        (tobin, True, False),
    ]
    assert changes[0]["clock"] == "Day 1, 08:02"  # two minutes a line
    assert all(e["lib_item_id"] for e in back.json()["entities"])

    undone = api.delete(f"/presence/{changes[1]['id']}")
    assert undone.status_code == 200
    assert {e["name"]: e["present"] for e in undone.json()["entities"]}["Tobin"] is False
    assert len(undone.json()["changes"]) == 1
    assert api.delete(f"/presence/{changes[1]['id']}").status_code == 404


def test_a_new_scene_can_start_after_time_passes(api, story):
    gull = cast(api, story)["The Gull"]["id"]
    scene = api.post(
        f"/stories/{story}/scene",
        json={"present": [], "place_id": gull, "skip": "the next morning"},
    )
    assert scene.status_code == 201
    marker = api.get(f"/stories/{story}/messages").json()[-1]
    assert marker["text"] == "— The Gull —" and marker["skip_minutes"] > 0
    assert marker["clock"].startswith("Day 2, ")
    whenever = api.post(f"/stories/{story}/scene", json={"present": [], "skip": "whenever"})
    assert whenever.status_code == 422


def test_rereading_twice_leaves_one_presence_row_and_runs_say_what_they_filed(
    api, story, backend, conn
):
    who = cast(api, story)
    backend.say("Hm.")
    api.post(f"/stories/{story}/turn", json={"text": "Tobin, fetch a round from the bar."})
    found = {
        "memories": [
            {"kind": "event", "detail": "Aren sent Tobin to the bar.",
             "gist": "Tobin was sent off.", "importance": 3, "line": 1,
             "participants": [{"ref": f"E{who['Aren']['id']}", "role": "actor"},
                              {"ref": f"E{who['Tobin']['id']}", "role": "target"}]}
        ],
        "presence": [{"entity": f"E{who['Tobin']['id']}", "present": False}],
    }  # fmt: skip
    backend.say(json.dumps(found), json.dumps(found), json.dumps(found))
    run = api.post(f"/stories/{story}/extract").json()["run"]
    assert run["filed"] == 1
    again = api.post(f"/runs/{run['id']}/reread", json={}).json()
    again = api.post(f"/runs/{again['id']}/reread", json={}).json()
    rows = conn.execute(
        "SELECT run_id FROM presence WHERE entity_id=? AND message_id IS NOT NULL",
        (who["Tobin"]["id"],),
    ).fetchall()
    assert [r[0] for r in rows] == [again["id"]]
    assert api.get(f"/stories/{story}/runs").json()[0]["filed"] == 1
    changes = api.get(f"/stories/{story}/cast").json()["changes"]
    assert [(c["entity_id"], c["present"], c["found"]) for c in changes] == [
        (who["Tobin"]["id"], False, True)
    ]


def test_the_version_changes_when_memory_reads_the_story(api, story, backend):
    backend.say("Hm.")
    api.post(f"/stories/{story}/turn", json={"text": "Mira, the ledger is under the floorboard."})
    before = api.get(f"/stories/{story}/version").json()
    assert before == {"v": "0:0:0:0", "waiting": 1}
    backend.say(json.dumps({"memories": []}))
    run = api.post(f"/stories/{story}/extract").json()["run"]
    after = api.get(f"/stories/{story}/version").json()
    assert after == {"v": f"{run['id']}:1:1:0", "waiting": 0}


def test_signals_say_who_heard_each_line(api, story, backend):
    backend.say("Hm.")
    api.post(f"/stories/{story}/turn", json={"text": "Evening, Mira."})
    said = api.get(f"/stories/{story}/messages").json()[-2]
    got = api.get(f"/stories/{story}/signals")
    assert got.status_code == 200
    mira = cast(api, story)["Mira"]["id"]
    receipts = got.json()["lines"][str(said["id"])]["receipts"]
    assert {"id": mira, "state": "heard", "pending": True} in receipts
    assert api.get("/stories/999/signals").status_code == 404


def test_activity_and_the_story_list_say_what_is_new(api, story, backend, conn):
    who = cast(api, story)
    backend.say("Hm.")
    api.post(f"/stories/{story}/turn", json={"text": "Mira, the ledger is under the floorboard."})
    memory = {
        "memories": [
            {"kind": "event", "detail": "Aren hid the ledger under the floorboard.",
             "gist": "Aren hid the ledger.", "importance": 8, "line": 1,
             "participants": [{"ref": f"E{who['Aren']['id']}", "role": "actor"},
                              {"ref": f"E{who['Mira']['id']}", "role": "target"}]}
        ]
    }  # fmt: skip
    backend.say(json.dumps(memory))
    api.post(f"/stories/{story}/extract")

    events = api.get("/activity").json()
    assert events[0]["kind"] == "memory" and events[0]["new"] is True
    assert events[0]["text"].startswith("Mira")
    assert api.get("/activity?kind=belief").json() == []
    listed = next(s for s in api.get("/stories").json() if s["id"] == story)
    assert (listed["new_events"], listed["waiting"]) == (1, 0)  # the read drained what waited
    assert api.get("/activity?limit=-1").status_code == 422

    api.post(f"/stories/{story}/seen")
    assert api.get("/activity").json()[0]["new"] is False
    assert next(s for s in api.get("/stories").json() if s["id"] == story)["new_events"] == 0


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


# --- who is in a story, and what a friend is like ----------------------------------------------


def ledger_scene(api, story, backend, conn):
    """The brief's scene, short: Tobin is sent off, Aren tells Mira the secret, the reader files
    what it meant. Returns the cast by name."""
    backend.say("*pockets the coin* Anything for a paying customer.")
    api.post(f"/stories/{story}/turn", json={"text": "Tobin, fetch us a round from the bar?"})
    who = cast(api, story)
    api.post(f"/stories/{story}/presence", json={"entity_id": who["Tobin"]["id"], "present": False})
    backend.say("*her eyes flick to the bar* Then stop saying it out loud.")
    api.post(
        f"/stories/{story}/turn",
        json={"text": "I hid the guild ledger under the third floorboard.",
              "audience": [who["Mira"]["id"]]},
    )  # fmt: skip
    read = {
        "memories": [
            {
                "kind": "event",
                "detail": "Aren hid the guild ledger under the third floorboard.",
                "gist": "Aren hid the ledger behind the bar.",
                "importance": 9,
                "line": 3,
                "participants": [
                    {"ref": f"E{who['Aren']['id']}", "role": "actor"},
                    {"ref": f"E{who['Mira']['id']}", "role": "target"},
                ],
            },
            {
                "kind": "fact",
                "detail": "The Gull keeps a green apron behind the bar.",
                "gist": "The Gull has a green apron.",
                "importance": 2,
                "line": 1,
                "participants": [{"ref": f"E{who['Mira']['id']}", "role": "witness"}],
            },
        ],
        "flags": [
            {
                "entity": f"E{who['Mira']['id']}",
                "key": "holding",
                "value": "a mug she hasn't touched",
            },
            {"entity": f"E{who['Mira']['id']}", "key": "wearing", "value": "a green apron"},
            {
                "entity": f"E{who['Mira']['id']}",
                "key": "aches",
                "value": "an old wrist break",
                "private": True,
            },
        ],  # fmt: skip
        "edges": [
            {
                "src": f"E{who['Mira']['id']}",
                "dst": f"E{who['Aren']['id']}",
                "rel": "trusts",
                "note": "He told her where the ledger is.",
            },
            {
                "src": f"E{who['Tobin']['id']}",
                "dst": f"E{who['Aren']['id']}",
                "rel": "resents",
                "note": "Sent off like a servant.",
            },
        ],  # fmt: skip
    }
    backend.say(json.dumps(read))
    assert api.post(f"/stories/{story}/extract").json()["run"]["status"] == "ok"
    return who


def test_the_people_of_a_story_say_what_they_hold_recall_and_feel(api, story, backend, conn):
    who = ledger_scene(api, story, backend, conn)
    people = {p["name"]: p for p in api.get(f"/stories/{story}/people").json()}
    assert list(people) == ["Mira", "Tobin"]  # the AI characters, not you

    mira = people["Mira"]
    assert (mira["id"], mira["present"], mira["where"]) == (who["Mira"]["id"], True, "The Gull")
    assert mira["lib_item_id"] and mira["since"] == "Day 1, 08:00"  # there from the opening
    assert mira["state"] == [
        {"key": "holding", "value": "a mug she hasn't touched", "private": False},
        {"key": "wearing", "value": "a green apron", "private": False},
        {"key": "aches", "value": "an old wrist break", "private": True},
    ]
    assert mira["on_mind"] == {
        "tier": "sharp",
        "text": "Aren hid the guild ledger under the third floorboard.",
    }
    assert mira["remembers"] == 2  # the secret and the apron
    assert mira["about_you"]["count"] == 1 and mira["about_you"]["sharp"] == 1
    assert (mira["about_you"]["hazy"], mira["about_you"]["forgotten"]) == (0, 0)
    [sample] = mira["about_you"]["samples"]
    assert sample["text"] == "Aren hid the guild ledger under the third floorboard."
    assert (sample["tier"], sample["belief"]) == ("sharp", 1.0)
    assert mira["relationships"] == [
        {"rel": "trusts", "other_id": who["Aren"]["id"], "other": "Aren", "you": True,
         "note": "He told her where the ledger is.", "since": "Day 1, 08:06"},
    ]  # fmt: skip

    tobin = people["Tobin"]
    assert tobin["present"] is False and tobin["since"] == "Day 1, 08:04"  # sent off after line 2
    assert tobin["about_you"]["count"] == 0  # the secret was whispered past him
    assert tobin["state"] == []  # Mira's mug and coat are hers, not his
    assert tobin["remembers"] == 1  # he was at the bar for it, but he did hear about the apron
    assert tobin["on_mind"] == {
        "tier": "sharp",
        "text": "The Gull keeps a green apron behind the bar.",
    }
    assert [r["rel"] for r in tobin["relationships"]] == ["resents"]


def test_people_in_director_mode_know_nothing_about_you(api, backend, conn):
    mira = api.post("/library", json={"kind": "character", "name": "Mira"}).json()["id"]
    story = api.post("/stories", json={"title": "Alone", "character_ids": [mira]}).json()["id"]
    [person] = api.get(f"/stories/{story}/people").json()
    assert person["about_you"] is None and person["remembers"] == 0
    assert (
        api.get(f"/library/{mira}/profile").json()["places"] == []
    )  # played nowhere in particular
    assert api.get("/stories/999/people").status_code == 404


def test_a_friends_profile_gathers_her_stories_and_the_places_she_has_been(
    api, story, backend, conn
):
    who = ledger_scene(api, story, backend, conn)
    lib = {i["name"]: i["id"] for i in api.get("/library").json()}
    profile = api.get(f"/library/{lib['Mira']}/profile").json()

    [entry] = profile["stories"]
    assert (entry["id"], entry["title"], entry["role"]) == (story, "Low Tide", "ai")
    assert entry["person"]["name"] == "Mira" and entry["person"]["remembers"] == 2
    assert entry["known_by"] is None
    assert profile["places"] == [
        {"name": "The Gull", "lib_item_id": lib["The Gull"], "story": "Low Tide",
         "story_id": story, "clock": "Day 1, 08:08"},
    ]  # fmt: skip

    mine = api.get(f"/library/{lib['Aren']}/profile").json()
    [as_me] = mine["stories"]
    assert as_me["role"] == "persona" and as_me["person"] is None
    assert as_me["known_by"] == [
        {"id": who["Mira"]["id"], "name": "Mira", "lib_item_id": lib["Mira"], "count": 1,
         "sharp": 1, "hazy": 0, "forgotten": 0},
        {"id": who["Tobin"]["id"], "name": "Tobin", "lib_item_id": lib["Tobin"], "count": 0,
         "sharp": 0, "hazy": 0, "forgotten": 0},
    ]  # fmt: skip
    assert api.get("/library/999/profile").status_code == 404


def test_a_new_scene_starts_how_long_they_have_been_here_again(api, story, backend, conn):
    who = ledger_scene(api, story, backend, conn)
    docks = api.post("/library", json={"kind": "place", "name": "The Docks"}).json()["id"]
    api.post(
        f"/stories/{story}/scene",
        json={"present": [who["Mira"]["id"], who["Tobin"]["id"]], "library_place_id": docks,
              "skip": "the next morning"},
    )  # fmt: skip
    people = {p["name"]: p for p in api.get(f"/stories/{story}/people").json()}
    # Tobin was sent off yesterday; he is back, and he has been at the docks since it opened
    assert (people["Tobin"]["present"], people["Tobin"]["since"]) == (True, "Day 2, 08:00")
    assert people["Mira"]["since"] == "Day 2, 08:00" and people["Mira"]["where"] == "The Docks"


def test_a_feeling_that_ended_is_no_longer_how_she_feels(api, story, backend, conn):
    who = ledger_scene(api, story, backend, conn)
    backend.say("*sets the mug down* I'll think about it.")
    api.post(f"/stories/{story}/turn", json={"text": "You don't believe me?"})
    backend.say(json.dumps({"edges": [
        {"src": f"E{who['Mira']['id']}", "dst": f"E{who['Aren']['id']}", "rel": "trusts",
         "ended": True},
    ]}))  # fmt: skip
    assert api.post(f"/stories/{story}/extract").json()["run"]["status"] == "ok"
    mira = {p["name"]: p for p in api.get(f"/stories/{story}/people").json()}["Mira"]
    assert mira["relationships"] == []  # the reader saw the trust end


def test_what_a_read_on_a_branch_you_took_back_wrote_is_not_who_she_is(api, story, backend, conn):
    who = ledger_scene(api, story, backend, conn)
    lib = {i["name"]: i["id"] for i in api.get("/library").json()}

    def mira():
        return {p["name"]: p for p in api.get(f"/stories/{story}/people").json()}["Mira"]

    def places():
        return [p["name"] for p in api.get(f"/library/{lib['Mira']}/profile").json()["places"]]

    backend.say("*she says nothing at all*")
    api.post(f"/stories/{story}/regenerate")  # a second take of her reply
    taken_again = api.get(f"/stories/{story}/messages").json()[-1]["id"]
    backend.say("*she turns the letter over*")
    api.post(f"/stories/{story}/turn", json={"text": "Mira?"})  # the take gets a read of its own
    backend.say(json.dumps({
        "flags": [{"entity": f"E{who['Mira']['id']}", "key": "holding", "value": "the letter"}],
        "edges": [{"src": f"E{who['Mira']['id']}", "dst": f"E{who['Aren']['id']}",
                   "rel": "doubts", "note": "He went quiet."}],
    }))  # fmt: skip
    assert api.post(f"/stories/{story}/extract").json()["run"]["status"] == "ok"
    docks = api.post("/library", json={"kind": "place", "name": "The Docks"}).json()["id"]
    api.post(
        f"/stories/{story}/scene",
        json={"present": [who["Mira"]["id"]], "library_place_id": docks},
    )
    assert mira()["state"][0]["value"] == "the letter"
    assert [r["rel"] for r in mira()["relationships"]] == ["trusts", "doubts"]
    assert places() == ["The Gull", "The Docks"]

    api.post(f"/stories/{story}/swipe", json={"message_id": taken_again, "step": -1})
    backend.say("*she pushes the mug aside*")
    api.post(f"/stories/{story}/turn", json={"text": "Mira?"})  # on past the moment it was written
    assert mira()["state"][0]["value"] == "a mug she hasn't touched"  # that take never happened
    assert [r["rel"] for r in mira()["relationships"]] == ["trusts"]
    assert places() == ["The Gull"]  # and they were never at the docks
    assert mira()["remembers"] == 2  # what the first read filed is still hers


def test_after_six_years_nothing_small_is_on_his_mind(api, story, backend, conn):
    ledger_scene(api, story, backend, conn)
    api.post(f"/stories/{story}/line", json={"text": "", "skip": "six years later"})
    people = {p["name"]: p for p in api.get(f"/stories/{story}/people").json()}
    # Tobin only ever knew where the aprons are kept; six years takes that
    assert people["Tobin"]["on_mind"] is None and people["Tobin"]["remembers"] == 1
    # the secret is what she was told, and it is still there, if only the shape of it
    assert people["Mira"]["on_mind"]["tier"] in ("sharp", "hazy")
    assert people["Mira"]["about_you"]["count"] == 1


def test_books_gather_stories_and_the_list_says_which_book_a_story_is_in(api, story):
    book = api.post("/books", json={"title": "The Gull Years", "blurb": "At the bar"}).json()
    assert (book["title"], book["stories"]) == ("The Gull Years", 0)
    assert api.get("/books").json() == [book]

    assert api.patch(f"/stories/{story}", json={"book_id": book["id"]}).status_code == 200
    listed = next(s for s in api.get("/stories").json() if s["id"] == story)
    assert listed["book"] == {"id": book["id"], "title": "The Gull Years"}
    assert api.get("/books").json()[0]["stories"] == 1

    mira = next(i["id"] for i in api.get("/library").json() if i["name"] == "Mira")
    other = api.post("/stories", json={"title": "Later", "character_ids": [mira]}).json()["id"]
    api.patch(f"/stories/{other}", json={"book_id": book["id"]})
    assert api.post(f"/books/{book['id']}/stories", json={"story_ids": [other, story]}).json() == [
        {"id": other, "title": "Later"},
        {"id": story, "title": "Low Tide"},
    ]

    assert (
        api.patch(f"/books/{book['id']}", json={"title": "The Gull"}).json()["title"] == "The Gull"
    )
    assert api.delete(f"/books/{book['id']}").status_code == 204
    assert api.get("/books").json() == []
    assert next(s for s in api.get("/stories").json() if s["id"] == story)["book"] is None
    assert api.get("/books/999").status_code == 404
    assert api.patch(f"/stories/{story}", json={"book_id": 999}).status_code == 422
