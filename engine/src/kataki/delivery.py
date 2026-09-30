"""How a reply is delivered (docs/specs/2026-09-29-minds.md slice 9; note 15 §7B, "the courier").

Pure code between the model's finished reply and the UI: how long she answers and in what
register (chosen from her state before the prompt, sent in words), and, for a chat-style reply,
the plan the UI plays: bubbles ("bursts"), a pause and a typing time for each, and at most one
display typo she corrects in the next bubble. Prose is never touched. Nothing here sleeps or
calls a model; the plan is a hint the user can always skip.

ponytail: every number here is a starting point from note 15 (whose own rates are unsourced
defaults); tune on the texting probe, not by feel.
"""

import random
import re
import zlib

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


# --- the courier: bursts, timing, one corrected typo (note 15 §3, §7B) --------------------------

CAP = {"light": 2, "natural": 3, "messy": 4}  # ponytail: the most bubbles a reply becomes
TYPO_RATE = {"natural": 0.1, "messy": 0.2}  # ponytail: note 15 §7A (natural 1 in 10, messy 1 in 5)
READ_MS, READ_CAP = 30, 3000  # ponytail: reading the user's line (Jones and Bergen: 30 ms a char)
TYPE_MS = 55  # ponytail: typing a character (the Turing test's 300 ms drags in a long roleplay)
TYPING_MIN, TYPING_MAX = 400, 6000  # ponytail: ms
DELAY_MAX = 8000  # ponytail: note 15 §3: keep a simulated wait within about 1.5-8 s
GAP_MS = (300, 900)  # ponytail: the pause between one bubble and the next
FIX_MS = (300, 700)  # ponytail: and before the "*word" that corrects a typo
WEIGHTY = 1.5  # ponytail: a hard moment (a decision in [Directive]) is slower to start
PROSE = re.compile(r'[*_"“”]')
PRONOUN = frozenset({"she", "he", "they", "her", "his", "their"})
ABBREV = re.compile(r"\b(?:mr|mrs|ms|dr|st)\.$", re.I)
KEYS = "qwertyuiop asdfghjkl zxcvbnm".split()


def chatty(text: str, name: str) -> bool:
    """Is this reply a text message, not prose? No action markup, no quoted speech, no opening
    pronoun and not her own name (narration names its subject; a text does not). Every doubt
    reads as prose: a false "prose" costs the effect, a false "text" would mangle a story."""
    if not text.strip() or PROSE.search(text):
        return False
    first = re.match(r"\W*(\w+)", text)
    if first and first.group(1).lower() in PRONOUN:
        return False
    names = [n for n in dict.fromkeys([name, *name.split()[:1]]) if n]
    return not any(re.search(rf"\b{re.escape(n)}\b", text, re.I) for n in names)


def _sentences(line: str) -> list[str]:
    out: list[str] = []
    for piece in re.split(r"(?<=[.!?…])\s+", line):
        if out and (ABBREV.search(out[-1]) or out[-1].endswith(("..", "…"))):
            out[-1] += " " + piece  # "Mr. Vey", "the dock... he": not a sentence's end
        else:
            out.append(piece)
    return [p for p in out if p.strip()]


def split(text: str, cap: int, lines_only: bool) -> list[str]:
    """The model's own lines, then (unless `lines_only`) their sentences, with the shortest
    neighbours merged until there are at most `cap`. Lines merged into one bubble keep their line
    break (an unpunctuated line would otherwise run into the next); sentences, a space."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    parts = [  # (text, its first line, its last line)
        (s, n, n) for n, ln in enumerate(lines) for s in ([ln] if lines_only else _sentences(ln))
    ]
    while len(parts) > max(cap, 1):
        i = min(range(len(parts) - 1), key=lambda i: len(parts[i][0]) + len(parts[i + 1][0]))
        (a, first, end), (b, start, last) = parts[i], parts[i + 1]
        parts[i : i + 2] = [(f"{a}{' ' if end == start else chr(10)}{b}", first, last)]
    return [p for p, _, _ in parts]


def _pace(mood: dict | None, tired: bool) -> float:
    """How fast she answers: wound up is quicker, low or hurt slower, tired slower."""
    mood = mood if isinstance(mood, dict) else {}
    label, word = mood.get("label"), mood.get("word")
    p = 1.0
    if word in ("buzzing", "on edge") or label in ("excited", "angry"):
        p = 0.8
    elif word == "low" or label in ("hurt", "sad", "ashamed", "bored"):
        p = 1.3
    return p * (1.2 if tired else 1.0)


def _typing(text: str, pace: float) -> int:
    return round(min(max(len(text) * TYPE_MS * pace, TYPING_MIN), TYPING_MAX))


def _mistype(word: str, rng: random.Random) -> str:
    """One keyboard-plausible slip: two letters swapped, one dropped or doubled, or a neighbour
    key hit instead."""
    for _ in range(8):
        i = rng.randrange(1, len(word) - 1)
        how = rng.choice(("swap", "drop", "double", "near"))
        if how == "swap":
            out = word[:i] + word[i + 1] + word[i] + word[i + 2 :]
        elif how == "drop":
            out = word[:i] + word[i + 1 :]
        elif how == "double":
            out = word[:i] + word[i] + word[i:]
        else:
            row = next((r for r in KEYS if word[i] in r), None)
            if row is None:
                continue
            j = row.index(word[i])
            near = [row[k] for k in (j - 1, j + 1) if 0 <= k < len(row)]
            out = word[:i] + rng.choice(near) + word[i + 1 :]
        if out != word:
            return out
    return word


def plan(text: str, dial: str, *, name: str, heard: str | None, mood: dict | None,
         tired: bool, weighty: bool, typo_ok: bool, seed: str) -> dict | None:  # fmt: skip
    """The delivery plan for a finished, clean reply (spec §8.3 slice 9), or None when the dial
    is off. `heard`: the line she answers (she reads it first); `weighty`: a decision rode in
    [Directive]; `typo_ok`: the turn allows a typo at all; `seed`: the same reply always gets the
    same plan. Prose gets `mode: "prose"` and no bursts. Display only: `text` is never changed."""
    if dial == "off":
        return None
    dial = dial if dial in CAP else "light"
    if not chatty(text, name):
        return {"mode": "prose", "dial": dial, "bursts": [], "typo": None}
    rng = random.Random(zlib.crc32(seed.encode()))
    pace = _pace(mood, tired)
    parts = split(text, CAP[dial], lines_only=dial == "light")
    bursts = []
    for i, part in enumerate(parts):
        if i == 0:
            wait = min(len(heard or ""), READ_CAP // READ_MS) * READ_MS
            wait += rng.gammavariate(2.5, 0.25) * 1000  # thinking, right-skewed
            wait *= pace * (WEIGHTY if weighty else 1.0)
        else:
            wait = rng.uniform(*GAP_MS) * pace
        bursts.append({"text": part, "typing_ms": _typing(part, pace),
                       "delay_ms": round(min(wait, DELAY_MAX))})  # fmt: skip
    typo = None
    roll = rng.random()  # drawn every time, so allowing a typo never moves the timing
    if typo_ok and roll < TYPO_RATE.get(dial, 0.0):
        spots = [(i, m) for i, b in enumerate(bursts)
                 for m in re.finditer(r"(?<![\w'])[a-z]{4,}(?![\w'])", b["text"])]  # fmt: skip
        if spots:
            i, m = rng.choice(spots)
            right = m.group()
            wrong = _mistype(right, rng)
            if wrong != right:
                b = bursts[i]
                b["text"] = b["text"][: m.start()] + wrong + b["text"][m.end() :]
                b["typo"] = typo = {"wrong": wrong, "right": right}
                fix = f"*{right}"
                bursts.insert(i + 1, {"text": fix, "typing_ms": _typing(fix, pace),
                                      "delay_ms": round(rng.uniform(*FIX_MS)),
                                      "correction": True})  # fmt: skip
    return {"mode": "text", "dial": dial, "bursts": bursts, "typo": typo}
