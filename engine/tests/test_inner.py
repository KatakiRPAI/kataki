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


def test_react_hurts_whoever_heard_it_and_save_anchors_it(local_model):
    from kataki import chat, turns

    conn = local_model
    mira = library.create_item(conn, "character", "Mira")
    tobin = library.create_item(conn, "character", "Tobin")
    aren = library.create_item(conn, "character", "Aren")
    story = library.create_story(conn, "s", character_ids=[mira, tobin], persona_id=aren)
    ids = dict(conn.execute("SELECT name, id FROM entities WHERE story_id=?", (story,)).fetchall())
    turns.say(conn, story, "Tobin, you're useless.", audience=[ids["Tobin"]])  # a whisper

    path = chat.active_path(conn, story)
    states = inner.react(conn, story, path)
    assert states[ids["Tobin"]]["emotions"][0]["label"] == "hurt"
    assert states[ids["Mira"]]["emotions"] == []  # she didn't hear it

    inner.save(conn, states, path[-1]["id"])
    kept = inner.current(conn, ids["Tobin"], path, inner.profile(conn, ids["Tobin"]))
    assert kept["emotions"][0]["cause"] == 'Aren said "Tobin, you\'re useless."'
    assert inner.current(conn, ids["Tobin"], path[:-1], inner.shape({})) is None  # other branch


BAD = [
    {"regulation": "suppress"},
    {"regulation": {"style": "shout", "capacity": "high"}},
    {"axes": {"warmth": 70}},
    {"axes": {"warmth": [70]}},
    {"inertia_h": "6"},
    {"inertia_h": True},
    {"anxiety": None},
    {"baseline": [0.1]},
    {"baseline": "calm"},
    {"attachment": []},
]


@pytest.mark.parametrize("own", BAD)
def test_a_malformed_profile_shapes_to_usable_values(own):
    prof = inner.shape(own)
    assert prof["regulation"] == P["regulation"] and prof["axes"] == P["axes"]
    assert prof["inertia_h"] == 6 and prof["anxiety"] == 0.2
    state = inner.feel(inner.fresh(prof, 0), "hurt", 0.8, "cruel", prof)
    assert inner.tick(state, 30, prof) and inner.mean(prof, "warmth") == 50
    assert set(inner.baseline(prof)) == {"v", "a", "d"}


def test_good_values_and_unknown_keys_survive_shaping():
    prof = inner.shape(
        {"axes": {"warmth": [80, 5]}, "inertia_h": 2.5, "baseline": [0.1, 0, -0.2], "extra": 1}
    )
    assert prof["axes"]["warmth"] == [80, 5] and prof["inertia_h"] == 2.5
    assert prof["baseline"] == [0.1, 0, -0.2] and prof["extra"] == 1


def _cast(conn):
    mira = library.create_item(conn, "character", "Mira")
    tobin = library.create_item(conn, "character", "Tobin")
    aren = library.create_item(conn, "character", "Aren")
    story = library.create_story(conn, "s", character_ids=[mira, tobin], persona_id=aren)
    ids = dict(conn.execute("SELECT name, id FROM entities WHERE story_id=?", (story,)).fetchall())
    return story, ids


def test_a_line_is_aimed_at_who_it_names_else_who_spoke_last(local_model):
    from kataki import chat, turns

    conn = local_model
    story, ids = _cast(conn)
    both = [ids["Mira"], ids["Tobin"]]
    turns.say(conn, story, "Tobin, you're useless.")
    assert inner.targets(conn, chat.active_path(conn, story), both) == {ids["Tobin"]}
    chat.append_message(conn, story, "assistant", "Easy.", ids["Mira"])
    turns.say(conn, story, "You're useless.")
    path = chat.active_path(conn, story)
    assert inner.targets(conn, path, both) == {ids["Mira"]}  # she is the one being answered
    assert inner.targets(conn, path, []) == set()


def test_only_the_one_it_is_aimed_at_takes_it_personally(local_model):
    from kataki import chat, turns

    conn = local_model
    story, ids = _cast(conn)
    turns.say(conn, story, "Mira, you're useless.")
    states = inner.react(conn, story, chat.active_path(conn, story))
    assert states[ids["Mira"]]["emotions"][0]["label"] == "hurt"
    assert states[ids["Tobin"]]["emotions"] == []  # he heard it; it wasn't about him


def test_a_line_names_people_in_the_order_it_names_them(local_model):
    from kataki import chat

    conn = local_model
    story, ids = _cast(conn)
    both = [ids["Mira"], ids["Tobin"]]
    assert chat.named(conn, "Tobin and Mira, listen.", both) == [ids["Tobin"], ids["Mira"]]
    assert chat.named(conn, "Nobody here.", both) == []
    assert chat.named(conn, "Mira!", []) == []


def test_social_traits_default_and_refuse_junk():
    assert P["social"] == {"forgiveness": 0.5, "trust_propensity": 0.5}
    prof = inner.shape({"social": {"forgiveness": 0.9, "trust_propensity": "lots"}})
    assert prof["social"] == {"forgiveness": 0.9, "trust_propensity": 0.5}


# --- slice 7: needs and energy ------------------------------------------------------------------

H = 60


def test_energy_follows_the_clock_and_the_chronotype():
    assert inner.energy(15 * H) > 0.8  # mid-afternoon
    assert inner.energy(3 * H) < 0.15  # before dawn
    assert inner.energy(1 * H) < inner.TIRED < inner.energy(21 * H)
    owl = 3  # hours her day runs late
    assert inner.energy(1 * H, owl) > inner.TIRED  # still going at one in the morning
    assert inner.energy(10 * H, owl) < inner.energy(10 * H)  # and slow in the morning


def test_needs_drift_to_rest_in_closed_form_and_move_with_what_is_said():
    prof = inner.shape({})
    state = inner.drive(inner.fresh(prof, 0), prof)
    assert state["needs"] == inner.START
    hurt = inner.drive(state, prof, "insult", "You're useless.")
    assert hurt["needs"]["competence"] < state["needs"]["competence"]
    bossed = inner.drive(state, prof, None, "You will do as I say, Mira.")
    assert bossed["needs"]["autonomy"] < state["needs"]["autonomy"]
    praised = inner.drive(hurt, prof, "praise", "You did so well today.")
    assert praised["needs"]["competence"] > hurt["needs"]["competence"]
    later = inner.tick(hurt, 12 * H, prof)  # half-way back to rest in twelve story-hours
    rest = inner.rest(prof)["competence"]
    assert later["needs"]["competence"] == pytest.approx(
        rest + (hurt["needs"]["competence"] - rest) / 2, abs=0.002
    )
    once, twice = (
        inner.tick(hurt, 6 * H, prof),
        inner.tick(inner.tick(hurt, 3 * H, prof), 6 * H, prof),
    )
    assert once["needs"] == pytest.approx(twice["needs"], abs=0.002)
    lonely = inner.shape({"attachment": {"anxiety": 0.9}})
    assert inner.rest(lonely)["relatedness"] < inner.LOW < inner.rest(prof)["relatedness"]


def test_the_most_pressing_need_shows_as_behaviour_outside_its_cooldown():
    prof = inner.shape({})
    state = inner.drive(inner.fresh(prof, 0), prof)
    assert inner.need_row(state, prof, 15 * H, []) is None  # all met, wide awake
    tired = inner.need_row(state, prof, 2 * H, [])
    assert tired["need"] == "energy" and "deny" in tired["text"]
    assert not re.search(r"\d", tired["text"])
    assert inner.need_row(state, prof, 2 * H, ["energy"]) is None  # shown lately: not again
    low = {**state, "needs": {**state["needs"], "competence": 0.1, "autonomy": 0.25}}
    got = inner.need_row(low, prof, 15 * H, [])
    assert got["need"] == "competence"  # the lowest first
    assert inner.need_row(low, prof, 15 * H, ["competence"])["need"] == "autonomy"
    assert inner.need_row(None, prof, 2 * H, [])["need"] == "energy"  # moods off: energy still
    owl = inner.shape({"chronotype_h": "late"})  # a bad value is ignored
    assert inner.need_row(None, owl, 2 * H, [])["need"] == "energy"
