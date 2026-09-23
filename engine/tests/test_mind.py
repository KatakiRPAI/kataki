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
