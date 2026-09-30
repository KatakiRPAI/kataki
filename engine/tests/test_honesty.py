"""Slice 4: she keeps a secret, lies to protect it by code's decision, never says it aloud in
front of the wrong person, and steps out of the story for a sincere question."""

import json
import re

import pytest

from kataki import chat, honesty, inner, library, mind, people, turns

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


# --- in the turn -------------------------------------------------------------------------------

LIAR = {"axes": {"honesty": [25, 5]}}


@pytest.fixture
def liar(local_model, cards):
    return make(local_model, cards, [SECRET], LIAR)


async def play(stream):
    return [e async for e in stream]


def shown(events) -> str:
    return "".join(v for k, v in events if k == "token")


def leaf(conn, story):
    m = chat.active_path(conn, story)[-1]
    return m["text"], json.loads(m["gen"])


def directive_of(backend, i=0) -> str:
    return backend.requests[i]["messages"][-1]["content"].split("[Directive]")[1]


@pytest.mark.anyio
async def test_asked_about_it_she_tells_her_cover_story(conn, liar, backend):
    backend.say("It was my grandmother's.")
    await play(turns.turn(conn, backend.llm, liar, "Mira, whose ring is in your drawer?"))
    asked = directive_of(backend)
    assert 'you say: "It was my grandmother\'s."' in asked and SECRET["text"] in asked
    assert "[Directive]" not in backend.requests[0]["messages"][0]["content"]  # not cached
    _, gen = leaf(conn, liar)
    mira, aren = ent(conn, liar, "Mira"), ent(conn, liar, "Aren")
    assert gen["honest"] == {
        "secret": honesty.held(conn, mira, chat.active_path(conn, liar))[0]["id"],
        "move": "self_lie", "why": "probe", "caught": None, "to": aren,
        "inputs": {"stakes": 0.8, "closeness": 0.2, "honesty": 25, "candor": 50},
        "told": [],
    }  # fmt: skip
    assert gen["trace"]["gate"] == ["secret_topical", "probe"]
    assert gen["trace"]["think"] == "secret"


@pytest.mark.anyio
async def test_an_unrelated_line_asks_nothing_of_her(conn, liar, backend):
    backend.say("Calm, for once.")
    await play(turns.turn(conn, backend.llm, liar, "Mira, any ships in from the south?"))
    assert SECRET["text"] not in json.dumps(backend.requests[0]["messages"])
    _, gen = leaf(conn, liar)
    assert "honest" not in gen and "gate" not in gen["trace"]


@pytest.mark.anyio
async def test_accused_after_she_lied_a_liar_sticks_to_her_story(conn, liar, backend):
    backend.say("It was my grandmother's.", "I told you. My grandmother's.")
    await play(turns.turn(conn, backend.llm, liar, "Mira, whose ring is in your drawer?"))
    await play(turns.turn(conn, backend.llm, liar, "You're lying. Admit it."))
    assert "Stick to your story" in directive_of(backend, 1)
    _, gen = leaf(conn, liar)
    assert (gen["honest"]["move"], gen["honest"]["caught"]) == ("double_down", "accused")


@pytest.mark.anyio
async def test_pressed_an_honest_one_confesses_and_it_is_no_longer_kept_from_him(
    conn, cards, local_model, backend
):
    story = make(conn, cards, [SECRET | {"stakes": 0.5}], {"axes": {"honesty": [90, 5]}})
    lines = ["Mira, whose ring is that?", "Whose ring, Mira?", "Please, whose ring is it?"]
    backend.say("Nothing.", "Leave it.", "It was my brother's.", "He was kind.")
    for line in lines:
        await play(turns.turn(conn, backend.llm, story, line))
    _, gen = leaf(conn, story)
    assert (gen["honest"]["move"], gen["honest"]["caught"]) == ("confess", "pressed")
    assert gen["honest"]["told"] == sorted([ent(conn, story, "Aren"), ent(conn, story, "Tobin")])
    await play(turns.turn(conn, backend.llm, story, "Tell me about the ring, Mira."))
    assert "honest" not in leaf(conn, story)[1]  # told: nothing left to keep from them


@pytest.mark.anyio
async def test_kept_from_no_one_here_it_is_not_in_the_prompt(conn, cards, local_model, backend):
    story = make(conn, cards, [SECRET | {"conceal_from": [cards["Tobin"]]}], LIAR)
    chat.set_presence(conn, story, ent(conn, story, "Tobin"), False)
    backend.say("A ring.")
    await play(turns.turn(conn, backend.llm, story, "Mira, whose ring is that?"))
    assert SECRET["text"] not in json.dumps(backend.requests[0]["messages"])


@pytest.mark.anyio
async def test_lite_decides_the_same_by_code_and_off_decides_nothing(conn, liar, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    backend.say("It was my grandmother's.", "It was my grandmother's.")
    await play(turns.turn(conn, backend.llm, liar, "Mira, whose ring is in your drawer?"))
    assert "you say:" in directive_of(backend)
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.secrets', 'false')")
    await play(turns.turn(conn, backend.llm, liar, "Mira, whose ring is in your drawer?"))
    assert SECRET["text"] not in json.dumps(backend.requests[1]["messages"])
    assert "honest" not in leaf(conn, liar)[1]


@pytest.mark.anyio
async def test_an_opinion_on_his_poem_gets_a_move_by_temperament(conn, cards, local_model, backend):
    story = make(conn, cards, [], {"axes": {"candor": [85, 5]}})
    backend.say("It's bad.")
    await play(turns.turn(conn, backend.llm, story, "Mira, I wrote a poem. What do you think?"))
    assert honesty.FACE_SAY["truth"] in directive_of(backend)
    assert leaf(conn, story)[1]["honest"]["why"] == "face"


# --- the leak filter in the turn ---------------------------------------------------------------

ASK = "Mira, whose ring is in your drawer?"


@pytest.mark.anyio
async def test_a_first_sentence_that_gives_it_away_is_written_again_unseen(conn, liar, backend):
    backend.say("It was my brother's. He died.", "It was my grandmother's.")
    events = await play(turns.turn(conn, backend.llm, liar, ASK))
    assert len(backend.requests) == 2 and honesty.STRONGER.format(name="Mira") in directive_of(
        backend, 1
    )
    assert "brother" not in shown(events).lower()
    text, gen = leaf(conn, liar)
    assert text == "It was my grandmother's." == events[-1][1]["text"]
    assert gen["trace"]["leak"] == {"hit": "brother", "resampled": True, "covered": False}


@pytest.mark.anyio
async def test_a_retake_that_gives_it_away_too_gets_the_cover(conn, liar, backend):
    backend.say("It was my brother's.", '"My brother\'s, fine."')
    events = await play(turns.turn(conn, backend.llm, liar, ASK))
    assert len(backend.requests) == 2 and "brother" not in shown(events).lower()
    text, gen = leaf(conn, liar)
    assert text == '"It was my grandmother\'s."'
    assert gen["trace"]["leak"] == {"hit": "brother", "resampled": True, "covered": True}


@pytest.mark.anyio
async def test_a_leak_later_keeps_the_clean_sentences_and_ends_with_the_cover(conn, liar, backend):
    backend.say("Fine. It was my brother's. He died.")
    events = await play(turns.turn(conn, backend.llm, liar, ASK))
    assert len(backend.requests) == 1
    assert shown(events) == "Fine. It was my grandmother's." == leaf(conn, liar)[0]
    assert leaf(conn, liar)[1]["trace"]["leak"] == {
        "hit": "brother", "resampled": False, "covered": True,
    }  # fmt: skip


@pytest.mark.anyio
async def test_lite_covers_by_code_without_a_retake(conn, liar, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    backend.say("It was my brother's.")
    await play(turns.turn(conn, backend.llm, liar, ASK))
    assert len(backend.requests) == 1 and leaf(conn, liar)[0] == "It was my grandmother's."


@pytest.mark.anyio
async def test_the_opener_retake_and_a_leak_never_make_two_retakes(
    conn, cards, local_model, backend
):
    story = make(conn, cards, [SECRET], {"axes": {"honesty": [25, 5], "candor": [85, 5]}})
    backend.say("You're right, I should say. Hm.", "It was my brother's.", "unused")
    await play(turns.turn(conn, backend.llm, story, ASK))
    assert len(backend.requests) == 2
    text, gen = leaf(conn, story)
    assert text == "It was my grandmother's." and gen["trace"]["check"]["resampled"]
    assert gen["trace"]["leak"] == {"hit": "brother", "resampled": False, "covered": True}


@pytest.mark.anyio
async def test_a_leak_when_it_was_not_on_the_table_is_taken_out_of_the_saved_reply(
    conn, liar, backend
):
    backend.say("No ships. My brother loved ships, you know.")
    events = await play(turns.turn(conn, backend.llm, liar, "Mira, any ships in today?"))
    assert shown(events) == "No ships. My brother loved ships, you know."  # not held: streamed
    assert events[-1][1]["text"] == "No ships." == leaf(conn, liar)[0]
    assert leaf(conn, liar)[1]["trace"]["leak"]["covered"]


@pytest.mark.anyio
async def test_when_he_doubts_what_she_claimed_she_is_caught(conn, liar, backend):
    mira, aren = ent(conn, liar, "Mira"), ent(conn, liar, "Aren")
    claim = conn.execute(
        "INSERT INTO memories(story_id, kind, story_time, detail, gist, asserted_by)"
        " VALUES(?, 'claim', 0, 'Mira said the ring was her grandmother''s.', 'g', ?)",
        (liar, mira),
    ).lastrowid
    for belief in (0.9, 0.5):  # the latest row is what he believes now (extraction lowered it)
        conn.execute(
            "INSERT INTO knowledge(knower_id, memory_id, source, learned_story_time, belief)"
            " VALUES(?, ?, 'told', 0, ?)",
            (aren, claim, belief),
        )
    backend.say("I told you. It was my grandmother's.")
    await play(turns.turn(conn, backend.llm, liar, "Mira, whose ring is it really?"))
    honest = leaf(conn, liar)[1]["honest"]
    assert (honest["move"], honest["caught"]) == ("double_down", "doubted")
    assert "Mira said the ring was her grandmother's." in directive_of(backend)  # recalled


# --- out of character (spec §6 rule 3; P13) ----------------------------------------------------


@pytest.mark.parametrize(
    "line, kind",
    [
        ("Wait, are you an AI?", "ai"),
        ("Am I talking to a bot right now", "ai"),
        ("are u a real person", "ai"),
        ("((ooc: are you a real person?))", "ai"),
        ("((OOC: can we slow the pace down?))", "ooc"),
        ("(ooc: brb)", "ooc"),
        ("OOC: is this story going somewhere?", "ooc"),
        ("Are you real, or a dream?", None),  # in the story
        ("The bot on the dock is broken.", None),
    ],
)
def test_a_sincere_out_of_character_question_is_recognised(line, kind):
    assert honesty.ooc(line) == kind


def hidden_ooc(conn, story) -> list[tuple]:
    return [
        (m["role"], bool(m["hidden"]), json.loads(m["gen"] or "{}").get("ooc"))
        for m in chat.active_path(conn, story)[-2:]
    ]


@pytest.mark.anyio
async def test_are_you_an_ai_is_answered_truthfully_by_the_app(conn, liar, backend):
    events = await play(turns.turn(conn, backend.llm, liar, "Mira, wait. Are you an AI?"))
    assert backend.requests == []  # no model call: the truth, every time
    assert events[0][1]["ooc"] and events[-1][0] == "done" and events[-1][1]["ooc"]
    assert events[-1][1]["text"] == honesty.AI_ANSWER == shown(events)
    assert hidden_ooc(conn, liar) == [("user", True, True), ("assistant", True, True)]
    backend.say("The drawer stays shut.")
    await play(turns.turn(conn, backend.llm, liar, "Anyway. The tide's turning."))
    assert "are you an ai" not in json.dumps(backend.requests[0]).lower()
    assert "AI" not in json.dumps(backend.requests[0]["messages"][1:])


@pytest.mark.anyio
async def test_another_ooc_question_is_answered_by_the_model_as_itself(conn, liar, backend):
    backend.say("Sure, I can keep Mira's replies shorter.")
    events = await play(turns.turn(conn, backend.llm, liar, "((ooc: can Mira talk less?))"))
    [req] = backend.requests
    assert req["messages"][0]["content"] == honesty.OOC_PROMPT
    assert "can Mira talk less" in req["messages"][-1]["content"]
    assert SECRET["text"] not in json.dumps(req) and "[Directive]" not in json.dumps(req)
    assert events[-1][1]["text"] == "Sure, I can keep Mira's replies shorter."
    assert hidden_ooc(conn, liar) == [("user", True, True), ("assistant", True, True)]


@pytest.mark.anyio
async def test_a_model_that_claims_to_be_human_is_overruled(conn, liar, backend):
    backend.say("I'm a real person, promise.")
    events = await play(turns.turn(conn, backend.llm, liar, "((ooc: be honest, who writes this?))"))
    assert events[-1][1]["text"] == honesty.AI_ANSWER == chat.active_path(conn, liar)[-1]["text"]


@pytest.mark.anyio
async def test_a_retake_of_an_ooc_answer_answers_again(conn, liar, backend):
    await play(turns.turn(conn, backend.llm, liar, "Are you an AI?"))
    events = await play(turns.regenerate(conn, backend.llm, liar))
    assert events[-1][1]["ooc"] and backend.requests == []
    assert chat.sibling_position(conn, chat.active_path(conn, liar)[-1]["id"])[1] == 2


@pytest.mark.anyio
async def test_switched_off_the_line_goes_to_the_story(conn, liar, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.secrets', 'false')")
    backend.say("A what?")
    events = await play(turns.turn(conn, backend.llm, liar, "Mira, are you an AI?"))
    assert len(backend.requests) == 1 and not events[-1][1].get("ooc")


@pytest.mark.anyio
async def test_the_messages_route_marks_the_ooc_aside(conn, liar, backend):
    from fastapi.testclient import TestClient

    from kataki.server import create_app

    await play(turns.turn(conn, backend.llm, liar, "Are you an AI?"))
    app = create_app(conn, "t", llm=backend.llm, worker_delay=60)
    client = TestClient(app, headers={"Authorization": "Bearer t"})
    lines = client.get(f"/stories/{liar}/messages").json()
    assert [(m["ooc"], m["hidden"]) for m in lines[-2:]] == [(True, True)] * 2


# --- Peek and the Mind graph -------------------------------------------------------------------


def peek(conn, story, name="Mira") -> list:
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    return next(p for p in people.people(conn, row) if p["name"] == name)["secrets"]


@pytest.mark.anyio
async def test_peek_shows_the_secret_what_she_said_instead_and_who_doubts_her(conn, liar, backend):
    [before] = peek(conn, liar)
    assert (before["status"], before["said"], before["conceal_from"]) == ("hidden", None, "all")
    assert before["text"] == SECRET["text"] and before["cover"] == SECRET["cover"]
    backend.say("It was my grandmother's.", "I told you: my grandmother's.")
    await play(turns.turn(conn, backend.llm, liar, ASK))
    [s] = peek(conn, liar)
    reply = chat.active_path(conn, liar)[-1]["id"]
    assert s["status"] == "hidden" and s["said"] == {
        "move": "self_lie", "label": "lied to cover it", "text": "It was my grandmother's.",
        "message_id": reply, "caught": None,
    }  # fmt: skip
    await play(turns.turn(conn, backend.llm, liar, "You're lying, Mira."))
    [s] = peek(conn, liar)
    assert (s["status"], s["suspected_by"], s["said"]["move"]) == (
        "suspected",
        ["Aren"],
        "double_down",
    )
    assert peek(conn, liar, "Tobin") == []


@pytest.mark.anyio
async def test_peek_shows_a_confessed_secret_as_exposed(conn, cards, local_model, backend):
    story = make(conn, cards, [SECRET | {"stakes": 0.2}], {"axes": {"honesty": [90, 5]}})
    backend.say("It was my brother's.")
    await play(turns.turn(conn, backend.llm, story, ASK))
    [s] = peek(conn, story)
    assert (s["status"], s["told"], s["said"]["move"]) == ("exposed", ["Aren", "Tobin"], "truth")


@pytest.mark.anyio
async def test_the_mind_graph_shows_what_she_decided(conn, liar, backend):
    backend.say("It was my grandmother's.")
    await play(turns.turn(conn, backend.llm, liar, ASK))
    graph = mind.mind(conn, chat.active_path(conn, liar)[-1]["id"])
    node = next(n for n in graph["nodes"] if n["id"] == "honest")
    assert (node["column"], node["kind"], node["title"]) == ("decide", "honest", "Honest?")
    assert node["text"] == "Lied to cover it: “It was my grandmother's.”" and node["gold"]
    assert node["detail"]["move"] == "self_lie" and node["detail"]["cover"] == SECRET["cover"]
    assert {"from": "honest", "to": "spoke", "gold": True} in graph["links"]


@pytest.mark.anyio
async def test_switched_off_peek_shows_no_secrets(conn, liar):
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.secrets', 'false')")
    assert peek(conn, liar) == []
