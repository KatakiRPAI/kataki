from kataki import library, profile


def test_stats_count_what_the_person_made_and_wrote(conn):
    assert profile.stats(conn) == {
        "stories": 0,
        "characters": 0,
        "personas": 0,
        "places": 0,
        "messages": 0,
        "words": 0,
        "days": 0,
        "since": None,
    }
    mira = library.create_item(conn, "character", "Mira")
    library.create_item(conn, "character", "Aren", data={"persona": True})
    library.create_item(conn, "place", "The Gull")
    story = library.create_story(conn, "Low tide", [mira])
    with conn:
        conn.executemany(
            "INSERT INTO messages(story_id, role, text, story_time, created_at)"
            " VALUES(?, ?, ?, 0, ?)",
            [
                (story, "user", "Is the tide out?", "2026-10-01 09:00:00"),
                (story, "assistant", "It has been out for an hour.", "2026-10-01 09:00:05"),
                (story, "user", "Then we walk.", "2026-10-01 21:00:00"),
                (story, "user", "Morning.", "2026-10-02 08:00:00"),
            ],
        )
    got = profile.stats(conn)
    assert (got["stories"], got["characters"], got["personas"], got["places"]) == (1, 1, 1, 1)
    assert got["messages"] == 3  # only the lines the person wrote
    assert got["words"] == 8
    assert got["days"] == 2
    assert got["since"]
