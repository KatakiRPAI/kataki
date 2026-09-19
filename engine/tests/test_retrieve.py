"""The memory requirements, end to end: extraction rows in, what a character recalls out."""

import pytest

from kataki import chat, extract, library, retrieve
from kataki.activation import effortful_recall

DAY, YEAR = 1440, 365 * 1440
DETAIL = "Tobin told Mira he would betray the guild at the docks tonight."
GIST = "Tobin spoke of turning on the guild."


@pytest.fixture
def world(conn):
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Dara", "Aren")}
    gull = library.create_item(conn, "place", "The Gull", data={"aliases": ["the tavern"]})
    story = library.create_story(
        conn,
        "Low Tide",
        character_ids=[ids["Mira"], ids["Tobin"], ids["Dara"]],
        place_id=gull,
        persona_id=ids["Aren"],
    )
    scene = conn.execute("SELECT id FROM scenes WHERE story_id=?", (story,)).fetchone()["id"]
    conn.execute(  # Dara is elsewhere
        "INSERT INTO presence(scene_id, entity_id, present) VALUES(?, ?, 0)",
        (scene, eid(conn, "Dara")),
    )
    return story


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


def h(conn, name):
    return f"E{eid(conn, name)}"


def say(conn, story, text="...", skip=0):
    return chat.append_message(
        conn, story, "user", text, speaker_id=eid(conn, "Aren"), skip_minutes=skip
    )


def extracted(conn, story, data):
    first = say(conn, story)
    last = say(conn, story)
    run_id = extract.open_run(conn, story, first, last, "cadence")
    extract.apply(conn, run_id, data)
    say(conn, story)  # the conversation moves on, so the window no longer covers the run
    return run_id


def betrayal(conn, **extra):
    return {
        "kind": "event",
        "detail": DETAIL,
        "gist": GIST,
        "importance": 9,
        "participants": [
            {"ref": h(conn, "Tobin"), "role": "actor"},
            {"ref": h(conn, "Mira"), "role": "target"},
        ],
        "place": h(conn, "The Gull"),
        "tags": ["betrayal"],
        **extra,
    }


def recall(conn, story, who, text, **kw):
    return retrieve.recall(conn, story, eid(conn, who), text, noise=False, **kw)


def texts(recalled):
    return [r.text for r in recalled]


# --- req 3: a character who was not there cannot recall it --------------------------------


def test_the_absent_character_recalls_nothing_however_direct_the_question(conn, world):
    extracted(conn, world, {"memories": [betrayal(conn)]})
    assert texts(recall(conn, world, "Mira", "What did Tobin say about the guild?")) == [DETAIL]
    assert recall(conn, world, "Dara", "What did Tobin say about the guild?") == []
    assert recall(conn, world, "Dara", DETAIL) == []  # even quoting it verbatim


def test_once_told_she_recalls_it_as_hearsay(conn, world):
    extracted(conn, world, {"memories": [betrayal(conn)]})
    memory = conn.execute("SELECT id FROM memories").fetchone()["id"]
    told = {
        "knower": h(conn, "Dara"), "memory": f"M{memory}",
        "source": "told", "told_by": h(conn, "Mira"),
    }  # fmt: skip
    extracted(conn, world, {"knowledge": [told]})
    (got,) = recall(conn, world, "Dara", "What is Tobin planning with the guild?")
    assert got.text == f"(Mira told you) {DETAIL}"
    assert got.breakdown["F"] == -0.5


# --- req 4, 6, 7: forgetting runs on story time, importance resists it ---------------------


def test_six_years_later_only_the_gist_comes_back(conn, world):
    extracted(conn, world, {"memories": [betrayal(conn)]})
    fresh = recall(conn, world, "Mira", "Tell me about Tobin and the guild.", log=False)
    assert [(r.tier, r.text) for r in fresh] == [("sharp", DETAIL)]

    say(conn, world, "Six years later...", skip=6 * YEAR)
    faded = recall(conn, world, "Mira", "Tell me about Tobin and the guild.")
    assert [(r.tier, r.text) for r in faded] == [("hazy", GIST)]
    assert faded[0].gist == GIST


def test_a_trivial_memory_is_simply_gone_after_years_while_the_important_one_lingers(conn, world):
    apron = {
        "kind": "event", "detail": "Tobin wore a green apron.", "gist": "Tobin wore an apron.",
        "importance": 2, "participants": [{"ref": h(conn, "Tobin"), "role": "actor"}],
    }  # fmt: skip
    extracted(conn, world, {"memories": [betrayal(conn), apron]})
    say(conn, world, "Six years later...", skip=6 * YEAR)
    assert texts(recall(conn, world, "Mira", "What do you remember about Tobin?")) == [GIST]


def test_the_strongest_memories_come_first(conn, world):
    minor = betrayal(conn) | {
        "detail": "Tobin ordered ale.",
        "gist": "Tobin drank.",
        "importance": 2,
    }
    extracted(conn, world, {"memories": [minor, betrayal(conn)]})
    got = recall(conn, world, "Mira", "Tobin")
    assert texts(got) == [DETAIL, "Tobin ordered ale."]
    assert got[0].activation > got[1].activation


# --- branches, supersession, the verbatim window -------------------------------------------


def test_a_memory_from_an_abandoned_branch_is_not_recalled(conn, world):
    say(conn, world)
    fork = chat.append_message(conn, world, "assistant", "A", speaker_id=eid(conn, "Mira"))
    extracted(conn, world, {"memories": [betrayal(conn)]})
    assert recall(conn, world, "Mira", "Tobin guild") != []

    chat.append_sibling(conn, fork, "B")  # the user swipes back and takes another road
    assert recall(conn, world, "Mira", "Tobin guild") == []


def test_superseded_truth_sinks_below_what_replaced_it(conn, world):
    old = {"kind": "fact", "detail": "Marta owns The Gull.", "gist": "Marta owns it.",
           "importance": 5,
           "participants": [{"ref": h(conn, "The Gull"), "role": "subject"}]}  # fmt: skip
    extracted(conn, world, {"memories": [old]})
    old_id = conn.execute("SELECT id FROM memories").fetchone()["id"]
    new = old | {"detail": "Tobin owns The Gull now.", "supersedes": f"M{old_id}"}
    extracted(conn, world, {"memories": [new]})
    got = recall(conn, world, "Mira", "Who owns The Gull?")
    assert texts(got)[0] == "Tobin owns The Gull now."
    assert got[-1].breakdown["superseded"] is True


def test_what_is_still_in_the_verbatim_window_is_not_injected_twice(conn, world):
    run_id = extracted(conn, world, {"memories": [betrayal(conn)]})
    first = conn.execute(
        "SELECT from_message_id FROM extraction_runs WHERE id=?", (run_id,)
    ).fetchone()[0]
    assert recall(conn, world, "Mira", "Tobin guild", window_start=first) == []
    assert recall(conn, world, "Mira", "Tobin guild", window_start=first + 99) != []


# --- req 5: pressing a hazy memory ---------------------------------------------------------


def hazy_world(conn, world):
    extracted(conn, world, {"memories": [betrayal(conn)]})
    say(conn, world, "Six years later...", skip=6 * YEAR)
    return conn.execute("SELECT id FROM memories").fetchone()["id"]


def test_recall_is_rehearsal_but_only_once_per_scene(conn, world):
    hazy_world(conn, world)
    for _ in range(5):
        recall(conn, world, "Mira", "Tobin guild")
    rows = conn.execute("SELECT kind, sharp, weight FROM accesses").fetchall()
    assert [tuple(r) for r in rows] == [("recall", 0, 0.5)]  # and the gist never restores detail


def test_pressing_a_hazy_memory_makes_her_strain_with_one_fixed_outcome_per_scene(conn, world):
    memory = hazy_world(conn, world)
    mira = eid(conn, "Mira")
    first = recall(conn, world, "Mira", "Tobin guild")[0]
    assert first.tier == "hazy" and first.breakdown["effortful"] is None  # not pressed yet

    pressed = [recall(conn, world, "Mira", "Tobin guild", pressed={memory})[0] for _ in range(3)]
    scene = conn.execute("SELECT scene_id FROM messages ORDER BY id DESC").fetchone()[0]
    won = effortful_recall(first.breakdown["A_detail"], mira, memory, scene)
    assert pressed[0].breakdown["effortful"] is won
    if won:  # the detail is back, and stays back for the scene
        assert pressed[0].text == f"(after straining to recall) {DETAIL}"
        assert all(DETAIL in p.text for p in pressed)
        assert conn.execute("SELECT sharp FROM accesses").fetchone()["sharp"] == 1
    else:  # pressing harder in the same scene never changes the answer
        assert all(p.text == GIST for p in pressed)


def test_both_outcomes_of_straining_exist(conn, world):
    outcomes = {effortful_recall(-2.43, knower=1, memory=1, scene=s) for s in range(40)}
    assert outcomes == {True, False}


# --- robustness ----------------------------------------------------------------------------


def test_user_text_cannot_break_the_full_text_query(conn, world):
    extracted(conn, world, {"memories": [betrayal(conn)]})
    nasty = 'he said "NEAR( * AND OR NOT guild:^ -betray'
    assert texts(recall(conn, world, "Mira", nasty)) == [DETAIL]
    assert recall(conn, world, "Mira", "", log=False) == recall(
        conn, world, "Mira", "   ", log=False
    )


# --- clarity: how each memory would come back if it came up, the same on every screen ----


@pytest.mark.parametrize(
    ("importance", "later", "tier"),
    [
        (5, 0, "sharp"),  # fresh
        (5, 60 * DAY, "hazy"),  # hazy after about a month
        (5, 3 * YEAR, "hazy"),
        (5, 5 * YEAR, "forgotten"),  # forgotten after about four years
        (9, 6 * YEAR, "hazy"),
        (2, 6 * YEAR, "forgotten"),
    ],
)
def test_clarity_fades_with_story_time_and_importance(conn, world, importance, later, tier):
    extracted(conn, world, {"memories": [betrayal(conn, importance=importance)]})
    say(conn, world, skip=later)
    [memory] = retrieve.inspect(conn, world, eid(conn, "Mira"))
    assert memory["tier"] == tier


def test_a_lie_told_just_now_is_clear(conn, world):
    lie = {
        "kind": "claim", "detail": "Aren insists the ledger is buried by the lighthouse.",
        "gist": "Aren said something about the ledger.", "importance": 6,
        "asserted_by": h(conn, "Aren"), "heard_by": [h(conn, "Mira")],
    }  # fmt: skip
    extracted(conn, world, {"memories": [lie]})
    [memory] = retrieve.inspect(conn, world, eid(conn, "Mira"))
    assert (memory["source"], memory["tier"]) == ("told", "sharp")


def test_clarity_at_an_earlier_time_leaves_out_what_was_learned_later(conn, world):
    covert = betrayal(conn, covert=True, participants=[{"ref": h(conn, "Tobin"), "role": "actor"}])
    extracted(conn, world, {"memories": [covert]})
    secret = conn.execute("SELECT id FROM memories").fetchone()["id"]
    before = chat.active_path(conn, world)[-1]["story_time"]
    mira = eid(conn, "Mira")
    assert retrieve.inspect(conn, world, mira) == []  # only Tobin knows, for now
    say(conn, world, skip=DAY)
    told = {
        "knower": h(conn, "Mira"),
        "memory": f"M{secret}",
        "source": "told",
        "told_by": h(conn, "Tobin"),
    }
    extracted(conn, world, {"knowledge": [told]})
    assert [m["memory_id"] for m in retrieve.inspect(conn, world, mira)] == [secret]
    assert retrieve.inspect(conn, world, mira, now=before) == []


def test_common_knowledge_needs_no_knowledge_row(conn, world):
    conn.execute(
        "INSERT INTO memories"
        "(story_id, kind, story_time, detail, gist, importance, common, is_true)"
        " VALUES(?, 'fact', 0, 'The guild runs the harbour.', 'The guild is powerful.', 7, 1, 1)",
        (world,),
    )
    say(conn, world)
    assert texts(recall(conn, world, "Dara", "Who runs the harbour?")) == [
        "The guild runs the harbour."
    ]
