"""One chat turn end to end, against a scripted model."""

import json

import httpx2
import pytest

from kataki import chat, context, extract, library, turns

pytestmark = pytest.mark.anyio


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {
        name: library.create_item(conn, "character", name, description=f"{name}, a regular.")
        for name in ("Mira", "Tobin", "Aren")
    }
    library.update_item(conn, ids["Mira"], data={"aliases": ["the courier"]})
    gull = library.create_item(conn, "place", "The Gull")
    return library.create_story(
        conn,
        "Low Tide",
        character_ids=[ids["Mira"], ids["Tobin"]],
        place_id=gull,
        persona_id=ids["Aren"],
    )


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


async def play(stream):
    return [event async for event in stream]


def path(conn, story):
    return [(m["role"], m["speaker_id"], m["text"]) for m in chat.active_path(conn, story)]


# --- a turn --------------------------------------------------------------------------------


async def test_a_turn_streams_the_reply_and_keeps_it(conn, story, backend):
    backend.say("The tide turned early tonight.")
    events = await play(turns.turn(conn, backend.llm, story, "Evening, Mira."))

    kinds = [kind for kind, _ in events]
    assert kinds[0] == "meta" and kinds[-1] == "done" and kinds.count("token") > 1
    streamed = "".join(value for kind, value in events if kind == "token")
    assert streamed == "The tide turned early tonight."
    assert path(conn, story)[-2:] == [
        ("user", eid(conn, "Aren"), "Evening, Mira."),
        ("assistant", eid(conn, "Mira"), "The tide turned early tonight."),
    ]
    done = events[-1][1]
    assert done["message_id"] == chat.active_path(conn, story)[-1]["id"]
    gen = json.loads(chat.active_path(conn, story)[-1]["gen"])
    assert (gen["role"], gen["model"], gen["finish"]) == ("rp", "rp-model", "stop")


async def test_the_model_is_stopped_before_it_speaks_for_the_user(conn, story, backend):
    backend.say("Fine.")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    stops = backend.requests[0]["stop"]
    assert stops[0] == "\nAren:" and "\nTobin:" in stops and len(stops) <= 4


async def test_a_name_prefix_copied_from_the_history_format_is_dropped(conn, story, backend):
    backend.say("Mira: Hello yourself.")
    events = await play(turns.turn(conn, backend.llm, story, "Hello, Mira."))
    assert "".join(v for k, v in events if k == "token") == "Hello yourself."
    assert path(conn, story)[-1][2] == "Hello yourself."


async def test_thoughts_stream_apart_and_never_enter_the_story(conn, story, backend):
    backend.say({"reasoning_content": "She distrusts him.", "content": "Hm."})
    backend.say("Go on.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert ("thought", "She distrusts him.") in events
    assert path(conn, story)[-1][2] == "Hm."
    assert json.loads(chat.active_path(conn, story)[-1]["gen"])["reasoning"] == "She distrusts him."

    await play(turns.turn(conn, backend.llm, story, "And?"))
    assert "distrusts" not in json.dumps(backend.requests[-1]["messages"])


async def test_a_time_skip_in_what_the_user_writes_moves_the_story_clock(conn, story, backend):
    backend.say("So much has changed.")
    await play(turns.turn(conn, backend.llm, story, "Six years later, Aren returns to the Gull."))
    user = chat.active_path(conn, story)[-2]
    assert user["skip_minutes"] == 6 * 365 * 1440


# --- who speaks ----------------------------------------------------------------------------


async def test_the_character_the_user_addresses_answers(conn, story, backend):
    backend.say("What?")
    events = await play(turns.turn(conn, backend.llm, story, "Tobin, a word."))
    assert events[0][1]["speaker"] == {"id": eid(conn, "Tobin"), "name": "Tobin"}


async def test_an_alias_counts_as_addressing_someone(conn, story, backend):
    backend.say("Yes?")
    await play(turns.turn(conn, backend.llm, story, "Hey, courier."))
    assert path(conn, story)[-1][1] == eid(conn, "Mira")


async def test_with_no_one_named_the_last_speaker_carries_on(conn, story, backend):
    backend.say("Tobin here.", "Still Tobin.")
    await play(turns.turn(conn, backend.llm, story, "Tobin?"))
    await play(turns.turn(conn, backend.llm, story, "And then?"))
    assert path(conn, story)[-1][1] == eid(conn, "Tobin")


async def test_continuing_without_a_line_lets_the_quietest_character_speak(conn, story, backend):
    backend.say("Mira speaks.", "Tobin speaks.")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    await play(turns.turn(conn, backend.llm, story))
    assert path(conn, story)[-1][1] == eid(conn, "Tobin")


async def test_the_narrator_speaks_for_no_one_and_uses_its_own_role(conn, story, backend):
    conn.execute("INSERT INTO model_roles(role, provider_id, model) VALUES('narrator', 1, 'prose')")
    backend.say("Rain hammers the shutters.")
    events = await play(turns.turn(conn, backend.llm, story, "Time passes.", speaker="narrator"))
    assert events[0][1]["speaker"] is None and events[0][1]["role"] == "narrator"
    assert backend.requests[0]["model"] == "prose"
    assert path(conn, story)[-1] == ("assistant", None, "Rain hammers the shutters.")


# --- swipes, stops, failures -----------------------------------------------------------------


async def test_regenerate_adds_a_swipe_built_from_the_same_prompt(conn, story, backend):
    backend.say("First take.", "Second take.")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    first = chat.active_path(conn, story)[-1]
    await play(turns.regenerate(conn, backend.llm, story))
    second = chat.active_path(conn, story)[-1]

    assert (second["parent_id"], second["text"]) == (first["parent_id"], "Second take.")
    assert chat.sibling_position(conn, second["id"]) == (2, 2)
    assert backend.requests[0]["messages"] == backend.requests[1]["messages"]


async def test_stopping_midway_keeps_what_was_written(conn, story, backend):
    backend.say("One two three four five six seven.")
    stream = turns.turn(conn, backend.llm, story, "Mira?")
    seen = []
    async for kind, value in stream:
        if kind == "token":
            seen.append(value)
            if len(seen) == 2:
                break
    await stream.aclose()
    last = chat.active_path(conn, story)[-1]
    assert last["text"] == "".join(seen).strip()
    assert json.loads(last["gen"])["finish"] == "stopped"


async def test_a_failed_call_reports_the_error_and_keeps_no_reply(conn, story, backend):
    backend.say(httpx2.Response(503, text="model is loading"))
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert events[-1][0] == "error" and "model is loading" in events[-1][1]["message"]
    assert path(conn, story)[-1][0] == "user"  # the user's line is kept, no empty reply


async def test_without_a_model_the_error_says_which_role_to_set(conn, backend):
    story = library.create_story(
        conn, "Empty", character_ids=[library.create_item(conn, "character", "X")]
    )
    events = await play(turns.turn(conn, backend.llm, story, "hi"))
    assert events == [("error", {"message": "No model is set for the 'rp' role yet."})]


# --- memory reaches the right prompt ----------------------------------------------------------


async def test_only_the_speaker_s_memories_reach_the_prompt(conn, story, backend):
    aren, mira, tobin = (eid(conn, n) for n in ("Aren", "Mira", "Tobin"))
    chat.append_message(conn, story, "user", "Evening, all.", speaker_id=aren)
    chat.set_presence(conn, story, tobin, False)  # Tobin steps out
    first = chat.append_message(conn, story, "user", "Keep this quiet.", speaker_id=aren)
    last = chat.append_message(conn, story, "assistant", "I will.", speaker_id=mira)
    secret = {
        "kind": "event", "detail": "Aren hid the ledger under the third floorboard.",
        "gist": "Aren hid something.", "importance": 8,
        "participants": [{"ref": f"E{aren}", "role": "actor"}],
    }  # fmt: skip
    extract.apply(
        conn, extract.open_run(conn, story, first, last, "cadence"), {"memories": [secret]}
    )
    chat.set_presence(conn, story, tobin, True)  # and comes back
    for i in range(14):  # enough talk that the exchange scrolls out of the verbatim window
        chat.append_message(conn, story, "user", f"Filler {i}. " + "words " * 60, speaker_id=aren)
    conn.execute(
        "UPDATE model_roles SET params=? WHERE role='rp'", (json.dumps({"ctx_size": 2000}),)
    )

    backend.say("The floorboard.", "What ledger?")
    await play(turns.turn(conn, backend.llm, story, "Mira, where is the ledger?"))
    await play(turns.turn(conn, backend.llm, story, "Tobin, where is the ledger?"))
    to_mira, to_tobin = (json.dumps(r["messages"]) for r in backend.requests)
    assert "third floorboard" in to_mira  # she remembers it, though it has scrolled away
    assert "third floorboard" not in to_tobin  # he was not there


# --- the token budget learns the real tokenizer -----------------------------------------------


async def test_real_usage_calibrates_the_token_estimate(conn, story, backend):
    backend.say("Hm.")  # the fake tokenizer counts four characters per token
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    chars = sum(len(m["content"]) for m in backend.requests[0]["messages"])
    assert context.token_ratio(conn, "rp-model") == pytest.approx(
        0.8 * context.RATIO + 0.2 * chars / (chars // 4)
    )
    log = conn.execute("SELECT actual_tokens, message_id FROM context_log").fetchone()
    assert log["actual_tokens"] == chars // 4 and log["message_id"] is not None
