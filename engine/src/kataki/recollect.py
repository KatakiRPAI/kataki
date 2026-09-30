"""How a character's memory is human, not just faded (docs/specs/2026-09-29-minds.md, slice 6;
note 14 §7.4-7.5, note 15 §1-2, §7A). Zero model calls.

- What she feels tilts what comes back (mood-congruent recall).
- A hazy memory she is pressed on and cannot reach gives true partial cues, built by code.
- Pinned and locked memories are never distorted, and a locked one is never forgotten.

The truth row is never touched: whatever her memory becomes is a `recollections` row of her
own, anchored like every minds row, so a swipe or a branch swaps it for free.

ponytail: every constant here is note 14's design default; tune on the probes, not by feel.
"""

import re

from kataki import clock

W_MOOD = 0.5  # note 14 §7.4: A' = A + 0.5 * M
MAX_CUES = 2


def congruence(valence: float | None, mood: float | None, importance: int) -> float:
    """The mood term M, weighted: a memory that felt like she feels now comes up more easily,
    the more so the more it mattered (arousal-gated). 0 without a valence or a mood."""
    if valence is None or mood is None:
        return 0.0
    return W_MOOD * valence * mood * importance / 10


def ago(minutes: int) -> str:
    """'about six years ago', in words only."""
    said = clock.spell(max(minutes, 1)).lower()
    if re.search(r"\d", said):
        said = f"many {said.split()[-1]}"
    return f"about {said} ago"


def _initial(name: str) -> str:
    return re.sub(r"^(the|a|an)\s+", "", name.strip(), flags=re.I)[:1].upper()


def cues(linked: list[dict], here: set[int], knower: int, emotion: str | None, since: int) -> list:
    """Up to two true partial cues for a memory on the tip of her tongue (note 14 §7.5): the
    first letter of someone in it who is not here, of the place, the feeling, how long ago."""
    out = []
    person = next(
        (e for e in linked if e["kind"] == "character" and e["id"] not in here | {knower}), None
    )
    if person and _initial(person["name"]):
        out.append(f"a name that starts with {_initial(person['name'])}")
    place = next((e for e in linked if e["kind"] == "place"), None)
    if place and _initial(place["name"]):
        out.append(f"a place whose name starts with {_initial(place['name'])}")
    if emotion and emotion.strip():
        out.append(f"the feeling: {emotion.strip()}")
    out.append(ago(since))
    return out[:MAX_CUES]


def tip(gist: str, said: list[str]) -> str:
    return f"{gist} (on the tip of your tongue: {'; '.join(said)})"
