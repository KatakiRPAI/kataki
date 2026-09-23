"""How a reply came about: the Mind graph shows what the engine recorded, and nothing it didn't.
The ledger scene of the signal tests: Aren tells Mira a secret while Tobin is at the bar."""

# ruff: noqa: F811 (`story` is the signal tests' fixture, imported for pytest to find by name)
import json

from kataki import chat, mind
from test_signals import DETAIL, eid, event, ledger, line, memory_id, read, story  # noqa: F401


def reply(conn, story, text, who="Mira", recalled=(), cards=40, feelings=()):
    """A reply, with the context_log row the engine would have written for it."""
    message = line(conn, story, text, who=who)
    speaker = eid(conn, who) if who != "Narrator" else None
    sections = [
        {"name": "cards", "tokens": cards, "cap": 2000, "evicted": 0},
        {"name": "tail", "tokens": 50, "cap": 900, "evicted": 0, "feelings": list(feelings)},
    ]
    with conn:
        conn.execute(
            "INSERT INTO context_log(story_id, message_id, speaker_id, sections, memories)"
            " VALUES(?,?,?,?,?)",
            (story, message, speaker, json.dumps(sections), json.dumps(list(recalled))),
        )
    return message


def kinds(graph, kind):
    return [n for n in graph["nodes"] if n["kind"] == kind]


def test_what_reached_the_prompt_is_gold_and_what_was_cut_is_not(conn, story):
    with conn:
        conn.execute("UPDATE entities SET description='Guild courier.' WHERE name='Mira'")
    secret = line(conn, story, "The ledger is under the third floorboard.")
    read(conn, story, secret, secret, [ledger(conn, 1), event(conn, "Aren bought a round.", 3, 1)])
    kept, cut = memory_id(conn, DETAIL), memory_id(conn, "Aren bought a round.")
    answer = reply(conn, story, "*nods*", recalled=[
        {"memory_id": kept, "tier": "sharp", "rendered": "detail", "A": 1.2},
        {"memory_id": cut, "tier": "hazy", "rendered": "dropped", "A": -2.0},
    ])  # fmt: skip
    graph = mind.mind(conn, answer)
    recalls = {n["id"]: n for n in kinds(graph, "recall")}
    assert recalls[f"m{kept}"]["gold"] and not recalls[f"m{cut}"]["gold"]
    assert recalls[f"m{kept}"]["text"].startswith("Aren hid the guild ledger")
    heard = kinds(graph, "heard")[0]
    assert heard["text"] == "Aren: “The ledger is under the third floorboard.”"
    assert {"from": heard["id"], "to": f"m{kept}", "gold": True} in graph["links"]
    assert {"from": heard["id"], "to": f"m{cut}", "gold": False} in graph["links"]
    assert kinds(graph, "persona")[0]["gold"]  # the card reached the prompt


def test_a_thought_or_a_whisper_to_someone_else_never_came_in(conn, story):
    line(conn, story, "(I don't trust him.)", audience=[])
    line(conn, story, "psst", audience=[eid(conn, "Tobin")])
    line(conn, story, "Evening, Mira.")
    graph = mind.mind(conn, reply(conn, story, "Evening."))
    assert [n["text"] for n in kinds(graph, "heard")] == ["Aren: “Evening, Mira.”"]


def test_a_doubt_shows_only_for_a_memory_that_reached_the_prompt(conn, story):
    secret = line(conn, story, "The ledger is under the third floorboard.")
    read(conn, story, secret, secret, [ledger(conn, 1)])
    kept = memory_id(conn, DETAIL)
    with conn:
        conn.execute("UPDATE knowledge SET belief=0.4 WHERE memory_id=?", (kept,))
    doubted = reply(
        conn,
        story,
        "Hm.",
        recalled=[{"memory_id": kept, "tier": "sharp", "rendered": "detail", "A": 1}],
    )
    [belief] = kinds(mind.mind(conn, doubted), "belief")
    assert belief["weight"] == 0.4 and belief["text"].startswith(
        "Doubts it: Aren hid the guild ledger"
    )
    cut = reply(
        conn,
        story,
        "Hm.",
        recalled=[{"memory_id": kept, "tier": "sharp", "rendered": "dropped", "A": 1}],
    )
    assert kinds(mind.mind(conn, cut), "belief") == []


def test_a_feeling_is_the_one_held_then_and_gold_only_if_it_reached_the_prompt(conn, story):
    evening = line(conn, story, "Evening.")
    early = reply(conn, story, "Evening yourself.")
    read(conn, story, evening, early, [], edges=[
        {"src": f"E{eid(conn, 'Mira')}", "dst": f"E{eid(conn, 'Aren')}", "rel": "trusts"},
    ])  # fmt: skip
    assert kinds(mind.mind(conn, early), "feeling") == []  # read after she spoke
    later = reply(conn, story, "Go on.")
    [feeling] = kinds(mind.mind(conn, later), "feeling")
    assert (feeling["text"], feeling["gold"], feeling["detail"]["tone"]) == (
        "Trusts you",
        False,
        "warm",
    )
    edge = conn.execute("SELECT id FROM edges WHERE rel='trusts'").fetchone()["id"]
    felt = reply(conn, story, "I'll help.", feelings=[edge])
    assert kinds(mind.mind(conn, felt), "feeling")[0]["gold"]  # it reached the prompt


def test_the_narrator_has_no_feelings_or_persona_and_an_unlogged_reply_invents_nothing(conn, story):
    line(conn, story, "Tell me about the storm.")
    told = chat.append_message(conn, story, "assistant", "Rain lashes the windows.", None)
    graph = mind.mind(conn, told)
    assert graph["speaker"]["name"] == "Narrator"
    assert {n["column"] for n in graph["nodes"]} == {
        "in"
    }  # no log row: nothing inside, nothing decided
    assert graph["spoke"]["text"] == "Rain lashes the windows."
    assert mind.mind(conn, line(conn, story, "Thanks.")) is None  # your line has no mind


def test_why_they_answered_and_what_recall_searched_with_sit_between_heard_and_recall(conn, story):
    secret = line(conn, story, "Mira, the ledger is under the third floorboard.")
    read(conn, story, secret, secret, [ledger(conn, 1)])
    kept = memory_id(conn, DETAIL)
    answer = reply(conn, story, "*nods*", recalled=[
        {"memory_id": kept, "tier": "sharp", "rendered": "detail", "A": 1.0},
    ])  # fmt: skip
    ms = {"prompt": 3, "recall": 40, "first_token": 300, "reply": 900, "total": 950}
    trace = {"why": "named", "cue": "Mira, the ledger is under the third floorboard.", "ms": ms}
    with conn:
        conn.execute("UPDATE messages SET gen=? WHERE id=?", (json.dumps({"trace": trace}), answer))
    graph = mind.mind(conn, answer)
    [why] = kinds(graph, "attention")
    [cue] = kinds(graph, "cue")
    heard = kinds(graph, "heard")[0]["id"]
    assert why["text"] == "Aren named Mira" and why["column"] == "sense"
    assert {"from": heard, "to": cue["id"], "gold": True} in graph["links"]
    assert {"from": cue["id"], "to": f"m{kept}", "gold": True} in graph["links"]
    assert not any(x["from"] == heard and x["to"] == f"m{kept}" for x in graph["links"])
    assert graph["spoke"]["ms"] == 950


def test_how_she_feels_about_you_is_counted_read_by_read(conn, story):
    mira, aren = eid(conn, "Mira"), eid(conn, "Aren")
    edge = lambda rel: {"src": f"E{mira}", "dst": f"E{aren}", "rel": rel}  # noqa: E731
    first = line(conn, story, "Evening, Mira.")
    read(conn, story, first, first, [], edges=[edge("trusts"), edge("fond of")])
    lie = line(conn, story, "It was never behind the bar.")
    read(conn, story, lie, lie, [], edges=[edge("resents")])
    run = conn.execute("SELECT max(id) FROM extraction_runs").fetchone()[0]
    with conn:  # the lie she doubts
        claim = conn.execute(
            "INSERT INTO memories(story_id, kind, story_time, detail, gist, asserted_by, is_true,"
            " run_id) VALUES(?, 'claim', 0, 'Never behind the bar.', 'Not the bar.', ?, 0, ?)",
            (story, aren, run),
        ).lastrowid
        conn.execute(
            "INSERT INTO knowledge(knower_id, memory_id, source, learned_story_time, belief,"
            " run_id) VALUES(?, ?, 'witnessed', 0, 0.4, ?)",
            (mira, claim, run),
        )
    later = chat.append_message(conn, story, "user", "Aren returns.", aren, 6 * 365 * 1440)
    read(conn, story, later, later, [])
    got = mind.feelings(conn, story, mira, aren)
    counts = [(p["warmth"], p["trust"], p["doubt"]) for p in got["points"]]
    assert counts == [(1, 1, 0), (0, 1, 1), (0, 1, 1)]
    assert [s["label"] for s in got["skips"]] == ["Six years later"] and got["counted"]
