"""One chat turn end to end, against a scripted model."""

import json

import httpx2
import pytest

from kataki import chat, context, extract, library, retrieve, turns
from kataki.context import Recalled

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


@pytest.mark.parametrize(
    "sign", [" Mira", " — Mira", " - Mira", "\n\n– Mira:", " *Mira*", "\n\n_Mira_"]
)
async def test_a_signature_after_the_last_sentence_is_dropped(conn, story, backend, sign):
    # Qwen3.5-9B on HF ended a reply with "... in the service of the crown." — Payton Lin
    backend.say(f'"Fine." She smiles.{sign}')
    done = (await play(turns.turn(conn, backend.llm, story, "Mira?")))[-1][1]
    assert done["text"] == '"Fine." She smiles.'


async def test_a_memory_note_copied_into_the_reply_is_not_kept(conn, story, backend):
    # Qwen3.5-9B on HF wrote this paragraph into the story, copying the prompt's note format
    backend.say(
        '"Kai," I repeat.\n\nI type a quick thought to my own memory bank: [SHARP] Kai is my '
        'driver.\n\n"Ready?"'
    )
    done = (await play(turns.turn(conn, backend.llm, story, "Hi.")))[-1][1]
    assert done["text"] == '"Kai," I repeat.\n\n"Ready?"'
    assert path(conn, story)[-1][2] == done["text"]


async def test_the_reply_after_years_pass_sees_only_memory_of_the_old_lines(conn, story, backend):
    backend.say("I hid it under the third floorboard.")
    await play(turns.turn(conn, backend.llm, story, "Mira, where is it?"))
    backend.say(json.dumps({}), "So much has changed.")  # the past is read first, then the reply
    await play(turns.turn(conn, backend.llm, story, "Six years later, Aren returns to the Gull."))

    read, reply = backend.requests[-2:]
    assert "response_format" in read and "response_format" not in reply
    assert "floorboard" not in json.dumps(reply["messages"])


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


async def test_a_reply_keeps_why_its_speaker_answered_what_recall_searched_with_and_timings(
    conn, story, backend
):
    backend.say("Yes?", "Evening.", "Tobin speaks.", "Rain.")
    trace = lambda: json.loads(chat.active_path(conn, story)[-1]["gen"])["trace"]  # noqa: E731
    await play(turns.turn(conn, backend.llm, story, "Mira, a word?"))
    got = trace()
    assert (got["why"], got["cue"]) == ("named", "Mira, a word?")
    assert {"prompt", "recall", "first_token", "reply", "total"} <= set(got["ms"])
    assert got["ms"]["first_token"] <= got["ms"]["reply"] <= got["ms"]["total"]
    await play(turns.turn(conn, backend.llm, story, "Anyone?"))
    assert trace()["why"] == "last"  # nobody named: whoever spoke last among those who heard
    await play(turns.turn(conn, backend.llm, story))
    assert trace()["why"] == "quietest"
    await play(turns.turn(conn, backend.llm, story, "Tobin?", speaker=eid(conn, "Mira")))
    assert trace()["why"] == "picked"


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


async def test_rewriting_a_line_starts_a_new_take_from_it_and_keeps_the_old_one(
    conn, story, backend
):
    backend.say("Evening.", "The ledger?", "Back again?")
    await play(turns.turn(conn, backend.llm, story, "Hello."))
    asked = chat.active_path(conn, story)[0]
    await play(turns.turn(conn, backend.llm, story, "The ledger is safe."))
    old = [m["id"] for m in chat.active_path(conn, story)]

    await play(turns.rewrite(conn, backend.llm, story, asked["id"], "Hello again."))
    now = chat.active_path(conn, story)
    assert [m["text"] for m in now] == ["Hello again.", "Back again?"]
    assert (now[0]["parent_id"], now[0]["speaker_id"]) == (asked["parent_id"], asked["speaker_id"])
    assert chat.sibling_position(conn, now[0]["id"]) == (2, 2)
    # the old take, and everything after it, is still there to flip back to
    assert [m["id"] for m in chat.path_to(conn, old[-1])] == old


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


async def test_a_failed_call_reports_the_error_and_keeps_no_reply(
    conn, story, backend, monkeypatch
):
    monkeypatch.setattr("kataki.llm.RETRY_AFTER", 0)
    loading = httpx2.Response(503, text="model is loading")
    backend.say(loading, loading, loading)  # asked twice more, then it is the answer
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


async def test_a_reply_is_capped_at_the_room_the_budget_kept_for_it(conn, story, backend):
    backend.say("Hm.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert backend.requests[0]["max_tokens"] == events[0][1]["context"]["reserve"] == 600


@pytest.mark.parametrize(
    ("reply", "kept"),
    [
        ("Fine. Go on.\n\nMira", "Fine. Go on."),
        ("Fine. Go on. Mira", "Fine. Go on."),
        ('"Fine," she says.\nMira:', '"Fine," she says.'),
        ("They call me Mira", "They call me Mira"),  # her name in a sentence stays
        ("Thank you, Mira.", "Thank you, Mira."),
    ],
)
async def test_a_reply_signed_with_the_speakers_own_name_loses_the_signature(
    conn, story, backend, reply, kept
):
    backend.say(reply)
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert path(conn, story)[-1][2] == kept


# --- passing time, meta, thinking time ----------------------------------------------------


async def test_passing_time_then_continuing_writes_a_marker_and_meta_says_how_far(
    conn, story, backend
):
    backend.say("You look older.")
    events = await play(
        turns.turn(conn, backend.llm, story, None, eid(conn, "Mira"), skip="six years later")
    )
    meta = events[0][1]
    assert meta["skip"] == 6 * 365 * 24 * 60 == 3_153_600
    assert (meta["from_clock"], meta["clock"]) == ("Day 1, 08:02", "Year 7, Day 1, 08:04")
    assert (meta["from_date"], meta["date"]) == ("Day 1", "Year 7, Day 1")
    marker = chat.active_path(conn, story)[-2]
    assert (marker["role"], marker["text"], marker["skip_minutes"]) == (
        "system",
        "— Six years later —",
        3_153_600,
    )


async def test_a_skip_in_the_users_own_line_shows_in_meta(conn, story, backend):
    backend.say("Welcome back.")
    events = await play(turns.turn(conn, backend.llm, story, "Six years later, Aren returns."))
    assert events[0][1]["skip"] == 3_153_600 and events[0][1]["strained"] is False


async def test_meta_says_when_the_speaker_strained_to_recall(conn, story, backend, monkeypatch):
    rolled = Recalled(
        1, "sharp", "Aren hid the ledger under the floorboard.", breakdown={"effortful": True}
    )
    monkeypatch.setattr(retrieve, "recall", lambda *args, **kwargs: [rolled])
    backend.say("Under... the floorboard?")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, where is it?"))
    assert events[0][1]["strained"] is True


async def test_the_time_spent_thinking_is_kept_with_the_reply(conn, story, backend):
    backend.say({"reasoning_content": "She weighs it.", "content": "Fine."}, "Again.")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    gen = json.loads(chat.active_path(conn, story)[-1]["gen"])
    assert isinstance(gen["think_ms"], int) and gen["think_ms"] >= 0
    await play(turns.turn(conn, backend.llm, story, "And?"))  # no thinking, no time
    assert json.loads(chat.active_path(conn, story)[-1]["gen"]).get("think_ms") is None
