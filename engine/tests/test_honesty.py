"""Slice 4: she keeps a secret, lies to protect it by code's decision, never says it aloud in
front of the wrong person, and steps out of the story for a sincere question."""

import pytest

from kataki import chat, honesty, library

SECRET = {
    "text": "The ring in the drawer was her late brother's.",
    "keys": ["brother"],
    "topic": ["ring", "drawer"],
    "cover": "It was my grandmother's.",
    "stakes": 0.8,
    "motive": "protect_self",
}


@pytest.fixture
def cards(conn):
    return {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}


def make(conn, cards, secrets, mind: dict | None = None) -> int:
    library.update_item(conn, cards["Mira"], data={"mind": {"secrets": secrets, **(mind or {})}})
    return library.create_story(
        conn, "Low Tide", character_ids=[cards["Mira"], cards["Tobin"]], persona_id=cards["Aren"]
    )


def ent(conn, story: int, name: str) -> int:
    return conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name=?", (story, name)
    ).fetchone()[0]


# --- secrets in a story ------------------------------------------------------------------------


def test_a_cards_secret_lands_in_the_story(conn, cards):
    story = make(conn, cards, [SECRET | {"conceal_from": [cards["Aren"]]}, {"text": " "}, "junk"])
    mira = ent(conn, story, "Mira")
    [got] = honesty.held(conn, mira, chat.active_path(conn, story))
    assert got["conceal_from"] == [ent(conn, story, "Aren")]
    assert (got["keys"], got["topic"], got["cover"]) == (
        ["brother"],
        ["ring", "drawer"],
        SECRET["cover"],
    )
    assert (got["stakes"], got["motive"], got["sincere"]) == (0.8, "protect_self", False)
    assert honesty.held(conn, ent(conn, story, "Tobin"), chat.active_path(conn, story)) == []


def test_a_secret_kept_from_everyone_by_default_and_odd_values_are_tamed(conn, cards):
    story = make(conn, cards, [{"text": "She can't swim.", "stakes": 7, "motive": "spite"}])
    [got] = honesty.held(conn, ent(conn, story, "Mira"), chat.active_path(conn, story))
    assert got["conceal_from"] == "all" and got["stakes"] == 1.0 and got["motive"] is None
    assert got["keys"] == [] and got["cover"] is None


def test_the_topic_is_its_topic_words_keys_and_cover():
    sec = {"keys": ["brother"], "topic": ["ring"], "cover": "It was my grandmother's."}
    assert honesty.topical(sec, "Whose ring is that?")
    assert honesty.topical(sec, "Was it your BROTHER'S, then?")
    assert honesty.topical(sec, "Your grandmother, you said?")
    assert honesty.topical(sec, "Those rings in the drawer.")
    assert not honesty.topical(sec, "Any ships in from the south?")
    assert not honesty.topical({"keys": [], "topic": [], "cover": None}, "ring")


def test_questions_and_accusations():
    assert honesty.question("Whose ring is that") and honesty.question("It's yours?")
    assert honesty.question("Tell me who gave it to you.")
    assert not honesty.question("Nice ring.")
    assert honesty.ACCUSE.search("You're lying. Admit it.")
    assert honesty.ACCUSE.search("Tobin told me it was your brother's.")
    assert not honesty.ACCUSE.search("Nice ring.")
