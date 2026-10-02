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
        data={"looks": "A wiry woman in an oilskin coat."},
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
    assert "A wiry woman in an oilskin coat." in system["content"]  # what anyone can see
    assert "A guild courier." not in system["content"]  # who she is: hers, not shared
    assert "A dockside tavern." in system["content"]
    assert [m["role"] for m in history] == ["user", "assistant", "user"]
    assert history[1]["content"] == "Mira: He left an hour ago."
    last = history[-1]["content"]
    assert last.endswith("Aren: Where to?")
    assert "[SHARP] Tobin said he was going to the docks." in last
    assert "Reply only as Mira" in last
    assert "[Who Mira is]\nA guild courier." in last


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


def test_world_state_shows_what_anyone_could_see_plus_only_the_speakers_private_flags(conn, story):
    say(conn, story, "Aren", "Hello.")
    flags = [
        ("Tobin", "injured", "cut on the left hand", 0),
        ("Tobin", "plans", "to sell the ledger", 1),
        ("Mira", "owes", "forty silver to the guild", 1),
        ("Mira", "holding", "a lantern", 0),
        ("Mira", "holding", None, 0),  # later cleared
    ]
    for name, key, value, private in flags:
        conn.execute(
            "INSERT INTO flags(entity_id, key, value, story_time, private) VALUES(?, ?, ?, 0, ?)",
            (eid(conn, name), key, value, private),
        )
    tail = context.build(conn, story, eid(conn, "Mira"), EP).messages[-1]["content"]
    assert "Tobin: injured: cut on the left hand" in tail
    assert "owes: forty silver to the guild" in tail
    assert "to sell the ledger" not in tail  # Tobin's private state is his alone
    assert "lantern" not in tail  # cleared


def test_scene_summaries_never_reach_a_characters_prompt(conn, story):
    # found against a real model: the reader summarised a secret told while Tobin was out, and
    # the shared block put that summary in front of Tobin. What someone knows comes only from
    # their own memory; summaries are for the app to show.
    first = say(conn, story, "Aren", "Mira, the ledger is under the third floorboard.")
    reply = say(conn, story, "Mira", "I'll keep it.")
    run = conn.execute(
        "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger, status)"
        " VALUES(?, ?, ?, 'cadence', 'ok')",
        (story, first, reply),
    ).lastrowid
    conn.execute(
        "INSERT INTO summaries(story_id, text, run_id) VALUES(?, 'Aren told Mira of the"
        " floorboard.', ?)",
        (story, run),
    )
    say(conn, story, "Aren", "Tobin, what do you know?")
    prompt = json.dumps(context.build(conn, story, eid(conn, "Tobin"), EP).messages)
    assert "Aren told Mira" not in prompt


def test_the_window_start_is_reported_for_recall(conn, story):
    for i in range(300):
        say(conn, story, "Aren" if i % 2 == 0 else "Mira", f"Line {i}. " + "words " * 60)
    built = context.build(conn, story, eid(conn, "Mira"), EP)
    first_shown = conn.execute(
        "SELECT text FROM messages WHERE id=?", (built.window_start,)
    ).fetchone()["text"]
    assert first_shown.split(".")[0] in json.dumps(built.messages)
    assert built.window_start > chat.active_path(conn, story)[0]["id"]


def test_a_character_never_hears_what_was_said_while_they_were_out(conn, story):
    say(conn, story, "Aren", "Evening.")
    chat.set_presence(conn, story, eid(conn, "Tobin"), False)
    say(conn, story, "Aren", "The ledger is under the floorboard.")
    say(conn, story, "Mira", "Understood.")
    chat.set_presence(conn, story, eid(conn, "Tobin"), True)
    say(conn, story, "Aren", "Tobin! Welcome back.")

    to_tobin = flat(context.build(conn, story, eid(conn, "Tobin"), EP).messages)
    to_mira = flat(context.build(conn, story, eid(conn, "Mira"), EP).messages)
    narrator = flat(context.build(conn, story, None, EP).messages)
    assert "floorboard" in to_mira and "floorboard" in narrator
    assert "floorboard" not in to_tobin and "Understood." not in to_tobin
    assert "Evening." in to_tobin and "Welcome back." in to_tobin
    assert "present: Mira, Tobin, Aren" in to_tobin  # he is back in the room


def test_only_the_speakers_example_dialogue_is_sent_and_it_is_capped(conn, story):
    conn.execute(
        "UPDATE entities SET examples='Mira: Coin first. Questions after.' WHERE name='Mira'"
    )
    conn.execute("UPDATE entities SET examples=? WHERE name='Tobin'", ("Tobin: Heh. " * 400,))
    say(conn, story, "Aren", "Hello.")

    to_mira = context.build(conn, story, eid(conn, "Mira"), EP)
    assert "[How Mira talks]\nMira: Coin first. Questions after." in to_mira.messages[-1]["content"]
    assert "Tobin: Heh." not in flat(to_mira.messages)
    assert "Coin first" not in to_mira.messages[0]["content"]  # never in the shared, cached part

    to_tobin = context.build(conn, story, eid(conn, "Tobin"), EP)
    examples = next(s for s in to_tobin.sections if s["name"] == "examples")
    assert 0 < examples["tokens"] <= examples["cap"] and examples["evicted"] == 1


def test_a_long_time_skip_closes_the_verbatim_window_once_the_past_is_in_memory(conn, story):
    first = say(conn, story, "Aren", "The ledger is under the third floorboard.")
    last = say(conn, story, "Mira", "I will remember.")
    skip = chat.append_message(
        conn, story, "user", "Six years later, Aren returns.", eid(conn, "Aren"), 6 * 525600
    )
    say(conn, story, "Mira", "You look older.")
    say(conn, story, "Aren", "Where did I hide it?")
    assert "third floorboard" in flat(context.build(conn, story, eid(conn, "Mira"), EP).messages)

    run = conn.execute(  # the stretch before the skip has been read into memory
        "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger, status)"
        " VALUES(?, ?, ?, 'skip', 'ok')",
        (story, first, last),
    ).lastrowid
    built = context.build(conn, story, eid(conn, "Mira"), EP)
    assert "third floorboard" not in flat(built.messages)  # six years on, only memory has it
    assert "Six years later" in flat(built.messages) and built.window_start == skip
    assert run


def test_a_story_keeps_the_premise_it_started_with(conn):
    mira = library.create_item(conn, "character", "Mira")
    plot = library.create_item(
        conn, "scenario", "The Missing Ledger", description="The guild ledger has vanished."
    )
    story = library.create_story(conn, "s", character_ids=[mira], scenario_id=plot)

    def system():
        return context.build(conn, story, eid(conn, "Mira"), EP).messages[0]["content"]

    assert "## Scenario\nThe guild ledger has vanished." in system()
    library.update_item(conn, plot, description="Rewritten in the library.")
    assert "The guild ledger has vanished." in system() and "Rewritten" not in system()
    library.delete_item(conn, plot)
    assert "The guild ledger has vanished." in system()


def test_deleting_the_plot_of_an_older_story_copies_its_premise_into_the_story_first(conn):
    mira = library.create_item(conn, "character", "Mira")
    plot = library.create_item(conn, "scenario", "Frost", description="The pass is snowed in.")
    story = library.create_story(conn, "s", character_ids=[mira], scenario_id=plot)
    with conn:  # a story from before premises were copied reads the library row
        conn.execute("UPDATE stories SET overrides='{}' WHERE id=?", (story,))
    library.delete_item(conn, plot)
    row = conn.execute("SELECT scenario_id, overrides FROM stories").fetchone()
    assert row["scenario_id"] is None and json.loads(row["overrides"]) == {
        "premise": "The pass is snowed in."
    }
    prompt = context.build(conn, story, eid(conn, "Mira"), EP).messages[0]["content"]
    assert "## Scenario\nThe pass is snowed in." in prompt


def test_how_the_speaker_feels_about_whoever_is_here_is_in_their_prompt_and_logged(conn, story):
    say(conn, story, "Aren", "Hello.")
    mira, tobin, aren = eid(conn, "Mira"), eid(conn, "Tobin"), eid(conn, "Aren")
    edges = [
        (mira, aren, "distrusts", "He lied about the ledger.", 0),
        (mira, aren, "trusts", "Aren trusted her with the ledger.", 0),  # the latest wins
        (mira, tobin, "resents", None, 1),  # ended: no longer
        (tobin, aren, "fears", None, 0),  # Tobin's, not Mira's
    ]
    for src, dst, rel, note, ended in edges:
        conn.execute(
            "INSERT INTO edges(story_id, src_id, dst_id, rel, note, story_time, ended)"
            " VALUES(?,?,?,?,?,0,?)",
            (story, src, dst, rel, note, ended),
        )
    built = context.build(conn, story, mira, EP)
    tail = built.messages[-1]["content"]
    assert "[How Mira feels]\n- trusts Aren (Aren trusted her with the ledger.)" in tail
    assert "distrusts" not in tail and "resents" not in tail and "fears" not in tail
    trusts = conn.execute("SELECT id FROM edges WHERE rel='trusts'").fetchone()["id"]
    assert next(s for s in built.sections if s["name"] == "tail")["feelings"] == [trusts]
    narrated = context.build(conn, story, None, EP).messages[-1]["content"]
    assert "feels]" not in narrated  # the narrator voices no one's feelings


def test_others_know_only_what_anyone_can_see(conn, story):
    # Kai's description said he came from a combat family; Payton read it and called him a
    # fighter without ever being told. Who someone is stays in their own prompt.
    say(conn, story, "Aren", "Hello.")
    tobin = flat(context.build(conn, story, eid(conn, "Tobin"), EP).messages)
    assert "A guild courier." not in tobin and "A newcomer." not in tobin
    assert "A wiry woman in an oilskin coat." in tobin
    assert "A smuggler." in tobin  # his own


def test_how_chatty_replies_are_is_a_setting(conn, story):
    say(conn, story, "Aren", "Hello.")
    last = lambda: context.build(conn, story, eid(conn, "Mira"), EP).messages[-1]["content"]  # noqa: E731
    assert context.LENGTHS["medium"] in last()  # the default
    conn.execute("INSERT INTO settings(key, value) VALUES('reply_length', '\"short\"')")
    assert context.LENGTHS["short"] in last() and context.LENGTHS["medium"] not in last()


def test_the_rules_keep_notes_out_of_the_story_and_the_story_in_english(conn, story):
    say(conn, story, "Aren", "Hello.")
    system = context.build(conn, story, eid(conn, "Mira"), EP).messages[0]["content"]
    assert "English" in system and "never mention" in system.lower()


def test_every_reply_is_told_how_far_the_story_may_go(conn, story):
    say(conn, story, "Aren", "Hello.")

    def system():
        return context.build(conn, story, eid(conn, "Mira"), EP).messages[0]["content"]

    assert context.CONTENT["mature"] in system() and context.NEVER in system()  # the default
    for level in ("gentle", "explicit"):
        conn.execute(
            "INSERT OR REPLACE INTO settings(key, value) VALUES('content.level', ?)",
            (json.dumps(level),),
        )
        assert (
            context.CONTENT[level] in system() and context.NEVER in system()
        )  # the line never goes
    conn.execute(
        "INSERT OR REPLACE INTO settings(key, value) VALUES('content.level', '\"anything\"')"
    )
    assert context.CONTENT["mature"] in system()  # an unknown level is the default
    avoid = ["spiders", "  ", 7, "x" * 60] + [f"t{i}" for i in range(30)]
    conn.execute(
        "INSERT OR REPLACE INTO settings(key, value) VALUES('content.avoid', ?)",
        (json.dumps(avoid),),
    )
    said = system()
    assert "Keep these out of the story entirely" in said and "spiders; " + "x" * 40 + ";" in said
    assert "t17" in said and "t18" not in said  # twenty at most


def test_the_inside_block_sits_before_the_directive_and_is_capped(conn, story):
    inside = "[Inside Mira right now: show it, never say it]\nFeeling: hurt."
    built = context.build(conn, story, eid(conn, "Mira"), EP, inside=inside)
    tail = built.messages[-1]["content"]
    assert tail.index("[Inside Mira") < tail.index("[Directive]")
    mind = next(s for s in built.sections if s["name"] == "mind")
    assert 0 < mind["tokens"] <= mind["cap"]
    assert "never state it" in built.messages[0]["content"]  # the one RULES line
