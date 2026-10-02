"""Badges: rules over what the library already holds, so they can be run again at any time.

A rule is met when one of the profile's numbers reaches its target. A rule met for the first
time is stored and reported once as new; rules already met the first time a library is looked
at are stored as backdated and never announced (docs/specs/2026-10-02-profiles-and-accounts.md
P3). No streaks, and nothing here is worth money.

The list is a starter set: the owner defines the real one.
"""

import sqlite3

from kataki import knobs, profile

# key, group, the number it watches (a key of profile.stats), target
RULES = [
    ("first_message", "first", "messages", 1),
    ("first_character", "first", "characters", 1),
    ("first_story", "first", "stories", 1),
    ("first_place", "first", "places", 1),
    ("words_1k", "writing", "words", 1_000),
    ("words_10k", "writing", "words", 10_000),
    ("words_100k", "writing", "words", 100_000),
    ("messages_100", "writing", "messages", 100),
    ("messages_1k", "writing", "messages", 1_000),
    ("characters_5", "building", "characters", 5),
    ("characters_25", "building", "characters", 25),
    ("places_5", "building", "places", 5),
    ("personas_3", "building", "personas", 3),
    ("story_1k", "long", "longest_story", 1_000),
    ("days_30", "long", "days", 30),
    ("days_100", "long", "days", 100),
]


def check(conn: sqlite3.Connection) -> dict:
    numbers = profile.stats(conn)
    first_look = knobs.setting(conn, "achievements.started", None) is None
    have = {r["key"]: r for r in conn.execute("SELECT * FROM achievements")}
    new = [key for key, _, number, target in RULES if key not in have and numbers[number] >= target]
    with conn:
        conn.executemany(
            "INSERT INTO achievements(key, backdated) VALUES(?, ?)",
            [(key, int(first_look)) for key in new],
        )
        if first_look:
            conn.execute(
                "INSERT OR REPLACE INTO settings(key, value) VALUES('achievements.started', '1')"
            )
    have = {r["key"]: r for r in conn.execute("SELECT * FROM achievements")}
    return {
        "badges": [
            {
                "key": key,
                "group": group,
                "target": target,
                "progress": min(numbers[number], target),
                "earned_at": have[key]["earned_at"] if key in have else None,
                "backdated": bool(have[key]["backdated"]) if key in have else False,
            }
            for key, group, number, target in RULES
        ],
        "new": [] if first_look else new,
    }
