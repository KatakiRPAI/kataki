import json

import pytest

from kataki import chat, context, library
from kataki.context import Recalled
from kataki.llm import Endpoint

EP = Endpoint(base_url="http://x/v1", model="m", params={"ctx_size": 8192})


@pytest.fixture
def story(conn):
    mira = library.create_item(
        conn,
        "character",
        "Mira",
        description="A guild courier.",
        private="Reports to the harbour master.",
    )
    tobin = library.create_item(
        conn, "character", "Tobin", description="A smuggler.", private="Plans to betray the guild."
    )
    you = library.create_item(conn, "character", "Aren", description="A newcomer.")
    gull = library.create_item(conn, "place", "The Gull", description="A dockside tavern.")
    return library.create_story(
        conn, "Low Tide", character_ids=[mira, tobin], place_id=gull, persona_id=you
    )


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


def say(conn, story, who, text):
    if who == "Aren":
        return chat.append_message(conn, story, "user", text, speaker_id=eid(conn, "Aren"))
    return chat.append_message(conn, story, "assistant", text, speaker_id=eid(conn, who))


def flat(messages):
    return json.dumps(messages, ensure_ascii=False)


def test_prompt_runs_stable_to_volatile(conn, story):
    say(conn, story, "Aren", "Evening. Is Tobin around?")
    say(conn, story, "Mira", "He left an hour ago.")
    say(conn, story, "Aren", "Where to?")
    recalled = [Recalled(memory_id=1, tier="sharp", text="Tobin said he was going to the docks.")]
    built = context.build(conn, story, eid(conn, "Mira"), EP, recalled=recalled)

    system, *history = built.messages
    assert system["role"] == "system"
    assert "A guild courier." in system["content"] and "A smuggler." in system["content"]
    assert "A dockside tavern." in system["content"]
    assert [m["role"] for m in history] == ["user", "assistant", "user"]
    assert history[1]["content"] == "Mira: He left an hour ago."
    last = history[-1]["content"]
    assert last.endswith("Aren: Where to?")
    assert "[SHARP] Tobin said he was going to the docks." in last
    assert "Reply only as Mira" in last


def test_only_the_speakers_private_card_is_ever_in_the_prompt(conn, story):
    say(conn, story, "Aren", "Hello.")
    prompt = flat(context.build(conn, story, eid(conn, "Mira"), EP).messages)
    assert "Reports to the harbour master." in prompt
    assert "Plans to betray the guild." not in prompt  # Tobin's secret stays Tobin's

    system = context.build(conn, story, eid(conn, "Tobin"), EP).messages[0]["content"]
    assert "Plans to betray" not in system and "Reports to" not in system  # prefix is speaker-free


def test_the_volatile_tail_is_never_persisted(conn, story):
    say(conn, story, "Aren", "Hello.")
    context.build(
        conn, story, eid(conn, "Mira"), EP, recalled=[Recalled(1, "hazy", "a vague thing")]
    )
    stored = " ".join(r["text"] for r in conn.execute("SELECT text FROM messages"))
    assert "HAZY" not in stored and "Reply only as" not in stored


def test_when_no_user_line_is_pending_the_tail_rides_a_synthetic_one(conn, story):
    say(conn, story, "Aren", "Hello.")
    say(conn, story, "Mira", "Evening.")
    messages = context.build(conn, story, eid(conn, "Tobin"), EP).messages
    assert messages[-1]["role"] == "user" and "Reply only as Tobin" in messages[-1]["content"]


def test_the_tail_goes_before_a_multi_paragraph_user_message_never_inside_it(conn, story):
    say(conn, story, "Aren", "An earlier aside.")
    say(conn, story, "Aren", "First paragraph.\n\nSecond paragraph.")
    last = context.build(conn, story, eid(conn, "Mira"), EP).messages[-1]["content"]
    assert last.endswith("Aren: First paragraph.\n\nSecond paragraph.")
    assert last.index("An earlier aside.") < last.index("Reply only as Mira") < last.index("First")


def test_consecutive_same_role_messages_are_merged(conn, story):
    say(conn, story, "Aren", "Hello.")
    say(conn, story, "Mira", "Evening.")
    say(conn, story, "Tobin", "What do you want?")
    say(conn, story, "Aren", "A word.")
    roles = [m["role"] for m in context.build(conn, story, eid(conn, "Mira"), EP).messages]
    assert roles == ["system", "user", "assistant", "user"]


def test_the_prompt_never_exceeds_the_budget_however_long_the_story(conn, story):
    for i in range(400):
        say(conn, story, "Aren" if i % 2 == 0 else "Mira", f"Line {i}. " + "words " * 60)
    built = context.build(conn, story, eid(conn, "Mira"), EP)
    assert built.est_tokens <= 8192 - built.response_reserve
    assert "Line 399." in flat(built.messages) and "Line 0." not in flat(built.messages)
    history = next(s for s in built.sections if s["name"] == "history")
    assert history["evicted"] > 0 and history["tokens"] <= history["cap"]


def test_history_slides_in_big_chunks_so_the_prefix_survives_most_turns(conn, story):
    for i in range(120):  # fill the window first
        say(conn, story, "Aren" if i % 2 == 0 else "Mira", f"Line {i}. " + "words " * 60)

    breaks, previous = 0, None
    for turn in range(12):
        say(conn, story, "Aren", f"Turn {turn}. " + "words " * 60)
        built = context.build(conn, story, eid(conn, "Mira"), EP)
        if previous is not None:
            stable = flat(previous[:-1])[:-1]  # everything before the last, tail-carrying user line
            breaks += not flat(built.messages).startswith(stable)
        previous = built.messages
        say(conn, story, "Mira", f"Reply {turn}. " + "words " * 60)
    assert breaks <= 2  # a per-turn sliding window would break the cache on all 11


def test_a_reasoning_model_reserves_room_to_think_and_history_shrinks_to_pay_for_it(conn, story):
    for i in range(200):
        say(conn, story, "Aren" if i % 2 == 0 else "Mira", f"Line {i}. " + "words " * 60)
    plain = context.build(conn, story, eid(conn, "Mira"), EP)
    thinker = Endpoint(
        base_url="http://x/v1", model="m", reasoning=True,
        params={"ctx_size": 8192, "think_budget_tokens": 1500},
    )  # fmt: skip
    thinking = context.build(conn, story, eid(conn, "Mira"), thinker)

    assert thinking.response_reserve == plain.response_reserve + 1500
    assert thinking.est_tokens <= 8192 - thinking.response_reserve
    assert len(thinking.messages) < len(plain.messages)


def test_token_estimates_follow_the_calibrated_ratio():
    text = "x" * 3600
    assert context.estimate(text) == 1080  # len/3.6 plus the 8% margin
    assert context.estimate(text, ratio=3.0) == 1296


def test_recalled_memories_degrade_to_gists_then_drop_when_the_memory_budget_is_tight(conn, story):
    say(conn, story, "Aren", "Hello.")
    recalled = [
        Recalled(i, "sharp", f"detail {i} " + "long " * 80, gist=f"gist {i}", activation=float(-i))
        for i in range(40)
    ]
    built = context.build(conn, story, eid(conn, "Mira"), EP, recalled=recalled)
    tail = built.messages[-1]["content"]
    memory = next(s for s in built.sections if s["name"] == "memory")
    assert memory["tokens"] <= memory["cap"]
    assert "detail 0 " in tail  # the strongest keeps its detail
    assert "gist 39" not in tail and "detail 39" not in tail  # the weakest is cut
    assert any(m["rendered"] == "gist" for m in built.memories)


def test_every_turn_is_logged_for_the_inspector_and_old_prompts_are_pruned(conn, story):
    for turn in range(25):
        message = say(conn, story, "Aren", f"Turn {turn}")
        built = context.build(conn, story, eid(conn, "Mira"), EP)
        context.log(conn, story, message, eid(conn, "Mira"), built)
    rows = conn.execute("SELECT prompt, sections FROM context_log ORDER BY id").fetchall()
    assert len(rows) == 25
    assert sum(r["prompt"] is not None for r in rows) == 20
    assert {s["name"] for s in json.loads(rows[-1]["sections"])} >= {"cards", "history", "memory"}
