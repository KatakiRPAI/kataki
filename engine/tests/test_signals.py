"""What each line signals: who heard it, how clearly they will remember it, what a reply
recalled. A small ledger scene: Aren tells Mira a secret while Tobin is at the bar."""

import pytest

from kataki import chat, extract, library, signals, turns

DETAIL = "Aren hid the guild ledger under the third floorboard behind the bar."
GIST = "Aren hid the guild ledger somewhere behind the bar."


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {
        name: library.create_item(conn, "character", name, data={"pronouns": pronouns})
        for name, pronouns in (("Mira", "she"), ("Tobin", "he"), ("Aren", "he"))
    }
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


def read(conn, story, first, last, memories, **more):
    run_id = extract.open_run(conn, story, first, last, "cadence")
    extract.apply(conn, run_id, {"memories": memories, **more})


def memory_id(conn, detail):
    return conn.execute("SELECT id FROM memories WHERE detail=?", (detail,)).fetchone()["id"]


def event(conn, detail, importance, at_line, target="Mira"):
    return {
        "kind": "event", "detail": detail, "gist": detail, "importance": importance,
        "line": at_line,
        "participants": [
            {"ref": f"E{eid(conn, 'Aren')}", "role": "actor"},
            {"ref": f"E{eid(conn, target)}", "role": "target"},
        ],
    }  # fmt: skip


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


# --- callouts ------------------------------------------------------------------------------


def test_after_six_years_the_trivial_is_gone_and_the_important_is_hazy_and_faded(conn, story):
    mira = eid(conn, "Mira")
    chat.set_presence(conn, story, eid(conn, "Tobin"), False)
    apron = line(conn, story, "Tobin's apron is green, by the way.")
    secret = line(conn, story, "The ledger is under the third floorboard.")
    nod = line(conn, story, "*nods*", who="Mira")
    read(conn, story, apron, nod, [event(conn, "Tobin wore green.", 2, 1), ledger(conn, 2)])
    callout = {
        "kind": "memory", "who": [mira], "text": "Mira will remember this", "reason": None,
        "faded": False, "memory_id": memory_id(conn, DETAIL),
    }  # fmt: skip
    fresh = signals.signals(conn, story)["lines"]
    assert fresh[secret]["callouts"] == [callout]
    assert "callouts" not in fresh[apron]  # importance 2 is not worth a callout

    turns.say(conn, story, skip="six years later")
    later = signals.signals(conn, story)["lines"]
    assert later[apron]["receipts"] == [{"id": mira, "state": "forgotten"}]
    assert later[secret]["receipts"] == [{"id": mira, "state": "hazy"}]
    assert later[secret]["callouts"] == [callout | {"faded": True}]


@pytest.mark.parametrize(
    ("resolution", "text"),
    [
        ("challenged", "Mira knows that's not true"),
        ("doubted", "Mira has her doubts"),
        ("accepted", "Mira believed you"),
    ],
)
def test_a_lie_on_your_line_says_whether_she_believed_it_and_why(conn, story, resolution, text):
    mira = eid(conn, "Mira")
    chat.set_presence(conn, story, eid(conn, "Tobin"), False)  # just the two of them
    secret = line(conn, story, "The ledger is under the third floorboard.")
    nod = line(conn, story, "*nods*", who="Mira")
    read(conn, story, secret, nod, [ledger(conn, 1)])
    lie_line = line(conn, story, "It was never there. I buried it by the lighthouse.")
    frown = line(conn, story, "*frowns*", who="Mira")
    lie = {
        "kind": "claim", "detail": "Aren says the ledger is buried by the lighthouse.",
        "gist": "Aren says the ledger is elsewhere.", "importance": 6, "line": 1,
        "asserted_by": f"E{eid(conn, 'Aren')}", "heard_by": [f"E{mira}"],
    }  # fmt: skip
    clash = {
        "claim": 0, "contradicts": f"M{memory_id(conn, DETAIL)}", "hearer": f"E{mira}",
        "resolution": resolution,
    }  # fmt: skip
    read(conn, story, lie_line, frown, [lie], contradictions=[clash])
    [belief] = [c for c in signals.signals(conn, story)["lines"][lie_line]["callouts"]]
    assert (belief["kind"], belief["who"], belief["text"]) == ("belief", [mira], text)
    assert belief["reason"] == f"Mira remembers it clearly: “{DETAIL}”"


def test_a_feeling_lands_on_the_line_they_share_or_else_the_last_line_read(conn, story):
    mira, tobin = eid(conn, "Mira"), eid(conn, "Tobin")
    evening = line(conn, story, "Evening, both of you.")
    fetch = line(conn, story, "Tobin, fetch us a round from the bar.")
    grin = line(conn, story, "*grins* Anything for a paying customer.", who="Tobin")
    sent = event(conn, "Aren sent Tobin to fetch a round.", 3, 2, target="Tobin")
    edges = [
        {"src": f"E{tobin}", "dst": f"E{eid(conn, 'Aren')}", "rel": "resents",
         "note": "Sent off like a servant."},
        {"src": f"E{mira}", "dst": f"E{eid(conn, 'Aren')}", "rel": "trusts"},
    ]  # fmt: skip
    read(conn, story, evening, grin, [sent], edges=edges)
    lines = signals.signals(conn, story)["lines"]
    assert lines[fetch]["callouts"] == [
        {"kind": "feeling", "who": [tobin], "text": "Tobin didn't like that",
         "reason": "Sent off like a servant.", "faded": False,
         "memory_id": memory_id(conn, "Aren sent Tobin to fetch a round.")},
    ]  # fmt: skip
    [trust] = lines[grin]["callouts"]  # nothing they share in this read: its last line
    assert (trust["who"], trust["text"], trust["memory_id"]) == (
        [mira], "Mira trusts you a little more", None,
    )  # fmt: skip


# --- skip reports --------------------------------------------------------------------------


def test_a_skip_of_a_day_or_more_reports_what_each_character_let_go(conn, story):
    mira = eid(conn, "Mira")
    chat.set_presence(conn, story, eid(conn, "Tobin"), False)
    first = line(conn, story, "The ledger is under the third floorboard.")
    line(conn, story, "And the key is in the lamp.")
    nod = line(conn, story, "*nods*", who="Mira")
    memories = [ledger(conn, 1), event(conn, "The key is in the lamp.", 5, 2),
                event(conn, "Aren said it quietly.", 2, 2)]  # fmt: skip
    read(conn, story, first, nod, memories)
    marker = turns.say(conn, story, skip="six years later")
    report = signals.signals(conn, story)["lines"][marker]["skip"]
    assert report["minutes"] == 6 * 365 * 1440
    assert (report["from_clock"], report["to_clock"]) == ("Day 1, 08:06", "Year 7, Day 1, 08:08")
    assert report["faded"] == [{"id": mira, "hazy": 1, "gone": 2}]
    assert report["text"] == "1 of Mira's memories is going hazy. 2 are fading out."
