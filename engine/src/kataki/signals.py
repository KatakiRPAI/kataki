"""What each line of a story signals, for the Scene: who heard it and how clearly they will
remember it (receipts), what it meant to someone (callouts), what a reply recalled, and what a
time skip made them forget. Read-only; the engine writes every sentence.

ponytail: everything is recomputed on each call (the demo story takes a few ms); cache on the
story version, or batch the clarity queries, if a long story gets slow.
"""

import json
import sqlite3
from dataclasses import dataclass

from kataki import chat, clock, db, retrieve

ORDER = {"sharp": 0, "hazy": 1, "forgotten": 2}  # the best clarity wins a receipt
PRONOUNS = {  # subject, possessive
    "she": ("she", "Her"),
    "he": ("he", "His"),
    "they": ("they", "Their"),
}
# how an AI character's feeling about someone reads: (rel prefixes, text with {src} and {dst},
# tone). The tone colours the reaction: warm (sage), mood (sky), or a feeling (rose).
FEELINGS = [
    (("distrust", "suspicious"), "{src} is suspicious of {dst}", "feeling"),
    (("trust",), "{src} trusts {dst} a little more", "warm"),
    (("dislike", "resent", "annoyed", "angry", "hate"), "{src} didn't like that", "feeling"),
    (("like", "fond", "grateful", "warm"), "{src} warmed to {dst}", "warm"),
    (("glad", "happy"), "{src} is glad to see {dst}", "warm"),
    (("worried", "afraid", "fear", "scared", "concerned"), "{src} is worried for {dst}", "mood"),
]


def listed(names: list[str]) -> str:
    """'Mira', 'Mira and Tobin', 'Mira, Tobin and Ilsa'."""
    return f"{', '.join(names[:-1])} and {names[-1]}" if len(names) > 1 else "".join(names)


@dataclass
class Scene:
    """What every signal needs, worked out once per request."""

    conn: sqlite3.Connection
    story: sqlite3.Row
    path: list
    ai: list[int]  # the AI characters of the story
    names: dict[int, str]
    hearing: dict[int, dict[int, str]]  # character -> message -> said/heard/away/whisper/thought
    clarity: dict[int, dict[int, str]]  # character -> memory -> tier, as of now
    from_library: dict[int, int | None]  # entity -> the library item it came from
    live: set[int]
    read_to: int

    def pronoun(self, entity_id: int) -> tuple[str, str]:
        row = self.conn.execute(
            "SELECT i.data FROM entities e JOIN lib_items i ON i.id=e.lib_item_id WHERE e.id=?",
            (entity_id,),
        ).fetchone()
        return PRONOUNS.get(json.loads(row[0]).get("pronouns") if row else None, PRONOUNS["they"])

    def person(self, entity_id: int) -> str:
        """Their name, or "you" for the persona."""
        return "you" if entity_id == self.story["persona_entity_id"] else self.names[entity_id]

    def memories(self, where: str = "1", args: tuple = ()) -> list[sqlite3.Row]:
        live_sql, live_args = db.live_filter(self.live)
        return self.conn.execute(
            f"SELECT * FROM memories WHERE story_id=? AND hidden=0 AND {live_sql} AND {where}"
            " ORDER BY id",
            [self.story["id"], *live_args, *args],
        ).fetchall()


def summary(receipts: list[dict], names: dict[int, str]) -> str:
    """The quiet sentence under a line: 'Mira will remember · Tobin wasn't there'."""

    def who(state: str, why: str | None = None) -> list[str]:
        return [names[r["id"]] for r in receipts if r["state"] == state and r.get("why") == why]

    parts = []
    if sharp := who("sharp"):
        parts.append(f"{listed(sharp)} will remember")
    if hazy := who("hazy"):
        parts.append(f"{listed(hazy)} {'remembers' if len(hazy) == 1 else 'remember'} it vaguely")
    if gone := who("forgotten"):
        parts.append(f"{listed(gone)} {'has' if len(gone) == 1 else 'have'} forgotten")
    if heard := who("heard"):
        parts.append(f"Heard by {listed(heard)}")
    if away := who("absent", "away"):
        parts.append(f"{listed(away)} {'wasn' if len(away) == 1 else 'weren'}'t there")
    if missed := who("absent", "whisper"):
        parts.append(f"{listed(missed)} didn't hear")
    return " · ".join(parts)


def _receipts(s: Scene) -> dict[int, list[dict]]:
    """Per line, per AI character: heard (pending until a live run reads it), then the best
    clarity of the memories anchored to that line which they know; or absent from your line
    while they had been following the scene."""
    anchored: dict[int, list[int]] = {}
    for m in s.memories("message_id IS NOT NULL"):
        anchored.setdefault(m["message_id"], []).append(m["id"])
    out: dict[int, list[dict]] = {}
    following = dict.fromkeys(s.ai, False)  # heard something in this scene since a big skip
    scene = object()
    for m in s.path:
        if m["scene_id"] != scene or m["skip_minutes"] >= clock.DAY:
            scene, following = m["scene_id"], dict.fromkeys(s.ai, False)
        receipts = []
        for c in s.ai:
            how = s.hearing[c][m["id"]]
            if m["hidden"] or m["role"] == "system":
                pass
            elif how in ("said", "heard"):
                if m["id"] > s.read_to:
                    receipts.append({"id": c, "state": "heard", "pending": True})
                else:
                    tiers = [
                        s.clarity[c][x] for x in anchored.get(m["id"], []) if x in s.clarity[c]
                    ]
                    best = min(tiers, key=ORDER.__getitem__) if tiers else "heard"
                    receipts.append({"id": c, "state": best})
            elif m["role"] == "user" and how in ("away", "whisper") and following[c]:
                receipts.append({"id": c, "state": "absent", "why": how})
            if how in ("said", "heard"):
                following[c] = True
        if receipts:
            out[m["id"]] = receipts
    return out


def _callouts(s: Scene) -> dict[int, list[dict]]:
    """Per line: the memory worth remembering, whether a lie was believed, and feelings."""
    on_path = {m["id"]: m for m in s.path}
    out: dict[int, list[dict]] = {}

    def add(
        key,
        message_id,
        kind,
        who,
        text,
        reason=None,
        faded=False,
        memory_id=None,
        run=None,
        gist=None,
        tone=None,  # a memory or a belief is its own tone
    ):
        out.setdefault(message_id, []).append(
            {"key": key, "kind": kind, "tone": tone or kind, "who": who, "text": text,
             "reason": reason, "faded": faded, "memory_id": memory_id, "run": run, "gist": gist}
        )  # fmt: skip

    # memory: the most important thing on the line that someone will keep
    best: dict[int, tuple] = {}
    for m in s.memories("kind != 'claim' AND importance >= 7 AND message_id IS NOT NULL"):
        who = [c for c in s.ai if s.clarity[c].get(m["id"]) in ("sharp", "hazy")]
        if who and m["message_id"] in on_path:
            key = (m["importance"], m["id"])
            if m["message_id"] not in best or key > best[m["message_id"]][0]:
                best[m["message_id"]] = (key, m, who)
    for message_id, (_, m, who) in best.items():
        faded = not any(s.clarity[c][m["id"]] == "sharp" for c in who)
        text = f"{listed([s.names[c] for c in who])} will remember this"
        add(f"m{m['id']}", message_id, "memory", who, text, faded=faded, memory_id=m["id"],
            run=m["run_id"], gist=m["gist"])  # fmt: skip

    # belief: a lie on your line, and how each hearer took it
    know_sql, know_args = db.live_filter(s.live)
    for claim in s.memories("kind='claim' AND is_true=0 AND message_id IS NOT NULL"):
        line = on_path.get(claim["message_id"])
        if line is None or line["role"] != "user":
            continue
        heard = s.conn.execute(
            f"SELECT knower_id, belief FROM knowledge WHERE memory_id=? AND {know_sql} ORDER BY id",
            [claim["id"], *know_args],
        ).fetchall()
        truth = s.conn.execute(
            "SELECT detail FROM memories WHERE id=?", (claim["contradicts_id"],)
        ).fetchone()
        for k in {k["knower_id"]: k for k in heard}.values():  # the latest row per hearer
            c = k["knower_id"]
            if c not in s.ai or c == claim["asserted_by"]:
                continue
            name, (subject, possessive) = s.names[c], s.pronoun(c)
            text = (
                f"{name} knows that's not true" if k["belief"] < 0.3
                else f"{name} has {possessive.lower()} doubts" if k["belief"] < 0.7
                else f"{name} believed you"
            )  # fmt: skip
            tier = s.clarity[c].get(claim["contradicts_id"]) if truth else None
            hazy = f"{possessive} memory of it has gone hazy, so {subject} can be talked out of it."
            reason = (
                f"{name} remembers it clearly: “{truth['detail']}”" if tier == "sharp"
                else hazy if tier == "hazy"
                else f"{name} has no memory of it."
            )  # fmt: skip
            # one per hearer, so the key carries them both
            add(f"b{claim['id']}.{c}", line["id"], "belief", [c], text, reason,
                memory_id=claim["id"], run=claim["run_id"], gist=claim["gist"])  # fmt: skip

    # feeling: an AI character's feeling about someone, on the line they shared in that read
    run_sql, run_args = db.live_filter(s.live, "e.run_id")
    for edge in s.conn.execute(
        f"SELECT e.*, r.to_message_id FROM edges e JOIN extraction_runs r ON r.id=e.run_id"
        f" WHERE e.story_id=? AND {run_sql} ORDER BY e.id",
        [s.story["id"], *run_args],
    ):
        if edge["src_id"] not in s.ai:
            continue
        shared = s.conn.execute(
            "SELECT m.id, m.message_id FROM memories m WHERE m.run_id=? AND m.message_id IS NOT"
            " NULL AND EXISTS(SELECT 1 FROM memory_entities WHERE memory_id=m.id AND entity_id=?)"
            " AND EXISTS(SELECT 1 FROM memory_entities WHERE memory_id=m.id AND entity_id=?)"
            " ORDER BY m.message_id DESC, m.id DESC LIMIT 1",
            (edge["run_id"], edge["src_id"], edge["dst_id"]),
        ).fetchone()
        at = shared["message_id"] if shared else edge["to_message_id"]
        if at not in on_path:
            continue
        rel = edge["rel"].strip().lower()
        src, dst = s.names[edge["src_id"]], s.person(edge["dst_id"])
        text, tone = next(
            ((t, tone) for starts, t, tone in FEELINGS if rel.startswith(starts)),
            ("{src} {rel} {dst}", "feeling"),
        )
        text = (
            f"{src} no longer {rel} {dst}"
            if edge["ended"]
            else text.format(src=src, dst=dst, rel=rel)
        )
        add(
            f"f{edge['id']}",
            at,
            "feeling",
            [edge["src_id"]],
            text,
            edge["note"],
            memory_id=shared and shared["id"],
            run=edge["run_id"],
            tone=tone,
        )
    return out


def _recall(s: Scene) -> dict[int, dict]:
    """Per reply: what its speaker recalled, when something worth a spark came back (hazy,
    strained for, or important)."""
    on_path = {m["id"] for m in s.path}
    know_sql, know_args = db.live_filter(s.live)
    out: dict[int, dict] = {}
    for log in s.conn.execute(
        "SELECT message_id, speaker_id, memories FROM context_log WHERE story_id=?"
        " AND message_id IS NOT NULL AND speaker_id IS NOT NULL ORDER BY id",
        (s.story["id"],),
    ):
        if log["message_id"] not in on_path:
            continue
        shown = [x for x in json.loads(log["memories"]) if x["rendered"] != "dropped"]
        spark = [x for x in shown if x["tier"] == "hazy" or x.get("effortful") or x["imp"] >= 7]
        if not spark:
            out.pop(log["message_id"], None)  # a later retake of this reply may have none
            continue
        items = []
        for x in (spark + [x for x in shown if x not in spark])[:3]:
            memory = s.conn.execute(
                "SELECT * FROM memories WHERE id=?", (x["memory_id"],)
            ).fetchone()
            if memory is None:
                continue  # its run was discarded since
            known = s.conn.execute(
                f"SELECT * FROM knowledge WHERE knower_id=? AND memory_id=? AND {know_sql}"
                " ORDER BY id DESC LIMIT 1",
                [log["speaker_id"], memory["id"], *know_args],
            ).fetchone()
            if known:
                source = known["source"]
                if source == "told" and known["told_by_id"]:
                    source = f"told by {s.names.get(known['told_by_id'], 'someone')}"
                when = clock.label(known["learned_story_time"], s.story["epoch_offset_min"])
                how = f"{source} {when}"
            else:
                how = "common knowledge"
            items.append(
                {
                    "memory_id": memory["id"],
                    "tier": x["tier"],
                    "text": memory["gist"] if x["tier"] == "hazy" else memory["detail"],
                    "how": how,
                    "detail": memory["detail"],
                }
            )
        manner = (
            "after straining" if any(x.get("effortful") for x in shown)
            else "vaguely" if any(x["tier"] == "hazy" for x in shown)
            else "clearly"
        )  # fmt: skip
        out[log["message_id"]] = {
            "speaker": log["speaker_id"],
            "title": f"{s.names.get(log['speaker_id'], 'They')} remembered, {manner}",
            "items": items,
        }
    return out


def _skips(s: Scene) -> dict[int, dict]:
    """Per line that skips a day or more, per AI character there: of what they knew before it,
    how much went from sharp to hazy, and how much faded out, over the skip."""
    epoch = s.story["epoch_offset_min"]
    out: dict[int, dict] = {}
    previous = 0  # the clock on the line before
    for m in s.path:
        last, previous = previous, m["story_time"]
        if m["skip_minutes"] < clock.DAY:
            continue
        before = m["story_time"] - m["skip_minutes"]
        # as the time lands, a minute before anyone recalls anything: a reply right after the
        # skip logs its recall at this line's time, and that rehearsal is not the skip's doing
        after = m["story_time"] - 1
        faded, sentences = [], []
        for c in s.ai:
            if s.hearing[c][m["id"]] == "away":
                continue
            then = {
                x["memory_id"]: x["tier"]
                for x in retrieve.inspect(s.conn, s.story["id"], c, now=before)
            }
            now = {
                x["memory_id"]: x["tier"]
                for x in retrieve.inspect(s.conn, s.story["id"], c, now=after)
            }
            hazy = sum(1 for x, t in then.items() if t == "sharp" and now.get(x) == "hazy")
            gone = sum(1 for x, t in then.items() if t != "forgotten" and now.get(x) == "forgotten")
            faded.append({"id": c, "hazy": hazy, "gone": gone})
            name = s.names[c]
            if hazy:
                sentences.append(
                    f"{hazy} of {name}'s memories {'is' if hazy == 1 else 'are'} going hazy."
                )
            if gone:
                whose = "" if hazy else f" of {name}'s memories"
                sentences.append(f"{gone}{whose} {'is' if gone == 1 else 'are'} fading out.")
        out[m["id"]] = {
            "minutes": m["skip_minutes"],
            "from_clock": clock.label(last, epoch),
            "to_clock": clock.label(m["story_time"], epoch),
            "faded": faded,
            "text": " ".join(sentences) or "Nothing has faded.",
        }
    return out


def scene(conn: sqlite3.Connection, story: sqlite3.Row) -> Scene:
    """Everything one story's signals are worked out from."""
    story_id = story["id"]
    path = chat.active_path(conn, story_id)
    live = db.live_runs(conn, story_id)
    marks = ",".join("?" * len(live))
    ends = conn.execute(
        f"SELECT max(to_message_id) FROM extraction_runs WHERE id IN ({marks})", sorted(live)
    ).fetchone()[0]
    ai = [
        r[0]
        for r in conn.execute(
            "SELECT id FROM entities WHERE story_id=? AND kind='character' AND is_ai=1 ORDER BY id",
            (story_id,),
        )
    ]
    return Scene(
        conn=conn,
        story=story,
        path=path,
        ai=ai,
        names=dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,))),
        from_library=dict(
            conn.execute("SELECT id, lib_item_id FROM entities WHERE story_id=?", (story_id,))
        ),
        hearing={c: chat.hearing(conn, path, c) for c in ai},
        clarity={
            c: {x["memory_id"]: x["tier"] for x in retrieve.inspect(conn, story_id, c)} for c in ai
        },
        live=live,
        read_to=ends or 0,
    )


def signals(conn: sqlite3.Connection, story_id: int) -> dict:
    """`{"read_to": <last line a live run has read>, "lines": {message id: {summary, receipts,
    callouts, recall, skip}}}`; a line carries only the parts it has."""
    s = scene(conn, conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone())
    lines: dict[int, dict] = {}
    for message_id, receipts in _receipts(s).items():
        lines[message_id] = {"summary": summary(receipts, s.names), "receipts": receipts}
    for key, parts in (("callouts", _callouts(s)), ("recall", _recall(s)), ("skip", _skips(s))):
        for message_id, part in parts.items():
            if key == "callouts":  # `run` and `gist` are the feed's plumbing, not the Scene's
                part = [{k: v for k, v in c.items() if k not in ("run", "gist")} for c in part]
            lines.setdefault(message_id, {})[key] = part
    return {"read_to": s.read_to, "lines": lines}


def _clause(text: str, names: dict[int, str]) -> str:
    """A sentence folded into another one: 'Master Oren paid the debt.' keeps the name it opens
    with (and "Mira's coat…" the possessive), 'The ledger was hidden.' loses its capital."""
    named = any(text.startswith(n) for n in names.values()) or text.startswith("I ")
    return text if named else text[:1].lower() + text[1:]


def _cost(faded: list[dict], names: dict[int, str]) -> str:
    """What a skip took, in the past tense: "1 of Mira's memories went hazy. 2 faded out." """
    said = []
    for f in faded:
        name, parts = names[f["id"]], []
        if f["hazy"]:
            parts.append(f"{f['hazy']} of {name}'s memories went hazy")
        if f["gone"]:
            more = (
                f"{f['gone']} faded out" if parts else f"{f['gone']} of {name}'s memories faded out"
            )
            parts.append(more)
        if parts:
            said.append(". ".join(parts) + ".")
    return " ".join(said)


def _who(s: Scene, ids: list[int]) -> list[dict]:
    return [
        {"id": i, "name": s.names.get(i, "someone"), "lib_item_id": s.from_library.get(i)}
        for i in ids
    ]


def activity(
    conn: sqlite3.Connection,
    story_id: int | None = None,
    kind: str | None = None,
    limit: int | None = 100,
) -> list[dict]:
    """The same signals as a feed, newest first: what someone will remember, what they made of
    a claim, how they felt, and what time cost them. `new` means a read you have not seen wrote
    it; time passing is never new.

    ponytail: every story is worked out from scratch on each call; cache per story version if a
    library ever holds hundreds of stories.
    """
    rows = conn.execute(
        "SELECT * FROM stories" + (" WHERE id=?" if story_id is not None else " ORDER BY id"),
        (story_id,) if story_id is not None else (),
    ).fetchall()
    events: list[dict] = []
    for story in rows:
        s = scene(conn, story)
        lines = {m["id"]: m for m in s.path}
        heard = {m: summary(r, s.names) for m, r in _receipts(s).items()}
        for message_id, callouts in _callouts(s).items():
            line = lines[message_id]
            for c in callouts:
                text = c["text"]
                if c["kind"] == "memory":
                    text = f"{text.removesuffix(' this')} that {_clause(c['gist'], s.names)}"
                events.append(
                    {
                        "key": c["key"],
                        "kind": c["kind"],
                        "story_id": story["id"],
                        "story": story["title"],
                        "message_id": message_id,
                        "clock": clock.label(line["story_time"], story["epoch_offset_min"]),
                        "who": _who(s, c["who"]),
                        "text": text,
                        "sub": c["reason"] or heard.get(message_id, ""),
                        "line": {"speaker": s.names.get(line["speaker_id"]), "text": line["text"]},
                        "new": c["run"] is not None and c["run"] > story["seen_run_id"],
                    }
                )
        for message_id, skip in _skips(s).items():
            line = lines[message_id]
            passed = f"{clock.spell(skip['minutes'])} passed in {story['title']}."
            events.append(
                {
                    "key": f"t{message_id}",
                    "kind": "time",
                    "story_id": story["id"],
                    "story": story["title"],
                    "message_id": message_id,
                    "clock": skip["to_clock"],
                    "who": [],
                    "text": f"{passed} {_cost(skip['faded'], s.names)}".strip(),
                    "sub": f"{skip['from_clock']} to {skip['to_clock']}",
                    "line": {"speaker": s.names.get(line["speaker_id"]), "text": line["text"]},
                    "new": False,
                }
            )
    if kind:
        events = [e for e in events if e["kind"] == kind]
    events.sort(key=lambda e: e["message_id"], reverse=True)  # ids grow with the telling
    return events[:limit] if limit is not None else events
