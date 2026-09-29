"""Slice 1 end to end: moods that last, per branch, in the prompt, in the API."""

import json

import pytest

from kataki import chat, library, people, turns

pytestmark = pytest.mark.anyio


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    library.update_item(
        conn, ids["Mira"], data={"mind": {"regulation": {"style": "suppress", "capacity": 0.5}}}
    )
    gull = library.create_item(conn, "place", "The Gull")
    return library.create_story(
        conn, "Low Tide", character_ids=[ids["Mira"], ids["Tobin"]], place_id=gull,
        persona_id=ids["Aren"],
    )  # fmt: skip


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


async def play(stream):
    return [e async for e in stream]


def tail(request):
    return request["messages"][-1]["content"]


async def test_an_insult_is_felt_before_the_reply_and_still_felt_after(conn, story, backend):
    backend.say("...", "Fine.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert "[Inside Mira right now" in tail(backend.requests[0])
    assert "Hiding the hurt" in tail(backend.requests[0])  # she suppresses
    assert events[-1][1]["mood"]["label"] == "hurt"

    await play(turns.turn(conn, backend.llm, story, "Anyway, Mira."))
    assert "Feeling:" in tail(backend.requests[1])  # a few story-minutes on, still there


async def test_two_hours_later_only_a_low_mood_is_left(conn, story, backend):
    backend.say("...", "Morning.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    await play(turns.turn(conn, backend.llm, story, "Mira?", skip="two hours later"))
    block = tail(backend.requests[1])
    assert "Feeling:" not in block and "Mood: low." in block


async def test_a_new_take_does_not_feel_it_twice(conn, story, backend):
    backend.say("First.", "Second.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    await play(turns.regenerate(conn, backend.llm, story))
    a, b = (
        json.loads(r["state"])
        for r in conn.execute(
            "SELECT state FROM mind_states WHERE entity_id=? ORDER BY id", (eid(conn, "Mira"),)
        )
    )
    assert a["emotions"] == b["emotions"]


async def test_switched_off_no_mood_reaches_the_tail(conn, story, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.affect', 'false')")
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.bonds', 'false')")
    backend.say("Fine.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert "Feeling:" not in tail(backend.requests[0])  # the ledger's rows may still be there
    assert conn.execute("SELECT COUNT(*) FROM mind_states").fetchone()[0] == 0


async def test_the_lite_level_picks_the_face_without_a_call(conn, story, backend):
    lib = conn.execute("SELECT lib_item_id FROM entities WHERE name='Tobin'").fetchone()[0]
    library.update_item(conn, lib, data={"pack": {"neutral": 1}})
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    backend.say("Hey.")  # one reply and nothing else: a face call would find no script
    await play(turns.turn(conn, backend.llm, story, "Tobin, you're useless."))
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["expression"] == "wary"  # Tobin expresses: hurt shows as wary
    assert len(backend.requests) == 1


async def test_peek_sees_the_feeling_and_the_mask(conn, story, backend):
    backend.say("...")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    mira = next(p for p in people.people(conn, row) if p["name"] == "Mira")
    assert (mira["mood"]["label"], mira["mood"]["shows"]) == ("hurt", "calm")
    tobin = next(p for p in people.people(conn, row) if p["name"] == "Tobin")
    assert tobin["mood"] is None  # he heard it, but it was aimed at Mira


async def test_the_mind_graph_draws_the_mood_it_replied_with(conn, story, backend):
    from kataki import mind

    backend.say("...")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    graph = mind.mind(conn, chat.active_path(conn, story)[-1]["id"])
    node = next(n for n in graph["nodes"] if n["kind"] == "mood")
    assert node["text"] == "very hurt · showing calm"


@pytest.mark.parametrize("bad", [{"regulation": "suppress", "axes": {"warmth": 70}}, "junk"])
async def test_a_malformed_mind_profile_never_breaks_a_turn(conn, story, backend, bad):
    library.update_item(conn, conn.execute(
        "SELECT lib_item_id FROM entities WHERE name='Mira'").fetchone()[0], data={"mind": bad})  # fmt: skip
    backend.say("Fine.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert events[-1][0] == "done" and chat.active_path(conn, story)[-1]["text"] == "Fine."
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    assert {p["name"] for p in people.people(conn, row)} >= {"Mira", "Tobin"}


async def test_a_failing_mind_step_still_keeps_the_reply(conn, story, backend, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr("kataki.inner.react", boom)
    backend.say("Fine.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert events[-1][0] == "done" and events[-1][1]["mood"] is None
    assert "Feeling:" not in tail(backend.requests[0])  # the ledger's rows may still be there
    monkeypatch.setattr("kataki.inner.public", boom)  # and Peek without a mood
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    assert all(p["mood"] is None for p in people.people(conn, row))
