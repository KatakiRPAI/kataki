from kataki import achievements, db, library, profile


def earned(result):
    return {b["key"] for b in result["badges"] if b["earned_at"]}


def test_every_rule_watches_a_number_the_profile_has(conn):
    numbers = profile.stats(conn)
    assert all(number in numbers for _, _, number, _ in achievements.RULES)
    assert len({key for key, *_ in achievements.RULES}) == len(achievements.RULES)


def test_a_badge_is_new_once(conn):
    assert achievements.check(conn) == {
        "badges": [
            {**b, "progress": 0, "earned_at": None, "backdated": False}
            for b in achievements.check(conn)["badges"]
        ],
        "new": [],
    }
    library.create_item(conn, "character", "Mira")
    first = achievements.check(conn)
    assert first["new"] == ["first_character"]
    assert earned(first) == {"first_character"}
    again = achievements.check(conn)
    assert again["new"] == [] and earned(again) == {"first_character"}
    five = next(b for b in again["badges"] if b["key"] == "characters_5")
    assert (five["progress"], five["target"]) == (1, 5)


def test_what_a_library_already_holds_is_backdated_not_announced(conn):
    library.create_item(conn, "character", "Mira")
    library.create_item(conn, "place", "The Gull")
    first = achievements.check(conn)  # the first look at a library that was here before badges
    assert first["new"] == []
    assert earned(first) == {"first_character", "first_place"}
    assert all(b["backdated"] for b in first["badges"] if b["earned_at"])
    library.create_story(conn, "Low tide", [])
    assert achievements.check(conn)["new"] == ["first_story"]


def test_v19_adds_achievements_to_a_v18_library(tmp_path):
    path = tmp_path / "v18.db"
    old = db.connect(path)  # today's schema, then pretend it is v18
    library.create_item(old, "character", "Mira")
    old.executescript("DROP TABLE achievements; PRAGMA user_version=18;")
    old.commit()
    old.close()

    conn = db.connect(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    assert earned(achievements.check(conn)) == {"first_character"}  # and what was there counts
