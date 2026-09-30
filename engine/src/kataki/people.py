"""Who is in a story and what they are like right now, and what a library friend has been
through: the peek card, the Chats panel and the profile page all read from here.

ponytail: every call walks each character's whole memory (`retrieve.inspect`); a profile does it
once per story they are in. Cache per story version if a library ever holds hundreds of stories.
"""

import json
import logging
import sqlite3

from kataki import (
    between,
    bonds,
    chat,
    clock,
    db,
    features,
    goals,
    growth,
    honesty,
    inner,
    recollect,
    retrieve,
)

TIERS = ("sharp", "hazy", "forgotten")


def _where(conn: sqlite3.Connection, scene_id: int | None) -> tuple[str | None, int | None]:
    """The place this scene is in, as a name and the library item its art comes from."""
    row = conn.execute(
        "SELECT e.name, e.lib_item_id FROM scenes s LEFT JOIN entities e ON e.id=s.place_id"
        " WHERE s.id IS ?",
        (scene_id,),
    ).fetchone()
    return (row["name"], row["lib_item_id"]) if row else (None, None)


def _since(changes: list[dict], times: dict[int, int], scene_start: int) -> dict[int, int]:
    """When each character last came or went. Only changes inside the scene they are in now count:
    walking out of an earlier one is not how long they have been here."""
    out: dict[int, int] = {}
    for c in changes:
        out[c["entity_id"]] = times.get(c["message_id"], scene_start)
    return out


def _state(conn: sqlite3.Connection, entity_id: int, now: int, live: set[int]) -> list[dict]:
    """What they hold, wear and suffer: each flag's latest live value at or before now."""
    live_sql, live_args = db.live_filter(live)
    rows = conn.execute(
        f"SELECT key, value, private FROM flags WHERE entity_id=? AND story_time<=? AND {live_sql}"
        " ORDER BY story_time, id",
        [entity_id, now, *live_args],
    )
    current: dict[str, dict] = {}
    for r in rows:
        current[r["key"].lower()] = {  # the column is NOCASE: "Holding" is the same flag
            "key": r["key"],
            "value": r["value"],
            "private": bool(r["private"]),
        }
    return [f for f in current.values() if f["value"] is not None]


def _about(known: list[dict], of_whom: set[int] | None) -> dict | None:
    """What they know that involves you: the counts by tier and the two sharpest samples.
    None when you are directing and there is no you in the story."""
    if of_whom is None:
        return None
    mine = [m for m in known if m["memory_id"] in of_whom]
    counts = {tier: sum(1 for m in mine if m["tier"] == tier) for tier in TIERS}
    return {
        "count": len(mine),
        **counts,
        "samples": [
            {
                "memory_id": m["memory_id"],
                "tier": m["tier"],
                "text": m["detail"] if m["tier"] == "sharp" else m["gist"],
                "belief": m["belief"],
            }
            for m in mine[:2]  # inspect sorts by activation, so these are what comes to mind
        ],
    }


def _yours(conn: sqlite3.Connection, story_id: int, persona_id: int | None) -> set[int] | None:
    """The memories that are about you: you were in them, or you are the one who claimed it."""
    if persona_id is None:
        return None
    rows = conn.execute(
        "SELECT memory_id FROM memory_entities WHERE entity_id=?"
        " UNION SELECT id FROM memories WHERE story_id=? AND asserted_by=?",
        (persona_id, story_id, persona_id),
    )
    return {r[0] for r in rows}


def _relationships(
    conn: sqlite3.Connection, entity_id: int, names: dict[int, str], persona_id: int | None,
    epoch: int, live: set[int],
) -> list[dict]:  # fmt: skip
    """How they stand towards the others, in the order it happened, one row per person and kind.
    The edges log is append-only, so the last row wins and an `ended` one ends it."""
    live_sql, live_args = db.live_filter(live)
    rows = conn.execute(
        f"SELECT * FROM edges WHERE src_id=? AND {live_sql} ORDER BY story_time, id",
        [entity_id, *live_args],
    )
    out: dict[tuple[int, str], dict] = {}
    for e in rows:
        felt = (e["dst_id"], e["rel"])
        if e["ended"]:
            out.pop(felt, None)  # she doesn't any more
            continue
        out[felt] = {
            "rel": e["rel"],
            "other_id": e["dst_id"],
            "other": names.get(e["dst_id"], "someone"),
            "you": e["dst_id"] == persona_id,
            "note": e["note"],
            "since": clock.label(e["story_time"], epoch),
        }
    return list(out.values())


def _mood(conn: sqlite3.Connection, entity_id: int, path: list, now: int) -> dict | None:
    """How they feel now, faded to the present (Peek; spec §8.2)."""
    try:
        prof = inner.profile(conn, entity_id)
        state = inner.current(conn, entity_id, path, prof)
        return state and inner.public(inner.tick(state, now, prof), prof)
    except Exception as e:  # a bad profile costs the mood line, not the whole Peek
        logging.getLogger(__name__).warning("mood unavailable for %s: %s", entity_id, e)
        return None


def _bonds(conn, entity_id: int, path: list, names: dict, persona_id, epoch: int) -> list[dict]:
    """How they stand with each person the ledger has something on (Peek; spec §8.3)."""
    try:
        rows = bonds.ledger(conn, entity_id, path)
        now = path[-1]["story_time"] if path else 0
        stands = bonds.toward(rows, sorted({r["dst_id"] for r in rows}), now)
        return [
            bonds.public(st, d, names.get(d, "someone"), d == persona_id, epoch)
            for d, st in stands.items()
        ]
    except Exception as e:  # a bad row costs the bonds, not the whole Peek
        logging.getLogger(__name__).warning("bonds unavailable for %s: %s", entity_id, e)
        return []


def _thought(path: list, entity_id: int) -> dict | None:
    """Their latest thought on this branch (Peek; spec §8.3). Replies written without one (the
    thought is asked only when it matters) look back to the last that had one."""
    try:
        for m in reversed(path):
            if m["role"] == "assistant" and m["speaker_id"] == entity_id:
                if said := json.loads(m["gen"] or "{}").get("thought"):
                    return {**said, "message_id": m["id"]}
        return None
    except Exception as e:  # a bad row costs the thought, not the whole Peek
        logging.getLogger(__name__).warning("thought unavailable for %s: %s", entity_id, e)
        return None


def _secrets(conn, story_id: int, entity_id: int, path: list) -> list[dict]:
    """What they keep from whom, and what they said instead (Peek; spec §8.3 slice 4)."""
    try:
        return honesty.public(conn, story_id, entity_id, path)
    except Exception as e:  # a bad row costs the secrets, not the whole Peek
        logging.getLogger(__name__).warning("secrets unavailable for %s: %s", entity_id, e)
        return []


def _seeds(conn, entity_id: int, path: list, names: dict, epoch: int) -> list[dict]:
    """What is on their mind from their life between scenes (minds slice 5); a failure costs
    only this."""
    try:
        if between._off(conn, entity_id):  # their own dial is off: nothing to show
            return []
        return between.public(conn, entity_id, path, names, epoch)
    except Exception as e:
        logging.getLogger(__name__).warning("seeds not shown for %s: %s", entity_id, e)
        return []


def _goals(conn, entity_id: int, path: list, epoch: int) -> list[dict]:
    """What she wants (Peek; spec §8.3 slice 7); a failure costs only this."""
    try:
        return goals.public(conn, entity_id, path, epoch)
    except Exception as e:
        logging.getLogger(__name__).warning("goals not shown for %s: %s", entity_id, e)
        return []


def _growth(conn, story_id: int, entity_id: int, path: list, names: dict, epoch: int):
    """How she has changed (slice 8), or None when it can't be read (never the whole Peek)."""
    try:
        return growth.public(conn, story_id, entity_id, path, names, epoch)
    except Exception as e:
        logging.getLogger(__name__).warning("growth not shown for %s: %s", entity_id, e)
        return None


def _needs(conn, entity_id: int, path: list, now: int, epoch: int) -> dict | None:
    """Her energy now and her drives, if tracked (Peek; spec §8.3 slice 7); guarded."""
    try:
        prof = inner.profile(conn, entity_id)
        state = inner.current(conn, entity_id, path, prof)
        state = state and inner.tick(state, now, prof)
        minute = (now + epoch) % clock.DAY
        top = inner.need_row(state, prof, minute, [])
        return inner.levels(state, prof, minute) | {
            "pressing": top and top["need"],
            "shows": top and top["text"],
        }
    except Exception as e:
        logging.getLogger(__name__).warning("needs not shown for %s: %s", entity_id, e)
        return None


VERSIONS = 5


def _versions(conn, entity_id: int, path: list, known: list[dict]) -> list[dict]:
    """Peek's "her version vs the truth" (spec §8.3 slice 6), newest first; guarded."""
    try:
        due = {s["memory_id"] for s in recollect.open_slips(conn, entity_id, path)}
        mine = [m for m in known if m["version"] and m["version"]["basis"] != "recount"]
        mine.sort(key=lambda m: m["story_time"], reverse=True)
        return [
            {"memory_id": m["memory_id"], "truth": m["detail"], "version": m["version"]["text"],
             "basis": m["version"]["basis"], "since": m["version"]["since"],
             "correction": "due" if m["version"]["basis"] == "alt" and m["memory_id"] in due else None}
            for m in mine[:VERSIONS]
        ]  # fmt: skip
    except Exception as e:
        logging.getLogger(__name__).warning("versions not shown for %s: %s", entity_id, e)
        return []


def people(conn: sqlite3.Connection, story: sqlite3.Row) -> list[dict]:
    """One entry per AI character: where they are, what they hold, what is on their mind, what
    they know about you, and how they stand towards everyone."""
    story_id = story["id"]
    path = chat.active_path(conn, story_id)
    scene_id = chat.scene_of(conn, story_id, path)
    here = {e["id"] for e in chat.present_entities(conn, scene_id, path)}
    now = path[-1]["story_time"] if path else 0
    scene = conn.execute(
        "SELECT start_story_time FROM scenes WHERE id IS ?", (scene_id,)
    ).fetchone()
    since = _since(
        chat.presence_changes(conn, story_id, [m for m in path if m["scene_id"] == scene_id]),
        {m["id"]: m["story_time"] for m in path},
        scene["start_story_time"] if scene else 0,
    )
    where, where_item = _where(conn, scene_id)
    epoch = story["epoch_offset_min"]
    persona_id = story["persona_entity_id"]
    yours = _yours(conn, story_id, persona_id)
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)))
    live = db.live_runs(conn, story_id)
    feeling = features.enabled(conn, "mind.affect")
    tied = features.enabled(conn, "mind.bonds")
    thinking = features.enabled(conn, "mind.thought")
    secretive = features.enabled(conn, "mind.secrets")
    offscreen = features.enabled(conn, "mind.offscreen")
    human = features.enabled(conn, "mind.recall")
    wanting = features.enabled(conn, "mind.goals")
    growing = features.enabled(conn, "mind.growth")

    out = []
    for e in conn.execute(
        "SELECT * FROM entities WHERE story_id=? AND kind='character' AND is_ai=1 AND hidden=0"
        " ORDER BY name",
        (story_id,),
    ).fetchall():
        known = [m for m in retrieve.inspect(conn, story_id, e["id"]) if not m["hidden"]]
        mind = next((m for m in known if m["tier"] != "forgotten"), None)
        out.append(
            {
                "id": e["id"],
                "name": e["name"],
                "lib_item_id": e["lib_item_id"],
                "present": e["id"] in here,
                "since": clock.label(
                    since.get(e["id"], scene["start_story_time"] if scene else 0), epoch
                ),
                "where": where,
                "where_item_id": where_item,
                "state": _state(conn, e["id"], now, live),
                "on_mind": mind
                and {
                    "tier": mind["tier"],
                    "text": mind["detail"] if mind["tier"] == "sharp" else mind["gist"],
                },
                "about_you": _about(known, yours),
                "remembers": len(known),
                "relationships": _relationships(conn, e["id"], names, persona_id, epoch, live),
                "secret": e["private"],
                "mood": _mood(conn, e["id"], path, now) if feeling else None,
                "bonds": _bonds(conn, e["id"], path, names, persona_id, epoch) if tied else [],
                "thought": _thought(path, e["id"]) if thinking else None,
                "secrets": _secrets(conn, story_id, e["id"], path) if secretive else [],
                "seeds": _seeds(conn, e["id"], path, names, epoch) if offscreen else [],
                "versions": _versions(conn, e["id"], path, known) if human else [],
                "goals": _goals(conn, e["id"], path, epoch) if wanting else [],
                "needs": _needs(conn, e["id"], path, now, epoch) if wanting else None,
                "growth": _growth(conn, story_id, e["id"], path, names, epoch) if growing else None,
            }
        )
    return out


def profile(conn: sqlite3.Connection, lib_item_id: int) -> dict:
    """Everywhere this friend (or persona) has been: the stories they are in, what they are like
    in each, and the places they have played."""
    stories, places = [], {}
    for e in conn.execute(
        "SELECT e.id, e.story_id FROM entities e WHERE e.lib_item_id=? AND e.kind='character'"
        " ORDER BY e.story_id",
        (lib_item_id,),
    ).fetchall():
        story = conn.execute("SELECT * FROM stories WHERE id=?", (e["story_id"],)).fetchone()
        if story is None:
            continue
        mine = e["id"] == story["persona_entity_id"]
        cast = people(conn, story)
        person = next((p for p in cast if p["id"] == e["id"]), None)
        stories.append(
            {
                "id": story["id"],
                "title": story["title"],
                "role": "persona" if mine else "ai",
                "clock": clock.label(_now(conn, story["id"]), story["epoch_offset_min"]),
                "person": None if mine else person,
                "known_by": [
                    {
                        "id": p["id"],
                        "name": p["name"],
                        "lib_item_id": p["lib_item_id"],
                        **{k: p["about_you"][k] for k in ("count", *TIERS)},
                    }
                    for p in cast
                    if p["about_you"] is not None
                ]
                if mine
                else None,
            }
        )
        for seen in _places(conn, story):
            places[(story["id"], seen["name"])] = seen
    return {"stories": stories, "places": list(places.values())}


def _places(conn: sqlite3.Connection, story: sqlite3.Row) -> list[dict]:
    """Every place this story has really played in, and when it left: the next scene's beginning,
    or where the story stands now for the one it is still in. A scene on a branch you took back
    never happened."""
    path = chat.active_path(conn, story["id"])
    ours = retrieve.live_scenes(conn, story["id"], path)
    scenes = [
        s
        for s in conn.execute(
            "SELECT s.id, s.start_story_time, e.name, e.lib_item_id FROM scenes s"
            " JOIN entities e ON e.id=s.place_id WHERE s.story_id=?"
            " ORDER BY s.start_story_time, s.id",
            (story["id"],),
        )
        if s["id"] in ours
    ]
    if not scenes:
        return []  # a story that never named a place: nowhere to have been
    ends = [s["start_story_time"] for s in scenes[1:]] + [path[-1]["story_time"] if path else 0]
    return [
        {
            "name": s["name"],
            "lib_item_id": s["lib_item_id"],
            "story": story["title"],
            "story_id": story["id"],
            "clock": clock.label(max(end, s["start_story_time"]), story["epoch_offset_min"]),
        }
        for s, end in zip(scenes, ends, strict=True)
    ]


def _now(conn: sqlite3.Connection, story_id: int) -> int:
    path = chat.active_path(conn, story_id)
    return path[-1]["story_time"] if path else 0
