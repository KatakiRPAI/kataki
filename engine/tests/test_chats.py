"""A SillyTavern chat coming in: the file becomes a story, and its swipes become takes."""

import json

import pytest
from fastapi.testclient import TestClient

from kataki import chat, chats, library
from kataki.server import create_app

HEADER = {
    "user_name": "Aren",
    "character_name": "Mira",
    "create_date": "2026-03-01@21h14m02s",
    "chat_metadata": {"note": "kept"},
}
LINES = [
    {"name": "Mira", "is_user": False, "is_name": True, "mes": "*no glance up* We're closed."},
    {"name": "Aren", "is_user": True, "is_name": True, "mes": "I'm not here to drink."},
    {
        "name": "Mira", "is_user": False, "is_name": True, "mes": "*a page turns* Then say it.",
        "swipe_id": 1,
        "swipes": ["*she says nothing at all.*", "*a page turns* Then say it."],
        "swipe_info": [{}, {}],
    },
]  # fmt: skip


def jsonl(header, lines) -> bytes:
    return "\n".join(json.dumps(o) for o in ([header] if header else []) + lines).encode()


@pytest.fixture
def api(conn, backend):
    client = TestClient(create_app(conn, "t", llm=backend.llm, worker_delay=60))
    client.headers["Authorization"] = "Bearer t"
    with client:
        yield client


def path(conn, story_id):
    return [(m["role"], m["text"]) for m in chat.active_path(conn, story_id)]


def test_a_chat_becomes_a_story_with_its_cast(conn):
    made = chats.add(conn, jsonl(HEADER, LINES))
    story = made["story_id"]

    assert made["lines"] == 3 and made["takes"] == 1
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    assert row["title"] == "Mira — 2026-03-01"
    # nobody was named in the library, so the chat's own two people were made
    cast = {e["name"]: dict(e) for e in conn.execute(
        "SELECT * FROM entities WHERE story_id=?", (story,)
    )}  # fmt: skip
    assert sorted(cast) == ["Aren", "Mira"]
    assert cast["Mira"]["is_ai"] == 1 and cast["Aren"]["is_ai"] == 0
    assert row["persona_entity_id"] == cast["Aren"]["id"]
    assert sorted(i["name"] for i in library.list_items(conn, "character")) == ["Aren", "Mira"]

    assert path(conn, story) == [
        ("assistant", "*no glance up* We're closed."),
        ("user", "I'm not here to drink."),
        ("assistant", "*a page turns* Then say it."),
    ]
    speakers = [m["speaker_id"] for m in chat.active_path(conn, story)]
    assert speakers == [cast["Mira"]["id"], cast["Aren"]["id"], cast["Mira"]["id"]]


def test_swipes_become_takes_and_the_one_they_kept_is_the_one_showing(conn):
    story = chats.add(conn, jsonl(HEADER, LINES))["story_id"]
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["text"] == "*a page turns* Then say it."
    assert chat.sibling_position(conn, leaf["id"]) == (2, 2)  # the second of two, as it was

    others = conn.execute(
        "SELECT text FROM messages WHERE parent_id IS ? ORDER BY id", (leaf["parent_id"],)
    ).fetchall()
    assert [o["text"] for o in others] == [
        "*she says nothing at all.*",
        "*a page turns* Then say it.",
    ]


def test_a_chat_can_be_told_which_friends_it_is_about(conn):
    mira = library.create_item(conn, "character", "Mira", "She keeps the ledger.")
    aren = library.create_item(conn, "character", "Aren", "Late.", data={"persona": True})
    made = chats.add(conn, jsonl(HEADER, LINES), character_id=mira, persona_id=aren)

    cast = conn.execute(
        "SELECT name, lib_item_id FROM entities WHERE story_id=?", (made["story_id"],)
    ).fetchall()
    assert {c["name"]: c["lib_item_id"] for c in cast} == {"Mira": mira, "Aren": aren}
    assert len(library.list_items(conn, "character")) == 2  # nobody new was invented


def test_her_greeting_is_not_pushed_in_front_of_the_chat(conn):
    """The story starts where the file starts. A friend's own opening line belongs to a story
    she is beginning, not one already written."""
    mira = library.create_item(
        conn, "character", "Mira", "She keeps the ledger.", data={"first_message": "You're late."}
    )
    story = chats.add(conn, jsonl(HEADER, LINES), character_id=mira)["story_id"]
    assert path(conn, story)[0] == ("assistant", "*no glance up* We're closed.")


def test_a_system_line_is_narration_and_an_empty_one_is_nothing(conn):
    lines = [
        {"name": "System", "is_user": False, "is_system": True, "mes": "Aren left the room."},
        {"name": "Mira", "is_user": False, "mes": "   "},
        {"name": "Mira", "is_user": False, "mes": "*she waits.*"},
    ]
    made = chats.add(conn, jsonl(HEADER, lines))
    assert made["lines"] == 2 and made["skipped"] == 1
    [system, hers] = chat.active_path(conn, made["story_id"])
    assert system["speaker_id"] is None and system["text"] == "Aren left the room."
    assert hers["speaker_id"] is not None


def test_a_file_with_no_header_still_reads(conn):
    """Some exports are messages and nothing else; the names in them are enough."""
    made = chats.add(conn, jsonl(None, LINES))
    assert made["lines"] == 3
    cast = [e["name"] for e in conn.execute(
        "SELECT name FROM entities WHERE story_id=? ORDER BY name", (made["story_id"],)
    )]  # fmt: skip
    assert cast == ["Aren", "Mira"]


def test_a_broken_line_is_stepped_over_not_a_failed_import(conn):
    body = b"\n".join([
        json.dumps(HEADER).encode(),
        b"{not json at all",
        json.dumps(LINES[0]).encode(),
        b"",
        json.dumps({"name": "Aren", "is_user": True, "mes": "Still here."}).encode(),
    ])  # fmt: skip
    made = chats.add(conn, body)
    assert made["lines"] == 2
    assert any("1 line" in n for n in made["notes"])


def test_what_is_not_a_chat_says_so(conn):
    for blob, says in [
        (b"", "not a chat"),
        (b"not json\nnot json either\n", "not a chat"),
        (json.dumps(HEADER).encode(), "nothing in it"),
    ]:
        with pytest.raises(chats.BadCard, match=says):
            chats.add(conn, blob)


def test_the_route_imports_a_chat_and_the_story_can_be_played_on(api, backend, conn):
    provider = api.post("/providers", json={"name": "local", "base_url": "http://fake/v1/"}).json()
    api.put("/roles/rp", json={"provider_id": provider["id"], "model": "rp-model"})

    made = api.post("/import/chat", content=jsonl(HEADER, LINES))
    assert made.status_code == 201
    story = made.json()["story_id"]
    assert [m["text"] for m in api.get(f"/stories/{story}/messages").json()][-1].endswith(
        "Then say it."
    )

    backend.say("*she closes the book* Go on, then.")
    api.post(f"/stories/{story}/turn", json={"text": "The ledger."})
    assert api.get(f"/stories/{story}/messages").json()[-1]["text"].startswith("*she closes")

    assert api.post("/import/chat", content=b"rubbish").status_code == 422


def test_a_group_chat_brings_everyone_who_spoke(conn):
    """More than one voice answered in that file; each of them is someone here."""
    lines = [
        {"name": "Mira", "is_user": False, "mes": "*a page turns* We're closed."},
        {"name": "Aren", "is_user": True, "mes": "Tobin sent me."},
        {"name": "Tobin", "is_user": False, "mes": "*from the doorway* She did."},
        {"name": "Mira", "is_user": False, "mes": "*she looks up at last*"},
    ]
    made = chats.add(conn, jsonl(HEADER, lines))
    assert made["lines"] == 4
    assert any("Tobin" in n for n in made["notes"])

    cast = {e["name"]: e["id"] for e in conn.execute(
        "SELECT id, name FROM entities WHERE story_id=?", (made["story_id"],)
    )}  # fmt: skip
    assert sorted(cast) == ["Aren", "Mira", "Tobin"]
    assert [m["speaker_id"] for m in chat.active_path(conn, made["story_id"])] == [
        cast["Mira"], cast["Aren"], cast["Tobin"], cast["Mira"],
    ]  # fmt: skip


# --- what the review found: the files other apps actually write -----------------------------

GROUP = {"chat_metadata": {}, "user_name": "unused", "character_name": "unused"}


def test_a_real_group_chat_keeps_the_friend_you_chose(conn):
    """SillyTavern writes `unused` in the header of every group chat and every chat its own
    converters made, so the names on the messages are all there is to go on."""
    mira = library.create_item(conn, "character", "Mira Solane", "She keeps the ledger.")
    aren = library.create_item(conn, "character", "Aren", "Late.", data={"persona": True})
    lines = [
        {"name": "Tobin", "is_user": False, "mes": "*from the doorway* She's busy."},
        {"name": "Aren", "is_user": True, "mes": "Tobin sent me."},
        {"name": "Mira Solane", "is_user": False, "mes": "*a page turns* We're closed."},
    ]
    made = chats.add(conn, jsonl(GROUP, lines), character_id=mira, persona_id=aren)

    cast = {e["name"]: e["lib_item_id"] for e in conn.execute(
        "SELECT name, lib_item_id FROM entities WHERE story_id=?", (made["story_id"],)
    )}  # fmt: skip
    assert sorted(cast) == ["Aren", "Mira Solane", "Tobin"]  # nobody doubled
    assert cast["Mira Solane"] == mira and cast["Aren"] == aren
    assert [i["name"] for i in library.list_items(conn, "character")] == [
        "Aren",
        "Mira Solane",
        "Tobin",
    ]
    names = {e["id"]: e["name"] for e in conn.execute(
        "SELECT id, name FROM entities WHERE story_id=?", (made["story_id"],)
    )}  # fmt: skip
    spoke = [names.get(m["speaker_id"]) for m in chat.active_path(conn, made["story_id"])]
    assert spoke == ["Tobin", "Aren", "Mira Solane"]  # each line by whoever said it


def test_the_file_may_call_her_something_shorter(conn):
    """The header names her "Mira" and the library calls her Mira Solane: still one person."""
    mira = library.create_item(conn, "character", "Mira Solane")
    made = chats.add(conn, jsonl(HEADER, LINES), character_id=mira)
    cast = [e["name"] for e in conn.execute(
        "SELECT name FROM entities WHERE story_id=? AND is_ai=1", (made["story_id"],)
    )]  # fmt: skip
    assert cast == ["Mira Solane"]


def test_someone_who_walks_in_is_in_the_room(conn):
    """A voice made from the file has to be present, or she hears none of it and can never
    be asked to speak."""
    lines = [
        {"name": "Mira", "is_user": False, "mes": "*a page turns* We're closed."},
        {"name": "Tobin", "is_user": False, "mes": "*from the doorway* She did."},
    ]
    story = chats.add(conn, jsonl(HEADER, lines))["story_id"]
    path = chat.active_path(conn, story)
    here = {e["name"] for e in chat.present_entities(conn, path[-1]["scene_id"], path)}
    assert here == {"Mira", "Aren", "Tobin"}

    tobin = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name='Tobin'", (story,)
    ).fetchone()["id"]
    assert len(chat.heard_by(conn, path, tobin)) == 2  # he was there for all of it


def test_a_chat_from_chub_is_not_an_empty_story(conn):
    """Chub wraps every message in an object, and so every swipe."""
    lines = [
        {"name": "Mira", "is_user": False, "mes": {"message": "*a page turns* We're closed."}},
        {"name": "Aren", "is_user": True, "mes": {"message": "Tobin sent me."}},
        {
            "name": "Mira", "is_user": False, "mes": {"message": "Then say it."}, "swipe_id": 1,
            "swipes": [{"message": "*nothing at all*"}, {"message": "Then say it."}],
        },
    ]  # fmt: skip
    made = chats.add(conn, jsonl(GROUP, lines))
    assert (made["lines"], made["takes"], made["skipped"]) == (3, 1, 0)
    assert path(conn, made["story_id"])[-1] == ("assistant", "Then say it.")


def test_a_converted_chat_is_not_called_unused(conn):
    made = chats.add(conn, jsonl(GROUP, LINES))
    title = conn.execute("SELECT title FROM stories WHERE id=?", (made["story_id"],)).fetchone()[
        "title"
    ]
    assert title == "Mira"  # the first voice in it, since the header names nobody


def test_a_line_somebody_hid_is_still_theirs(conn):
    """`/hide` sets is_system on whatever it points at, the user's own words included. They
    stay out of the prompt, and they stay the user's."""
    lines = [
        {"name": "Aren", "is_user": True, "is_system": True, "mes": "I'm not here to drink."},
        {"name": "System", "is_user": False, "is_system": True, "mes": "Aren left the room."},
        {"name": "Mira", "is_user": False, "mes": "*she waits.*"},
    ]
    made = chats.add(conn, jsonl(HEADER, lines))
    rows = chat.active_path(conn, made["story_id"])
    names = {e["id"]: e["name"] for e in conn.execute(
        "SELECT id, name FROM entities WHERE story_id=?", (made["story_id"],)
    )}  # fmt: skip
    assert [(r["role"], names.get(r["speaker_id"]), bool(r["hidden"])) for r in rows] == [
        ("user", "Aren", True),
        ("assistant", None, True),  # a notice in nobody's voice
        ("assistant", "Mira", False),
    ]
    assert "System" not in [i["name"] for i in library.list_items(conn, "character")]


def test_a_blank_swipe_does_not_move_the_one_they_kept(conn):
    """A failed generation leaves an empty swipe. Dropping it must not shift the index."""
    lines = [
        {"name": "Mira", "is_user": False, "mes": "KEPT", "swipe_id": 1,
         "swipes": ["", "KEPT", "other"]},
        {"name": "Aren", "is_user": True, "mes": "And then?"},
    ]  # fmt: skip
    made = chats.add(conn, jsonl(HEADER, lines))
    assert path(conn, made["story_id"]) == [("assistant", "KEPT"), ("user", "And then?")]


def test_a_swipe_id_that_is_not_an_index_is_not_one(conn):
    """`true` is an int in Python and is not the second take."""
    lines = [{"name": "Mira", "is_user": False, "mes": "first", "swipe_id": True,
              "swipes": ["first", "second"]}]  # fmt: skip
    made = chats.add(conn, jsonl(HEADER, lines))
    assert path(conn, made["story_id"]) == [("assistant", "first")]


def test_swipes_that_are_not_a_list_are_not_letters(conn):
    lines = [{"name": "Mira", "is_user": False, "mes": "*she waits.*", "swipes": "abc"}]
    made = chats.add(conn, jsonl(HEADER, lines))
    assert made["takes"] == 0
    assert path(conn, made["story_id"]) == [("assistant", "*she waits.*")]


def test_a_chat_longer_than_the_engine_will_read_says_so(conn, monkeypatch):
    monkeypatch.setattr(chats, "MAX_LINES", 4)
    lines = [{"name": "Mira", "is_user": False, "mes": f"line {i}"} for i in range(9)]
    made = chats.add(conn, jsonl(HEADER, lines))
    assert made["lines"] == 3  # the header took one of the four
    assert any("stayed behind" in n for n in made["notes"])


def test_the_route_will_not_take_someone_who_is_not_a_character(api):
    place = api.post("/library", json={"kind": "place", "name": "The Gull"}).json()["id"]
    plot = api.post("/library", json={"kind": "scenario", "name": "Low Tide"}).json()["id"]
    mira = api.post("/library", json={"kind": "character", "name": "Mira"}).json()["id"]
    body = jsonl(HEADER, LINES)

    assert api.post(f"/import/chat?character_id={place}", content=body).status_code == 422
    assert api.post(f"/import/chat?persona_id={plot}", content=body).status_code == 422
    assert (
        api.post(f"/import/chat?character_id={mira}&persona_id={mira}", content=body).status_code
        == 422
    )
    assert api.post(f"/import/chat?character_id={mira}", content=body).status_code == 201
