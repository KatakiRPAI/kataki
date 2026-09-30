import pytest

from kataki import library


@pytest.fixture
def cast(conn):
    mira = library.create_item(
        conn,
        "character",
        "Mira",
        description="A guild courier.",
        private="Secretly reports to the harbour master.",
        data={"aliases": ["the courier"], "first_message": "Mira slides a letter across the bar."},
        tags=["Guild", "docks"],
    )
    tobin = library.create_item(conn, "character", "Tobin", description="A smuggler.")
    you = library.create_item(conn, "character", "Aren", description="A newcomer.")
    tavern = library.create_item(conn, "place", "The Gull", data={"aliases": ["the tavern"]})
    return {"mira": mira, "tobin": tobin, "you": you, "tavern": tavern}


def test_items_round_trip_with_data_and_tags(conn, cast):
    item = library.get_item(conn, cast["mira"])
    assert item["name"] == "Mira" and item["kind"] == "character"
    assert item["data"]["aliases"] == ["the courier"]
    assert item["tags"] == ["docks", "Guild"]  # sorted, original case kept


def test_list_filters_by_kind_and_tag_case_insensitively(conn, cast):
    assert [i["name"] for i in library.list_items(conn, kind="place")] == ["The Gull"]
    assert [i["name"] for i in library.list_items(conn, tag="guild")] == ["Mira"]
    assert len(library.list_items(conn)) == 4


def test_update_replaces_fields_and_tags(conn, cast):
    library.update_item(conn, cast["mira"], description="Retired.", tags=["retired"])
    item = library.get_item(conn, cast["mira"])
    assert (item["description"], item["tags"]) == ("Retired.", ["retired"])
    assert item["updated_at"] is not None
    assert library.list_items(conn, tag="guild") == []


def test_update_rejects_unknown_fields(conn, cast):
    with pytest.raises(ValueError, match="unknown field"):
        library.update_item(conn, cast["mira"], kind="place")


def test_delete_removes_the_item_and_its_taggings(conn, cast):
    library.delete_item(conn, cast["mira"])
    assert library.get_item(conn, cast["mira"]) is None
    assert conn.execute("SELECT count(*) FROM taggings").fetchone()[0] == 0


# --- starting a story ------------------------------------------------------------------


@pytest.fixture
def story(conn, cast):
    return library.create_story(
        conn,
        "Low Tide",
        character_ids=[cast["mira"], cast["tobin"]],
        place_id=cast["tavern"],
        persona_id=cast["you"],
    )


def entity(conn, story_id, name):
    return conn.execute(
        "SELECT * FROM entities WHERE story_id=? AND name=?", (story_id, name)
    ).fetchone()


def test_a_story_snapshots_its_cast_so_later_library_edits_do_not_rewrite_it(conn, cast, story):
    library.update_item(conn, cast["mira"], description="Rewritten in the library.")
    mira = entity(conn, story, "Mira")
    assert mira["description"] == "A guild courier."
    assert mira["private"] == "Secretly reports to the harbour master."
    assert (mira["lib_item_id"], mira["is_ai"], mira["run_id"]) == (cast["mira"], 1, None)


def test_deleting_an_item_a_story_uses_unlinks_it_and_the_story_keeps_its_copy(conn, cast, story):
    library.delete_item(conn, cast["mira"])
    mira = entity(conn, story, "Mira")
    assert (mira["description"], mira["lib_item_id"]) == ("A guild courier.", None)


def test_the_persona_is_an_ordinary_entity_the_ai_does_not_play(conn, story):
    aren = entity(conn, story, "Aren")
    row = conn.execute("SELECT persona_entity_id FROM stories WHERE id=?", (story,)).fetchone()
    assert aren["is_ai"] == 0 and row["persona_entity_id"] == aren["id"]


def test_names_and_aliases_become_recall_hooks(conn, story):
    aliases = {
        r["alias"]
        for r in conn.execute(
            "SELECT alias FROM aliases JOIN entities ON entities.id=entity_id WHERE story_id=?",
            (story,),
        )
    }
    assert {"Mira", "the courier", "Tobin", "Aren", "The Gull", "the tavern"} <= aliases


def test_the_opening_scene_is_at_the_place_with_everyone_present(conn, story):
    scene = conn.execute("SELECT * FROM scenes WHERE story_id=?", (story,)).fetchone()
    assert scene["place_id"] == entity(conn, story, "The Gull")["id"]
    assert scene["start_message_id"] is None  # always live, whatever branch is active
    present = {
        r["name"]
        for r in conn.execute(
            "SELECT name FROM presence JOIN entities ON entities.id=entity_id"
            " WHERE scene_id=? AND present=1",
            (scene["id"],),
        )
    }
    assert present == {"Mira", "Tobin", "Aren"}


def test_the_first_characters_greeting_opens_the_story(conn, story):
    row = conn.execute("SELECT active_leaf_id FROM stories WHERE id=?", (story,)).fetchone()
    first = conn.execute("SELECT * FROM messages WHERE id=?", (row["active_leaf_id"],)).fetchone()
    assert first["text"] == "Mira slides a letter across the bar."
    assert (first["role"], first["parent_id"], first["story_time"]) == ("assistant", None, 0)
    assert first["speaker_id"] == entity(conn, story, "Mira")["id"]


def test_the_opening_is_the_one_typed_else_the_plots_else_a_greeting(conn, cast):
    plot = library.create_item(
        conn, "scenario", "Heist", data={"first_message": "Rain on the glass."}
    )

    def opening(**kw):
        story = library.create_story(conn, "S", character_ids=[cast["mira"]], **kw)
        leaf = conn.execute("SELECT active_leaf_id FROM stories WHERE id=?", (story,)).fetchone()[0]
        row = conn.execute("SELECT text, speaker_id FROM messages WHERE id=?", (leaf,)).fetchone()
        return (row["text"], row["speaker_id"] is None) if row else None

    assert opening(scenario_id=plot, first_message="The lights go out.") == (
        "The lights go out.",
        True,
    )
    assert opening(first_message="  The lights go out.  ") == ("The lights go out.", True)
    assert opening(scenario_id=plot) == ("Rain on the glass.", True)
    assert opening() == (
        "Mira slides a letter across the bar.",
        False,
    )  # an imported card's greeting
    tobin = library.create_story(conn, "S", character_ids=[cast["tobin"]], first_message=" ")
    assert (
        conn.execute("SELECT active_leaf_id FROM stories WHERE id=?", (tobin,)).fetchone()[0]
        is None
    )


def test_director_mode_has_no_persona(conn, cast):
    story = library.create_story(conn, "Watching", character_ids=[cast["tobin"]])
    row = conn.execute(
        "SELECT persona_entity_id, active_leaf_id FROM stories WHERE id=?", (story,)
    ).fetchone()
    assert row["persona_entity_id"] is None
    assert row["active_leaf_id"] is None  # Tobin has no greeting, so the story starts empty


def test_example_dialogue_is_copied_into_the_story_with_the_character(conn):
    mira = library.create_item(
        conn, "character", "Mira", data={"example_dialogue": "Mira: Coin first. Questions after."}
    )
    story = library.create_story(conn, "s", character_ids=[mira])
    library.update_item(conn, mira, data={"example_dialogue": "changed later"})
    row = conn.execute("SELECT examples FROM entities WHERE story_id=?", (story,)).fetchone()
    assert row["examples"] == "Mira: Coin first. Questions after."


# --- books: stories that belong together --------------------------------------------------------


def test_a_book_holds_its_stories_in_an_order(conn, cast):
    first = library.create_story(conn, "One", character_ids=[cast["mira"]])
    second = library.create_story(conn, "Two", character_ids=[cast["tobin"]])
    third = library.create_story(conn, "Three", character_ids=[cast["mira"]])
    book = library.create_book(conn, "The Gull Years", blurb="Everything that happened at the bar")

    library.set_book(conn, second, book)
    library.set_book(conn, first, book)
    assert [s["title"] for s in library.book_stories(conn, book)] == ["Two", "One"]  # as added

    library.order_book(conn, book, [first, second])
    assert [s["title"] for s in library.book_stories(conn, book)] == ["One", "Two"]

    [listed] = library.list_books(conn)
    assert (listed["title"], listed["blurb"], listed["stories"]) == (
        "The Gull Years",
        "Everything that happened at the bar",
        2,
    )
    library.update_book(conn, book, title="The Gull", blurb="")
    assert library.get_book(conn, book)["title"] == "The Gull"

    # a story leaves a book without leaving the library
    library.set_book(conn, first, None)
    assert [s["title"] for s in library.book_stories(conn, book)] == ["Two"]
    assert conn.execute("SELECT count(*) FROM stories").fetchone()[0] == 3

    place = library.create_item(
        conn, "place", "Harbour", data={"links": {"book": book}, "time": "dusk"}
    )

    # deleting the book keeps every story, place and plot, not filed anywhere
    library.delete_book(conn, book)
    assert library.list_books(conn) == []
    assert conn.execute("SELECT count(*) FROM stories").fetchone()[0] == 3
    assert conn.execute("SELECT count(*) FROM stories WHERE book_id IS NOT NULL").fetchone()[0] == 0
    assert library.get_item(conn, place)["data"] == {"links": {}, "time": "dusk"}
    assert third  # untouched throughout


def test_a_story_can_only_join_a_book_that_exists(conn, cast):
    story = library.create_story(conn, "One", character_ids=[cast["mira"]])
    with pytest.raises(ValueError):
        library.set_book(conn, story, 999)
