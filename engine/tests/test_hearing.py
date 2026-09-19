"""Whispers and thoughts: who hears a line decides who can ever know it."""

import json

import pytest

from kataki import chat, context, extract, library, retrieve, turns
from kataki.llm import Endpoint

EP = Endpoint(base_url="http://x/v1", model="m", params={"ctx_size": 8192})


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {name: library.create_item(conn, "character", name) for name in ("Mira", "Tobin", "Aren")}
    return library.create_story(
        conn, "Low Tide", character_ids=[ids["Mira"], ids["Tobin"]], persona_id=ids["Aren"]
    )


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


def say(conn, story, text, audience=None, who="Aren"):
    role = "user" if who == "Aren" else "assistant"
    return chat.append_message(conn, story, role, text, eid(conn, who), audience=audience)


def prompt(conn, story, speaker):
    speaker_id = None if speaker is None else eid(conn, speaker)
    return json.dumps(context.build(conn, story, speaker_id, EP).messages, ensure_ascii=False)


def test_a_whisper_is_heard_only_by_the_one_it_is_for(conn, story):
    whisper = say(conn, story, "The ledger is under the third floorboard.", [eid(conn, "Mira")])
    path = chat.active_path(conn, story)
    assert whisper in chat.heard_by(conn, path, eid(conn, "Mira"))
    assert whisper not in chat.heard_by(conn, path, eid(conn, "Tobin"))
    assert whisper in chat.heard_by(conn, path, eid(conn, "Aren"))  # they said it


def test_a_thought_reaches_no_prompt_not_even_the_narrators(conn, story):
    say(conn, story, "Evening, both of you.")
    say(conn, story, "I should never have trusted Tobin.", audience=[])
    for who in ("Mira", "Tobin", None):
        assert "trusted Tobin" not in prompt(conn, story, who)


def test_a_whisper_stays_out_of_tobins_prompt_and_the_narrator_only_sees_that_it_happened(
    conn, story
):
    say(conn, story, "Quickly: the ledger is under the third floorboard.", [eid(conn, "Mira")])
    say(conn, story, "*nods*", who="Mira")
    assert "third floorboard" in prompt(conn, story, "Mira")
    assert "third floorboard" not in prompt(conn, story, "Tobin")
    narrator = prompt(conn, story, None)
    assert "third floorboard" not in narrator and "Aren whispers to Mira." in narrator


def test_the_reply_comes_from_someone_who_heard_the_line(conn, story):
    # Mira is named, but only Tobin heard it
    say(conn, story, "Mira, the ledger is yours to hide.", [eid(conn, "Tobin")])
    assert turns.select_speaker(conn, story) == eid(conn, "Tobin")


def test_after_a_thought_the_quietest_character_carries_on(conn, story):
    say(conn, story, "Evening.")
    say(conn, story, "Evening yourself.", who="Tobin")
    say(conn, story, "Why is Tobin so cheerful tonight?", audience=[])  # nobody hears it
    assert turns.select_speaker(conn, story) == eid(conn, "Mira")


def test_a_whispered_claim_never_reaches_tobin_even_if_the_reader_lists_him(conn, story):
    mira, tobin, aren = (eid(conn, n) for n in ("Mira", "Tobin", "Aren"))
    first = say(conn, story, "The ledger is buried by the lighthouse.", [mira])
    last = say(conn, story, "*nods*", who="Mira")
    run_id = extract.open_run(conn, story, first, last, "cadence")
    claim = {
        "kind": "claim",
        "detail": "Aren says the ledger is buried by the lighthouse.",
        "gist": "Aren says the ledger is hidden somewhere.",
        "importance": 6,
        "participants": [
            {"ref": f"E{aren}", "role": "actor"},
            {"ref": f"E{tobin}", "role": "target"},
        ],
        "asserted_by": f"E{aren}",
        "heard_by": [f"E{mira}", f"E{tobin}"],
        "line": 1,
    }
    extract.apply(conn, run_id, {"memories": [claim]})
    knowers = {r[0] for r in conn.execute("SELECT knower_id FROM knowledge")}
    assert mira in knowers and aren in knowers and tobin not in knowers


def test_the_reader_is_told_which_lines_were_whispered_or_thought(conn, story):
    first = say(conn, story, "The ledger is under the floorboard.", [eid(conn, "Mira")])
    say(conn, story, "I'm so tired of secrets.", audience=[])
    chunk = [m for m in chat.active_path(conn, story) if m["id"] >= first]
    body = extract.prompt(conn, story, chunk)[0][-1]["content"]
    assert "Aren (whispering to Mira): The ledger is under the floorboard." in body
    assert "Aren (thinking; no one hears): I'm so tired of secrets." in body


@pytest.mark.anyio
async def test_asking_someone_absent_to_speak_is_refused_before_anything_is_written(
    conn, story, backend
):
    tobin = eid(conn, "Tobin")
    chat.set_presence(conn, story, tobin, False)
    before = len(chat.active_path(conn, story))
    events = [e async for e in turns.turn(conn, backend.llm, story, "Tobin?", tobin)]
    assert events == [("error", {"message": "Tobin isn't in the scene. Bring them in first."})]
    assert len(chat.active_path(conn, story)) == before and backend.requests == []


@pytest.mark.anyio
async def test_the_speaker_recalls_from_lines_they_heard_not_from_a_whisper(
    conn, story, backend, monkeypatch
):
    cues = []
    monkeypatch.setattr(
        retrieve, "recall", lambda conn, story, who, recent, **kw: cues.append(recent) or []
    )
    say(conn, story, "Tobin, the ledger is under the third floorboard.", [eid(conn, "Tobin")])
    backend.say("Hm?")
    [e async for e in turns.turn(conn, backend.llm, story, None, eid(conn, "Mira"))]
    assert cues and "floorboard" not in cues[0]
