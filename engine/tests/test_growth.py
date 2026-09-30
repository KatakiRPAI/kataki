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
        seed = growth.write(conn, story, mira, "habit", "learned to ask for help", [97, 98, 99],
                            "seed", 0, delta={"warmth": 2})  # fmt: skip
    path = chat.active_path(conn, story)
    [r] = growth.current(conn, mira, path)
    assert (r["id"], r["status"], r["trait_delta"]) == (seed, "seed", {"warmth": 2})
    accepted = growth.act(conn, seed, "accept")
    [r] = growth.current(conn, mira, path)
    assert (r["id"], r["status"], r["supersedes_id"]) == (accepted, "ring", seed)
    assert r["sources"] == [97, 98, 99] and r["message_id"] is None and r["run_id"] is None
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


# --- the deep pass (note 22 §3 B2) -----------------------------------------------------------------

from kataki import between, clock, turns  # noqa: E402

DAY = clock.DAY
DIARY = {"diary": "A long week. I kept the office going.", "worth_telling": [], "seeds": [],
         "preoccupation": "the ledger"}  # fmt: skip


def setting(conn, key: str, value) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)", (key, json.dumps(value))
    )
    conn.commit()


@pytest.fixture
def cards(conn):
    return {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}


def make(conn, cards) -> int:
    return library.create_story(
        conn, "Low Tide", character_ids=[cards["Mira"], cards["Tobin"]], persona_id=cards["Aren"]
    )


def hers(conn, story: int, who: int, detail: str, t: int = 0, importance: int = 8) -> int:
    mid = conn.execute(
        "INSERT INTO memories(story_id, kind, story_time, detail, gist, importance)"
        " VALUES(?, 'event', ?, ?, ?, ?)",
        (story, t, detail, detail, importance),
    ).lastrowid
    conn.execute(
        "INSERT INTO knowledge(knower_id, memory_id, source, learned_story_time)"
        " VALUES(?, ?, 'witnessed', ?)",
        (who, mid, t),
    )
    conn.commit()
    return mid


def skipped(conn, cards, words="eight days later"):
    story = make(conn, cards)
    mira, tobin, aren = (ent(conn, story, n) for n in ("Mira", "Tobin", "Aren"))
    chat.append_message(conn, story, "user", "See you, Mira.", aren)
    mems = [
        hers(conn, story, mira, "Aren carried Mira's crates up from the harbour.", 0),
        hers(conn, story, mira, "Mira asked Aren to help her with the ledger.", 10),
        hers(conn, story, mira, "Aren came back to the office after a storm.", DAY + 10),
    ]
    secret = hers(conn, story, tobin, "Tobin buried the strongbox under the pier.", 0)
    turns.say(conn, story, skip=words)
    run = between.at_skip(conn, story, chat.active_path(conn, story))
    return story, run, mira, aren, mems, secret


def raw(conn, run) -> dict:
    row = conn.execute("SELECT raw FROM extraction_runs WHERE id=?", (run,)).fetchone()
    return json.loads(row[0])


def test_a_long_skip_calls_for_a_deep_pass_and_a_short_one_not(conn, cards):
    story, run, mira, *_ = skipped(conn, cards)
    tobin = ent(conn, story, "Tobin")
    assert raw(conn, run)["deep"] == {str(mira): "long_skip", str(tobin): "long_skip"}
    _, run2, *_ = skipped(conn, cards, "two days later")
    assert "deep" not in raw(conn, run2)


def test_lite_and_off_never_reflect(conn, cards):
    setting(conn, "mind.level", "lite")
    _, run, *_ = skipped(conn, cards)
    assert "deep" not in raw(conn, run)
    setting(conn, "mind.level", "standard")
    setting(conn, "features.mind.growth", False)
    _, run, *_ = skipped(conn, cards)
    assert "deep" not in raw(conn, run)


def test_forty_new_memories_or_a_closed_chapter_call_for_one(conn, cards):
    story = make(conn, cards)
    mira, aren = ent(conn, story, "Mira"), ent(conn, story, "Aren")
    chat.append_message(conn, story, "user", "Hello.", aren)
    for i in range(growth.PILE):
        hers(conn, story, mira, f"Small thing number {i}.", i)
    path = chat.path_to(conn, turns.say(conn, story, skip="two days later"))
    assert growth.trigger(conn, story, mira, path, "standard") == "memories"
    assert growth.trigger(conn, story, mira, path, "lite") is None
    story2 = make(conn, cards)
    a = chat.append_message(conn, story2, "user", "Hello.", ent(conn, story2, "Aren"))
    chapter = library.open_chapter(conn, story2, "One", a)
    library.close_chapter(conn, chapter, a)
    path = chat.path_to(conn, turns.say(conn, story2, skip="two days later"))
    mira2 = ent(conn, story2, "Mira")
    assert growth.trigger(conn, story2, mira2, path, "standard") == "arc"
    run = between.at_skip(conn, story2, path)  # her deep pass ran on that skip
    done = raw(conn, run) | {"b1": {str(mira2): "ok"}}
    conn.execute("UPDATE extraction_runs SET raw=? WHERE id=?", (json.dumps(done), run))
    path = chat.path_to(conn, turns.say(conn, story2, skip="two days later"))
    assert growth.trigger(conn, story2, mira2, path, "standard") is None  # that arc is behind her


GOOD = {
    "relationship": [{"about": None, "line": "He keeps coming back, even after the storm.",
                      "sources": None}],
    "self": {"line": "I ask for help now.", "sources": None},
    "rings": [
        {"kind": "habit", "claim": "learned to ask for help", "sources": None, "trait": "softer"},
        {"kind": "belief", "claim": "Captain Vey will save the harbour", "sources": None,
         "trait": "none"},
    ],
}  # fmt: skip


def answer(mems, aren, line: str | None = None) -> dict:
    deep = json.loads(json.dumps(GOOD))
    handles = [f"M{m}" for m in mems]
    deep["relationship"][0] |= {"about": f"P{aren}", "sources": handles[:2]}
    if line:
        deep["relationship"][0]["line"] = line
    deep["self"]["sources"] = handles[1:2]
    for r in deep["rings"]:
        r["sources"] = handles
    return DIARY | {"deep": deep}


@pytest.mark.anyio
async def test_the_one_diary_call_reflects_on_her_own_memories_only(local_model, cards, backend):
    conn = local_model
    story, run, mira, aren, mems, secret = skipped(conn, cards)
    backend.say(json.dumps(answer(mems, aren)))
    assert await between.think(conn, backend.llm, story, run, mira)
    assert len(backend.requests) == 1  # no second call
    sent = "\n".join(m["content"] for m in backend.requests[0]["messages"])
    assert f"M{mems[0]}: Aren carried Mira's crates" in sent and f"P{aren}: Aren" in sent
    assert "strongbox" not in sent and f"M{secret}" not in sent
    assert "deep" in json.dumps(backend.requests[0].get("response_format", {}))
    path = chat.active_path(conn, story)
    rows = {r["kind"]: r for r in growth.current(conn, mira, path)}
    assert rows["relationship"]["status"] == "ring" and rows["relationship"]["subject_id"] == aren
    assert rows["self"]["status"] == "ring"
    assert rows["habit"]["status"] == "seed" and rows["habit"]["trait_delta"] == {"yielding": 2}
    assert "belief" not in rows  # a new name: dropped
    assert all(r["run_id"] == run for r in rows.values())
    [warning] = raw(conn, run)["deep_warnings"][str(mira)]
    assert "Vey" in warning
    assert inner.profile(conn, mira)["axes"]["yielding"][0] == 50  # a seed nudges nothing yet
    chat.set_skip(conn, path[-1]["id"], 0)  # undo the skip: it all goes
    assert growth.current(conn, mira, chat.active_path(conn, story)) == []


@pytest.mark.anyio
async def test_a_second_deep_pass_replaces_her_line_but_keeps_rings(local_model, cards, backend):
    conn = local_model
    story, run, mira, aren, mems, _ = skipped(conn, cards)
    backend.say(json.dumps(answer(mems, aren)))
    await between.think(conn, backend.llm, story, run, mira)
    turns.say(conn, story, skip="two weeks later")
    run2 = between.at_skip(conn, story, chat.active_path(conn, story))
    backend.say(json.dumps(answer(mems, aren, "He stays.")))
    await between.think(conn, backend.llm, story, run2, mira)
    rows = growth.current(conn, mira, chat.active_path(conn, story))
    assert [r["text"] for r in rows if r["kind"] == "relationship"] == ["He stays."]
    assert len([r for r in rows if r["kind"] == "habit"]) == 2  # rings only add


@pytest.mark.anyio
async def test_a_failed_call_or_no_deep_section_leaves_a_warning(local_model, cards, backend):
    conn = local_model
    story, run, mira, *_ = skipped(conn, cards)
    backend.say("not json", "still not json")
    assert not await between.think(conn, backend.llm, story, run, mira)
    assert "did not run" in raw(conn, run)["deep_warnings"][str(mira)][0]
    tobin = ent(conn, story, "Tobin")
    backend.say(json.dumps(DIARY))  # a diary, but no deep section: the diary is kept
    assert await between.think(conn, backend.llm, story, run, tobin)
    assert "missing" in raw(conn, run)["deep_warnings"][str(tobin)][0]


# --- reinforcement (note 17 §6): a seed takes hold only when later scenes bear it out -----------


def seeded(conn, cards, status="seed"):
    story = make(conn, cards)
    mira, aren = ent(conn, story, "Mira"), ent(conn, story, "Aren")
    chat.append_message(conn, story, "user", "Hello, Mira.", aren)
    with conn:
        rid = growth.write(conn, story, mira, "habit", "learned to ask for help", [97, 98, 99],
                           status, 0, delta={"warmth": 2})  # fmt: skip
    return story, mira, rid


def bear_out(conn, story, mira, days=(1, 1, 2)):
    for n, d in enumerate(days):
        hers(conn, story, mira, f"Mira asked Tobin for help with the nets ({n}).", d * DAY)


def skip_now(conn, story, words="three days later") -> int:
    turns.say(conn, story, skip=words)
    return between.at_skip(conn, story, chat.active_path(conn, story))


def status(conn, story, mira) -> str:
    return growth.current(conn, mira, chat.active_path(conn, story))[0]["status"]


def test_a_seed_borne_out_in_two_later_scenes_becomes_a_ring(conn, cards):
    story, mira, _ = seeded(conn, cards)
    bear_out(conn, story, mira)
    assert inner.profile(conn, mira)["axes"]["warmth"][0] == 50
    run = skip_now(conn, story)
    [r] = growth.current(conn, mira, chat.active_path(conn, story))
    assert (r["status"], r["run_id"]) == ("ring", run)
    assert inner.profile(conn, mira)["axes"]["warmth"][0] == 52  # now it counts


def test_too_little_evidence_keeps_it_a_seed_and_long_unconfirmed_it_passes(conn, cards):
    story, mira, _ = seeded(conn, cards)
    bear_out(conn, story, mira, days=(1, 1, 1))  # three memories, one scene
    skip_now(conn, story)
    assert status(conn, story, mira) == "seed"
    skip_now(conn, story, "a month later")
    assert status(conn, story, mira) == "past"


def test_locked_or_rejected_are_never_touched_and_lite_reinforces_too(conn, cards):
    setting(conn, "mind.level", "lite")
    story, mira, rid = seeded(conn, cards)
    bear_out(conn, story, mira)
    skip_now(conn, story)
    assert status(conn, story, mira) == "ring"  # code only, zero calls
    story, mira, rid = seeded(conn, cards, "locked")
    skip_now(conn, story, "two months later")
    assert status(conn, story, mira) == "locked"
    story, mira, rid = seeded(conn, cards, "rejected")
    bear_out(conn, story, mira)
    skip_now(conn, story)
    assert status(conn, story, mira) == "rejected"


# --- one line in the mind block (note 22 §4 row 3) -----------------------------------------------

from kataki import mind as graph  # noqa: E402


async def reply_to(conn, backend, story, text="Hello, Mira.", says="Hello."):
    backend.say(says)
    mira = ent(conn, story, "Mira")
    events = [e async for e in turns.turn(conn, backend.llm, story, text, speaker=mira)]
    assert events[-1][0] == "done", events[-1]
    tail = backend.requests[-1]["messages"][-1]["content"]
    gen = json.loads(chat.active_path(conn, story)[-1]["gen"])
    return tail, gen


def reflect(conn, story, who, kind, text, status="ring", subject=None) -> int:
    with conn:
        return growth.write(conn, story, who, kind, text, [97, 98, 99], status, 0, subject=subject)


@pytest.mark.anyio
async def test_her_line_about_the_one_she_answers_reaches_the_reply(local_model, cards, backend):
    conn = local_model
    story = make(conn, cards)
    mira, aren = ent(conn, story, "Mira"), ent(conn, story, "Aren")
    reflect(conn, story, mira, "habit", "learned to ask for help")
    rid = reflect(conn, story, mira, "relationship", "He keeps coming back.", subject=aren)
    reflect(conn, story, mira, "scar", "never trusts a promise", "seed")
    tail, gen = await reply_to(conn, backend, story)
    assert "How you have come to see Aren: “He keeps coming back.”" in tail
    assert "ask for help" not in tail and "promise" not in tail  # one line; a seed never
    assert gen["growth"]["reflection"] == rid and gen["growth"]["kind"] == "relationship"
    node = next(n for n in graph.mind(conn, chat.active_path(conn, story)[-1]["id"])["nodes"]
                if n["id"] == "growth")  # fmt: skip
    assert node["title"] == "Growth" and node["column"] == "inside" and node["gold"]


@pytest.mark.anyio
async def test_else_her_strongest_ring_and_never_a_rejected_one(local_model, cards, backend):
    conn = local_model
    story = make(conn, cards)
    mira = ent(conn, story, "Mira")
    reflect(conn, story, mira, "habit", "learned to ask for help", "locked")
    growth.act(conn, reflect(conn, story, mira, "stance", "stands up to bullies"), "reject")
    tail, gen = await reply_to(conn, backend, story)
    assert "Something that has changed in you: learned to ask for help." in tail
    assert "bullies" not in tail and gen["growth"]["kind"] == "habit"


@pytest.mark.anyio
async def test_off_or_broken_the_turn_goes_on_without_it(local_model, cards, backend, monkeypatch):
    conn = local_model
    story = make(conn, cards)
    reflect(conn, story, ent(conn, story, "Mira"), "habit", "learned to ask for help")
    setting(conn, "features.mind.growth", False)
    tail, gen = await reply_to(conn, backend, story)
    assert "ask for help" not in tail and "growth" not in gen
    setting(conn, "features.mind.growth", True)

    def boom(*a, **k):
        raise RuntimeError("no")

    monkeypatch.setattr(growth, "line", boom)
    tail, gen = await reply_to(conn, backend, story, "Still there?")
    assert "growth" not in gen


# --- Peek and the user's say (§6 rule 6) ------------------------------------------------------------

from fastapi.testclient import TestClient  # noqa: E402

from kataki import bonds, people  # noqa: E402
from kataki.server import create_app  # noqa: E402


@pytest.fixture
def api(conn, backend):
    client = TestClient(
        create_app(conn, "t", llm=backend.llm, worker_delay=60),
        headers={"Authorization": "Bearer t"},
    )
    with client:
        yield client


def peek(conn, story, name="Mira") -> dict:
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    return next(p for p in people.people(conn, row) if p["name"] == name)


def test_peek_shows_each_reflection_with_its_evidence_and_drift(conn, cards):
    story, mira, rid = seeded(conn, cards)
    aren = ent(conn, story, "Aren")
    src = hers(conn, story, mira, "Aren carried Mira's crates up from the harbour.", 0)
    with conn:
        growth.write(conn, story, mira, "relationship", "He keeps coming back.", [src], "ring", 0,
                     subject=aren)  # fmt: skip
    bear_out(conn, story, mira)
    run = skip_now(conn, story)
    raw_ = raw(conn, run) | {"deep_warnings": {str(mira): ["A growth ring was dropped: x."]}}
    conn.execute("UPDATE extraction_runs SET raw=? WHERE id=?", (json.dumps(raw_), run))
    got = peek(conn, story)["growth"]
    ring, line_ = sorted(got["reflections"], key=lambda r: r["kind"])
    assert (ring["kind"], ring["status"], ring["by"]) == ("habit", "ring", "code")
    assert ring["evidence"] == {"memories": 3, "scenes": 2}
    assert ring["trait"] == {"axis": "warmth", "delta": 2, "words": "a little warmer"}
    assert (line_["about"], line_["about_id"], line_["evidence"]) == ("Aren", aren, None)
    assert line_["sources"] == [
        {"memory_id": src, "text": "Aren carried Mira's crates up from the harbour."}
    ]
    assert got["drift"] == [{"axis": "warmth", "delta": 2, "words": "a little warmer"}]
    assert got["warnings"] == ["A growth ring was dropped: x."]
    setting(conn, "features.mind.growth", False)
    assert peek(conn, story)["growth"] is None


def test_accept_reject_lock_through_the_api(conn, cards, api):
    story, mira, rid = seeded(conn, cards)
    got = api.post(f"/reflections/{rid}", json={"action": "accept"})
    assert got.status_code == 201 and got.json()["status"] == "ring"
    assert got.json()["by"] == "user"
    assert inner.profile(conn, mira)["axes"]["warmth"][0] == 52
    rejected = api.post(f"/reflections/{got.json()['id']}", json={"action": "reject"}).json()
    assert rejected["status"] == "rejected" and rejected["trait"]["delta"] == 2
    assert inner.profile(conn, mira)["axes"]["warmth"][0] == 50
    assert peek(conn, story)["growth"]["drift"] == []
    assert api.post(f"/reflections/{rid}", json={"action": "lock"}).json()["status"] == "locked"
    assert api.post("/reflections/9999", json={"action": "lock"}).status_code == 404
    assert api.post(f"/reflections/{rid}", json={"action": "erase"}).status_code == 422


@pytest.mark.anyio
async def test_a_rejected_grudge_is_struck_on_every_branch(local_model, cards, backend):
    conn = local_model
    story = make(conn, cards)
    await reply_to(conn, backend, story, "Mira, you're useless.", "Fine.")
    [bond] = peek(conn, story)["bonds"]
    grudge = bond["grudge"]
    assert grudge["event"] == "insult" and grudge["id"]
    client = TestClient(create_app(conn, "t", llm=backend.llm, worker_delay=60),
                        headers={"Authorization": "Bearer t"})  # fmt: skip
    with client:
        got = client.post(f"/opinions/{grudge['id']}/reject")
        assert got.status_code == 200 and len(got.json()["rejected"]) == 3
        assert client.post("/opinions/9999/reject").status_code == 404
        kind = conn.execute("SELECT id FROM opinions WHERE event='rejected'").fetchone()[0]
        assert client.post(f"/opinions/{kind}/reject").status_code == 409  # not a grudge
    assert peek(conn, story)["bonds"] == [] or peek(conn, story)["bonds"][0]["grudge"] is None
    tail, _ = await reply_to(conn, backend, story, "Hello again.")
    assert "not forgiven" not in tail
    rows = bonds.ledger(conn, ent(conn, story, "Mira"), chat.active_path(conn, story))
    assert bonds.standing(rows, ent(conn, story, "Aren"), 10**6)["grudge"] is None
