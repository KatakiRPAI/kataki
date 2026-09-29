"""How a character feels right now, kept by code between turns (docs/specs/2026-09-29-minds.md).

Emotions fade on story time (half-life ~25 story-minutes); mood follows them and drifts back to
the character's baseline over hours; what they show can differ from what they feel, and a mask
held too long leaks as a tell. The model never sets any of this: code reads what happened to
them, and the prompt gets the result in words. Zero model calls.

ponytail: every constant here is an estimate from the research (note 11 §9); tune them on the
probes (evals/probes.py), not by feel.
"""

import copy
import re
import sqlite3

import numpy as np

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
    prof = copy.deepcopy(DEFAULT)
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
    settle = 0.5 ** (dt / (max(prof["inertia_h"], 0.1) * 60))
    base = baseline(prof)
    emotions = [
        {**e, "i": round(e["i"] * fade, 3)} for e in state["emotions"] if e["i"] * fade >= FLOOR
    ]
    return {
        **state,
        "emotions": emotions,
        "shown": state["shown"] if emotions else None,
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


EVENTS = ("threat", "insult", "bad_news", "apology", "good_news", "praise")  # first match wins
WORDS = {
    "threat": r"\b(i'?ll|i will|gonna) (kill|hurt|end) you\b|\bor else\b|\byou'?ll regret\b",
    "insult": r"\b(idiot|stupid|useless|pathetic|worthless|loser|moron|shut up|hate you"
    r"|disgusting|liar)\b",
    "bad_news": r"\b(died|passed away|got fired|lost my|broke up|bad news|in (the )?hospital)\b",
    "apology": r"\b(i'?m sorry|i apologi[sz]e|forgive me|my fault|i was wrong)\b",
    "good_news": r"\b(got the job|got in|we won|good news|i passed|engaged|promoted)\b",
    "praise": r"\b(thank you|thanks|proud of you|amazing|brilliant|beautiful|love you|well done"
    r"|you'?re the best)\b",
}
PATTERNS = {event: re.compile(words, re.IGNORECASE) for event, words in WORDS.items()}
SEEDS = {  # a few lines per event; their mean vector is what "means that" looks like
    "threat": ["I'll make you regret this.", "Do it or you'll get hurt.", "Watch your back."],
    "insult": ["You're worthless.", "Nobody could stand you.", "You're a joke."],
    "bad_news": ["Something terrible happened.", "We lost everything.", "She's gone."],
    "apology": ["I shouldn't have said that.", "That was unfair of me.", "Can you forgive me?"],
    "good_news": ["It worked out!", "They said yes!", "Guess what, we did it."],
    "praise": ["You did so well.", "I really admire you.", "You're wonderful."],
}
SENSE_MIN = 0.5  # cosine to an event's centre before it counts
_centres: dict[int, tuple[list[str], np.ndarray]] = {}


def _centre(model) -> tuple[list[str], np.ndarray]:
    key = id(model)  # ponytail: one entry per loaded model object; there is one per process
    if key not in _centres:
        names = list(SEEDS)
        m = np.stack([np.asarray(model.encode(SEEDS[n]), dtype=float).mean(axis=0) for n in names])
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        _centres[key] = names, np.divide(m, norms, out=np.zeros_like(m), where=norms > 0)
    return _centres[key]


def sense(text: str, model=None) -> tuple[str, float] | None:
    """What a line was, to the one who heard it: (event, strength 0-1), or None. A word list
    first (precise); then, with an embedding model, closeness in meaning (catches rewordings).
    ponytail: no negation handling ("you're not stupid" reads as an insult); slice 2's side call
    labels events on the standard level."""
    for event in EVENTS:
        if PATTERNS[event].search(text):
            return event, 1.0
    if model is None or not text.strip():
        return None
    names, centres = _centre(model)
    vec = np.asarray(model.encode([text]), dtype=float)[0]
    if not (norm := np.linalg.norm(vec)):
        return None
    sims = centres @ (vec / norm)
    best = int(np.argmax(sims))
    return (names[best], round(float(sims[best]), 3)) if sims[best] >= SENSE_MIN else None


NOUN = {"angry": "anger", "afraid": "fear", "anxious": "worry", "sad": "sadness",
        "ashamed": "shame", "annoyed": "annoyance", "bored": "boredom"}  # fmt: skip


def _strength(i: float) -> str:
    return "a little " if i < 0.3 else "very " if i >= 0.6 else ""


def mood_word(state: dict, prof: dict) -> str:
    base = baseline(prof)
    dv = state["mood"]["v"] - base["v"]
    da = state["mood"]["a"] - base["a"]
    if dv <= -MOOD_SHOWS:
        return "on edge" if da > AROUSED else "low"
    if dv >= MOOD_SHOWS:
        return "buzzing" if da > AROUSED else "in a good mood"
    return ""


def public(state: dict, prof: dict) -> dict | None:
    """The mood as the app shows it (spec §8.2); None at rest. `feels` is private (Peek);
    `shows` and `tell` are what anyone in the room could see."""
    emotions, word = state["emotions"], mood_word(state, prof)
    if not emotions and not word:
        return None
    top = emotions[0] if emotions else None
    shown = state.get("shown")
    return {
        "label": top and top["label"],
        "feels": ", and ".join(f"{_strength(e['i'])}{e['label']}" for e in emotions[:2]) or word,
        "shows": shown["label"] if shown else "calm",
        "tell": shown and shown["tell"],
        "word": word,
        "why": top and top["cause"],
    }


def render(state: dict, prof: dict, name: str) -> str:
    """The mind block for the prompt's tail: words, never numbers; empty at rest."""
    if (p := public(state, prof)) is None:
        return ""
    lines = [f"[Inside {name} right now: show it, never say it]"]
    if p["label"]:
        lines.append(f"Feeling: {p['feels']}" + (f" ({p['why']})." if p["why"] else "."))
        if p["shows"] != p["label"]:
            hiding = f"Showing: {p['shows']}. Hiding the {NOUN.get(p['label'], p['label'])}"
            lines.append(hiding + (f"; it slips out as {p['tell']}." if p["tell"] else "."))
    if p["word"]:
        lines.append(f"Mood: {p['word']}.")
    return "\n".join(lines)


def face(state: dict) -> str:
    """The sprite for what they show (the lite level's face, no model call)."""
    shown = state.get("shown")
    return FEEL[shown["label"]][1] if shown else "neutral"
