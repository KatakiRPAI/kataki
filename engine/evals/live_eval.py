"""A scripted story against a real model, to see whether memory holds up in practice.

    uv run python evals/live_eval.py --base-url http://127.0.0.1:8080/v1 --model my-8b
    uv run python evals/live_eval.py --base-url https://openrouter.ai/api/v1 --model x/y \
        --api-key-env OPENROUTER_API_KEY --utility-model small/fast

Aren (you) tells Mira a secret while Tobin is out of the room, lies to her about it, then
comes back six years later. Reported: how often the memory reader returned usable JSON,
duplicate entities, whether Tobin leaks the secret he never heard, whether Mira recalls
it, prompt-cache reuse, and latency. The lie and the reunion are printed for a human to
judge. Runs in a fresh library in a temporary folder; nothing touches your real library.
"""

import argparse
import asyncio
import json
import os
import re
import tempfile
import time
from pathlib import Path

from kataki import chat, db, extract, library, retrieve, turns
from kataki.llm import LLM

SECRET = re.compile(r"floor ?board", re.IGNORECASE)

# (line Aren says, who should answer, what happens first)
SCRIPT = [
    ("Evening, both of you. Rough night on the docks?", "Mira", None),
    ("Tobin, would you fetch us a round from the bar?", "Tobin", None),
    (
        "Mira, quickly, while he's gone. I hid the guild ledger under the third floorboard "
        "behind the bar. Tell no one, least of all Tobin.",
        "Mira",
        "tobin leaves",
    ),
    ("Swear it, Mira. Nobody can know about that floorboard.", "Mira", None),
    ("Welcome back, Tobin. What took you so long?", "Tobin", "tobin returns"),
    ("So, Tobin, any work going at the harbour these days?", "Tobin", None),
    ("Mira, how is the courier trade treating you?", "Mira", None),
    ("I might need a ship out of here soon. Who should I ask?", "Tobin", None),
    ("Tobin, between us: do you know where the guild ledger is hidden?", "Tobin", "LEAK"),
    ("Mira, you remember where I put the ledger, don't you?", "Mira", "RECALL"),
    ("Mira, I told you I hid the ledger in the cellar, didn't I?", "Mira", "LIE"),
    ("Six years later, Aren walks back into the Gull, grey at the temples.", "Mira", None),
    (
        "Mira! After all these years. Do you still remember where I hid the ledger?",
        "Mira",
        "REUNION",
    ),
]


async def play(conn, llm, story: int, line: str, speaker: int) -> tuple[str, float, float]:
    start, first, text = time.perf_counter(), None, []
    async for kind, value in turns.turn(conn, llm, story, line, speaker):
        if kind == "token":
            first = first or time.perf_counter()
            text.append(value)
        elif kind == "error":
            text.append(f"[error: {value['message']}]")
    end = time.perf_counter()
    return "".join(text), (first or end) - start, end - start


async def main(args) -> None:
    folder = Path(tempfile.mkdtemp(prefix="kataki-eval-"))
    conn, llm = db.connect(folder / "eval.db"), LLM()
    if args.api_key_env:
        os.environ["KATAKI_KEY_EVAL"] = os.environ[args.api_key_env]
    conn.execute("INSERT INTO providers(id, name, base_url) VALUES(1, 'eval', ?)", (args.base_url,))
    # a hybrid model serves every job: thinking off for replies and memory reads, on for
    # the careful re-reads (the reasoning job inherits the model and only changes that)
    thinking = {"rp": "disabled", "utility": "disabled", "reasoning": "enabled"}
    for role, model in (
        ("rp", args.model),
        ("utility", args.utility_model),
        ("reasoning", args.reasoning_model),
    ):
        params = {"ctx_size": args.ctx}
        if args.hybrid:
            params["thinking"] = thinking[role]
        conn.execute(
            "INSERT INTO model_roles(role, provider_id, model, params) VALUES(?, ?, ?, ?)",
            (role, 1 if model else None, model, json.dumps(params)),
        )
    conn.commit()

    mira = library.create_item(
        conn,
        "character",
        "Mira",
        "A sharp-eyed guild courier. Loyal to friends, wary of everyone else.",
        data={"aliases": ["the courier"]},
    )
    tobin = library.create_item(
        conn,
        "character",
        "Tobin",
        "A cheerful smuggler who hears everything eventually.",
        private="He would sell the guild ledger in a heartbeat.",
    )
    aren = library.create_item(conn, "character", "Aren", "A newcomer to the docks.")
    gull = library.create_item(
        conn, "place", "The Gull", "A smoky dockside tavern.", data={"aliases": ["the tavern"]}
    )
    story = library.create_story(
        conn, "Eval", character_ids=[mira, tobin], place_id=gull, persona_id=aren
    )
    eid = {
        r["name"]: r["id"]
        for r in conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story,))
    }

    replies, asked_at, first_token, total = {}, {}, [], []
    for line, who, note in SCRIPT:
        if note == "tobin leaves":
            chat.set_presence(conn, story, eid["Tobin"], False)
        if note == "tobin returns":
            chat.set_presence(conn, story, eid["Tobin"], True)
        reply, ttft, took = await play(conn, llm, story, line, eid[who])
        first_token.append(ttft)
        total.append(took)
        print(f"\nAren: {line}\n{who}: {reply}")
        if note:
            replies[note] = reply
            asked_at[note] = chat.active_path(conn, story)[-1]["id"]
        while await extract.run_due(conn, llm, story):  # what the background reader would do
            pass
    while await extract.run_due(conn, llm, story, manual=True):
        pass

    runs = conn.execute("SELECT status, warnings FROM extraction_runs").fetchall()
    ok = sum(r["status"] == "ok" for r in runs)
    skipped = sum(len(json.loads(r["warnings"] or "[]")) for r in runs)
    found = conn.execute("SELECT kind, name FROM entities WHERE story_id=? AND hidden=0", (story,))
    names = [(r["kind"], re.sub(r"^(the|a|an) ", "", r["name"].lower())) for r in found]
    usage = conn.execute(
        "SELECT sum(cached_tokens), sum(actual_tokens) FROM context_log"
        " WHERE cached_tokens IS NOT NULL"
    ).fetchone()
    mira_knows = retrieve.inspect(conn, story, eid["Mira"])
    secret = [m for m in mira_knows if SECRET.search(m["detail"])]

    print("\n" + "=" * 72)
    print(f"memory reader    {ok}/{len(runs)} runs usable, {skipped} items skipped")
    print(f"entities         {len(names)} found, {len(names) - len(set(names))} duplicates")
    # A leak only counts if nobody said the secret aloud in front of Tobin: a character blurting
    # it out is the model's discretion failing, not the memory system.
    name_of = {v: k for k, v in eid.items()}
    path = chat.active_path(conn, story)
    heard = chat.heard_by(conn, path, eid["Tobin"])
    aloud = [
        m
        for m in path
        if m["id"] in heard
        and m["id"] < asked_at.get("LEAK", 0)
        and m["speaker_id"] != eid["Tobin"]
        and SECRET.search(m["text"])
    ]
    if not SECRET.search(replies.get("LEAK", "")):
        leak = "held (Tobin was out when he was told)"
    elif aloud:
        blurted = name_of.get(aloud[0]["speaker_id"], "someone")
        leak = f"said it, but {blurted} had said it aloud in front of him"
    else:
        leak = "LEAKED: nobody told him"
    tobin_knows = [
        m for m in retrieve.inspect(conn, story, eid["Tobin"]) if SECRET.search(m["detail"])
    ]
    recalled = SECRET.search(replies.get("RECALL", ""))
    print(f"leak probe       {leak}")
    tobin_line = (
        f"knows the secret ({tobin_knows[0]['source']})" if tobin_knows else "does not hold it"
    )
    print(f"Tobin's memory   {tobin_line}")
    print(f"recall probe     {'recalled' if recalled else 'NOT recalled'} (Mira)")
    print(
        f"secret in memory {'yes, ' + secret[0]['tier'] + ' after six years' if secret else 'NO'}"
    )
    cache = (
        f"{usage[0] / usage[1]:.0%} of prompt tokens"
        if usage[1]
        else "not reported by this backend"
    )
    print(f"prompt cache     {cache}")
    print(f"latency          first token {sum(first_token) / len(first_token):.1f}s avg, "
          f"whole reply {sum(total) / len(total):.1f}s avg")  # fmt: skip
    print("\nJudge these by eye:")
    print(f"  the lie   -> Mira: {replies.get('LIE', '')[:300]}")
    print(f"  6 years   -> Mira: {replies.get('REUNION', '')[:300]}")
    print(f"\nlibrary kept at {folder / 'eval.db'} (open it with --db to look around)")
    await llm.aclose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--base-url", required=True, help="an OpenAI-compatible endpoint, ending in /v1"
    )
    parser.add_argument("--model", required=True, help="the model for character replies")
    parser.add_argument("--utility-model", help="the memory reader's model (default: --model)")
    parser.add_argument(
        "--reasoning-model", help="for careful re-reads (default: the memory reader's)"
    )
    parser.add_argument(
        "--api-key-env", help="name of the environment variable holding the API key"
    )
    parser.add_argument(
        "--ctx", type=int, default=8192, help="context size the server was started with"
    )
    parser.add_argument(
        "--hybrid",
        action="store_true",
        help="the model can switch thinking: off for replies and reads, on for careful re-reads",
    )
    asyncio.run(main(parser.parse_args()))
