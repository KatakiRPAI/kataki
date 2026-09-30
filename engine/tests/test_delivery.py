"""The courier (minds slice 9): length and register from state, and the delivery plan."""

import re

from kataki import context, delivery

HURT = {"label": "hurt", "shows": "calm", "word": "low"}  # felt hurt, masked as calm
ANGRY = {"label": "angry", "shows": "angry", "word": "on edge"}
BUZZING = {"label": "excited", "shows": "excited", "word": "buzzing"}


def test_the_setting_is_where_the_length_starts():
    for setting in ("short", "medium", "long"):
        assert (
            delivery.style(setting, "What did you do today, then?", None, False, None)["length"]
            == setting
        )


def test_a_curt_line_a_low_mood_and_tiredness_each_shorten_it():
    line = "So what did you get up to today at the docks?"
    assert delivery.style("medium", "Hm.", None, False, None)["length"] == "short"
    assert delivery.style("medium", line, HURT, False, None)["length"] == "short"
    assert delivery.style("medium", line, None, True, None)["length"] == "short"
    assert delivery.style("medium", "Hm.", HURT, True, None)["length"] == "brief"  # at most two
    assert delivery.style("short", "Hm.", HURT, True, None)["length"] == "brief"


def test_a_long_line_lengthens_it_by_one_at_most():
    long = " ".join(["word"] * 45)
    assert delivery.style("medium", long, None, False, None)["length"] == "long"
    assert delivery.style("long", long, BUZZING, False, None)["length"] == "long"


def test_register_follows_what_she_shows_and_where_she_stands():
    line = "Hello there, how are you?"
    grudge = {"trust": -20, "closeness": -5, "grudge": {"event": "promise_broken"}}
    assert delivery.style("medium", line, HURT, False, None)["register"] == "plain"  # masked
    assert delivery.style("medium", line, ANGRY, False, None)["register"] == "clipped"
    assert delivery.style("medium", line, None, False, grudge)["register"] == "clipped"
    wary = {"trust": -12, "closeness": 0, "grudge": None}
    assert delivery.style("medium", line, None, False, wary)["register"] == "guarded"
    assert delivery.style("medium", line, BUZZING, False, None)["register"] == "animated"
    close = {"trust": 3, "closeness": 14, "grudge": None}
    assert delivery.style("medium", line, None, False, close)["register"] == "warm"


def test_the_words_replace_the_setting_and_carry_no_numbers():
    got = delivery.style("medium", "Hello there, how are you?", None, False, None)
    assert got["words"] == context.LENGTHS["medium"]  # plain: the length line only
    got = delivery.style("medium", "Hm.", ANGRY, True, None)
    assert got["length"] == "brief" and got["register"] == "clipped"
    assert delivery.REGISTER_WORDS["clipped"] in got["words"]
    assert not re.search(r"\d", got["words"])


def test_bad_inputs_never_raise():
    got = delivery.style("nonsense", None, {"shows": None}, False, {"trust": "x"})
    assert got["length"] == "medium" and got["register"] == "plain"
