"""The extraction pipeline: what to read, when, what the model is shown, and the worker."""

import asyncio
import json

import httpx2
import pytest

from kataki import chat, extract, library
from kataki.models import extraction_schema

pytestmark = pytest.mark.anyio


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    library.update_item(conn, ids["Mira"], data={"aliases": ["the courier"]})
    gull = library.create_item(conn, "place", "The Gull")
    library.create_item(conn, "place", "The Docks")
    return library.create_story(
        conn, "Low Tide", character_ids=[ids["Mira"], ids["Tobin"]], place_id=gull,
        persona_id=ids["Aren"],
    )  # fmt: skip


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


def talk(conn, story, n, text="line"):
    ids = []
    for i in range(n):
        who, role = ("Aren", "user") if i % 2 == 0 else ("Mira", "assistant")
        ids.append(chat.append_message(conn, story, role, f"{text} {i}", speaker_id=eid(conn, who)))
    return ids


def todo_ids(conn, story):
    return [m["id"] for m in extract.pending(conn, story)]


# --- what is waiting to be read ------------------------------------------------------------


def test_a_reply_waits_until_the_user_answers_it(conn, story):
    ids = talk(conn, story, 4)  # user, reply, user, reply
    assert todo_ids(conn, story) == ids[:3]
    chat.append_message(conn, story, "user", "and?", speaker_id=eid(conn, "Aren"))
    assert todo_ids(conn, story)[-2:] == [ids[3], ids[3] + 1]


def test_what_a_live_run_covered_is_not_read_again(conn, story):
    ids = talk(conn, story, 7)
    run = extract.open_run(conn, story, ids[0], ids[3], "cadence")
    extract.apply(conn, run, {})
    assert todo_ids(conn, story) == ids[4:]


# --- when a run is due ---------------------------------------------------------------------


def plan(conn, story, **kw):
    chunk, trigger = extract.plan(extract.pending(conn, story), **kw)
    return [m["id"] for m in chunk], trigger


def test_nothing_is_due_after_a_few_lines(conn, story):
    talk(conn, story, 5)
    assert plan(conn, story) == ([], None)


def test_after_ten_lines_a_run_is_due_and_reads_all_that_is_waiting(conn, story):
    assert plan(conn, story) == ([], None)
    ids = talk(conn, story, 11)
    assert plan(conn, story) == (ids, "cadence")


def test_a_run_reads_at_most_twelve_lines(conn, story):
    ids = talk(conn, story, 30)
    chunk, _ = plan(conn, story)
    assert chunk == ids[:12]


def test_a_time_skip_closes_the_stretch_before_it(conn, story):
    ids = talk(conn, story, 3)
    skip = chat.append_message(conn, story, "user", "Years later.", eid(conn, "Aren"), 999_999)
    chat.append_message(conn, story, "assistant", "...", eid(conn, "Mira"))
    assert plan(conn, story) == (ids, "skip")
    assert skip not in plan(conn, story)[0]


def test_lines_scrolling_out_of_view_are_read_before_they_go(conn, story):
    ids = talk(conn, story, 5)
    assert plan(conn, story, history_from=ids[2]) == (ids[:5], "evict")


def test_asking_for_it_reads_whatever_is_waiting(conn, story):
    ids = talk(conn, story, 3)
    assert plan(conn, story, manual=True) == (ids, "manual")


# --- what the model is shown ---------------------------------------------------------------


def test_the_roster_lists_who_is_here_and_who_is_named_with_handles(conn, story):
    chat.append_message(
        conn, story, "user", "Ever been to the docks?", speaker_id=eid(conn, "Aren")
    )
    entities, _ = extract.roster(conn, story, extract.pending(conn, story))
    lines = "\n".join(entities)
    assert f"E{eid(conn, 'Mira')} Mira (character) aka the courier" in lines
    assert f"E{eid(conn, 'The Gull')} The Gull (place)" in lines


def test_the_schema_only_accepts_known_handles():
    schema = extraction_schema(["E1", "E2", "N1", "N2"], ["M9"], lines=4)
    defs = schema["$defs"]
    participant = defs["Participant"]["properties"]["ref"]
    assert participant["enum"] == ["E1", "E2", "N1", "N2"]
    knowledge = defs["KnowledgeItem"]["properties"]["memory"]
    assert knowledge["enum"] == ["M9"]
    line = defs["MemoryItem"]["properties"]["line"]
    assert {"minimum": 1, "maximum": 4}.items() <= next(
        b for b in line["anyOf"] if b.get("type") == "integer"
    ).items()


def test_with_no_earlier_memories_nothing_can_point_at_one():
    schema = extraction_schema(["E1", "N1"], [], lines=2)
    assert schema["properties"]["knowledge"]["maxItems"] == 0
    assert schema["properties"]["contradictions"]["maxItems"] == 0
    supersedes = schema["$defs"]["MemoryItem"]["properties"]["supersedes"]
    assert supersedes == {"type": "null", "default": None}


# --- a run, end to end ---------------------------------------------------------------------


def canned(conn):
    return {
        "memories": [
            {
                "kind": "event", "detail": "Mira handed Aren a sealed letter.",
                "gist": "Mira gave Aren something.", "importance": 6, "line": 2,
                "participants": [{"ref": f"E{eid(conn, 'Mira')}", "role": "actor"},
                                 {"ref": f"E{eid(conn, 'Aren')}", "role": "target"}],
            }
        ]
    }  # fmt: skip


async def test_a_due_run_asks_the_utility_model_with_the_schema_and_applies_the_answer(
    conn, story, backend
):
    talk(conn, story, 11)
    backend.say(json.dumps(canned(conn)))
    run_id = await extract.run_due(conn, backend.llm, story)

    run = conn.execute("SELECT * FROM extraction_runs WHERE id=?", (run_id,)).fetchone()
    assert (run["status"], run["trigger"], run["role"], run["model"]) == (
        "ok", "cadence", "utility", "rp-model",
    )  # fmt: skip
    sent = backend.requests[0]
    assert sent["response_format"]["type"] == "json_schema" and sent["temperature"] == 0
    assert "[2] Mira: line 1" in sent["messages"][-1]["content"]
    detail = conn.execute("SELECT detail FROM memories").fetchone()["detail"]
    assert detail == "Mira handed Aren a sealed letter."


async def test_a_scene_closing_is_read_by_the_reasoning_role(conn, story, backend):
    conn.execute(
        "INSERT INTO model_roles(role, provider_id, model) VALUES('reasoning', 1, 'thinker')"
    )
    talk(conn, story, 3)
    scene = conn.execute(
        "INSERT INTO scenes(story_id, start_story_time) VALUES(?, 0)", (story,)
    ).lastrowid
    new = chat.append_message(conn, story, "user", "Later, at the docks.", eid(conn, "Aren"))
    conn.execute("UPDATE messages SET scene_id=? WHERE id=?", (scene, new))
    chat.append_message(conn, story, "assistant", "...", eid(conn, "Mira"))
    backend.say(json.dumps({}))
    run_id = await extract.run_due(conn, backend.llm, story)
    run = conn.execute("SELECT trigger, role FROM extraction_runs WHERE id=?", (run_id,)).fetchone()
    assert tuple(run) == ("scene", "reasoning")
    assert backend.requests[0]["model"] == "thinker"


async def test_a_failing_window_is_retried_twice_then_left_for_the_user(conn, story, backend):
    talk(conn, story, 11)
    for _ in range(3):
        backend.say(httpx2.Response(500, text="boom"))
        await extract.run_due(conn, backend.llm, story)
    assert await extract.run_due(conn, backend.llm, story) is None  # no fourth automatic try
    run = conn.execute("SELECT status, attempts, error FROM extraction_runs").fetchone()
    assert (run["status"], run["attempts"]) == ("failed", 3) and "boom" in run["error"]

    backend.say(json.dumps({}))
    run_id = await extract.run_due(conn, backend.llm, story, manual=True)
    assert (
        conn.execute("SELECT status FROM extraction_runs WHERE id=?", (run_id,)).fetchone()[0]
        == "ok"
    )


async def test_witnesses_are_exact_to_the_line_where_it_happened(conn, story, backend):
    aren, mira, tobin = (eid(conn, n) for n in ("Aren", "Mira", "Tobin"))
    first = chat.append_message(conn, story, "user", "Tobin, fetch the ale.", aren)
    chat.set_presence(conn, story, tobin, False)
    chat.append_message(conn, story, "assistant", "Mira slips Aren a letter.", mira)
    back = chat.append_message(conn, story, "user", "Welcome back.", aren)
    chat.set_presence(conn, story, tobin, True)
    last = chat.append_message(conn, story, "assistant", "Mira toasts.", mira)
    both = {
        "kind": "event",
        "gist": "g",
        "importance": 5,
        "participants": [{"ref": f"E{mira}", "role": "actor"}],
    }
    data = {
        "memories": [both | {"detail": "letter", "line": 2}, both | {"detail": "toast", "line": 4}]
    }
    extract.apply(conn, extract.open_run(conn, story, first, last, "manual"), data)

    def knowers(detail):
        rows = conn.execute(
            "SELECT knower_id FROM knowledge JOIN memories m ON m.id=memory_id WHERE m.detail=?",
            (detail,),
        )
        return {r[0] for r in rows}

    assert tobin not in knowers("letter")  # he was fetching ale
    assert knowers("toast") == {aren, mira, tobin}
    assert back  # (the line he came back after)


# --- the worker ----------------------------------------------------------------------------


async def test_the_worker_reads_once_the_story_goes_quiet(conn, story, backend):
    talk(conn, story, 11)
    backend.say(json.dumps({}))
    worker = extract.Worker(conn, backend.llm, delay=0.01)
    worker.poke(story)
    await worker.idle()
    assert conn.execute("SELECT status FROM extraction_runs").fetchone()[0] == "ok"


async def test_a_turn_on_the_same_endpoint_stops_the_worker_and_leaves_no_trace(
    conn, story, backend
):
    talk(conn, story, 11)
    started = asyncio.Event()

    async def slow(request):
        started.set()
        await asyncio.sleep(5)
        return httpx2.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    from kataki.llm import LLM

    worker = extract.Worker(conn, LLM(transport=httpx2.MockTransport(slow)), delay=0)
    worker.poke(story)
    await started.wait()
    worker.turn_started(story, base_url="http://fake/v1")
    await worker.idle()
    assert conn.execute("SELECT count(*) FROM extraction_runs").fetchone()[0] == 0


async def test_a_worker_on_another_endpoint_keeps_going(conn, story):
    talk(conn, story, 11)
    started = asyncio.Event()

    async def slow(request):
        started.set()
        await asyncio.sleep(0.05)
        return httpx2.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    from kataki.llm import LLM

    worker = extract.Worker(conn, LLM(transport=httpx2.MockTransport(slow)), delay=0)
    worker.poke(story)
    await started.wait()
    worker.turn_started(story, base_url="http://elsewhere/v1")  # a separate CPU utility server
    await worker.idle()
    assert conn.execute("SELECT status FROM extraction_runs").fetchone()[0] == "ok"


def test_startup_forgets_runs_that_never_finished(conn, story):
    ids = talk(conn, story, 3)
    run = extract.open_run(conn, story, ids[0], ids[2], "cadence")
    conn.execute("UPDATE extraction_runs SET status='running' WHERE id=?", (run,))
    extract.recover(conn)
    assert conn.execute("SELECT count(*) FROM extraction_runs").fetchone()[0] == 0
