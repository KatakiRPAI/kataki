"""Slice 10: she sounds like herself. The cue, what is spoken, the cache."""

import json

import pytest

from kataki import library, speech


def _set(conn, key, value):
    conn.execute(
        "INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)", (key, json.dumps(value))
    )
    conn.commit()


@pytest.fixture
def mira(local_model):
    conn = local_model
    lib = library.create_item(conn, "character", "Mira")
    story = library.create_story(conn, "Low Tide", character_ids=[lib])
    who = conn.execute("SELECT id FROM entities WHERE name='Mira'").fetchone()["id"]
    return {"conn": conn, "lib": lib, "story": story, "id": who}


def _voice_role(conn):
    conn.execute("INSERT INTO providers(id, name, base_url) VALUES(2, 'tts', 'http://tts/v1')")
    conn.execute("INSERT INTO model_roles(role, provider_id, model) VALUES('voice', 2, 'kokoro')")
    conn.commit()


# --- who is voiced ---------------------------------------------------------------------------


def test_voice_is_off_until_a_voice_model_and_the_setting_are_there(mira):
    conn, who = mira["conn"], mira["id"]
    assert not speech.on(conn, who)  # no voice role
    _voice_role(conn)
    assert not speech.on(conn, who)  # off by default
    _set(conn, "voice.on", True)
    assert speech.on(conn, who)
    library.update_item(conn, mira["lib"], data={"voice": {"on": False}})
    assert not speech.on(conn, who)  # her own choice wins
    library.update_item(conn, mira["lib"], data={"voice": {"on": "inherit"}})
    assert speech.on(conn, who)
    _set(conn, "features.mind.voice", False)
    assert not speech.on(conn, who)
    assert not speech.on(conn, None)  # the narrator has no voice of her own


def test_the_voice_role_never_inherits_the_reply_model(local_model):
    from kataki import roles

    assert roles.resolve(local_model, "voice") is None


# --- the cue ---------------------------------------------------------------------------------


def _mood(label, shows=None, feels=None, word=""):
    return {"label": label, "shows": shows or label, "feels": feels or label, "word": word}


def test_tone_follows_what_she_shows_not_what_she_hides():
    hurt = speech.cue({"mind": _mood("hurt", feels="very hurt")}, "Fine.")
    assert hurt["tone"] == "hurt" and hurt["intensity"] == 3 and hurt["by"] == "code"
    masked = speech.cue({"mind": _mood("hurt", shows="calm", feels="very hurt")}, "Fine.")
    assert masked["tone"] == "neutral" and masked["intensity"] == 1
    glad = speech.cue({"mind": _mood("amused", feels="a little amused")}, "Ha, sure.")
    assert glad["tone"] == "cheerful" and glad["intensity"] == 1
    low = speech.cue({"mind": {"label": None, "shows": "calm", "feels": "low", "word": "low"}}, "x")
    assert low["tone"] == "sad" and low["intensity"] == 1
    rest = speech.cue({}, "Evening.")
    assert rest == {
        "tone": "neutral",
        "intensity": 1,
        "pause_ms": rest["pause_ms"],
        "speed": 1.0,
        "tags": [],
        "by": "code",
    }


def test_a_sad_line_waits_longer_and_speaks_slower_than_an_excited_one():
    sad = speech.cue({"mind": _mood("sad")}, "x")
    excited = speech.cue({"mind": _mood("excited")}, "x")
    assert sad["pause_ms"] > excited["pause_ms"] and sad["speed"] < 1.0 < excited["speed"]
    very = speech.cue({"mind": _mood("sad", feels="very sad")}, "x")
    assert very["speed"] < sad["speed"]  # stronger shows more


def test_her_own_speed_scales_the_tone_and_everything_is_clamped():
    slow = speech.cue({"mind": _mood("sad")}, "x", {"speed": 0.8})
    assert slow["speed"] == pytest.approx(speech.cue({"mind": _mood("sad")}, "x")["speed"] * 0.8)
    assert speech.cue({}, "x", {"speed": 9})["speed"] == 2.0
    assert speech.cue({}, "x", {"speed": "fast"})["speed"] == 1.0


def test_one_tag_at_most_her_own_action_first():
    got = speech.cue({}, "*sighs heavily* Fine. *laughs* Whatever.")
    assert got["tags"] == ["sigh"]
    stripped = speech.cue({"voice": {"tags": ["laugh"]}}, "Fine.")
    assert stripped["tags"] == ["laugh"]
    side = {"after": {"voice": {"tone": "cold", "tag": "groan"}}}
    by_side = speech.cue(side, "Fine.")
    assert by_side["tone"] == "cold" and by_side["tags"] == ["groan"] and by_side["by"] == "side"
    assert speech.cue(side, "*chuckles* Fine.")["tags"] == ["chuckle"]  # hers wins


def test_the_side_calls_labels_are_checked():
    bad = {"after": {"voice": {"tone": "sultry", "tag": "scream"}}, "mind": _mood("glad")}
    got = speech.cue(bad, "Hi.")
    assert got["tone"] == "cheerful" and got["tags"] == [] and got["by"] == "code"
    for junk in (None, "x", {"mind": "calm", "after": "skipped", "voice": []}):
        assert speech.cue(junk, "Hi.")["tone"] == "neutral"


def test_untag_takes_out_speech_tags_only():
    text, tags = speech.untag("[laughs] Oh, stop. <sigh> Fine. [OOC] and *sighs*")
    assert text == "Oh, stop. Fine. [OOC] and *sighs*" and tags == ["laugh", "sigh"]
    assert speech.untag("No tags here.") == ("No tags here.", [])
    assert speech.untag("[Laugh]\nLine two.") == ("Line two.", ["laugh"])
