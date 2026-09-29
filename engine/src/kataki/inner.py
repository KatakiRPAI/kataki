"""How a character feels right now, kept by code between turns (docs/specs/2026-09-29-minds.md).

Emotions fade on story time (half-life ~25 story-minutes); mood follows them and drifts back to
the character's baseline over hours; what they show can differ from what they feel, and a mask
held too long leaks as a tell. The model never sets any of this: code reads what happened to
them, and the prompt gets the result in words. Zero model calls.

ponytail: every constant here is an estimate from the research (note 11 §9); tune them on the
probes (evals/probes.py), not by feel.
"""

import sqlite3

from kataki import knobs

DEFAULT = {  # research note 22 §1; the profile editor fills the rest later
    "axes": {  # [mean 0-100, spread 0-30]
        "dominance": [50, 10],
        "warmth": [50, 10],
        "candor": [50, 10],
        "honesty": [60, 5],
        "yielding": [50, 10],
        "volatility": [40, 10],
    },
    "attachment": {"anxiety": 0.2, "avoidance": 0.2},
    "anxiety": 0.2,
    "coping": 0.6,
    "regulation": {"style": "express", "capacity": 0.5},  # express|suppress|reappraise|avoid
    "inertia_h": 6,  # mood half-life, story hours
    "susceptibility": 0.4,
}


def shape(own: dict) -> dict:
    """The defaults with a character's own values laid over them, one level deep."""
    prof = {k: dict(v) if isinstance(v, dict) else v for k, v in DEFAULT.items()}
    for key, value in own.items():
        if isinstance(prof.get(key), dict) and isinstance(value, dict):
            prof[key] = {**prof[key], **value}
        else:
            prof[key] = value
    return prof


def profile(conn: sqlite3.Connection, entity_id: int) -> dict:
    """The character's mind profile: their library item's `data.mind` over the defaults."""
    return shape(knobs.own(conn, entity_id).get("mind") or {})


def mean(prof: dict, axis: str) -> float:
    return prof["axes"].get(axis, [50, 10])[0]


def _clamp(x: float) -> float:
    return round(max(-1.0, min(1.0, x)), 3)


def baseline(prof: dict) -> dict[str, float]:
    """Resting mood in PAD space (valence, arousal, dominance), from temperament."""
    if b := prof.get("baseline"):
        return {"v": b[0], "a": b[1], "d": b[2]}
    warm, vol, dom = mean(prof, "warmth"), mean(prof, "volatility"), mean(prof, "dominance")
    anx = prof["anxiety"]
    return {
        "v": _clamp(0.6 * (warm - 50) / 100 - 0.3 * anx + 0.1),
        "a": _clamp(0.4 * (vol - 50) / 100 + 0.3 * anx - 0.1),
        "d": _clamp(0.8 * (dom - 50) / 100),
    }
