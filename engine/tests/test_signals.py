"""What each line signals: who heard it, how clearly they will remember it, what a reply
recalled. A small ledger scene: Aren tells Mira a secret while Tobin is at the bar."""

import pytest

from kataki import chat, extract, library, signals, turns

DETAIL = "Aren hid the guild ledger under the third floorboard behind the bar."
GIST = "Aren hid the guild ledger somewhere behind the bar."


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {name: library.create_item(conn, "character", name) for name in ("Mira", "Tobin", "Aren")}
    gull = library.create_item(conn, "place", "The Gull")
    return library.create_story(
        conn, "Low Tide", character_ids=[ids["Mira"], ids["Tobin"]], place_id=gull,
        persona_id=ids["Aren"],
    )  # fmt: skip


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


def line(conn, story, text, who="Aren", audience=None):
    role = "user" if who == "Aren" else "assistant"
    return chat.append_message(conn, story, role, text, eid(conn, who), audience=audience)


def read(conn, story, first, last, memories):
    run_id = extract.open_run(conn, story, first, last, "cadence")
    extract.apply(conn, run_id, {"memories": memories})


def ledger(conn, at_line, importance=9):
    return {
        "kind": "event", "detail": DETAIL, "gist": GIST, "importance": importance,
        "line": at_line,
        "participants": [
            {"ref": f"E{eid(conn, 'Aren')}", "role": "actor"},
            {"ref": f"E{eid(conn, 'Mira')}", "role": "target"},
        ],
    }  # fmt: skip


def test_receipts_go_from_heard_to_remembered_once_memory_reads_the_line(conn, story):
    mira, tobin = eid(conn, "Mira"), eid(conn, "Tobin")
    evening = line(conn, story, "Evening, both of you.")
    chat.set_presence(conn, story, tobin, False)  # sent to the bar
    secret = line(conn, story, "Quickly: the ledger is under the third floorboard.")
    reply = line(conn, story, "*nods* Safe with me.", who="Mira")

    before = signals.signals(conn, story)
    assert before["read_to"] == 0
    assert before["lines"][secret]["receipts"] == [
        {"id": mira, "state": "heard", "pending": True},
        {"id": tobin, "state": "absent", "why": "away"},
    ]
    assert before["lines"][secret]["summary"] == "Heard by Mira · Tobin wasn't there"

    read(conn, story, evening, reply, [ledger(conn, at_line=2)])
    after = signals.signals(conn, story)
    assert after["read_to"] == reply
    assert after["lines"][secret]["receipts"][0] == {"id": mira, "state": "sharp"}
    assert after["lines"][secret]["summary"] == "Mira will remember · Tobin wasn't there"
    # nothing was filed from the greeting: heard, no dots
    assert after["lines"][evening]["receipts"] == [
        {"id": mira, "state": "heard"},
        {"id": tobin, "state": "heard"},
    ]
    # absent only on your own lines
    assert after["lines"][reply]["receipts"] == [{"id": mira, "state": "heard"}]


def test_a_whisper_leaves_whoever_it_was_not_for_absent_and_says_why(conn, story):
    mira, tobin = eid(conn, "Mira"), eid(conn, "Tobin")
    line(conn, story, "Evening.")
    whisper = line(conn, story, "Psst. Not a word to Tobin.", audience=[mira])
    thought = line(conn, story, "I hope she keeps it.", audience=[])
    lines = signals.signals(conn, story)["lines"]
    assert {"id": tobin, "state": "absent", "why": "whisper"} in lines[whisper]["receipts"]
    assert thought not in lines  # a thought is heard by no one, and nobody missed it


def test_no_one_is_absent_from_a_line_before_they_ever_heard_the_scene(conn, story):
    chat.set_presence(conn, story, eid(conn, "Tobin"), False)
    first = line(conn, story, "Just us, then.")
    assert signals.signals(conn, story)["lines"][first]["receipts"] == [
        {"id": eid(conn, "Mira"), "state": "heard", "pending": True}
    ]


@pytest.mark.anyio
async def test_the_reply_after_six_years_says_what_she_recalled_and_how(conn, story, backend):
    mira = eid(conn, "Mira")
    told = line(conn, story, "The ledger is under the third floorboard, behind the bar.")
    nod = line(conn, story, "*nods*", who="Mira")
    read(conn, story, told, nod, [ledger(conn, at_line=1)])
    memory_id = conn.execute("SELECT id FROM memories").fetchone()["id"]
    turns.say(conn, story, skip="six years later")
    backend.say("The ledger? Behind the bar... somewhere.")
    [e async for e in turns.turn(conn, backend.llm, story, "Mira, where is the ledger?", mira)]

    reply = chat.active_path(conn, story)[-1]["id"]
    recall = signals.signals(conn, story)["lines"][reply]["recall"]
    assert recall["speaker"] == mira
    assert recall["title"] == "Mira remembered, vaguely"
    [item] = recall["items"]
    assert (item["memory_id"], item["tier"], item["text"], item["detail"]) == (
        memory_id, "hazy", GIST, DETAIL,
    )  # fmt: skip
    assert item["how"] == "witnessed Day 1, 08:02"
