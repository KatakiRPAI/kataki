"""What a file would become, said before anything is made of it."""

import json

import pytest

from kataki import intake
from kataki.cards import BadCard
from test_cards import V3 as CARD
from test_cards import carded, charx, png
from test_chats import HEADER, LINES, jsonl


def test_a_card_says_who_it_would_bring_in_and_what_comes_with_them():
    look = intake.look(png(ccv3=carded("chara_card_v3", "3.0", CARD)))
    assert look["kind"] == "card" and look["title"] == "Mira Vale"
    said = " ".join(look["what"])
    assert "Mira Vale" in said and "lorebook" in said and "1" in said
    assert "portrait" in said.lower()
    # the same card in its other two shapes reads the same way
    assert intake.look(charx(CARD, {}))["kind"] == "card"
    assert intake.look(json.dumps({"spec": "chara_card_v3", "data": CARD}).encode())["title"] == (
        "Mira Vale"
    )


def test_a_chat_says_the_story_it_would_make_and_how_long_it_is():
    look = intake.look(jsonl(HEADER, LINES))
    assert look["kind"] == "chat"
    said = " ".join(look["what"])
    assert "3 lines" in said and "Mira" in said and "Aren" in said
    assert "take" in said  # one of the three lines has two of them


def test_a_world_info_file_says_how_much_a_story_would_learn():
    book = {"entries": {"0": {"key": ["ledger"], "content": "green", "constant": True},
                        "1": {"key": ["tide"], "content": "out"}}}  # fmt: skip
    look = intake.look(json.dumps(book).encode())
    assert look["kind"] == "lorebook"
    said = " ".join(look["what"])
    assert "2" in said and "1" in said  # two entries, one of them always there
    assert look["needs_story"] is True


def test_a_library_says_what_is_in_it_and_that_this_one_must_be_empty(conn, tmp_path):
    from kataki import archive, library

    library.create_item(conn, "character", "Mira")
    archive.dump(conn, tmp_path / "out.kataki")
    look = intake.look((tmp_path / "out.kataki").read_bytes())
    assert look["kind"] == "kataki"
    said = " ".join(look["what"])
    assert "1 friend, 0 stories, 0 memories" in said  # counted in English, not in "memorys"
    assert any("empty" in n for n in look["notes"])


def test_a_file_that_is_nothing_we_know_says_so_rather_than_guessing():
    with pytest.raises(BadCard) as bad:
        intake.look(b"\x00\x01\x02 not a card, not a chat, not a book")
    assert "not" in str(bad.value)
    with pytest.raises(BadCard):
        intake.look(b"")


def test_what_the_preview_counts_is_what_the_import_keeps(conn, tmp_path):
    """The whole point of a preview is that it does not lie. Both sides, same file."""
    from kataki import chats, library, lore

    # a book of four entries, of which the adder keeps two: one is a blank divider, and one
    # has words but no key, no memo and is not always on, so nothing could ever cue it
    book = {
        "entries": [
            {"key": ["ledger"], "content": "It is green.", "constant": True},
            {"key": ["tide"], "content": "The tide is out."},
            {"key": ["docks"], "content": "", "comment": "a divider"},
            {"key": [], "content": "Nobody can ever cue this."},
        ]
    }
    look = intake.look(json.dumps(book).encode())
    story = library.create_story(conn, "Low Tide", [library.create_item(conn, "character", "Mira")])
    made = lore.add(conn, story, lore.read(json.dumps(book).encode()))
    assert look["what"][0].startswith(f"{made['made']} things")
    assert f"{made['pinned']} of them is" in look["what"][1]
    assert any("2" in n for n in look["notes"])  # and it says the other two are dropped

    # a chat whose blank lines the adder skips, and whose other voices it makes friends of
    rows = [
        {"name": "Mira", "is_user": False, "mes": "*no glance up* We're closed."},
        {"name": "Aren", "is_user": True, "mes": "I'm not here to drink."},
        {"name": "Tobin", "is_user": False, "mes": "Then what are you here for?"},
        {"name": "Mira", "is_user": False, "mes": "   "},  # an aborted reply
        {"name": "Mira", "is_user": False, "mes": ""},
    ]
    blob = jsonl({"user_name": "Aren", "character_name": "Mira"}, rows)
    look = intake.look(blob)
    kept = chats.add(conn, blob)
    assert f"{kept['lines']} lines" in look["what"][1]
    assert any("blank" in n or "nothing in them" in n for n in look["notes"])
    assert any("Tobin" in line for line in look["what"])  # a third voice is a third friend


def test_a_library_says_what_it_replaces_rather_than_promising_it_replaces_nothing(conn, tmp_path):
    from kataki import archive

    archive.dump(conn, tmp_path / "out.kataki")
    notes = " ".join(intake.look((tmp_path / "out.kataki").read_bytes())["notes"])
    for word in ("model", "settings", "tags"):  # archive.REPLACED, in the reader's words
        assert word in notes
    assert "nothing here is overwritten" not in notes


def test_a_library_nobody_should_believe(conn, tmp_path):
    """A .kataki comes from anywhere, so nothing it says about itself is taken on trust."""
    import zipfile

    made = tmp_path / "liar.kataki"
    with zipfile.ZipFile(made, "w") as z:
        z.writestr("kataki.json", json.dumps({"kataki": 1, "schema_version": 1,
                                              "holds": {"friends": "lots", "stories": {"a": 1},
                                                        "pictures": None}}))  # fmt: skip
    look = intake.look(made.read_bytes())
    assert "0 friends, 0 stories, 0 memories" in look["what"][0]

    # and a member that cannot be read is a file we cannot take, not a crash
    broken = tmp_path / "broken.kataki"
    body = bytearray(made.read_bytes())
    body[-40:] = b"\x00" * 40  # scribble over the central directory / member data
    broken.write_bytes(bytes(body))
    with pytest.raises(BadCard):
        intake.look(broken.read_bytes())


def test_json_written_the_way_other_apps_write_it(conn):
    """A byte-order mark or UTF-16 is still a card: the import routes read both, so must this."""
    import codecs

    card = json.dumps({"spec": "chara_card_v3", "data": CARD})
    assert intake.look(codecs.BOM_UTF8 + card.encode())["title"] == "Mira Vale"
    assert intake.look(card.encode("utf-16"))["title"] == "Mira Vale"


def test_a_file_too_big_to_read_is_refused_before_it_is_read():
    with pytest.raises(BadCard) as bad:
        intake.look(b"{" + b" " * (intake.MAX_BYTES + 1))
    assert "big" in str(bad.value)


def test_json_nested_past_all_reason_is_refused_rather_than_crashing():
    deep = b'{"data":' * 1200 + b'{"entries":[{"key":["a"],"content":"c"}]}' + b"}" * 1200
    with pytest.raises(BadCard):
        intake.look(deep)


def test_looking_at_a_file_makes_nothing(conn):
    from kataki import library

    before = len(library.list_items(conn, None, None))
    intake.look(png(ccv3=carded("chara_card_v3", "3.0", CARD)))
    intake.look(jsonl(HEADER, LINES))
    assert len(library.list_items(conn, None, None)) == before
