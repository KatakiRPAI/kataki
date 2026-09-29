"""How a character stands with each person, kept by code (docs/specs/2026-09-29-minds.md, slice 2).

A relationship is a ledger, not a number (note 16 §5; note 22 §1 `opinions`): each thing someone
did leaves rows (what, which way, how much, why, when), and how the character feels about them now
is those rows faded to the present. Most fade on story time. A grudge (an insult, a broken
promise, a crossed line) is sticky: it holds at no less than 40% of itself until it is forgiven,
and forgiving turns it into slow decay, so trust comes back slower than it went. A hollow apology
forgives nothing. The prompt gets words, never numbers. Zero model calls.

ponytail: every constant here is an estimate from the research (note 16 §9.3); tune them on the
probes (evals/probes.py), not by feel.
"""

import re
import sqlite3

from kataki import chat, clock, db, inner, knobs

DIMS = ("closeness", "trust", "respect", "familiarity")  # the dimensions events move so far
SHOWN = ("trust", "closeness", "respect")  # the ones worth a word
# note 22's EVENT list, less the five that code detects in later slices (neglect_gap,
# favouritism_shown, lie_discovered, disclosure_unreciprocated, secret_betrayed).
# event: ({dimension: change at intensity 1}, kind, half-life in story days)
EVENTS: dict[str, tuple[dict[str, float], str, int]] = {
    "kindness": ({"closeness": 2, "trust": 1}, "decay", 14),
    "support_given": ({"closeness": 3, "trust": 2}, "decay", 21),
    "support_ignored": ({"closeness": -2, "trust": -2}, "decay", 7),
    "vulnerable_disclosure": ({"closeness": 3, "familiarity": 2}, "decay", 30),
    "disclosure_reciprocated": ({"closeness": 3, "trust": 2}, "decay", 30),
    "shared_joy": ({"closeness": 2}, "decay", 14),
    "compliment": ({"closeness": 1, "respect": 1}, "decay", 7),
    "teasing_ok": ({"closeness": 1}, "decay", 7),
    "teasing_hurt": ({"closeness": -2, "trust": -1}, "decay", 7),
    "insult": ({"closeness": -3, "trust": -2, "respect": -3}, "sticky", 30),
    "dismissal": ({"closeness": -2, "respect": -1}, "decay", 7),
    "promise_kept": ({"trust": 3}, "decay", 30),
    "promise_broken": ({"trust": -8, "closeness": -3}, "sticky", 30),
    "secret_kept": ({"trust": 3}, "decay", 30),
    "boundary_crossed": ({"trust": -6, "closeness": -4}, "sticky", 30),
    "apology_sincere": ({"closeness": 1}, "decay", 7),  # and forgives every open grudge
    "apology_hollow": ({"respect": -1}, "decay", 3),
    "amends_made": ({"trust": 2}, "decay", 30),  # and forgives every open grudge
    "help_refused": ({"closeness": -2, "trust": -1}, "decay", 7),
}
REPAIR = frozenset({"apology_sincere", "amends_made"})
STICKY_FLOOR = 0.4  # ponytail: an unforgiven grudge never fades below this share of itself
REPAIR_DAYS = 30  # ponytail: forgiven, it halves in this many story days / (0.5 + forgiveness)
SCENE_CAP = {"closeness": 8, "trust": 10}  # ponytail: the most one scene can raise either
START_CLOSENESS = 20  # ponytail: where a pair starts, for diminishing returns only
HARSH = {"gentle": 0.5, "realistic": 1.0, "harsh": 1.5}  # Realism › Relationships, on losses
FADED = 1.0  # a cause weaker than this is no longer worth naming


def _fade(minutes: int, half_life: int | None) -> float:
    return 0.5 ** (max(minutes, 0) / max(half_life or 1, 1))


def strength(row: dict, fix: dict | None, now: int) -> float:
    """How much of a row is left at `now`, 0-1. A forgiven grudge fades from what it was when it
    was forgiven, at the forgiving row's pace."""
    if row["kind"] == "permanent":
        return 1.0
    if row["kind"] == "decay":
        return _fade(now - row["story_time"], row["half_life_min"])
    if fix is None:
        return max(STICKY_FLOOR, _fade(now - row["story_time"], row["half_life_min"]))
    held = max(STICKY_FLOOR, _fade(fix["story_time"] - row["story_time"], row["half_life_min"]))
    return held * _fade(now - fix["story_time"], fix["half_life_min"])


def _fixes(rows: list[dict]) -> dict[int, dict]:
    """Which rows have been forgiven, by which row."""
    return {r["resolves_id"]: r for r in rows if r["resolves_id"] is not None}


def standing(rows: list[dict], dst: int, now: int) -> dict:
    """Where the ledger's owner stands with `dst` at `now`: how far each dimension has moved
    since they started, the strongest causes, the open grudge (the latest) and the latest
    forgiven one."""
    fixes = _fixes(rows)
    moved = dict.fromkeys(DIMS, 0.0)
    causes: dict[tuple, dict] = {}
    grudge = forgiven = None
    for r in rows:
        if r["dst_id"] != dst or r["resolves_id"] is not None:
            continue
        fix = fixes.get(r["id"]) if r["id"] is not None else None
        left = strength(r, fix, now)
        moved[r["dim"]] += r["value"] * left
        key = (r["event"], r["cause"], r["story_time"])
        c = causes.setdefault(key, {"event": r["event"], "cause": r["cause"],
                                    "t": r["story_time"], "kind": r["kind"],
                                    "forgiven": fix is not None, "weight": 0.0})  # fmt: skip
        c["weight"] += abs(r["value"] * left)
        if r["kind"] == "sticky":
            if fix is None:
                grudge = c
            else:
                forgiven = c
    top = sorted((c for c in causes.values() if c["weight"] >= FADED), key=lambda c: -c["weight"])
    return {
        **{d: round(v, 1) for d, v in moved.items()},
        "causes": top[:2],
        "grudge": grudge,
        "forgiven": forgiven,
    }


def _row(dst, dim, value, kind, half_life, event, cause, resolves, now, scene_id) -> dict:
    return {"id": None, "dst_id": dst, "dim": dim, "value": value, "kind": kind,
            "half_life_min": half_life, "event": event, "cause": cause, "resolves_id": resolves,
            "story_time": now, "scene_id": scene_id}  # fmt: skip


def apply(
    rows: list[dict],
    dst: int,
    event: str,
    intensity: int,
    cause: str,
    now: int,
    scene_id: int | None,
    prof: dict,
    dial: str = "realistic",
) -> list[dict]:
    """The rows one event adds to a ledger that already holds `rows` (saved or not), by the
    owner's temperament: the anxious take losses harder, the trusting gain trust faster, closeness
    comes slower the closer they are, one scene can only raise it so far, and a repair forgives
    every open grudge toward `dst` (a forgiving owner forgives faster)."""
    deltas, kind, half_days = EVENTS[event]
    social = {k: min(1.0, max(0.0, v)) for k, v in prof["social"].items()}
    before = standing(rows, dst, now)
    new = []
    for dim, per in deltas.items():
        value = per * intensity
        if value < 0:
            value *= (1 + 0.5 * prof["attachment"]["anxiety"]) * HARSH.get(dial, 1.0)
        else:
            if dim == "trust":
                value *= 0.5 + social["trust_propensity"]
            if dim == "closeness":
                value *= max(0.0, 1 - (START_CLOSENESS + before["closeness"]) / 100) ** 0.5
            if dim in SCENE_CAP:
                spent = sum(
                    r["value"]
                    for r in rows
                    if r["dst_id"] == dst and r["dim"] == dim and r["value"] > 0
                    and r["scene_id"] == scene_id
                )  # fmt: skip
                value = min(value, max(0.0, SCENE_CAP[dim] - spent))
        if abs(value) < 0.05:
            continue
        row_kind = "permanent" if dim == "familiarity" else kind
        new.append(_row(dst, dim, round(value, 2), row_kind, half_days * clock.DAY, event, cause,
                        None, now, scene_id))  # fmt: skip
    if event in REPAIR:
        half_life = round(REPAIR_DAYS * clock.DAY / (0.5 + social["forgiveness"]))
        fixes = _fixes(rows)
        for g in rows:
            if (g["dst_id"] == dst and g["kind"] == "sticky" and g["id"] is not None
                    and g["id"] not in fixes):  # fmt: skip
                new.append(_row(dst, g["dim"], 0.0, "decay", half_life, event, cause, g["id"],
                                now, scene_id))  # fmt: skip
    return new


# what a line did, read by rules: the lite level, and the fallback when the side call can't run
BROKEN = re.compile(
    r"\b(i forgot (about (us|you|tonight|it)|to (come|call|meet|write))"
    r"|i didn'?t (come|show up|make it|call)(?! (here|up|out|back|in|it up)\b)"
    r"|couldn'?t make it|broke (my|the|a|our) promise|stood you up)\b",
    re.IGNORECASE,
)
OWNED = re.compile(  # an apology that owns the wrong
    r"\b(i was wrong|my fault|i shouldn'?t have|that was (wrong|unfair|cruel)|i broke"
    r"|i let you down|i'?ll make it up|i hurt you)\b",
    re.IGNORECASE,
)
RULED = {  # inner.sense's events, as the ledger names them
    "insult": "insult",
    "threat": "boundary_crossed",
    "praise": "compliment",
    "good_news": "shared_joy",
    "bad_news": "vulnerable_disclosure",
}


def rule_events(text: str, hit: tuple[str, float] | None) -> list[tuple[str, int]]:
    """What a line did to the one it was aimed at, by rules: [(event, intensity 1-3)]. An apology
    is sincere only when it owns the wrong, and one that names the wrong is not that wrong again.
    ponytail: keywords only (inner.sense's list plus two of our own); the side call reads the
    rest on the standard level."""
    if hit and hit[0] == "apology":
        return [("apology_sincere" if OWNED.search(text) else "apology_hollow", 2)]
    out = [("promise_broken", 2)] if BROKEN.search(text) else []
    if hit:
        out.append((RULED[hit[0]], 2 if hit[1] >= 0.9 else 1))
    return out


def ledger(conn: sqlite3.Connection, src: int, path: list) -> list[dict]:
    """Every live row of `src`'s ledger, oldest first: written on this branch (or by the user),
    each with the scene it was written in."""
    scene = {m["id"]: m["scene_id"] for m in path}
    where, args = db.anchor_filter(set(), set(scene))
    rows = conn.execute(
        f"SELECT * FROM opinions WHERE src_id=? AND {where} ORDER BY story_time, id", [src, *args]
    )
    return [{**dict(r), "scene_id": scene.get(r["message_id"])} for r in rows]


def react(conn: sqlite3.Connection, story_id: int, path: list, model=None) -> dict[int, list]:
    """What the latest user line adds to the ledger of each character it was aimed at, not yet
    saved: {character id: [rows]}. Like inner.react, the same path always gives the same rows,
    so a new take never counts it twice."""
    if not path or path[-1]["role"] != "user" or path[-1]["speaker_id"] is None:
        return {}
    last, now = path[-1], path[-1]["story_time"]
    events = rule_events(last["text"], inner.sense(last["text"], model))
    if not events:
        return {}
    scene_id = chat.scene_of(conn, story_id, path)
    cast = [
        e["id"]
        for e in chat.present_entities(conn, scene_id, path)
        if e["is_ai"] and e["kind"] == "character"
    ]
    heard = [e for e in cast if last["id"] in chat.heard_by(conn, path, e)]
    who = conn.execute("SELECT name FROM entities WHERE id=?", (last["speaker_id"],)).fetchone()
    cause = inner.said(who["name"] if who else "Someone", last["text"])
    out = {}
    for src in inner.targets(conn, path, heard):
        rows, new = ledger(conn, src, path), []
        prof, dial = inner.profile(conn, src), knobs.dial(conn, src, "relationships", "realistic")
        if dial not in HARSH:  # a stray value must never break a turn
            dial = "realistic"
        for event, intensity in events:
            new += apply(
                rows + new, last["speaker_id"], event, intensity, cause, now, scene_id, prof, dial
            )
        if new:
            out[src] = new
    return out


COLUMNS = ("dst_id", "dim", "value", "kind", "half_life_min", "event", "cause", "resolves_id",
           "story_time")  # fmt: skip


def _insert(conn, story_id: int, src: int, rows: list[dict], message_id: int) -> None:
    conn.executemany(
        f"INSERT INTO opinions(story_id, src_id, {', '.join(COLUMNS)}, message_id)"
        f" VALUES({', '.join('?' * (len(COLUMNS) + 3))})",
        [(story_id, src, *(r[c] for c in COLUMNS), message_id) for r in rows],
    )


def save(conn: sqlite3.Connection, story_id: int, rows: dict[int, list], message_id: int) -> None:
    """Anchored on the reply they were read before: a new take or another branch has its own."""
    with conn:
        for src, new in rows.items():
            _insert(conn, story_id, src, new, message_id)


NOTICE, STRONG = 5, 15  # ponytail: a move this big is worth a word; this big, "much"


def _how(x: float, up: str, down: str) -> str:
    if abs(x) < NOTICE:
        return ""
    return (up if x > 0 else down).format(much="much " if abs(x) >= STRONG else "")


def _ago(minutes: int) -> str:
    """How long ago, in words only: clock.spell turns to digits from eleven units up."""
    if minutes < 60:
        return "just now"
    said = clock.spell(minutes).lower()
    if re.search(r"\d", said):
        said = "most of a day" if minutes < clock.DAY else "many " + said.split()[-1]
    return f"{said} ago"


def sentences(st: dict, name: str, now: int) -> list[str]:
    """Where they stand with `name`, as rows of the mind block (note 22 §4 row 3): how it has
    moved, why (the strongest causes, with their age), and what an open grudge means for this
    reply. Words, never numbers."""
    moved = [
        _how(st["trust"], "you trust them {much}more than before",
             "you trust them {much}less than before"),
        _how(st["closeness"], "you feel {much}closer to them", "you feel {much}further from them"),
        _how(st["respect"], "you respect them {much}more", "you respect them {much}less"),
    ]  # fmt: skip
    moved = [m for m in moved if m]
    if not moved and not st["grudge"]:
        return []
    why = "; ".join(f"{c['cause']}, {_ago(now - c['t'])}" for c in st["causes"][:1])
    rows = [
        f"Toward {name}: " + ("; ".join(moved) or "something is unresolved")
        + (f" ({why})." if why else ".")
    ]  # fmt: skip
    if g := st["grudge"]:
        rows.append(
            f"You have not forgiven {name} ({g['cause']}). Stay civil; do not warm up unless"
            f" {name} owns it."
        )
    elif st["forgiven"] and st["trust"] <= -NOTICE:
        rows.append(f"You have forgiven {name}, but trust comes back slowly.")
    return rows


def summary(st: dict) -> str:
    """The same standing in a few words for the app."""
    parts = [
        _how(st["trust"], "trusts {much}more", "trusts {much}less"),
        _how(st["closeness"], "{much}closer", "{much}further"),
        _how(st["respect"], "respects {much}more", "respects {much}less"),
        "holds a grudge" if st["grudge"] else "has forgiven" if st["forgiven"] else "",
    ]
    return " · ".join(p for p in parts if p)


def public(st: dict, other_id: int, other: str, you: bool, epoch: int) -> dict:
    """One bond as the app shows it (spec §8.3): numbers for a soft bar, words for the rest."""

    def cause(c: dict) -> dict:
        return {"event": c["event"], "cause": c["cause"], "since": clock.label(c["t"], epoch),
                "kind": c["kind"], "forgiven": c["forgiven"]}  # fmt: skip

    return {
        "other_id": other_id,
        "other": other,
        "you": you,
        **{d: st[d] for d in SHOWN},
        "words": summary(st),
        "grudge": cause(st["grudge"]) if st["grudge"] else None,
        "causes": [cause(c) for c in st["causes"]],
    }


def _size(st: dict) -> float:
    return sum(abs(st[d]) for d in SHOWN) + (100 if st["grudge"] else 0)


def toward(rows: list[dict], others: list[int], now: int) -> dict[int, dict]:
    """Standings worth a word, for each of `others` the ledger has something on."""
    out = {}
    for dst in others:
        st = standing(rows, dst, now)
        if st["grudge"] or any(abs(st[d]) >= NOTICE for d in SHOWN):
            out[dst] = st
    return out


def render(
    conn: sqlite3.Connection, story_id: int, src: int, path: list, pending: list[dict]
) -> tuple[list[str], list[dict]]:
    """The speaker's relationship rows for the mind block, and the same for the app: toward
    whoever they are answering, and the one other person here they feel most about."""
    story = conn.execute(
        "SELECT persona_entity_id, epoch_offset_min FROM stories WHERE id=?", (story_id,)
    ).fetchone()
    now = path[-1]["story_time"] if path else 0
    scene_id = chat.scene_of(conn, story_id, path)
    here = [e["id"] for e in chat.present_entities(conn, scene_id, path) if e["id"] != src]
    stands = toward(ledger(conn, src, path) + pending, here, now)
    last = path[-1]["speaker_id"] if path else None
    answering = last if last not in (None, src) else story["persona_entity_id"]
    rest = sorted((d for d in stands if d != answering), key=lambda d: -_size(stands[d]))
    picked = ([answering] if answering in stands else []) + rest[:1]
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)))
    rows, shown = [], []
    for d in picked:
        rows += sentences(stands[d], names.get(d, "them"), now)
        you = d == story["persona_entity_id"]
        shown.append(public(stands[d], d, names.get(d, "someone"), you, story["epoch_offset_min"]))
    return rows, shown
