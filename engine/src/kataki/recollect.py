"""How a character's memory is human, not just faded (docs/specs/2026-09-29-minds.md, slice 6;
note 14 §7.4-7.5, note 15 §1-2, §7A). Zero model calls.

- What she feels tilts what comes back (mood-congruent recall).
- A hazy memory she is pressed on and cannot reach gives true partial cues, built by code.
- Pinned and locked memories are never distorted, and a locked one is never forgotten.

The truth row is never touched: whatever her memory becomes is a `recollections` row of her
own, anchored like every minds row, so a swipe or a branch swaps it for free.

ponytail: every constant here is note 14's design default; tune on the probes, not by feel.
"""

import json
import re
import sqlite3

from kataki import clock, db, knobs

W_MOOD = 0.5  # note 14 §7.4: A' = A + 0.5 * M
MAX_CUES = 2


def congruence(valence: float | None, mood: float | None, importance: int) -> float:
    """The mood term M, weighted: a memory that felt like she feels now comes up more easily,
    the more so the more it mattered (arousal-gated). 0 without a valence or a mood."""
    if valence is None or mood is None:
        return 0.0
    return W_MOOD * valence * mood * importance / 10


def ago(minutes: int) -> str:
    """'about six years ago', in words only."""
    said = clock.spell(max(minutes, 1)).lower()
    if re.search(r"\d", said):
        said = f"many {said.split()[-1]}"
    return f"about {said} ago"


def _initial(name: str) -> str:
    first = re.sub(r"^(the|a|an)\s+", "", name.strip(), flags=re.I)[:1].upper()
    return first if first.isalpha() else ""  # words, never numbers


def cues(linked: list[dict], here: set[int], knower: int, emotion: str | None, since: int) -> list:
    """Up to two true partial cues for a memory on the tip of her tongue (note 14 §7.5): the
    first letter of someone in it who is not here, of the place, the feeling, how long ago."""
    out = []
    person = next(
        (e for e in linked if e["kind"] == "character" and e["id"] not in here | {knower}), None
    )
    if person and _initial(person["name"]):
        out.append(f"a name that starts with {_initial(person['name'])}")
    place = next((e for e in linked if e["kind"] == "place"), None)
    if place and _initial(place["name"]):
        out.append(f"a place whose name starts with {_initial(place['name'])}")
    if emotion and emotion.strip():
        out.append(f"the feeling: {emotion.strip()}")
    out.append(ago(since))
    return out[:MAX_CUES]


def lost(gist: str) -> str:
    """A hazy note that says so: models fill a bare gist in with invented detail (probe P6)."""
    return f"{gist} (the details are gone)"


def tip(gist: str, said: list[str]) -> str:
    return f"{gist} (on the tip of your tongue: {'; '.join(said)})"


# --- her version: what a memory has become for her (append-only; the truth row never changes) --

P_BASE, P_SPAN, P_CAP = 0.10, 0.30, 0.40  # note 14 D2: p = min(0.4, 0.10 + 0.30 * (1 - imp/10))
DIAL = {"faithful": 0.0, "human": 1.0, "dreamlike": 1.5}  # realism.memory (spec §6)
DREAM_CAP = 0.6
CANON = 8  # ponytail: a memory this important is canon (note 15 §1: never err on canon)
EARLY = 2  # ponytail: no slip in a story's first lines (note 15 §7A)


def dial(conn: sqlite3.Connection, entity_id: int | None) -> str:
    value = knobs.dial(conn, entity_id, "memory", "human")
    return value if value in DIAL else "human"


def drift_p(importance: int, style: str) -> float:
    """How likely a hazy memory's minor detail drifts this scene (note 14 D2), by the dial."""
    k = DIAL.get(style, 1.0)
    cap = DREAM_CAP if k > 1 else P_CAP
    return min(cap, k * (P_BASE + P_SPAN * (1 - importance / 10)))


def with_detail(gist: str, phrase: str) -> str:
    """The gist with one detail said: 'They met at a café, on Tuesday.'"""
    return f"{gist.rstrip(' .')}, {phrase.strip().rstrip('.')}."


def alts_of(m) -> list[dict]:
    try:
        got = json.loads(m["alts"] or "[]")
    except (TypeError, ValueError):
        return []
    return [a for a in got if isinstance(a, dict) and a.get("right") and a.get("wrong")]


def version(conn, knower: int, memory: int, runs: set[int], messages: set[int], now: int):
    """Her latest live recollection of this memory at `now` (by story time: a retelling filed
    late never undoes a correction made in between), or None."""
    where, args = db.anchor_filter(runs, messages)
    return conn.execute(
        f"SELECT * FROM recollections WHERE knower_id=? AND memory_id=? AND story_time<=?"
        f" AND {where} ORDER BY story_time DESC, id DESC LIMIT 1",
        [knower, memory, now, *args],
    ).fetchone()


def differs(row, m) -> str | None:
    """Her version's words when they are not simply the stored truth, else None. A `recount`
    (she put herself right) is true, and more exact than the gist, so it renders too."""
    if row is None or row["text"] in (m["detail"], m["gist"]):
        return None
    if (m["core_locked"] or m["pinned"]) and row["basis"] != "user":
        return None  # locked or pinned: never distorted (a user's own Correct still stands)
    return row["text"]


def write(conn, knower: int, memory: int, basis: str, text: str, t: int, *, parent=None,
          scene=None, message=None, run=None) -> int:  # fmt: skip
    return conn.execute(
        "INSERT INTO recollections(knower_id, memory_id, parent_id, basis, text, story_time,"
        " scene_id, message_id, run_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (knower, memory, parent, basis, text, t, scene, message, run),
    ).lastrowid


def pass_on(conn, teller: int, hearer: int, memory: int, runs: set[int], messages: set[int],
            now: int, *, run=None, message=None) -> int | None:  # fmt: skip
    """Being told a memory by someone who holds a version of it: the hearer gets that version
    (the telephone effect, note 14 §7.3). -> the new row, or None."""
    m = conn.execute("SELECT * FROM memories WHERE id=?", (memory,)).fetchone()
    if m is None or m["pinned"] or m["core_locked"] or dial(conn, hearer) == "faithful":
        return None
    theirs = version(conn, teller, memory, runs, messages, now)
    if differs(theirs, m) is None:
        return None
    return write(conn, hearer, memory, "retelling", theirs["text"], now, parent=theirs["id"],
                 run=run, message=message)  # fmt: skip


def open_slips(conn, who: int, path: list) -> list[dict]:
    """Her `correction` seeds on this branch that no reply has corrected yet and that have not
    lapsed, oldest first, with their payload."""
    if not path:
        return []
    where, args = db.anchor_filter(set(), {m["id"] for m in path})
    seeds = [
        {**dict(r), "payload": json.loads(r["payload"] or "{}")}
        for r in conn.execute(
            f"SELECT * FROM seeds WHERE entity_id=? AND kind='correction' AND {where} ORDER BY id",
            [who, *args],
        )
    ]
    done = set()
    for m in path:
        if m["role"] == "assistant" and m["speaker_id"] == who and m["gen"]:
            fixed = (json.loads(m["gen"]).get("recall") or {}).get("correction") or {}
            done.add(fixed.get("seed"))
    return [s for s in seeds if s["id"] not in done and not lapsed(s, path, who)]


def plant(conn, story_id: int, knower: int, m, alt: dict, at: dict, scene: int | None) -> int:
    """A slip, with the truth kept (note 15 §7A): her version with the wrong detail, and a
    `correction` seed that holds the right one. Both hang on the line being answered."""
    now = at["story_time"]
    rid = write(conn, knower, m["id"], "alt", with_detail(m["gist"], alt["wrong"]), now,
                scene=scene, message=at["id"])  # fmt: skip
    payload = {"slot": alt.get("slot"), "wrong": alt["wrong"], "right": alt["right"],
               "recollection": rid}  # fmt: skip
    conn.execute(
        "INSERT INTO seeds(story_id, entity_id, kind, text, memory_id, weight, half_life_min,"
        " payload, story_time, message_id) VALUES(?, ?, 'correction', ?, ?, 1.0, ?, ?, ?, ?)",
        (story_id, knower, f"it was {alt['right']}, not {alt['wrong']}", m["id"], clock.DAY,
         json.dumps(payload), now, at["id"]),
    )  # fmt: skip
    return rid


LAPSE = 6  # ponytail: her replies after a slip in which, never said, it is let go
STOP = frozenset("on in at the a an of with to by for from".split())


def _words(text: str) -> set[str]:
    return set(re.findall(r"[^\W_]+", (text or "").lower()))


def said(text: str, wrong: str, right: str) -> bool:
    """Did this line say the wrong detail (its own words, not the ones it shares with the
    truth)? 'on Tuesday' vs 'on Thursday' -> 'tuesday'."""
    key = _words(wrong) - _words(right) - STOP
    return bool(key & _words(text))


def _replies_after(seed: dict, path: list, who: int) -> list:
    ids = [m["id"] for m in path]
    if seed["message_id"] not in ids:
        return []
    after = path[ids.index(seed["message_id"]) + 1 :]
    return [m for m in after if m["role"] == "assistant" and m["speaker_id"] == who]


def lapsed(seed: dict, path: list, who: int) -> bool:
    """Never said within LAPSE of her replies: nothing to correct."""
    p = seed["payload"]
    after = _replies_after(seed, path, who)
    return len(after) >= LAPSE and not any(said(m["text"], p["wrong"], p["right"]) for m in after)


# --- the repair, and holding the line (decisions, so they go in [Directive]) -------------------

REPAIR_AFTER = 1  # ponytail: her replies between saying the slip and correcting it (note 15: 2-8)
CORRECTING = re.compile(
    r"\b(no,|nope|actually|you'?re wrong|that'?s (?:wrong|not (?:right|true|how))|you mean"
    r"|you said|didn'?t you|wasn'?t it|misremember\w*|(?:remember(?:ing)?|got) (?:it |that )?wrong)",
    re.IGNORECASE,
)


def _core(phrase: str) -> str:
    """'on Thursday' -> 'Thursday': the words a quick self-correction would say."""
    kept = [w for w in phrase.split() if w.lower() not in STOP]
    return " ".join(kept) or phrase


def repair(conn, who: int, path: list, user: str | None) -> dict | None:
    """Her first open slip that is now due: said, and then one more reply of hers ("due"); or
    said, and the user has just named the truth ("caught"). -> {"directive", "record"} or None."""
    them = user or "the other person"
    for seed in open_slips(conn, who, path):
        p = seed["payload"]
        after = _replies_after(seed, path, who)
        at = next((i for i, m in enumerate(after) if said(m["text"], p["wrong"], p["right"])), None)
        if at is None:
            continue
        record = {"seed": seed["id"], "memory_id": seed["memory_id"], "wrong": p["wrong"],
                  "right": p["right"]}  # fmt: skip
        if any(said(m["text"], p["right"], p["wrong"]) for m in after[at:]):
            return {"directive": "", "record": {**record, "why": "self"}}  # already put right
        pending = path[-1] if path and path[-1]["role"] == "user" else None
        if pending is not None and said(pending["text"], p["right"], p["wrong"]):
            why = "caught"
            text = (f"{them} is right: it was {p['right']}, not {p['wrong']}. Own the slip"
                    " lightly and carry on.")  # fmt: skip
        elif len(after) - at - 1 >= REPAIR_AFTER:
            why = "due"
            text = (f"You realise you had something wrong earlier: it was {p['right']}, not"
                    f" {p['wrong']}. Correct yourself in passing (“wait, … {_core(p['right'])}”),"
                    " then carry on.")  # fmt: skip
        else:
            continue
        return {"directive": text, "record": {**record, "why": why}}
    return None


def hold(path: list, recalled: list, user: str | None, names: set[str] = frozenset()) -> str:
    """The user's line reads as a correction and she holds a sharp memory right now: tell her
    to trust it (the sycophancy guard, note 15 §7A.6). The RULES' [SHARP] line says why.
    `names`: the words of the story's names and aliases, which never count as a shared word
    (naming her is not talking about what she remembers)."""
    pending = path[-1] if path and path[-1]["role"] == "user" else None
    if pending is None or not CORRECTING.search(pending["text"]):
        return ""
    words = _words(pending["text"]) - STOP - names
    if not any(
        r.tier == "sharp"
        and "elsewhere" not in r.breakdown
        and words & {w for w in _words(r.text) if len(w) > 3}
        for r in recalled
    ):
        return ""  # nothing she clearly remembers is what the line is about
    them = user or "the other person"
    return (f"If {them} says something that goes against what you clearly remember, trust your"
            f" memory and say so kindly; do not agree just to please {them}.")  # fmt: skip


def settle(conn, who: int, record: dict, message_id: int, t: int) -> None:
    """After the correcting reply: her memory is back on the truth, anchored on that reply."""
    m = conn.execute("SELECT * FROM memories WHERE id=?", (record["memory_id"],)).fetchone()
    with conn:
        write(conn, who, m["id"], "recount", with_detail(m["gist"], record["right"]), t,
              message=message_id)  # fmt: skip
