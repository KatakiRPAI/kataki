import json
from dataclasses import dataclass, field

from kataki import activation, chat, knobs, library


@dataclass
class Ep:
    params: dict = field(default_factory=dict)


def _set(conn, key, value):
    conn.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)", (key, json.dumps(value)))
    conn.commit()


def _story(conn, **data):
    mira = library.create_item(conn, "character", "Mira", data=data)
    story = library.create_story(conn, "T", character_ids=[mira])
    return story, conn.execute("SELECT id FROM entities WHERE story_id=?", (story,)).fetchone()["id"]


def test_fade_follows_the_setting_unless_the_character_says(conn):
    _, mira = _story(conn)
    assert knobs.decay(conn, mira) == activation.DECAY
    _set(conn, "memory.fade", "never")
    assert knobs.decay(conn, mira) == 0.0
    _, slow = _story(conn, fade="slow")
    assert knobs.decay(conn, slow) == knobs.FADE["slow"]


def test_doubt_can_be_switched_off_for_everyone_or_one(conn):
    _, mira = _story(conn)
    assert knobs.can_doubt(conn, mira)
    _set(conn, "memory.canDoubt", False)
    assert not knobs.can_doubt(conn, mira)
    _, sure = _story(conn, doubt=True)
    assert knobs.can_doubt(conn, sure)


def test_everyone_hears_everything_when_asked(conn):
    story, mira = _story(conn)
    chat.set_presence(conn, story, mira, False)
    line = chat.append_message(conn, story, "user", "psst")
    path = chat.active_path(conn, story)
    assert chat.hearing(conn, path, mira)[line] == "away"
    _set(conn, "memory.hearing", "all")
    assert chat.hearing(conn, path, mira)[line] == "heard"


def test_thinking_none_and_a_lot_but_a_role_setting_wins(conn):
    assert knobs.thinking(conn, Ep()).params == {}
    _set(conn, "memory.thinking", "none")
    assert knobs.thinking(conn, Ep()).params == {"thinking": "disabled"}
    _set(conn, "memory.thinking", "lot")
    assert knobs.thinking(conn, Ep()).params["thinking"] == "enabled"
    assert knobs.thinking(conn, Ep({"thinking": "disabled"})).params == {"thinking": "disabled"}


def test_a_characters_authored_relationships_start_the_story(conn):
    theo = library.create_item(conn, "character", "Theo")
    mike = library.create_item(conn, "character", "Mike", data={"relationships": [{"id": theo, "feels": "wary"}]})
    liv = library.create_item(conn, "character", "Liv", data={"persona": True})
    alone = library.create_item(conn, "character", "Jae", data={"relationships": [{"id": liv, "feels": "fond"}]})
    story = library.create_story(conn, "T", character_ids=[mike, theo], persona_id=liv)
    rels = conn.execute(
        "SELECT s.name AS src, d.name AS dst, rel FROM edges e JOIN entities s ON s.id=e.src_id"
        " JOIN entities d ON d.id=e.dst_id WHERE e.story_id=?", (story,)
    ).fetchall()
    assert [(r["src"], r["dst"], r["rel"]) for r in rels] == [("Mike", "Theo", "wary of")]
    assert alone  # someone not in the story brings nothing


def test_a_character_can_have_their_own_model(conn):
    from kataki.llm import Endpoint

    pid = conn.execute("INSERT INTO providers(name, base_url) VALUES('far', 'http://far/v1')").lastrowid
    conn.commit()
    _, plain = _story(conn)
    _, own = _story(conn, model={"provider_id": pid, "model": "big"})
    _, gone = _story(conn, model={"provider_id": 999, "model": "big"})
    ep = Endpoint(base_url="http://near/v1", model="small")
    assert knobs.character_model(conn, plain, ep, lambda n: None) is ep
    assert (knobs.character_model(conn, own, ep, lambda n: "k").base_url, knobs.character_model(conn, own, ep, lambda n: "k").model) == ("http://far/v1", "big")
    assert knobs.character_model(conn, gone, ep, lambda n: None) is ep
