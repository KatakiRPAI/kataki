"""A story on its way out: Markdown to read, JSONL to keep."""

import json

import pytest
from fastapi.testclient import TestClient

from kataki import chat, library, readable
from kataki.server import create_app


@pytest.fixture
def api(conn, backend):
    client = TestClient(create_app(conn, "t", llm=backend.llm, worker_delay=60))
    client.headers["Authorization"] = "Bearer t"
    with client:
        yield client


@pytest.fixture
def story(conn):
    """A story with everything an export has to render: a premise, a cast, a whisper, a
    thought, narration, a time skip and two chapters."""
    plot = library.create_item(
        conn, "scenario", "Low Tide", "A room above the Gull, the night the ledger went missing."
    )
    mira = library.create_item(conn, "character", "Mira", "She keeps the ledger.")
    tobin = library.create_item(conn, "character", "Tobin", "A fence with a bad cough.")
    aren = library.create_item(conn, "character", "Aren", "Late.", data={"persona": True})
    gull = library.create_item(conn, "place", "The Gull")
    story_id = library.create_story(
        conn, "The Third Floorboard", [mira, tobin], place_id=gull,
        persona_id=aren, scenario_id=plot,
    )  # fmt: skip
    who = {
        e["name"]: e["id"]
        for e in conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,))
    }
    say = lambda role, text, **kw: chat.append_message(conn, story_id, role, text, **kw)  # noqa: E731

    first = say("assistant", "*no glance up* We're closed.", speaker_id=who["Mira"])
    say("user", "I'm not here to drink.", speaker_id=who["Aren"])
    say("assistant", "The lamp gutters.")  # narration: nobody's voice
    later = say("assistant", "Third floorboard.", speaker_id=who["Mira"], audience=[who["Aren"]])
    say("user", "She's lying.", speaker_id=who["Aren"], audience=[])
    # a time skip is a line of the story's own, the way turns.py writes one
    say("system", "— An hour later —", skip_minutes=60)
    say("assistant", "*a cough from the stairs*", speaker_id=who["Tobin"])

    library.open_chapter(conn, story_id, "The first night", first)
    library.open_chapter(conn, story_id, "What the ledger said", later)
    return story_id


def test_a_story_reads_as_a_story(conn, story):
    out = readable.markdown(conn, story)
    assert out.startswith("# The Third Floorboard\n")
    assert "> A room above the Gull, the night the ledger went missing." in out
    assert "*Mira, Tobin and Aren · 6 lines*" in out  # the skip marker is not a line

    # the chapters are the headings, in the order they were opened
    assert [line for line in out.splitlines() if line.startswith("## ")] == [
        "## The first night",
        "## What the ledger said",
    ]
    # where it opens, and when — the one marker the story does not write itself
    assert "*— The Gull · Day 1, 08:00 —*" in out
    # and the skip is the story's own line, said once
    assert out.count("An hour later") == 1 and "*— An hour later —*" in out

    assert "**Mira**\n*no glance up* We're closed." in out
    assert "**Mira** *(whispering to Aren)*\nThird floorboard." in out
    assert "**Aren** *(thinking)*\nShe's lying." in out
    assert "\nThe lamp gutters.\n" in out  # narration is nobody's line, so nobody is named
    assert "**None**" not in out and "undefined" not in out


def test_the_same_story_line_by_line(conn, story):
    lines = [json.loads(line) for line in readable.jsonl(conn, story).splitlines()]
    assert len(lines) == 7
    assert lines[0] == {
        "story_time": 2,
        "clock": "Day 1, 08:02",
        "role": "assistant",
        "speaker": "Mira",
        "text": "*no glance up* We're closed.",
        "chapter": "The first night",
        "scene": "The Gull",
    }
    assert lines[2]["speaker"] is None  # narration
    assert lines[3]["to"] == ["Aren"] and "thought" not in lines[3]
    assert lines[4]["thought"] is True
    assert lines[5] == {
        "story_time": 72,
        "clock": "Day 1, 09:12",
        "role": "system",
        "speaker": None,
        "text": "— An hour later —",
        "skip": 60,
    }
    assert lines[6]["speaker"] == "Tobin"
    # nothing of the engine's own bookkeeping
    assert not {"id", "parent_id", "gen", "run_id", "tokens", "scene_id"} & set(lines[0])


def test_a_story_with_nothing_in_it_is_still_a_story(conn):
    bare = library.create_story(conn, "Untitled")
    assert readable.markdown(conn, bare).strip() == "# Untitled"
    assert readable.jsonl(conn, bare) == ""


def test_a_hidden_line_is_struck_through_not_taken_out(conn, story):
    """Hiding a line keeps it out of the prompt, not out of the story — the app says so as it
    does it ("It stays in the story but never reaches the AI") and strikes it through."""
    path = chat.active_path(conn, story)
    conn.execute("UPDATE messages SET hidden=1 WHERE id=?", (path[1]["id"],))
    conn.commit()
    assert "~~I'm not here to drink.~~" in readable.markdown(conn, story)
    lines = [json.loads(line) for line in readable.jsonl(conn, story).splitlines()]
    assert len(lines) == 7 and lines[1]["hidden"] is True
    assert "hidden" not in lines[0]


def test_a_chapter_that_starts_on_a_hidden_line_keeps_its_heading(conn, story):
    path = chat.active_path(conn, story)
    conn.execute("UPDATE messages SET hidden=1 WHERE id=?", (path[0]["id"],))
    conn.commit()
    assert "## The first night" in readable.markdown(conn, story)


def test_only_the_take_the_story_reads_on(conn, story):
    """Another take is not another line: the story is the path you are on."""
    path = chat.active_path(conn, story)
    chat.append_sibling(conn, path[-1]["id"], "*nothing at all*")
    chat.set_leaf(conn, story, path[-1]["id"])
    out = readable.markdown(conn, story)
    assert "*a cough from the stairs*" in out and "*nothing at all*" not in out


def test_the_routes_hand_over_a_file(api, conn, story):
    md = api.get(f"/stories/{story}/export?as=markdown")
    assert md.status_code == 200
    assert md.headers["content-type"].startswith("text/markdown")
    assert "the-third-floorboard.md" in md.headers["content-disposition"]
    assert md.text.startswith("# The Third Floorboard")

    jl = api.get(f"/stories/{story}/export?as=jsonl")
    assert jl.headers["content-type"].startswith("application/x-ndjson")
    assert "the-third-floorboard.jsonl" in jl.headers["content-disposition"]
    assert len(jl.text.splitlines()) == 7

    assert api.get(f"/stories/{story}/export").status_code == 200  # markdown by default
    assert api.get(f"/stories/{story}/export?as=pdf").status_code == 422
    assert api.get("/stories/999/export").status_code == 404


def test_a_title_that_is_not_a_filename(api, conn, story):
    """A story can be called anything; a file cannot."""
    conn.execute("UPDATE stories SET title=? WHERE id=?", ('  ../Låg tide: "él"?  ', story))
    conn.commit()
    said = api.get(f"/stories/{story}/export").headers["content-disposition"]
    assert "lag-tide-el.md" in said and ".." not in said
    assert all(ord(c) < 128 for c in said)

    conn.execute("UPDATE stories SET title='🌊' WHERE id=?", (story,))
    conn.commit()
    assert "story.md" in api.get(f"/stories/{story}/export").headers["content-disposition"]


# --- what the review found: a story is user text, and a document is not a safe place for it ---


def test_a_story_nobody_plays_in_still_knows_who_spoke(conn):
    """Director mode: the player has no character, so their lines carry no speaker — but they
    are still the player's lines, not the world narrating itself."""
    mira = library.create_item(conn, "character", "Mira", "She keeps the ledger.")
    story = library.create_story(conn, "Low Tide", [mira])  # no persona: directing
    chat.append_message(conn, story, "user", "Have someone knock at the door.")
    chat.append_message(conn, story, "assistant", "A knock. Three slow taps.")
    chat.append_message(conn, story, "user", "She should be afraid of it.", audience=[])

    out = readable.markdown(conn, story)
    assert "**You**\nHave someone knock at the door." in out
    assert "**You** *(thinking)*\nShe should be afraid of it." in out
    assert "\nA knock. Three slow taps.\n" in out  # the world's own prose stays unnamed


def test_a_line_of_story_cannot_forge_a_heading(conn, story):
    """`---` under a name is how Markdown makes a heading, and a story is allowed to say it."""
    who = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
    ).fetchone()["id"]
    for said in (
        "---\nand then she left.",
        "# Not a chapter",
        "```\nnot a fence",
        "> not a quote",
        "1. not a list",
        "    not code",
        "| not | a table |",
    ):
        chat.append_message(conn, story, "assistant", said, speaker_id=who)

    out = readable.markdown(conn, story)
    assert [line for line in out.splitlines() if line.startswith("## ")] == [
        "## The first night",
        "## What the ledger said",
    ]  # no line of story became a heading
    for opener in (r"\---", r"\# Not a chapter", "\\```", r"\> not a quote", r"\1. not a list"):
        assert opener in out
    assert r"\| not \| a table \|" not in out  # only the first character of a line is syntax
    assert r"\| not | a table |" in out
    assert "\n    not code" not in out  # four spaces would be a code block


def test_a_name_cannot_break_out_of_its_own_line(conn):
    """Names come from the library and from imported cards, so they are user text too."""
    odd = library.create_item(conn, "character", "M*i*ra\n# Not a heading")
    story = library.create_story(conn, "Low Tide", [odd])
    who = conn.execute("SELECT id FROM entities WHERE story_id=?", (story,)).fetchone()["id"]
    chat.append_message(conn, story, "assistant", "Hm.", speaker_id=who)

    out = readable.markdown(conn, story)
    assert r"**M\*i\*ra \# Not a heading**" in out
    assert [line for line in out.splitlines() if line.startswith("#")] == ["# Low Tide"]


def test_a_premise_of_several_lines_stays_in_its_quote(conn):
    plot = library.create_item(conn, "scenario", "Low Tide", "The Gull, at low tide.\nIt is late.")
    story = library.create_story(conn, "Low Tide", scenario_id=plot)
    out = readable.markdown(conn, story)
    assert "> The Gull, at low tide.\n> It is late." in out


def test_the_scene_says_what_moved_even_when_it_has_no_name(conn):
    """A scene with neither a place nor a title is still a scene change, and a reader tracking
    the field has to be told the old one ended."""
    mira = library.create_item(conn, "character", "Mira")
    gull = library.create_item(conn, "place", "The Gull")
    story = library.create_story(conn, "Low Tide", [mira], place_id=gull)
    who = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
    ).fetchone()["id"]
    chat.append_message(conn, story, "assistant", "The lamp turns.", speaker_id=who)
    chat.new_scene(conn, story, [who])  # no place, no title
    chat.append_message(conn, story, "assistant", "Somewhere else, then.", speaker_id=who)

    lines = [json.loads(line) for line in readable.jsonl(conn, story).splitlines()]
    assert lines[0]["scene"] == "The Gull"
    assert lines[1]["scene"] is None  # the marker line: the old scene ended here
    assert "scene" not in lines[2]


def test_a_scene_with_a_title_is_called_what_the_story_calls_it(conn):
    mira = library.create_item(conn, "character", "Mira")
    gull = library.create_item(conn, "place", "The Gull")
    story = library.create_story(conn, "Low Tide", [mira], place_id=gull)
    who = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
    ).fetchone()["id"]
    chat.append_message(conn, story, "assistant", "The lamp turns.", speaker_id=who)
    chat.new_scene(conn, story, [who], place_id=None, title="The night it burned")
    lines = [json.loads(line) for line in readable.jsonl(conn, story).splitlines()]
    assert lines[1]["text"] == "— The night it burned —" and lines[1]["scene"] == (
        "The night it burned"
    )


def test_a_story_that_opens_on_a_marker_still_says_where_it_is(conn):
    mira = library.create_item(conn, "character", "Mira")
    gull = library.create_item(conn, "place", "The Gull")
    story = library.create_story(conn, "Low Tide", [mira], place_id=gull)
    who = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
    ).fetchone()["id"]
    chat.append_message(conn, story, "system", "— An hour later —", skip_minutes=60)
    chat.append_message(conn, story, "assistant", "*a cough*", speaker_id=who)
    assert "*— The Gull · Day 1, 08:00 —*" in readable.markdown(conn, story)


def test_one_line_is_one_line(conn):
    mira = library.create_item(conn, "character", "Mira")
    story = library.create_story(conn, "Low Tide", [mira])
    chat.append_message(conn, story, "system", "— An hour later —", skip_minutes=60)
    chat.append_message(conn, story, "assistant", "Hm.", speaker_id=1)
    assert "*Mira · 1 line*" in readable.markdown(conn, story)  # the marker is not a line
