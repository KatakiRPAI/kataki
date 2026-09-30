"""Deterministic apply(): canned extraction JSON in, memory rows out. No LLM anywhere."""

import json

import pytest

from kataki import chat, db, extract, library


@pytest.fixture
def world(conn):
    ids = {
        name: library.create_item(conn, "character", name, data={"aliases": aliases})
        for name, aliases in {"Mira": ["the courier"], "Tobin": [], "Dara": [], "Aren": []}.items()
    }
    gull = library.create_item(conn, "place", "The Gull", data={"aliases": ["the tavern"]})
    story = library.create_story(
        conn,
        "Low Tide",
        character_ids=[ids["Mira"], ids["Tobin"], ids["Dara"]],
        place_id=gull,
        persona_id=ids["Aren"],
    )
    scene = conn.execute("SELECT id FROM scenes WHERE story_id=?", (story,)).fetchone()["id"]
    # Dara is not in the room for what follows
    conn.execute(
        "INSERT INTO presence(scene_id, entity_id, present) VALUES(?, ?, 0)",
        (scene, eid(conn, "Dara")),
    )
    return story


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


def h(conn, name):
    return f"E{eid(conn, name)}"


def talk(conn, story, n=2):
    first = chat.append_message(conn, story, "user", "line", speaker_id=eid(conn, "Aren"))
    last = first
    for _ in range(n - 1):
        last = chat.append_message(conn, story, "assistant", "line", speaker_id=eid(conn, "Mira"))
    return first, last


def run(conn, story, data, window=None):
    first, last = window or talk(conn, story)
    run_id = extract.open_run(conn, story, first, last, "cadence")
    extract.apply(conn, run_id, data)
    return run_id


def betrayal(conn, **extra):
    return {
        "kind": "event",
        "detail": "Tobin told Mira he would betray the guild at the docks tonight.",
        "gist": "Tobin spoke of turning on the guild.",
        "importance": 9,
        "participants": [
            {"ref": h(conn, "Tobin"), "role": "actor"},
            {"ref": h(conn, "Mira"), "role": "target"},
        ],
        "place": h(conn, "The Gull"),
        "tags": ["betrayal", "guild"],
        **extra,
    }


def knowers(conn, memory_id):
    rows = conn.execute(
        "SELECT e.name, k.source FROM knowledge k JOIN entities e ON e.id=k.knower_id"
        " WHERE k.memory_id=?",
        (memory_id,),
    )
    return {r["name"]: r["source"] for r in rows}


def only_memory(conn):
    return conn.execute("SELECT * FROM memories ORDER BY id DESC LIMIT 1").fetchone()


# --- req 1: things that are mentioned come to exist --------------------------------------


def test_a_new_entity_is_created_with_its_aliases_and_linked_to_what_happened(conn, world):
    data = {
        "new_entities": [
            {"handle": "N1", "kind": "item", "name": "the sealed letter", "aliases": ["the letter"]}
        ],
        "memories": [
            betrayal(conn)
            | {
                "participants": [
                    {"ref": h(conn, "Mira"), "role": "actor"},
                    {"ref": "N1", "role": "item"},
                ]
            }
        ],
    }
    run_id = run(conn, world, data)
    letter = conn.execute("SELECT * FROM entities WHERE name='the sealed letter'").fetchone()
    assert (letter["kind"], letter["run_id"]) == ("item", run_id)
    aliases = {
        r["alias"]
        for r in conn.execute("SELECT alias FROM aliases WHERE entity_id=?", (letter["id"],))
    }
    assert aliases == {"the sealed letter", "the letter"}
    linked = conn.execute(
        "SELECT role FROM memory_entities WHERE entity_id=?", (letter["id"],)
    ).fetchone()
    assert linked["role"] == "item"


def test_a_new_entity_that_matches_a_known_alias_is_merged_not_duplicated(conn, world):
    data = {
        "new_entities": [{"handle": "N1", "kind": "character", "name": "The Courier"}],
        "memories": [betrayal(conn) | {"participants": [{"ref": "N1", "role": "actor"}]}],
    }
    run(conn, world, data)
    assert conn.execute("SELECT count(*) FROM entities WHERE kind='character'").fetchone()[0] == 4
    assert conn.execute("SELECT entity_id FROM memory_entities WHERE role='actor'").fetchone()[
        "entity_id"
    ] == eid(conn, "Mira")


def test_pronouns_never_become_entities(conn, world):
    run(conn, world, {"new_entities": [{"handle": "N1", "kind": "character", "name": "She"}]})
    assert conn.execute("SELECT count(*) FROM entities WHERE name='She'").fetchone()[0] == 0


# --- req 2: cross-linking falls out of the participant list ------------------------------


def test_everyone_in_an_event_is_linked_to_each_other_and_to_the_place(conn, world):
    run(conn, world, {"memories": [betrayal(conn)]})
    neighbours = {
        r["name"]
        for r in conn.execute(
            "SELECT DISTINCT e.name FROM memory_entities mine"
            " JOIN memory_entities theirs ON theirs.memory_id=mine.memory_id"
            " JOIN entities e ON e.id=theirs.entity_id"
            " WHERE mine.entity_id=? AND theirs.entity_id<>mine.entity_id",
            (eid(conn, "Mira"),),
        )
    }
    assert {"Tobin", "The Gull"} <= neighbours


# --- req 3: who knows is decided by code, from presence ----------------------------------


def test_those_present_witness_an_event_and_the_absent_do_not(conn, world):
    run(conn, world, {"memories": [betrayal(conn)]})
    assert knowers(conn, only_memory(conn)["id"]) == {
        "Tobin": "witnessed",
        "Mira": "witnessed",
        "Aren": "witnessed",  # in the room, so the persona saw it too
    }


def test_a_covert_event_is_known_only_to_its_participants(conn, world):
    run(conn, world, {"memories": [betrayal(conn, covert=True)]})
    assert set(knowers(conn, only_memory(conn)["id"])) == {"Tobin", "Mira"}


def test_being_told_later_creates_a_knowledge_line_with_its_source(conn, world):
    run(conn, world, {"memories": [betrayal(conn)]})
    memory = only_memory(conn)["id"]
    told = {
        "knowledge": [
            {
                "knower": h(conn, "Dara"),
                "memory": f"M{memory}",
                "source": "told",
                "told_by": h(conn, "Mira"),
            }
        ]
    }
    run(conn, world, told)
    row = conn.execute(
        "SELECT * FROM knowledge WHERE knower_id=? AND memory_id=?", (eid(conn, "Dara"), memory)
    ).fetchone()
    assert (row["source"], row["told_by_id"], row["fidelity"]) == ("told", eid(conn, "Mira"), -0.5)


def test_memory_time_is_the_story_clock_of_its_source_message(conn, world):
    first, last = talk(conn, world, n=3)
    run(conn, world, {"memories": [betrayal(conn)]}, window=(first, last))
    clock = conn.execute("SELECT story_time FROM messages WHERE id=?", (last,)).fetchone()[0]
    memory = only_memory(conn)
    assert (memory["story_time"], memory["from_message_id"], memory["to_message_id"]) == (
        clock,
        first,
        last,
    )


# --- req 5: lies ------------------------------------------------------------------------


def test_what_a_character_says_is_a_claim_that_never_overwrites_the_truth(conn, world):
    run(conn, world, {"memories": [betrayal(conn)]})
    truth = only_memory(conn)["id"]
    lie = {
        "kind": "claim",
        "detail": "Aren insists Tobin was never at the Gull that night.",
        "gist": "Aren said Tobin was not there.",
        "importance": 6,
        "asserted_by": h(conn, "Aren"),
        "heard_by": [h(conn, "Mira")],
        "participants": [{"ref": h(conn, "Tobin"), "role": "subject"}],
        "supersedes": f"M{truth}",  # a claim may ask; the code refuses
    }
    data = {
        "memories": [lie],
        "contradictions": [
            {
                "claim": 0,
                "contradicts": f"M{truth}",
                "hearer": h(conn, "Mira"),
                "resolution": "challenged",
            }
        ],
    }
    run(conn, world, data)
    claim = only_memory(conn)
    assert (claim["kind"], claim["is_true"], claim["supersedes_id"]) == ("claim", 0, None)
    assert claim["asserted_by"] == eid(conn, "Aren")
    heard = conn.execute(
        "SELECT source, told_by_id, belief FROM knowledge WHERE memory_id=? AND knower_id=?",
        (claim["id"], eid(conn, "Mira")),
    ).fetchone()
    assert tuple(heard) == ("told", eid(conn, "Aren"), 0.1)  # challenged: she does not buy it


@pytest.mark.parametrize(("resolution", "belief"), [("doubted", 0.5), ("accepted", 0.9)])
def test_how_the_hearer_reacted_sets_how_much_they_believe(conn, world, resolution, belief):
    run(conn, world, {"memories": [betrayal(conn)]})
    truth = only_memory(conn)["id"]
    lie = {
        "kind": "claim", "detail": "d", "gist": "g", "importance": 5,
        "asserted_by": h(conn, "Aren"), "heard_by": [h(conn, "Mira")],
    }  # fmt: skip
    clash = {
        "claim": 0,
        "contradicts": f"M{truth}",
        "hearer": h(conn, "Mira"),
        "resolution": resolution,
    }
    run(conn, world, {"memories": [lie], "contradictions": [clash]})
    row = conn.execute(
        "SELECT belief FROM knowledge WHERE memory_id=? AND knower_id=?",
        (only_memory(conn)["id"], eid(conn, "Mira")),
    ).fetchone()
    assert row["belief"] == belief


def test_a_memory_keeps_the_exact_line_it_came_from_and_the_run_keeps_its_range(conn, world):
    first, last = talk(conn, world, n=3)
    run(conn, world, {"memories": [betrayal(conn, line=2)]}, window=(first, last))
    memory = only_memory(conn)
    second = [m["id"] for m in chat.active_path(conn, world)][-2]
    assert memory["message_id"] == second
    assert (memory["from_message_id"], memory["to_message_id"]) == (first, last)


def test_a_claim_records_the_memory_it_contradicts(conn, world):
    run(conn, world, {"memories": [betrayal(conn)]})
    truth = only_memory(conn)["id"]
    assert only_memory(conn)["contradicts_id"] is None
    lie = {
        "kind": "claim", "detail": "d", "gist": "g", "importance": 5,
        "asserted_by": h(conn, "Aren"), "heard_by": [h(conn, "Mira")],
    }  # fmt: skip
    clash = {
        "claim": 0,
        "contradicts": f"M{truth}",
        "hearer": h(conn, "Mira"),
        "resolution": "doubted",
    }
    run(conn, world, {"memories": [lie], "contradictions": [clash]})
    assert only_memory(conn)["contradicts_id"] == truth


def test_narration_can_supersede_an_earlier_fact(conn, world):
    fact = {
        "kind": "fact",
        "detail": "The Gull is owned by Marta.",
        "gist": "Marta owns it.",
        "importance": 4,
    }
    run(conn, world, {"memories": [fact]})
    old = only_memory(conn)["id"]
    newer = fact | {"detail": "The Gull now belongs to Tobin.", "supersedes": f"M{old}"}
    run(conn, world, {"memories": [newer]})
    assert only_memory(conn)["supersedes_id"] == old
    assert conn.execute("SELECT count(*) FROM memories").fetchone()[0] == 2  # nothing deleted


# --- req 8: tags, flags, edges, presence, summaries --------------------------------------


def test_tags_are_recall_hooks_in_full_text_search(conn, world):
    run(conn, world, {"memories": [betrayal(conn)]})
    hit = conn.execute(
        "SELECT rowid FROM memories_fts WHERE memories_fts MATCH 'betrayal'"
    ).fetchone()
    assert hit["rowid"] == only_memory(conn)["id"]
    tagged = conn.execute("SELECT count(*) FROM taggings WHERE obj='memory'").fetchone()[0]
    assert tagged == 2


def test_state_is_an_append_only_log_with_story_time(conn, world):
    data = {
        "flags": [{"entity": h(conn, "Tobin"), "key": "injured", "value": "cut on the left hand"}],
        "edges": [{"src": h(conn, "Mira"), "dst": h(conn, "Tobin"), "rel": "distrusts"}],
        "presence": [{"entity": h(conn, "Tobin"), "present": False}],
        "scene_summary": "Tobin let slip his plan and left.",
    }
    first, last = talk(conn, world)
    run_id = run(conn, world, data, window=(first, last))
    clock = conn.execute("SELECT story_time FROM messages WHERE id=?", (last,)).fetchone()[0]

    flag = conn.execute("SELECT * FROM flags").fetchone()
    assert (flag["key"], flag["value"], flag["story_time"], flag["run_id"]) == (
        "injured", "cut on the left hand", clock, run_id,
    )  # fmt: skip
    assert conn.execute("SELECT rel FROM edges").fetchone()["rel"] == "distrusts"
    gone = conn.execute(
        "SELECT present, message_id FROM presence WHERE entity_id=? ORDER BY id DESC",
        (eid(conn, "Tobin"),),
    ).fetchone()
    assert (gone["present"], gone["message_id"]) == (0, last)
    assert (
        conn.execute("SELECT text FROM summaries").fetchone()["text"].startswith("Tobin let slip")
    )


# --- robustness: bad items are skipped, not fatal ----------------------------------------


def test_a_bad_reference_becomes_a_warning_and_the_rest_still_applies(conn, world):
    data = {
        "memories": [
            betrayal(conn),
            betrayal(conn)
            | {"participants": [{"ref": "E99999", "role": "actor"}], "detail": "ghost"},
            {"kind": "event", "importance": "very"},  # not even the right shape
        ],
        "flags": [{"entity": "N7", "key": "x", "value": "y"}],  # N7 was never declared
    }
    run_id = run(conn, world, data)
    row = conn.execute(
        "SELECT status, warnings FROM extraction_runs WHERE id=?", (run_id,)
    ).fetchone()
    assert row["status"] == "ok" and len(json.loads(row["warnings"])) == 3
    assert [r["detail"] for r in conn.execute("SELECT detail FROM memories")] == [
        betrayal(conn)["detail"]
    ]


# --- task 14: idempotency and branches ----------------------------------------------------


def counts(conn):
    tables = (
        "entities",
        "aliases",
        "memories",
        "memory_entities",
        "knowledge",
        "flags",
        "taggings",
    )
    return {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in tables}


def test_retrying_a_run_leaves_exactly_the_same_rows(conn, world):
    data = {
        "new_entities": [{"handle": "N1", "kind": "item", "name": "the ledger"}],
        "memories": [betrayal(conn) | {"participants": [{"ref": "N1", "role": "item"}]}],
        "flags": [{"entity": h(conn, "Tobin"), "key": "mood", "value": "tense"}],
    }
    window = talk(conn, world)
    run(conn, world, data, window=window)
    before = counts(conn)

    db.discard_run(conn, conn.execute("SELECT max(id) FROM extraction_runs").fetchone()[0])
    assert counts(conn)["memories"] == 0 and counts(conn)["flags"] == 0
    run(conn, world, data, window=window)
    assert counts(conn) == before


def test_invalid_output_applies_nothing_and_fails_the_run(conn, world):
    before = counts(conn)
    first, last = talk(conn, world)
    run_id = extract.open_run(conn, world, first, last, "cadence")
    with pytest.raises(ValueError):
        extract.apply(conn, run_id, {"memories": "none, sorry"})
    assert counts(conn) == before
    assert (
        conn.execute("SELECT status FROM extraction_runs WHERE id=?", (run_id,)).fetchone()[0]
        == "failed"
    )


def test_memories_follow_the_branch_they_were_extracted_on(conn, world):
    chat.append_message(conn, world, "user", "one", speaker_id=eid(conn, "Aren"))
    reply_a = chat.append_message(conn, world, "assistant", "A", speaker_id=eid(conn, "Mira"))
    on_a = chat.append_message(conn, world, "user", "deeper on A", speaker_id=eid(conn, "Aren"))
    run_a = extract.open_run(conn, world, reply_a, on_a, "cadence")
    extract.apply(conn, run_a, {"memories": [betrayal(conn)]})
    assert db.live_runs(conn, world) == {run_a}

    chat.append_sibling(conn, reply_a, "B")  # swipe to another reply: a different branch
    assert db.live_runs(conn, world) == set()

    chat.set_leaf(conn, world, reply_a)
    assert db.live_runs(conn, world) == {run_a}


# --- suspicion (minds slice 4): a believed contradiction makes her claim doubted -----------------


def _belief(conn, memory_id, who):
    live = db.live_runs(conn, conn.execute("SELECT id FROM stories").fetchone()[0])
    where, args = db.live_filter(live)
    row = conn.execute(
        f"SELECT belief, source, told_by_id FROM knowledge WHERE memory_id=? AND knower_id=?"
        f" AND {where} ORDER BY id DESC LIMIT 1",
        [memory_id, eid(conn, who), *args],
    ).fetchone()
    return tuple(row)


@pytest.mark.parametrize(
    ("resolution", "belief"), [("accepted", 0.1), ("doubted", 0.5), ("challenged", 0.9)]
)
def test_believing_a_contradiction_makes_the_earlier_claim_doubted(conn, world, resolution, belief):
    said = {
        "kind": "claim", "detail": "Mira said the ring was her grandmother's.", "gist": "g",
        "importance": 5, "asserted_by": h(conn, "Mira"), "heard_by": [h(conn, "Aren")],
    }  # fmt: skip
    run(conn, world, {"memories": [said]})
    hers = only_memory(conn)["id"]
    assert _belief(conn, hers, "Aren") == (0.9, "told", eid(conn, "Mira"))
    other = said | {
        "detail": "Tobin said the ring was her brother's.",
        "asserted_by": h(conn, "Tobin"),
    }
    clash = {
        "claim": 0,
        "contradicts": f"M{hers}",
        "hearer": h(conn, "Aren"),
        "resolution": resolution,
    }
    second = run(conn, world, {"memories": [other], "contradictions": [clash]})
    assert _belief(conn, hers, "Aren") == (belief, "told", eid(conn, "Mira"))  # source kept
    assert _belief(conn, hers, "Mira")[0] == 1.0  # she knows what she said
    db.discard_run(conn, second)
    assert _belief(conn, hers, "Aren")[0] == 0.9  # the reading undone, the doubt goes with it


# --- minds slice 6: how it felt, what could be mixed up, what must never change -----------


def test_a_memory_keeps_how_it_felt_its_mix_ups_and_its_lock(conn, world):
    alts = [{"slot": "where", "right": "at the docks", "wrong": "at the mill"}]
    run(conn, world, {"memories": [betrayal(conn, valence=-0.7, alts=alts, core_locked=True)]})
    m = only_memory(conn)
    assert (m["valence"], json.loads(m["alts"]), m["core_locked"]) == (-0.7, alts, 1)


def test_a_mix_up_whose_truth_is_not_in_the_detail_is_dropped_with_a_warning(conn, world):
    alts = [
        {"slot": "when", "right": "on Thursday", "wrong": "on Tuesday"},  # not in the detail
        {"slot": "where", "right": "the docks", "wrong": "the mill"},
    ]
    same = [{"slot": "where", "right": "At The Docks", "wrong": "at the docks"}]  # no change
    first, last = talk(conn, world)
    run_id = extract.open_run(conn, world, first, last, "cadence")
    data = {"memories": [betrayal(conn, alts=alts), betrayal(conn, alts=same)]}
    warnings = extract.apply(conn, run_id, data)
    rows = conn.execute("SELECT alts FROM memories ORDER BY id").fetchall()
    assert [json.loads(r[0]) if r[0] else None for r in rows] == [[alts[1]], None]
    assert sum("alts" in w for w in warnings) == 2


def test_a_bad_valence_or_mix_up_never_costs_the_memory(conn, world):
    bad = betrayal(
        conn, valence="very sad", alts=[{"slot": "why", "right": 3}, "x"], core_locked=None
    )
    run(conn, world, {"memories": [bad, betrayal(conn, valence=7)]})
    rows = conn.execute("SELECT valence, alts, core_locked FROM memories ORDER BY id").fetchall()
    assert [tuple(r) for r in rows] == [(None, None, 0), (1.0, None, 0)]  # clamped, not dropped


def test_the_reader_is_asked_for_them_only_with_the_feature_on(conn, world):
    talk(conn, world)
    chunk = extract.pending(conn, world)
    messages, schema = extract.prompt(conn, world, chunk)
    fields = schema["$defs"]["MemoryItem"]["properties"]
    assert {"valence", "alts", "core_locked"} <= set(fields)
    assert "alts:" in messages[0]["content"]
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.recall', 'false')")
    messages, off = extract.prompt(conn, world, chunk)
    assert not {"valence", "alts", "core_locked"} & set(off["$defs"]["MemoryItem"]["properties"])
    assert "Alt" not in off["$defs"] and messages[0]["content"] == extract.INSTRUCTIONS
    grown = len(json.dumps(schema)) / len(json.dumps(off))
    assert grown < 1.25, grown  # note 22 C18: a slice grows the reader's schema by 25% at most
