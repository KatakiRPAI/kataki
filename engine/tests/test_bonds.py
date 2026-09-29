"""The relationship ledger: pure maths on story minutes, then the turn, Peek and the graph."""

import pytest

from kataki import bonds, clock, inner

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
