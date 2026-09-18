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

import re
import sqlite3

from kataki import activation, chat, db
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


def _assess(conn, m, knower_id, known, now, live_scenes, live, relevance, graph, wobble, d):
    """One memory, one knower: (how they know it, is it superseded, activation score)."""
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
    )
    return source, superseded, s


def _live_scenes(conn, story_id: int, path: list) -> set[int]:
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
) -> list[Recalled]:
    path = chat.path_to(conn, leaf_id) if leaf_id else chat.active_path(conn, story_id)
    if not path:
        return []
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
        return []
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
    live_scenes = _live_scenes(conn, story_id, path)

    results = []
    for m in rows:
        if window_start is not None and (m["to_message_id"] or 0) >= window_start:
            continue  # the model can already read this in the chat itself
        known = conn.execute(
            f"SELECT k.* FROM knowledge k WHERE k.knower_id=? AND k.memory_id=? AND {know_sql}"
            " ORDER BY k.id DESC LIMIT 1",
            [knower_id, m["id"], *know_args],
        ).fetchone()
        if known is None and not m["common"]:
            continue  # the hard gate: this character does not know it

        relevance = relevance_of(m["id"])
        wobble = activation.noise(knower_id, m["id"], scene_id or 0) if noise else 0.0
        source, superseded, s = _assess(
            conn, m, knower_id, known, now, live_scenes, live, relevance, graph.get(m["id"], 0.0),
            wobble, d,
        )  # fmt: skip
        if s.tier is None:
            continue  # forgotten, for now

        effortful = None
        if s.tier == "hazy" and m["id"] in pressed:
            effortful = activation.effortful_recall(s.a_detail, knower_id, m["id"], scene_id or 0)
        sharp = s.tier == "sharp" or bool(effortful)
        body = m["detail"] if sharp else m["gist"]
        if effortful:
            body = f"(after straining to recall) {body}"
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
                },
            )
        )

    results.sort(key=lambda r: r.activation, reverse=True)
    results = results[:LIMIT]
    if log and scene_id is not None:
        with conn:
            for r in results:
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


def inspect(conn: sqlite3.Connection, story_id: int, knower_id: int) -> list[dict]:
    """Everything this character knows, and how it would come back right now with no cue at
    all. The inspector's view: read-only, no noise, nothing logged."""
    path = chat.active_path(conn, story_id)
    now = path[-1]["story_time"] if path else 0
    live = db.live_runs(conn, story_id)
    live_sql, live_args = db.live_filter(live)
    know_sql, know_args = db.live_filter(live, "k.run_id")
    live_scenes = _live_scenes(conn, story_id, path)
    names = dict(
        conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)).fetchall()
    )
    out = []
    for m in conn.execute(
        f"SELECT * FROM memories WHERE story_id=? AND story_time<=? AND {live_sql} ORDER BY id",
        [story_id, now, *live_args],
    ).fetchall():
        known = conn.execute(
            f"SELECT k.* FROM knowledge k WHERE k.knower_id=? AND k.memory_id=? AND {know_sql}"
            " ORDER BY k.id DESC LIMIT 1",
            [knower_id, m["id"], *know_args],
        ).fetchone()
        if known is None and not m["common"]:
            continue
        source, superseded, s = _assess(
            conn, m, knower_id, known, now, live_scenes, live, 0.0, 0.0, 0.0, activation.DECAY
        )
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
            }
        )
    return sorted(out, key=lambda r: r["A"], reverse=True)
