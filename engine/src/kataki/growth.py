"""How a character changes, slowly (docs/specs/2026-09-29-minds.md, slice 8; note 22 §1, §3 B2).

After a big skip the Between call she already makes grows a deep section: how she has come to
see the people closest to her, a line about herself, up to two candidate growth rings, each
citing the memories it rests on. Code gates every line mechanically (cited handles only, no new
names or numbers, hard length caps) and drops what fails with a warning. A ring enters as a seed
and takes hold only when later scenes bear it out; only then may it nudge one personality axis,
by a step code sets and caps, in this story only. Every row is a version (`supersedes_id`),
anchored like every minds table; the user accepts, rejects or locks with rows of their own.

ponytail: every constant here is an estimate from the research (note 12 §7, note 17 §6: "3
memories from 2 scenes", "±2 per step, ±10 per arc"); tune them on the probes, not by feel.
"""

import json
import re
import sqlite3

from kataki import chat, clock, db, features

RINGS = ("stance", "habit", "skill", "scar", "belief")
COUNTS = ("ring", "locked")  # the statuses whose trait nudge applies
TRAITS = {  # the direction the model may name -> (axis, sign); code sets the size
    "warmer": ("warmth", 1), "colder": ("warmth", -1),
    "bolder": ("dominance", 1), "meeker": ("dominance", -1),
    "franker": ("candor", 1), "more_guarded": ("candor", -1),
    "more_honest": ("honesty", 1), "less_honest": ("honesty", -1),
    "softer": ("yielding", 1), "firmer": ("yielding", -1),
    "calmer": ("volatility", -1), "touchier": ("volatility", 1),
}  # fmt: skip
STEP = 2  # ponytail: axis points one ring moves (note 12 §7: "±2 per axis per window")
CAP = 10  # ponytail: the most all rings together move one axis (note 12 §7: "±10 per arc")
WORDS = {"relationship": 25, "self": 80, "ring": 15}  # hard caps (note 22 §3)
SENTENCES = 6  # the self line
EVIDENCE, SCENES = 3, 2  # a ring rests on this many memories from this many scenes (note 17 §6)
NUMBERS = frozenset(
    "one two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty"
    " hundred thousand million".split()
)
ME = frozenset({"i", "i'm", "i've", "i'd", "i'll"})


# --- the gate (note 14 §6): every item, before it becomes a row --------------------------------


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'’-]*|\d+", text)


def _new_name(line: str, allowed: set[str]) -> str | None:
    """A capitalised word that is not a sentence's first word, not "I", and not a name or word
    the call was shown: a new proper noun."""
    for sentence in re.split(r"(?<=[.!?:;—])\s+", line):
        for i, w in enumerate(_words(sentence.strip(" \"'“”‘’*("))):
            if i and w[0].isupper() and w.lower() not in ME and w.lower() not in allowed:
                return w
    return None


def _new_number(line: str, cited: str) -> str | None:
    """A digit or number word that is not in the memories the line cites."""
    have = {w.lower() for w in _words(cited)}
    return next((w for w in _words(line) if (w.isdigit() or w.lower() in NUMBERS)
                 and w.lower() not in have), None)  # fmt: skip


def gate(item: dict, kind: str, memories: dict[str, dict], people: dict[str, int],
         names: set[str]) -> str | None:  # fmt: skip
    """Why one item of the deep section may not become a row, or None when it passes. `kind`:
    "relationship", "self" or "ring"; `memories`: the handles it was shown ({"M31": {"id",
    "text", "scene"}}); `people`: its person handles; `names`: lower-case names in the story."""
    line = item.get("claim" if kind == "ring" else "line")
    sources = item.get("sources")
    if not isinstance(line, str) or not line.strip():
        return "it was empty"
    if not isinstance(sources, list) or not sources:
        return "it cited no source"
    if bad := [s for s in sources if not isinstance(s, str) or s not in memories]:
        return f"it cited an unknown memory ({bad[0]})"
    about = item.get("about")
    if kind == "relationship" and not (isinstance(about, str) and about in people):
        return "it was about someone it was not shown"
    if len(line.split()) > WORDS[kind] or (
        kind == "self" and len(re.findall(r"[.!?]+(?:\s|$)", line.strip())) > SENTENCES
    ):
        return "it was too long"
    cited = " ".join(memories[s]["text"] for s in sources)
    if n := _new_number(line, cited):
        return f'it added a number ("{n}")'
    shown = {w.lower() for m in memories.values() for w in _words(m["text"])}
    if w := _new_name(line, names | shown):
        return f'it named someone or something her memories don\'t ("{w}")'
    if kind == "ring":
        seen = {s for s in sources}
        if len(seen) < EVIDENCE or len({memories[s]["scene"] for s in seen}) < SCENES:
            return "it had too little evidence (three memories from two scenes)"
    return None


# --- trait drift: code's, capped, reversible ------------------------------------------------------


def step(trait) -> dict | None:
    """The nudge a ring's direction carries: one axis, STEP points. None for none or unknown."""
    if not isinstance(trait, str) or trait not in TRAITS:
        return None
    axis, sign = TRAITS[trait]
    return {axis: sign * STEP}


def drift(rows: list[dict]) -> dict[str, int]:
    """What current rings add to each axis: rings and locked ones only, capped per axis."""
    out: dict[str, float] = {}
    for r in rows:
        if r["status"] in COUNTS and isinstance(r.get("trait_delta"), dict):
            for axis, d in r["trait_delta"].items():
                if isinstance(d, (int, float)) and not isinstance(d, bool):
                    out[axis] = out.get(axis, 0) + d
    return {a: int(max(-CAP, min(CAP, v))) for a, v in out.items() if v}


# --- rows -----------------------------------------------------------------------------------------


def _row(r: sqlite3.Row) -> dict:
    out = dict(r)
    for key in ("sources", "trait_delta"):
        try:
            out[key] = json.loads(r[key]) if r[key] else ([] if key == "sources" else None)
        except ValueError:
            out[key] = [] if key == "sources" else None
    return out


def live(conn: sqlite3.Connection, who: int, path: list) -> list[dict]:
    """Every live row of hers on this branch (the user's own, on a line of `path`, or on a live
    run), oldest first."""
    runs = db.live_runs(conn, path[-1]["story_id"], path[-1]["id"]) if path else set()
    where, args = db.anchor_filter(runs, {m["id"] for m in path})
    return [
        _row(r)
        for r in conn.execute(
            f"SELECT * FROM reflections WHERE knower_id=? AND {where} ORDER BY id", [who, *args]
        )
    ]


def current(conn: sqlite3.Connection, who: int, path: list) -> list[dict]:
    """Her reflections as they stand: live rows no live row supersedes, newest first. A version
    counts only where the row it changes is live (the user's own versions are unanchored, so a
    ring accepted on one branch must not appear on another)."""
    ids, rows = set(), []
    for r in live(conn, who, path):  # id order: a row comes after the one it supersedes
        if r["supersedes_id"] is None or r["supersedes_id"] in ids:
            ids.add(r["id"])
            rows.append(r)
    gone = {r["supersedes_id"] for r in rows if r["supersedes_id"] is not None}
    return [r for r in reversed(rows) if r["id"] not in gone]


def write(conn, story_id: int, who: int, kind: str, text: str, sources: list[int], status: str,
          now: int, *, subject: int | None = None, delta: dict | None = None,
          supersedes: int | None = None, message_id: int | None = None,
          run_id: int | None = None) -> int:  # fmt: skip
    """One row, inside the caller's transaction."""
    return conn.execute(
        "INSERT INTO reflections(story_id, knower_id, kind, subject_id, text, sources, status,"
        " trait_delta, supersedes_id, story_time, message_id, run_id)"
        " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (story_id, who, kind, subject, text, json.dumps(sources), status,
         json.dumps(delta) if delta else None, supersedes, now, message_id, run_id),
    ).lastrowid  # fmt: skip


def again(conn, r: dict, status: str, now: int, message_id=None, run_id=None) -> int:
    """A new version of `r` with another status (inside the caller's transaction)."""
    return write(conn, r["story_id"], r["knower_id"], r["kind"], r["text"], r["sources"], status,
                 now, subject=r["subject_id"], delta=r["trait_delta"], supersedes=r["id"],
                 message_id=message_id, run_id=run_id)  # fmt: skip


ACTIONS = {"accept": "ring", "reject": "rejected", "lock": "locked"}


def act(conn: sqlite3.Connection, reflection_id: int, action: str) -> int:
    """The user's say (§6 rule 6): a new, unanchored version, holding wherever the row it changes
    is live. The row it supersedes is never touched. KeyError: no such row; LookupError: not
    current on the active branch (stale, or another branch's). -> the new row's id."""
    if action not in ACTIONS:
        raise ValueError(f"unknown action {action!r}")
    r = conn.execute("SELECT * FROM reflections WHERE id=?", (reflection_id,)).fetchone()
    if r is None:
        raise KeyError(reflection_id)
    path = chat.active_path(conn, r["story_id"])
    if reflection_id not in {x["id"] for x in current(conn, r["knower_id"], path)}:
        raise LookupError("that reflection is not current on this branch")
    last = conn.execute(
        "SELECT MAX(story_time) FROM messages WHERE story_id=?", (r["story_id"],)
    ).fetchone()[0]
    with conn:
        return again(conn, _row(r), ACTIONS[action], max(last or 0, r["story_time"]))


def profile_drift(conn: sqlite3.Connection, who: int) -> dict[str, int]:
    """The capped drift her current rings give her on the active branch (inner.profile adds it).
    Cheap when she has no nudge at all (the usual case): one indexed query."""
    row = conn.execute(
        "SELECT story_id FROM reflections WHERE knower_id=? AND trait_delta IS NOT NULL LIMIT 1",
        (who,),
    ).fetchone()
    if row is None or not features.enabled(conn, "mind.growth"):
        return {}
    return drift(current(conn, who, chat.active_path(conn, row[0])))


def since(r: dict, epoch: int) -> str:
    return clock.label(r["story_time"], epoch)


# --- the deep pass (note 22 §3 B2): when, on what, and what comes of it -------------------------

DEEP_SKIP = {"premium": clock.DAY}  # ponytail: a skip this long calls for a deep pass ...
LONG = 7 * clock.DAY  # ... on standard (note 14 §6: "about 7 story-days")
PILE = 40  # new memories since her last deep pass that call for one (note 14 §6)
WORK = 30  # ponytail: her memories the call is shown (note 22 §3: "about 30 items")
PEOPLE_MAX = 6  # people it may write a line about
TRIGGER = "between"


def _last(conn, story_id: int, who: int, path: list, skip_id: int) -> int | None:
    """The story time of her last deep pass on this branch that ran, or None."""
    ids = [m["id"] for m in path if m["id"] != skip_id]
    if not ids:
        return None
    times = {m["id"]: m["story_time"] for m in path}
    rows = conn.execute(
        f"SELECT to_message_id, raw FROM extraction_runs WHERE story_id=? AND trigger=?"
        f" AND status='ok' AND to_message_id IN ({','.join('?' * len(ids))})",
        [story_id, TRIGGER, *ids],
    ).fetchall()
    done = []
    for r in rows:
        raw = json.loads(r["raw"] or "{}")
        if str(who) in (raw.get("deep") or {}) and (raw.get("b1") or {}).get(str(who)) == "ok":
            done.append(times[r["to_message_id"]])
    return max(done, default=None)


def trigger(
    conn: sqlite3.Connection, story_id: int, who: int, path: list, level: str
) -> str | None:
    """Whether the skip at the end of `path` calls for her deep pass, and why: `long_skip`,
    `memories` (enough new ones since the last), `arc` (a chapter closed since). Code, zero
    calls; lite never gets one."""
    if level == "lite" or not path:
        return None
    skip = path[-1]
    if skip["skip_minutes"] >= DEEP_SKIP.get(level, LONG):
        return "long_skip"
    last = _last(conn, story_id, who, path, skip["id"])
    after = -1 if last is None else last
    live = db.live_runs(conn, story_id, skip["id"])
    know, args = db.live_filter(live, "k.run_id")
    n = conn.execute(
        "SELECT COUNT(DISTINCT m.id) FROM memories m JOIN knowledge k ON k.memory_id=m.id"
        f" WHERE k.knower_id=? AND m.story_id=? AND m.hidden=0 AND m.story_time>?"
        f" AND m.story_time<=? AND {know}",
        [who, story_id, after, skip["story_time"], *args],
    ).fetchone()[0]
    if n >= PILE:
        return "memories"
    ids = [m["id"] for m in path]
    times = {m["id"]: m["story_time"] for m in path}
    for (to,) in conn.execute(
        f"SELECT to_message_id FROM chapters WHERE story_id=? AND to_message_id IN"
        f" ({','.join('?' * len(ids))})",
        [story_id, *ids],
    ):
        if times[to] > after:
            return "arc"
    return None


def _scene(conn, memory_id: int, t: int) -> str:
    """Which scene a memory is from, for "two scenes" (note 17 §6: scenes or story-days): its
    line's scene and its story-day together."""
    row = conn.execute(
        "SELECT ms.scene_id FROM memories m LEFT JOIN messages ms ON ms.id=m.message_id"
        " WHERE m.id=?",
        (memory_id,),
    ).fetchone()
    return f"{row and row[0]}:{t // clock.DAY}"


def working(conn: sqlite3.Connection, story_id: int, who: int, now: int, known: list[dict]) -> dict:
    """What the deep pass may use: her strongest and newest memories (`known`, from
    retrieve.inspect: hers only, as she holds them) as handles, the people in the story as
    handles, and every name the story has. Never an earlier reflection (C3)."""
    held = [m for m in known if m["tier"] != "forgotten" and not m["hidden"]]
    held.sort(key=lambda m: (-m["importance"], -m["story_time"]))
    picked = sorted(held[:WORK], key=lambda m: (m["story_time"], m["memory_id"]))
    memories = {}
    for m in picked:
        text = (m.get("version") or {}).get("text") or (
            m["detail"] if m["tier"] == "sharp" else m["gist"]
        )
        memories[f"M{m['memory_id']}"] = {
            "id": m["memory_id"], "text": text, "scene": _scene(conn, m["memory_id"], m["story_time"]),
        }  # fmt: skip
    story = conn.execute("SELECT persona_entity_id FROM stories WHERE id=?", (story_id,)).fetchone()
    others = conn.execute(
        "SELECT id, name FROM entities WHERE story_id=? AND kind='character' AND hidden=0"
        " AND id<>?",
        (story_id, who),
    ).fetchall()
    said = " ".join(m["text"] for m in memories.values()).lower()
    others = sorted(others, key=lambda e: (e["id"] != story["persona_entity_id"],
                                          -said.count(e["name"].lower())))  # fmt: skip
    called = conn.execute(
        "SELECT name FROM entities WHERE story_id=? UNION"
        " SELECT a.alias FROM aliases a JOIN entities e ON e.id=a.entity_id WHERE e.story_id=?",
        (story_id, story_id),
    )
    return {
        "memories": memories,
        "people": {f"P{e['id']}": e["id"] for e in others[:PEOPLE_MAX]},
        "who": {f"P{e['id']}": e["name"] for e in others[:PEOPLE_MAX]},
        "names": {w.lower() for (n,) in called for w in _words(n)},
    }


def take(conn: sqlite3.Connection, story_id: int, who: int, deep, work: dict, path: list,
         message_id: int, run_id: int, now: int) -> list[str]:  # fmt: skip
    """The deep section's items that pass the gate, as rows on the skip's run (inside the
    caller's transaction): lines in force at once, superseding her previous one on the same
    subject (never a locked one); rings as seeds with the nudge code gives them. -> warnings for
    what was dropped."""
    if not isinstance(deep, dict):
        return ["The reflection was missing from the answer."]
    mems, people, names = work["memories"], work["people"], work["names"]
    warn: list[str] = []
    before = current(conn, who, path)

    def kept(item, kind, what) -> bool:
        why = "it was malformed" if not isinstance(item, dict) else gate(
            item, kind, mems, people, names)  # fmt: skip
        if why:
            warn.append(f"{what} was dropped: {why}.")
        return why is None

    def line(kind: str, item: dict, subject: int | None) -> None:
        old = next((r for r in before if r["kind"] == kind and r["subject_id"] == subject
                    and r["status"] == "ring"), None)  # fmt: skip
        write(conn, story_id, who, kind, " ".join(item["line"].split()),
              [mems[s]["id"] for s in dict.fromkeys(item["sources"])], "ring", now,
              subject=subject, supersedes=old and old["id"], message_id=message_id,
              run_id=run_id)  # fmt: skip

    rel = deep.get("relationship") if isinstance(deep.get("relationship"), list) else []
    seen: set[int] = set()
    for item in rel[:2]:
        if kept(item, "relationship", "A line about someone") and people[item["about"]] not in seen:
            seen.add(people[item["about"]])
            line("relationship", item, people[item["about"]])
    if deep.get("self") is not None and kept(deep["self"], "self", "The line about herself"):
        line("self", deep["self"], None)
    rings = deep.get("rings") if isinstance(deep.get("rings"), list) else []
    for item in rings[:2]:
        if not kept(item, "ring", "A growth ring"):
            continue
        if item.get("kind") not in RINGS:
            warn.append("A growth ring was dropped: it was malformed.")
            continue
        write(conn, story_id, who, item["kind"], " ".join(item["claim"].split()),
              [mems[s]["id"] for s in dict.fromkeys(item["sources"])], "seed", now,
              delta=step(item.get("trait")), message_id=message_id, run_id=run_id)  # fmt: skip
    return warn


# --- reinforcement (note 17 §6), at every skip's tick: zero calls, every level -------------------

TTL = 30 * clock.DAY  # ponytail: a seed not borne out in this long passes (kept, viewable)
STOP = frozenset(
    "that this with from have been into about when what were they them their there then than"
    " your just more some very also only over again after before still even ever never always"
    " learned learnt became become grown began".split()
)


def stems(text: str) -> set[str]:
    """A ring's content words, cut to five letters so 'helped' meets 'help' (ponytail: words
    only, no embedder)."""
    return {_stem(w) for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 4 and w not in STOP}


def _stem(w: str) -> str:
    return re.sub(r"(ing|ed|es|s)$", "", w)[:5]


def born(r: dict, rows: dict[int, dict]) -> int:
    """When a reflection first came to be: its earliest version among `rows`."""
    seen = set()
    while r["supersedes_id"] in rows and r["id"] not in seen:
        seen.add(r["id"])
        r = rows[r["supersedes_id"]]
    return r["story_time"]


def evidence(conn, who: int, r: dict, path: list, now: int, since: int | None = None) -> dict:
    """What bears a ring out: memories she holds, dated after it (or `since`), that share a
    content word with it (its own sources aside), and how many scenes they span."""
    want = stems(r["text"])
    if not want or not path:
        return {"memories": 0, "scenes": 0}
    live = db.live_runs(conn, path[-1]["story_id"], path[-1]["id"])
    know, args = db.live_filter(live, "k.run_id")
    rows = conn.execute(
        "SELECT DISTINCT m.id, m.detail, m.story_time FROM memories m"
        " JOIN knowledge k ON k.memory_id=m.id"
        f" WHERE k.knower_id=? AND m.hidden=0 AND m.story_time>? AND m.story_time<=? AND {know}",
        [who, r["story_time"] if since is None else since, now, *args],
    ).fetchall()
    hits = [
        m for m in rows
        if m["id"] not in r["sources"]
        and want & {_stem(w) for w in re.findall(r"[a-z]+", m["detail"].lower())}
    ]  # fmt: skip
    return {
        "memories": len(hits),
        "scenes": len({_scene(conn, m["id"], m["story_time"]) for m in hits}),
    }


def reinforce(conn, who: int, path: list, now: int, message_id: int, run_id: int) -> None:
    """Her seeds, at a skip: borne out by three memories from two later scenes, a ring; not
    borne out in thirty story-days, past. Rows on the skip's run (inside the caller's
    transaction); a ring, a locked or a rejected one is never touched."""
    for r in current(conn, who, path):
        if r["status"] != "seed" or r["kind"] not in RINGS:
            continue
        ev = evidence(conn, who, r, path, now)
        if ev["memories"] >= EVIDENCE and ev["scenes"] >= SCENES:
            again(conn, r, "ring", now, message_id, run_id)
        elif now - r["story_time"] >= TTL:
            again(conn, r, "past", now, message_id, run_id)


# --- what reaches her reply: one line at most (note 22 §4 row 3; C17) ----------------------------


def line(conn, who: int, path: list, answering: int | None, name: str | None) -> dict | None:
    """Her line about whoever she answers, else her strongest ring (locked first, then newest),
    as one row of the mind block, in words. Seeds, past and rejected ones never reach it.
    -> {"reflection", "kind", "text"} or None."""
    rows = [r for r in current(conn, who, path) if r["status"] in COUNTS]
    first = lambda rs: min(rs, key=lambda r: (r["status"] != "locked", -r["id"]), default=None)  # noqa: E731
    r = first([r for r in rows if r["kind"] == "relationship" and r["subject_id"] == answering])
    if r is not None and name:
        text = f"How you have come to see {name}: “{r['text']}”"
    elif (r := first([r for r in rows if r["kind"] in RINGS])) is not None:
        text = f"Something that has changed in you: {r['text'].rstrip('.')}."
    else:
        return None
    if re.search(r"\d", text):  # words, never numbers (the gate already holds this)
        return None
    return {"reflection": r["id"], "kind": r["kind"], "text": text}


# --- what the app shows (spec §8.3 slice 8) ---------------------------------------------------------

AXIS_WORDS = {  # axis -> (up, down), for Peek; the prompt never gets these
    "warmth": ("warmer", "colder"), "dominance": ("bolder", "meeker"),
    "candor": ("franker", "more guarded"), "honesty": ("more honest", "less honest"),
    "yielding": ("quicker to give way", "firmer"), "volatility": ("touchier", "calmer"),
}  # fmt: skip


def words(axis: str, delta: float) -> str:
    up, down = AXIS_WORDS.get(axis, (f"more {axis}", f"less {axis}"))
    size = "a little " if abs(delta) <= STEP else "much " if abs(delta) > 6 else ""
    return size + (up if delta > 0 else down)


def _trait(delta) -> dict | None:
    if not isinstance(delta, dict) or not delta:
        return None
    axis, d = next(iter(delta.items()))
    return {"axis": axis, "delta": d, "words": words(axis, d)}


def warnings(conn, story_id: int, who: int, path: list) -> list[str]:
    """Why her latest reflection dropped something, from the latest between run on the branch."""
    ids = [m["id"] for m in path]
    if not ids:
        return []
    for (raw,) in conn.execute(
        f"SELECT raw FROM extraction_runs WHERE story_id=? AND trigger=? AND status='ok'"
        f" AND to_message_id IN ({','.join('?' * len(ids))}) ORDER BY to_message_id DESC",
        [story_id, TRIGGER, *ids],
    ):
        said = json.loads(raw or "{}").get("deep_warnings", {})
        if str(who) in said:
            return list(said[str(who)])
    return []


def holds(conn, story_id: int, who: int) -> dict[int, str]:
    """Her memories as she holds them (her version, else sharp detail or hazy gist), by id: the
    text the deep pass judged, for Peek's sources."""
    from kataki import retrieve  # retrieve imports inner, which imports this module

    return {
        m["memory_id"]: (m.get("version") or {}).get("text")
        or (m["detail"] if m["tier"] == "sharp" else m["gist"])
        for m in retrieve.inspect(conn, story_id, who)
    }


def entry(conn, r: dict, path: list, names: dict, epoch: int, rows: dict | None = None,
          texts: dict[int, str] | None = None) -> dict:  # fmt: skip
    """One reflection as Peek shows it."""
    before = (rows or {}).get(r["supersedes_id"]) if r["supersedes_id"] else None
    if before is None and r["supersedes_id"]:
        got = conn.execute("SELECT text FROM reflections WHERE id=?", (r["supersedes_id"],))
        before = got.fetchone()
    anchored = r["message_id"] is not None or r["run_id"] is not None
    by = "user" if not anchored else "code" if before and before["text"] == r["text"] else "deep"
    src = [s for s in r["sources"] if isinstance(s, int)] or [0]
    held = conn.execute(
        f"SELECT id, detail FROM memories WHERE id IN ({','.join('?' * len(src))})", src
    ).fetchall()
    now = path[-1]["story_time"] if path else 0
    return {
        "id": r["id"], "kind": r["kind"], "about": names.get(r["subject_id"]),
        "about_id": r["subject_id"], "text": r["text"], "status": r["status"], "by": by,
        "sources": [{"memory_id": m["id"], "text": (texts or {}).get(m["id"], m["detail"])}
                    for m in held],  # fmt: skip
        "evidence": evidence(conn, r["knower_id"], r, path, now, born(r, rows or {}))
        if r["kind"] in RINGS
        else None,
        "trait": _trait(r["trait_delta"]),
        "since": clock.label(r["story_time"], epoch), "message_id": r["message_id"],
    }  # fmt: skip


def public(conn, story_id: int, who: int, path: list, names: dict, epoch: int) -> dict:
    """Peek's `growth` (spec §8.3): her reflections as they stand, the drift, the warnings."""
    rows = {r["id"]: r for r in live(conn, who, path)}
    now = current(conn, who, path)
    texts = holds(conn, story_id, who) if now else {}
    return {
        "reflections": [entry(conn, r, path, names, epoch, rows, texts) for r in now],
        "drift": [{"axis": a, "delta": d, "words": words(a, d)} for a, d in drift(now).items()],
        "warnings": warnings(conn, story_id, who, path),
    }
