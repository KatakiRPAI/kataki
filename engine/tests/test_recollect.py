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


# --- her version: a hazy detail drifts, with the truth kept ---------------------------------

THURSDAY = {"slot": "when", "right": "on Thursday", "wrong": "on Tuesday"}
DRIFTED = "Tobin spoke of turning on the guild, on Tuesday."


def test_how_often_a_detail_drifts_follows_the_dial_and_importance():
    assert recollect.drift_p(6, "faithful") == 0
    assert recollect.drift_p(6, "human") == pytest.approx(0.22)
    assert recollect.drift_p(6, "dreamlike") == pytest.approx(0.33)
    assert recollect.drift_p(1, "human") == pytest.approx(0.37)
    assert recollect.drift_p(0, "human") == 0.4 and recollect.drift_p(0, "dreamlike") == 0.6


@pytest.fixture
def always(monkeypatch):
    monkeypatch.setattr(recollect, "drift_p", lambda importance, dial: 1.0)


def rows(conn, table):
    return [dict(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY id")]


def test_a_hazy_detail_drifts_into_her_version_and_the_truth_is_kept(conn, world, always):
    memory = hazy(conn, world, alts=[THURSDAY])
    (got,) = recall(conn, world)
    assert got.text == DRIFTED and got.breakdown["drift"] == THURSDAY
    leaf = chat.active_path(conn, world)[-1]["id"]
    [mine] = rows(conn, "recollections")
    assert (mine["basis"], mine["text"], mine["memory_id"], mine["message_id"]) == (
        "alt", DRIFTED, memory, leaf
    )  # fmt: skip
    [fix] = rows(conn, "seeds")
    assert (fix["kind"], fix["text"], fix["memory_id"], fix["message_id"]) == (
        "correction", "it was on Thursday, not on Tuesday", memory, leaf
    )  # fmt: skip
    assert conn.execute("SELECT detail FROM memories").fetchone()[0] == DETAIL  # the truth
    assert recall(conn, world)[0].text == DRIFTED  # stable: her version now
    assert len(rows(conn, "recollections")) == len(rows(conn, "seeds")) == 1


@pytest.mark.parametrize(
    "extra",
    [{"core_locked": True}, {"importance": 8}, {}],
    ids=["locked", "canon", "sharp"],
)
def test_what_may_never_drift_never_does(conn, world, always, extra):
    if extra:
        hazy(conn, world, alts=[THURSDAY], **extra)
    else:  # fresh, so sharp
        extracted(conn, world, {"memories": [betrayal(conn, alts=[THURSDAY])]})
    assert "Tuesday" not in recall(conn, world)[0].text
    assert rows(conn, "recollections") == [] == rows(conn, "seeds")


def test_faithful_never_drifts_and_off_is_todays_recall(conn, world, always):
    hazy(conn, world, alts=[THURSDAY])
    conn.execute("INSERT INTO settings(key, value) VALUES('realism.memory', '\"faithful\"')")
    assert recall(conn, world)[0].text == GIST
    conn.execute("UPDATE settings SET value='\"human\"' WHERE key='realism.memory'")
    off(conn)
    assert recall(conn, world)[0].text == GIST
    assert rows(conn, "recollections") == []


def test_her_version_stays_on_its_branch(conn, world, always, monkeypatch):
    hazy(conn, world, alts=[THURSDAY])
    assert recall(conn, world)[0].text == DRIFTED
    monkeypatch.setattr(recollect, "drift_p", lambda importance, dial: 0.0)
    leaf = chat.active_path(conn, world)[-1]["id"]
    chat.append_sibling(conn, leaf, "Another take.")
    assert recall(conn, world)[0].text == GIST


def test_a_reading_never_writes(conn, world, always):
    hazy(conn, world, alts=[THURSDAY])
    assert recall(conn, world, log=False)[0].text == DRIFTED
    assert rows(conn, "recollections") == [] == rows(conn, "seeds")


# --- a retelling becomes her version, and travels -------------------------------------------


def claim(conn, detail, memory):
    return {
        "memories": [
            {
                "kind": "claim",
                "detail": detail,
                "gist": "Mira spoke of Tobin and the guild.",
                "participants": [{"ref": h(conn, "Tobin"), "role": "subject"}],
                "asserted_by": h(conn, "Mira"),
                "heard_by": [h(conn, "Aren")],
            }
        ],
        "contradictions": [
            {"claim": 0, "contradicts": f"M{memory}", "hearer": h(conn, "Aren"),
             "resolution": "accepted"}
        ],
    }  # fmt: skip


TOLD = "Tobin said he would turn on the guild at the mill."


def test_a_claim_against_her_own_hazy_memory_becomes_her_version(conn, world):
    memory = hazy(conn, world)
    extracted(conn, world, claim(conn, TOLD, memory))
    [mine] = rows(conn, "recollections")
    assert (mine["knower_id"], mine["memory_id"], mine["basis"], mine["text"]) == (
        eid(conn, "Mira"), memory, "retelling", TOLD
    )  # fmt: skip
    assert memory in [r.memory_id for r in recall(conn, world) if r.text == TOLD]


def test_a_claim_against_a_sharp_memory_stays_a_claim(conn, world):
    extracted(conn, world, {"memories": [betrayal(conn)]})
    memory = conn.execute("SELECT id FROM memories").fetchone()[0]
    extracted(conn, world, claim(conn, TOLD, memory))
    assert rows(conn, "recollections") == []


def test_telling_someone_passes_on_her_version(conn, world):
    memory = hazy(conn, world)
    extracted(conn, world, claim(conn, TOLD, memory))
    told = {"knower": h(conn, "Dara"), "memory": f"M{memory}", "source": "told",
            "told_by": h(conn, "Mira")}  # fmt: skip
    extracted(conn, world, {"knowledge": [told]})
    mira, dara = rows(conn, "recollections")
    assert (dara["knower_id"], dara["text"], dara["parent_id"], dara["basis"]) == (
        eid(conn, "Dara"), TOLD, mira["id"], "retelling"
    )  # fmt: skip


def test_a_pending_correction_is_never_offered_as_something_on_her_mind(conn, world, always):
    from kataki import between

    hazy(conn, world, alts=[THURSDAY])
    recall(conn, world)
    path = chat.active_path(conn, world)
    assert [s["kind"] for s in between.open_seeds(conn, eid(conn, "Mira"), path)] == ["correction"]
    assert between.on_mind(conn, world, eid(conn, "Mira"), path, "Aren") is None
