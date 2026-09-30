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


# --- what is said ----------------------------------------------------------------------------

CUE = {"tone": "neutral", "intensity": 1, "pause_ms": 250, "speed": 1.0, "tags": [], "by": "code"}


def test_prose_speaks_only_her_quoted_words():
    text = '*Mira sets the glass down.* "Early tide." She looks away. \u201cCome by tomorrow.\u201d'
    assert speech.speakable(text, CUE) == "Early tide. Come by tomorrow."


def test_chat_speaks_everything_but_her_actions():
    assert speech.speakable("honestly? *shrugs* no idea\nask Tobin", CUE) == (
        "honestly? no idea ask Tobin"
    )
    assert speech.speakable("*nods*", CUE) == ""  # nothing to say
    assert speech.speakable("[laughs] *sighs*", {**CUE, "tags": ["sigh"]}) == ""


def test_the_tag_is_rendered_for_the_engine_where_she_made_the_sound():
    sigh = {**CUE, "tags": ["sigh"]}
    text = "Fine. *sighs* Whatever you want."
    assert speech.speakable(text, sigh) == "Fine. Hah... Whatever you want."
    assert speech.speakable(text, sigh, "brackets") == "Fine. [sigh] Whatever you want."
    assert speech.speakable(text, sigh, "angle") == "Fine. <sigh> Whatever you want."
    laugh = {**CUE, "tags": ["laugh"]}
    assert speech.speakable('"You wish."', laugh, "brackets") == "[laugh] You wish."
    assert speech.speakable("sure", {**CUE, "tags": ["sniff"]}) == "sure"  # no sound for it


def test_instructions_are_words():
    got = speech.instruct({**CUE, "tone": "hurt", "intensity": 3})
    assert got.startswith("Speak") and not any(ch.isdigit() for ch in got)


# --- the adapter and the cache ---------------------------------------------------------------

MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 64


def _audio(data=MP3, status=200):
    import httpx2

    return httpx2.Response(status, content=data)


@pytest.fixture
def voiced(mira):
    conn = mira["conn"]
    _voice_role(conn)
    _set(conn, "voice.on", True)
    from kataki import chat

    line = chat.add_child(conn, mira["story"], None, "user", "Evening.", None)
    gen = {"mind": _mood("sad", feels="very sad")}
    reply = chat.add_child(
        conn, mira["story"], line, "assistant", '*sighs* "Evening."', mira["id"], 0, gen
    )
    return {**mira, "reply": reply}


@pytest.mark.anyio
async def test_speech_posts_the_openai_shape_and_meters_characters(voiced, backend):
    from kataki import roles

    conn = voiced["conn"]
    backend.say(_audio())
    llm = backend.llm
    used = []
    llm.on_usage = lambda ep, usage: used.append((ep.role, usage))
    ep = roles.resolve(conn, "voice", get_key=lambda _: "k")
    got = await llm.speech(ep, "Evening.", "af_heart", 0.9, "mp3", "Speak sadly.")
    assert got == MP3
    assert backend.requests[-1] == {
        "model": "kokoro",
        "input": "Evening.",
        "voice": "af_heart",
        "speed": 0.9,
        "response_format": "mp3",
        "instructions": "Speak sadly.",
    }
    assert used == [("voice", {"prompt_tokens": len("Evening.")})]


@pytest.mark.anyio
@pytest.mark.parametrize("reply", [_audio(b"<html>busy</html>"), _audio(b"nope", 500)])
async def test_speech_raises_on_an_error_or_no_audio(voiced, backend, reply):
    from kataki import roles
    from kataki.llm import LLMError

    backend.say(reply)
    ep = roles.resolve(voiced["conn"], "voice", get_key=lambda _: None)
    with pytest.raises(LLMError):
        await backend.llm.speech(ep, "Evening.", "af_heart", 1.0, "mp3")


@pytest.mark.anyio
async def test_render_saves_once_and_replays_for_free(voiced, backend):
    from kataki import chat, media

    conn = voiced["conn"]
    backend.say(_audio())
    first = await speech.render(conn, backend.llm, voiced["reply"])
    assert first["cached"] is False and first["voice"] == "af_heart"
    assert first["url"] == f"/media/{first['media']}" and first["media"].endswith(".mp3")
    assert media.find(conn, first["media"]).read_bytes() == MP3
    assert first["cue"]["tone"] == "sad" and first["cue"]["tags"] == ["sigh"]
    assert backend.requests[-1]["input"] == "Hah... Evening."
    assert first["chars"] == len("Hah... Evening.")
    again = await speech.render(conn, backend.llm, voiced["reply"])
    assert again == {**first, "cached": True} and len(backend.requests) == 1
    gen = json.loads(chat.get_message(conn, voiced["reply"])["gen"])
    assert list(gen["voice"]["audio"].values()) == [first["media"]]

    library.update_item(conn, voiced["lib"], data={"voice": {"name": "bf_emma"}})
    backend.say(_audio(MP3 + b"\x01"))
    other = await speech.render(conn, backend.llm, voiced["reply"])
    assert other["cached"] is False and backend.requests[-1]["voice"] == "bf_emma"


@pytest.mark.anyio
async def test_render_refuses_what_it_cannot_say(voiced, backend):
    from kataki import chat

    conn = voiced["conn"]
    with pytest.raises(speech.Refused) as e:
        await speech.render(conn, backend.llm, 999)
    assert e.value.status == 404
    user_line = chat.get_message(conn, voiced["reply"])["parent_id"]
    with pytest.raises(speech.Refused) as e:
        await speech.render(conn, backend.llm, user_line)
    assert e.value.status == 404
    silent = chat.add_child(conn, voiced["story"], None, "assistant", "*nods*", voiced["id"])
    with pytest.raises(speech.Refused) as e:
        await speech.render(conn, backend.llm, silent)
    assert e.value.status == 422
    _set(conn, "voice.on", False)
    with pytest.raises(speech.Refused) as e:
        await speech.render(conn, backend.llm, voiced["reply"])
    assert e.value.status == 409
    assert backend.requests == []


# --- the route -------------------------------------------------------------------------------


@pytest.fixture
def api(voiced, backend):
    from fastapi.testclient import TestClient

    from kataki.server import create_app

    client = TestClient(create_app(voiced["conn"], "t", llm=backend.llm, worker_delay=60))
    client.headers["Authorization"] = "Bearer t"
    with client:
        yield client


def test_the_app_asks_for_a_replys_audio_and_a_replay_is_free(api, voiced, backend):
    backend.say(_audio())
    first = api.post(f"/messages/{voiced['reply']}/voice")
    assert first.status_code == 200
    body = first.json()
    assert body["cached"] is False and body["cue"]["tone"] == "sad"
    again = api.post(f"/messages/{voiced['reply']}/voice").json()
    assert again["cached"] is True and again["media"] == body["media"]
    assert len(backend.requests) == 1
    heard = api.get(f"{body['url']}?token=t", headers={"Authorization": ""})
    assert heard.status_code == 200 and heard.content == MP3
    assert heard.headers["content-type"] == "audio/mpeg"
    assert api.post("/media", content=MP3).status_code == 415  # never an upload


def test_the_route_says_why_there_is_no_audio(api, voiced, backend):
    assert api.post("/messages/999/voice").status_code == 404
    backend.say(_audio(b"oops", 500))
    failed = api.post(f"/messages/{voiced['reply']}/voice")
    assert failed.status_code == 502
    gen = json.loads(
        voiced["conn"]
        .execute("SELECT gen FROM messages WHERE id=?", (voiced["reply"],))
        .fetchone()["gen"]
    )
    assert "voice" not in gen  # nothing saved; ask again
    _set(voiced["conn"], "features.mind.voice", False)
    assert api.post(f"/messages/{voiced['reply']}/voice").status_code == 409
