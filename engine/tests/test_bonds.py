"""The relationship ledger: pure maths on story minutes, then the turn, Peek and the graph."""

import json
import re

import pytest

from kataki import bonds, chat, clock, inner, library, mind, people, turns

P = inner.shape({})
DAY = clock.DAY
CAUSE = 'Aren said "I forgot"'


def breach(prof=P, now=0, scene=1, dial="realistic"):
    return bonds.apply([], 7, "promise_broken", 2, CAUSE, now, scene, prof, dial)


def saved(rows, start=1):
    """The rows as if written: they get ids, so an apology can point at them."""
    return [{**r, "id": start + i} for i, r in enumerate(rows)]


def test_a_broken_promise_costs_more_trust_than_a_kept_one_earns():
    lost = bonds.standing(breach(), 7, 0)["trust"]
    kept = bonds.standing(bonds.apply([], 7, "promise_kept", 2, "came", 0, 1, P), 7, 0)["trust"]
    assert lost == pytest.approx(-17.6) and kept > 0
    assert abs(lost) >= 2 * kept


def test_a_grudge_holds_while_a_kindness_fades():
    rows = saved(breach() + bonds.apply([], 7, "kindness", 2, "brought soup", 0, 1, P))
    later = bonds.standing(rows, 7, 90 * DAY)
    assert later["trust"] == pytest.approx(bonds.STICKY_FLOOR * -17.6, abs=0.1)
    assert later["grudge"]["event"] == "promise_broken"


def test_a_hollow_apology_forgives_nothing():
    rows = saved(breach())
    rows += bonds.apply(rows, 7, "apology_hollow", 2, "sorry", 60, 1, P)
    now = bonds.standing(rows, 7, 60)
    assert now["grudge"] is not None and now["trust"] == pytest.approx(-17.6, abs=0.1)


def test_a_sincere_apology_forgives_and_trust_comes_back_slowly():
    rows = saved(breach())
    rows += bonds.apply(rows, 7, "apology_sincere", 2, "I broke my promise", 60, 1, P)
    now = bonds.standing(rows, 7, 60)
    assert now["grudge"] is None and now["forgiven"]["event"] == "promise_broken"
    assert now["trust"] < -15  # forgiving is not forgetting
    week = bonds.standing(rows, 7, 60 + 7 * DAY)["trust"]
    assert -17.6 < week < -12  # a week on, most of it is still missing


def test_forgiving_people_forgive_faster():
    def a_month_after_sorry(prof):
        rows = saved(breach(prof))
        rows += bonds.apply(rows, 7, "apology_sincere", 2, "sorry", 0, 1, prof)
        return bonds.standing(rows, 7, 30 * DAY)["trust"]

    kind = inner.shape({"social": {"forgiveness": 1.0}})
    hard = inner.shape({"social": {"forgiveness": 0.0}})
    assert a_month_after_sorry(kind) > a_month_after_sorry(hard)


def test_one_scene_cannot_buy_closeness():
    rows: list[dict] = []
    for _ in range(10):
        rows += bonds.apply(rows, 7, "support_given", 3, "helped", 0, 1, P)
    assert bonds.standing(rows, 7, 0)["closeness"] <= bonds.SCENE_CAP["closeness"]
    rows += bonds.apply(rows, 7, "support_given", 3, "helped", 0, 2, P)  # the next scene
    assert bonds.standing(rows, 7, 0)["closeness"] > bonds.SCENE_CAP["closeness"]


def test_anxious_people_take_it_harder_and_the_dial_scales_it():
    base = bonds.standing(breach(), 7, 0)["trust"]
    anxious = inner.shape({"attachment": {"anxiety": 0.9}})
    assert bonds.standing(breach(anxious), 7, 0)["trust"] < base
    assert bonds.standing(breach(dial="gentle"), 7, 0)["trust"] == pytest.approx(base / 2)


def test_rows_are_about_one_person_at_a_time():
    rows = saved(breach())
    other = bonds.standing(rows, 8, 0)
    assert other["trust"] == 0 and other["grudge"] is None and other["causes"] == []


@pytest.mark.parametrize(
    "line, events",
    [
        ("I forgot. I didn't come last night.", [("promise_broken", 2)]),
        ("You're useless.", [("insult", 2)]),
        ("I'm sorry.", [("apology_hollow", 2)]),
        ("I'm sorry I broke my promise. It was my fault.", [("apology_sincere", 2)]),
        ("You did so well, thank you.", [("compliment", 2)]),
        ("Nice weather.", []),
        ("I didn't come here to fight.", []),
        ("I forgot how pretty the harbour is.", []),
        ("I didn't make it up, I swear.", []),
    ],
)
def test_rules_read_what_a_line_did(line, events):
    assert bonds.rule_events(line, inner.sense(line)) == events


def test_only_the_one_it_was_aimed_at_writes_it_down_on_this_branch(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    story = library.create_story(
        conn, "s", character_ids=[ids["Mira"], ids["Tobin"]], persona_id=ids["Aren"]
    )
    who = dict(conn.execute("SELECT name, id FROM entities WHERE story_id=?", (story,)).fetchall())
    turns.say(conn, story, "Tobin, you're useless.")
    path = chat.active_path(conn, story)

    pending = bonds.react(conn, story, path)
    assert set(pending) == {who["Tobin"]}
    assert {r["dst_id"] for r in pending[who["Tobin"]]} == {who["Aren"]}
    assert {r["event"] for r in pending[who["Tobin"]]} == {"insult"}

    bonds.save(conn, story, pending, path[-1]["id"])
    kept = bonds.ledger(conn, who["Tobin"], path)
    assert len(kept) == 3 and all(r["id"] and r["scene_id"] for r in kept)
    assert bonds.ledger(conn, who["Tobin"], path[:-1]) == []  # another branch never had it
    assert bonds.react(conn, story, path[:-1]) == {}  # nothing new was said there


def test_the_block_says_it_in_words_never_numbers():
    rows = saved(breach())
    text = "\n".join(bonds.sentences(bonds.standing(rows, 7, 120), "Aren", 120))
    assert text.startswith(
        "Toward Aren: you trust them much less than before; you feel further from them"
        ' (Aren said "I forgot", two hours ago).'
    )
    assert (
        'You have not forgiven Aren (Aren said "I forgot"). Stay civil; do not warm up unless'
        " Aren owns it." in text
    )
    assert not re.search(r"\d", text)


def test_forgiven_but_not_yet_trusted():
    rows = saved(breach())
    rows += bonds.apply(rows, 7, "apology_sincere", 2, "sorry", 60, 1, P)
    text = "\n".join(bonds.sentences(bonds.standing(rows, 7, 60), "Aren", 60))
    assert "You have forgiven Aren, but trust comes back slowly." in text
    assert "not forgiven" not in text


def test_nothing_happened_nothing_to_say():
    assert bonds.sentences(bonds.standing([], 7, 0), "Aren", 0) == []
    assert bonds.toward([], [7], 0) == {}


def test_the_app_gets_words_and_numbers():
    st = bonds.standing(saved(breach()), 7, 0)
    shown = bonds.public(st, 7, "Aren", True, 480)
    assert shown["words"] == "trusts much less · further · holds a grudge"
    assert shown["trust"] == pytest.approx(-17.6) and shown["you"] is True
    assert shown["grudge"] == {"event": "promise_broken", "cause": CAUSE, "since": "Day 1, 08:00",
                               "kind": "sticky", "forgiven": False}  # fmt: skip
    assert [c["event"] for c in shown["causes"]] == ["promise_broken"]


def test_one_mind_block_holds_feelings_and_bonds():
    hurt = inner.feel(inner.fresh(P, 0), "hurt", 0.8, "cruel", P)
    feeling = inner.lines(inner.regulate(hurt, P), P)
    block = inner.block("Mira", [*feeling, "Toward Aren: you feel further from them."])
    assert block.splitlines()[0] == "[Inside Mira right now: show it, never say it]"
    assert block.splitlines()[-1] == "Toward Aren: you feel further from them."
    assert inner.block("Mira", []) == ""
    assert inner.render(inner.regulate(hurt, P), P, "Mira") == inner.block("Mira", feeling)


def test_how_long_ago_is_never_a_digit():
    for minutes in (12 * 60, 20 * DAY, 3 * 365 * DAY, 400 * DAY, 15 * 365 * DAY):
        said = bonds._ago(minutes)
        assert not re.search(r"\d", said) and said.endswith(" ago")


def test_render_answers_first_adds_one_other_and_merges_pending(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Cara", "Aren")}
    story = library.create_story(
        conn,
        "s",
        character_ids=[ids["Mira"], ids["Tobin"], ids["Cara"]],
        persona_id=ids["Aren"],
    )
    who = dict(conn.execute("SELECT name, id FROM entities WHERE story_id=?", (story,)).fetchall())
    turns.say(conn, story, "Mira, hello.")
    path = chat.active_path(conn, story)
    mira = inner.profile(conn, who["Mira"])
    now = path[-1]["story_time"]
    kept = bonds.apply([], who["Aren"], "promise_broken", 2, CAUSE, now, 1, mira)
    kept += bonds.apply([], who["Tobin"], "insult", 1, "Tobin sneered", now, 1, mira)
    bonds.save(conn, story, {who["Mira"]: kept}, path[-1]["id"])
    pending = bonds.apply(
        [], who["Cara"], "boundary_crossed", 3, "Cara read her diary", now, 1, mira
    )

    rows, shown = bonds.render(conn, story, who["Mira"], path, pending)
    text = " ".join(rows)
    assert rows[0].startswith("Toward Aren:") and "Toward Cara:" in text
    assert "Tobin" not in text and [s["other"] for s in shown] == ["Aren", "Cara"]
    assert shown[0]["you"] is True and not re.search(r"\d", text)


# --- in the turn ------------------------------------------------------------------------------


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    return library.create_story(
        conn, "Low Tide", character_ids=[ids["Mira"], ids["Tobin"]], persona_id=ids["Aren"]
    )


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


async def play(stream):
    return [e async for e in stream]


def tail(request):
    return request["messages"][-1]["content"]


@pytest.mark.anyio
async def test_she_holds_it_for_twenty_turns_a_hollow_sorry_fails_a_real_one_lands(
    conn, story, backend
):
    backend.say(*["Mm."] * 23)
    await play(turns.turn(conn, backend.llm, story, "Mira, I forgot. I didn't come last night."))
    assert "You have not forgiven Aren" in tail(backend.requests[0])
    for _ in range(20):
        await play(turns.turn(conn, backend.llm, story, "Nice weather, Mira."))
    assert "You have not forgiven Aren" in tail(backend.requests[-1])
    await play(turns.turn(conn, backend.llm, story, "Mira, I'm sorry."))
    assert "You have not forgiven Aren" in tail(backend.requests[-1])
    await play(
        turns.turn(conn, backend.llm, story, "Mira, I'm sorry I broke my promise. My fault.")
    )
    block = tail(backend.requests[-1])
    assert "You have forgiven Aren, but trust comes back slowly." in block
    assert "you trust them much less than before" in block


@pytest.mark.anyio
async def test_a_new_take_does_not_count_it_twice(conn, story, backend):
    backend.say("First.", "Second.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    await play(turns.regenerate(conn, backend.llm, story))
    live = bonds.ledger(conn, eid(conn, "Mira"), chat.active_path(conn, story))
    assert len(live) == 3  # the insult once, on this take
    assert conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0] == 6  # both takes kept
    assert tail(backend.requests[0]) == tail(backend.requests[1])


@pytest.mark.anyio
async def test_switched_off_there_is_no_ledger(conn, story, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.bonds', 'false')")
    backend.say("Fine.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert "Toward Aren" not in tail(backend.requests[0])
    assert conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0] == 0


@pytest.mark.anyio
async def test_a_failing_ledger_still_keeps_the_reply(conn, story, backend, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr("kataki.bonds.react", boom)
    backend.say("Fine.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert events[-1][0] == "done" and chat.active_path(conn, story)[-1]["text"] == "Fine."
    assert "Toward Aren" not in tail(backend.requests[0])


@pytest.mark.anyio
async def test_peek_and_the_mind_graph_show_the_ledger(conn, story, backend):
    backend.say("Mm.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    cast = {p["name"]: p for p in people.people(conn, row)}
    [bond] = cast["Mira"]["bonds"]
    assert (bond["other"], bond["you"], bond["grudge"]["event"]) == ("Aren", True, "insult")
    assert bond["respect"] < 0
    assert cast["Tobin"]["bonds"] == []  # he heard it; it wasn't aimed at him

    leaf = chat.active_path(conn, story)[-1]
    graph = mind.mind(conn, leaf["id"])
    node = next(n for n in graph["nodes"] if n["id"] == f"o{eid(conn, 'Aren')}")
    assert node["kind"] == "feeling" and node["gold"] is True
    assert node["text"] == "Toward you: further · respects less · holds a grudge"
    assert node["detail"]["source"] == "ledger"
    assert json.loads(leaf["gen"])["bonds"][0]["other"] == "Aren"


@pytest.mark.anyio
async def test_a_failing_render_still_saves_the_events(conn, story, backend, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr("kataki.bonds.render", boom)
    backend.say("Fine.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert events[-1][0] == "done"
    assert "Toward Aren" not in tail(backend.requests[0])
    assert conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0] == 3


@pytest.mark.anyio
@pytest.mark.parametrize("bad", [{"bonds": 5}, {"bonds": [{}]}, {"mind": 5}])
async def test_a_malformed_stored_ledger_does_not_break_the_graph(conn, story, backend, bad):
    backend.say("Fine.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    leaf = chat.active_path(conn, story)[-1]
    conn.execute("UPDATE messages SET gen=? WHERE id=?", (json.dumps(bad), leaf["id"]))
    assert mind.mind(conn, leaf["id"])["nodes"]


@pytest.mark.anyio
async def test_peek_survives_a_failing_ledger_and_a_switch(conn, story, backend, monkeypatch):
    backend.say("Fine.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr("kataki.bonds.ledger", boom)
    assert all(p["bonds"] == [] for p in people.people(conn, row))
    monkeypatch.undo()
    assert people.people(conn, row)[0]["bonds"] or people.people(conn, row)[1]["bonds"]
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.bonds', 'false')")
    assert all(p["bonds"] == [] for p in people.people(conn, row))


def test_a_person_named_but_away_is_not_insulted_by_who_is_left(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    story = library.create_story(
        conn, "s", character_ids=[ids["Mira"], ids["Tobin"]], persona_id=ids["Aren"]
    )
    who = dict(conn.execute("SELECT name, id FROM entities WHERE story_id=?", (story,)).fetchall())
    chat.set_presence(conn, story, who["Tobin"], False)
    turns.say(conn, story, "Tobin is useless.")
    path = chat.active_path(conn, story)
    assert inner.targets(conn, path, [who["Mira"]]) == set()
    assert bonds.react(conn, story, path) == {}


def test_a_hostile_temperament_never_breaks_the_ledger():
    odd = inner.shape({"social": {"forgiveness": -0.5, "trust_propensity": -1}})
    zero = inner.shape({"social": {"forgiveness": 0.0, "trust_propensity": 0.0}})
    args = (7, "apology_sincere", 2, "sorry", DAY, 2)
    assert bonds.apply(saved(breach(odd)), *args, odd) == bonds.apply(
        saved(breach(zero)), *args, zero
    )
    args = (7, "support_given", 2, "helped", 0, 1)
    assert bonds.apply([], *args, odd) == bonds.apply([], *args, zero)


def test_a_merge_carries_the_ledger_and_the_mind(local_model):
    conn = local_model
    a = library.create_item(conn, "character", "Mira")
    b = library.create_item(conn, "character", "Mirabel")
    story = library.create_story(conn, "s", character_ids=[a, b])
    keep, drop = (
        conn.execute("SELECT id FROM entities WHERE story_id=? AND name=?", (story, n)).fetchone()[
            0
        ]
        for n in ("Mira", "Mirabel")
    )
    conn.execute(
        "INSERT INTO opinions(story_id, src_id, dst_id, dim, value, kind, story_time)"
        " VALUES(?, ?, ?, 'trust', -5, 'sticky', 0), (?, ?, ?, 'trust', 3, 'decay', 0)",
        (story, drop, keep, story, keep, drop),
    )
    conn.execute(
        "INSERT INTO mind_states(entity_id, story_time, state) VALUES(?, 0, '{}')", (drop,)
    )
    conn.commit()
    library.merge_entities(conn, keep, drop)
    count = lambda sql, *a: conn.execute(sql, a).fetchone()[0]  # noqa: E731
    assert count("SELECT COUNT(*) FROM opinions WHERE src_id=? AND dst_id=?", keep, keep) == 2
    assert count("SELECT COUNT(*) FROM opinions WHERE src_id=? OR dst_id=?", drop, drop) == 0
    assert count("SELECT COUNT(*) FROM mind_states WHERE entity_id=?", keep) == 1


# --- holding their ground ---------------------------------------------------------------------


def test_nothing_at_stake_no_decision():
    assert bonds.stance(inner.fresh(P, 0), P, "realistic", False, "Aren", 1, 0) == ""
    assert bonds.stance(None, P, "realistic", False, "Aren", 1, 0) == ""


@pytest.mark.parametrize(
    "dial, words",
    [
        ("soft", "You can come round when Aren makes a fair point."),
        ("realistic", "Change your position only if Aren gives a new reason that matters to you"),
        ("stubborn", "never because Aren is upset or insists."),
        ("nonsense", "Change your position only if Aren gives a new reason"),
    ],
)
def test_a_grudge_brings_the_dials_yield_rule(dial, words):
    assert words in bonds.stance(None, P, dial, True, "Aren", 1, 0)


def test_a_position_binds_her_for_a_day():
    st = bonds.took(inner.fresh(P, 0), {"text": "won't go", "firm": 3}, False, 1, 0)
    assert bonds.stance(st, P, "realistic", False, "Aren", 1, 60).startswith(
        'You have taken a position: "won\'t go". Change your position only if Aren'
    )
    assert bonds.stance(st, P, "realistic", False, "Aren", 1, 2 * DAY) == ""


def test_giving_way_spends_the_scenes_budget():
    st = bonds.took(inner.fresh(P, 0), {"text": "won't go", "firm": 1}, False, 1, 0)
    assert bonds.HOLD_LINE not in bonds.stance(st, P, "realistic", False, "Aren", 1, 5)
    gave = bonds.took(st, {"text": "one drink, then home", "firm": 1}, True, 1, 5)
    assert gave["conceded"] == {"scene": 1, "n": 1}
    assert bonds.HOLD_LINE in bonds.stance(gave, P, "realistic", False, "Aren", 1, 6)
    assert bonds.HOLD_LINE not in bonds.stance(gave, P, "realistic", False, "Aren", 2, 6)
    again = bonds.took(gave, None, True, 2, 7)  # a new scene starts the count again
    assert again["conceded"] == {"scene": 2, "n": 1} and again["position"] is None


def test_the_budget_follows_the_dial_and_the_temperament():
    assert bonds.budget("stubborn", P) == 0 and bonds.budget("realistic", P) == 1
    assert bonds.budget("soft", inner.shape({"axes": {"yielding": [80, 10]}})) == 4
    assert bonds.budget("realistic", inner.shape({"axes": {"yielding": [20, 10]}})) == 0
    assert bonds.HOLD_LINE not in bonds.stance(None, P, "stubborn", True, "Aren", 1, 0)


def test_the_opening_is_checked_when_she_is_cold_holding_or_blunt():
    calm = inner.fresh(P, 0)
    assert not bonds.armed(calm, P, False, 0)
    assert bonds.armed(calm, P, True, 0)  # a grudge
    assert bonds.armed(inner.feel(calm, "hurt", 0.6, "cruel", P), P, False, 0)
    assert bonds.armed(bonds.took(calm, {"text": "no", "firm": 2}, False, 1, 0), P, False, 0)
    assert bonds.armed(None, inner.shape({"axes": {"candor": [85, 5]}}), False, 0)


@pytest.mark.parametrize(
    "reply, hit",
    [
        ("You're right. I'm useless.", "you're right"),
        ("*sighs* I'm sorry, you're right.", "i'm sorry"),
        ("As an AI, I can't feel that.", "as an ai"),
        ("What a lovely poem!", "what a lovely"),
        ("No. Go home, Aren.", None),
        ("I'm not going.", None),
    ],
)
def test_assistant_openings(reply, hit):
    assert bonds.opener(reply) == hit


@pytest.mark.anyio
async def test_a_grudge_puts_the_yield_rule_in_the_directive(conn, story, backend):
    backend.say("Hm.", "Hm.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    directive = tail(backend.requests[0]).split("[Directive]")[1]
    assert "Change your position only if Aren gives a new reason that matters to you" in directive
    conn.execute("INSERT INTO settings(key, value) VALUES('realism.pushback', '\"stubborn\"')")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert "never because Aren is upset" in tail(backend.requests[1]).split("[Directive]")[1]


@pytest.mark.anyio
async def test_an_assistant_opening_is_dropped_unseen_and_written_again(conn, story, backend):
    backend.say("You're right. I'm useless.", "Say that again.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert "".join(v for k, v in events if k == "token") == "Say that again."
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["text"] == "Say that again." and len(backend.requests) == 2
    assert json.loads(leaf["gen"])["trace"]["check"] == {"hit": "you're right", "resampled": True}
    assert "Do not open by agreeing" in tail(backend.requests[1])


@pytest.mark.anyio
async def test_the_lite_level_only_notes_it(conn, story, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    backend.say("You're right.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["text"] == "You're right." and len(backend.requests) == 1
    assert json.loads(leaf["gen"])["trace"]["check"] == {"hit": "you're right", "resampled": False}


@pytest.mark.anyio
async def test_a_calm_character_is_not_checked(conn, story, backend):
    backend.say("You're right, it is.")
    await play(turns.turn(conn, backend.llm, story, "Nice weather, Mira."))
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["text"] == "You're right, it is." and len(backend.requests) == 1
    assert "check" not in json.loads(leaf["gen"])["trace"]


@pytest.mark.anyio
async def test_a_failed_second_take_keeps_the_first_reply(conn, story, backend):
    import httpx2

    backend.say("You're right. I'm useless.", httpx2.Response(500, text="boom"))
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert [k for k, _ in events].count("error") == 1  # one error, no second visible reply
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["role"] == "assistant" and leaf["text"].startswith("You're right.")
