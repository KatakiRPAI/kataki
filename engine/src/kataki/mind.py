"""How one reply came about, for Backstage's Mind graph: what the speaker heard and saw, where and
when it was, what recall weighed and what reached the prompt, how they felt and what they
doubted, the face they chose, and what they said.

Read-only, and only what the engine recorded (docs/specs/2026-09-23-mind-graph.md): a step it
keeps no row for is left out, never drawn with made-up numbers. "Gold" is what reached the prompt
the reply was written from; the rest was weighed and cut. Beliefs and feelings are the ones held
when they replied: only memory reads that had finished by then count.
"""

import json
import logging
import math
import sqlite3

from kataki import chat, clock, db, honesty
from kataki.signals import FEELINGS

RECALLS, FEELS, BELIEFS = 4, 3, 2  # at most this many of each; the rest are counted
WHY = {  # why this speaker answered (turns.speaker_why), in words
    "picked": "You picked {who} to answer",
    "named": "{by} named {who}",
    "last": "{who} spoke last of those who heard",
    "quietest": "Nothing waiting: {who}, the quietest here",
    "urgent": "{who} was stirred up",
    "wants_in": "{who} had something to say",
    "balance": "{who}'s turn: the others had spoken more",
    "retake": "Another take on {who}'s reply",
    "narrator": "You asked the narrator",
    "alone": "No one here but the narrator",
}


def _short(text: str, n: int = 70) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def mind(conn: sqlite3.Connection, message_id: int) -> dict | None:
    """The graph for one reply, or None when the message is not a reply."""
    m = chat.get_message(conn, message_id)
    if m is None or m["role"] != "assistant":
        return None
    story = conn.execute("SELECT * FROM stories WHERE id=?", (m["story_id"],)).fetchone()
    epoch, who = story["epoch_offset_min"], m["speaker_id"]
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story["id"],)))
    path = chat.path_to(conn, message_id)
    nodes: list[dict] = []
    links: list[dict] = []
    more: dict[str, int] = {}

    def node(id, column, kind, title, text, weight=None, gold=True, detail=None) -> str:
        nodes.append({"id": id, "column": column, "kind": kind, "title": title, "text": text,
                      "weight": weight, "gold": gold, "detail": detail})  # fmt: skip
        return id

    def link(a: str, b: str, gold: bool) -> None:
        links.append({"from": a, "to": b, "gold": gold})

    # --- IN: what reached them since they last spoke
    before = path[:-1]
    own = [i for i, x in enumerate(before) if who is not None and x["speaker_id"] == who]
    since = before[own[-1] + 1 :] if own else before
    hearing = chat.hearing(conn, path, who) if who is not None else {}
    heard = [
        x
        for x in since
        if x["role"] != "system"
        and not x["hidden"]
        and (hearing.get(x["id"]) == "heard" if who is not None else chat.audience_of(x) is None)
    ]
    cue = [
        node(f"h{x['id']}", "in", "heard", "Heard",
             f"{names.get(x['speaker_id'], 'Narrator')}: “{_short(x['text'], 60)}”", 1.0)
        for x in heard[-2:]
    ]  # fmt: skip
    ins = list(cue)
    if since:
        marks = ",".join("?" * len(since))
        for r in conn.execute(
            f"SELECT id, entity_id, present FROM presence WHERE message_id IN ({marks})"
            " AND entity_id IS NOT ? ORDER BY id",
            [*(x["id"] for x in since), who],
        ):
            said = "came in" if r["present"] else "left"
            ins.append(node(f"p{r['id']}", "in", "saw", "Saw", f"{names[r['entity_id']]} {said}"))
    scene = conn.execute("SELECT place_id FROM scenes WHERE id IS ?", (m["scene_id"],)).fetchone()
    minute = (m["story_time"] + epoch) % clock.DAY
    part = next(p for end, p in clock.PARTS if minute < end)
    place = names.get(scene["place_id"]) if scene else None
    ins.append(node("place", "in", "place", "Place", f"{place or 'Nowhere named'} · {part}"))
    moments = json.loads(story["overrides"]).get("moments", [])
    when = clock.date(m["story_time"], epoch, moments)
    gap = m["story_time"] - before[own[-1]]["story_time"] if own else 0
    if gap >= clock.DAY:
        when += f" · {clock.spell(gap).lower()} since they last spoke"
    ins.append(node("time", "in", "time", "Time", when))

    # --- SENSE: why they answered and what recall searched with (recorded since 2026-09-23)
    gen = json.loads(m["gen"]) if m["gen"] else {}
    trace = gen.get("trace") or {}
    if why := trace.get("why"):
        by = names.get(heard[-1]["speaker_id"], "You") if heard else "You"
        text = WHY.get(why, why).format(who=names.get(who, "the narrator"), by=by)
        attention = node("why", "sense", "attention", "Attention", text)
        if why in ("named", "last") and cue:
            link(cue[-1], attention, True)
    if trace.get("cue"):
        searched = node("cue", "sense", "cue", "Cue", f"“{_short(trace['cue'], 60)}”")
        for h in cue:
            link(h, searched, True)
        cue = [searched]  # recall hangs off what it searched with

    # --- INSIDE: what recall weighed, what they doubted, how they felt, who they are
    log = conn.execute(
        "SELECT sections, memories FROM context_log WHERE message_id=? ORDER BY id DESC LIMIT 1",
        (message_id,),
    ).fetchone()
    sections = {s["name"]: s for s in json.loads(log["sections"])} if log else {}
    recalled = json.loads(log["memories"]) if log else []
    ranked = sorted(recalled, key=lambda r: (r["rendered"] == "dropped", -r.get("A", 0)))
    inside: list[tuple[str, bool]] = []
    for r in ranked[:RECALLS]:
        row = conn.execute(
            "SELECT detail, gist FROM memories WHERE id=?", (r["memory_id"],)
        ).fetchone()
        if row is None:
            continue
        gold = r["rendered"] != "dropped"
        text = row["detail"] if r["rendered"] == "detail" else row["gist"]
        detail = {k: r.get(k) for k in ("memory_id", "tier", "rendered", "A", "B", "S", "G", "imp")}
        weight = round(1 / (1 + math.exp(-r.get("A", 0))), 2)  # activation, squashed to 0..1
        text = f"{_short(text, 56)} · {r['tier']}"
        nid = node(f"m{r['memory_id']}", "inside", "recall", "Recall", text, weight, gold, detail)
        inside.append((nid, gold))
        for h in cue:
            link(h, nid, gold)
    if len(recalled) > RECALLS:
        more["recall"] = len(recalled) - RECALLS

    # what they held when they replied: the reads on this branch that had finished by then
    runs = db.live_runs(conn, story["id"], leaf_id=message_id)
    if runs:
        marks = ",".join("?" * len(runs))
        runs = {r[0] for r in conn.execute(
            f"SELECT id FROM extraction_runs WHERE id IN ({marks}) AND to_message_id < ?",
            [*runs, message_id],
        )}  # fmt: skip
    live_sql, live_args = db.live_filter(runs)
    know_sql, know_args = db.live_filter(runs, "k.run_id")
    if who is not None:
        doubts = 0
        for r in ranked:
            if r["rendered"] == "dropped" or doubts == BELIEFS:
                continue
            k = conn.execute(
                "SELECT k.belief, m.gist FROM knowledge k JOIN memories m ON m.id=k.memory_id"
                f" WHERE k.knower_id=? AND k.memory_id=? AND {know_sql} ORDER BY k.id DESC LIMIT 1",
                [who, r["memory_id"], *know_args],
            ).fetchone()
            if k and k["belief"] < 0.7:
                doubts += 1
                b = node(f"b{r['memory_id']}", "inside", "belief", "Belief",
                         f"Doubts it: {_short(k['gist'], 50)}", round(k["belief"], 2))  # fmt: skip
                link(f"m{r['memory_id']}", b, True)
                inside.append((b, True))

        feelings = {}  # the latest edge to each person
        for e in conn.execute(
            f"SELECT * FROM edges WHERE story_id=? AND src_id=? AND {live_sql} ORDER BY id",
            [story["id"], who, *live_args],
        ):
            feelings[e["dst_id"]] = e
        shown = [e for e in feelings.values() if not e["ended"]]
        for e in shown[:FEELS]:
            rel = e["rel"].strip().lower()
            tone = next((t for starts, _, t in FEELINGS if rel.startswith(starts)), "feeling")
            other = "you" if e["dst_id"] == story["persona_entity_id"] else names[e["dst_id"]]
            # gold if it reached the prompt (prompts log their feelings since 2026-09-23)
            felt = e["id"] in sections.get("tail", {}).get("feelings", [])
            detail = {"tone": tone, "note": e["note"], "in_prompt": felt}
            text = f"{rel.capitalize()} {other}"
            fid = node(f"f{e['id']}", "inside", "feeling", "Feeling", text, None, felt, detail)
            inside.append((fid, felt))
        if len(shown) > FEELS:
            more["feeling"] = len(shown) - FEELS
        try:  # what the reply was written with; stored JSON, so a bad shape costs only itself
            if felt := gen.get("mind"):  # the mood (minds spec §8.2)
                text = f"{felt['feels']} · showing {felt['shows']}"
                mood = node("mood", "inside", "mood", "Mood", text, None, True, felt)
                inside.append((mood, True))
        except Exception as e:
            logging.getLogger(__name__).warning("mood not shown: %s", e)
        try:
            for b in gen.get("bonds") or []:  # the ledger (§8.3)
                other = "you" if b["you"] else b["other"]
                detail = {"source": "ledger", **b}
                text = f"Toward {other}: {b['words']}"
                tie = node(
                    f"o{b['other_id']}", "inside", "feeling", "Feeling", text, None, True, detail
                )
                inside.append((tie, True))
        except Exception as e:
            logging.getLogger(__name__).warning("ledger not shown: %s", e)
        try:  # the thought the reply was written from (slice 3: Mind 5, cheaply)
            said = gen.get("thought") or {}
            caused = said.get("from") == "before"  # an afterthought was read off the reply
            th = None
            if said.get("thinks"):
                title = "Thought" if caused else "Afterthought"
                th = node("thought", "inside", "thought", title, said["thinks"], None, caused, said)
            if said.get("wants"):
                want = node(
                    "intent", "decide", "intent", "Intent", said["wants"], None, caused, said
                )
                if th:
                    link(th, want, caused)
                link(want, "spoke", caused)
            elif th:
                inside.append((th, caused))
        except Exception as e:
            logging.getLogger(__name__).warning("thought not shown: %s", e)
        try:  # what they decided to do about the truth, before the reply (slice 4)
            if (said := gen.get("honest")) and said.get("move"):
                row = conn.execute(
                    "SELECT cover FROM secrets WHERE id IS ?", (said.get("secret"),)
                ).fetchone()
                cover = row["cover"] if row else None
                label = honesty.LABEL.get(said["move"], said["move"])
                lied = cover and said["move"] in honesty.LIES
                text = label[0].upper() + label[1:] + (f": “{cover}”" if lied else "")
                detail = {**said, "label": label, "cover": cover}
                honest = node("honest", "decide", "honest", "Honest?", text, None, True, detail)
                link(honest, "spoke", True)
        except Exception as e:
            logging.getLogger(__name__).warning("honesty not shown: %s", e)
        try:  # what she wanted, and her body, when the reply was written (slice 7)
            if (said := gen.get("agenda")) and said.get("text"):
                goal = node("goal", "decide", "goal", "Goal", f"Wants: {said['text']}",
                            None, True, said)  # fmt: skip
                link(goal, "spoke", True)
            if (need := gen.get("need")) and need.get("text"):
                body = node("need", "inside", "need", "Body", need["text"], None, True, need)
                inside.append((body, True))
        except Exception as e:
            logging.getLogger(__name__).warning("goal not shown: %s", e)
        try:  # what she has made of her story, when a reflection rode in (slice 8)
            if (grown := gen.get("growth")) and grown.get("text"):
                ring = node(
                    "growth", "inside", "growth", "Growth", grown["text"], None, True, grown
                )
                inside.append((ring, True))
        except Exception as e:
            logging.getLogger(__name__).warning("growth not shown: %s", e)

        card = conn.execute("SELECT description FROM entities WHERE id=?", (who,)).fetchone()
        if card and card["description"]:
            gold = sections.get("cards", {}).get("tokens", 0) > 0
            first = _short(card["description"].strip().splitlines()[0], 60)
            p = node("persona", "inside", "persona", "Persona", first, gold=gold)
            inside.append((p, gold))

    # --- DECIDE, and what they said
    ends = "spoke"
    if m["expression"]:
        ends = node("face", "decide", "expression", "Expression", m["expression"])
        link(ends, "spoke", True)
    for nid, gold in inside:
        if gold:
            link(nid, ends, True)
    for nid in ins:
        link(nid, "spoke", True)
    return {
        "message_id": message_id,
        "speaker": {"id": who, "name": names.get(who, "Narrator")},
        "clock": clock.label(m["story_time"], epoch),
        "date": clock.date(m["story_time"], epoch, moments),
        "nodes": nodes,
        "links": links,
        "more": more,
        "spoke": {
            "text": m["text"],
            "model": gen.get("model"),
            "tokens": (gen.get("usage") or {}).get("completion_tokens"),
            "ms": (trace.get("ms") or {}).get("total"),
            "timings": trace.get("ms") or {},
        },
    }


def feelings(conn: sqlite3.Connection, story_id: int, who: int, about: int) -> dict:
    """How `who` has come to feel about `about` across the story, counted at each memory read on
    this branch (docs/specs/2026-09-23-mind-graph.md §4.3). Relationships carry words, not
    numbers, so this is a count and says so: warmth is +1 for each warm feeling filed and -1 for
    each cold one; trust +1 for trust and -1 for distrust or suspicion; doubt is how many of
    `about`'s claims `who` disbelieves (belief < 0.7). Skips of a day or more are marked."""
    story = conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()
    epoch = story["epoch_offset_min"]
    moments = json.loads(story["overrides"]).get("moments", [])
    path = chat.active_path(conn, story_id)
    when = {m["id"]: m["story_time"] for m in path}
    runs = sorted(db.live_runs(conn, story_id))
    marks = ",".join("?" * len(runs)) or "NULL"
    ends = dict(
        conn.execute(f"SELECT id, to_message_id FROM extraction_runs WHERE id IN ({marks})", runs)
    )
    edges = conn.execute(
        f"SELECT rel, run_id FROM edges WHERE src_id=? AND dst_id=? AND run_id IN ({marks})"
        " ORDER BY id",
        [who, about, *runs],
    ).fetchall()
    claims = conn.execute(
        "SELECT k.memory_id, k.belief, k.run_id FROM knowledge k"
        " JOIN memories m ON m.id=k.memory_id"
        f" WHERE k.knower_id=? AND m.kind='claim' AND m.asserted_by=? AND k.run_id IN ({marks})"
        " ORDER BY k.id",
        [who, about, *runs],
    ).fetchall()
    points, warmth, trust, belief = [], 0, 0, {}
    for run in runs:
        for e in (e for e in edges if e["run_id"] == run):
            rel = e["rel"].strip().lower()
            if rel.startswith("trust"):
                trust += 1
            elif rel.startswith(("distrust", "suspicious")):
                trust -= 1
            else:
                tone = next((t for starts, _, t in FEELINGS if rel.startswith(starts)), None)
                warmth += {"warm": 1, "feeling": -1}.get(tone, 0)
        belief |= {k["memory_id"]: k["belief"] for k in claims if k["run_id"] == run}
        t = when.get(ends[run])
        if t is None:
            continue  # read on another branch's line
        points.append({
            "run": run, "story_time": t, "date": clock.date(t, epoch, moments),
            "warmth": warmth, "trust": trust, "doubt": sum(b < 0.7 for b in belief.values()),
        })  # fmt: skip
    skips = [
        {"story_time": m["story_time"], "label": f"{clock.spell(m['skip_minutes'])} later"}
        for m in path
        if m["skip_minutes"] >= clock.DAY
    ]
    return {"who": who, "about": about, "points": points, "skips": skips, "counted": True}
