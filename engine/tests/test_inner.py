"""The affect core: pure functions, story minutes, no model."""

from kataki import inner, library


def test_a_profile_fills_what_the_card_leaves_out():
    p = inner.shape({"axes": {"dominance": [80, 10]}, "regulation": {"style": "suppress"}})
    assert inner.mean(p, "dominance") == 80
    assert inner.mean(p, "warmth") == 50  # default kept beside the override
    assert p["regulation"] == {"style": "suppress", "capacity": 0.5}


def test_warm_people_start_brighter_and_dominant_ones_stronger():
    cold = inner.baseline(inner.shape({"axes": {"warmth": [20, 10]}}))
    warm = inner.baseline(inner.shape({"axes": {"warmth": [80, 10]}}))
    boss = inner.baseline(inner.shape({"axes": {"dominance": [90, 10]}}))
    assert warm["v"] > cold["v"]
    assert boss["d"] > 0.2


def test_the_profile_is_read_from_the_library_character(conn):
    mira = library.create_item(conn, "character", "Mira")
    library.update_item(conn, mira, data={"mind": {"anxiety": 0.8}})
    story = library.create_story(conn, "s", character_ids=[mira])
    entity = conn.execute(
        "SELECT id FROM entities WHERE name='Mira' AND story_id=?", (story,)
    ).fetchone()["id"]
    assert inner.profile(conn, entity)["anxiety"] == 0.8
