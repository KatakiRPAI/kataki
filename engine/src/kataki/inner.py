"""How a character feels right now, kept by code between turns (docs/specs/2026-09-29-minds.md).

Emotions fade on story time (half-life ~25 story-minutes); mood follows them and drifts back to
the character's baseline over hours; what they show can differ from what they feel, and a mask
held too long leaks as a tell. The model never sets any of this: code reads what happened to
them, and the prompt gets the result in words. Zero model calls.

ponytail: every constant here is an estimate from the research (note 11 §9); tune them on the
probes (evals/probes.py), not by feel.
"""

import copy
import json
import math
import re
import sqlite3

import numpy as np

from kataki import chat, db, growth, knobs

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
    "social": {"forgiveness": 0.5, "trust_propensity": 0.5},  # 0-1; bonds.py reads them
}


STYLES = ("express", "suppress", "reappraise", "avoid")


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _ok(key: str, value, default) -> bool:
    """Whether a profile value can stand in for the default without breaking the maths."""
    if key == "style":
        return value in STYLES
    return _num(value) if _num(default) else isinstance(value, type(default))


def shape(own: dict) -> dict:
    """The defaults with a character's own values laid over them, one level deep. A value the
    maths can't use (wrong type, bad shape) is dropped, so a hand-edited profile never breaks
    a turn."""
    prof = copy.deepcopy(DEFAULT)
    for key, value in (own if isinstance(own, dict) else {}).items():
        if key == "axes" and isinstance(value, dict):
            prof[key] |= {
                k: v
                for k, v in value.items()
                if isinstance(v, list) and len(v) == 2 and all(map(_num, v))
            }
        elif key == "baseline":
            if isinstance(value, list) and len(value) == 3 and all(map(_num, value)):
                prof[key] = value
        elif key not in prof:
            prof[key] = value
        elif isinstance(prof[key], dict):
            if isinstance(value, dict):
                prof[key] |= {
                    k: v for k, v in value.items() if k not in prof[key] or _ok(k, v, prof[key][k])
                }
        elif _ok(key, value, prof[key]):
            prof[key] = value
    return prof


def profile(conn: sqlite3.Connection, entity_id: int) -> dict:
    """The character's mind profile: their library item's `data.mind` over the defaults, with
    the capped drift their growth rings in this story give them (slice 8)."""
    prof = shape(knobs.own(conn, entity_id).get("mind") or {})
    for axis, d in growth.profile_drift(conn, entity_id).items():
        if axis in prof["axes"]:
            mean_, spread = prof["axes"][axis]
            prof["axes"][axis] = [max(0, min(100, mean_ + d)), spread]
    return prof


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
    out = {
        **state,
        "emotions": emotions,
        "shown": state["shown"] if emotions else None,
        "mood": {c: round(base[c] + (state["mood"][c] - base[c]) * settle, 3) for c in "vad"},
        "reg_load": round(state["reg_load"] * 0.5 ** (dt / LOAD_HALF_MIN), 3),
        "t": now,
    }
    if isinstance(state.get("needs"), dict):  # slice 7: needs drift back to their resting level
        r, k = rest(prof), 0.5 ** (dt / NEED_HALF_MIN)
        out["needs"] = {n: round(r[n] + (v - r[n]) * k, 3) for n, v in state["needs"].items()
                        if n in r and _num(v)}  # fmt: skip
    return out


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
        "affection": [("fond", 0.6)],
        "flirt": [("fond", 0.3 + 0.3 * warm / 100)],
        "joke": [("amused", 0.5)],
        "snub": [("annoyed" if dom >= 50 else "hurt", 0.4)],
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


EVENTS = (
    "threat",
    "insult",
    "bad_news",
    "apology",
    "affection",
    "good_news",
    "praise",
    "flirt",
    "joke",
    "snub",
)  # first match wins
WORDS = {
    "threat": r"\b(i'?ll|i will|gonna) (kill|hurt|end) you\b|\bor else\b|\byou'?ll regret\b",
    "insult": r"\b(idiot|stupid|useless|pathetic|worthless|loser|moron|shut up|hate you"
    r"|disgusting|liar|fool|arrogant|coward|jerk)\b",
    # touch, flirting, laughter and being ignored: before these, a kiss or a snub did nothing on
    # lite. ponytail: words and *actions* only, like the rest
    "affection": r"\b(kiss(es|ed|ing)?|hugs?|hugged|hugging|embraces?|embraced|cuddles?"
    r"|nuzzles?|caress(es|ed)?|holds? (his|her|their|your) hand)\b",
    "flirt": r"\b(winks?|winked|flirts?|flirting|handsome|gorgeous|cute|sexy"
    r"|you look (good|nice|great|lovely|stunning))\b",
    "joke": r"\b(ha(ha)+|he(he)+|lol|lmao|jokes?|joking|kidding|funny|laughs?|laughing)\b",
    "snub": r"\b(ignores?|ignored|ignoring|walks? (past|away)|turns? (my|his|her|their) back"
    r"|without a word|whatever|not listening|leave me alone|go away"
    # refusing their touch rebuffs them: "stop touching me", "get off me", *pushes him away*
    r"|(don'?t|do not|stop|quit) (touch|kiss|hug|grabb?|hold)(ing)? me|hands off"
    r"|get (off|away from) me|(push|shove)(es|ed|s)? (him|her|them|you) (away|off))\b",
    "bad_news": r"\b(died|passed away|got fired|lost my|broke up|bad news|in (the )?hospital)\b",
    "apology": r"\b(i'?m sorry|i apologi[sz]e|forgive me|my fault|i was wrong)\b",
    "good_news": r"\b(got the job|got in|we won|good news|i passed|engaged|promoted)\b",
    "praise": r"\b(thank you|thanks|proud of you|amazing|brilliant|beautiful|love you|well done"
    r"|you'?re the best)\b",
}
PATTERNS = {event: re.compile(words, re.IGNORECASE) for event, words in WORDS.items()}
# a refusal or denial earlier in the same clause cancels a word: "don't kiss me", "I'm not
# flirting", "you're not stupid". Threats are exempt: "don't move or else" is still one.
NEGATION = re.compile(
    r"\b(not|no|never|stop|quit|dont|wont|cant|didnt|doesnt|isnt|\w+n['’]t)\b", re.IGNORECASE
)
CLAUSE = re.compile(r"[.!?;:,*\n]|\b(?:but|and|so)\b", re.IGNORECASE)


def _meant(text: str, event: str) -> bool:
    """Whether the event's words appear in `text` with no negation earlier in their clause.
    ponytail: one cue word, no scope or double negatives ("I can't stop laughing" reads as not
    laughing); the side call reads such lines on the standard level."""
    for m in PATTERNS[event].finditer(text):
        if event == "threat" or not NEGATION.search(CLAUSE.split(text[: m.start()])[-1]):
            return True
    return False


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
    ponytail: words and a negation cue (_meant), no deeper reading; slice 2's side call labels
    events on the standard level."""
    for event in EVENTS:
        if _meant(text, event):
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
        # every feeling held, strongest first, for the character card (0-1, faded to now)
        "emotions": [{"label": e["label"], "i": e["i"], "why": e["cause"]} for e in emotions],
    }


HEADER = "[Inside {name} right now: show it, never say it]"


def lines(state: dict, prof: dict) -> list[str]:
    """How they feel, as rows of the mind block: words, never numbers; none at rest."""
    if (p := public(state, prof)) is None:
        return []
    rows = []
    if p["label"]:
        rows.append(f"Feeling: {p['feels']}" + (f" ({p['why']})." if p["why"] else "."))
        if p["shows"] != p["label"]:
            hiding = f"Showing: {p['shows']}. Hiding the {NOUN.get(p['label'], p['label'])}"
            rows.append(hiding + (f"; it slips out as {p['tell']}." if p["tell"] else "."))
    if p["word"]:
        rows.append(f"Mood: {p['word']}.")
    return rows


def block(name: str, rows: list[str]) -> str:
    """The one mind block for the prompt's tail (note 22 §4): its rows under one header, or
    nothing when there is nothing to say."""
    return "\n".join([HEADER.format(name=name), *rows]) if rows else ""


def render(state: dict, prof: dict, name: str) -> str:
    """The mind block with only how they feel in it; empty at rest."""
    return block(name, lines(state, prof))


def face(state: dict) -> str:
    """The sprite for what they show (the lite level's face, no model call)."""
    shown = state.get("shown")
    return FEEL[shown["label"]][1] if shown else "neutral"


def _quote(text: str, n: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def said(name: str, text: str) -> str:
    """Why a feeling or a grudge is there, when a line caused it: 'Aren said "…"'."""
    return f'{name} said "{_quote(text)}"'


def targets(conn: sqlite3.Connection, path: list, hearers: list[int]) -> set[int]:
    """Who the latest line is aimed at, of those who heard it: everyone it names; else whoever of
    them spoke last (the one being answered); else all of them. Only they take it personally.
    ponytail: "Mira, Tobin is useless" aims at both; a name alone can't tell who is spoken to
    from who is spoken about."""
    if not hearers or not path:
        return set()
    story = [
        r[0]
        for r in conn.execute(
            "SELECT id FROM entities WHERE story_id=? AND kind='character'", (path[-1]["story_id"],)
        )
    ]
    if named := chat.named(conn, path[-1]["text"], story):
        return {n for n in named if n in hearers}  # named, but away: nobody here takes it
    last = next(
        (
            m["speaker_id"]
            for m in reversed(path[:-1])
            if m["role"] == "assistant" and m["speaker_id"] in hearers
        ),
        None,
    )
    return {last} if last is not None else set(hearers)


def current(conn: sqlite3.Connection, entity_id: int, path: list, prof: dict) -> dict | None:
    """Their latest state on this branch (anchored on a message of `path`, or written by the
    user), or None when they have felt nothing yet. Not ticked to now."""
    where, args = db.anchor_filter(set(), {m["id"] for m in path})
    row = conn.execute(
        f"SELECT state FROM mind_states WHERE entity_id=? AND {where}"
        " ORDER BY story_time DESC, id DESC LIMIT 1",
        [entity_id, *args],
    ).fetchone()
    return json.loads(row["state"]) if row else None


def react(
    conn: sqlite3.Connection, story_id: int, path: list, model=None, needs: bool = False
) -> dict[int, dict]:
    """Everyone here after the latest line, as they are now: faded to the present, stirred by
    that line if it was aimed at them and meant something (the others only overheard it),
    regulated; with `needs` (slice 7), their needs moved by it too. Nothing is written; the same
    path always gives the same answer, so a new take never feels it twice."""
    if not path:
        return {}
    last, now = path[-1], path[-1]["story_time"]
    scene_id = chat.scene_of(conn, story_id, path)
    cast = [
        e
        for e in chat.present_entities(conn, scene_id, path)
        if e["is_ai"] and e["kind"] == "character"
    ]
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)))
    hit = sense(last["text"], model) if last["role"] == "user" else None
    heard = [e["id"] for e in cast if last["id"] in chat.heard_by(conn, path, e["id"])]
    aimed = targets(conn, path, heard) if hit else set()
    spoken = targets(conn, path, heard) if needs and last["role"] == "user" else set()
    out = {}
    for e in cast:
        prof = profile(conn, e["id"])
        state = tick(current(conn, e["id"], path, prof) or fresh(prof, now), now, prof)
        if e["id"] in aimed:
            cause = said(names.get(last["speaker_id"], "Someone"), last["text"])
            for label, intensity in appraise(*hit, prof, state):
                state = feel(state, label, intensity, cause, prof)
        if needs:  # said to her, the line moves her needs; overheard, only time does
            to_her = e["id"] in spoken
            event = hit[0] if hit and e["id"] in aimed else None
            state = drive(state, prof, event, last["text"] if to_her else None)
        out[e["id"]] = regulate(state, prof)
    return out


def save(conn: sqlite3.Connection, states: dict[int, dict], message_id: int) -> None:
    """One row per character, anchored on the reply they were part of."""
    with conn:
        conn.executemany(
            "INSERT INTO mind_states(entity_id, story_time, state, message_id) VALUES(?, ?, ?, ?)",
            [(eid, s["t"], json.dumps(s), message_id) for eid, s in states.items()],
        )


# --- needs and energy (slice 7; note 17 §1, note 22 §1 and §4 row 6) -----------------------------

NEEDS = ("autonomy", "competence", "relatedness", "stimulation")  # SDT, plus boredom's opposite
START = {"autonomy": 0.6, "competence": 0.6, "relatedness": 0.5, "stimulation": 0.5}  # 1 = met
NEED_HALF_MIN = 12 * 60  # ponytail: story minutes for a need to drift half-way back to rest
LOW = 0.3  # ponytail: below this a need shows in behaviour
TIRED = 0.3  # ponytail: and below this, energy
NEED_COOL = 3  # ponytail: a need shown in one of her last this many replies waits
EFFECT = {  # what a line aimed at her does to her needs (note 17 §1: SDT thwarting)
    "insult": {"competence": -0.25, "relatedness": -0.1},
    "threat": {"autonomy": -0.3},
    "praise": {"competence": 0.2, "relatedness": 0.1},
    "apology": {"relatedness": 0.1},
    "good_news": {"stimulation": 0.2},
    "bad_news": {"relatedness": 0.05},
    "affection": {"relatedness": 0.15},
    "flirt": {"relatedness": 0.05, "stimulation": 0.05},
    "joke": {"stimulation": 0.15},
    "snub": {"relatedness": -0.15},
}
BOSSY = re.compile(
    r"\b(you (?:will|must|have to|need to) (?!be\b)|do as i say|do what i say|obey\b|i order you"
    r"|because i said so|that'?s an order|don'?t argue)",
    re.IGNORECASE,
)
CONTACT, DULL, LIVELY = 0.05, -0.015, 0.02  # ponytail: being talked to; a curt line; a real one
CURT = 3  # words or fewer, and no question: a curt line


def rest(prof: dict) -> dict[str, float]:
    """Where each need settles on its own: relatedness lower for the anxiously attached (alone,
    they get lonely), stimulation a little low (idle time bores)."""
    anx = prof["attachment"].get("anxiety", 0.2)
    anx = min(1.0, max(0.0, anx)) if _num(anx) else 0.2
    return {"autonomy": 0.6, "competence": 0.6, "relatedness": round(0.45 - 0.3 * anx, 3),
            "stimulation": 0.4}  # fmt: skip


def drive(state: dict, prof: dict, event: str | None = None, text: str | None = None) -> dict:
    """Her needs after a line: what it did to her (`event`, from sense), and, for a line said to
    her (`text`), being talked to, bossed about, or given a curt answer. Starts them if new."""
    needs = dict(state.get("needs") or START)
    for k, d in EFFECT.get(event, {}).items():
        needs[k] = needs.get(k, START[k]) + d
    if text is not None:
        if BOSSY.search(text):
            needs["autonomy"] -= 0.2
        needs["relatedness"] += CONTACT
        words = len(text.split())
        if words >= 8:
            needs["stimulation"] += LIVELY
        elif words <= CURT and "?" not in text:
            needs["stimulation"] += DULL
    return {**state, "needs": {k: round(min(1.0, max(0.0, v)), 3) for k, v in needs.items()}}


def energy(minute_of_day: int, chronotype_h: float = 0) -> float:
    """How much energy she has at this time of day, 0-1 (closed form, never stored): a circadian
    curve peaking mid-afternoon and lowest before dawn, minus sleep pressure that builds after
    about sixteen hours awake, peaks before dawn and is gone by her usual waking hour;
    `chronotype_h` shifts her day later (+) or earlier (-).
    ponytail: the two-process model with a fixed wake time; no sleep is tracked."""
    h = (minute_of_day / 60 - chronotype_h) % 24
    circadian = math.cos(2 * math.pi * (h - 15) / 24)
    pressure = max(0.0, 1 - abs((h - 7) % 24 - 20) / 4)  # 0 at 23:00 and 07:00, 1 at 03:00
    return round(min(1.0, max(0.0, 0.55 + 0.3 * circadian - 0.35 * pressure)), 3)


ROWS = {  # the need as behaviour, never as an announcement (note 17 §1)
    "energy": "Body: you're worn out. Shorter answers, little patience, a bit"
    " snappish; if anyone says you seem tired, deny it.",
    "autonomy": "Lately you have felt pushed around: you bristle at being told what to do and"
    " want to make your own call.",
    "competence": "Lately you have felt not good enough: touchy about criticism, keen to prove"
    " yourself.",
    "relatedness": "Lately you have felt lonely: you want closeness, and you ask about the other"
    " person more.",
    "stimulation": "You are restless and bored: you drift toward something new to do or talk"
    " about.",
}


def levels(state: dict | None, prof: dict, minute_of_day: int) -> dict[str, float]:
    """Energy now, and her drives if they are tracked."""
    chrono = prof.get("chronotype_h", 0)
    out = {"energy": energy(minute_of_day, chrono if _num(chrono) else 0)}
    needs = (state or {}).get("needs")
    return out | ({k: v for k, v in needs.items() if k in NEEDS} if isinstance(needs, dict) else {})


def need_row(state: dict | None, prof: dict, minute_of_day: int, recent: list) -> dict | None:
    """Row 6 of the mind block: the single most pressing need below its threshold and not shown
    in her last few replies (`recent`), as behaviour. -> {"need", "text"} or None."""
    low = [
        (v / (TIRED if k == "energy" else LOW), k)
        for k, v in levels(state, prof, minute_of_day).items()
        if v < (TIRED if k == "energy" else LOW) and k not in recent
    ]
    if not low:
        return None
    k = min(low)[1]
    return {"need": k, "text": ROWS[k]}
