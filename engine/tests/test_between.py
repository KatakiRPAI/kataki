"""Slice 5: a life between scenes. Time away is felt by attachment style, the card's own life is
rolled into offstage beats, each character writes a diary, and one thing reaches the reply."""

import json
import random
import re

import pytest

from kataki import between, clock, inner

DAY, HOUR = clock.DAY, clock.HOUR


def prof(**mind) -> dict:
    return inner.shape(mind)


# --- the rules (pure) --------------------------------------------------------------------------


def test_beats_grow_with_the_skip_and_stop_at_a_cap():
    assert [between.beats(m) for m in (HOUR, 2 * HOUR, 20 * HOUR, 2 * DAY, 5 * DAY)] == [
        0,
        1,
        1,
        2,
        3,
    ]
    assert between.beats(3 * 7 * DAY) == 3 and between.beats(60 * DAY) == 6


def test_absence_worries_the_anxious_and_not_the_secure():
    anxious = between.absence(prof(attachment={"anxiety": 0.8, "avoidance": 0.2}), 2 * DAY)
    secure = between.absence(prof(attachment={"anxiety": 0.2, "avoidance": 0.2}), 2 * DAY)
    assert anxious["style"] == "anxious" and anxious["worry"] > 0.4
    assert dict(anxious["cool"])["trust"] < 0
    assert secure["style"] == "secure" and secure["worry"] is None and secure["cool"] == []
    assert secure["glad"]
    # an unanswered question worries more; a short gap not at all
    thread = between.absence(prof(attachment={"anxiety": 0.8}), 2 * DAY, open_thread=True)
    assert thread["worry"] > anxious["worry"]
    assert between.absence(prof(attachment={"anxiety": 0.8}), 3 * HOUR)["worry"] is None


def test_the_avoidant_cool_and_the_fearful_do_both():
    avoidant = between.absence(prof(attachment={"anxiety": 0.2, "avoidance": 0.8}), 3 * DAY)
    assert avoidant["style"] == "avoidant" and avoidant["worry"] is None
    assert dict(avoidant["cool"])["closeness"] < 0 and not avoidant["glad"]
    fearful = between.absence(prof(attachment={"anxiety": 0.8, "avoidance": 0.8}), 3 * DAY)
    assert fearful["style"] == "fearful" and fearful["worry"] and dict(fearful["cool"])["trust"]


def test_worries_habituate_over_days():
    seed = {"kind": "worry", "weight": 0.8, "story_time": 0, "half_life_min": 2 * DAY}
    assert between.weight(seed, 2 * DAY) == pytest.approx(0.4)
    assert between.weight({**seed, "half_life_min": None}, DAY) < 0.8


def test_gossip_is_likelier_between_close_gossips_and_rare_for_secrets():
    open_ = between.gossip_p(0.8, 0.8, 0.9, 8, covert=False)
    assert open_ > 0.5
    assert between.gossip_p(0.8, 0.8, 0.9, 8, covert=True) == pytest.approx(open_ * 0.2)
    assert between.gossip_p(0.3, 0.3, 0.1, 3, covert=False) < 0.05
    assert between.level(0) == 0.5 and between.level(-200) == 0.1 and between.level(90) == 1


EVENTS = [{"text": "auditioned for the spring play", "good": "got a callback",
           "bad": "froze on the second monologue"}]  # fmt: skip


def test_a_roll_is_the_same_for_the_same_seed_and_skips_what_was_lived():
    rolls = [between.roll(random.Random("s:1:2:0"), prof(), EVENTS, set()) for _ in range(2)]
    assert rolls[0] == rolls[1]
    only_bad = [{"text": "auditioned", "bad": "froze"}]
    got = [between.roll(random.Random(f"k{i}"), prof(), only_bad, set()) for i in range(20)]
    assert all(g is None or (g["good"] is False and g["outcome"] == "froze") for g in got)
    assert any(got)
    assert between.roll(random.Random("x"), prof(), only_bad, {"auditioned"}) is None
    assert between.roll(random.Random("x"), prof(), [{"text": "x"}, "junk", {}], set()) is None


def test_the_templated_diary_is_first_person_and_has_no_digits():
    beat = {"text": "auditioned for the spring play", "outcome": "froze", "good": False}
    said = between.diary(330 * DAY, [beat], ["rehearsed lines"], "why Aren never answered")
    assert (
        said.startswith("Many months went by.")
        and "I auditioned for the spring play, and froze" in said
    )
    assert "I kept thinking about why Aren never answered." in said
    assert not re.search(r"\d", said)
    assert between.diary(2 * DAY, [], [], None) == "Two days went by. Nothing much happened."


def test_the_diary_calls_output_is_validated():
    got = between.read(
        {
            "diary": "I missed the harbour. " * 60,
            "worth_telling": ["I got a callback", " ", 3, "a", "b"],
            "seeds": [
                {"kind": "worry", "text": "whether the callback comes", "weight": 2},
                {"kind": "grudge", "text": "x", "weight": 2},
                {"kind": "plan", "text": "", "weight": 1},
                {"kind": "idea", "text": "a song", "weight": 7},
            ],
            "preoccupation": "the callback " * 20,
        }
    )
    assert len(got["diary"].split()) <= between.WORDS["diary"]
    assert got["worth_telling"] == ["I got a callback", "a"]
    assert got["seeds"] == [{"kind": "worry", "text": "whether the callback comes", "weight": 2}]
    assert len(got["preoccupation"].split()) == between.WORDS["preoccupation"]
    with pytest.raises(ValueError):
        between.read({"diary": " ", "worth_telling": [], "seeds": [], "preoccupation": ""})
    assert between.read({"diary": "Quiet days."})["seeds"] == []
    assert set(between.schema()["properties"]) == {
        "diary",
        "worth_telling",
        "seeds",
        "preoccupation",
    }


# --- the tick at the skip (B0) -----------------------------------------------------------------

from kataki import bonds, chat, db, extract, library, retrieve, turns  # noqa: E402

AUDITION = {"text": "auditioned for the spring play", "bad": "froze on the second monologue"}


@pytest.fixture
def cards(conn):
    return {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}


def make(conn, cards, mira: dict | None = None, tobin: dict | None = None) -> int:
    library.update_item(conn, cards["Mira"], data={"mind": mira or {}})
    library.update_item(conn, cards["Tobin"], data={"mind": tobin or {}})
    return library.create_story(
        conn, "Low Tide", character_ids=[cards["Mira"], cards["Tobin"]], persona_id=cards["Aren"]
    )


def ent(conn, story: int, name: str) -> int:
    return conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name=?", (story, name)
    ).fetchone()[0]


def line(conn, story: int, who: str, text: str, skip: int = 0) -> int:
    role = "user" if who == "Aren" else "assistant"
    return chat.append_message(conn, story, role, text, ent(conn, story, who), skip)


def seeds(conn, entity: int) -> list:
    return conn.execute("SELECT * FROM seeds WHERE entity_id=? ORDER BY id", (entity,)).fetchall()


def setting(conn, key: str, value) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)", (key, json.dumps(value))
    )
    conn.commit()


ANXIOUS = {"attachment": {"anxiety": 0.8, "avoidance": 0.2}}


def scene(conn, cards, **kw) -> tuple[int, int]:
    """Aren talks to Mira, she asks him something, and two days pass (the pass-time control)."""
    story = make(conn, cards, **kw)
    line(conn, story, "Aren", "I have to go, Mira.")
    line(conn, story, "Mira", "Will you come to the harbour tomorrow?")
    skip = turns.say(conn, story, skip="two days later")
    return story, skip


def test_a_two_day_skip_worries_the_anxious_one_only(conn, cards):
    story, skip = scene(conn, cards, mira=ANXIOUS)
    run = between.at_skip(conn, story, chat.active_path(conn, story))
    assert run is not None
    mira, tobin, aren = (ent(conn, story, n) for n in ("Mira", "Tobin", "Aren"))
    [worry] = [s for s in seeds(conn, mira) if s["kind"] == "worry"]
    assert worry["text"] == "why Aren never answered" and worry["about_id"] == aren
    assert (worry["message_id"], worry["run_id"]) == (skip, run)
    assert not [s for s in seeds(conn, tobin) if s["kind"] == "worry"]
    path = chat.active_path(conn, story)
    state = inner.current(conn, mira, path, inner.profile(conn, mira))
    top = state["emotions"][0]
    assert top["label"] == "anxious" and "two days" in top["cause"]
    rows = [r for r in bonds.ledger(conn, mira, path) if r["event"] == "neglect_gap"]
    assert rows and all(r["value"] < 0 for r in rows) and any(r["dim"] == "trust" for r in rows)
    assert not [r for r in bonds.ledger(conn, tobin, path) if r["event"] == "neglect_gap"]
    count = len(seeds(conn, mira))
    assert between.at_skip(conn, story, path) is None  # once per skip
    assert len(seeds(conn, mira)) == count


def test_gentle_relationships_write_no_ledger_rows(conn, cards):
    setting(conn, "realism.relationships", "gentle")
    story, _ = scene(conn, cards, mira=ANXIOUS)
    between.at_skip(conn, story, chat.active_path(conn, story))
    assert conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0] == 0
    assert [s["kind"] for s in seeds(conn, ent(conn, story, "Mira"))] == ["worry"]


def test_a_card_event_becomes_her_covert_memory_and_news(conn, cards, monkeypatch):
    monkeypatch.setattr(between, "P_EVENT", 1.0)
    story, skip = scene(conn, cards, mira={"events": [AUDITION], "routine": ["rehearsed lines"]})
    between.at_skip(conn, story, chat.active_path(conn, story))
    mira, tobin = ent(conn, story, "Mira"), ent(conn, story, "Tobin")
    [news] = [s for s in seeds(conn, mira) if s["kind"] == "news"]
    assert news["text"] == "auditioned for the spring play, and froze on the second monologue"
    event = conn.execute("SELECT * FROM memories WHERE id=?", (news["memory_id"],)).fetchone()
    assert event["covert"] == 1 and "offscreen" in event["tags_text"]
    assert event["to_message_id"] is None  # not in the transcript: recall must not skip it
    known = {m["memory_id"] for m in retrieve.inspect(conn, story, mira)}
    assert event["id"] in known
    assert event["id"] not in {m["memory_id"] for m in retrieve.inspect(conn, story, tobin)}
    diary = conn.execute(
        "SELECT * FROM memories WHERE tags_text LIKE '%diary%' AND id IN"
        " (SELECT memory_id FROM memory_entities WHERE entity_id=?)",
        (mira,),
    ).fetchone()
    assert "I auditioned for the spring play, and froze" in diary["detail"]
    state = inner.current(conn, mira, chat.active_path(conn, story), inner.profile(conn, mira))
    assert state["mood"]["v"] < inner.baseline(inner.profile(conn, mira))["v"]  # still low


def test_short_skips_and_switched_off_do_nothing(conn, cards):
    story = make(conn, cards, mira=ANXIOUS)
    line(conn, story, "Aren", "Back in an hour.")
    turns.say(conn, story, skip="an hour later")
    assert between.at_skip(conn, story, chat.active_path(conn, story)) is None
    story, _ = scene(conn, cards, mira=ANXIOUS)
    setting(conn, "realism.offscreen", "off")
    assert between.at_skip(conn, story, chat.active_path(conn, story)) is None
    setting(conn, "realism.offscreen", "on")
    setting(conn, "features.mind.offscreen", False)
    assert between.at_skip(conn, story, chat.active_path(conn, story)) is None
    assert conn.execute("SELECT COUNT(*) FROM seeds").fetchone()[0] == 0


def test_a_character_can_opt_out(conn, cards):
    library.update_item(
        conn, cards["Mira"], data={"mind": ANXIOUS, "realism": {"offscreen": "off"}}
    )
    story = library.create_story(
        conn, "Low Tide", character_ids=[cards["Mira"], cards["Tobin"]], persona_id=cards["Aren"]
    )
    line(conn, story, "Mira", "Will you come?")
    turns.say(conn, story, skip="two days later")
    between.at_skip(conn, story, chat.active_path(conn, story))
    mira, tobin = ent(conn, story, "Mira"), ent(conn, story, "Tobin")
    assert seeds(conn, mira) == []
    raw = json.loads(
        conn.execute("SELECT raw FROM extraction_runs WHERE trigger='between'").fetchone()[0]
    )
    assert raw["tracked"] == [tobin]


def test_undoing_the_skip_or_another_branch_drops_it(conn, cards, monkeypatch):
    monkeypatch.setattr(between, "P_EVENT", 1.0)
    story, skip = scene(conn, cards, mira=ANXIOUS | {"events": [AUDITION]})
    run = between.at_skip(conn, story, chat.active_path(conn, story))
    mira = ent(conn, story, "Mira")
    other = chat.append_sibling(conn, skip, "— Later —")  # a take without the skip
    chat.set_leaf(conn, story, other)
    path = chat.active_path(conn, story)
    assert run not in db.live_runs(conn, story)
    assert not any("froze" in m["detail"] for m in retrieve.inspect(conn, story, mira))
    state = inner.current(conn, mira, path, inner.profile(conn, mira))
    assert state is None or not state["emotions"]
    chat.set_leaf(conn, story, skip)
    assert run in db.live_runs(conn, story)
    chat.set_skip(conn, skip, 0)  # the undo chip
    for table in ("seeds", "mind_states", "opinions", "memories"):
        left = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE run_id=?", (run,)).fetchone()[0]
        assert left == 0, table


def test_two_who_spent_the_skip_together_may_pass_a_fact_on(conn, cards, monkeypatch):
    monkeypatch.setattr(between, "gossip_p", lambda *a, **k: 1.0)
    story = make(conn, cards)
    mira, tobin = ent(conn, story, "Mira"), ent(conn, story, "Tobin")
    fact = conn.execute(
        "INSERT INTO memories(story_id, kind, story_time, detail, gist, importance)"
        " VALUES(?, 'event', 0, 'The harbour master took a bribe.', 'A bribe.', 7)",
        (story,),
    ).lastrowid
    conn.execute(
        "INSERT INTO knowledge(knower_id, memory_id, source, learned_story_time)"
        " VALUES(?, ?, 'witnessed', 0)",
        (tobin, fact),
    )
    conn.commit()
    line(conn, story, "Tobin", "Quiet night.")
    turns.say(conn, story, skip="the next morning")
    run = between.at_skip(conn, story, chat.active_path(conn, story))
    [told] = conn.execute(
        "SELECT * FROM knowledge WHERE knower_id=? AND memory_id=?", (mira, fact)
    ).fetchall()
    assert (told["source"], told["told_by_id"], told["belief"], told["run_id"]) == (
        "told",
        tobin,
        0.7,
        run,
    )
    # Tobin's own diary never travels
    assert not conn.execute(
        "SELECT 1 FROM knowledge k JOIN memories m ON m.id=k.memory_id"
        " WHERE k.knower_id=? AND m.tags_text LIKE '%diary%' AND m.id IN"
        " (SELECT memory_id FROM memory_entities WHERE entity_id=?)",
        (mira, tobin),
    ).fetchone()


def test_the_memory_reader_still_reads_the_lines_before_the_skip(conn, cards):
    story, _ = scene(conn, cards, mira=ANXIOUS)
    before = [m["id"] for m in extract.pending(conn, story)]
    between.at_skip(conn, story, chat.active_path(conn, story))
    assert [m["id"] for m in extract.pending(conn, story)] == before


def test_an_eased_worry_rebounds_once_at_the_next_skip(conn, cards):
    story, _ = scene(conn, cards, mira=ANXIOUS)
    between.at_skip(conn, story, chat.active_path(conn, story))
    mira = ent(conn, story, "Mira")
    [first] = [s for s in seeds(conn, mira) if s["kind"] == "worry"]
    line(conn, story, "Aren", "Sorry, I was away.")
    line(conn, story, "Mira", "Oh. That's alright.")  # contact: the worry is eased
    turns.say(conn, story, skip="seven hours later")
    between.at_skip(conn, story, chat.active_path(conn, story))
    worries = [s for s in seeds(conn, mira) if s["kind"] == "worry"]
    assert len(worries) == 2
    again = worries[-1]
    assert again["text"] == first["text"] and again["weight"] == pytest.approx(first["weight"] / 2)
    assert json.loads(again["payload"])["rebound_of"] == first["id"]
    turns.say(conn, story, skip="seven hours later")  # once only
    between.at_skip(conn, story, chat.active_path(conn, story))
    assert len([s for s in seeds(conn, mira) if s["kind"] == "worry"]) == 2


# --- the diary call (B1) -----------------------------------------------------------------------

DIARY = {
    "diary": "Two days of rain. I kept checking the door for Aren.",
    "worth_telling": ["I finally fixed the lantern", "auditioned and froze on the monologue"],
    "seeds": [
        {"kind": "plan", "text": "ask Aren to the harbour fair", "weight": 2},
        {"kind": "curse", "text": "x", "weight": 1},
    ],
    "preoccupation": "whether Aren still wants to see me",
}


def known_only_to(conn, story: int, who: int, detail: str) -> int:
    mid = conn.execute(
        "INSERT INTO memories(story_id, kind, story_time, detail, gist, importance, covert)"
        " VALUES(?, 'event', 0, ?, ?, 6, 1)",
        (story, detail, detail),
    ).lastrowid
    conn.execute(
        "INSERT INTO memory_entities(memory_id, entity_id, role) VALUES(?, ?, 'actor')", (mid, who)
    )
    conn.execute(
        "INSERT INTO knowledge(knower_id, memory_id, source, learned_story_time)"
        " VALUES(?, ?, 'witnessed', 0)",
        (who, mid),
    )
    conn.commit()
    return mid


def asked(backend) -> str:
    return "\n".join(m["content"] for m in backend.requests[-1]["messages"])


@pytest.mark.anyio
async def test_each_character_writes_her_own_diary_from_her_own_mind(
    local_model, cards, backend, monkeypatch
):
    conn = local_model
    monkeypatch.setattr(between, "P_EVENT", 1.0)
    story, skip = scene(conn, cards, mira=ANXIOUS | {"events": [AUDITION]})
    mira, tobin = ent(conn, story, "Mira"), ent(conn, story, "Tobin")
    known_only_to(conn, story, mira, "Mira keeps a blue lantern in the office.")
    known_only_to(conn, story, tobin, "Tobin buried the strongbox under the pier.")
    conn.execute(
        "INSERT INTO summaries(story_id, text) VALUES(?, 'Everyone knows about the strongbox.')",
        (story,),
    )
    conn.commit()
    run = between.at_skip(conn, story, chat.active_path(conn, story))
    assert between.todo(conn, story) == [(run, mira), (run, tobin)]
    backend.say(json.dumps(DIARY))
    assert await between.think(conn, backend.llm, story, run, mira)
    said = asked(backend)
    assert "blue lantern" in said and "froze on the second monologue" in said
    assert "why Aren never answered" in said and "Will you come to the harbour" in said
    assert "strongbox" not in said  # another's covert memory, and the all-seeing summary
    diaries = conn.execute(
        "SELECT detail FROM memories WHERE run_id=? AND tags_text LIKE '%diary%' AND id IN"
        " (SELECT memory_id FROM memory_entities WHERE entity_id=?)",
        (run, mira),
    ).fetchall()
    assert [d[0] for d in diaries] == [DIARY["diary"]]  # the template is gone
    kinds = [(s["kind"], s["text"]) for s in seeds(conn, mira)]
    assert ("news", "I finally fixed the lantern") in kinds
    assert ("news", "auditioned and froze on the monologue") not in kinds  # already known news
    assert ("plan", "ask Aren to the harbour fair") in kinds
    assert ("preoccupation", "whether Aren still wants to see me") in kinds
    assert all(s["run_id"] == run and s["message_id"] == skip for s in seeds(conn, mira))
    assert between.todo(conn, story) == [(run, tobin)]
    assert not await between.think(conn, backend.llm, story, run, mira)  # once


@pytest.mark.anyio
async def test_a_failed_diary_call_keeps_the_tick(local_model, cards, backend):
    conn = local_model
    story, _ = scene(conn, cards, mira=ANXIOUS)
    run = between.at_skip(conn, story, chat.active_path(conn, story))
    mira = ent(conn, story, "Mira")
    before = len(seeds(conn, mira))
    backend.say('{"diary": ""}', "not json")
    assert not await between.think(conn, backend.llm, story, run, mira)
    raw = json.loads(
        conn.execute("SELECT raw FROM extraction_runs WHERE id=?", (run,)).fetchone()[0]
    )
    assert raw["b1"][str(mira)] == "failed"
    assert len(seeds(conn, mira)) == before
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM memories WHERE run_id=? AND tags_text LIKE '%diary%'", (run,)
        ).fetchone()[0]
        == 1
    )  # the templated one stays


def test_lite_makes_no_call(conn, cards):
    setting(conn, "mind.level", "lite")
    story, _ = scene(conn, cards, mira=ANXIOUS)
    run = between.at_skip(conn, story, chat.active_path(conn, story))
    assert between.todo(conn, story) == []
    raw = json.loads(
        conn.execute("SELECT raw FROM extraction_runs WHERE id=?", (run,)).fetchone()[0]
    )
    assert set(raw["b1"].values()) == {"lite"}


@pytest.mark.anyio
async def test_the_worker_writes_the_diaries_after_the_pass_time_control(
    local_model, cards, backend
):
    conn = local_model
    story, _ = scene(conn, cards, mira=ANXIOUS)
    between.at_skip(conn, story, chat.active_path(conn, story))
    backend.say(json.dumps(DIARY), json.dumps(DIARY), "{}", "{}", "{}", "{}")
    worker = extract.Worker(conn, backend.llm, delay=0)
    worker.poke(story)
    await worker.idle()
    first = [m["content"] for m in backend.requests[0]["messages"]]
    assert "diary" in first[0]  # the diaries come before the memory reader
    assert between.todo(conn, story) == []


# --- one thing reaches the reply ---------------------------------------------------------------


async def play(stream):
    return [e async for e in stream]


def directive_of(backend, i=-1) -> str:
    return backend.requests[i]["messages"][-1]["content"].split("[Directive]")[1]


def tail_of(backend, i=-1) -> str:
    return backend.requests[i]["messages"][-1]["content"]


def gen_of(conn, story) -> dict:
    return json.loads(chat.active_path(conn, story)[-1]["gen"])


def plan(conn, story: int, who: int, text: str = "fix the old lantern") -> int:
    with conn:
        return conn.execute(
            "INSERT INTO seeds(story_id, entity_id, kind, text, weight, story_time)"
            " VALUES(?, ?, 'plan', ?, 0.9, ?)",
            (story, who, text, chat.active_path(conn, story)[-1]["story_time"]),
        ).lastrowid


@pytest.mark.anyio
async def test_back_after_two_days_she_shows_relief_tells_her_news_and_asks_about_yours(
    local_model, cards, backend, monkeypatch
):
    conn = local_model
    monkeypatch.setattr(between, "P_EVENT", 1.0)
    story, _ = scene(conn, cards, mira=ANXIOUS | {"events": [AUDITION]})
    mira = ent(conn, story, "Mira")
    backend.say("{}", "Oh! You're here.", "It went badly, honestly.")  # {}: the memory reader
    await play(turns.turn(conn, backend.llm, story, "Mira, I'm back.", speaker=mira))
    said = directive_of(backend)
    assert "let the relief show and look for a little reassurance" in said
    assert "no guilt" in said and "two days" in said
    assert "froze on the second monologue" in said and "Ask what Aren has been up to" in said
    assert not re.search(r"\d", said.split("Reply")[0])
    got = gen_of(conn, story)["onmind"]
    assert got["reentry"] and got["kind"] == "worry" and got["news"]
    await play(turns.turn(conn, backend.llm, story, "What's new?", speaker=mira))
    later = directive_of(backend)
    assert "relief" not in later and "froze on the second monologue" not in later  # once
    assert "onmind" not in gen_of(conn, story)  # nothing else on her mind


@pytest.mark.anyio
async def test_a_seed_rides_in_the_mind_block_on_two_replies(local_model, cards, backend):
    conn = local_model
    story, _ = scene(conn, cards)  # a secure Mira: no worry, and nothing to tell
    mira = ent(conn, story, "Mira")
    seed = plan(conn, story, mira)
    backend.say("{}", "Hello again.", "Mm.", "Sure.", "Right.")
    await play(turns.turn(conn, backend.llm, story, "Mira, I'm back.", speaker=mira))
    assert "Ask what Aren has been up to" in directive_of(backend)  # glad to see him
    for _ in range(3):
        await play(turns.turn(conn, backend.llm, story, "Nice weather.", speaker=mira))
    tails = [tail_of(backend, i) for i in range(1, 5)]
    block = "On your mind: fix the old lantern. Bring it up only if there is a natural opening"
    assert [block in t for t in tails] == [False, True, True, False]  # one thing at a time
    path = chat.active_path(conn, story)
    first, second = (json.loads(path[i]["gen"])["onmind"] for i in (-7, -5))
    assert first == {"seed": None, "kind": None, "text": None, "news": None, "reentry": True}
    assert second == {"seed": seed, "kind": "plan", "text": "fix the old lantern", "news": None,
                      "reentry": False}  # fmt: skip


@pytest.mark.anyio
async def test_off_reaches_nothing_and_a_failure_never_breaks_the_turn(
    local_model, cards, backend, monkeypatch
):
    conn = local_model
    story, _ = scene(conn, cards, mira=ANXIOUS)
    mira = ent(conn, story, "Mira")
    plan(conn, story, mira)
    setting(conn, "features.mind.offscreen", False)
    backend.say("{}", "Hi.", "Hello.")
    await play(turns.turn(conn, backend.llm, story, "Mira?", speaker=mira))
    assert "lantern" not in tail_of(backend) and "onmind" not in gen_of(conn, story)
    setting(conn, "features.mind.offscreen", True)

    def broken(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(between, "on_mind", broken)
    events = await play(turns.turn(conn, backend.llm, story, "Mira?", speaker=mira))
    assert events[-1][0] == "done"
