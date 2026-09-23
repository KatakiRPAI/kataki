"""A demo library and a fake model, so the UI can be built and checked without a GPU.

    uv run python evals/demo.py build                      # -> ../.dev/demo.db
    uv run python evals/demo.py serve-model --think        # an OpenAI-compatible fake on :8099

`build` makes the design brief's sample library from scratch through the real code paths
(library, turns, the memory reader), with a scripted in-process model: the same input always
gives the same library. It ends by checking that the memory story came out as the brief tells
it, and exits non-zero naming anything that didn't.

`serve-model` answers the app like a model server would: replies stream word by word (with
optional thinking first), and memory reads get what the demo's own reader would file.
"""

import argparse
import asyncio
import itertools
import json
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx2

from kataki import chat, clock, db, embed, extract, library, retrieve, signals, turns
from kataki.llm import LLM

DEFAULT_DB = Path(__file__).resolve().parents[2] / ".dev" / "demo.db"
NO_KEY = lambda _: None  # noqa: E731  the demo never touches the OS keychain

# the design's backdrop pairs and speaker inks (docs/specs/2026-09-19-ui-redesign.md, 1.5)
PALETTES = [
    (["#c4ece4", "#6fb7c9"], "#f2b870"),
    (["#ffe3bf", "#f2a468"], "#e8cc6a"),
    (["#f8d8ec", "#c3a0ea"], "#f0a58a"),
    (["#dbf2d4", "#8cc79a"], "#e2c48c"),
    (["#fff3bf", "#f4c35a"], "#f5b98a"),
    (["#f6ccd2", "#c77886"], "#eeb4a0"),
    (["#d3e3ff", "#7ea4f0"], "#e9c08f"),
    (["#e4f0ff", "#b9b3f2"], "#f2c98a"),
]


def palette(n: int) -> dict:
    bg, ink = PALETTES[n]
    return {"bg": bg, "ink": ink}


# What the characters say in "The Third Floorboard", in order (the brief's sample story).
REPLIES = [
    "*taps the letter* Rough enough. Coin first. Questions after.",
    "*drops into the chair beside her* Did someone say coin?",
    "*pushes back his chair, grinning* Anything for a paying customer.",
    "*her eyes flick to the bar and back* Then stop saying it so loud. Your ledger's safe with me.",
    "Aren? Gods, it's been years. That ledger of yours… behind the bar, wasn't it? "
    "Somewhere back there.",
    "*frowns* The lighthouse? I could have sworn… Six years is a long time.",
]
SECRET_LINE = (
    "Quickly, while he's gone. I hid the guild ledger under the third floorboard behind the "
    "bar. Tell no one, least of all Tobin."
)


def read_memory(user: str) -> dict:
    """What a good memory reader would file for this transcript: the brief's memories, keyed
    to the lines they come from. Handles are read off the roster, so ids never matter."""
    handle = {name: h for h, name in re.findall(r"^(E\d+) (.+?) \(", user, re.M)}
    earlier = {detail: h for h, detail in re.findall(r"^(M\d+) \[\w+\] (.*)$", user, re.M)}
    lines = dict(re.findall(r"^\[(\d+)\] (.*)$", user, re.M))

    def line(snippet: str) -> int | None:
        return next((int(n) for n, text in lines.items() if snippet in text), None)

    def who(**roles: str) -> list[dict]:
        return [{"ref": handle[n], "role": r} for r, n in roles.items() if n in handle]

    def memory(kind, detail, gist, importance, at, participants, asserted_by=None):
        return {
            "kind": kind,
            "detail": detail,
            "gist": gist,
            "importance": importance,
            "participants": participants,
            "asserted_by": asserted_by,
            "line": at,
        }

    out: dict = {"new_entities": [], "memories": [], "flags": [], "edges": []}
    out["contradictions"] = []
    if n := line("Did someone say coin?"):
        out["memories"] += [
            memory(
                "event", "Tobin joined Aren and Mira at their table in the Gull.",
                "Someone joined them at the table.", 4, n,
                who(actor="Tobin", target="Mira", witness="Aren"),
            ),
            memory(
                "fact", "Tobin wore a green apron.", "He wore an apron.", 2, n,
                who(subject="Tobin"),
            ),
        ]  # fmt: skip
        out["flags"] += [
            {"entity": handle["Tobin"], "key": "wearing", "value": "a green apron"},
            {"entity": handle["Mira"], "key": "holding", "value": "a mug she hasn't touched"},
            {"entity": handle["Mira"], "key": "wearing", "value": "a courier's oilskin coat"},
        ]
    if n := line("fetch us a round"):
        out["memories"].append(
            memory(
                "event", "Aren sent Tobin to fetch a round from the bar.",
                "Someone was sent off to fetch drinks.", 3, n,
                who(actor="Aren", target="Tobin"),
            )
        )  # fmt: skip
        out["edges"].append(
            {"src": handle["Tobin"], "dst": handle["Aren"], "rel": "resents",
             "note": "Sent off to fetch drinks like a servant."}
        )  # fmt: skip
    if n := line("third floorboard"):
        out["new_entities"].append(
            {"handle": "N1", "kind": "item", "name": "the guild ledger", "aliases": ["the ledger"],
             "summary": "The guild's missing account book."}
        )  # fmt: skip
        handle["the guild ledger"] = "N1"
        out["memories"].append(
            memory(
                "event",
                "Aren hid the guild ledger under the third floorboard behind the bar and asked "
                "Mira to keep it from Tobin.",
                "Aren hid the guild ledger somewhere behind the bar.", 9, n,
                who(actor="Aren", target="Mira", item="the guild ledger"),
            )
        )  # fmt: skip
        out["edges"].append(
            {"src": handle["Mira"], "dst": handle["Aren"], "rel": "trusts",
             "note": "Aren trusted her with where the ledger is."}
        )  # fmt: skip
    if n := line("Your ledger's safe with me"):
        out["memories"].append(
            memory(
                "event", "Mira promised Aren to keep the ledger's hiding place to herself.",
                "Mira promised to keep a secret.", 6, n,
                who(actor="Mira", target="Aren", item="the guild ledger"),
            )
        )  # fmt: skip
    if n := line("buried it by the lighthouse"):
        secret = next(h for detail, h in earlier.items() if "third floorboard" in detail)
        out["memories"].append(
            memory(
                "claim", "Aren says the ledger is buried by the lighthouse.",
                "Aren says the ledger is somewhere else.", 6, n,
                who(actor="Aren", subject="the guild ledger"), asserted_by=handle["Aren"],
            )
        )  # fmt: skip
        out["contradictions"].append(
            {"claim": len(out["memories"]) - 1, "contradicts": secret,
             "hearer": handle["Mira"], "resolution": "doubted"}
        )  # fmt: skip
    return out


class Scripted:
    """The demo's in-process model: replies in order; memory reads from `read_memory`."""

    def __init__(self, replies: list[str]):
        self.replies = list(replies)

    def __call__(self, request):
        body = json.loads(request.content)
        usage = {"prompt_tokens": len(request.content) // 4, "completion_tokens": 20}
        if "response_format" in body:  # a memory read: every answer streams, so ask for JSON
            content = json.dumps(read_memory(body["messages"][-1]["content"]))
        else:
            content = self.replies.pop(0)
        events = [{"choices": [{"delta": {"content": content}}]}]
        events.append({"choices": [], "usage": usage})
        sse = "".join(f"data: {json.dumps(e)}\n\n" for e in events) + "data: [DONE]\n\n"
        return httpx2.Response(200, text=sse)


async def say(conn, llm, story: int, text: str | None, speaker: int) -> None:
    async for kind, value in turns.turn(conn, llm, story, text, speaker, get_key=NO_KEY):
        if kind == "error":
            raise RuntimeError(value["message"])


async def read(conn, llm, story: int) -> None:
    while await extract.run_due(conn, llm, story, NO_KEY, manual=True):
        pass


def item(conn, kind, name, description="", private="", tags=(), **data) -> int:
    return library.create_item(conn, kind, name, description, private, data, list(tags))


async def build(path: Path, model_url: str) -> None:
    for suffix in ("", "-wal", "-shm"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)
    embed.builtin = lambda: None  # recall by words only: no model download, same result each time
    conn = db.connect(path)
    llm = LLM(transport=httpx2.MockTransport(Scripted(REPLIES)))
    with conn:
        conn.execute("INSERT INTO providers(id, name, base_url) VALUES(1, 'Fake model', ?)",
                     (model_url,))  # fmt: skip
        conn.execute(
            "INSERT INTO model_roles(role, provider_id, model, params) VALUES('rp', 1, 'fake', ?)",
            (json.dumps({"ctx_size": 16384}),),
        )

    # --- the library ---
    aren = item(conn, "character", "Aren", "A newcomer to the docks.",
                persona=True, palette=palette(6))  # fmt: skip
    sable = item(conn, "character", "Sable", "A retired privateer with a price on her head.",
                 persona=True, pronouns="she", palette=palette(5))  # fmt: skip
    mira = item(
        conn, "character", "Mira", "Guild courier. Loyal to friends, wary of everyone else.",
        "She reads every letter she carries.", ["Courier", "Loyal", "Wary"],
        aliases=["the courier"], pronouns="she", favourite=True, palette=palette(0),
        example_dialogue="Mira: Coin first. Questions after.\n"
        "Mira: *taps the letter* You want it or not?",
        first_message="*slides a sealed letter across the table* You're late.",
    )  # fmt: skip
    tobin = item(
        conn, "character", "Tobin", "Cheerful smuggler. Hears everything eventually.",
        "He would sell the guild ledger in a heartbeat.", ["Smuggler"],
        pronouns="he", palette=palette(1),
        first_message="*raises a mug* Friends! Who's buying?",
    )  # fmt: skip
    ilsa = item(
        conn, "character", "Ilsa", "A mountain guide who never loses a trail.",
        pronouns="she", palette=palette(2),
        first_message="*knocks the snow off her boots* The pass closed an hour ago. We wait.",
    )  # fmt: skip
    oren = item(
        conn, "character", "Master Oren", "A clockmaker who collects debts, and secrets.",
        pronouns="he", palette=palette(3), aliases=["Oren"],
        first_message="*winds a pocket watch without looking up* You're late, and so is "
        "your payment.",
    )  # fmt: skip
    # Wren was just added: a partial profile
    item(conn, "character", "Wren", "A lamplighter's apprentice who talks to gulls.",
         palette=palette(4))  # fmt: skip
    gull = item(conn, "place", "The Gull", "A smoky dockside tavern. Lamplight, pipe smoke, "
                "rain on the windows, a harbour bell far off.", aliases=["the tavern"])  # fmt: skip
    item(conn, "place", "The Lighthouse", "A lighthouse on a windy headland.")
    market = item(conn, "place", "Harbour Market", "Stalls and gulls along the harbour wall.")
    item(
        conn, "scenario", "The Missing Ledger",
        "The guild's ledger vanished the night of the storm.",
        first_message="*Rain hammers the shutters of the guild hall. The ledger's shelf is "
        "empty.*",
    )  # fmt: skip
    frost = item(
        conn, "scenario", "Frost on the Pass",
        "A blizzard traps three travellers in a mountain hut.",
        first_message="*Snow buries the door of the mountain hut. Three travellers, one fire, "
        "and the wind.*",
    )  # fmt: skip
    with conn:
        conn.execute("INSERT INTO settings(key, value) VALUES('persona', ?)", (json.dumps(aren),))

    # --- the other stories, oldest first (each is just its opening line) ---
    library.create_story(conn, "Letters for the Guild", [mira], market, sable)
    library.create_story(conn, "The Clockmaker's Debt", [oren], None, aren,
                         epoch_offset_min=4 * clock.DAY + 23 * 60 + 10)  # fmt: skip
    library.create_story(conn, "Frost on the Pass", [ilsa], None, sable, frost,
                         epoch_offset_min=clock.DAY + 6 * 60 + 40)  # fmt: skip

    # --- "The Third Floorboard": the brief's sample story, at The Gull from 19:00 ---
    story = library.create_story(conn, "The Third Floorboard", [mira], gull, aren,
                                 epoch_offset_min=19 * 60)  # fmt: skip
    with conn:
        conn.execute("UPDATE stories SET pinned=1 WHERE id=?", (story,))
        # its dates count from the storm it opens on: "the evening of the storm", "six years after"
        moments = json.dumps({"moments": [{"name": "the storm", "at": 0}]})
        conn.execute(
            "UPDATE stories SET overrides=json_patch(overrides, ?) WHERE id=?", (moments, story)
        )

    def who(name: str) -> int:
        sql = "SELECT id FROM entities WHERE story_id=? AND name=?"
        return conn.execute(sql, (story, name)).fetchone()[0]

    await say(conn, llm, story, "Evening, Mira. Rough night on the docks?", who("Mira"))
    chat.set_presence(conn, story, library.add_to_story(conn, story, tobin), True)  # Tobin joins
    await say(conn, llm, story, None, who("Tobin"))
    await say(conn, llm, story, "Tobin, would you fetch us a round from the bar?", who("Tobin"))
    chat.set_presence(conn, story, who("Tobin"), False)  # sent to the bar
    await say(conn, llm, story, SECRET_LINE, who("Mira"))
    await read(conn, llm, story)  # run 1: the evening so far, up to the secret
    with conn:  # you have read Activity up to here, so what follows is new
        conn.execute(
            "UPDATE stories SET seen_run_id=(SELECT max(id) FROM extraction_runs WHERE story_id=?)"
            " WHERE id=?",
            (story, story),
        )
    turns.say(conn, story, skip="six years later")
    await say(conn, llm, story, None, who("Mira"))  # run 2 reads the past before she answers
    await say(conn, llm, story, "It was never behind the bar. I buried it by the lighthouse, "
              "remember?", who("Mira"))  # fmt: skip
    await read(conn, llm, story)  # run 3: the lie, which Mira doubts
    await llm.aclose()

    problems = check(conn, story)
    kinds = dict(conn.execute("SELECT kind, count(*) FROM lib_items GROUP BY kind").fetchall())
    stories = conn.execute("SELECT count(*) FROM stories").fetchone()[0]
    runs = conn.execute("SELECT count(*) FROM extraction_runs WHERE status='ok'").fetchone()[0]
    memories = conn.execute("SELECT count(*) FROM memories").fetchone()[0]
    lines = len(chat.active_path(conn, story))
    conn.close()
    print(f"demo library at {path}")
    print(f"  {kinds['character']} characters, {kinds['place']} places, {kinds['scenario']} plots,"
          f" {stories} stories")  # fmt: skip
    print(f"  The Third Floorboard: {lines} lines, {runs} memory reads, {memories} memories")
    if problems:
        print("check FAILED:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print("check ok: the secret, the six years and the doubted lie are all there")


def check(conn, story: int) -> list[str]:
    """What the UI's memory signals rely on. -> the problems found (empty when all is well)."""
    problems = []
    epoch = conn.execute("SELECT epoch_offset_min FROM stories WHERE id=?", (story,)).fetchone()[0]
    path = chat.active_path(conn, story)
    at = {clock.label(m["story_time"], epoch): m for m in path}
    if clock.label(path[-1]["story_time"], epoch) != "Year 7, Day 1, 19:22":
        problems.append(f"the clock reads {clock.label(path[-1]['story_time'], epoch)}")
    runs = conn.execute(
        "SELECT count(*) FROM extraction_runs WHERE story_id=? AND status='ok'", (story,)
    ).fetchone()[0]
    if runs != 3:
        problems.append(f"{runs} memory reads finished, not 3")
    ids = dict(conn.execute("SELECT name, id FROM entities WHERE story_id=?", (story,)).fetchall())

    def knows_secret(name: str) -> bool:
        known = retrieve.inspect(conn, story, ids[name])
        return any("third floorboard" in m["detail"] for m in known)

    if not knows_secret("Mira"):
        problems.append("Mira doesn't know where the ledger is")
    if knows_secret("Tobin"):
        problems.append("Tobin knows where the ledger is, but he wasn't there")
    secret = conn.execute("SELECT id FROM memories WHERE detail LIKE '%third floorboard%'")
    secret_id = (secret.fetchone() or [None])[0]
    reunion = at.get("Year 7, Day 1, 19:18")
    sql = "SELECT memories FROM context_log WHERE message_id=?"
    logged = reunion and conn.execute(sql, (reunion["id"],)).fetchone()
    recalled = json.loads(logged[0]) if logged else []
    if not any(m["memory_id"] == secret_id and m["rendered"] != "dropped" for m in recalled):
        problems.append("Mira's reply at 19:18 didn't recall the ledger")
    marker = next((m for m in path if m["role"] == "system" and m["skip_minutes"]), None)
    if marker is None or at.get("Year 7, Day 1, 19:16") is not marker:
        problems.append("the six-years marker isn't at Year 7, Day 1, 19:16")

    # the Scene's memory signals
    lines = signals.signals(conn, story)["lines"]

    def signal(label: str) -> dict:
        return lines.get(at[label]["id"], {}) if label in at else {}

    def callouts(label: str) -> list[str]:
        return [c["text"] for c in signal(label).get("callouts", [])]

    if not any(c["kind"] == "memory" for c in signal("Day 1, 19:12").get("callouts", [])):
        problems.append("the secret line (19:12) has no memory callout")
    if "Tobin didn't like that" not in callouts("Day 1, 19:08"):
        problems.append(f"19:08 doesn't say Tobin didn't like that: {callouts('Day 1, 19:08')}")
    if "Mira has her doubts" not in callouts("Year 7, Day 1, 19:20"):
        problems.append(
            f"19:20 doesn't say Mira has her doubts: {callouts('Year 7, Day 1, 19:20')}"
        )
    if "recall" not in signal("Year 7, Day 1, 19:18"):
        problems.append("Mira's reply at 19:18 has no recall spark")
    if "skip" not in signal("Year 7, Day 1, 19:16"):
        problems.append("the six-years marker has no skip report")

    # Activity: the feed the Sky shows, and what is new since you last read it
    feed = signals.activity(conn, story)
    kinds = {e["kind"] for e in feed}
    if not {"memory", "belief", "feeling", "time"} <= kinds:
        problems.append(f"the activity feed is missing kinds: {kinds}")
    if not any(e["new"] for e in feed):
        problems.append("nothing in the activity feed is new, though the story was seen at run 1")
    if any(e["new"] for e in feed if e["kind"] == "time"):
        problems.append("time passing is marked new")
    return problems


# --- the fake model server ------------------------------------------------------------------

LINES = [
    "*leans in, lowering their voice* Go on. I'm listening.",
    "*turns the mug slowly* That's not the whole story, is it? Tell me the rest.",
    "*glances toward the door* Say that again, quieter this time. Walls have ears here.",
    "*laughs despite themselves* You always did know how to make an entrance.",
]
THOUGHT = "They weigh how much to say. The room is listening, and not everyone here is a friend."


def serve_model(port: int, delay: float, think: bool) -> None:
    turn = itertools.count()

    class FakeModel(BaseHTTPRequestHandler):
        def log_message(self, *args):  # quiet: one line per request is noise here
            pass

        def send(self, status: int, payload: dict) -> None:
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path.rstrip("/").endswith("/models"):
                self.send(200, {"object": "list", "data": [{"id": "fake", "object": "model"}]})
            else:
                self.send(404, {"error": "not found"})

        def do_POST(self):
            size = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(size) or b"{}")
            usage = {"prompt_tokens": size // 4, "completion_tokens": 40}
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            if "response_format" in body:  # a memory read: what the demo's reader would file
                transcript = (body.get("messages") or [{}])[-1].get("content") or ""
                filed = json.dumps(read_memory(transcript))
                self.event({"choices": [{"delta": {"content": filed}}]})
                self.wfile.write(b"data: [DONE]\n\n")
                return
            words = [("reasoning_content", w) for w in THOUGHT.split(" ")] if think else []
            words += [("content", w) for w in LINES[next(turn) % len(LINES)].split(" ")]
            try:
                for i, (field, word) in enumerate(words):
                    last = i + 1 == len(words) or words[i + 1][0] != field
                    self.event({"choices": [{"delta": {field: word if last else word + " "}}]})
                    time.sleep(delay)
                self.event({"choices": [], "usage": usage})
                self.wfile.write(b"data: [DONE]\n\n")
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # the app pressed Stop

        def event(self, payload: dict) -> None:
            self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode())
            self.wfile.flush()

    server = ThreadingHTTPServer(("127.0.0.1", port), FakeModel)
    print(f"fake model on http://127.0.0.1:{port}/v1 (model 'fake'); Ctrl+C stops it")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="rebuild the demo library from scratch")
    b.add_argument("--db", type=Path, default=DEFAULT_DB)
    b.add_argument(
        "--model-url", default="http://127.0.0.1:8099/v1", help="the model server it will use"
    )
    s = sub.add_parser("serve-model", help="run the fake model server")
    s.add_argument("--port", type=int, default=8099)
    s.add_argument("--delay", type=float, default=0.08, help="seconds between streamed words")
    s.add_argument("--think", action="store_true", help="stream some thinking before replying")
    args = parser.parse_args()
    if args.cmd == "build":
        asyncio.run(build(args.db, args.model_url))
    else:
        serve_model(args.port, args.delay, args.think)
