"""The person behind the library: what they have made and written, counted from the library.

The profile card itself (name, picture, bio) is the `profile` setting; this is its numbers
(docs/specs/2026-10-02-profiles-and-accounts.md P2), and what badges are awarded from (P3).
"""

import sqlite3


def stats(conn: sqlite3.Connection) -> dict:
    def one(sql: str):
        return conn.execute(sql).fetchone()[0]

    mine = "FROM messages WHERE role='user' AND text != ''"
    return {
        "stories": one("SELECT count(*) FROM stories"),
        "characters": one(
            "SELECT count(*) FROM lib_items WHERE kind='character'"
            " AND coalesce(json_extract(data, '$.persona'), 0) = 0"
        ),
        "personas": one(
            "SELECT count(*) FROM lib_items WHERE kind='character'"
            " AND json_extract(data, '$.persona')"
        ),
        "places": one("SELECT count(*) FROM lib_items WHERE kind='place'"),
        "messages": one(f"SELECT count(*) {mine}"),
        # ponytail: reads every line you wrote on each call; keep a running count in settings
        # if a library ever makes this slow
        "words": sum(len(text.split()) for (text,) in conn.execute(f"SELECT text {mine}")),
        "days": one(f"SELECT count(DISTINCT date(created_at)) {mine}"),
        "since": one("SELECT min(created_at) FROM stories"),
    }
