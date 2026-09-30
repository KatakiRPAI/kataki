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

import contextlib
import json
import logging
import random
import re
import sqlite3
from collections.abc import Callable

from kataki import (
    bonds,
    chat,
    clock,
    db,
    features,
    goals,
    growth,
    honesty,
    inner,
    knobs,
    recollect,
    retrieve,
    roles,
)
from kataki.activation import FIDELITY
from kataki.llm import LLM

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
WORDS = {"diary": 80, "telling": 20, "seed": 20, "preoccupation": 15, "tactic": 12}
# a line said to the user ("Next time, just stay") is a message, not news of her own days
ADDRESSED = re.compile(r"\b(you|your|you're|yours)\b", re.IGNORECASE)


def schema(goals_: list[str] = (), work: dict | None = None) -> dict:
    """The diary call's JSON; with her goals' handles (slice 7), one optional goal change; with a
    deep pass's working set (slice 8), the deep section."""
    text = {"type": "string"}
    out = {
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
    if goals_:
        change = {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "enum": list(goals_)},
                "change": {"type": "string", "enum": list(goals.CHANGES)},
                "tactic": text,
            },
            "required": ["goal", "change", "tactic"],
            "additionalProperties": False,
        }
        out["properties"]["goal"] = {"anyOf": [{"type": "null"}, change]}
        out["required"].append("goal")
    if work:
        out["properties"]["deep"] = _deep_schema(work)
        out["required"].append("deep")
    return out


def _deep_schema(work: dict) -> dict:
    """B2's section (note 22 §3), every reference closed to the handles it was shown."""
    text = {"type": "string"}
    cite = {"type": "array", "items": {"type": "string", "enum": list(work["memories"])}}

    def obj(**props) -> dict:
        return {"type": "object", "properties": props, "required": list(props),
                "additionalProperties": False}  # fmt: skip

    deep = {
        "self": {"anyOf": [{"type": "null"}, obj(line=text, sources=cite)]},
        "rings": {"type": "array", "items": obj(
            kind={"type": "string", "enum": list(growth.RINGS)}, claim=text, sources=cite,
            trait={"type": "string", "enum": [*growth.TRAITS, "none"]})},
    }  # fmt: skip
    if work["people"]:
        about = {"type": "string", "enum": list(work["people"])}
        deep = {"relationship": {"type": "array", "items": obj(about=about, line=text,
                                                               sources=cite)}} | deep  # fmt: skip
    return obj(**deep)


def _goal(data: dict, goals_: list[str]) -> dict:
    """The one goal change, only when goals were given; anything off the lists is None."""
    if not goals_:
        return {}
    g = data.get("goal")
    ok = isinstance(g, dict) and g.get("goal") in goals_ and g.get("change") in goals.CHANGES
    tactic = g.get("tactic") if ok and isinstance(g.get("tactic"), str) else ""
    return {
        "goal": {"goal": g["goal"], "change": g["change"], "tactic": _clip(tactic, WORDS["tactic"])}
        if ok
        else None
    }


def _clip(text: str, n: int) -> str:
    return " ".join(text.split()[:n])


def read(data: dict, goals_: list[str] = (), deep: bool = False) -> dict:
    """Validate the diary call. No diary raises ValueError (it is asked once more); a bad seed,
    news line or goal change is only dropped; the deep section is passed on for its gate."""
    said = data.get("diary")
    if not isinstance(said, str) or not said.strip():
        raise ValueError("diary must be two or three sentences in the character's voice")
    tell = data.get("worth_telling") if isinstance(data.get("worth_telling"), list) else []
    seeds = data.get("seeds") if isinstance(data.get("seeds"), list) else []
    pre = data.get("preoccupation")
    return (
        {
            "diary": _clip(said, WORDS["diary"]),
            "worth_telling": [
                _clip(t, WORDS["telling"])
                for t in tell
                if isinstance(t, str) and t.strip() and not ADDRESSED.search(t)
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
        | _goal(data, goals_)
        | ({"deep": data.get("deep")} if deep else {})
    )


# --- the tick at the skip (B0): zero calls, all levels ------------------------------------------

TRIGGER = "between"  # an extraction_runs row that reads no transcript: the job's rows ride on it
TRACK = 4  # ponytail: characters followed through a skip (note 22 §3: "up to 3-4")
CALLS = 3  # ponytail: of those, how many get the diary call
RECENT = 20  # lines back in which having spoken still counts as "on screen lately"
REBOUND_MIN = 6 * HOUR  # a relational worry eased by contact comes back after this long
REBOUND = 0.5  # at this share of itself, once
NEGLECT_HALF = 7 * DAY  # ponytail: how fast the cooling of time apart fades
BEAT_FEEL = {True: ("glad", 0.5), False: ("sad", 0.6)}  # an offstage beat's mood nudge
TOLD_BELIEF = 0.7  # gossip is believed, a little less than being there (note 16 §6)
GOSSIP_MAX = 2  # facts one passes to another per skip
GOSSIP_MIN = 4  # importance a fact needs to be worth passing on


def missed(ab: dict) -> str | None:
    """How the time away landed, from what absence() decided, never from the style alone: a
    short absence is just a short absence (§6 rule 1)."""
    if ab["worry"]:
        return "worried"
    if ab["style"] in ("avoidant", "fearful") and dict(ab["cool"]).get("closeness"):
        return "cooler"
    return "glad" if ab["glad"] else None


def _skip(path: list) -> dict | None:
    """The skip this path has just been through: the latest of its last three lines that moved
    the clock two story-hours or more. Older skips have been lived through already."""
    return next((m for m in reversed(path[-3:]) if m["skip_minutes"] >= MIN_SKIP), None)


def run_of(conn: sqlite3.Connection, story_id: int, message_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM extraction_runs WHERE story_id=? AND trigger=? AND to_message_id=?",
        (story_id, TRIGGER, message_id),
    ).fetchone()


def job(conn: sqlite3.Connection, story_id: int, path: list) -> sqlite3.Row | None:
    """The latest between run on this branch, if any."""
    if not path:
        return None
    ids = [m["id"] for m in path]
    return conn.execute(
        f"SELECT * FROM extraction_runs WHERE story_id=? AND trigger=? AND status='ok'"
        f" AND to_message_id IN ({','.join('?' * len(ids))}) ORDER BY to_message_id DESC LIMIT 1",
        [story_id, TRIGGER, *ids],
    ).fetchone()


def _off(conn: sqlite3.Connection, entity_id: int) -> bool:
    return knobs.dial(conn, entity_id, "offscreen", "on") == "off"


def tracked(conn: sqlite3.Connection, story_id: int, path: list) -> list[int]:
    """Who is followed through the skip: the AI characters here, then whoever spoke lately."""
    scene_id = chat.scene_of(conn, story_id, path)
    here = [
        e["id"]
        for e in chat.present_entities(conn, scene_id, path)
        if e["is_ai"] and e["kind"] == "character"
    ]
    spoke = [m["speaker_id"] for m in reversed(path[-RECENT:]) if m["role"] == "assistant"]
    ai = {
        r[0]
        for r in conn.execute(
            "SELECT id FROM entities WHERE story_id=? AND kind='character' AND is_ai=1"
            " AND hidden=0",
            (story_id,),
        )
    }
    return [c for c in dict.fromkeys([*here, *spoke]) if c in ai and not _off(conn, c)][:TRACK]


class _Tick:
    """One skip's job, written inside one transaction on its run."""

    def __init__(self, conn, story_id: int, path: list, skip: dict, run: int):
        self.conn, self.story_id, self.run, self.skip = conn, story_id, run, skip
        self.path = path  # up to and including the skip message
        self.now, self.minutes = skip["story_time"], skip["skip_minutes"]
        self.start = self.now - self.minutes
        story = conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()
        self.persona = story["persona_entity_id"]
        self.names = dict(
            conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,))
        )
        self.user = self.names.get(self.persona)
        self.affect = features.enabled(conn, "mind.affect")
        self.bonded = features.enabled(conn, "mind.bonds")

    def rng(self, *key) -> random.Random:
        """Seeded by the story, the skip and what is rolled: a retake rolls the same life."""
        return random.Random(":".join(map(str, (self.story_id, self.skip["id"], *key))))

    def seed(self, who: int, kind: str, text: str, weight: float, t: int | None = None,
             about: int | None = None, memory: int | None = None, payload: dict | None = None) -> int:  # fmt: skip
        return self.conn.execute(
            "INSERT INTO seeds(story_id, entity_id, kind, text, about_id, memory_id, weight,"
            " half_life_min, payload, story_time, message_id, run_id)"
            " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (self.story_id, who, kind, text, about, memory, round(weight, 3),
             HALF_LIFE.get(kind, SEED_HALF), json.dumps(payload) if payload else None,
             self.now if t is None else t, self.skip["id"], self.run),
        ).lastrowid  # fmt: skip

    def memory(self, who: int, detail: str, gist: str, importance: int, t: int, tags: list[str],
               emotion: str | None = None) -> int:  # fmt: skip
        """A covert memory only `who` holds: not in the transcript, so no message range."""
        mid = self.conn.execute(
            "INSERT INTO memories(story_id, kind, story_time, detail, gist, importance, emotion,"
            " is_true, covert, tags_text, run_id, message_id)"
            " VALUES(?, 'event', ?, ?, ?, ?, ?, 1, 1, ?, ?, ?)",
            (self.story_id, t, detail, gist, importance, emotion, " ".join(tags), self.run,
             self.skip["id"]),
        ).lastrowid  # fmt: skip
        self.conn.execute(
            "INSERT INTO memory_entities(memory_id, entity_id, role) VALUES(?, ?, 'actor')",
            (mid, who),
        )
        _tag(self.conn, mid, tags)
        self.know(who, mid, "witnessed", None, 1.0, t)
        return mid

    def know(self, who: int, memory: int, source: str, told_by, belief: float, t: int) -> None:
        self.conn.execute(
            "INSERT INTO knowledge(knower_id, memory_id, source, told_by_id, learned_story_time,"
            " fidelity, belief, run_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (who, memory, source, told_by, t, FIDELITY[source], belief, self.run),
        )

    def seeds_of(self, who: int) -> list[dict]:
        """`who`'s live seeds before this skip (this branch, or the user's own)."""
        where, args = db.anchor_filter(set(), {m["id"] for m in self.path})
        rows = self.conn.execute(
            f"SELECT * FROM seeds WHERE entity_id=? AND {where} ORDER BY id", [who, *args]
        )
        return [{**dict(r), "payload": json.loads(r["payload"] or "{}")} for r in rows]

    def contact(self, who: int) -> tuple[int | None, bool]:
        """When `who` last heard the user before the skip, and whether their own last word to
        the user was a question left unanswered (an open thread)."""
        before = self.path[:-1]  # the skip line itself is said after the time has passed
        heard = chat.heard_by(self.conn, before, who)
        last_user = next(
            (m for m in reversed(before) if m["speaker_id"] == self.persona and m["id"] in heard),
            None,
        )
        said = [m for m in before if m["role"] != "system" and m["id"] in heard]
        thread = bool(said) and said[-1]["speaker_id"] == who and said[-1]["text"].rstrip(
            " *\"”_").endswith("?")  # fmt: skip
        return (last_user["story_time"] if last_user else None), thread

    def one(self, who: int) -> dict:
        """B0 for one character. -> what the card needs to know about it."""
        conn, name = self.conn, self.names.get(who, "They")
        prof = inner.profile(conn, who)
        card = knobs.own(conn, who).get("mind")
        card = card if isinstance(card, dict) else {}
        state = None
        if self.affect:
            state = inner.current(conn, who, self.path, prof) or inner.fresh(prof, self.start)
            state = inner.tick(state, self.start, prof)
        mine = self.seeds_of(who)
        # offstage beats, from the card's own life
        lived = {s["payload"].get("event") for s in mine if s["kind"] == "news"}
        routine = [r.strip() for r in card.get("routine") or [] if isinstance(r, str) and r.strip()]
        n, done = beats(self.minutes), []
        for b in range(n):
            t = self.start + (b + 1) * self.minutes // (n + 1)
            got = roll(self.rng(who, "beat", b), prof, card.get("events"), lived)
            if got is None:
                continue
            lived.add(got["text"])
            done.append(got)
            said = f"{got['text']}, and {got['outcome']}"
            label, i = BEAT_FEEL[got["good"]]
            mid = self.memory(who, f"{name} {said}.", f"{name} {got['text']}.",
                              5 if got["good"] else 6, t, ["offscreen"], label)  # fmt: skip
            self.seed(who, "news", said, 0.6 if got["good"] else 0.7, t, memory=mid,
                      payload={"event": got["text"], "good": got["good"]})  # fmt: skip
            if state is not None:
                state = inner.feel(inner.tick(state, t, prof), label, i, said, prof)
        # time without the user, by attachment
        out: dict = {"missed": None, "worry": None}
        seen, thread = (None, False)
        if self.persona is not None and self.persona != who:
            seen, thread = self.contact(who)
        if seen is not None:
            gap = self.now - seen
            ab = absence(prof, gap, open_thread=thread)
            out["missed"] = missed(ab)
            if ab["worry"]:
                text = (
                    f"why {self.user} never answered"
                    if thread
                    else f"whether {self.user} is pulling away"
                )
                self.seed(who, "worry", text, ab["worry"], about=self.persona,
                          payload={"absence": True})  # fmt: skip
                out["worry"] = text
                if state is not None:
                    cause = f"no word from {self.user} in {span(gap).lower()}"
                    state = inner.feel(
                        inner.tick(state, self.now, prof), "anxious", ab["worry"], cause, prof
                    )
            else:
                self.rebound(who, mine, prof)
            dial = knobs.dial(conn, who, "relationships", "realistic")
            harsh = 0.0 if dial == "gentle" else bonds.HARSH.get(dial, 1.0)
            if self.bonded and harsh and ab["cool"]:
                cause = f"no word from {self.user} in {span(gap).lower()}"
                conn.executemany(
                    "INSERT INTO opinions(story_id, src_id, dst_id, dim, value, kind,"
                    " half_life_min, event, cause, story_time, message_id, run_id)"
                    " VALUES(?, ?, ?, ?, ?, 'decay', ?, 'neglect_gap', ?, ?, ?, ?)",
                    [(self.story_id, who, self.persona, dim, round(v * harsh, 2), NEGLECT_HALF,
                      cause, self.now, self.skip["id"], self.run) for dim, v in ab["cool"]],
                )  # fmt: skip
        if state is not None:
            with_rows = inner.regulate(inner.tick(state, self.now, prof), prof)
            conn.execute(
                "INSERT INTO mind_states(entity_id, story_time, state, message_id, run_id)"
                " VALUES(?, ?, ?, ?, ?)",
                (who, self.now, json.dumps(with_rows), self.skip["id"], self.run),
            )
        pick = routine[self.rng(who, "routine").randrange(len(routine))] if routine else None
        if done or pick or out["worry"]:  # "nothing much happened" is not worth remembering
            said = diary(self.minutes, done, [pick] if pick else [], out["worry"])
            self.memory(who, said, said, 3, self.now, ["offscreen", "diary"])
        return out

    def rebound(self, who: int, mine: list[dict], prof: dict) -> None:
        """Reassurance's rebound (note 11 §3): a relational worry that contact eased comes back
        once, weaker, at the next skip of some hours, for someone anxious by nature."""
        if prof["attachment"].get("anxiety", 0) < ATTACHED:
            return
        again = {s["payload"].get("rebound_of") for s in mine}
        for s in mine:
            if (s["kind"] == "worry" and s["payload"].get("absence") and s["id"] not in again
                    and not s["payload"].get("rebound_of") and self.now - s["story_time"] >= REBOUND_MIN
                    and eased(s, self.path)):  # fmt: skip
                self.seed(who, "worry", s["text"], s["weight"] * REBOUND, about=s["about_id"],
                          payload={"absence": True, "rebound_of": s["id"]})  # fmt: skip

    def gossip(self, cast: list[int]) -> None:
        """Two who spent the skip within reach of each other may pass a fact on (note 16 §6)."""
        scene_id = chat.scene_of(self.conn, self.story_id, self.path)
        here = {e["id"] for e in chat.present_entities(self.conn, scene_id, self.path)}
        together = [c for c in cast if c in here]
        live = db.live_runs(self.conn, self.story_id, self.skip["id"]) - {self.run}
        know, args = db.live_filter(live, "k.run_id")
        hidden: dict[
            int, list
        ] = {}  # per hearer: the keys (and memories) of secrets kept from them
        for owner in together:
            for sec in honesty.held(self.conn, owner, self.path):
                for b in together:
                    if b != owner and (sec["conceal_from"] == "all" or b in sec["conceal_from"]):
                        hidden.setdefault(b, []).append(sec["keys"])
                        if sec["memory_id"]:
                            hidden[b].append(sec["memory_id"])
        for a in together:
            gossip = inner.profile(self.conn, a)["social"].get("gossip", 0.3)
            gossip = min(1.0, max(0.0, gossip)) if isinstance(gossip, (int, float)) else 0.3
            rows = bonds.ledger(self.conn, a, self.path)
            for b in together:
                if a == b:
                    continue
                st = bonds.standing(rows, b, self.now)
                facts = self.conn.execute(
                    "SELECT m.id, m.detail, m.importance, m.covert FROM memories m"
                    " JOIN knowledge k ON k.memory_id=m.id AND k.knower_id=?"
                    f" WHERE m.story_id=? AND m.hidden=0 AND m.common=0 AND m.covert=0"
                    " AND m.importance>=?"
                    f" AND m.tags_text NOT LIKE '%diary%' AND m.story_time<=? AND {know}"
                    " AND k.belief>=0.5"
                    " AND NOT EXISTS(SELECT 1 FROM knowledge k3 WHERE k3.knower_id=? AND"
                    " k3.memory_id=m.id)"
                    " AND NOT EXISTS(SELECT 1 FROM memory_entities me WHERE me.memory_id=m.id"
                    " AND me.entity_id=?) ORDER BY m.importance DESC, m.id DESC LIMIT 10",
                    [a, self.story_id, GOSSIP_MIN, self.now, *args, b, b],
                ).fetchall()
                passed, kept = 0, hidden.get(b, [])
                for f in facts:
                    if passed >= GOSSIP_MAX:
                        break
                    if f["id"] in kept or any(honesty.leak(f["detail"], k) for k in kept if k):
                        continue  # a secret kept from b never reaches b by gossip
                    p = gossip_p(level(st["closeness"]), level(st["trust"]), gossip,
                                 f["importance"], bool(f["covert"]))  # fmt: skip
                    if self.rng(a, b, "gossip", f["id"]).random() < p:
                        self.know(b, f["id"], "told", a, TOLD_BELIEF, self.now)
                        self.version(a, b, f["id"], live)
                        passed += 1

    def reinforce(self, cast: list[int]) -> None:
        """Growth seeds later scenes bore out become rings; old unconfirmed ones pass (slice 8).
        A failure costs only that."""
        try:
            if not features.enabled(self.conn, "mind.growth"):
                return
            for who in cast:
                growth.reinforce(self.conn, who, self.path, self.now, self.skip["id"], self.run)
        except Exception as e:
            logging.getLogger(__name__).warning("rings not reinforced: %s", e)

    def version(self, teller: int, hearer: int, memory: int, live: set[int]) -> None:
        """What is passed on is the teller's own version of it (slice 6), if they hold one."""
        try:
            if features.enabled(self.conn, "mind.recall"):
                ids = {m["id"] for m in self.path}
                recollect.pass_on(self.conn, teller, hearer, memory, live, ids, self.now,
                                  run=self.run)  # fmt: skip
        except Exception as e:
            logging.getLogger(__name__).warning("version not passed on: %s", e)


def _tag(conn: sqlite3.Connection, memory_id: int, tags: list[str]) -> None:
    for name in tags:
        conn.execute("INSERT OR IGNORE INTO tags(name) VALUES(?)", (name,))
        conn.execute(
            "INSERT OR IGNORE INTO taggings(tag_id, obj, obj_id)"
            " SELECT id, 'memory', ? FROM tags WHERE name=?",
            (memory_id, name),
        )


def eased(seed: dict, path: list) -> bool:
    """A relational worry is eased once its owner has answered the user after it was written."""
    ids = [m["id"] for m in path]
    if seed["message_id"] not in ids:
        return False
    after = path[ids.index(seed["message_id"]) + 1 :]
    return any(m["role"] == "assistant" and m["speaker_id"] == seed["entity_id"] for m in after)


def _deep(conn, story_id: int, upto: list, calls: list[int]) -> dict[str, str]:
    """Who of those getting the diary call also reflects on this skip, and why (slice 8). Code,
    zero calls; a failure costs only the deep pass."""
    try:
        if not calls or not features.enabled(conn, "mind.growth"):
            return {}
        level = knobs.setting(conn, "mind.level", "standard")
        why = {str(c): growth.trigger(conn, story_id, c, upto, level) for c in calls}
        return {c: r for c, r in why.items() if r}
    except Exception as e:
        logging.getLogger(__name__).warning("deep pass not decided: %s", e)
        return {}


def at_skip(conn: sqlite3.Connection, story_id: int, path: list) -> int | None:
    """B0 for the skip this path has just been through, once: one between run, and on it each
    tracked character's settled mood, time-apart ledger rows, worries, offstage beats, templated
    diary, and gossip between those who were together. -> the run id, or None when there is no
    new skip (or the feature, or the dial, is off)."""
    if not path or not features.enabled(conn, "mind.offscreen"):
        return None
    skip = _skip(path)
    if skip is None or run_of(conn, story_id, skip["id"]) is not None:
        return None
    upto = path[: [m["id"] for m in path].index(skip["id"]) + 1]
    cast = tracked(conn, story_id, upto)
    if not cast:
        return None
    lite = knobs.setting(conn, "mind.level", "standard") == "lite"
    with conn:
        run = conn.execute(
            "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger, status,"
            " role, model, attempts, started_at, finished_at)"
            " VALUES(?, 0, ?, ?, 'ok', 'code', '', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (story_id, skip["id"], TRIGGER),
        ).lastrowid
        tick = _Tick(conn, story_id, upto, dict(skip), run)
        people = {str(c): tick.one(c) for c in cast}
        tick.gossip(cast)
        calls = [] if lite else cast[:CALLS]
        raw = {
            "tracked": cast,
            "b1": {str(c): "pending" if c in calls else "lite" if lite else "code" for c in cast},
            "people": people,
        }
        if deep := _deep(conn, story_id, upto, calls):
            raw["deep"] = deep
        tick.reinforce(cast)
        conn.execute("UPDATE extraction_runs SET raw=? WHERE id=?", (json.dumps(raw), run))
    return run


# --- the diary call (B1): one per tracked character, in the background -------------------------

PROMPT = """\
You write what went on inside {name} while time passed off-screen in an ongoing story, for the \
app that keeps the character's mind. What happened to {name} is given and fixed: never \
contradict it, and never invent new people, places or big events; small everyday details are \
fine. Write in {name}'s own voice, first person. Reply with JSON only.
- diary: {name}'s private diary of the time that passed: two or three sentences, first person \
("I"), about {name}'s own days, addressed to no one.
- worth_telling: zero to two pieces of news from {name}'s own days that {name} would bring up \
with {user}: something that happened to {name} or that {name} did, told as a fact in first \
person, at most 20 words each. Never a message or a plea to \
{user}, never about {user}. Empty when nothing happened.
- seeds: one to three things on {name}'s mind now. kind: worry (something that might go wrong), \
rumination (something past they keep replaying), plan (something they mean to do), unfinished \
(something left open), intrusive (a thought that keeps coming back), idea (something new they \
thought of). text: at most 20 words. weight: 1 a little, 2 clearly, 3 a lot.
- preoccupation: the one thing most on their mind, at most 15 words."""
MEMORIES = 5  # of her own memories, the ones the call sees
HEARD = 6  # the last lines she heard before the skip
TELL_WEIGHT, PRE_WEIGHT = 0.5, 0.5  # ponytail: how much the call's news and preoccupation weigh


def _raw(run: sqlite3.Row) -> dict:
    raw = json.loads(run["raw"] or "{}")
    raw.setdefault("b1", {})
    raw.setdefault("people", {})
    return raw


def todo(conn: sqlite3.Connection, story_id: int) -> list[tuple[int, int]]:
    """(run, character) pairs still owed their diary call: the latest skip on the active branch,
    standard and premium only."""
    if knobs.setting(conn, "mind.level", "standard") == "lite":
        return []
    run = job(conn, story_id, chat.active_path(conn, story_id))
    if run is None:
        return []
    return [(run["id"], int(c)) for c, s in _raw(run)["b1"].items() if s == "pending"]


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z']+", text.lower()) if len(w) > 3}


def _same(a: str, b: str) -> bool:
    """Two news lines about the same thing (most of the shorter one's words are in the other)."""
    wa, wb = _words(a), _words(b)
    return bool(wa and wb) and len(wa & wb) >= 0.5 * min(len(wa), len(wb))


def _ask(conn, story_id: int, who: int, run: sqlite3.Row, skip: sqlite3.Row, path: list,
         wants: dict[str, dict] | None = None, work: dict | None = None) -> list:  # fmt: skip
    """The call's input: only this character's own card, state and memories (never a scene
    summary, which an all-seeing reader wrote)."""
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)))
    story = conn.execute("SELECT persona_entity_id FROM stories WHERE id=?", (story_id,)).fetchone()
    name, user = names.get(who, "them"), names.get(story["persona_entity_id"]) or "the others"
    me = conn.execute("SELECT description FROM entities WHERE id=?", (who,)).fetchone()
    mine = conn.execute(
        "SELECT kind, text, payload FROM seeds WHERE run_id=? AND entity_id=? ORDER BY id",
        (run["id"], who),
    ).fetchall()
    happened = [s["text"] for s in mine if s["kind"] == "news"]
    minds = [s["text"] for s in mine if s["kind"] != "news"]
    prof = inner.profile(conn, who)
    state = inner.current(conn, who, path, prof)
    mood = inner.public(state, prof) if state else None
    ours = {r[0] for r in conn.execute("SELECT id FROM memories WHERE run_id=?", (run["id"],))}
    known = [
        m
        for m in retrieve.inspect(conn, story_id, who, now=skip["story_time"])
        if m["tier"] != "forgotten" and m["memory_id"] not in ours and not m["hidden"]
    ]
    known.sort(key=lambda m: (-m["importance"], -m["story_time"]))
    remembered = [m["detail"] if m["tier"] == "sharp" else m["gist"] for m in known[:MEMORIES]]
    heard = chat.heard_by(conn, path[:-1], who)
    lines = [
        f"{names.get(m['speaker_id'], 'Narration')}: {m['text'][-300:]}"
        for m in [m for m in path[:-1] if m["id"] in heard and not m["hidden"]][-HEARD:]
    ]
    body = [
        f"You are {name}. {(me['description'] if me else '')[:600]}".strip(),
        f"Time that just passed off-screen: {span(skip['skip_minutes']).lower()}, away from {user}.",
        "What happened to you meanwhile:\n"
        + ("\n".join(f"- {h}" for h in happened) or "- nothing out of the ordinary"),
    ]
    if minds:
        body.append("Already on your mind:\n" + "\n".join(f"- {t}" for t in minds))
    if mood:
        body.append(
            f"How you feel now: {mood['feels']}" + (f" ({mood['why']})" if mood["why"] else "")
        )
    if remembered:
        body.append("What you remember:\n" + "\n".join(f"- {r}" for r in remembered))
    if lines:
        body.append("The last things you heard before the time passed:\n" + "\n".join(lines))
    system = PROMPT.format(name=name, user=user)
    if wants:  # slice 7: what she is after, and the one change the time may have made
        body.append(_wants(conn, who, path, wants))
        system += GOAL.format(name=name)
    if work:  # slice 8: looking back, on her own memories only, each with a handle
        body.append(
            "Your memories, for looking back (handle: memory):\n"
            + "\n".join(f"- {h}: {m['text']}" for h, m in work["memories"].items())
        )
        if work["who"]:
            body.append(
                "People (handle: name):\n"
                + "\n".join(f"- {h}: {n}" for h, n in work["who"].items())
            )
        system += DEEP.format(name=name, traits=", ".join(growth.TRAITS))
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(body)},
    ]


GOAL = """
- goal: if the time that passed moved one of {name}'s goals (listed with their handles), that \
one, else null. goal: its handle; change: progressed ({name} got closer), stalled (nothing moved, \
but a new plan), done ({name} got it), dropped ({name} gave up on it), revived ({name} means to \
try again); tactic: how {name} means to go about it now, at most 12 words. Only what fits what \
happened."""


DEEP = """
- deep: {name} looks back over a long stretch of the story. Use ONLY the memories listed with \
handles (M...) and the people listed with handles (P...); cite in `sources` the handles each item \
rests on. Never add a name, place or number that is not in those memories.
  - relationship: the one or two people {name} feels most about (empty only if her memories \
hold no one): about (their handle), line (how {name} has come to see them, first person, at most \
25 words).
  - self: how {name} sees herself now, first person, at most six sentences (null only if her \
memories say nothing about her).
  - rings: zero to two ways {name} has really changed, each resting on at least three memories \
from at least two different times: kind (stance: a position she now holds; habit: something she \
now does; skill: something she learned to do; scar: something that hurt and still does; belief: \
something she now believes), claim (at most 15 words, like "learned to ask for help"), trait (the \
one way it moves her, if any: {traits}; or none). Empty when nothing really changed."""


def _wants(conn, who: int, path: list, wants: dict[str, dict]) -> str:
    """Her goals for the diary call, with handles; what she needs and fears, as context only."""
    rows = [f"- {h}: {g['text']}" + (" (you let it drop lately)" if g["status"] == "dormant"
            else "") for h, g in wants.items()]  # fmt: skip
    deep = {g["key"]: g["text"] for g in goals.live(conn, who, path) if g["key"] in goals.UNPURSUED}
    out = "What you are after:\n" + "\n".join(rows)
    if deep.get("need"):
        out += f"\nDeep down, without quite knowing it, you need {deep['need']}."
    if deep.get("fear"):
        out += f"\nYou are afraid of {deep['fear']}."
    return out


def _mark(conn: sqlite3.Connection, run_id: int, who: int, status: str) -> None:
    row = conn.execute("SELECT * FROM extraction_runs WHERE id=?", (run_id,)).fetchone()
    if row is None:
        return
    raw = _raw(row)
    raw["b1"][str(who)] = status
    with conn:
        conn.execute("UPDATE extraction_runs SET raw=? WHERE id=?", (json.dumps(raw), run_id))


def _write(conn, story_id: int, run: sqlite3.Row, skip: sqlite3.Row, who: int, got: dict,
           wants: dict[str, dict] | None = None, work: dict | None = None) -> None:  # fmt: skip
    """The call's words, on the run: the diary in place of the template, then the news she did
    not have yet, her seeds, her preoccupation, and the one goal the time moved."""
    tick = _Tick(conn, story_id, chat.path_to(conn, skip["id"]), dict(skip), run["id"])
    old = conn.execute(
        "SELECT m.id FROM memories m JOIN memory_entities me ON me.memory_id=m.id"
        " WHERE m.run_id=? AND me.entity_id=? AND m.tags_text LIKE '%diary%'",
        (run["id"], who),
    ).fetchall()
    for (mid,) in old:
        conn.execute("DELETE FROM taggings WHERE obj='memory' AND obj_id=?", (mid,))
        conn.execute("DELETE FROM memories WHERE id=?", (mid,))
    tick.memory(who, got["diary"], got["diary"], 3, tick.now, ["offscreen", "diary"])
    news = [
        r[0]
        for r in conn.execute(
            "SELECT text FROM seeds WHERE run_id=? AND entity_id=? AND kind='news'",
            (run["id"], who),
        )
    ]
    for said in got["worth_telling"]:
        if not any(_same(said, n) for n in news):
            tick.seed(who, "news", said, TELL_WEIGHT, payload={"from": "diary"})
            news.append(said)
    for s in got["seeds"]:
        tick.seed(who, s["kind"], s["text"], 0.3 * s["weight"])
    if got["preoccupation"]:
        tick.seed(who, "preoccupation", got["preoccupation"], PRE_WEIGHT)
    if (moved := got.get("goal")) and (g := (wants or {}).get(moved["goal"])):  # one, at most
        goals.change(conn, g, moved["change"], moved["tactic"] or None, skip["id"], run["id"],
                     tick.now)  # fmt: skip
    if work:  # slice 8: what passes the gate becomes her reflections, the rest a warning
        warn = growth.take(conn, story_id, who, got.get("deep"), work, tick.path, skip["id"],
                           run["id"], tick.now)  # fmt: skip
        _warn(conn, run["id"], who, warn, got.get("deep"))


def _warn(conn, run_id: int, who: int, warnings: list[str], said=None) -> None:
    """Why her deep pass dropped something, and what it said (Backstage can show both), on the
    run (inside a transaction)."""
    row = conn.execute("SELECT raw FROM extraction_runs WHERE id=?", (run_id,)).fetchone()
    if row is None:
        return
    raw = json.loads(row[0] or "{}")
    raw.setdefault("deep_warnings", {})[str(who)] = warnings
    if said is not None:
        raw.setdefault("deep_said", {})[str(who)] = said
    conn.execute("UPDATE extraction_runs SET raw=? WHERE id=?", (json.dumps(raw), run_id))


def _work(conn, story_id: int, who: int, run: sqlite3.Row, skip: sqlite3.Row) -> dict | None:
    """Her deep pass's working set when this skip calls for one, else None; a failure costs
    only the deep pass."""
    if not _raw(run).get("deep", {}).get(str(who)):
        return None
    try:
        if not features.enabled(conn, "mind.growth"):
            return None
        ours = {r[0] for r in conn.execute("SELECT id FROM memories WHERE run_id=?", (run["id"],))}
        known = [
            m
            for m in retrieve.inspect(conn, story_id, who, now=skip["story_time"])
            if m["memory_id"] not in ours
        ]
        work = growth.working(conn, story_id, who, skip["story_time"], known)
        if not work["memories"]:  # nothing read into memory yet: nothing to look back on
            with conn:
                _warn(
                    conn,
                    run["id"],
                    who,
                    ["No reflection: she has no memories to look back on yet."],
                )
            return None
        return work
    except Exception as e:
        logging.getLogger(__name__).warning("deep pass skipped for %s: %s", who, e)
        with contextlib.suppress(Exception), conn:
            _warn(conn, run["id"], who, ["The reflection was skipped: something went wrong."])
        return None


def _goals_of(conn, who: int, path: list) -> dict[str, dict]:
    """Her open goals for the diary call (slice 7), or none; a failure costs only them."""
    try:
        return goals.handles(conn, who, path) if features.enabled(conn, "mind.goals") else {}
    except Exception as e:
        logging.getLogger(__name__).warning("goals not given to the diary call: %s", e)
        return {}


async def think(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    run_id: int,
    who: int,
    get_key: Callable[[str], str | None] = roles.get_key,
    ep=None,
) -> bool:
    """B1 for one character: one `utility` call, validated, written on the run. -> whether it
    wrote anything. A failure costs only the words: the tick's rows stay (`b1` = "failed", never
    retried by itself, since the call may be paid). A cancel (a reply started) leaves it owed."""
    run = conn.execute("SELECT * FROM extraction_runs WHERE id=?", (run_id,)).fetchone()
    if run is None or run["trigger"] != TRIGGER or _raw(run)["b1"].get(str(who)) != "pending":
        return False
    active = {m["id"] for m in chat.active_path(conn, story_id)}
    if run["to_message_id"] not in active:  # another branch now: it waits for its own
        return False
    ep = ep or roles.resolve(conn, "utility", story_id, get_key)
    if ep is None:
        return False
    try:
        skip = chat.get_message(conn, run["to_message_id"])
        path = chat.path_to(conn, skip["id"])
        wants = _goals_of(conn, who, path)
        work = _work(conn, story_id, who, run, skip)
        ask = _ask(conn, story_id, who, run, skip, path, wants, work)
        got = await llm.complete_json(
            ep,
            ask,
            schema(list(wants), work),
            lambda d: read(d, list(wants), work is not None),
            name="between",
        )
        if conn.execute("SELECT 1 FROM extraction_runs WHERE id=?", (run_id,)).fetchone() is None:
            return False  # the skip was undone while the model was busy
        with conn:
            _write(conn, story_id, run, skip, who, got, wants, work)
    except Exception as e:  # never the turn's undoing, never retried unasked
        logging.getLogger(__name__).warning("diary call failed for %s: %s", who, e)
        _mark(conn, run_id, who, "failed")
        if _raw(run).get("deep", {}).get(str(who)):
            with contextlib.suppress(Exception), conn:
                _warn(conn, run_id, who, ["The reflection did not run: the call failed."])
        return False
    _mark(conn, run_id, who, "ok")
    return True


# --- one thing reaches the reply (note 22 §4 row 5) ---------------------------------------------

SURFACE = 2  # ponytail: replies one seed rides in before it is let go
REENTRY_LINES = 4  # ponytail: a first reply this many lines after the skip still greets
FLOOR = 0.15  # ponytail: a seed lighter than this is no longer on her mind
MAX_WORRIES = 2  # note 11 §3: at most two worries count at once
WORRIES = ("worry", "rumination")


def open_seeds(conn: sqlite3.Connection, who: int, path: list) -> list[dict]:
    """What is on `who`'s mind at the end of `path`, strongest first: live seeds, weighed now,
    without the closed ones, the faded ones, a relational worry contact has eased, and any
    worry past the second."""
    if not path:
        return []
    now = path[-1]["story_time"]
    where, args = db.anchor_filter(set(), {m["id"] for m in path})
    rows = [
        {**dict(r), "payload": json.loads(r["payload"] or "{}")}
        for r in conn.execute(
            f"SELECT * FROM seeds WHERE entity_id=? AND story_time<=? AND {where} ORDER BY id",
            [who, now, *args],
        )
    ]
    closed = {r["closes_id"] for r in rows if r["closes_id"] is not None}
    out = []
    for r in rows:
        if r["closes_id"] is not None or r["id"] in closed:
            continue
        if r["payload"].get("absence") and eased(r, path):
            continue
        if (w := weight(r, now)) >= FLOOR:
            out.append({**r, "now": round(w, 3)})
    out.sort(key=lambda r: -r["now"])
    ranked = sorted(
        (r for r in out if r["kind"] in WORRIES), key=lambda r: not r["payload"].get("absence")
    )
    worries = [r["id"] for r in ranked][:MAX_WORRIES]  # the worry about the user first
    return [r for r in out if r["kind"] not in WORRIES or r["id"] in worries]


def _offered(path: list, who: int) -> dict[int, int]:
    """How many of `who`'s replies each seed has already ridden in."""
    seen: dict[int, int] = {}
    for m in path:
        if m["role"] == "assistant" and m["speaker_id"] == who and m["gen"]:
            got = json.loads(m["gen"]).get("onmind") or {}
            for key in ("seed", "news"):
                if got.get(key) is not None:
                    seen[got[key]] = seen.get(got[key], 0) + (SURFACE if key == "news" else 1)
    return seen


def _reentry(skip: dict, missed: str | None, worry: str | None, news: str | None, user: str) -> str:
    """The first reply after time away: how the time landed, one thing to tell, a question back.
    Decisions, so they go in [Directive]; words only; no guilt (note 17 §4)."""
    gap = span(skip["skip_minutes"]).lower()
    out = []
    if missed == "worried":
        out.append(
            f"You spent {gap} without a word from {user}"
            + (f", wondering {worry}" if worry else "")
            + f". Now that {user} is here, let the relief show and look for a little reassurance;"
            " no guilt, no accusations."
        )
    elif missed == "cooler":
        out.append(
            f"It has been {gap} since you saw {user} and you have cooled a little: keep some"
            f" distance at first, and warm up only if {user} keeps it easy."
        )
    elif missed == "glad":
        out.append(f"It has been {gap} since you saw {user}, and you are glad to see {user} again.")
    if news:
        out.append(f"Since you last saw {user}: {news}. Mention it if it fits.")
    if news or missed == "glad":
        out.append(f"Ask what {user} has been up to.")
    return " ".join(out)


def on_mind(
    conn: sqlite3.Connection, story_id: int, who: int, path: list, user: str | None
) -> dict | None:
    """The one thing about her time away that reaches this reply. On her first reply after a
    skip: the re-entry decision for [Directive]. Otherwise: her strongest seed as "On your mind"
    for the mind block, on at most two replies. -> {"row", "directive", "record"} or None."""
    seeds = open_seeds(conn, who, path)
    offered = _offered(path, who)
    run = job(conn, story_id, path)
    if run is not None and user:
        raw, ids = _raw(run), [m["id"] for m in path]
        after = path[ids.index(run["to_message_id"]) + 1 :]
        mine = raw["people"].get(str(who))
        if (
            mine is not None
            and len(after) <= REENTRY_LINES
            and not any(m["role"] == "assistant" and m["speaker_id"] == who for m in after)
        ):
            news = min(  # what really happened (the tick's events) before the diary's words
                (s for s in seeds if s["kind"] == "news" and s["run_id"] == run["id"]
                 and s["id"] not in offered),
                key=lambda s: (not s["payload"].get("event"), -s["now"]),
                default=None,
            )  # fmt: skip
            worry = next(
                (s for s in seeds if s["payload"].get("absence") and s["run_id"] == run["id"]),
                None,
            )
            skip = chat.get_message(conn, run["to_message_id"])
            said = _reentry(dict(skip), mine.get("missed"), mine.get("worry"),
                            news and news["text"], user)  # fmt: skip
            if said:
                top = worry if mine.get("missed") == "worried" else news
                return {
                    "row": "",
                    "directive": said,
                    "record": {"seed": worry and worry["id"], "kind": top and top["kind"],
                               "text": top and top["text"], "news": news and news["id"],
                               "reentry": True},
                }  # fmt: skip
    pick = next(  # a correction is not a thought to share: the repair decides it (slice 6)
        (s for s in seeds if offered.get(s["id"], 0) < SURFACE and not s["payload"].get("absence")
         and s["kind"] != "correction"),
        None,
    )  # fmt: skip
    if pick is None:
        return None
    them = user or "them"
    what = {"news": f"{pick['text']} (something to tell {them})",
            "worry": f"{pick['text']}, and it worries you"}.get(pick["kind"], pick["text"])  # fmt: skip
    row = (
        f"On your mind: {what}. Bring it up only if there is a natural opening; drop it if"
        f" {them} dodges."
    )
    return {
        "row": row,
        "directive": "",
        "record": {"seed": pick["id"], "kind": pick["kind"], "text": pick["text"], "news": None,
                   "reentry": False},
    }  # fmt: skip


# --- what the app shows: the "while you were away" card, and Peek's seeds -----------------------


def _strength(w: float) -> str:
    return "strong" if w >= 0.6 else "some" if w >= 0.3 else "faint"


def public(conn: sqlite3.Connection, who: int, path: list, names: dict, epoch: int) -> list[dict]:
    """Peek's view of what is on their mind (spec §8.3), strongest first."""
    return [
        {"id": s["id"], "kind": s["kind"], "text": s["text"], "strength": _strength(s["now"]),
         "about": names.get(s["about_id"]), "since": clock.label(s["story_time"], epoch),
         "message_id": s["message_id"]}
        for s in open_seeds(conn, who, path)
    ]  # fmt: skip


def away(conn: sqlite3.Connection, story: dict) -> dict:
    """The latest skip's "while you were away" card on the active branch (spec §8.3), or
    {"away": None}. Pulled by the app, never pushed."""
    if not features.enabled(conn, "mind.offscreen"):
        return {"away": None}
    path = chat.active_path(conn, story["id"])
    run = job(conn, story["id"], path)
    if run is None:
        return {"away": None}
    raw, skip = _raw(run), chat.get_message(conn, run["to_message_id"])
    epoch, moments = story["epoch_offset_min"], json.loads(story["overrides"]).get("moments", [])
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story["id"],)))
    people = []
    never = knobs.setting(conn, "mind.level", "standard") == "lite" or (
        roles.resolve(conn, "utility", story["id"], roles.get_key) is None
    )  # the calls owed will never run: the card must not wait for them
    for who in raw.get("tracked", []):
        status, mine = raw["b1"].get(str(who)), raw["people"].get(str(who), {})
        if status == "pending" and never:
            status = "code"
        news = [
            r[0]
            for r in conn.execute(
                "SELECT text FROM seeds WHERE run_id=? AND entity_id=? AND kind='news'"
                " ORDER BY weight DESC, id LIMIT 2",
                (run["id"], who),
            )
        ]
        diary = conn.execute(
            "SELECT m.detail FROM memories m JOIN memory_entities me ON me.memory_id=m.id"
            " WHERE m.run_id=? AND me.entity_id=? AND m.tags_text LIKE '%diary%'",
            (run["id"], who),
        ).fetchone()
        state = conn.execute(
            "SELECT state FROM mind_states WHERE run_id=? AND entity_id=?", (run["id"], who)
        ).fetchone()
        people.append(
            {"id": who, "name": names.get(who), "done": status != "pending",
             "from": "diary" if status == "ok" else "template",
             "news": news, "worry": mine.get("worry"), "missed_you": mine.get("missed"),
             "diary": diary[0] if diary else None,
             "mood": state and inner.public(json.loads(state[0]), inner.profile(conn, who))}
        )  # fmt: skip
    start = skip["story_time"] - skip["skip_minutes"]
    return {
        "away": {
            "message_id": skip["id"],
            "since": span(skip["skip_minutes"]),
            "from_date": clock.date(start, epoch, moments),
            "date": clock.date(skip["story_time"], epoch, moments),
            "done": all(p["done"] for p in people),
            "level": knobs.setting(conn, "mind.level", "standard"),
            "people": people,
        }
    }
