"""What each line of a story signals, for the Scene: who heard it and how clearly they will
remember it (receipts), and what a reply recalled. Read-only; recomputed per request.

ponytail: everything is recomputed on each call; cache on the story version if it gets slow.
"""

import json
import sqlite3

from kataki import chat, clock, db, retrieve

ORDER = {"sharp": 0, "hazy": 1, "forgotten": 2}  # the best clarity wins a receipt


def listed(names: list[str]) -> str:
    """'Mira', 'Mira and Tobin', 'Mira, Tobin and Ilsa'."""
    return f"{', '.join(names[:-1])} and {names[-1]}" if len(names) > 1 else "".join(names)


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


def _receipts(conn, story, path, read_to) -> dict[int, list[dict]]:
    """Per line, per AI character: heard (pending until a live run reads it), then the best
    clarity of the memories anchored to that line which they know; or absent from your line
    while they had been following the scene."""
    ai = [
        r[0]
        for r in conn.execute(
            "SELECT id FROM entities WHERE story_id=? AND kind='character' AND is_ai=1 ORDER BY id",
            (story["id"],),
        )
    ]
    live_sql, live_args = db.live_filter(db.live_runs(conn, story["id"]))
    anchored: dict[int, list[int]] = {}
    for r in conn.execute(
        f"SELECT id, message_id FROM memories WHERE story_id=? AND hidden=0"
        f" AND message_id IS NOT NULL AND {live_sql}",
        [story["id"], *live_args],
    ):
        anchored.setdefault(r["message_id"], []).append(r["id"])
    hearing = {c: chat.hearing(conn, path, c) for c in ai}
    clarity = {
        c: {m["memory_id"]: m["tier"] for m in retrieve.inspect(conn, story["id"], c)} for c in ai
    }

    out: dict[int, list[dict]] = {}
    following = dict.fromkeys(ai, False)  # heard something in this scene since the last big skip
    scene = object()
    for m in path:
        if m["scene_id"] != scene or m["skip_minutes"] >= clock.DAY:
            scene, following = m["scene_id"], dict.fromkeys(ai, False)
        receipts = []
        for c in ai:
            how = hearing[c][m["id"]]
            if m["hidden"] or m["role"] == "system":
                pass
            elif how in ("said", "heard"):
                if m["id"] > read_to:
                    receipts.append({"id": c, "state": "heard", "pending": True})
                else:
                    tiers = [clarity[c][x] for x in anchored.get(m["id"], []) if x in clarity[c]]
                    best = min(tiers, key=ORDER.__getitem__) if tiers else "heard"
                    receipts.append({"id": c, "state": best})
            elif m["role"] == "user" and how in ("away", "whisper") and following[c]:
                receipts.append({"id": c, "state": "absent", "why": how})
            if how in ("said", "heard"):
                following[c] = True
        if receipts:
            out[m["id"]] = receipts
    return out


def _recall(conn, story, path) -> dict[int, dict]:
    """Per reply: what its speaker recalled, when something worth a spark came back (hazy,
    strained for, or important)."""
    on_path = {m["id"] for m in path}
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story["id"],)))
    live = db.live_runs(conn, story["id"])
    know_sql, know_args = db.live_filter(live, "run_id")
    out: dict[int, dict] = {}
    for log in conn.execute(
        "SELECT message_id, speaker_id, memories FROM context_log WHERE story_id=?"
        " AND message_id IS NOT NULL AND speaker_id IS NOT NULL ORDER BY id",
        (story["id"],),
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
            memory = conn.execute("SELECT * FROM memories WHERE id=?", (x["memory_id"],)).fetchone()
            if memory is None:
                continue  # its run was discarded since
            known = conn.execute(
                f"SELECT * FROM knowledge WHERE knower_id=? AND memory_id=? AND {know_sql}"
                " ORDER BY id DESC LIMIT 1",
                [log["speaker_id"], memory["id"], *know_args],
            ).fetchone()
            if known:
                source = known["source"]
                if source == "told" and known["told_by_id"]:
                    source = f"told by {names.get(known['told_by_id'], 'someone')}"
                when = clock.label(known["learned_story_time"], story["epoch_offset_min"])
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
        name = names.get(log["speaker_id"], "They")
        manner = (
            "after straining" if any(x.get("effortful") for x in shown)
            else "vaguely" if any(x["tier"] == "hazy" for x in shown)
            else "clearly"
        )  # fmt: skip
        out[log["message_id"]] = {
            "speaker": log["speaker_id"],
            "title": f"{name} remembered, {manner}",
            "items": items,
        }
    return out


def signals(conn: sqlite3.Connection, story_id: int) -> dict:
    """`{"read_to": <last line a live run has read>, "lines": {message id: {...}}}`."""
    story = conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()
    path = chat.active_path(conn, story_id)
    live = sorted(db.live_runs(conn, story_id))
    ends = conn.execute(
        f"SELECT max(to_message_id) FROM extraction_runs WHERE id IN ({','.join('?' * len(live))})",
        live,
    ).fetchone()[0]
    read_to = ends or 0
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)))
    lines: dict[int, dict] = {}
    for message_id, receipts in _receipts(conn, story, path, read_to).items():
        lines[message_id] = {"summary": summary(receipts, names), "receipts": receipts}
    for message_id, recall in _recall(conn, story, path).items():
        lines.setdefault(message_id, {})["recall"] = recall
    return {"read_to": read_to, "lines": lines}
