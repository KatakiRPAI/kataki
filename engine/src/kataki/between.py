"""A life between scenes (docs/specs/2026-09-29-minds.md, slice 5; note 22 §3).

When two story-hours or more pass, each tracked character's time away is worked out by code (B0,
zero calls): feelings settle, worries habituate and an eased one rebounds, the time without the
user lands by attachment style, two characters who spent it together may pass a fact on, and the
card's own routine and events become offstage beats. On the standard and premium levels one small
call per character (B1) then words it: a first-person diary, what she would tell you, what is on
her mind. Everything is anchored on the skip message, so undoing the skip or switching branch
drops it. The prompt gets one thing, in words.

ponytail: every constant here is an estimate from the research (notes 11 §3, 16 §6-7, 17 §3);
tune them on the probes (evals/probes.py), not by feel.
"""

import random
import re

from kataki import clock

DAY, HOUR = clock.DAY, clock.HOUR
MIN_SKIP = 2 * HOUR  # a skip shorter than this is not time away


def beats(minutes: int) -> int:
    """How many offstage beats a skip holds: one under a day, one a day up to three, then one a
    week up to six (note 17 §3)."""
    if minutes < MIN_SKIP:
        return 0
    if minutes < DAY:
        return 1
    if minutes < 7 * DAY:
        return min(3, minutes // DAY)
    return min(6, max(3, minutes // (7 * DAY)))


EXPECTED_GAP = DAY  # ponytail: the user's usual gap; their running median is owed
ATTACHED = 0.5  # attachment anxiety or avoidance from which the style shows
MAX_WORRY = 0.8  # ponytail: the clinginess cap (note 16 §7): no worry is ever overwhelming
THREAD = 1.3  # an unanswered question worries more


def absence(prof: dict, gap: int, expected: int = EXPECTED_GAP, open_thread: bool = False) -> dict:
    """How time without the user lands, by attachment (note 16 §7): the anxious worry once the
    gap is long for them, the avoidant cool, the secure are glad to see you and cool only after a
    long silence. -> {"style", "worry": 0-1 | None, "cool": [(dimension, ledger change)], "glad"}"""
    anx = min(1.0, max(0.0, prof["attachment"].get("anxiety", 0.2)))
    avo = min(1.0, max(0.0, prof["attachment"].get("avoidance", 0.2)))
    anxious, avoidant = anx >= ATTACHED, avo >= ATTACHED
    style = ("fearful" if avoidant else "anxious") if anxious else (
        "avoidant" if avoidant else "secure"
    )  # fmt: skip
    ratio = gap / max(expected, 1)
    k = min(3.0, ratio / 2)  # how hard it lands: one at two usual gaps, three at six or more
    out: dict = {"style": style, "worry": None, "cool": [], "glad": False}
    cool: dict[str, float] = {}
    if anxious and ratio >= 2 - anx:
        out["worry"] = round(
            min(MAX_WORRY, anx * min(1.0, ratio / 3) * (THREAD if open_thread else 1)), 2
        )
        cool["trust"] = -2 * anx * k
        cool["closeness"] = -1 * k
    if avoidant and ratio >= 1:
        cool["closeness"] = cool.get("closeness", 0) - 3 * avo * k
    if style == "secure":
        out["glad"] = ratio >= 1
        if ratio > 3:
            cool["closeness"] = -0.5 * k
    out["cool"] = [(d, round(v, 2)) for d, v in cool.items() if v]
    return out


HALF_LIFE = {"worry": 2 * DAY, "rumination": 2 * DAY, "news": 3 * DAY}  # habituation (note 11)
SEED_HALF = DAY  # the rest: plans, ideas, the preoccupation


def weight(seed: dict, now: int) -> float:
    """How much a seed weighs at `now`: worries habituate over days, the rest fade faster."""
    half = seed.get("half_life_min") or HALF_LIFE.get(seed["kind"], SEED_HALF)
    return seed["weight"] * 0.5 ** (max(0, now - seed["story_time"]) / half)


GOSSIP_BASE = 2.0  # ponytail
SECRET_SHARE = 0.2  # a covert fact is a secret: it travels a fifth as often (note 16 §6)


def level(x: float) -> float:
    """A ledger number (how far they have moved, roughly -100..100) as 0.1-1 around a half."""
    return round(min(1.0, max(0.1, 0.5 + x / 100)), 3)


def gossip_p(close: float, trust: float, gossip: float, importance: int, covert: bool) -> float:
    """The chance a fact passes from one to another over a skip they spent together."""
    p = GOSSIP_BASE * close * trust * gossip * importance / 10
    return min(1.0, p * (SECRET_SHARE if covert else 1))


P_EVENT = 0.6  # ponytail: a beat is an event this often (steady storyteller pacing)


def _events(events) -> list[dict]:
    ok = []
    for e in events if isinstance(events, list) else []:
        if not isinstance(e, dict) or not isinstance(e.get("text"), str) or not e["text"].strip():
            continue
        good, bad = (e.get(k) if isinstance(e.get(k), str) and e[k].strip() else None
                     for k in ("good", "bad"))  # fmt: skip
        if good or bad:
            w = e.get("weight", 1)
            w = w if isinstance(w, (int, float)) and not isinstance(w, bool) and w > 0 else 1
            ok.append({"text": e["text"].strip(), "good": good, "bad": bad, "weight": w})
    return ok


def roll(rng: random.Random, prof: dict, events, lived: set[str]) -> dict | None:
    """One offstage beat from the card's events: which, and how it went (the able cope better),
    or None for an ordinary stretch. An event already lived in this story is not rolled again.
    -> {"text", "outcome", "good"}"""
    pool = [e for e in _events(events) if e["text"] not in lived]
    if not pool or rng.random() >= P_EVENT:
        return None
    ev = rng.choices(pool, weights=[e["weight"] for e in pool])[0]
    good = (
        rng.random() < 0.35 + 0.3 * prof.get("coping", 0.6)
        if ev["good"] and ev["bad"]
        else bool(ev["good"])
    )
    return {"text": ev["text"], "outcome": ev["good"] if good else ev["bad"], "good": good}


def span(minutes: int) -> str:
    """How long, in words only ('Two days'; 'Many months' where clock.spell would use digits)."""
    said = clock.spell(minutes)
    return f"Many {said.split()[-1]}" if re.search(r"\d", said) else said


def diary(minutes: int, lived: list[dict], routine: list[str], worry: str | None) -> str:
    """The templated diary (lite, and until the diary call has run): first person, no digits."""
    parts = [f"{span(minutes)} went by."]
    parts += [f"I {b['text']}, and {b['outcome']}." for b in lived]
    if routine:
        parts.append(f"Mostly I {routine[0]}.")
    if worry:
        parts.append(f"I kept thinking about {worry}.")
    if len(parts) == 1:
        parts.append("Nothing much happened.")
    return " ".join(parts)


# --- the diary call's output (B1), closed and validated like after.py -------------------------

KINDS = ("worry", "rumination", "plan", "unfinished", "intrusive", "idea")
WORDS = {"diary": 80, "telling": 20, "seed": 20, "preoccupation": 15}


def schema() -> dict:
    text = {"type": "string"}
    return {
        "type": "object",
        "properties": {
            "diary": text,
            "worth_telling": {"type": "array", "items": text},
            "seeds": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": list(KINDS)},
                        "text": text,
                        "weight": {"type": "integer", "enum": [1, 2, 3]},
                    },
                    "required": ["kind", "text", "weight"],
                    "additionalProperties": False,
                },
            },
            "preoccupation": text,
        },
        "required": ["diary", "worth_telling", "seeds", "preoccupation"],
        "additionalProperties": False,
    }


def _clip(text: str, n: int) -> str:
    return " ".join(text.split()[:n])


def read(data: dict) -> dict:
    """Validate the diary call. No diary raises ValueError (it is asked once more); a bad seed or
    news line is only dropped."""
    said = data.get("diary")
    if not isinstance(said, str) or not said.strip():
        raise ValueError("diary must be two or three sentences in the character's voice")
    tell = data.get("worth_telling") if isinstance(data.get("worth_telling"), list) else []
    seeds = data.get("seeds") if isinstance(data.get("seeds"), list) else []
    pre = data.get("preoccupation")
    return {
        "diary": _clip(said, WORDS["diary"]),
        "worth_telling": [
            _clip(t, WORDS["telling"]) for t in tell if isinstance(t, str) and t.strip()
        ][:2],
        "seeds": [
            {"kind": s["kind"], "text": _clip(s["text"], WORDS["seed"]), "weight": s["weight"]}
            for s in seeds
            if isinstance(s, dict)
            and s.get("kind") in KINDS
            and isinstance(s.get("text"), str)
            and s["text"].strip()
            and type(s.get("weight")) is int
            and 1 <= s["weight"] <= 3
        ][:3],
        "preoccupation": _clip(pre, WORDS["preoccupation"])
        if isinstance(pre, str) and pre.strip()
        else None,
    }
