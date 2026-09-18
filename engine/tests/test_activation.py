"""The numbers here are the worked examples in docs/specs/2026-09-18-m0-m1-design.md."""

import pytest

from kataki.activation import Access, effortful_recall, hash01, noise, score

DAY = 1440
YEAR = 365 * DAY
NOW = 10 * YEAR
CUED = {"relevance": 0.9, "graph": 1.0}


def encoded(ago):
    return Access(story_time=NOW - ago, weight=1.0, sharp=True)


def scored(accesses, importance=9, source="witnessed", **kw):
    return score(accesses, now=NOW, importance=importance, source=source, **{**CUED, **kw})


# --- example 1: Mira witnessed "Tobin betrayed the guild at the docks", importance 9 ----


def test_next_day_the_memory_is_sharp():
    s = scored([encoded(DAY)])
    assert (round(s.base_all, 2), round(s.a_all, 2), s.tier) == (-3.64, 1.41, "sharp")


def test_six_years_later_only_the_gist_remains():
    s = scored([encoded(6 * YEAR)])
    assert (round(s.base_all, 2), round(s.a_all, 2), s.tier) == (-7.48, -2.43, "hazy")


def test_six_years_later_and_uncued_it_is_not_recalled_at_all():
    s = scored([encoded(6 * YEAR)], relevance=0.2, graph=0.0)
    assert (round(s.a_all, 2), s.tier) == (-4.48, None)


def test_retelling_it_every_year_keeps_it_sharp():
    s = scored([encoded(n * YEAR) for n in range(6, 0, -1)])
    assert (round(s.base_all, 2), round(s.a_all, 2), s.tier) == (-5.29, -0.24, "sharp")


def test_recalling_the_gist_keeps_the_gist_but_never_resurrects_detail():
    gist_recall = Access(story_time=NOW - DAY, weight=0.5, sharp=False)
    s = scored([encoded(6 * YEAR), gist_recall])
    assert (round(s.base_all, 2), round(s.a_all, 2)) == (-4.29, 0.76)
    assert (round(s.base_detail, 2), round(s.a_detail, 2)) == (-7.48, -2.43)
    assert s.tier == "hazy"


# --- example 2: importance, both memories 30 days old, same cue -------------------------


@pytest.mark.parametrize(
    ("importance", "age", "cue", "a", "tier"),
    [
        (9, 30 * DAY, CUED, -0.29, "sharp"),
        (2, 30 * DAY, CUED, -2.39, "hazy"),
        (2, 6 * YEAR, CUED, -4.53, None),
        (2, 1 * YEAR, {"relevance": 0.5, "graph": 0.5}, -4.74, None),
    ],
)
def test_importance_decides_how_long_a_memory_lasts(importance, age, cue, a, tier):
    s = scored([encoded(age)], importance=importance, **cue)
    assert (round(s.a_all, 2), s.tier) == (a, tier)


# --- guards ----------------------------------------------------------------------------


def test_a_just_formed_memory_does_not_blow_up():
    s = scored([encoded(0)])  # dt is floored at ten story minutes
    assert round(s.base_all, 2) == -1.15


def test_base_level_never_goes_positive_however_often_it_is_rehearsed():
    s = scored([encoded(10)] * 500)
    assert s.base_all == 0.0


def test_hearsay_fades_before_what_you_saw_yourself():
    seen = scored([encoded(YEAR)])  # -1.54
    rumor = scored([encoded(YEAR)], source="rumor")  # -3.04
    assert round(seen.a_all - rumor.a_all, 2) == 1.5
    assert (seen.tier, rumor.tier) == ("sharp", "hazy")


def test_a_superseded_memory_is_pushed_down():
    live = scored([encoded(DAY)])
    old = scored([encoded(DAY)], superseded=True)
    assert round(live.a_all - old.a_all, 2) == 2.0


def test_the_sharpness_slider_controls_how_fast_everything_fades():
    dreamy = scored([encoded(YEAR)], d=0.8)
    crisp = scored([encoded(YEAR)], d=0.3)
    assert dreamy.a_all < scored([encoded(YEAR)]).a_all < crisp.a_all


# --- noise and effortful recall are deterministic ---------------------------------------


def test_noise_is_stable_within_a_scene_bounded_and_varies_between_scenes():
    values = {noise(knower=1, memory=7, scene=s) for s in range(200)}
    assert noise(knower=1, memory=7, scene=3) == noise(knower=1, memory=7, scene=3)
    assert len(values) > 150
    assert all(-0.75 <= v <= 0.75 for v in values)


def test_hash01_is_uniform_enough():
    xs = [hash01("probe", i) for i in range(4000)]
    assert all(0 < x < 1 for x in xs)
    assert 0.47 < sum(xs) / len(xs) < 0.53


def test_straining_to_remember_succeeds_about_as_often_as_the_detail_is_strong():
    # a_detail = -2.43 -> p = sigmoid(-0.43) = 0.39
    wins = sum(effortful_recall(-2.43, knower=1, memory=7, scene=s) for s in range(4000))
    assert 0.36 < wins / 4000 < 0.42
    assert effortful_recall(-2.43, 1, 7, 5) == effortful_recall(-2.43, 1, 7, 5)


def test_straining_is_hopeless_for_a_long_dead_detail_and_easy_for_a_fresh_one():
    assert not any(effortful_recall(-12.0, 1, 7, s) for s in range(300))
    assert all(effortful_recall(8.0, 1, 7, s) for s in range(300))
