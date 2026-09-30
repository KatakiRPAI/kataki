"""The side call (minds slice 2b): its schema, its parser, and the turn it runs in."""

import json

import pytest

from kataki import after, bonds, chat, images, inner, library, turns

HANDLES = ["E3", "E4"]


def labels(**over) -> dict:
    base = {"felt": {"label": "calm", "intensity": 1, "about": None, "cause": ""},
            "events": [], "position": None, "yielded": False, "face": "neutral"}  # fmt: skip
    return base | over


def test_the_schema_closes_every_list():
    s = after.schema(HANDLES)["properties"]
    assert s["felt"]["properties"]["label"]["enum"] == list(inner.FEEL)
    assert s["events"]["items"]["properties"]["target"]["enum"] == HANDLES
    assert "maxItems" not in s["events"]  # a strict host may reject it; read() caps at 3
    assert s["face"]["enum"] == list(images.EXPRESSIONS)


def test_good_labels_are_read_and_bad_events_dropped():
    got = after.read(
        labels(
            felt={"label": "hurt", "intensity": 3, "about": "E3", "cause": "he broke his promise"},
            events=[
                {"target": "E3", "type": "promise_broken", "intensity": 2},
                {"target": "E9", "type": "insult", "intensity": 2},  # nobody here
                {"target": "E4", "type": "hugged", "intensity": 1},  # not on the list
                {"target": "E4", "type": "insult", "intensity": True},  # not a level
                {"target": "E4", "type": ["insult"], "intensity": 1},  # not even a word
            ],
            position={"text": " won't go ", "firm": 3},
            yielded=True,
        ),
        HANDLES,
    )
    assert got["felt"] == {"label": "hurt", "intensity": 3, "about": "E3",
                           "cause": "he broke his promise"}  # fmt: skip
    assert got["events"] == [{"target": "E3", "type": "promise_broken", "intensity": 2}]
    assert got["position"] == {"text": "won't go", "firm": 3} and got["yielded"] is True


@pytest.mark.parametrize(
    "bad",
    [
        labels(felt={"label": "smug", "intensity": 1, "about": None, "cause": ""}),
        labels(felt={"label": ["hurt"], "intensity": 1, "about": None, "cause": ""}),
        labels(felt={"label": "hurt", "intensity": 5, "about": None, "cause": ""}),
        labels(face="smirk"),
        {"events": []},
    ],
)
def test_unusable_labels_are_refused(bad):
    with pytest.raises(ValueError):
        after.read(bad, HANDLES)


# --- in the turn ------------------------------------------------------------------------------


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    return library.create_story(
        conn, "Low Tide", character_ids=[ids["Mira"], ids["Tobin"]], persona_id=ids["Aren"]
    )


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


async def play(stream):
    return [e async for e in stream]


def tail(request):
    return request["messages"][-1]["content"]


def said(**over) -> str:
    return json.dumps(labels(**over))


def events_of(conn, name):
    rows = conn.execute("SELECT event FROM opinions WHERE src_id=?", (eid(conn, name),))
    return {r[0] for r in rows}


def test_lite_never_asks(conn, side_call):
    assert after.wanted(conn)
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    assert not after.wanted(conn)


@pytest.mark.anyio
async def test_the_side_call_is_the_face_call_now(conn, story, backend, side_call):
    lib = conn.execute("SELECT lib_item_id FROM entities WHERE name='Mira'").fetchone()[0]
    library.update_item(conn, lib, data={"pack": {"neutral": 1, "smiling": 2}})
    backend.say("*grins* Hi.", said(face="smiling"))
    events = await play(turns.turn(conn, backend.llm, story, "Hi, Mira."))
    assert events[-1][1]["expression"] == "smiling" and len(backend.requests) == 2
    asked = backend.requests[1]
    assert asked["response_format"]["json_schema"]["name"] == "after"
    assert "*grins* Hi." in asked["messages"][-1]["content"]
    assert f"E{eid(conn, 'Aren')} = Aren (the user)" in asked["messages"][-1]["content"]
    ms = json.loads(chat.active_path(conn, story)[-1]["gen"])["trace"]["ms"]
    assert "after" in ms and "face" not in ms  # the side call's time is not counted twice


@pytest.mark.anyio
async def test_without_sprites_it_still_reads_but_sets_no_face(conn, story, backend, side_call):
    backend.say("Hi.", said(face="smiling"))
    events = await play(turns.turn(conn, backend.llm, story, "Hi, Mira."))
    assert events[-1][1]["expression"] is None and len(backend.requests) == 2
    leaf = chat.active_path(conn, story)[-1]
    assert json.loads(leaf["gen"])["after"]["face"] == "smiling"


@pytest.mark.anyio
async def test_what_she_felt_and_who_did_what_come_from_the_side_call(
    conn, story, backend, side_call
):
    aren, mira = eid(conn, "Aren"), eid(conn, "Mira")
    backend.say(
        "Ha. Cute.",
        said(
            felt={"label": "amused", "intensity": 2, "about": f"E{aren}", "cause": "he teased her"},
            events=[{"target": f"E{aren}", "type": "teasing_ok", "intensity": 1}],
        ),
    )
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert events_of(conn, "Mira") == {"teasing_ok"}  # in place of the rules' insult
    cause = conn.execute("SELECT cause FROM opinions WHERE src_id=?", (mira,)).fetchone()[0]
    assert cause == "he teased her"
    path = chat.active_path(conn, story)
    state = inner.current(conn, mira, path, inner.profile(conn, mira))
    assert any(e["label"] == "amused" for e in state["emotions"])
    assert json.loads(path[-1]["gen"])["after"]["events"][0]["type"] == "teasing_ok"


@pytest.mark.anyio
async def test_a_bad_side_call_keeps_the_rules_reading(conn, story, backend, side_call):
    backend.say("Fine.", "not json", "still not json")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert events[-1][0] == "done" and events[-1][1]["expression"] is None
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["text"] == "Fine." and json.loads(leaf["gen"])["after"] == "skipped"
    assert events_of(conn, "Mira") == {"insult"}


@pytest.mark.anyio
async def test_a_broken_apply_keeps_the_reply_and_the_rules(
    conn, story, backend, side_call, monkeypatch
):
    def boom(*a, **k):
        raise RuntimeError("ledger down")

    monkeypatch.setattr(bonds, "replace", boom)
    kind = {"target": f"E{eid(conn, 'Aren')}", "type": "kindness", "intensity": 1}
    backend.say("Fine.", said(events=[kind]))
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    leaf = chat.active_path(conn, story)[-1]
    assert events[-1][0] == "done" and json.loads(leaf["gen"])["after"] == "skipped"
    assert events_of(conn, "Mira") == {"insult"}
    assert events[-1][1]["mood"] == json.loads(leaf["gen"])["mind"]  # nothing half-applied


@pytest.mark.anyio
async def test_the_side_call_is_metered_like_any_call(conn, story, backend, side_call):
    seen = []
    llm = backend.llm
    llm.on_usage = lambda ep, used: seen.append(ep.role)
    backend.say("Hi.", said())
    await play(turns.turn(conn, llm, story, "Hi, Mira."))
    assert seen == ["rp", "utility"]


@pytest.mark.anyio
async def test_lite_keeps_the_rules_events_and_the_lite_face(conn, story, backend, side_call):
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    lib = conn.execute("SELECT lib_item_id FROM entities WHERE name='Mira'").fetchone()[0]
    library.update_item(conn, lib, data={"pack": {"neutral": 1, "hurt": 2}})
    backend.say("Fine.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert len(backend.requests) == 1 and events[-1][1]["expression"] is not None
    assert events_of(conn, "Mira") == {"insult"}


@pytest.mark.anyio
async def test_a_position_she_took_binds_her_next_reply(conn, story, backend, side_call):
    backend.say(
        "I'm not going.",
        said(position={"text": "won't go to the party", "firm": 3}),
        "No.",
        said(),
    )
    await play(turns.turn(conn, backend.llm, story, "Mira, come to the party."))
    await play(turns.turn(conn, backend.llm, story, "Mira, please?"))
    directive = tail(backend.requests[2]).split("[Directive]")[1]
    assert 'You have taken a position: "won\'t go to the party".' in directive
    assert "Change your position only if Aren gives a new reason" in directive


def hurt(conn, story, name="Mira"):
    path = chat.active_path(conn, story)
    state = inner.current(conn, eid(conn, name), path, inner.profile(conn, eid(conn, name)))
    return next((e["i"] for e in state["emotions"] if e["label"] == "hurt"), 0)


@pytest.mark.anyio
async def test_a_side_call_echo_of_the_mood_changes_nothing(conn, story, backend, side_call):
    aren = f"E{eid(conn, 'Aren')}"
    insult = {"target": aren, "type": "insult", "intensity": 2}
    felt = {"label": "hurt", "intensity": 3, "about": aren, "cause": "called me useless"}
    backend.say("Hm.", said(felt=felt, events=[insult]))
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless at this job."))
    first, rows = hurt(conn, story), conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0]
    assert first > 0
    backend.say("The shipment? Not yet.", said(felt=felt, events=[insult]))
    await play(turns.turn(conn, backend.llm, story, "Mira, did the shipment come in?"))
    assert conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0] == rows
    assert hurt(conn, story) <= first  # it fades as if there were no side call


@pytest.mark.anyio
async def test_the_same_event_twice_in_one_reply_is_one_row(conn, story, backend, side_call):
    aren = f"E{eid(conn, 'Aren')}"
    tease = {"target": aren, "type": "teasing_ok", "intensity": 1}
    felt = {"label": "amused", "intensity": 2, "about": aren, "cause": "he teased her"}
    backend.say("Ha.", said(felt=felt, events=[tease, tease, tease]))
    await play(turns.turn(conn, backend.llm, story, "Mira, hello."))
    n = conn.execute("SELECT COUNT(*) FROM opinions WHERE event='teasing_ok'").fetchone()[0]
    assert n == 1


@pytest.mark.anyio
async def test_a_reply_to_a_reply_is_not_an_appraisal(conn, story, backend, side_call):
    aren = f"E{eid(conn, 'Aren')}"
    backend.say(
        "Hm.",
        said(),
        "Tobin nods.",
        said(),
        "Still here.",
        said(
            felt={"label": "hurt", "intensity": 3, "about": aren, "cause": "x"},
            events=[{"target": aren, "type": "insult", "intensity": 3}],
        ),
    )
    await play(turns.turn(conn, backend.llm, story, "Mira, hello."))
    async for _ in turns.turn(conn, backend.llm, story, None, speaker=eid(conn, "Tobin")):
        pass
    async for _ in turns.turn(conn, backend.llm, story, None, speaker=eid(conn, "Mira")):
        pass
    assert conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0] == 0


@pytest.mark.anyio
async def test_the_side_call_re_reads_the_line_instead_of_feeling_it_twice(
    conn, story, backend, side_call
):
    mira = eid(conn, "Mira")
    lib = conn.execute("SELECT lib_item_id FROM entities WHERE id=?", (mira,)).fetchone()[0]
    mind = {"regulation": {"style": "suppress", "capacity": 0.5}}
    library.update_item(conn, lib, data={"mind": mind})
    prof = inner.profile(conn, mira)
    aren = f"E{eid(conn, 'Aren')}"
    felt = {"label": "hurt", "intensity": 3, "about": aren, "cause": "called me useless"}
    backend.say("Hm.", said(felt=felt, events=[{"target": aren, "type": "insult", "intensity": 2}]))
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    path = chat.active_path(conn, story)
    rows = conn.execute("SELECT COUNT(*) FROM mind_states WHERE entity_id=? AND message_id=?",
                        (mira, path[-1]["id"])).fetchone()[0]  # fmt: skip
    st = inner.current(conn, mira, path, prof)
    once = inner.regulate(
        inner.feel(inner.fresh(prof, st["t"]), "hurt", after.FELT[3], "c", prof), prof
    )
    assert rows == 1
    assert st["emotions"][0]["i"] == once["emotions"][0]["i"] == after.FELT[3]
    assert st["reg_load"] == once["reg_load"] and st["mood"] == once["mood"]
    later = inner.tick(st, st["t"] + 120, prof)
    assert inner.mood_word(later, prof) == "low"


@pytest.mark.anyio
async def test_the_mood_a_reply_shows_is_the_one_the_side_call_saved(
    conn, story, backend, side_call
):
    """The rules read her as wound up (an insult from Aren); the side call reads the line as a
    sad one. `done.mood` and the saved `gen.mind` must show what was saved, not the rules' first read."""
    mira, aren = eid(conn, "Mira"), f"E{eid(conn, 'Aren')}"
    felt = {"label": "sad", "intensity": 1, "about": aren, "cause": "c"}
    backend.say("Hm.", said(felt=felt, events=[{"target": aren, "type": "insult", "intensity": 1}]))
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    path = chat.active_path(conn, story)
    prof = inner.profile(conn, mira)
    saved = inner.public(inner.current(conn, mira, path, prof), prof)
    assert saved["label"] == "sad"
    assert events[-1][1]["mood"] == saved == json.loads(path[-1]["gen"])["mind"]


@pytest.mark.anyio
async def test_the_side_call_judges_the_line_not_the_reply(conn, story, backend, side_call):
    backend.say("Wounded silence, quiet fury, Zorblax.", said())
    await play(
        turns.turn(
            conn, backend.llm, story, "Morning. Everything alright?", speaker=eid(conn, "Mira")
        )
    )
    ask = backend.requests[1]["messages"]
    body = ask[-1]["content"]
    judged, reply = body.split("[Mira's reply: for position, yielded and face only]")
    assert "Morning. Everything alright?" in judged and "Zorblax" not in judged
    assert "Zorblax" in reply
    assert "NOT evidence" in ask[0]["content"] and "small talk do nothing" in ask[0]["content"]


@pytest.mark.anyio
async def test_a_hollow_apology_label_does_not_wipe_a_broken_promise(
    conn, story, backend, side_call
):
    """Real response (Qwen3-235B, 2026-09-30): on "I forgot. I didn't come last night." the side
    call said apology_hollow. That must not replace the rules' promise_broken."""
    aren = eid(conn, "Aren")
    backend.say(
        "Hm.",
        said(events=[{"target": f"E{aren}", "type": "apology_hollow", "intensity": 2}]),
    )
    await play(turns.turn(conn, backend.llm, story, "Mira, I forgot. I didn't come last night."))
    assert events_of(conn, "Mira") == {"promise_broken", "apology_hollow"}


@pytest.mark.anyio
async def test_a_sincere_apology_label_does_replace_the_rules_grudge(
    conn, story, backend, side_call
):
    aren = eid(conn, "Aren")
    backend.say(
        "Hm.",
        said(events=[{"target": f"E{aren}", "type": "apology_sincere", "intensity": 2}]),
    )
    await play(turns.turn(conn, backend.llm, story, "Mira, I forgot. I didn't come last night."))
    assert events_of(conn, "Mira") == {"apology_sincere"}


@pytest.mark.anyio
async def test_a_relabel_to_another_grudge_charges_one_not_two(conn, story, backend, side_call):
    aren = eid(conn, "Aren")
    backend.say(
        "Hm.", said(events=[{"target": f"E{aren}", "type": "boundary_crossed", "intensity": 2}])
    )
    await play(turns.turn(conn, backend.llm, story, "Mira, I forgot. I didn't come last night."))
    assert events_of(conn, "Mira") == {"boundary_crossed"}


@pytest.mark.anyio
async def test_a_kindness_to_someone_else_does_not_wipe_the_grudge_toward_him(
    conn, story, backend, side_call
):
    tobin = eid(conn, "Tobin")
    backend.say("Hm.", said(events=[{"target": f"E{tobin}", "type": "kindness", "intensity": 1}]))
    await play(turns.turn(conn, backend.llm, story, "Mira, I forgot. I didn't come last night."))
    assert {"promise_broken", "kindness"} <= events_of(conn, "Mira")


# --- voice (minds slice 10) -------------------------------------------------------------------


def test_the_voice_field_is_asked_only_when_she_is_voiced():
    from kataki import speech

    assert "voice" not in after.schema(HANDLES)["properties"]
    s = after.schema(HANDLES, voice=True)
    assert s["properties"]["voice"]["properties"]["tone"]["enum"] == list(speech.TONES)
    assert s["properties"]["voice"]["properties"]["tag"]["enum"] == [*speech.TAGS, None]
    assert "voice" in s["required"]
    got = after.read(labels(voice={"tone": "hurt", "tag": "sigh"}), HANDLES, voice=True)
    assert got["voice"] == {"tone": "hurt", "tag": "sigh"}
    bad = after.read(labels(voice={"tone": "sultry", "tag": "scream"}), HANDLES, voice=True)
    assert bad["voice"] == {"tone": None, "tag": None}
    assert "voice" not in after.read(labels(voice={"tone": "hurt"}), HANDLES)
