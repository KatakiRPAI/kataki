"""How a reply sounds (docs/specs/2026-09-29-minds.md slice 10; note 18 §6, §8).

A per-line cue decided by code from what she shows (tone, how strongly, a pause before she
speaks, how fast), with at most one non-verbal tag: her own `*sighs*` first, else the side
call's. Nothing here reaches a prompt, and nothing runs in the turn but `untag` and `cue`: the
audio is made only when the app asks for it.

ponytail: the pause and speed numbers are starting points (note 18 gives none); tune by ear.
"""

import re
import sqlite3

from kataki import features, knobs, roles

TONES = ("neutral", "warm", "cheerful", "excited", "anxious", "sad", "hurt", "cold", "angry",
         "flat")  # fmt: skip
TAGS = ("laugh", "chuckle", "sigh", "gasp", "sniff", "groan", "hum")
SHOWN = {  # what she shows (inner.FEEL) -> how it sounds
    "calm": "neutral", "content": "warm", "fond": "warm", "relieved": "warm",
    "glad": "cheerful", "amused": "cheerful", "excited": "excited", "surprised": "excited",
    "anxious": "anxious", "afraid": "anxious", "ashamed": "anxious", "sad": "sad",
    "hurt": "hurt", "annoyed": "cold", "angry": "angry", "bored": "flat",
}  # fmt: skip
WORD = {"low": "sad", "on edge": "anxious", "buzzing": "cheerful", "in a good mood": "warm"}
PACE = {  # ponytail: tone -> (pause before speaking in ms, speed) at clear strength
    "neutral": (250, 1.0), "warm": (300, 1.0), "cheerful": (200, 1.05),
    "excited": (150, 1.1), "anxious": (200, 1.08), "sad": (700, 0.9), "hurt": (600, 0.92),
    "cold": (400, 0.97), "angry": (150, 1.06), "flat": (400, 0.95),
}  # fmt: skip
STRONG = {1: (0.75, 0.5), 2: (1.0, 1.0), 3: (1.25, 1.5)}  # strength -> (pause x, speed shift x)
SPEED = (0.5, 2.0)
VERBS = {  # a one-word action of hers that is a sound: *sighs*, *laughs softly*
    "laugh": "laugh", "laughs": "laugh", "giggles": "laugh", "chuckle": "chuckle",
    "chuckles": "chuckle", "snorts": "chuckle", "sigh": "sigh", "sighs": "sigh",
    "gasp": "gasp", "gasps": "gasp", "sniff": "sniff", "sniffs": "sniff", "sniffles": "sniff",
    "groan": "groan", "groans": "groan", "hum": "hum", "hums": "hum",
}  # fmt: skip
ACTION = re.compile(r"\*([^*\n]{1,60})\*|_([^_\n]{1,60})_")
TAG = re.compile(r"[\[<]\s*(" + "|".join(sorted(VERBS, key=len, reverse=True)) + r")\s*[\]>]",
                 re.I)  # fmt: skip


def on(conn: sqlite3.Connection, entity_id: int | None) -> bool:
    """Is this character voiced? The feature, a `voice` model, and `voice.on` (her own
    `data.voice.on` wins; off by default on every level, lite included)."""
    if entity_id is None or not features.enabled(conn, "mind.voice"):
        return False
    if roles.resolve(conn, "voice", get_key=lambda _: None) is None:
        return False
    mine = knobs.own(conn, entity_id).get("voice")
    choice = mine.get("on") if isinstance(mine, dict) else None
    if choice in (None, "inherit"):
        choice = knobs.setting(conn, "voice.on", False)
    return choice is True


def untag(text: str) -> tuple[str, list[str]]:
    """Speech tags the model wrote (`[laughs]`, `<sigh>`) out of the visible reply, kept as
    tags. Only the closed list: `[OOC]` and anything else stays."""
    tags = [VERBS[m.group(1).lower()] for m in TAG.finditer(text)]
    if not tags:
        return text, []
    kept = TAG.sub("", text)
    kept = "\n".join(re.sub(r"[ \t]{2,}", " ", line).strip() for line in kept.splitlines())
    return re.sub(r"\n{3,}", "\n\n", kept).strip(), tags


def acted(text: str) -> str | None:
    """The first sound her own actions make: `*sighs*`, `*laughs softly*` (four words at most)."""
    for m in ACTION.finditer(text or ""):
        words = (m.group(1) or m.group(2)).lower().split()
        if len(words) <= 4 and (hit := next((VERBS[w] for w in words if w in VERBS), None)):
            return hit
    return None


def _strength(mood: dict) -> int:
    feels = str(mood.get("feels") or "")
    return 3 if feels.startswith("very ") else 1 if feels.startswith("a little ") else 2


def _num(x, default: float) -> float:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else default


def cue(gen, text: str, own: dict | None = None) -> dict:
    """The cue for one reply (spec §8.3 slice 10) from its `gen` (the mood it was said with,
    `after.voice`, stripped `voice.tags`), its text and her `data.voice` (speed)."""
    gen = gen if isinstance(gen, dict) else {}
    mood = gen.get("mind") if isinstance(gen.get("mind"), dict) else {}
    tone, strength = "neutral", 1
    shows = mood.get("shows")
    if shows in SHOWN and shows != "calm":
        tone = SHOWN[shows]
        strength = _strength(mood) if shows == mood.get("label") else 1
    elif not mood.get("label") and mood.get("word") in WORD:  # a mood with no feeling behind it
        tone = WORD[mood["word"]]
    after = gen.get("after") if isinstance(gen.get("after"), dict) else {}
    side = after.get("voice") if isinstance(after.get("voice"), dict) else {}
    by = "code"
    if side.get("tone") in TONES:
        tone, by = side["tone"], "side"
    kept = (gen.get("voice") or {}).get("tags") if isinstance(gen.get("voice"), dict) else None
    tag = acted(text) or next((t for t in kept or [] if t in TAGS), None)
    if tag is None and side.get("tag") in TAGS:
        tag, by = side["tag"], "side"
    pause, speed = PACE[tone]
    pause_x, shift_x = STRONG[strength]
    mine = _num((own or {}).get("speed"), 1.0) if isinstance(own, dict) else 1.0
    speed = min(max((1 + (speed - 1) * shift_x) * mine, SPEED[0]), SPEED[1])
    return {
        "tone": tone,
        "intensity": strength,
        "pause_ms": round(pause * pause_x),
        "speed": round(speed, 3),
        "tags": [tag] if tag else [],
        "by": by,
    }
