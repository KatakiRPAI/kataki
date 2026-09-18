import pytest

from kataki import chat


@pytest.fixture
def story(conn):
    return conn.execute("INSERT INTO stories(title, minutes_per_turn) VALUES('s', 2)").lastrowid


def texts(rows):
    return [r["text"] for r in rows]


def test_appending_walks_the_story_clock_forward(conn, story):
    a = chat.append_message(conn, story, "user", "hello")
    b = chat.append_message(conn, story, "assistant", "hi")
    c = chat.append_message(conn, story, "user", "Six years later...", skip_minutes=3_153_600)
    times = [
        conn.execute("SELECT story_time FROM messages WHERE id=?", (i,)).fetchone()[0]
        for i in (a, b, c)
    ]
    assert times == [2, 4, 3_153_606]


def test_active_path_runs_root_to_leaf(conn, story):
    chat.append_message(conn, story, "user", "one")
    chat.append_message(conn, story, "assistant", "two")
    chat.append_message(conn, story, "user", "three")
    assert texts(chat.active_path(conn, story)) == ["one", "two", "three"]


def test_regenerating_adds_a_sibling_and_makes_it_active(conn, story):
    chat.append_message(conn, story, "user", "one")
    first = chat.append_message(conn, story, "assistant", "reply A")
    second = chat.append_sibling(conn, first, "reply B")

    assert texts(chat.active_path(conn, story)) == ["one", "reply B"]
    assert chat.sibling_position(conn, second) == (2, 2)
    assert chat.sibling_position(conn, first) == (1, 2)
    a, b = (
        conn.execute("SELECT * FROM messages WHERE id=?", (i,)).fetchone() for i in (first, second)
    )
    assert (a["story_time"], a["role"], a["speaker_id"]) == (
        b["story_time"],
        b["role"],
        b["speaker_id"],
    )


def test_swiping_back_to_a_branch_resumes_at_its_newest_leaf(conn, story):
    chat.append_message(conn, story, "user", "one")
    branch_a = chat.append_message(conn, story, "assistant", "reply A")
    chat.append_message(conn, story, "user", "deeper on A")
    chat.append_sibling(conn, branch_a, "reply B")
    assert texts(chat.active_path(conn, story)) == ["one", "reply B"]

    chat.set_leaf(conn, story, branch_a)
    assert texts(chat.active_path(conn, story)) == ["one", "reply A", "deeper on A"]


def test_set_leaf_refuses_a_message_from_another_story(conn, story):
    other = conn.execute("INSERT INTO stories(title) VALUES('other')").lastrowid
    foreign = chat.append_message(conn, other, "user", "elsewhere")
    with pytest.raises(ValueError):
        chat.set_leaf(conn, story, foreign)


def test_editing_fixes_text_in_place_and_flags_the_run_that_read_it(conn, story):
    a = chat.append_message(conn, story, "user", "I saw Tobn at the docks")
    b = chat.append_message(conn, story, "assistant", "Did you?")
    c = chat.append_message(conn, story, "user", "yes")
    covering = conn.execute(
        "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger, status)"
        " VALUES(?, ?, ?, 'cadence', 'ok')",
        (story, a, b),
    ).lastrowid
    later = conn.execute(
        "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger, status)"
        " VALUES(?, ?, ?, 'cadence', 'ok')",
        (story, c, c),
    ).lastrowid

    chat.edit_message(conn, a, "I saw Tobin at the docks")

    assert (
        texts(chat.active_path(conn, story))[0] == "I saw Tobin at the docks"
    )  # no fork for a typo
    stale = dict(conn.execute("SELECT id, stale FROM extraction_runs").fetchall())
    assert stale == {covering: 1, later: 0}
    edited = conn.execute("SELECT edited_at FROM messages WHERE id=?", (a,)).fetchone()[0]
    assert edited is not None


def test_a_run_on_another_branch_is_not_flagged(conn, story):
    root = chat.append_message(conn, story, "user", "one")
    branch_a = chat.append_message(conn, story, "assistant", "reply A")
    branch_b = chat.append_sibling(conn, branch_a, "reply B")
    run_on_b = conn.execute(
        "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger, status)"
        " VALUES(?, ?, ?, 'cadence', 'ok')",
        (story, root, branch_b),
    ).lastrowid

    chat.edit_message(conn, branch_a, "reply A, reworded")  # id falls inside [root, branch_b]

    assert (
        conn.execute("SELECT stale FROM extraction_runs WHERE id=?", (run_on_b,)).fetchone()[0] == 0
    )
