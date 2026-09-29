"""Slice 3: the thought before the reply, read, kept out of the reply, checked, and shown."""

from kataki import thought
from kataki.llm import Endpoint

TAGS = ("<think>", "</think>")
EP = Endpoint(base_url="http://x/v1", model="m")


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
