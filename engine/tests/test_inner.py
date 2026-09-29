"""The affect core: pure functions, story minutes, no model."""

import re

import numpy as np
import pytest

from kataki import inner, library


def test_a_profile_fills_what_the_card_leaves_out():
    p = inner.shape({"axes": {"dominance": [80, 10]}, "regulation": {"style": "suppress"}})
    assert inner.mean(p, "dominance") == 80
    assert inner.mean(p, "warmth") == 50  # default kept beside the override
    assert p["regulation"] == {"style": "suppress", "capacity": 0.5}


def test_warm_people_start_brighter_and_dominant_ones_stronger():
    cold = inner.baseline(inner.shape({"axes": {"warmth": [20, 10]}}))
    warm = inner.baseline(inner.shape({"axes": {"warmth": [80, 10]}}))
    boss = inner.baseline(inner.shape({"axes": {"dominance": [90, 10]}}))
    assert warm["v"] > cold["v"]
    assert boss["d"] > 0.2


def test_the_profile_is_read_from_the_library_character(conn):
    mira = library.create_item(conn, "character", "Mira")
    library.update_item(conn, mira, data={"mind": {"anxiety": 0.8}})
    story = library.create_story(conn, "s", character_ids=[mira])
    entity = conn.execute(
        "SELECT id FROM entities WHERE name='Mira' AND story_id=?", (story,)
    ).fetchone()["id"]
    assert inner.profile(conn, entity)["anxiety"] == 0.8


P = inner.shape({})


def hurt(prof=P, i=0.8, now=0):
    return inner.feel(inner.fresh(prof, now), "hurt", i, "Aren said something cruel", prof)


def test_an_emotion_halves_every_half_life_and_then_is_gone():
    state = hurt()
    assert inner.tick(state, 25, P)["emotions"][0]["i"] == pytest.approx(0.4, abs=0.01)
    assert inner.tick(state, 300, P)["emotions"] == []


def test_mood_stays_low_for_hours_and_settles_within_a_day():
    base = inner.baseline(P)["v"]
    state = hurt()
    assert state["mood"]["v"] < base - 0.2
    assert inner.tick(state, 120, P)["mood"]["v"] < base - inner.MOOD_SHOWS
    assert inner.tick(state, 24 * 60, P)["mood"]["v"] > base - inner.MOOD_SHOWS


def test_an_insult_hurts_the_meek_and_angers_the_dominant():
    meek = inner.shape({"axes": {"dominance": [30, 10]}})
    boss = inner.shape({"axes": {"dominance": [80, 10]}})
    assert inner.appraise("insult", 1.0, meek, inner.fresh(meek, 0))[0][0] == "hurt"
    assert inner.appraise("insult", 1.0, boss, inner.fresh(boss, 0))[0][0] == "angry"


def test_an_anxious_person_also_gets_anxious():
    worrier = inner.shape({"anxiety": 0.8})
    labels = [label for label, _ in inner.appraise("insult", 1.0, worrier, inner.fresh(worrier, 0))]
    assert labels == ["hurt", "anxious"]


def test_an_apology_only_relieves_someone_who_is_hurting():
    assert inner.appraise("apology", 1.0, P, inner.fresh(P, 0)) == []
    state = hurt()
    [(label, _)] = inner.appraise("apology", 1.0, P, state)
    eased = inner.feel(state, label, 0.4, "Aren apologised", P)
    assert eased["emotions"][0]["label"] in ("hurt", "relieved")
    assert next(e for e in eased["emotions"] if e["label"] == "hurt")["i"] < 0.8


def test_at_most_three_feelings_are_held():
    state = inner.fresh(P, 0)
    for label in ("hurt", "anxious", "sad", "annoyed"):
        state = inner.feel(state, label, 0.5, "x", P)
    assert len(state["emotions"]) == 3


def test_a_suppressor_looks_calm_then_leaks_then_the_mask_slips():
    p = inner.shape({"regulation": {"style": "suppress", "capacity": 0.5}})
    first = inner.regulate(hurt(p, 0.7), p)
    assert first["shown"] == {"label": "calm", "i": 0.3, "tell": None}
    second = inner.regulate(first, p)
    assert second["shown"]["tell"] == inner.TELLS["hurt"]
    third = inner.regulate(second, p)
    assert third["shown"]["label"] == "hurt"


def test_good_feelings_are_never_masked():
    p = inner.shape({"regulation": {"style": "suppress", "capacity": 0.5}})
    glad = inner.feel(inner.fresh(p, 0), "glad", 0.6, "good news", p)
    assert inner.regulate(glad, p)["shown"]["label"] == "glad"


def test_words_say_what_a_line_was():
    assert inner.sense("Honestly, you're useless.") == ("insult", 1.0)
    assert inner.sense("I'm sorry, my dog died this morning.") == ("bad_news", 1.0)
    assert inner.sense("I'm sorry, I was wrong.") == ("apology", 1.0)
    assert inner.sense("The tide is out.") is None


class Meaning:
    """A stand-in for the built-in model: 'dirt' means an insult, nothing else means anything."""

    def encode(self, texts):
        return np.array(
            [[1.0, 0.0] if t in inner.SEEDS["insult"] or "dirt" in t else [0.0, 0.0] for t in texts]
        )


def test_meaning_catches_what_the_word_list_misses():
    assert inner.sense("You're dirt to me.", Meaning()) == ("insult", 1.0)
    assert inner.sense("The tide is out.", Meaning()) is None


def test_a_faded_feeling_is_no_longer_shown():
    assert inner.tick(inner.regulate(hurt(), P), 300, P)["shown"] is None


def test_a_profile_with_no_inertia_still_ticks():
    p = inner.shape({"inertia_h": 0})
    assert inner.tick(hurt(p), 10, p)["t"] == 10


def test_shaping_a_profile_never_edits_the_defaults():
    inner.shape({})["axes"]["dominance"][0] = 99
    assert inner.DEFAULT["axes"]["dominance"][0] == 50


def test_at_rest_there_is_nothing_to_say():
    assert inner.render(inner.fresh(P, 0), P, "Mira") == ""
    assert inner.public(inner.fresh(P, 0), P) is None


def test_the_block_is_words_never_numbers():
    block = inner.render(inner.regulate(hurt(), P), P, "Mira")
    assert block.startswith("[Inside Mira right now: show it, never say it]")
    assert "Feeling: very hurt (Aren said something cruel)." in block
    assert "Mood: low." in block
    assert not re.search(r"\d", block)


def test_a_mask_is_in_the_block_and_in_the_api():
    p = inner.shape({"regulation": {"style": "suppress", "capacity": 0.5}})
    state = inner.regulate(inner.regulate(hurt(p, 0.7), p), p)
    assert "Showing: calm. Hiding the hurt; it slips out as short answers" in inner.render(
        state, p, "Mira"
    )
    mood = inner.public(state, p)
    assert (mood["label"], mood["shows"], mood["word"]) == ("hurt", "calm", "low")
    assert inner.face(state) == "neutral"  # the face shows the mask, not the feeling


def test_hours_later_only_the_mood_is_left():
    later = inner.tick(hurt(), 120, P)
    block = inner.render(later, P, "Mira")
    assert "Feeling:" not in block and "Mood: low." in block
