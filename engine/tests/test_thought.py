"""Slice 3: the thought before the reply, read, kept out of the reply, checked, and shown."""

import json

import pytest

from kataki import after, bonds, chat, library, mind, people, thought, turns
from kataki.llm import Endpoint

TAGS = ("<think>", "</think>")
EP = Endpoint(base_url="http://x/v1", model="m")
HEADER = "<think>\nMira thinks: Don't look at the ring.\nMira wants: him to drop it\n</think>\n"
SEEN = {"thinks": "Don't look at the ring.", "wants": "him to drop it", "from": "before"}


# --- pure --------------------------------------------------------------------------------------


def test_the_header_is_asked_for_with_the_endpoints_own_tags():
    line = thought.ask("Mira", ("<thought>", "</thought>"))
    assert "<thought>\nMira thinks:" in line and "Mira wants:" in line and "</thought>" in line
    assert "at most 25 words" in line and "at most 10 words" in line


def test_header_lines_are_read_in_any_dress():
    lines = ["**Mira thinks:** “Don't look at the ring.”", "mira wants: him to drop it"]
    assert thought.parse(lines, "Mira Voss") == {
        "thinks": "Don't look at the ring.",
        "wants": "him to drop it",
    }
    assert thought.parse(["Thinks: only this"], "Mira") == {"thinks": "only this", "wants": None}
    assert thought.parse(["She sighs."], "Mira") is None


def test_a_long_thought_is_clipped_to_its_cap():
    long = "Mira thinks: " + " ".join(["word"] * 40)
    assert len(thought.parse([long], "Mira")["thinks"].split()) == thought.WORDS["thinks"]


def test_split_takes_header_lines_and_stray_tags_out_of_a_text():
    rest, found = thought.split("Nothing.\n</think>\n\nMira thinks: he saw it.", "Mira", TAGS)
    assert rest == "Nothing." and found == ["Mira thinks: he saw it."]
    assert thought.split("He thinks: nothing.", "Mira", TAGS)[1] == []  # someone else's line


def test_an_echo_is_five_words_of_the_thought_in_a_row():
    thinks = "I promised myself I wouldn't ask about the ring."
    assert thought.echoed(thinks, "*sighs* I promised myself I wouldn't, okay?") == (
        "i promised myself i wouldn't"
    )
    assert thought.echoed(thinks, "The ring? What ring. I never ask.") is None
    assert thought.echoed(None, "anything at all here") is None


def test_who_gets_a_thought(conn):
    assert thought.mode(conn, EP, 3) == "inline"
    assert thought.mode(conn, EP, None) is None  # the narrator voices no one's mind
    thinking = Endpoint(base_url="x", model="m", params={"thinking": "enabled"})
    assert thought.mode(conn, thinking, 3) == "after"
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    assert thought.mode(conn, EP, 3) is None
    conn.execute("UPDATE settings SET value='\"premium\"' WHERE key='mind.level'")
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.thought', 'false')")
    assert thought.mode(conn, EP, 3) is None


def feed(header: thought.Header, *chunks: str) -> str:
    return "".join(header.feed(c) for c in chunks) + header.flush()


def test_a_plain_words_header_never_reaches_the_reply():
    h = thought.Header(True, "Mira", TAGS)
    shown = feed(h, "Mi", "ra thi", "nks: don't look.\nMira wa", "nts: out\n</thi", "nk>\n\nNo.")
    assert shown.strip() == "No." and h.caught == ["Mira thinks: don't look.", "Mira wants: out"]


def test_an_ordinary_reply_passes_at_once():
    h = thought.Header(True, "Mira", TAGS)
    assert h.feed("Th") == ""  # could still be "thinks:"
    assert h.feed("e tide.") == "The tide."
    assert h.feed(" More.") == " More." and h.caught == []


def test_a_stream_that_ends_on_a_header_line_shows_nothing():
    h = thought.Header(True, "Mira", TAGS)
    assert feed(h, "Mira thinks: tired") == "" and h.caught == ["Mira thinks: tired"]


def test_a_header_in_markdown_dress_is_still_a_header():
    lines = ["**Mira thinks**: he saw it.", "*Mira wants*: out", "Mira thinks — sunk."]
    assert thought.parse(lines[:2], "Mira") == {"thinks": "he saw it.", "wants": "out"}
    assert thought.parse(lines[2:], "Mira") == {"thinks": "sunk.", "wants": None}
    rest, found = thought.split("\n".join([*lines, "", "No."]), "Mira", TAGS)
    assert rest == "No." and len(found) == 3
    h = thought.Header(True, "Mira", TAGS)
    assert feed(h, "**Mira thi", "nks**: x\nMira wants — y\nNo.").strip() == "No."
    assert len(h.caught) == 2


def test_ordinary_lines_stay_and_trailing_headers_go():
    assert feed(thought.Header(True, "Mira", TAGS), "Mira sighs.") == "Mira sighs."
    keep = "Mira sighs.\nWants: a drink.\nMore."  # a real dialogue line, mid-reply
    assert thought.split(keep, "Mira", TAGS) == (keep, [])
    rest, found = thought.split("Ok.\n\n**Mira thinks**: hm\nWants: out", "Mira", TAGS)
    assert rest == "Ok." and len(found) == 2


def test_an_accented_echo_is_caught():
    thinks = "il était très fatigué ce soir-là"
    assert thought.echoed(thinks, "Oui, il était très fatigué ce soir, dis") == (
        "il était très fatigué ce"
    )
    assert thought.echoed(thinks, "Il etait tres fatigue ce soir") is None


# --- in the turn -------------------------------------------------------------------------------


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    return library.create_story(
        conn, "Low Tide", character_ids=[ids["Mira"], ids["Tobin"]], persona_id=ids["Aren"]
    )


async def play(stream):
    return [e async for e in stream]


def shown(events) -> str:
    return "".join(v for k, v in events if k == "token")


def leaf(conn, story):
    m = chat.active_path(conn, story)[-1]
    return m["text"], json.loads(m["gen"])


@pytest.mark.anyio
async def test_she_thinks_first_and_the_thought_stays_out_of_the_story(conn, story, backend):
    backend.say(HEADER + "Nothing. Just tired.", "Fine.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, what's wrong?"))
    asked = backend.requests[0]["messages"][-1]["content"].split("[Directive]")[1]
    assert "<think>\nMira thinks:" in asked
    assert "Mira thinks: Don't look at the ring." in "".join(v for k, v in events if k == "thought")
    assert shown(events) == "Nothing. Just tired."
    text, gen = leaf(conn, story)
    assert text == "Nothing. Just tired." and gen["thought"] == SEEN
    assert gen["reasoning"] is None and "think_ms" not in gen
    assert isinstance(gen["trace"]["ms"]["thought"], int)
    assert events[-1][1]["thought"] == SEEN

    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert "the ring" not in json.dumps(backend.requests[1]["messages"])


@pytest.mark.anyio
@pytest.mark.parametrize(
    "reply, came",
    [
        ("Mira thinks: Don't look at the ring.\nMira wants: him to drop it\n\nNothing.", "before"),
        ("Mira thinks: Don't look at the ring.\n</think>\nNothing.", "before"),
        ("<think>\nMira thinks: Don't look at the ring.\n\nNothing.", "before"),  # never closed
        ("Nothing.\n<think>Mira thinks: Don't look at the ring.</think>", "after"),
        ("Nothing.\n\nMira thinks: Don't look at the ring.", "after"),
    ],
)
async def test_a_header_in_the_wrong_place_never_stays_in_the_reply(
    conn, story, backend, reply, came
):
    backend.say(reply)
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    text, gen = leaf(conn, story)
    assert text == "Nothing." and events[-1][1]["text"] == "Nothing."
    assert gen["thought"]["thinks"] == "Don't look at the ring." and gen["thought"]["from"] == came
    if came == "before":  # a header at the start is never streamed as words either
        assert "thinks" not in shown(events) and "think>" not in shown(events)


@pytest.mark.anyio
@pytest.mark.parametrize("reply", ["Nothing.", "<think>whatever I feel</think>Nothing."])
async def test_no_header_or_a_malformed_one_costs_only_the_thought(conn, story, backend, reply):
    backend.say(reply)
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    text, gen = leaf(conn, story)
    assert events[-1][0] == "done" and text == "Nothing." and "thought" not in gen
    assert events[-1][1]["thought"] is None


@pytest.mark.anyio
async def test_the_narrator_and_lite_are_never_asked(conn, story, backend):
    backend.say("The tide turns.", "Fine.")
    await play(turns.turn(conn, backend.llm, story, None, speaker="narrator"))
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert all("thinks:" not in json.dumps(r["messages"]) for r in backend.requests)


@pytest.mark.anyio
async def test_a_reply_that_says_its_thought_aloud_is_written_again_once(
    conn, story, backend, monkeypatch
):
    monkeypatch.setattr(bonds, "armed", lambda *a: True)  # the echo is held only when armed
    header = "<think>\nMira thinks: I promised myself I wouldn't ask about the ring.\n</think>\n"
    backend.say(
        header + "I promised myself I wouldn't ask. So I won't.",
        header + "I promised myself I wouldn't ask, okay?",  # the retake echoes too: kept
    )
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert len(backend.requests) == 2  # one retake, never two
    retake = backend.requests[1]["messages"][-1]["content"].split("[Directive]")[1]
    assert thought.STRONGER.format(name="Mira") in retake and "Mira thinks:" in retake
    assert "So I won't" not in shown(events)
    text, gen = leaf(conn, story)
    assert gen["trace"]["echo"] == {"hit": "i promised myself i wouldn't", "resampled": True}
    assert "check" not in gen["trace"] and text == "I promised myself I wouldn't ask, okay?"


@pytest.mark.anyio
async def test_an_echo_after_the_first_sentence_is_noted_not_retaken(conn, story, backend):
    header = "<think>\nMira thinks: I promised myself I wouldn't ask about the ring.\n</think>\n"
    backend.say(header + "Hm. Fine. I promised myself I wouldn't, so.")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    _, gen = leaf(conn, story)
    assert len(backend.requests) == 1
    assert gen["trace"]["echo"] == {"hit": "i promised myself i wouldn't", "resampled": False}


def test_the_side_call_asks_for_an_afterthought_only_when_told():
    assert "thought" not in after.schema(["E1"])["properties"]
    s = after.schema(["E1"], afterthought=True)
    assert s["properties"]["thought"] == {"type": ["string", "null"]}
    assert "thought" in s["required"]
    base = {"felt": {"label": "calm", "intensity": 1, "about": None, "cause": ""},
            "events": [], "position": None, "yielded": False, "face": "neutral"}  # fmt: skip
    assert "thought" not in after.read(base | {"thought": None}, ["E1"])
    assert "thought" not in after.read(base | {"thought": 7}, ["E1"])
    assert after.read(base | {"thought": " Tired of him. "}, ["E1"])["thought"] == "Tired of him."


@pytest.mark.anyio
async def test_a_reasoning_model_gets_an_afterthought_from_the_side_call(
    conn, story, backend, side_call
):
    conn.execute("INSERT INTO settings(key, value) VALUES('memory.thinking', '\"lot\"')")
    labels = {"felt": {"label": "calm", "intensity": 1, "about": None, "cause": ""},
              "events": [], "position": None, "yielded": False, "face": "neutral",
              "thought": "He'll never let this go."}  # fmt: skip
    backend.say({"reasoning_content": "She weighs it.", "content": "Fine."}, json.dumps(labels))
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert "thinks:" not in json.dumps(backend.requests[0]["messages"])  # no header asked
    assert "thought" in backend.requests[1]["response_format"]["json_schema"]["schema"]["required"]
    after_ = {"thinks": "He'll never let this go.", "wants": None, "from": "after"}
    _, gen = leaf(conn, story)
    assert gen["thought"] == after_ and events[-1][1]["thought"] == after_
    assert gen["reasoning"] == "She weighs it."  # its own reasoning stays where it was


def script(monkeypatch, backend, *events, then=None):
    """Replace the stream with these (kind, value) events, then optionally raise `then`."""
    llm = backend.llm

    async def stream(*a, **k):
        for e in events:
            yield e
        if then:
            raise then

    monkeypatch.setattr(llm, "chat_stream", stream)
    return llm


async def stop_after(stream, n_kind, n):
    seen = []
    async for kind, value in stream:
        seen.append((kind, value))
        if sum(k == n_kind for k, _ in seen) == n:
            break
    await stream.aclose()
    return seen


@pytest.mark.anyio
async def test_a_stop_mid_thought_saves_no_reply_and_leaks_no_thought(
    conn, story, backend, monkeypatch
):
    llm = script(monkeypatch, backend, ("thought", "<think>\nMira thi"), ("thought", "nks: he"))
    seen = await stop_after(turns.turn(conn, llm, story, "Mira?"), "thought", 1)
    assert all(m["role"] != "assistant" for m in chat.active_path(conn, story))
    assert not any(k == "token" for k, _ in seen)


@pytest.mark.anyio
async def test_an_error_mid_thought_saves_no_reply(conn, story, backend, monkeypatch):
    from kataki.llm import LLMError

    llm = script(monkeypatch, backend, ("thought", "<think>\nMira thi"), then=LLMError("boom"))
    events = await play(turns.turn(conn, llm, story, "Mira?"))
    assert events[-1][0] == "error"
    assert all(m["role"] != "assistant" for m in chat.active_path(conn, story))


@pytest.mark.anyio
async def test_a_stop_mid_reply_keeps_it_clean(conn, story, backend):
    backend.say(HEADER + "Nothing. Just tired, that is all.")
    await stop_after(turns.turn(conn, backend.llm, story, "Mira?"), "token", 1)
    text, gen = leaf(conn, story)
    assert text and "thinks" not in text and "think>" not in text
    assert "Nothing. Just tired, that is all.".startswith(text) and gen["finish"] == "stopped"


@pytest.mark.anyio
async def test_a_stop_while_the_header_holds_a_tail_keeps_it_in_order(
    conn, story, backend, monkeypatch
):
    llm = script(monkeypatch, backend, ("token", "Mira th"), ("thought", "x"))
    await stop_after(turns.turn(conn, llm, story, "Mira?"), "thought", 1)
    assert leaf(conn, story)[0] == "Mira th"


@pytest.mark.anyio
async def test_a_failure_in_reading_the_thought_never_loses_the_reply(
    conn, story, backend, monkeypatch
):
    def boom(*a, **k):
        raise RuntimeError("bad")

    monkeypatch.setattr(thought, "parse", boom)
    backend.say(HEADER + "Nothing. Just tired.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    text, gen = leaf(conn, story)
    assert events[-1][0] == "done" and text == "Nothing. Just tired." and "thought" not in gen


@pytest.mark.anyio
async def test_peek_and_the_mind_graph_show_the_latest_thought(conn, story, backend):
    backend.say(HEADER + "Nothing.")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    cast = {p["name"]: p for p in people.people(conn, row)}
    reply = chat.active_path(conn, story)[-1]["id"]
    assert cast["Mira"]["thought"] == SEEN | {"message_id": reply}
    assert cast["Tobin"]["thought"] is None
    graph = mind.mind(conn, reply)
    nodes = {n["id"]: n for n in graph["nodes"]}
    assert nodes["thought"]["text"] == "Don't look at the ring." and nodes["thought"]["gold"]
    assert (nodes["intent"]["column"], nodes["intent"]["text"]) == ("decide", "him to drop it")
    assert {"from": "thought", "to": "intent", "gold": True} in graph["links"]
    assert {"from": "intent", "to": "spoke", "gold": True} in graph["links"]


@pytest.mark.anyio
async def test_switched_off_nothing_is_asked_or_shown(conn, story, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.thought', 'false')")
    backend.say(HEADER + "Nothing.")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert "thinks:" not in backend.requests[0]["messages"][-1]["content"]
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    assert all(p["thought"] is None for p in people.people(conn, row))


@pytest.mark.anyio
async def test_a_plain_text_header_is_timed_too(conn, story, backend):
    """The probe read "the header itself: None ms": a header in the tokens (no think stream) was
    never timed, since only thought events started the clock."""
    backend.say("Mira thinks: Don't look at the ring.\nMira wants: him to drop it\n\nNothing.")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    _, gen = leaf(conn, story)
    assert gen["thought"]["from"] == "before"
    assert isinstance(gen["trace"]["ms"]["thought"], int)


@pytest.mark.anyio
async def test_unarmed_the_first_sentence_streams_at_once_and_an_echo_is_only_noted(
    conn, story, backend
):
    header = "<think>\nMira thinks: I promised myself I wouldn't ask about the ring.\n</think>\n"
    backend.say(header + "I promised myself I wouldn't ask. So I won't.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert len(backend.requests) == 1  # no retake
    assert shown(events) == "I promised myself I wouldn't ask. So I won't."
    _, gen = leaf(conn, story)
    assert gen["trace"]["echo"] == {"hit": "i promised myself i wouldn't", "resampled": False}
