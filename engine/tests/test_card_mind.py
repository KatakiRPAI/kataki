"""The owner's night with the prince (2026-09-30): insulted, amused, flirted with, kissed, then
ignored, and the card still read 50/50/0. On the rules' reading (lite, or when the side call
can't run) none of it reached his mind. It must now, and Peek must show it with its reasons."""

import pytest

from kataki import inner, library, people, turns

LINES = [
    "You're an arrogant fool, and I don't care who your father is.",
    "Haha, you should see your face.",
    "*leans closer* You're rather handsome when you're not scowling.",
    "*kisses him*",
    "*walks past him without a word and talks to the guard instead*",
]


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Prince", "Me")}
    return library.create_story(conn, "Court", character_ids=[ids["Prince"]], persona_id=ids["Me"])


@pytest.mark.anyio
async def test_a_night_with_the_prince_moves_his_mind_and_peek_says_why(conn, story, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    conn.commit()
    for line in LINES:
        backend.say("Hm.")
        _ = [e async for e in turns.turn(conn, backend.llm, story, line)]
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    prince = people.people(conn, row)[0]
    events = {r[0] for r in conn.execute("SELECT event FROM opinions")}
    assert events == {"insult", "shared_joy", "flirt", "affection", "dismissal"}
    bond = prince["bonds"][0]
    assert bond["you"] and bond["attraction"] > 0 and bond["respect"] < 0 and bond["grudge"]
    assert [c["event"] for c in bond["recent"]][:2] == ["dismissal", "affection"]
    assert bond["recent"][1]["moves"]["closeness"] > 0  # "you kissed him: closeness +"
    felt = {e["label"] for e in prince["mood"]["emotions"]}
    assert "fond" in felt and felt & {"hurt", "annoyed", "angry"}


@pytest.mark.parametrize(
    ("line", "want"),
    [
        ("don't kiss me", "snub"),  # refusing touch rebuffs them; it is never affection
        ("Stop touching me.", "snub"),
        ("*pushes him away* Get off me!", "snub"),
        ("I'm not flirting with you.", None),
        ("You're not stupid.", None),
        ("I never said you were handsome", None),
        ("No, you're gorgeous.", "flirt"),  # the "no" is its own clause
        ("*kisses him*", "affection"),
        ("Don't move or else.", "threat"),  # threats ignore negation
    ],
)
def test_negation_and_refusal_in_the_rules(line, want):
    hit = inner.sense(line)
    assert (hit and hit[0]) == want


@pytest.mark.anyio
async def test_a_kiss_after_a_fresh_insult_crosses_a_line_on_lite(conn, story, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    conn.commit()
    for line in ("You're a pathetic, useless coward.", "*kisses him*"):
        backend.say("Hm.")
        _ = [e async for e in turns.turn(conn, backend.llm, story, line)]
    events = [r[0] for r in conn.execute("SELECT event FROM opinions ORDER BY id")]
    assert "affection" not in events and events[-1] == "boundary_crossed"
