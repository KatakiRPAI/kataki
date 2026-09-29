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


EMOTION_HALF_MIN = 25  # story minutes
LOAD_HALF_MIN = 60  # how fast holding a mask stops costing
MAX_EMOTIONS = 3
FLOOR = 0.08  # weaker than this, the feeling is gone
PUSH = 0.5  # how far one feeling moves mood toward its own anchor
MOOD_SHOWS = 0.05  # a mood this far from resting is worth a word
AROUSED = 0.15  # and this much more wound up than resting makes a low mood "on edge"

FEEL = {  # label -> ((valence, arousal, dominance), the sprite face it shows as)
    "calm": ((0.3, -0.4, 0.2), "neutral"),
    "content": ((0.5, -0.2, 0.3), "smiling"),
    "glad": ((0.6, 0.3, 0.3), "smiling"),
    "fond": ((0.6, 0.1, 0.1), "smiling"),
    "amused": ((0.5, 0.4, 0.3), "smiling"),
    "excited": ((0.6, 0.7, 0.3), "smiling"),
    "relieved": ((0.4, -0.3, 0.1), "smiling"),
    "surprised": ((0.1, 0.6, -0.1), "surprised"),
    "anxious": ((-0.4, 0.5, -0.4), "wary"),
    "afraid": ((-0.6, 0.7, -0.6), "wary"),
    "sad": ((-0.6, -0.3, -0.3), "neutral"),
    "hurt": ((-0.6, 0.2, -0.3), "wary"),
    "annoyed": ((-0.4, 0.3, 0.2), "doubtful"),
    "angry": ((-0.6, 0.7, 0.4), "wary"),
    "ashamed": ((-0.5, 0.2, -0.5), "wary"),
    "bored": ((-0.2, -0.6, 0.0), "neutral"),
}
NEGATIVE = frozenset(label for label, ((v, _, _), _) in FEEL.items() if v < 0)
TELLS = {  # how a masked feeling leaks
    "anxious": "over-explaining and fidgeting",
    "afraid": "glancing away",
    "sad": "going quiet, slower to answer",
    "hurt": "short answers, not meeting their eyes",
    "annoyed": "a flat tone",
    "angry": "clipped words",
    "ashamed": "steering away from the subject",
    "bored": "half-listening",
}


def fresh(prof: dict, now: int) -> dict:
    return {"mood": baseline(prof), "emotions": [], "reg_load": 0.0, "shown": None, "t": now}


def tick(state: dict, now: int, prof: dict) -> dict:
    """Time passes: feelings fade, mood settles back toward resting, a held mask costs less.
    Closed form, so a six-year skip costs the same as a minute."""
    dt = max(now - state["t"], 0)
    if not dt:
        return state
    fade = 0.5 ** (dt / EMOTION_HALF_MIN)
    settle = 0.5 ** (dt / (prof["inertia_h"] * 60))
    base = baseline(prof)
    return {
        **state,
        "emotions": [
            {**e, "i": round(e["i"] * fade, 3)} for e in state["emotions"] if e["i"] * fade >= FLOOR
        ],
        "mood": {c: round(base[c] + (state["mood"][c] - base[c]) * settle, 3) for c in "vad"},
        "reg_load": round(state["reg_load"] * 0.5 ** (dt / LOAD_HALF_MIN), 3),
        "t": now,
    }


def appraise(event: str, strength: float, prof: dict, state: dict) -> list[tuple[str, float]]:
    """What something that happened to them makes them feel, by temperament: the same insult
    hurts the meek and angers the dominant. -> [(label, intensity 0-1)]"""
    dom, warm = mean(prof, "dominance"), mean(prof, "warmth")
    hurting = any(e["label"] in ("hurt", "angry", "annoyed") for e in state["emotions"])
    felt = {
        "insult": [("angry" if dom >= 60 else "hurt", 0.7)],
        "threat": [("angry" if dom >= 70 else "afraid", 0.8)],
        "bad_news": [("sad", 0.3 + 0.4 * warm / 100)],
        "apology": [("relieved", 0.4)] if hurting else [],
        "good_news": [("glad", 0.5)],
        "praise": [("glad", 0.4 + 0.3 * warm / 100)],
    }[event]
    if event in ("insult", "threat") and prof["anxiety"] >= 0.5:
        felt.append(("anxious", 0.6 * prof["anxiety"]))
    gain = strength * (0.6 + 0.8 * mean(prof, "volatility") / 100)
    return [(label, round(min(1.0, i * gain), 3)) for label, i in felt]


def feel(state: dict, label: str, intensity: float, cause: str, prof: dict) -> dict:
    """Add one feeling: the strongest three are held, and mood moves toward it."""
    if prof["regulation"]["style"] == "reappraise" and label in NEGATIVE:
        intensity *= 1 - 0.4 * prof["regulation"]["capacity"]  # reappraisal really lowers it
    emotions = [dict(e) for e in state["emotions"]]
    if label == "relieved":  # relief eases what was hurting
        for e in emotions:
            if e["label"] in NEGATIVE:
                e["i"] = round(e["i"] * 0.6, 3)
    same = next((e for e in emotions if e["label"] == label), None)
    if same:
        same.update(i=max(same["i"], round(intensity, 3)), cause=cause, t=state["t"])
    else:
        emotions.append({"label": label, "i": round(intensity, 3), "cause": cause, "t": state["t"]})
    emotions = sorted((e for e in emotions if e["i"] >= FLOOR), key=lambda e: -e["i"])
    anchor = dict(zip("vad", FEEL[label][0], strict=True))
    mood = {
        c: round(state["mood"][c] + PUSH * intensity * (anchor[c] - state["mood"][c]), 3)
        for c in "vad"
    }
    return {**state, "emotions": emotions[:MAX_EMOTIONS], "mood": mood}


def regulate(state: dict, prof: dict) -> dict:
    """What they let show. Good feelings show. A bad one shows, or is masked or avoided by their
    regulation style; holding a mask builds up, first leaking as a tell, then slipping."""
    top = state["emotions"][0] if state["emotions"] else None
    style, capacity = prof["regulation"]["style"], prof["regulation"]["capacity"]
    load = state["reg_load"]
    if top is None:
        shown = None
    elif top["label"] not in NEGATIVE or style in ("express", "reappraise"):
        shown = {"label": top["label"], "i": top["i"], "tell": None}
    else:
        load = round(load + 0.5 * top["i"], 3)
        if load > 1.5 * capacity:  # the mask slips
            shown = {"label": top["label"], "i": top["i"], "tell": None}
        else:
            tell = TELLS.get(top["label"]) if load > capacity else None
            if style == "avoid":
                tell = "changing the subject"
            shown = {"label": "calm", "i": 0.3, "tell": tell}
    return {**state, "shown": shown, "reg_load": load}
