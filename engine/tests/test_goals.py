"""Slice 7: she wants something. The card's want becomes a goal she brings up at an opening, drops
when it is dodged twice and raises again later; her needs and energy show as behaviour."""

import json

import pytest

from kataki import chat, goals, library

BOAT = {"text": "to get Aren to come and see the boat she built", "cue": ["boat", "sail"]}


@pytest.fixture
def cards(conn):
    return {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}


def make(conn, cards, mira: dict | None = None) -> int:
    library.update_item(conn, cards["Mira"], data={"mind": mira or {}})
    return library.create_story(
        conn, "Low Tide", character_ids=[cards["Mira"], cards["Tobin"]], persona_id=cards["Aren"]
    )


def ent(conn, story: int, name: str) -> int:
    return conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name=?", (story, name)
    ).fetchone()[0]


def line(conn, story: int, who: str, text: str, skip: int = 0, gen: dict | None = None) -> int:
    role = "user" if who == "Aren" else "assistant"
    mid = chat.append_message(conn, story, role, text, ent(conn, story, who), skip)
    if gen is not None:
        with conn:
            conn.execute("UPDATE messages SET gen=? WHERE id=?", (json.dumps(gen), mid))
    return mid


def path(conn, story: int) -> list:
    return chat.active_path(conn, story)


# --- goals from the card -------------------------------------------------------------------------


def test_want_need_fear_and_listed_goals_become_her_goals(conn, cards):
    story = make(
        conn,
        cards,
        {
            "want": BOAT,
            "need": "to let someone help her",
            "fear": "being left behind",
            "goals": [
                {"text": "save for a bigger workshop", "tier": "ambition", "priority": 0.4},
                "junk",
                {"text": " "},
                {"text": "fix the pier", "tier": "someday", "priority": "high"},
            ],
        },
    )
    mira = ent(conn, story, "Mira")
    got = {g["key"]: g for g in goals.live(conn, mira, path(conn, story))}
    assert set(got) == {"want", "need", "fear", "g1", "g2"}
    assert got["want"]["status"] == "active" and got["want"]["cue"] == ["boat", "sail"]
    assert got["want"]["tier"] == "project"
    assert got["need"]["status"] == got["fear"]["status"] == "dormant"  # never pursued
    assert got["g1"]["tier"] == "ambition" and got["g1"]["priority"] == 0.4
    assert got["g2"]["tier"] == "project" and got["g2"]["priority"] == 0.5  # bad values: defaults
    assert got["g1"]["cue"] == ["save", "bigger", "workshop"]  # its own words, when none given
    assert all(g["message_id"] is None and g["run_id"] is None for g in got.values())
    tobin = ent(conn, story, "Tobin")
    assert goals.live(conn, tobin, path(conn, story)) == []


def test_a_malformed_card_never_breaks_the_story(conn, cards):
    story = make(conn, cards, {"want": 7, "need": ["x"], "goals": {"text": "x"}})
    assert goals.live(conn, ent(conn, story, "Mira"), path(conn, story)) == []


def test_cue_words_leave_out_small_words_and_names():
    assert goals.cues("to get Aren to come and see the boat she built", {"aren"}) == [
        "boat",
        "built",
    ]
    assert goals.cues("I want THE harbour-master's job!") == ["harbour", "master", "job"]


def test_the_latest_version_on_this_branch_is_the_goal(conn, cards):
    story = make(conn, cards, {"want": BOAT})
    mira = ent(conn, story, "Mira")
    root = line(conn, story, "Aren", "Morning.")
    here = line(conn, story, "Mira", "Morning!")
    first = goals.live(conn, mira, path(conn, story))[0]
    now = path(conn, story)[-1]["story_time"]
    goals.write(conn, first, here, None, now, status="dormant", deflections=2)
    assert goals.live(conn, mira, path(conn, story))[0]["status"] == "dormant"
    other = chat.add_child(conn, story, root, "assistant", "Hi.", mira, 0, {})
    chat.set_leaf(conn, story, other)
    assert goals.live(conn, mira, path(conn, story))[0]["status"] == "active"


def test_merged_people_keep_their_goals(conn, cards):
    story = make(conn, cards, {"want": BOAT})
    mira, tobin = ent(conn, story, "Mira"), ent(conn, story, "Tobin")
    library.merge_entities(conn, tobin, mira)
    assert [g["key"] for g in goals.live(conn, tobin, path(conn, story))] == ["want"]
