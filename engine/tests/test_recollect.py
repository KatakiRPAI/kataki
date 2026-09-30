"""Minds slice 6: what she feels tilts what comes back, half-remembered things give true cues,
her own version of a hazy memory, the slip code plants with the truth kept, and the repair."""

import re

import pytest

from kataki import activation, chat, extract, library, recollect, retrieve

DAY, YEAR = 1440, 365 * 1440
DETAIL = "Tobin told Mira he would betray the guild at the docks on Thursday."
GIST = "Tobin spoke of turning on the guild."


@pytest.fixture
def world(conn):
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Dara", "Aren")}
    gull = library.create_item(conn, "place", "The Gull")
    story = library.create_story(
        conn,
        "Low Tide",
        character_ids=[ids["Mira"], ids["Tobin"], ids["Dara"]],
        place_id=gull,
        persona_id=ids["Aren"],
    )
    scene = conn.execute("SELECT id FROM scenes WHERE story_id=?", (story,)).fetchone()["id"]
    conn.execute(  # Dara is elsewhere
        "INSERT INTO presence(scene_id, entity_id, present) VALUES(?, ?, 0)",
        (scene, eid(conn, "Dara")),
    )
    return story


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


def h(conn, name):
    return f"E{eid(conn, name)}"


def say(conn, story, text="...", skip=0):
    return chat.append_message(
        conn, story, "user", text, speaker_id=eid(conn, "Aren"), skip_minutes=skip
    )


def extracted(conn, story, data):
    first, last = say(conn, story), say(conn, story)
    run_id = extract.open_run(conn, story, first, last, "cadence")
    extract.apply(conn, run_id, data)
    say(conn, story)  # the conversation moves on, so the window no longer covers the run
    return run_id


def betrayal(conn, **extra):
    return {
        "kind": "event",
        "detail": DETAIL,
        "gist": GIST,
        "importance": 6,
        "participants": [
            {"ref": h(conn, "Tobin"), "role": "actor"},
            {"ref": h(conn, "Mira"), "role": "target"},
        ],
        "place": h(conn, "The Gull"),
        "tags": ["betrayal"],
        **extra,
    }


def recall(conn, story, text="Tobin guild", **kw):
    return retrieve.recall(conn, story, eid(conn, "Mira"), text, noise=False, **kw)


def off(conn):
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.recall', 'false')")


# --- what she feels tilts what comes back ---------------------------------------------------


def test_congruence_lifts_memories_that_match_the_mood_and_only_those_with_a_feeling():
    assert recollect.congruence(-0.8, -0.6, 8) > 0 > recollect.congruence(0.8, -0.6, 8)
    assert recollect.congruence(None, -0.6, 8) == recollect.congruence(-0.8, None, 8) == 0
    assert recollect.congruence(-0.8, -0.6, 2) < recollect.congruence(-0.8, -0.6, 8)  # arousal


def test_a_low_mood_brings_back_the_sad_memory_first(conn, world):
    sad = betrayal(conn, detail="Tobin wept at the Gull.", gist="Tobin wept.", valence=-0.8)
    glad = betrayal(conn, detail="Tobin laughed at the Gull.", gist="Tobin laughed.", valence=0.8)
    extracted(conn, world, {"memories": [glad, sad]})
    low = recall(conn, world, "Tobin", mood=-0.6, log=False)
    high = recall(conn, world, "Tobin", mood=0.6, log=False)
    assert [r.text for r in low][0] == "Tobin wept at the Gull."
    assert [r.text for r in high][0] == "Tobin laughed at the Gull."
    assert low[0].breakdown["M"] > 0 > low[1].breakdown["M"]
    off(conn)
    assert {r.breakdown.get("M", 0) for r in recall(conn, world, "Tobin", mood=-0.6)} == {0}


# --- the tip of the tongue ------------------------------------------------------------------


def test_cues_are_true_short_and_in_words():
    got = recollect.cues(
        [{"id": 2, "kind": "character", "name": "Tobin"}, {"id": 9, "kind": "place", "name": "The Gull"}],
        here={1}, knower=1, emotion="dread", since=6 * YEAR,
    )  # fmt: skip
    assert got == ["a name that starts with T", "a place whose name starts with G"]
    alone = recollect.cues([], here=set(), knower=1, emotion="dread", since=6 * YEAR)
    assert alone == ["the feeling: dread", "about six years ago"]
    assert not any(re.search(r"\d", c) for c in alone)


def hazy(conn, world, **extra):
    extracted(conn, world, {"memories": [betrayal(conn, **extra)]})
    say(conn, world, "Six years later...", skip=6 * YEAR)
    return conn.execute("SELECT id FROM memories").fetchone()["id"]


def test_pressed_on_a_hazy_memory_she_cannot_reach_she_gets_true_cues(conn, world, monkeypatch):
    memory = hazy(conn, world)
    monkeypatch.setattr(activation, "effortful_recall", lambda *a: False)
    (got,) = recall(conn, world, pressed={memory})
    # Tobin is in the room (his name is no cue); the place and the years are
    assert got.text == (
        f"{GIST} (on the tip of your tongue: a place whose name starts with G; about six years ago)"
    )
    assert got.breakdown["cue"]
    (unpressed,) = recall(conn, world)
    assert unpressed.text == GIST
    off(conn)
    assert recall(conn, world, pressed={memory})[0].text == GIST


# --- never forgotten ------------------------------------------------------------------------


def test_a_locked_memory_is_never_forgotten(conn, world):
    trivial = {"importance": 1, "detail": "Tobin wore a green apron.", "gist": "Tobin wore one."}
    hazy(conn, world, **trivial, core_locked=True)
    got = recall(conn, world, "Tobin", log=False)
    assert [(r.tier, r.text) for r in got] == [("hazy", "Tobin wore one.")]
    mira = eid(conn, "Mira")
    assert [m["tier"] for m in retrieve.inspect(conn, world, mira)] == ["hazy"]
    off(conn)
    assert recall(conn, world, "Tobin", log=False) == []


def test_a_turn_recalls_with_her_mood_and_never_breaks_on_a_bad_state():
    from kataki import turns

    assert turns._mood_of({"mood": {"v": -0.4, "a": 0.2, "d": 0}}) == -0.4
    assert turns._mood_of(None) is turns._mood_of({"mood": {}}) is None
