"""Slice 8: she changes, slowly. Reflections are gated mechanically, growth rings take hold only
on evidence, trait drift is code's and capped, and the user can accept, reject or lock each one."""

import json

import pytest

from kataki import chat, growth, inner, library

MEMS = {
    "M1": {"id": 1, "text": "Aren carried Mira's crates up from the harbour.", "scene": "s1"},
    "M2": {"id": 2, "text": "Mira asked Aren to help her with the ledger.", "scene": "s1"},
    "M3": {"id": 3, "text": "Aren came back after two days away.", "scene": "s2"},
}
PEOPLE = {"P12": 12}
NAMES = {"aren", "mira", "tobin"}


def gate(item, kind="relationship"):
    return growth.gate(item, kind, MEMS, PEOPLE, NAMES)


# --- the gate (pure) -----------------------------------------------------------------------------


def test_the_gate_passes_a_cited_plain_line():
    ok = {"about": "P12", "line": "He keeps coming back, even when I push him away.",
          "sources": ["M1", "M3"]}  # fmt: skip
    assert gate(ok) is None
    assert gate({"line": "I have learned to lean on Aren.", "sources": ["M2"]}, "self") is None


@pytest.mark.parametrize(
    "item, why",
    [
        ({"about": "P12", "line": "He keeps coming back.", "sources": []}, "no source"),
        ({"about": "P12", "line": "He keeps coming back.", "sources": ["M9"]}, "unknown"),
        ({"about": "P99", "line": "He keeps coming back.", "sources": ["M1"]}, "someone"),
        ({"about": "P12", "line": " ".join(["word"] * 26), "sources": ["M1"]}, "too long"),
        ({"about": "P12", "line": "He came back 3 times.", "sources": ["M1"]}, "number"),
        ({"about": "P12", "line": "He came back seven times.", "sources": ["M1"]}, "number"),
        ({"about": "P12", "line": "He sails with Captain Vey now.", "sources": ["M1"]}, "name"),
    ],
)
def test_the_gate_drops_what_it_cannot_trace(item, why):
    assert why in gate(item)


def test_a_number_or_name_from_the_cited_memories_is_fine():
    item = {"about": "P12", "line": "Two days away, and Aren still came back.", "sources": ["M3"]}
    assert gate(item) is None


def test_a_ring_needs_three_memories_from_two_scenes():
    ring = {"kind": "habit", "claim": "learned to ask for help", "sources": ["M1", "M2", "M3"]}
    assert growth.gate(ring, "ring", MEMS, PEOPLE, NAMES) is None
    thin = {**ring, "sources": ["M1", "M2"]}
    assert "evidence" in growth.gate(thin, "ring", MEMS, PEOPLE, NAMES)
    one_scene = {**MEMS, "M3": {**MEMS["M3"], "scene": "s1"}}
    assert "evidence" in growth.gate(ring, "ring", one_scene, PEOPLE, NAMES)
    long = {**ring, "claim": " ".join(["help"] * 16)}
    assert "too long" in growth.gate(long, "ring", MEMS, PEOPLE, NAMES)


def test_six_sentences_at_most_about_herself():
    line = "I lean on him. " * 7
    assert "too long" in gate({"line": line, "sources": ["M1"]}, "self")


# --- trait drift (pure) --------------------------------------------------------------------------


def test_a_direction_is_one_axis_and_a_small_step():
    assert growth.step("warmer") == {"warmth": 2}
    assert growth.step("firmer") == {"yielding": -2}
    assert growth.step("none") is None and growth.step("kinder") is None


def ring(status, delta, rid=1):
    return {"id": rid, "status": status, "trait_delta": delta}


def test_drift_counts_only_rings_and_is_capped():
    rows = [ring("ring", {"warmth": 2}, i) for i in range(8)]
    rows += [
        ring("seed", {"warmth": 2}),
        ring("rejected", {"candor": -2}),
        ring("past", {"candor": 2}),
    ]
    rows += [ring("locked", {"candor": -2})]
    assert growth.drift(rows) == {"warmth": 10, "candor": -2}
    assert growth.drift([]) == {}


# --- rows: versions, the user's say, the profile -------------------------------------------------


@pytest.fixture
def story(conn):
    mira = library.create_item(conn, "character", "Mira")
    aren = library.create_item(conn, "character", "Aren")
    sid = library.create_story(conn, "Low Tide", character_ids=[mira], persona_id=aren)
    return sid


def ent(conn, story, name):
    return conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name=?", (story, name)
    ).fetchone()[0]


def test_accept_reject_lock_are_new_versions(conn, story):
    mira = ent(conn, story, "Mira")
    with conn:
        seed = growth.write(conn, story, mira, "habit", "learned to ask for help", [1, 2, 3],
                            "seed", 0, delta={"warmth": 2})  # fmt: skip
    path = chat.active_path(conn, story)
    [r] = growth.current(conn, mira, path)
    assert (r["id"], r["status"], r["trait_delta"]) == (seed, "seed", {"warmth": 2})
    accepted = growth.act(conn, seed, "accept")
    [r] = growth.current(conn, mira, path)
    assert (r["id"], r["status"], r["supersedes_id"]) == (accepted, "ring", seed)
    assert r["sources"] == [1, 2, 3] and r["message_id"] is None and r["run_id"] is None
    assert inner.profile(conn, mira)["axes"]["warmth"][0] == 52
    growth.act(conn, accepted, "reject")
    [r] = growth.current(conn, mira, path)
    assert r["status"] == "rejected"
    assert inner.profile(conn, mira)["axes"]["warmth"][0] == 50  # the drift went with it
    old = conn.execute("SELECT status FROM reflections WHERE id=?", (seed,)).fetchone()[0]
    assert old == "seed"  # append-only
    locked = growth.act(conn, r["id"], "lock")
    assert growth.current(conn, mira, path)[0]["id"] == locked
    with pytest.raises(ValueError):
        growth.act(conn, locked, "delete")


def test_the_profile_drifts_only_with_the_feature_on(conn, story):
    mira = ent(conn, story, "Mira")
    with conn:
        growth.write(conn, story, mira, "stance", "stands up for herself", [1], "ring", 0,
                     delta={"dominance": 2})  # fmt: skip
    assert inner.profile(conn, mira)["axes"]["dominance"][0] == 52
    conn.execute(
        "INSERT INTO settings(key, value) VALUES('features.mind.growth', ?)", (json.dumps(False),)
    )
    conn.commit()
    assert inner.profile(conn, mira)["axes"]["dominance"][0] == 50


def test_another_branchs_reflection_does_not_count(conn, story):
    mira, aren = ent(conn, story, "Mira"), ent(conn, story, "Aren")
    a = chat.append_message(conn, story, "user", "Hello.", aren)
    b = chat.append_sibling(conn, a, "Hi.")
    run = conn.execute(
        "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger, status)"
        " VALUES(?, 0, ?, 'between', 'ok')",
        (story, a),
    ).lastrowid
    with conn:
        growth.write(conn, story, mira, "self", "I lean on people now.", [1], "ring", 0,
                     message_id=a, run_id=run)  # fmt: skip
    assert len(growth.current(conn, mira, chat.path_to(conn, a))) == 1
    assert growth.current(conn, mira, chat.path_to(conn, b)) == []
