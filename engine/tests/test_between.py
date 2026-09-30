"""Slice 5: a life between scenes. Time away is felt by attachment style, the card's own life is
rolled into offstage beats, each character writes a diary, and one thing reaches the reply."""

import random
import re

import pytest

from kataki import between, clock, inner

DAY, HOUR = clock.DAY, clock.HOUR


def prof(**mind) -> dict:
    return inner.shape(mind)


# --- the rules (pure) --------------------------------------------------------------------------


def test_beats_grow_with_the_skip_and_stop_at_a_cap():
    assert [between.beats(m) for m in (HOUR, 2 * HOUR, 20 * HOUR, 2 * DAY, 5 * DAY)] == [
        0,
        1,
        1,
        2,
        3,
    ]
    assert between.beats(3 * 7 * DAY) == 3 and between.beats(60 * DAY) == 6


def test_absence_worries_the_anxious_and_not_the_secure():
    anxious = between.absence(prof(attachment={"anxiety": 0.8, "avoidance": 0.2}), 2 * DAY)
    secure = between.absence(prof(attachment={"anxiety": 0.2, "avoidance": 0.2}), 2 * DAY)
    assert anxious["style"] == "anxious" and anxious["worry"] > 0.4
    assert dict(anxious["cool"])["trust"] < 0
    assert secure["style"] == "secure" and secure["worry"] is None and secure["cool"] == []
    assert secure["glad"]
    # an unanswered question worries more; a short gap not at all
    thread = between.absence(prof(attachment={"anxiety": 0.8}), 2 * DAY, open_thread=True)
    assert thread["worry"] > anxious["worry"]
    assert between.absence(prof(attachment={"anxiety": 0.8}), 3 * HOUR)["worry"] is None


def test_the_avoidant_cool_and_the_fearful_do_both():
    avoidant = between.absence(prof(attachment={"anxiety": 0.2, "avoidance": 0.8}), 3 * DAY)
    assert avoidant["style"] == "avoidant" and avoidant["worry"] is None
    assert dict(avoidant["cool"])["closeness"] < 0 and not avoidant["glad"]
    fearful = between.absence(prof(attachment={"anxiety": 0.8, "avoidance": 0.8}), 3 * DAY)
    assert fearful["style"] == "fearful" and fearful["worry"] and dict(fearful["cool"])["trust"]


def test_worries_habituate_over_days():
    seed = {"kind": "worry", "weight": 0.8, "story_time": 0, "half_life_min": 2 * DAY}
    assert between.weight(seed, 2 * DAY) == pytest.approx(0.4)
    assert between.weight({**seed, "half_life_min": None}, DAY) < 0.8


def test_gossip_is_likelier_between_close_gossips_and_rare_for_secrets():
    open_ = between.gossip_p(0.8, 0.8, 0.9, 8, covert=False)
    assert open_ > 0.5
    assert between.gossip_p(0.8, 0.8, 0.9, 8, covert=True) == pytest.approx(open_ * 0.2)
    assert between.gossip_p(0.3, 0.3, 0.1, 3, covert=False) < 0.05
    assert between.level(0) == 0.5 and between.level(-200) == 0.1 and between.level(90) == 1


EVENTS = [{"text": "auditioned for the spring play", "good": "got a callback",
           "bad": "froze on the second monologue"}]  # fmt: skip


def test_a_roll_is_the_same_for_the_same_seed_and_skips_what_was_lived():
    rolls = [between.roll(random.Random("s:1:2:0"), prof(), EVENTS, set()) for _ in range(2)]
    assert rolls[0] == rolls[1]
    only_bad = [{"text": "auditioned", "bad": "froze"}]
    got = [between.roll(random.Random(f"k{i}"), prof(), only_bad, set()) for i in range(20)]
    assert all(g is None or (g["good"] is False and g["outcome"] == "froze") for g in got)
    assert any(got)
    assert between.roll(random.Random("x"), prof(), only_bad, {"auditioned"}) is None
    assert between.roll(random.Random("x"), prof(), [{"text": "x"}, "junk", {}], set()) is None


def test_the_templated_diary_is_first_person_and_has_no_digits():
    beat = {"text": "auditioned for the spring play", "outcome": "froze", "good": False}
    said = between.diary(330 * DAY, [beat], ["rehearsed lines"], "why Aren never answered")
    assert (
        said.startswith("Many months went by.")
        and "I auditioned for the spring play, and froze" in said
    )
    assert "I kept thinking about why Aren never answered." in said
    assert not re.search(r"\d", said)
    assert between.diary(2 * DAY, [], [], None) == "Two days went by. Nothing much happened."


def test_the_diary_calls_output_is_validated():
    got = between.read(
        {
            "diary": "I missed the harbour. " * 60,
            "worth_telling": ["I got a callback", " ", 3, "a", "b"],
            "seeds": [
                {"kind": "worry", "text": "whether the callback comes", "weight": 2},
                {"kind": "grudge", "text": "x", "weight": 2},
                {"kind": "plan", "text": "", "weight": 1},
                {"kind": "idea", "text": "a song", "weight": 7},
            ],
            "preoccupation": "the callback " * 20,
        }
    )
    assert len(got["diary"].split()) <= between.WORDS["diary"]
    assert got["worth_telling"] == ["I got a callback", "a"]
    assert got["seeds"] == [{"kind": "worry", "text": "whether the callback comes", "weight": 2}]
    assert len(got["preoccupation"].split()) == between.WORDS["preoccupation"]
    with pytest.raises(ValueError):
        between.read({"diary": " ", "worth_telling": [], "seeds": [], "preoccupation": ""})
    assert between.read({"diary": "Quiet days."})["seeds"] == []
    assert set(between.schema()["properties"]) == {
        "diary",
        "worth_telling",
        "seeds",
        "preoccupation",
    }
