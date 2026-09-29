"""The relationship ledger: pure maths on story minutes, then the turn, Peek and the graph."""

import re

import pytest

from kataki import bonds, chat, clock, inner, library, turns

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
