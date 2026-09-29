"""Slice 3: the thought before the reply, read, kept out of the reply, checked, and shown."""

import json

import pytest

from kataki import chat, library, thought, turns
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
