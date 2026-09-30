"""What does this character recall right now? Zero LLM calls.

seeds      entities named in the recent text (alias match) + the current place
candidates memories one hop from a seed, two hops, tied to someone present, or an FTS hit
gate       live on this branch, not in the future, not still in the verbatim window, and
           KNOWN TO THIS CHARACTER: a knowledge row, or common knowledge. This is a hard
           filter, not a score - someone who was not there cannot recall it at any relevance.
score      activation.py, on story time
render     sharp -> detail, hazy -> gist; pressing a hazy memory makes them strain, once per
           scene, with a fixed outcome
rehearse   being recalled is an access, at most one per scene
"""

import json
import logging
import re
import sqlite3

from kataki import activation, chat, clock, db, features, knobs, recollect
from kataki.activation import Access
from kataki.context import Recalled

LIMIT = 30
RRF_K = 10
STOPWORDS = frozenset(
    "the and but for not with you your what who whom whose when where why how did does was were"
    " are has have had about that this they them then than there here from into will would could"
    " should can him her his she its our out any all tell told said say know remember".split()
)
HEARSAY = {
    "told": "({who} told you)",
    "overheard": "(you overheard)",
    "rumor": "(rumour has it)",
    "inferred": "(you suspect)",
}


def mentioned(conn: sqlite3.Connection, story_id: int, text: str) -> set[int]:
    """Entities the text names. Longest alias first, so 'the old docks' beats 'the docks'."""
    rows = conn.execute(
        "SELECT a.alias, a.entity_id FROM aliases a JOIN entities e ON e.id=a.entity_id"
        " WHERE e.story_id=? AND e.hidden=0 ORDER BY length(a.alias) DESC",
        (story_id,),
    ).fetchall()
    if not rows or not text.strip():
        return set()
    # ponytail: regex rebuilt per call; cache per story if a huge cast ever makes this show up
    by_alias = {r["alias"].lower(): r["entity_id"] for r in reversed(rows)}
    pattern = "|".join(re.escape(r["alias"]) for r in rows)
    found = re.findall(rf"(?<!\w)(?:{pattern})(?!\w)", text, re.IGNORECASE)
    return {by_alias[f.lower()] for f in found}


def _fts_query(text: str) -> str:
    """User text is never FTS syntax: keep plain words, quote each, OR them."""
    words = [w for w in re.findall(r"[^\W_]+", text.lower()) if len(w) > 2 and w not in STOPWORDS]
    return " OR ".join(f'"{w}"' for w in dict.fromkeys(words))


def _ids(rows) -> set[int]:
    return {r[0] for r in rows}


def _assess(
    conn, m, knower_id, known, now, live_scenes, live, relevance, graph, wobble, d, mood=0.0
):
    """One memory, one knower: (how they know it, is it superseded, activation score). A locked
    memory (minds slice 6, `mood` given means the feature is on) is never forgotten: at worst
    hazy."""
    live_sql, live_args = db.live_filter(live)
    source = known["source"] if known else "innate"
    learned = known["learned_story_time"] if known else m["story_time"]
    accesses = [Access(learned, 1.0, True)]  # the encoding itself
    accesses += [
        Access(a["story_time"], a["weight"], bool(a["sharp"]))
        for a in conn.execute(
            "SELECT * FROM accesses WHERE knower_id=? AND memory_id=?", (knower_id, m["id"])
        )
        if a["scene_id"] in live_scenes and a["story_time"] <= now
    ]
    superseded = bool(
        conn.execute(
            f"SELECT 1 FROM memories WHERE supersedes_id=? AND {live_sql}", [m["id"], *live_args]
        ).fetchone()
    )
    s = activation.score(
        accesses,
        now=now,
        importance=m["importance"],
        relevance=relevance,
        graph=graph,
        source=source,
        superseded=superseded,
        noise=wobble,
        d=d,
        mood=mood or 0.0,
    )
    if s.tier is None and mood is not None and m["core_locked"]:
        s = activation.Score(s.base_all, s.base_detail, s.a_all, s.a_detail, "hazy")
    return source, superseded, s


def live_scenes(conn, story_id: int, path: list) -> set[int]:
    return _ids(
        conn.execute(
            "SELECT id FROM scenes WHERE story_id=? AND (start_message_id IS NULL"
            f" OR start_message_id IN ({','.join('?' * len(path))}))",
            [story_id, *(m["id"] for m in path)],
        )
    )


def recall(
    conn: sqlite3.Connection,
    story_id: int,
    knower_id: int,
    text: str,
    *,
    window_start: int | None = None,  # first message id still shown verbatim
    pressed: set[int] | frozenset = frozenset(),  # hazy memories injected last turn too
    noise: bool = True,
    log: bool = True,  # False = a read-only look, for the inspector
    d: float = activation.DECAY,
    leaf_id: int | None = None,  # recall as of this message (a regenerate); default: active leaf
    vector_ranks: dict[int, int] | None = None,  # from embed.py, when an embedder is set
    mood: float | None = None,  # her mood's valence now (inner.py), for mood-congruent recall
) -> list[Recalled]:
    path = chat.path_to(conn, leaf_id) if leaf_id else chat.active_path(conn, story_id)
    if not path:
        # nothing said here yet, but a story it looks back at may still be in her
        return elsewhere(conn, story_id, knower_id, text, 0)
    now, scene_id = path[-1]["story_time"], path[-1]["scene_id"]
    live = db.live_runs(conn, story_id, leaf_id)
    live_sql, live_args = db.live_filter(live)
    scene = conn.execute("SELECT place_id FROM scenes WHERE id IS ?", (scene_id,)).fetchone()
    present = chat.present_entities(conn, scene_id, path)

    seeds = mentioned(conn, story_id, text)
    if scene and scene["place_id"]:
        seeds.add(scene["place_id"])
    nearby = {e["entity_id"] for e in present} - seeds

    def linked(entity_ids: set[int]) -> set[int]:
        if not entity_ids:
            return set()
        marks = ",".join("?" * len(entity_ids))
        return _ids(
            conn.execute(
                f"SELECT memory_id FROM memory_entities WHERE entity_id IN ({marks})",
                sorted(entity_ids),
            )
        )

    one_hop = linked(seeds)
    two_hop: set[int] = set()
    if one_hop:
        marks = ",".join("?" * len(one_hop))
        bridge = _ids(
            conn.execute(
                f"SELECT entity_id FROM memory_entities WHERE memory_id IN ({marks})",
                sorted(one_hop),
            )
        )
        two_hop = linked(bridge - seeds)
    graph = {m: 0.5 for m in two_hop | linked(nearby)} | {m: 1.0 for m in one_hop}

    ranks: dict[int, int] = {}
    if query := _fts_query(text):
        hits = conn.execute(
            "SELECT rowid FROM memories_fts WHERE memories_fts MATCH ? ORDER BY rank LIMIT ?",
            (query, LIMIT),
        )
        ranks = {r["rowid"]: i for i, r in enumerate(hits, start=1)}
    # reciprocal rank fusion over the ranked lists that were searched: words, and meaning
    searched = [r for r in (ranks if query else None, vector_ranks) if r is not None]

    def relevance_of(memory_id: int) -> float:
        fused = sum(1 / (RRF_K + r[memory_id]) for r in searched if memory_id in r)
        return fused / (len(searched) / (RRF_K + 1)) if searched else 0.0

    candidates = set(graph) | set(ranks) | set(vector_ranks or ())
    if not candidates:
        return elsewhere(conn, story_id, knower_id, text, now)
    marks = ",".join("?" * len(candidates))
    rows = conn.execute(
        f"SELECT * FROM memories WHERE id IN ({marks}) AND story_id=? AND hidden=0"
        f" AND story_time<=? AND {live_sql}",
        [*sorted(candidates), story_id, now, *live_args],
    ).fetchall()

    know_sql, know_args = db.live_filter(live, "k.run_id")
    names = dict(
        conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)).fetchall()
    )
    ours = live_scenes(conn, story_id, path)
    human = _human(conn)  # minds slice 6: the human effects of memory, or today's recall exactly
    here = {e["entity_id"] for e in present}
    on_path = {p["id"] for p in path}
    slip = True  # no new slip: off, early in the story, the dial, or one already open
    if human and len(path) > recollect.EARLY:
        try:
            slip = recollect.dial(conn, knower_id) == "faithful" or bool(
                recollect.open_slips(conn, knower_id, path)
            )
        except Exception as e:
            logging.getLogger(__name__).warning("no slips for %s: %s", knower_id, e)

    results = []
    for m in rows:
        if window_start is not None and (m["to_message_id"] or 0) >= window_start:
            continue  # the model can already read this in the chat itself
        if m["pinned"]:
            continue  # so can this: a pinned fact is in the stable block of every prompt
        known = conn.execute(
            f"SELECT k.* FROM knowledge k WHERE k.knower_id=? AND k.memory_id=? AND {know_sql}"
            " ORDER BY k.id DESC LIMIT 1",
            [knower_id, m["id"], *know_args],
        ).fetchone()
        if known is None and not m["common"]:
            continue  # the hard gate: this character does not know it

        relevance = relevance_of(m["id"])
        wobble = activation.noise(knower_id, m["id"], scene_id or 0) if noise else 0.0
        tilt = recollect.congruence(m["valence"], mood, m["importance"]) if human else None
        source, superseded, s = _assess(
            conn, m, knower_id, known, now, ours, live, relevance, graph.get(m["id"], 0.0),
            wobble, d, tilt,
        )  # fmt: skip
        if s.tier is None:
            continue  # forgotten, for now

        effortful = None
        if s.tier == "hazy" and m["id"] in pressed:
            effortful = activation.effortful_recall(s.a_detail, knower_id, m["id"], scene_id or 0)
        sharp = s.tier == "sharp" or bool(effortful)
        body = m["detail"] if sharp else m["gist"]
        mine, drift, cue = None, None, None
        if human:  # her own version wins, even over a strain; or a hazy detail drifts
            mine, drift = _mine(
                conn,
                m,
                knower_id,
                "sharp" if effortful else s.tier,
                live,
                on_path,
                now,
                scene_id,
                slip,
            )
            slip = slip or drift is not None  # one new slip at a time
        if mine:
            body = mine
        elif effortful:
            body = f"(after straining to recall) {body}"
        elif human and effortful is False:  # on the tip of her tongue: true pieces, no more
            cue = _cues(conn, m, here, knower_id, now)
            body = recollect.tip(body, cue) if cue else body
        elif human and not sharp and m["gist"] != m["detail"]:  # said, so she won't fill it in
            body = recollect.lost(body)
        if source in HEARSAY:
            who = names.get(known["told_by_id"], "someone") if known["told_by_id"] else "someone"
            body = f"{HEARSAY[source].format(who=who)} {body}"
        if known and m["kind"] == "claim" and known["belief"] < 0.7:
            doubt = "you did not believe this" if known["belief"] < 0.3 else "you were not sure"
            body = f"{body} ({doubt})"

        results.append(
            Recalled(
                memory_id=m["id"],
                tier="sharp" if sharp else "hazy",
                text=body,
                gist=m["gist"],
                activation=s.a_all,
                breakdown={
                    "A": round(s.a_all, 3),
                    "A_detail": s.a_detail,
                    "B": round(s.base_all, 3),
                    "S": round(relevance, 3),
                    "G": graph.get(m["id"], 0.0),
                    "imp": m["importance"],
                    "F": activation.FIDELITY[source],
                    "noise": round(wobble, 3),
                    "superseded": superseded,
                    "effortful": effortful,
                    **({"M": round(tilt, 3)} if tilt is not None else {}),
                    **({"cue": cue} if cue else {}),
                    **({"drift": drift} if drift else {}),
                },
            )
        )

    results += elsewhere(conn, story_id, knower_id, text, now)
    results.sort(key=lambda r: r.activation, reverse=True)
    results = results[:LIMIT]
    if log and scene_id is not None:
        with conn:
            for r in results:
                if "elsewhere" in r.breakdown:
                    continue  # another life's memory: this scene is no rehearsal there
                if "drift" in r.breakdown:  # the slip becomes hers, the truth kept beside it
                    _plant(conn, story_id, knower_id, r, path[-1], scene_id)
                won = bool(r.breakdown["effortful"])
                conn.execute(
                    "INSERT INTO accesses(knower_id, memory_id, scene_id, kind, story_time, sharp,"
                    " weight, message_id) VALUES(?, ?, ?, 'recall', ?, ?, ?, ?)"
                    # one rehearsal per scene; only a successful strain upgrades it to a sharp one
                    " ON CONFLICT DO UPDATE SET sharp=1, weight=1.0 WHERE excluded.weight=1.0",
                    (
                        knower_id,
                        r.memory_id,
                        scene_id,
                        now,
                        r.tier == "sharp",
                        1.0 if won else 0.5,
                        path[-1]["id"],
                    ),
                )
    return results


def _human(conn: sqlite3.Connection) -> bool:
    """mind.recall (slice 6), guarded: unreadable means today's recall."""
    try:
        return features.enabled(conn, "mind.recall")
    except Exception as e:
        logging.getLogger(__name__).warning("recall effects off: %s", e)
        return False


def _mine(conn, m, knower_id: int, tier: str, live, on_path, now, scene_id, slip: bool):
    """(her version's words or None, the alt that drifts now or None), guarded: a failure
    renders the truth as before. A detail drifts only in a hazy memory with alts that is not
    locked, not canon, and has no version yet, by a roll fixed for the scene (note 14 D2)."""
    try:
        row = recollect.version(conn, knower_id, m["id"], live, on_path, now)
        if row is not None:
            return recollect.differs(row, m), None
        alts = recollect.alts_of(m)
        if (slip or tier != "hazy" or not alts or m["core_locked"] or m["pinned"]
                or m["importance"] >= recollect.CANON):  # fmt: skip
            return None, None
        p = recollect.drift_p(m["importance"], recollect.dial(conn, knower_id))
        if activation.hash01("drift", knower_id, m["id"], scene_id or 0) >= p:
            return None, None
        alt = alts[int(activation.hash01("alt", knower_id, m["id"], scene_id or 0) * len(alts))]
        return recollect.with_detail(m["gist"], alt["wrong"]), alt
    except Exception as e:
        logging.getLogger(__name__).warning("no version for memory %s: %s", m["id"], e)
        return None, None


def _plant(conn, story_id: int, knower_id: int, r: Recalled, at, scene_id: int) -> None:
    try:
        conn.execute("SAVEPOINT plant")
        m = conn.execute("SELECT * FROM memories WHERE id=?", (r.memory_id,)).fetchone()
        recollect.plant(conn, story_id, knower_id, m, r.breakdown["drift"], at, scene_id)
        conn.execute("RELEASE plant")
    except Exception as e:
        conn.execute("ROLLBACK TO plant")
        conn.execute("RELEASE plant")
        logging.getLogger(__name__).warning("slip not kept for %s: %s", r.memory_id, e)


def _cues(conn: sqlite3.Connection, m, here: set[int], knower_id: int, now: int) -> list[str]:
    """recollect.cues for this memory, from its stored people and place; guarded."""
    try:
        linked = [
            dict(r)
            for r in conn.execute(
                "SELECT e.id, e.kind, e.name FROM memory_entities me"
                " JOIN entities e ON e.id=me.entity_id WHERE me.memory_id=? ORDER BY e.id",
                (m["id"],),
            )
        ]
        return recollect.cues(linked, here, knower_id, m["emotion"], now - m["story_time"])
    except Exception as e:
        logging.getLogger(__name__).warning("no cues for memory %s: %s", m["id"], e)
        return []


# Clarity, one definition on every screen: how a memory would come back if it came up.
# A cue of middling relevance (S) that touches its people (G), with no noise; replies keep
# using the real cue of the moment.
CLARITY_CUE = {"relevance": 0.5, "graph": 1.0}


def inspect(
    conn: sqlite3.Connection, story_id: int, knower_id: int, *, now: int | None = None
) -> list[dict]:
    """Everything this character knows at story time `now` (default: the active leaf), and
    its clarity then. Read-only, nothing logged."""
    path = chat.active_path(conn, story_id)
    if now is None:
        now = path[-1]["story_time"] if path else 0
    live = db.live_runs(conn, story_id)
    live_sql, live_args = db.live_filter(live)
    know_sql, know_args = db.live_filter(live, "k.run_id")
    ours = live_scenes(conn, story_id, path)
    names = dict(
        conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)).fetchall()
    )
    human = _human(conn)
    floor = 0.0 if human else None  # a locked memory is never forgotten (slice 6)
    on_path = {p["id"] for p in path}
    cut = _cut(conn, story_id, knower_id) if human else set()
    epoch = conn.execute("SELECT epoch_offset_min FROM stories WHERE id=?", (story_id,)).fetchone()
    out = []
    for m in conn.execute(
        f"SELECT * FROM memories WHERE story_id=? AND story_time<=? AND {live_sql} ORDER BY id",
        [story_id, now, *live_args],
    ).fetchall():
        known = conn.execute(
            f"SELECT k.* FROM knowledge k WHERE k.knower_id=? AND k.memory_id=? AND {know_sql}"
            " AND k.learned_story_time<=? ORDER BY k.id DESC LIMIT 1",
            [knower_id, m["id"], *know_args, now],
        ).fetchone()
        if known is None and not m["common"]:
            continue  # not known yet, as of `now`
        source, superseded, s = _assess(
            conn, m, knower_id, known, now, ours, live,
            CLARITY_CUE["relevance"], CLARITY_CUE["graph"], 0.0, knobs.decay(conn, knower_id),
            floor,
        )  # fmt: skip
        out.append(
            {
                "memory_id": m["id"],
                "kind": m["kind"],
                "detail": m["detail"],
                "gist": m["gist"],
                "importance": m["importance"],
                "hidden": m["hidden"],
                "pinned": m["pinned"],
                "source": source,
                "told_by": names.get(known["told_by_id"]) if known else None,
                "belief": known["belief"] if known else 1.0,
                "tier": s.tier or "forgotten",
                "A": round(s.a_all, 3),
                "A_detail": round(s.a_detail, 3),
                "B": round(s.base_all, 3),
                "superseded": superseded,
                "story_time": m["story_time"],
                "valence": m["valence"],
                "alts": recollect.alts_of(m) or None,
                "core_locked": bool(m["core_locked"]),
                "version": (
                    _version_of(conn, m, knower_id, live, on_path, now, epoch[0]) if human else None
                ),
                "why_not": (
                    ("faded" if s.tier is None else "budget" if m["id"] in cut else None)
                    if human
                    else None
                ),
            }
        )
    return sorted(out, key=lambda r: r["A"], reverse=True)


def _version_of(conn, m, knower_id, live, on_path, now, epoch: int) -> dict | None:
    """The ledger's `version` (spec §8.3 slice 6): her own version when it is not the truth."""
    row = recollect.version(conn, knower_id, m["id"], live, on_path, now)
    if recollect.differs(row, m) is None:
        return None
    return {"text": row["text"], "basis": row["basis"], "since": clock.label(row["story_time"], epoch),
            "message_id": row["message_id"]}  # fmt: skip


def _cut(conn, story_id: int, knower_id: int) -> set[int]:
    """Memories recalled for her last prompt but cut for room: the app lost them, not she."""
    row = conn.execute(
        "SELECT memories FROM context_log WHERE story_id=? AND speaker_id=? ORDER BY id DESC",
        (story_id, knower_id),
    ).fetchone()
    if row is None or not row["memories"]:
        return set()
    return {m["memory_id"] for m in json.loads(row["memories"]) if m.get("rendered") == "dropped"}


def clarity(conn, story_id: int, knower_id: int, memory_id: int, path: list, live) -> str | None:
    """How she would recall this memory at the end of `path` if asked about it directly (the
    ledger's cue): "sharp", "hazy", or None (forgotten, or she never knew it). Read-only."""
    now = path[-1]["story_time"] if path else 0
    m = conn.execute("SELECT * FROM memories WHERE id=?", (memory_id,)).fetchone()
    know_sql, know_args = db.live_filter(live, "k.run_id")
    known = conn.execute(
        f"SELECT k.* FROM knowledge k WHERE k.knower_id=? AND k.memory_id=? AND {know_sql}"
        " ORDER BY k.id DESC LIMIT 1",
        [knower_id, memory_id, *know_args],
    ).fetchone()
    if m is None or (known is None and not m["common"]):
        return None
    _, _, s = _assess(
        conn, m, knower_id, known, now, live_scenes(conn, story_id, path), live,
        CLARITY_CUE["relevance"], CLARITY_CUE["graph"], 0.0, knobs.decay(conn, knower_id),
    )  # fmt: skip
    return s.tier


# --- what another story, linked to this one, still leaves her with ------------------------------

CARRIES = ("continuation", "shared_universe")  # a reference link is a note, not a memory
ELSEWHERE_LIMIT = 4  # of a past life, only what is most alive comes up
# `inspect` asks "if she were asked about this directly?" and hands every memory a fixed cue. Here
# the cue is the line being said, so that one comes off and the real one goes on, and what is
# remembered from another life is a step less sure than what was lived here (FIDELITY's "told").
CLARITY_BONUS = (
    activation.W_RELEVANCE * CLARITY_CUE["relevance"] + activation.W_GRAPH * CLARITY_CUE["graph"]
)
ELSEWHERE_FIDELITY = activation.FIDELITY["told"]


def _other_self(conn: sqlite3.Connection, knower_id: int, story_id: int) -> int | None:
    """The same person in another story: the same library item, or one adopted into it."""
    me = conn.execute("SELECT * FROM entities WHERE id=?", (knower_id,)).fetchone()
    if me is None:
        return None
    item = me["lib_item_id"]
    if item is None and me["origin_entity_id"]:
        item = conn.execute(
            "SELECT lib_item_id FROM entities WHERE id=?", (me["origin_entity_id"],)
        ).fetchone()["lib_item_id"]
    if item is None:
        return None
    row = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND hidden=0 AND lib_item_id=? LIMIT 1",
        (story_id, item),
    ).fetchone()
    return row["id"] if row else None


def elsewhere(
    conn: sqlite3.Connection, story_id: int, knower_id: int, text: str, now: int
) -> list[Recalled]:
    """Memories this character holds in the stories this one points at. The link's offset is how
    long after that story's last line this one begins, so a year between them is a year of
    forgetting: what comes back is what that self would still recall by now, and it says where
    it is from.

    ponytail: one `inspect` per linked story, and the words are matched plainly; if a library
    ever links dozens of stories, rank these the way `recall` ranks the story's own.
    """
    links = conn.execute(
        "SELECT l.to_story_id, l.kind, l.offset_min, s.title FROM story_links l"
        " JOIN stories s ON s.id=l.to_story_id WHERE l.from_story_id=?",
        (story_id,),
    ).fetchall()
    words = {w for w in re.findall(r"[^\W_]+", text.lower()) if len(w) > 2 and w not in STOPWORDS}
    out: list[Recalled] = []
    seen: set[int] = set()  # a pair linked twice is still one past
    for link in links:
        if link["kind"] not in CARRIES:
            continue
        other = _other_self(conn, knower_id, link["to_story_id"])
        if other is None:
            continue  # she was never there, so there is nothing of hers to remember
        there = chat.active_path(conn, link["to_story_id"])
        ended = there[-1]["story_time"] if there else 0
        since = ended + link["offset_min"] + now  # where we are, on that story's clock
        for m in inspect(conn, link["to_story_id"], other, now=since):
            if m["hidden"] or m["memory_id"] in seen:
                continue
            said = {w.lower() for w in re.findall(r"[^\W_]+", f"{m['detail']} {m['gist']}")}
            overlap = len(words & said) / len(words) if words else 0.0
            if not overlap:
                continue  # not what is being talked about
            shift = activation.W_RELEVANCE * overlap - CLARITY_BONUS + ELSEWHERE_FIDELITY
            a_all, a_detail = m["A"] + shift, m["A_detail"] + shift
            if a_detail >= activation.SHARP_AT:
                tier, body = "sharp", m["detail"]
            elif a_all >= activation.HAZY_AT:
                tier, body = "hazy", m["gist"]
            else:
                continue  # that far back, she has lost it
            seen.add(m["memory_id"])
            out.append(
                Recalled(
                    memory_id=m["memory_id"],
                    tier=tier,
                    text=f"(from {link['title']}) {body}",
                    gist=m["gist"],
                    activation=a_all,
                    breakdown={
                        "A": round(a_all, 3),
                        "A_detail": round(a_detail, 3),
                        "B": m["B"],
                        "S": round(overlap, 3),
                        "G": 0.0,
                        "imp": m["importance"],
                        "F": ELSEWHERE_FIDELITY,
                        "effortful": None,
                        "superseded": m["superseded"],
                        "elsewhere": link["to_story_id"],
                    },
                )
            )
    out.sort(key=lambda r: r.activation, reverse=True)
    return out[:ELSEWHERE_LIMIT]
