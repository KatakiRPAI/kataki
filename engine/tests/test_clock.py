import pytest

from kataki.clock import DAY, HOUR, date, label, parse_skip, spell

H, D = 60, 1440
W, MO, Y = 7 * D, 30 * D, 365 * D
NOON = 12 * H


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("Six years later, the docks had changed.", 6 * Y),
        ("six years later", 3_153_600),
        ("Three days pass without word.", 3 * D),
        ("Two weeks went by.", 2 * W),
        ("10 minutes later the door opens.", 10),
        ("An hour later she returns.", H),
        ("A year passed.", Y),
        ("After a few hours of walking, they arrive.", 3 * H),
        ("A couple of days later, the letter came.", 2 * D),
        ("Several months later", 5 * MO),
        ("Many years later", 10 * Y),
        ("Half an hour later", 30),
        ("Hours later, he woke.", 3 * H),
        ("Years later they met again.", 3 * Y),
        ("Moments later the guard returned.", 5),
        ("A moment later", 5),
        ("Twenty minutes have passed.", 20),
        ("Five days had passed since the fire.", 5 * D),
        ("Some time later", H),
        ("One month later", MO),
        ("1 week later", W),
        ("Three days later... and two hours later still", 3 * D + 2 * H),
    ],
)
def test_relative_skips(text, minutes):
    assert parse_skip(text) == minutes


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("The next morning, she was gone.", 20 * H),  # noon -> 08:00 tomorrow
        ("The following day they set out.", D),
        ("Later that evening, the tavern filled.", 7 * H),  # noon -> 19:00
        ("That night he could not sleep.", 10 * H),  # noon -> 22:00
        ("The next week", W),
        ("The following year", Y),
        ("At dawn they left.", 18 * H),  # noon -> 06:00 tomorrow
    ],
)
def test_skips_to_a_time_of_day_count_from_the_current_story_clock(text, minutes):
    assert parse_skip(text, minute_of_day=NOON) == minutes


def test_a_time_of_day_already_past_rolls_to_tomorrow():
    assert parse_skip("That evening", minute_of_day=21 * H) == 22 * H


@pytest.mark.parametrize(
    "text",
    [
        "She smiles and pours another drink.",
        "It happened six years ago.",  # the past, not a skip
        '"Come back three days later," she said.',  # spoken, not narrated
        "“See you next week,” he called.",
        "He was later than usual.",
        "The latest shipment arrived.",
    ],
)
def test_ordinary_prose_does_not_move_the_clock(text):
    assert parse_skip(text, minute_of_day=NOON) == 0


def test_label_reads_like_a_story_clock():
    assert label(0) == "Day 1, 08:00"  # stories open at 08:00 by default
    assert label(20 * H) == "Day 2, 04:00"
    assert label(6 * Y + 90) == "Year 7, Day 1, 09:30"
    assert label(0, epoch_offset_min=0) == "Day 1, 00:00"


@pytest.mark.parametrize(
    ("minutes", "said"),
    [
        (H, "An hour"),
        (D, "A day"),
        (2 * D, "Two days"),
        (W, "A week"),
        (MO, "A month"),
        (6 * Y, "Six years"),
        (40 * Y, "40 years"),
    ],
)
def test_how_long_it_was_in_words(minutes, said):
    assert spell(minutes) == said


STORM = [{"name": "the storm", "at": 11 * HOUR}]  # 19:00 on day 1, with the default 08:00 start


@pytest.mark.parametrize(
    ("story_time", "moments", "said"),
    [
        (11 * HOUR + 2, STORM, "The evening of the storm"),
        (17 * HOUR, STORM, "The night of the storm"),  # 01:00: still that night
        (DAY + 2 * HOUR, STORM, "The day after the storm"),
        (5 * DAY, STORM, "Five days after the storm"),
        (6 * 365 * DAY + 11 * HOUR, STORM, "Six years after the storm"),
        (0, [{"name": "the storm", "at": 3 * DAY}], "Three days before the storm"),
        (6 * 365 * DAY, [], "Year 7, Day 1"),  # nothing named: the count
        (2 * DAY, [], "Day 3"),
    ],
)
def test_a_date_counts_from_the_moments_a_story_has_named(story_time, moments, said):
    assert date(story_time, moments=moments) == said


def test_the_latest_moment_already_passed_is_the_one_counted_from():
    moments = [*STORM, {"name": "the proposal", "at": 3 * DAY}]
    assert date(8 * DAY, moments=moments) == "Five days after the proposal"
    assert date(2 * DAY, moments=moments) == "Two days after the storm"
