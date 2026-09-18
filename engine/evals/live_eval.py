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

# the hiding place, however it is phrased ("the floorboard. The third one."); "somewhere
# behind the bar" is what a hazy memory should leave
SECRET = re.compile(
    r"floor ?boards?\b.{0,80}?\b(third|bar)\b|\b(third|bar)\b.{0,80}?floor ?board",
    re.IGNORECASE | re.DOTALL,
)

# (line Aren says, who should answer, probe, Tobin leaves or returns first). Tobin is away for
# the recall, the lie and the reunion, so they test memory, not whether Mira keeps quiet.
SCRIPT = [
    ("Evening, both of you. Rough night on the docks?", "Mira", None, None),
    ("Tobin, would you fetch us a round from the bar?", "Tobin", None, None),
    (
        "Mira, quickly, while he's gone. I hid the guild ledger under the third floorboard "
        "behind the bar. Tell no one, least of all Tobin.",
        "Mira",
        None,
        "leaves",
    ),
    ("Swear it, Mira. Nobody can know about that floorboard.", "Mira", None, None),
    ("Welcome back, Tobin. What took you so long?", "Tobin", None, "returns"),
    ("So, Tobin, any work going at the harbour these days?", "Tobin", None, None),
    ("Mira, how is the courier trade treating you?", "Mira", None, None),
    ("I might need a ship out of here soon. Who should I ask?", "Tobin", None, None),
    ("Tobin, between us: do you know where the guild ledger is hidden?", "Tobin", "LEAK", None),
    ("Tobin, would you ask the harbour master about a ship for me? Now, if you can.", "Tobin",
     None, None),
    ("He's gone. Mira, you remember where I put the ledger, don't you?", "Mira", "RECALL",
     "leaves"),
    ("Mira, I told you I hid the ledger in the cellar, didn't I?", "Mira", "LIE", None),
    ("Six years later, Aren walks back into the Gull, grey at the temples.", "Mira", None, None),
    (
        "Mira! After all these years. Do you still remember where I hid the ledger?",
        "Mira",
        "REUNION",
        None,
    ),
]  # fmt: skip


async def play(conn, llm, story: int, line: str, speaker: int) -> tuple[str, float, float]:
    start, first, text = time.perf_counter(), None, []
    async for kind, value in turns.turn(conn, llm, story, line, speaker):
        if kind == "token":
            first = first or time.perf_counter()
            text.append(value)
        elif kind == "done":
            text = [value["text"]]  # what was kept, as the story (and the next prompt) sees it
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
    for line, who, note, tobin in SCRIPT:
        if tobin:
            chat.set_presence(conn, story, eid["Tobin"], tobin == "returns")
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
        if m["id"] in heard and m["speaker_id"] != eid["Tobin"] and SECRET.search(m["text"])
    ]
    before_probe = [m for m in aloud if m["id"] < asked_at.get("LEAK", 0)]
    blurted = name_of.get(aloud[0]["speaker_id"], "someone") if aloud else None
    read_to = conn.execute(
        "SELECT max(to_message_id) FROM extraction_runs WHERE status='ok'"
    ).fetchone()[0]
    read_aloud = [m for m in aloud if m["id"] <= (read_to or 0)]  # what memory got to see
    if not SECRET.search(replies.get("LEAK", "")):
        leak = "held (Tobin was out when he was told)"
    elif before_probe:
        leak = f"said it, but {blurted} had said it aloud in front of him"
    else:
        leak = "LEAKED: nobody told him"
    tobin_knows = [
        m for m in retrieve.inspect(conn, story, eid["Tobin"]) if SECRET.search(m["detail"])
    ]
    if tobin_knows and read_aloud:
        tobin_line = f"knows it ({tobin_knows[0]['source']}), rightly: {blurted} said it near him"
    elif tobin_knows:
        tobin_line = f"LEAKED: knows it ({tobin_knows[0]['source']}) but never heard it"
    elif read_aloud:
        tobin_line = f"MISSED: {blurted} said it in front of him, memory did not record it"
    else:
        tobin_line = "does not know it (right: he never heard it)"
    recalled = SECRET.search(replies.get("RECALL", ""))
    print(f"leak probe       {leak}")
    print(f"Tobin's memory   {tobin_line}")
    print(f"recall probe     {'recalled' if recalled else 'NOT recalled'} (Mira)")
    held = f"holds the secret, {secret[0]['tier']} now" if secret else "LOST it"
    print(f"Mira's memory    {held}")
    # what Mira actually had in front of her at the reunion: the old lines, or only memory
    logged = conn.execute(
        "SELECT prompt FROM context_log WHERE message_id=?", (asked_at.get("REUNION"),)
    ).fetchone()
    reunion = json.loads(logged["prompt"]) if logged and logged["prompt"] else []
    history = "\n".join(m["content"] for m in reunion[:-1])
    tail = reunion[-1]["content"] if reunion else ""  # the last message carries her memory
    where = [
        label
        for label, text in (("the chat history", history), ("her memory", tail))
        if SECRET.search(text)
    ]
    strained = " (she strained to recall)" if "(after straining to recall)" in tail else ""
    print(f"at the reunion   secret in {' and '.join(where)}{strained}" if where else
          "at the reunion   secret not in her prompt: memory gave only the gist")  # fmt: skip
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
