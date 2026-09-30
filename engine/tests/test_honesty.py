"""Slice 4: she keeps a secret, lies to protect it by code's decision, never says it aloud in
front of the wrong person, and steps out of the story for a sincere question."""

import re

import pytest

from kataki import chat, honesty, inner, library

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


# --- the move and the directive ----------------------------------------------------------------


def prof(honesty=60, candor=50, warmth=50) -> dict:
    return {"axes": {"honesty": [honesty, 5], "candor": [candor, 5], "warmth": [warmth, 5]}}


SEC = {"text": SECRET["text"], "keys": ["brother"], "topic": ["ring"], "cover": SECRET["cover"],
       "stakes": 0.8, "motive": "protect_self", "sincere": False}  # fmt: skip


@pytest.mark.parametrize(
    "sec, who, close, probed, caught, move",
    [
        (SEC, prof(25), 0.2, True, None, "self_lie"),  # a liar, asked: the cover
        (SEC | {"motive": "kindness"}, prof(25), 0.2, True, None, "white_lie"),
        (SEC | {"cover": None}, prof(25), 0.2, True, None, "deflect"),  # nothing to lie with
        (SEC | {"stakes": 0.4}, prof(90), 0.2, True, None, "deflect"),  # honest: no lie
        (SEC | {"stakes": 0.4}, prof(90, candor=80), 0.2, True, None, "evade"),  # and blunt
        (SEC | {"stakes": 0.2}, prof(80), 0.2, True, None, "truth"),  # little to lose
        (SEC, prof(25), 0.2, False, None, "omit"),  # on the table, not asked
        (SEC | {"stakes": 0.3}, prof(60, candor=80), 0.2, False, None, "hint"),
        (SEC, prof(25), 0.2, True, "accused", "double_down"),
        (SEC | {"stakes": 0.5}, prof(90), 0.4, True, "accused", "confess"),
        (SEC | {"sincere": True}, prof(25), 0.2, True, "accused", "truth"),  # as she believes it
    ],
)
def test_code_decides_the_move(sec, who, close, probed, caught, move):
    assert honesty.decide(sec, inner.shape(who), close, probed, caught) == move


@pytest.mark.parametrize(
    "who, close, move",
    [
        (prof(candor=85), 0.2, "truth"),
        (prof(honesty=30, warmth=80), 0.2, "white_lie"),
        (prof(warmth=80), 0.2, "soften"),
        (prof(), 0.7, "soften"),
        (prof(), 0.2, "hedge"),
    ],
)
def test_an_opinion_on_their_work_is_answered_by_temperament(who, close, move):
    assert honesty.face_move(inner.shape(who), close) == move


def test_a_face_threat_is_an_opinion_asked_on_the_users_own_work():
    assert honesty.FACE.search("I wrote a poem. Be honest, what do you think?")
    assert honesty.FACE.search("Do you like my new coat?")
    assert not honesty.FACE.search("What do you think the weather will do?")


def test_the_lie_gives_the_cover_and_what_she_said_before_in_words():
    said = ["Mira said the ring was her grandmother's, from Porthleven."]
    line = honesty.directive(SEC, "self_lie", "Aren", said, None)
    assert SEC["text"] in line and 'you say: "It was my grandmother\'s."' in line
    assert said[0] in line and "to protect yourself" in line
    assert not re.search(r"\d", line)


@pytest.mark.parametrize("move", [m for m in honesty.MOVES if m != "exaggerate"])
def test_every_move_has_words_and_no_numbers(move):
    line = honesty.directive(SEC, move, "Aren", [], "accused")
    assert line and not re.search(r"\d", line)
    if move == "omit":  # not asked: the truth stays out of the prompt
        assert SEC["text"] not in line


def test_a_sincere_secret_never_puts_the_truth_in_the_prompt():
    line = honesty.directive(SEC | {"sincere": True}, "truth", "Aren", [], None)
    assert SEC["text"] not in line and SEC["cover"] in line


def test_her_earlier_claims_on_the_topic_are_recalled(conn, cards):
    story = make(conn, cards, [SECRET])
    mira = ent(conn, story, "Mira")
    for t, detail in [(5, "Mira said the ring was her grandmother's."), (6, "Mira said it rained."),
                      (7, "Mira said the ring came from Porthleven.")]:  # fmt: skip
        conn.execute(
            "INSERT INTO memories(story_id, kind, story_time, detail, gist, asserted_by)"
            " VALUES(?, 'claim', ?, ?, 'g', ?)",
            (story, t, detail, mira),
        )
    [sec] = honesty.held(conn, mira, chat.active_path(conn, story))
    assert honesty.claims(conn, story, mira, sec, chat.active_path(conn, story)) == [
        "Mira said the ring was her grandmother's.",
        "Mira said the ring came from Porthleven.",
    ]


# --- the leak check ----------------------------------------------------------------------------

GUARDS = [(["brother"], "It was my grandmother's.")]


def test_a_key_said_aloud_is_a_leak_in_any_case_or_number():
    assert honesty.leak("It was my Brother's.", ["brother"]) == "brother"
    assert honesty.leak("My brothers never knew.", ["brother"]) == "brother"
    assert honesty.leak("Brotherhood of the tide.", ["brother"]) is None
    assert honesty.leak("anything", []) is None


def test_scrub_puts_the_cover_where_the_leak_began_and_ends_there():
    text = '*She looks away.* "Fine. It was my brother\'s. He died in spring."'
    assert honesty.scrub(text, GUARDS) == (
        '*She looks away.* "Fine. It was my grandmother\'s."',
        "brother",
    )
    assert honesty.scrub("Nothing here.", GUARDS) == ("Nothing here.", None)
    assert honesty.scrub("It was my brother's.", [(["brother"], None)]) == ("…", "brother")


def feed(guard, *chunks):
    return "".join(guard.feed(c) for c in chunks) + guard.flush()


def test_the_guard_lets_clean_sentences_through_as_they_end():
    g = honesty.Guard(GUARDS)
    assert g.feed("It's an old") == ""
    assert g.feed(" ring. Why") == "It's an old ring. "
    assert g.feed(" ask?") == ""
    assert g.flush() == "Why ask?" and g.hit is None


def test_a_leak_in_the_first_sentence_shows_nothing():
    g = honesty.Guard(GUARDS)
    assert feed(g, "It was my bro", "ther's, if you must know. More.") == ""
    assert (g.hit, g.shown, g.cover) == ("brother", False, GUARDS[0][1])


def test_a_later_leak_keeps_what_came_before_it():
    g = honesty.Guard(GUARDS)
    assert feed(g, "Fine.\n", "It was my brother's. He died.") == "Fine.\n"
    assert g.hit == "brother" and g.shown


def test_no_guards_hold_nothing():
    g = honesty.Guard([([], "x")])
    assert g.feed("It was my brother") == "It was my brother" and g.hit is None


def test_the_cover_is_quoted_like_the_reply():
    assert honesty.scrub("*Shrugs.* It was my brother's.", GUARDS)[0] == (
        "*Shrugs.* It was my grandmother's."
    )
    assert honesty.scrub("*Shrugs.* “Mine.” “It was my brother's.”", GUARDS)[0] == (
        "*Shrugs.* “Mine.” “It was my grandmother's.”"
    )
