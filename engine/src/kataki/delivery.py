"""How a reply is delivered (docs/specs/2026-09-29-minds.md slice 9; note 15 §7B, "the courier").

Pure code between the model's finished reply and the UI: how long she answers and in what
register (chosen from her state before the prompt, sent in words), and, for a chat-style reply,
the plan the UI plays: bubbles ("bursts"), a pause and a typing time for each, and at most one
display typo she corrects in the next bubble. Prose is never touched. Nothing here sleeps or
calls a model; the plan is a hint the user can always skip.

ponytail: every number here is a starting point from note 15 (whose own rates are unsourced
defaults); tune on the texting probe, not by feel.
"""

from kataki import context

DIALS = ("off", "light", "natural", "messy")
CLASSES = ("brief", "short", "medium", "long")
LENGTH_WORDS = {"brief": "Keep it very short: a few words, a line at most.", **context.LENGTHS}
REGISTER_WORDS = {
    "warm": "Talk easily and warmly, as with someone close.",
    "animated": "Talk with energy; it shows in how you write.",
    "guarded": "Stay polite but guarded, and give little away.",
    "clipped": "Keep your words clipped and cool.",
}
SHAKEN = frozenset({"hurt", "sad", "afraid", "anxious", "ashamed", "angry", "annoyed", "bored"})
CURT_WORDS = 3  # ponytail: a user line this short gets a shorter answer (mirroring, note 15 §3)
LONG_WORDS = 40  # ponytail: and one this long a longer one
MOVED = 10  # ponytail: ledger points (trust fallen, closeness risen) that change the register


def _num(x) -> float:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else 0.0


def style(setting: str, user_text: str | None, mood: dict | None, tired: bool,
          bond: dict | None) -> dict:  # fmt: skip
    """Note 22 §2 step 7g: the length class and register for this reply. `setting` is the
    "Reply length" setting (where it starts), `user_text` the line she answers, `mood` her mood
    as the app shows it (inner.public), `tired` her energy below slice 7's threshold, `bond`
    where she stands with the one she answers (bonds.public). -> {"length", "register", "words"};
    `words` goes into [Directive] in place of the setting's line. Words only, never numbers."""
    mood, bond = mood if isinstance(mood, dict) else {}, bond if isinstance(bond, dict) else {}
    start = CLASSES.index(setting) if setting in CLASSES[1:] else CLASSES.index("medium")
    words = len((user_text or "").split())
    shift = 0
    if user_text is not None and words <= CURT_WORDS:
        shift -= 1
    if words >= LONG_WORDS:
        shift += 1
    if mood.get("label") in SHAKEN or mood.get("word") in ("low", "on edge"):
        shift -= 1
    if tired:
        shift -= 1
    length = CLASSES[min(max(start + max(-2, min(1, shift)), 0), len(CLASSES) - 1)]
    shows = mood.get("shows")
    if shows in ("angry", "annoyed") or bond.get("grudge"):
        register = "clipped"
    elif _num(bond.get("trust")) <= -MOVED:
        register = "guarded"
    elif mood.get("word") == "buzzing" or shows == "excited":
        register = "animated"
    elif _num(bond.get("closeness")) >= MOVED:
        register = "warm"
    else:
        register = "plain"
    said = " ".join(w for w in (LENGTH_WORDS[length], REGISTER_WORDS.get(register)) if w)
    return {"length": length, "register": register, "words": said}
