"""Slice 7: she wants something. The card's want becomes a goal she brings up at an opening, drops
when it is dodged twice and raises again later; her needs and energy show as behaviour."""

import json

import pytest

from kataki import chat, goals, inner, library

BOAT = {"text": "to get Aren to come and see the boat she built", "cue": ["boat", "sail"]}


@pytest.fixture
def cards(conn):
    return {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}


def make(conn, cards, mira: dict | None = None) -> int:
    library.update_item(conn, cards["Mira"], data={"mind": mira or {}})
    return library.create_story(
        conn, "Low Tide", character_ids=[cards["Mira"], cards["Tobin"]], persona_id=cards["Aren"]
    )


def ent(conn, story: int, name: str) -> int:
    return conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name=?", (story, name)
    ).fetchone()[0]


def line(conn, story: int, who: str, text: str, skip: int = 0, gen: dict | None = None) -> int:
    role = "user" if who == "Aren" else "assistant"
    mid = chat.append_message(conn, story, role, text, ent(conn, story, who), skip)
    if gen is not None:
        with conn:
            conn.execute("UPDATE messages SET gen=? WHERE id=?", (json.dumps(gen), mid))
    return mid


def path(conn, story: int) -> list:
    return chat.active_path(conn, story)


# --- goals from the card -------------------------------------------------------------------------


def test_want_need_fear_and_listed_goals_become_her_goals(conn, cards):
    story = make(
        conn,
        cards,
        {
            "want": BOAT,
            "need": "to let someone help her",
            "fear": "being left behind",
            "goals": [
                {"text": "save for a bigger workshop", "tier": "ambition", "priority": 0.4},
                "junk",
                {"text": " "},
                {"text": "fix the pier", "tier": "someday", "priority": "high"},
            ],
        },
    )
    mira = ent(conn, story, "Mira")
    got = {g["key"]: g for g in goals.live(conn, mira, path(conn, story))}
    assert set(got) == {"want", "need", "fear", "g1", "g2"}
    assert got["want"]["status"] == "active" and got["want"]["cue"] == ["boat", "sail"]
    assert got["want"]["tier"] == "project"
    assert got["need"]["status"] == got["fear"]["status"] == "dormant"  # never pursued
    assert got["g1"]["tier"] == "ambition" and got["g1"]["priority"] == 0.4
    assert got["g2"]["tier"] == "project" and got["g2"]["priority"] == 0.5  # bad values: defaults
    assert got["g1"]["cue"] == ["workshop"]  # its own nouns, when none given
    assert all(g["message_id"] is None and g["run_id"] is None for g in got.values())
    tobin = ent(conn, story, "Tobin")
    assert goals.live(conn, tobin, path(conn, story)) == []


def test_a_malformed_card_never_breaks_the_story(conn, cards):
    story = make(conn, cards, {"want": 7, "need": ["x"], "goals": {"text": "x"}})
    assert goals.live(conn, ent(conn, story, "Mira"), path(conn, story)) == []


def test_cue_words_leave_out_small_words_and_names():
    assert goals.cues("to get Aren to come and see the boat she built", {"aren"}) == ["boat"]
    assert goals.cues("I want THE harbour-master's job!") == ["harbour", "master", "job"]
    assert goals.cues("save for a bigger workshop, finally working") == ["workshop"]
    # short and common nouns are topics, not verbs or adjectives (minds spec, owed 7)
    assert goals.cues("the ring from the shed, for the wedding") == ["ring", "shed", "wedding"]
    assert goals.cues("see her family by the sea") == ["family", "sea"]


def test_the_cards_own_topic_words_need_three_letters(conn, cards):
    story = make(conn, cards, {"want": {"text": "see the boat", "cue": ["a", "sea", "Boat"]}})
    want = goals.live(conn, ent(conn, story, "Mira"), path(conn, story))[0]
    assert want["cue"] == ["sea", "boat"]  # "a" would match anything; "sea" is a topic


def test_the_latest_version_on_this_branch_is_the_goal(conn, cards):
    story = make(conn, cards, {"want": BOAT})
    mira = ent(conn, story, "Mira")
    root = line(conn, story, "Aren", "Morning.")
    here = line(conn, story, "Mira", "Morning!")
    first = goals.live(conn, mira, path(conn, story))[0]
    now = path(conn, story)[-1]["story_time"]
    with conn:
        goals.write(conn, first, here, None, now, status="dormant", deflections=2)
    assert goals.live(conn, mira, path(conn, story))[0]["status"] == "dormant"
    other = chat.add_child(conn, story, root, "assistant", "Hi.", mira, 0, {})
    chat.set_leaf(conn, story, other)
    assert goals.live(conn, mira, path(conn, story))[0]["status"] == "active"


def test_merged_people_keep_their_goals(conn, cards):
    story = make(conn, cards, {"want": BOAT})
    mira, tobin = ent(conn, story, "Mira"), ent(conn, story, "Tobin")
    library.merge_entities(conn, tobin, mira)
    assert [g["key"] for g in goals.live(conn, tobin, path(conn, story))] == ["want"]


# --- the agenda ----------------------------------------------------------------------------------


def test_an_opening_is_its_topic_an_open_question_or_a_lull():
    cue = ["boat", "sail"]
    assert goals.opening("Saw some boats down at the pier.", cue) == "topic"
    assert goals.opening("So, what's new with you?", cue) == "asked"
    assert goals.opening("How was your week, Mira?", cue) == "asked"
    assert goals.opening("Morning, Mira.", cue) == "lull"
    assert goals.opening("Did the rope shipment come in yet?", cue) is None
    assert goals.opening("We need to talk about the accounts before the inspector.", cue) is None
    assert goals.tried("I finished the boat! Come see her.", cue)
    assert not goals.tried("The shipment came in, yes.", cue)


from kataki import turns  # noqa: E402


async def play(stream):
    return [e async for e in stream]


def setting(conn, key: str, value) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)", (key, json.dumps(value))
    )
    conn.commit()


def directive_of(backend, i=-1) -> str:
    return backend.requests[i]["messages"][-1]["content"].split("[Directive]")[1]


def gen_of(conn, story) -> dict:
    return json.loads(path(conn, story)[-1]["gen"])


async def talk(conn, backend, story, text, reply, skip=None) -> dict:
    """Aren says `text` to Mira, who replies `reply`. -> the reply's gen."""
    backend.say(reply)
    mira = ent(conn, story, "Mira")
    events = await play(turns.turn(conn, backend.llm, story, text, speaker=mira, skip=skip))
    assert events[-1][0] == "done", events[-1]
    return gen_of(conn, story)


WANT = "Something you want: to get Aren to come and see the boat she built."


@pytest.mark.anyio
async def test_she_brings_it_up_only_at_an_opening_and_at_most_once_every_four_replies(
    local_model, cards, backend
):
    conn = local_model
    story = make(conn, cards, {"want": BOAT})
    said = [
        ("Did the rope shipment come in yet?", "It did."),  # no opening
        ("Morning, Mira.", "Morning! I finished the boat, you know."),  # a lull: offered, tried
        ("Great. Did Tobin pay his tab?", "He did."),  # dodged
        ("Nice.", "Mm."),  # a lull, but too soon
        ("Right.", "Yes."),
        ("Okay.", "The boat is ready to sail."),  # four replies on: offered again
    ]
    got = [await talk(conn, backend, story, text, reply) for text, reply in said]
    offered = [i for i, g in enumerate(got) if g.get("agenda")]
    assert offered == [1, 5]
    assert WANT in directive_of(backend, 1) and WANT not in directive_of(backend, 0)
    assert not any(ch.isdigit() for ch in directive_of(backend, 1).split("First, before")[0])
    first = got[1]["agenda"]
    assert first["why"] == "lull" and first["tried"] is True and first["resurfaced"] is False
    assert first["key"] == "want" and first["text"] == BOAT["text"]
    assert got[2]["goal"]["outcome"] == "deflected" and got[2]["goal"]["by"] == "rules"
    mira = ent(conn, story, "Mira")
    want = goals.live(conn, mira, path(conn, story))[0]
    assert want["deflections"] == 1 and want["status"] == "active"
    assert want["message_id"] == path(conn, story)[4]["id"]  # anchored on the line that dodged it


@pytest.mark.anyio
async def test_dodged_twice_it_goes_dormant_then_resurfaces_after_a_rest(
    local_model, cards, backend
):
    conn = local_model
    story = make(conn, cards, {"want": BOAT})
    mira = ent(conn, story, "Mira")
    for text, reply in [
        ("Morning.", "Come see my boat!"),
        ("Did Tobin pay?", "Yes."),  # dodge one
        ("Ok.", "Mm."),
        ("Ok.", "Mm."),
        ("Hi.", "The boat, though!"),  # offered again
        ("How's the office?", "Busy."),  # dodge two: dormant
        ("Ok.", "Mm."),
        ("Ok.", "Mm."),
        ("Hm.", "Mm."),  # an opening, the rate allows it, but it is resting
    ]:
        got = await talk(conn, backend, story, text, reply)
    assert "agenda" not in got
    want = goals.live(conn, mira, path(conn, story))[0]
    assert (want["status"], want["deflections"]) == ("dormant", 2)
    backend.say("{}", "{}")  # a day passes: the memory reader reads the lines before it first
    got = await talk(conn, backend, story, "Hey, Mira.", "Aren!", skip="the next day")
    assert got["onmind"]["reentry"] and "agenda" not in got  # the time away comes first
    got = await talk(conn, backend, story, "What's new?", "Still that boat.")
    assert got["agenda"]["resurfaced"] is True and got["agenda"]["why"] == "asked"
    assert "Something still on your mind" in directive_of(backend)
    got = await talk(conn, backend, story, "Oh, the boat? Show me.", "Tomorrow!")
    assert got["goal"]["outcome"] == "progressed"
    want = goals.live(conn, mira, path(conn, story))[0]
    assert (want["status"], want["deflections"], want["progress"]) == ("active", 0, 0.25)


@pytest.mark.anyio
async def test_not_when_the_line_hurts_or_a_heavier_decision_is_there(local_model, cards, backend):
    conn = local_model
    story = make(conn, cards, {"want": BOAT})
    got = await talk(conn, backend, story, "You're useless.", "Fine.")
    assert "agenda" not in got  # an emotional line is not the moment
    secret = {"text": "Mira sank the old boat.", "keys": ["sank"], "topic": ["boat"],
              "cover": "It rotted."}  # fmt: skip
    story = make(conn, cards, {"want": BOAT, "secrets": [secret]})
    got = await talk(conn, backend, story, "What happened to the old boat?", "It rotted.")
    assert got.get("honest") and "agenda" not in got  # the secret decides this reply


@pytest.mark.anyio
async def test_the_side_call_reads_the_answer_in_place_of_the_rules(
    local_model, cards, backend, side_call
):
    conn = local_model
    story = make(conn, cards, {"want": BOAT})
    mira = ent(conn, story, "Mira")
    label = {"felt": {"label": "calm", "intensity": 1, "about": None, "cause": ""}, "events": [],
             "position": None, "yielded": False, "face": "neutral"}  # fmt: skip
    backend.say("Morning! Come see her.", json.dumps(label | {"agenda": "tried"}))
    mira_events = await play(turns.turn(conn, backend.llm, story, "Morning.", speaker=mira))
    assert mira_events[-1][0] == "done"
    assert gen_of(conn, story)["agenda"]["tried"] is True  # no cue word, but the model says so
    assert '"not_tried"' in json.dumps(backend.requests[-1]["response_format"])
    backend.say("Fine.", json.dumps(label | {"agenda": "deflected"}))
    line_ = "Boats are lovely, sure. How's Tobin?"  # names the cue, and still dodges it
    await play(turns.turn(conn, backend.llm, story, line_, speaker=mira))
    got = gen_of(conn, story)
    assert got["goal"]["outcome"] == "deflected" and got["goal"]["by"] == "side"
    want = goals.live(conn, mira, path(conn, story))[0]
    assert want["deflections"] == 1  # replaced, not added to the rules' reading
    assert conn.execute("SELECT COUNT(*) FROM goals WHERE key='want'").fetchone()[0] == 2


@pytest.mark.anyio
async def test_lite_makes_no_extra_call_and_off_does_nothing(
    local_model, cards, backend, side_call
):
    conn = local_model
    setting(conn, "mind.level", "lite")
    story = make(conn, cards, {"want": BOAT})
    got = await talk(conn, backend, story, "Morning.", "The boat is done!")
    assert got["agenda"]["tried"] is True and len(backend.requests) == 1
    setting(conn, "features.mind.goals", False)
    story = make(conn, cards, {"want": BOAT})
    got = await talk(conn, backend, story, "Morning.", "Hi.")
    assert "agenda" not in got and "Something you want" not in directive_of(backend)


@pytest.mark.anyio
async def test_a_failure_never_breaks_the_turn(local_model, cards, backend, monkeypatch):
    conn = local_model
    story = make(conn, cards, {"want": BOAT})

    def broken(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(goals, "pick", broken)
    monkeypatch.setattr(goals, "judge", broken)
    got = await talk(conn, backend, story, "Morning.", "Hi.")
    assert "agenda" not in got


@pytest.mark.anyio
async def test_when_it_fires_the_seed_on_her_mind_waits(local_model, cards, backend):
    conn = local_model
    story = make(conn, cards, {"want": BOAT})
    line(conn, story, "Aren", "Morning.")
    line(conn, story, "Mira", "Morning.")
    mira = ent(conn, story, "Mira")
    with conn:
        conn.execute(
            "INSERT INTO seeds(story_id, entity_id, kind, text, weight, story_time)"
            " VALUES(?, ?, 'plan', 'fix the old lantern', 0.9, ?)",
            (story, mira, path(conn, story)[-1]["story_time"]),
        )
    got = await talk(conn, backend, story, "Nice day.", "The boat!")
    tail = backend.requests[-1]["messages"][-1]["content"]
    assert got["agenda"] and "onmind" not in got and "lantern" not in tail
    got = await talk(conn, backend, story, "Did Tobin pay?", "He did.")
    assert got["onmind"]["text"] == "fix the old lantern"  # its turn comes after


# --- needs and energy ----------------------------------------------------------------------------


def tail(backend, i=-1) -> str:
    return backend.requests[i]["messages"][-1]["content"]


@pytest.mark.anyio
async def test_late_at_night_she_is_tired_and_denies_it_but_not_every_reply(
    local_model, cards, backend
):
    conn = local_model
    story = make(conn, cards)
    with conn:
        conn.execute("UPDATE stories SET epoch_offset_min=? WHERE id=?", (2 * 60, story))  # 2 am
    got = [await talk(conn, backend, story, "You still up?", "Mm.") for _ in range(5)]
    assert [bool(g.get("need")) for g in got] == [True, False, False, False, True]
    assert got[0]["need"]["need"] == "energy"
    assert "if anyone says you seem tired, deny it" in tail(backend, 0)
    assert "deny it" not in tail(backend, 1)
    mira = ent(conn, story, "Mira")
    state = json.loads(
        conn.execute(
            "SELECT state FROM mind_states WHERE entity_id=? ORDER BY id DESC", (mira,)
        ).fetchone()[0]
    )
    assert set(state["needs"]) == {"autonomy", "competence", "relatedness", "stimulation"}


@pytest.mark.anyio
async def test_bossed_about_she_bristles_and_off_there_are_no_needs(local_model, cards, backend):
    conn = local_model
    story = make(conn, cards)
    orders = "You will do as I say, Mira. Obey me."
    got = await talk(conn, backend, story, orders, "Hm.")
    assert "need" not in got  # once is not yet a pattern
    got = await talk(conn, backend, story, orders, "No.")
    assert got["need"]["need"] == "autonomy" and "pushed around" in tail(backend)
    setting(conn, "features.mind.goals", False)
    with conn:
        conn.execute("UPDATE stories SET epoch_offset_min=? WHERE id=?", (2 * 60, story))
    got = await talk(conn, backend, story, "Still up?", "Mm.")
    assert "need" not in got and "deny it" not in tail(backend)


# --- between scenes ------------------------------------------------------------------------------

from kataki import between, db  # noqa: E402

DIARY = {"diary": "I worked on the boat all week.", "worth_telling": [], "seeds": [],
         "preoccupation": "the launch"}  # fmt: skip


@pytest.mark.anyio
async def test_time_away_can_move_one_goal_and_undoing_the_skip_undoes_it(
    local_model, cards, backend
):
    conn = local_model
    story = make(conn, cards, {"want": BOAT, "need": "to let someone help her"})
    mira = ent(conn, story, "Mira")
    line(conn, story, "Aren", "See you, Mira.")
    line(conn, story, "Mira", "Bye.")
    turns.say(conn, story, skip="three days later")
    run = between.at_skip(conn, story, path(conn, story))
    want = goals.live(conn, mira, path(conn, story))[0]
    backend.say(json.dumps(DIARY | {"goal": {"goal": f"G{want['id']}", "change": "progressed",
                                             "tactic": "invite him to the launch"}}))  # fmt: skip
    assert await between.think(conn, backend.llm, story, run, mira)
    fmt = json.dumps(backend.requests[-1]["response_format"])
    assert (
        f'"G{want["id"]}"' in fmt and "to let someone help her" not in fmt
    )  # the need is not moved
    asked = "\n".join(m["content"] for m in backend.requests[-1]["messages"])
    assert BOAT["text"] in asked
    moved = goals.live(conn, mira, path(conn, story))[0]
    assert (moved["progress"], moved["tactic"], moved["run_id"]) == (
        0.25,
        "invite him to the launch",
        run,
    )
    db.discard_run(conn, run)
    assert goals.live(conn, mira, path(conn, story))[0]["progress"] == 0


def test_the_diary_call_drops_a_goal_it_was_not_given():
    got = between.read(DIARY | {"goal": {"goal": "G99", "change": "done", "tactic": "x"}}, ["G1"])
    assert got["goal"] is None
    got = between.read(DIARY | {"goal": {"goal": "G1", "change": "won", "tactic": "x"}}, ["G1"])
    assert got["goal"] is None
    got = between.read(DIARY | {"goal": {"goal": "G1", "change": "done", "tactic": "a " * 30}},
                       ["G1"])  # fmt: skip
    assert got["goal"]["change"] == "done" and len(got["goal"]["tactic"].split()) == 12
    assert "goal" not in between.read(DIARY)  # no goals: unchanged
    assert "goal" in between.schema(["G1"])["properties"]


# --- Peek and the Mind graph ---------------------------------------------------------------------

from kataki import mind, people  # noqa: E402


def peek(conn, story: int, name: str = "Mira") -> dict:
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    return next(p for p in people.people(conn, row) if p["name"] == name)


@pytest.mark.anyio
async def test_peek_shows_what_she_wants_and_needs_and_the_graph_the_goal_a_reply_pursued(
    local_model, cards, backend
):
    conn = local_model
    story = make(conn, cards, {"want": BOAT, "fear": "being left behind"})
    with conn:
        conn.execute("UPDATE stories SET epoch_offset_min=? WHERE id=?", (2 * 60, story))
    await talk(conn, backend, story, "Morning.", "The boat is finished!")
    await talk(conn, backend, story, "Did Tobin pay?", "Yes.")
    me = peek(conn, story)
    want, fear = me["goals"]
    assert (want["kind"], want["status"], want["dodged"], want["progress"]) == (
        "want",
        "active",
        1,
        0,
    )
    first = path(conn, story)[1]["id"]
    assert want["raised"] == {"message_id": first, "why": "lull", "tried": True}
    assert (fear["kind"], fear["status"], fear["raised"]) == ("fear", "dormant", None)
    assert me["needs"]["energy"] < 0.3 and me["needs"]["pressing"] == "energy"
    assert "deny it" in me["needs"]["shows"] and "competence" in me["needs"]
    graph = mind.mind(conn, first)
    goal = next(n for n in graph["nodes"] if n["id"] == "goal")
    assert goal["text"] == f"Wants: {BOAT['text']}" and goal["column"] == "decide"
    assert {"from": "goal", "to": "spoke", "gold": True} in graph["links"]
    body = next(n for n in graph["nodes"] if n["id"] == "need")
    assert body["title"] == "Body" and "deny it" in body["text"]
    setting(conn, "features.mind.goals", False)
    me = peek(conn, story)
    assert me["goals"] == [] and me["needs"] is None


@pytest.mark.anyio
async def test_once_it_is_dropped_she_is_told_to_leave_it_be_for_a_few_replies(
    local_model, cards, backend
):
    conn = local_model
    story = make(conn, cards, {"want": BOAT})
    for text, reply in [("Morning.", "Come see my boat!"), ("Did Tobin pay?", "Yes."),
                        ("Ok.", "Mm."), ("Ok.", "Mm."), ("Hi.", "The boat, though!")]:  # fmt: skip
        await talk(conn, backend, story, text, reply)
    assert "leave it be" not in directive_of(backend)
    got = [await talk(conn, backend, story, "How's the office?", "Busy.")]  # dodged twice
    got += [await talk(conn, backend, story, "Ok.", "Mm.") for _ in range(4)]
    told = ["leave it be" in directive_of(backend, i) for i in range(-5, 0)]
    assert told == [True, True, True, True, False]  # the reply to the dodge, and three more
    assert "unless Aren brings it up" in directive_of(backend, -5)
    assert not any(ch.isdigit() for ch in directive_of(backend, -5).split("First, before")[0])


# --- review fixes --------------------------------------------------------------------------------

LABEL = {"felt": {"label": "hurt", "intensity": 2, "about": None, "cause": "he insulted her"},
         "position": None, "yielded": False, "face": "neutral"}  # fmt: skip


@pytest.mark.anyio
async def test_on_standard_the_side_call_keeps_what_the_line_did_to_her_needs(
    local_model, cards, backend, side_call
):
    conn = local_model
    story = make(conn, cards)
    mira, aren = ent(conn, story, "Mira"), ent(conn, story, "Aren")
    label = LABEL | {"events": [{"target": f"E{aren}", "type": "insult", "intensity": 2}]}
    backend.say("Fine.", json.dumps(label))
    await play(turns.turn(conn, backend.llm, story, "You're useless, Mira.", speaker=mira))
    assert gen_of(conn, story)["after"] != "skipped"
    state = json.loads(
        conn.execute(
            "SELECT state FROM mind_states WHERE entity_id=? ORDER BY id DESC", (mira,)
        ).fetchone()[0]
    )
    assert state["needs"]["competence"] < inner.START["competence"]


def test_short_questions_are_not_boring_but_a_run_of_grunts_is():
    prof = inner.shape({})
    state = inner.drive(inner.fresh(prof, 0), prof)
    for _ in range(10):
        state = inner.drive(state, prof, None, "Where did you put the rope?")
    assert inner.need_row(state, prof, 15 * 60, []) is None
    for _ in range(15):
        state = inner.drive(state, prof, None, "Mm.")
    assert inner.need_row(state, prof, 15 * 60, [])["need"] == "stimulation"


@pytest.mark.anyio
async def test_on_lite_a_yes_is_a_yes(local_model, cards, backend):
    conn = local_model
    setting(conn, "mind.level", "lite")
    story = make(conn, cards, {"want": BOAT})
    await talk(conn, backend, story, "Morning.", "Come see my boat!")
    got = await talk(conn, backend, story, "Yes, I'd love to see it!", "Tomorrow, then.")
    assert got["goal"]["outcome"] == "progressed"


@pytest.mark.anyio
async def test_on_lite_yes_but_not_now_is_a_dodge(local_model, cards, backend):
    conn = local_model
    setting(conn, "mind.level", "lite")
    story = make(conn, cards, {"want": BOAT})
    await talk(conn, backend, story, "Morning.", "Come see my boat!")
    got = await talk(conn, backend, story, "Yes, but not now. Maybe later.", "Oh. Fine.")
    assert got["goal"]["outcome"] == "deflected"


@pytest.mark.anyio
async def test_when_the_side_call_says_she_never_raised_it_nothing_is_judged(
    local_model, cards, backend, side_call
):
    conn = local_model
    story = make(conn, cards, {"want": BOAT})
    mira = ent(conn, story, "Mira")
    label = LABEL | {"felt": {**LABEL["felt"], "label": "calm", "intensity": 1}, "events": []}
    backend.say("The boat, the boat.", json.dumps(label | {"agenda": "not_tried"}))
    await play(turns.turn(conn, backend.llm, story, "Morning.", speaker=mira))
    assert gen_of(conn, story)["agenda"]["tried"] is False
    backend.say("Yes.", json.dumps(label))
    await play(turns.turn(conn, backend.llm, story, "Did Tobin pay?", speaker=mira))
    assert "goal" not in gen_of(conn, story)
    assert goals.live(conn, mira, path(conn, story))[0]["deflections"] == 0


@pytest.mark.anyio
async def test_a_clock_edit_keeps_her_goals_where_they_were(local_model, cards, backend):
    conn = local_model
    story = make(conn, cards, {"want": BOAT})
    mira = ent(conn, story, "Mira")
    await talk(conn, backend, story, "Did the rope come in yet?", "No.", skip="the next day")
    first = path(conn, story)[0]["id"]
    for text, reply in [("Hi.", "Come see my boat!"), ("Did Tobin pay?", "Yes."),
                        ("Ok.", "Mm."), ("Ok.", "Mm."), ("Hm.", "The boat!"),
                        ("How's the office?", "Busy.")]:  # fmt: skip
        await talk(conn, backend, story, text, reply)
    assert goals.live(conn, mira, path(conn, story))[0]["status"] == "dormant"
    chat.set_skip(conn, first, 0)  # the day never passed: everything after moves back
    assert goals.live(conn, mira, path(conn, story))[0]["status"] == "dormant"
