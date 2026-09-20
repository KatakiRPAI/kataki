"""Lorebooks coming in: a card's own book, a lorebook_v3 file, or a SillyTavern World Info
export, all landing as facts a story already knows how to hold."""

import json

import pytest
from fastapi.testclient import TestClient

from kataki import chat, context, library, lore, retrieve
from kataki.llm import Endpoint
from kataki.server import create_app
from test_cards import carded, charx, png

BOOK = {
    "name": "The Gull",
    "entries": [
        {
            "keys": ["the Gull", "tavern"],
            "content": "The Gull is the last tavern on the harbour road. {{char}} keeps its books.",
            "comment": "the tavern", "constant": True, "enabled": True,
            "insertion_order": 100, "use_regex": False, "extensions": {},
        },
        {
            "keys": ["ledger", "guild ledger"],
            "content": "The guild ledger lists every debt the harbour owes. {{user}} came for it.",
            "comment": "the ledger", "constant": False, "enabled": True,
            "insertion_order": 90, "use_regex": False, "extensions": {},
        },
        {
            "keys": ["shadowfangs"],
            "content": "The Shadowfangs took the north road years ago.",
            "constant": False, "enabled": False,  # switched off by whoever wrote it
            "insertion_order": 10, "use_regex": False, "extensions": {},
        },
    ],
}  # fmt: skip

WORLD_INFO = {  # what SillyTavern writes out: entries by uid, and its own field names
    "entries": {
        "0": {
            "uid": 0, "key": ["eldoria", "forest"], "keysecondary": [],
            "comment": "eldoria", "content": "Eldoria is a forest under a guardian's watch.",
            "constant": True, "selective": True, "order": 100, "position": 0, "disable": False,
        },
        "1": {
            "uid": 1, "key": ["shadowfangs"], "keysecondary": [],
            "comment": "the wolves", "content": "The Shadowfangs hunt the eastern glades.",
            "constant": False, "selective": True, "order": 90, "position": 0, "disable": True,
        },
    }
}  # fmt: skip


@pytest.fixture
def api(conn, backend):
    client = TestClient(create_app(conn, "t", llm=backend.llm, worker_delay=60))
    client.headers["Authorization"] = "Bearer t"
    with client:
        yield client


@pytest.fixture
def story(conn):
    mira = library.create_item(conn, "character", "Mira", "She keeps the ledger.")
    aren = library.create_item(conn, "character", "Aren", "Late, as ever.")
    return library.create_story(conn, "Low Tide", character_ids=[mira], persona_id=aren)


def memories(conn, story_id):
    """This story's memories, by the first word each one is cued by."""
    return {(m["tags_text"].split() or ["(no cue)"])[0]: dict(m) for m in conn.execute(
        "SELECT * FROM memories WHERE story_id=? ORDER BY id", (story_id,)
    )}  # fmt: skip


def test_a_book_becomes_facts_the_story_knows(conn, story):
    made = lore.add(conn, story, BOOK)
    assert (made["made"], made["pinned"]) == (2, 1)
    assert any("switched off" in n for n in made["notes"])

    by_key = memories(conn, story)
    assert sorted(by_key) == ["ledger", "the"]  # "the Gull", "ledger"
    tavern, ledger = by_key["the"], by_key["ledger"]

    # a constant entry is always in the prompt, so it lives in the stable block
    assert tavern["pinned"] == 1 and ledger["pinned"] == 0
    assert tavern["common"] == 1 and tavern["kind"] == "fact" and tavern["is_true"] == 1
    # the rest wait for their keywords, which is what the memory index is for
    assert ledger["tags_text"] == "ledger guild ledger"
    assert library.get_tags(conn, "memory", ledger["id"]) == ["guild ledger", "ledger"]
    assert ledger["gist"] == "The guild ledger lists every debt the harbour owes. Aren came for it."
    # and the story's own names are written into them
    assert tavern["detail"].endswith("Mira keeps its books.")
    assert ledger["detail"].endswith("Aren came for it.")


def test_the_words_that_cued_it_there_cue_it_here(conn, story):
    """The point of keywords: say the word in the story and the fact comes back."""
    lore.add(conn, story, BOOK)
    mira = conn.execute("SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,))
    who = mira.fetchone()["id"]
    chat.append_message(conn, story, "user", "Where is the guild ledger kept?")

    got = retrieve.recall(conn, story, who, "Where is the guild ledger kept?", noise=False)
    assert any("every debt the harbour owes" in r.text for r in got)


def test_a_pinned_fact_is_not_said_twice(conn, story):
    """It is already in the stable block every turn; recalling it again would be the same
    sentence in the same prompt."""
    lore.add(conn, story, BOOK)
    mira = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
    ).fetchone()["id"]
    chat.append_message(conn, story, "user", "Tell me about the Gull, the tavern.")

    got = retrieve.recall(conn, story, mira, "Tell me about the Gull, the tavern.", noise=False)
    assert not [r for r in got if "last tavern" in r.text]


def test_sillytavern_world_info_says_the_same_thing_in_its_own_words(conn, story):
    made = lore.add(conn, story, WORLD_INFO)
    assert (made["made"], made["pinned"]) == (1, 1)
    [only] = memories(conn, story).values()
    assert only["gist"] == "Eldoria is a forest under a guardian's watch." and only["pinned"] == 1
    # `key`, as SillyTavern spells it, plus the label — which here is a word it already had
    assert only["tags_text"] == "eldoria forest"


def test_a_lorebook_file_a_card_and_a_png_all_carry_a_book(conn, story):
    alone = json.dumps({"spec": "lorebook_v3", "data": BOOK}).encode()
    assert lore.add(conn, story, lore.read(alone))["made"] == 2

    card = {"spec": "chara_card_v3", "data": {"name": "Mira", "character_book": BOOK}}
    assert lore.add(conn, story, lore.read(json.dumps(card).encode()))["made"] == 2

    blob = png(ccv3=carded("chara_card_v3", "3.0", {"name": "Mira", "character_book": BOOK}))
    assert lore.add(conn, story, lore.read(blob))["made"] == 2
    assert (
        lore.add(conn, story, lore.read(charx({"name": "M", "character_book": BOOK}, {})))["made"]
        == 2
    )


def test_a_file_with_no_book_in_it_says_so(conn):
    for blob, says in [
        (b"not json", "not a lorebook"),
        (json.dumps({"spec": "lorebook_v3", "data": {"entries": []}}).encode(), "no entries"),
        (json.dumps({"name": "Mira"}).encode(), "no entries"),
        (png(ccv3=carded("chara_card_v3", "3.0", {"name": "Mira"})), "no entries"),
    ]:
        with pytest.raises(lore.BadCard, match=says):
            lore.read(blob)


def test_an_entry_with_nothing_in_it_is_not_a_fact(conn, story):
    book = {"entries": [
        {"keys": ["x"], "content": "   ", "enabled": True},
        {"keys": [], "content": "A fact with no keys is still a fact, if it is constant.",
         "constant": True, "enabled": True},
        {"keys": [], "content": "A keyless entry nothing can cue is nothing.", "enabled": True},
    ]}  # fmt: skip
    made = lore.add(conn, story, book)
    assert made["made"] == 1 and made["pinned"] == 1
    assert len(made["skipped"]) == 2


def test_the_route_takes_a_book_and_the_prompt_shows_it(api, conn):
    item = api.post("/import/card", content=png(
        ccv3=carded("chara_card_v3", "3.0", {"name": "Mira", "character_book": BOOK})
    )).json()["item"]  # fmt: skip
    me = api.post("/library", json={"kind": "character", "name": "Aren", "data": {"persona": True}})
    story = api.post(
        "/stories", json={"title": "Low Tide", "character_ids": [item["id"]],
                          "persona_id": me.json()["id"]},
    ).json()["id"]  # fmt: skip

    # her own book came with her when the story started
    assert len(api.get(f"/stories/{story}/memories").json()) == 2
    # and a book can be dropped on a story at any time; nothing merges, so this makes two more
    again = api.post(f"/stories/{story}/lorebook", content=json.dumps(WORLD_INFO).encode())
    assert again.status_code == 201 and again.json()["made"] == 1
    assert len(api.get(f"/stories/{story}/memories").json()) == 3

    assert api.post(f"/stories/{story}/lorebook", content=b"nonsense").status_code == 422


def test_the_established_facts_block_carries_them(conn, story):
    lore.add(conn, story, BOOK)
    ep = Endpoint(base_url="http://x/v1/", model="m")
    built = context.build(conn, story, None, ep)
    [system] = [m["content"] for m in built.messages if m["role"] == "system"]
    assert "## Established facts" in system and "last tavern on the harbour road" in system


# --- what the review found: a book written by another app, in all its moods -----------------


def test_decorators_are_instructions_and_never_prose(conn, story):
    """A V3 book can carry `@@depth 4` in its content. That is a note to the application, and
    the two the engine has a field for are read; none of them reach the prompt."""
    book = {"entries": [
        {"keys": ["eldoria"], "content": "@@depth 4\n@@role system\nEldoria is a forest."},
        {"keys": [], "content": "@@activate\nThe moon over Eldoria is always full."},
        {"keys": ["ruin"], "content": "@@dont_activate\nThe ruin is a set for later."},
        {"keys": ["tower"], "content": "@@dont_activate\n@@activate\nThe tower still stands."},
    ]}  # fmt: skip
    made = lore.add(conn, story, book)
    assert made["made"] == 3 and made["pinned"] == 2  # the ruin is off; two say @@activate

    by_key = memories(conn, story)
    assert by_key["eldoria"]["detail"] == "Eldoria is a forest."
    assert "@@" not in json.dumps([dict(m) for m in by_key.values()])
    moon = next(m for m in by_key.values() if "moon" in m["detail"])
    assert moon["pinned"] == 1  # @@activate is the decorator spelling of constant
    assert "ruin" not in by_key


def test_keys_written_as_one_string_are_still_keys(conn, story):
    """Some books write `key` as a line rather than a list. A string is iterable, and its
    letters are not an index of anyone's library."""
    book = {"entries": {"0": {"key": "eldoria,forest", "content": "A forest.", "constant": True}}}
    lore.add(conn, story, book)
    [only] = memories(conn, story).values()
    assert only["tags_text"] == "eldoria forest"
    assert library.all_tags(conn) == []  # a cue word inside a story is not a shelf


def test_a_key_that_is_a_macro_is_the_name_it_stands_for(conn, story):
    """An entry keyed on {{user}} is meant to fire when the player is named, not when someone
    says the word "user"."""
    book = {"entries": [{"key": ["{{user}}", "{{char}}"], "comment": "the debt",
                         "content": "The guild remembers a debt of nine crowns."}]}  # fmt: skip
    lore.add(conn, story, book)
    [only] = memories(conn, story).values()
    assert only["tags_text"] == "Aren Mira"

    mira = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
    ).fetchone()["id"]
    chat.append_message(conn, story, "user", "Aren walks in.")
    got = retrieve.recall(conn, story, mira, "Aren walks in.", noise=False)
    assert any("nine crowns" in r.text for r in got)


def test_the_authors_memo_is_a_cue_only_when_there_is_no_other(conn, story):
    """`comment` is a note to a person — "chapter 3 spoilers (bridge)" — and the spec says to
    keep it out of prompt work. It is the only cue there is when an entry has no keys."""
    book = {"entries": [
        {"keys": ["throne"], "comment": "chapter 3, do not delete (bridge)",
         "content": "The throne is hollow."},
        {"keys": [], "comment": "the harbour", "constant": True,
         "content": "The harbour freezes by midwinter."},
    ]}  # fmt: skip
    lore.add(conn, story, book)
    by_key = memories(conn, story)
    assert by_key["throne"]["tags_text"] == "throne"  # the memo is not a word in the story
    assert by_key["the"]["tags_text"] == "the harbour"


def test_a_story_nobody_plays_in_still_gets_a_plain_sentence(conn):
    """Director mode has no persona, and nothing downstream would ever resolve the macro."""
    mira = library.create_item(conn, "character", "Mira", "She keeps the ledger.")
    alone = library.create_story(conn, "Low Tide", character_ids=[mira])
    said = "{{user}} owns the Gull; {{char}} keeps it."
    lore.add(conn, alone, {"entries": [{"keys": ["gull"], "constant": True, "content": said}]})
    [only] = memories(conn, alone).values()
    assert only["detail"] == "the user owns the Gull; Mira keeps it."


def test_a_friend_whose_card_field_is_nonsense_still_starts_a_story(api):
    """`data` is the app's to write, so nothing in it is a shape the engine can count on."""
    odd = api.post(
        "/library", json={"kind": "character", "name": "Oops", "data": {"card": "not a dict"}}
    ).json()
    made = api.post("/stories", json={"title": "Boom", "character_ids": [odd["id"]]})
    assert made.status_code == 201
    assert api.get(f"/stories/{made.json()['id']}/memories").json() == []


def test_json_nested_beyond_reading_is_a_bad_file_not_a_crash(api, conn):
    story = api.post("/stories", json={"title": "Low Tide"}).json()["id"]
    deep = b'{"data":' * 20000 + b"{}" + b"}" * 20000
    assert api.post(f"/stories/{story}/lorebook", content=deep).status_code == 422
    assert api.post("/import/card", content=deep).status_code == 422
