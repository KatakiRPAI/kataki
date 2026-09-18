"""The story clock, in story minutes. Code owns it; the LLM never does.

`parse_skip` reads narration for time skips ("six years later", "the next morning") so that
memory decay runs on story time. It is deliberately a small regex grammar: a wrong guess
costs little (power-law decay forgives a 2x error) and the UI offers an undo chip.
"""

import re

MINUTE, HOUR, DAY = 1, 60, 1440
UNITS = {
    "moment": 5,
    "minute": MINUTE,
    "hour": HOUR,
    "day": DAY,
    "week": 7 * DAY,
    "month": 30 * DAY,
    "year": 365 * DAY,
}
NUMBERS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100,
    "a couple of": 2, "a couple": 2, "a few": 3, "few": 3, "several": 5, "many": 10,
}  # fmt: skip
BARE_PLURAL = 3  # "hours later", "years later"
TIMES_OF_DAY = {
    "dawn": 6 * HOUR,
    "morning": 8 * HOUR,
    "noon": 12 * HOUR,
    "afternoon": 14 * HOUR,
    "dusk": 18 * HOUR,
    "evening": 19 * HOUR,
    "night": 22 * HOUR,
    "midnight": 24 * HOUR,
}

_N = "|".join(sorted(map(re.escape, NUMBERS), key=len, reverse=True)) + r"|\d+"
_UNIT = "|".join(UNITS)
_TOD = "|".join(TIMES_OF_DAY)
_AFTER = r"later|pass(?:es|ed)?|go(?:es)? by|went by|(?:have|had|has) passed"
_FLAGS = re.IGNORECASE

_SPEECH = re.compile(r'"[^"]*"|“[^”]*”')  # people talk about time; only narration moves it
_PATTERNS = [
    re.compile(rf"\bhalf an? (?P<half>{_UNIT})s? (?:{_AFTER})", _FLAGS),
    re.compile(rf"\b(?:(?P<n>{_N}) )?(?P<unit>{_UNIT})(?P<plural>s?) (?:{_AFTER})", _FLAGS),
    re.compile(rf"\bafter (?P<n>{_N}) (?P<unit>{_UNIT})s?\b", _FLAGS),
    re.compile(r"\b(?P<some>some time) later", _FLAGS),
    re.compile(rf"\b(?:the )?(?:next|following) (?P<next>{_UNIT}|{_TOD})\b", _FLAGS),
    re.compile(
        rf"\b(?:later )?that (?P<tod>{_TOD})\b|\bat (?P<at>dawn|dusk|noon|midnight)\b", _FLAGS
    ),
]


def _until(target: int, minute_of_day: int, tomorrow: bool = False) -> int:
    ahead = target - minute_of_day
    return ahead + DAY if tomorrow or ahead <= 0 else ahead


def _minutes(m: re.Match, minute_of_day: int) -> int:
    g = m.groupdict()
    if g.get("half"):
        return UNITS[g["half"].lower()] // 2
    if g.get("some"):
        return HOUR
    if word := g.get("next"):
        word = word.lower()
        if word in UNITS:
            return UNITS[word]
        return _until(TIMES_OF_DAY[word], minute_of_day, tomorrow=True)
    if word := g.get("tod") or g.get("at"):
        return _until(TIMES_OF_DAY[word.lower()], minute_of_day)
    n = g.get("n")
    if n is None:
        if not g.get("plural"):
            return 0  # "the day passed" is not a quantity we can trust
        count = 1 if g["unit"].lower() == "moment" else BARE_PLURAL
    else:
        count = int(n) if n.isdigit() else NUMBERS[n.lower()]
    return count * UNITS[g["unit"].lower()]


def parse_skip(text: str, minute_of_day: int = 0) -> int:
    """Story minutes this narration skips, or 0. `minute_of_day` is the clock before the skip."""
    text = _SPEECH.sub(" ", text)
    total, taken = 0, []
    for pattern in _PATTERNS:
        for m in pattern.finditer(text):
            if any(m.start() < end and start < m.end() for start, end in taken):
                continue  # an earlier, more specific pattern already claimed these words
            minutes = _minutes(m, (minute_of_day + total) % DAY)
            if minutes:
                total += minutes
                taken.append(m.span())
    return total


def label(story_time: int, epoch_offset_min: int = 8 * HOUR) -> str:
    """'Day 3, 14:20', or 'Year 7, Day 1, 09:30' once a story runs past its first year."""
    total = story_time + epoch_offset_min
    days, minute = divmod(total, DAY)
    years, day = divmod(days, 365)
    clock = f"Day {day + 1}, {minute // HOUR:02d}:{minute % HOUR:02d}"
    return f"Year {years + 1}, {clock}" if years else clock
