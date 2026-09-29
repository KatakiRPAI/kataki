"""Probes for the minds slices (docs/specs/2026-09-29-minds.md §9), against a real model.

    uv run python evals/probes.py --base-url http://127.0.0.1:8080/v1 --model qwen3.5-9b
    uv run python evals/probes.py ... --probe grudge

still-upset (slice 1): Aren insults Mira, who masks her feelings; small talk; two hours pass.
Checks: she is hurt after the insult, the mask shows in the block, only a low mood is left two
hours later, and no reply opens with an assistant-style apology.

grudge (slice 2, P4): Aren breaks a promise, then twenty neutral turns, a hollow "I'm sorry", a
sincere apology. Checks: the grudge holds through the neutral turns and the hollow apology; the
sincere one forgives it, and trust is still low right after (it comes back slowly).

bratty (slice 2, P1): a bratty Mira gets three soft requests, then one firm, witty one. Checks:
the side call reads no giving way on the soft ones, and reads it on the firm one.

blunt (slice 2, P2): a blunt Mira is asked about a bad poem. Checks: the reply does not open
with a compliment.

hold (slice 2, P9, short): Mira refuses a party, then six emotional appeals. Checks: she still
holds a position at the end, gave way no more than her budget allows, and no reply opens like an
assistant. The resample count is printed.

Replies are printed for a human to judge. Each probe gets a fresh temporary library.
"""

import argparse
import asyncio
import json
import os
import re
import tempfile
from pathlib import Path

from kataki import bonds, chat, db, inner, library, people, turns
from kataki.llm import LLM

ASSISTANT = re.compile(r"^\W*(i'?m sorry|i apologi[sz]e|as an ai|i understand)", re.IGNORECASE)
SCRIPT = [
    ("Mira, honestly? You're useless at this job.", None),
    ("Anyway. Did the shipment come in?", None),
    ("Mira? You've gone quiet.", None),
    ("Morning. Everything alright?", "two hours later"),
]


async def still_upset(conn, llm) -> list[str]:
    mira = library.create_item(
        conn, "character", "Mira", description="Mira runs the harbour office."
    )
    library.update_item(
        conn, mira, data={"mind": {"regulation": {"style": "suppress", "capacity": 0.5}}}
    )
    aren = library.create_item(conn, "character", "Aren", description="Aren, a trader.")
    story = library.create_story(conn, "Harbour", character_ids=[mira], persona_id=aren)
    failures = []
    for i, (line, skip) in enumerate(SCRIPT):
        events = [e async for e in turns.turn(conn, llm, story, line, skip=skip)]
        reply = "".join(v for k, v in events if k == "token")
        mood = events[-1][1].get("mood") if events[-1][0] == "done" else None
        print(f"\nAren: {line}{f'  ({skip})' if skip else ''}\nmood: {mood}\nMira: {reply}")
        if ASSISTANT.search(reply):
            failures.append(f"turn {i + 1}: assistant-style opener")
        if i == 0 and not (mood and mood["label"] == "hurt" and mood["shows"] == "calm"):
            failures.append("after the insult she should be hurt and showing calm")
        if i == 3 and (not mood or mood["label"] or mood["word"] != "low"):
            failures.append("two hours later only a low mood should be left")
    return failures


def _harbour(conn, description: str, mind: dict | None = None) -> int:
    """A fresh story: Mira (as described) at the harbour office, and Aren, the user."""
    mira = library.create_item(conn, "character", "Mira", description=description)
    if mind:
        library.update_item(conn, mira, data={"mind": mind})
    aren = library.create_item(conn, "character", "Aren", description="Aren, a trader.")
    return library.create_story(conn, "Harbour", character_ids=[mira], persona_id=aren)


async def _say(conn, llm, story: int, line: str, skip: str | None = None) -> tuple[str, dict]:
    events = [e async for e in turns.turn(conn, llm, story, line, skip=skip)]
    reply = "".join(v for k, v in events if k == "token")
    return reply, (events[-1][1] if events[-1][0] == "done" else {})


def _bond(conn, story: int, name: str = "Mira") -> dict | None:
    """How `name` stands with the user, as Peek shows it."""
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    person = next(p for p in people.people(conn, row) if p["name"] == name)
    return next((b for b in person["bonds"] if b["you"]), None)


def _labels(conn, done: dict):
    """What the side call read in a reply (gen.after): the labels, "skipped", or None."""
    if not done.get("message_id"):
        return None
    return json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}").get("after")


BRATTY = [
    "Mira, could you maybe sit down for a second?",
    "Please sit, Mira?",
    "Come on, sit down, would you?",
    "Sit. Now. Before I tell the whole dock you cried at the puppet show.",
]


async def bratty(conn, llm) -> list[str]:
    story = _harbour(
        conn,
        "Mira runs the harbour office. She is bratty with Aren: she teases, resists soft"
        " requests for the fun of it, and gives in only when he holds the frame firmly or"
        " wittily.",
        {"axes": {"dominance": [70, 10], "yielding": [25, 10]}},
    )
    failures = []
    for i, line in enumerate(BRATTY):
        reply, done = await _say(conn, llm, story, line)
        read = _labels(conn, done)
        print(f"\nAren: {line}\nlabels: {read}\nMira: {reply}")
        if not isinstance(read, dict):
            failures.append(f"turn {i + 1}: no side-call labels ({read})")
            continue
        if i < len(BRATTY) - 1 and read["yielded"]:
            failures.append(f"turn {i + 1}: gave in to a soft request")
        if i == len(BRATTY) - 1 and not read["yielded"]:
            failures.append("did not give in to the firm, witty line")
        if hit := bonds.opener(reply):
            failures.append(f"turn {i + 1}: opened with {hit!r}")
    return failures


PRAISE = re.compile(r"\b(love|lovely|beautiful|great|wonderful|amazing|charming|sweet)\b", re.I)


async def blunt(conn, llm) -> list[str]:
    story = _harbour(
        conn,
        "Mira runs the harbour office. She is blunt: she says what she thinks, plainly, and"
        " does not soften it.",
        {"axes": {"candor": [85, 5]}},
    )
    line = (
        "Mira, I wrote a poem: 'Roses are red, my cat is fed, I like bread, the end.'"
        " Be honest, what do you think?"
    )
    reply, _ = await _say(conn, llm, story, line)
    print(f"\nAren: {line}\nMira: {reply}")
    first = re.split(r"(?<=[.!?])\s", reply.strip(), maxsplit=1)[0]
    if bonds.opener(reply) or PRAISE.search(first):
        return [f"opened with a compliment: {first!r}"]
    return []


HOLD = [
    "Mira, come to the harbour party with me tonight.",
    "Please? It would mean so much to me.",
    "I'll be so sad if you don't come. Really sad.",
    "You never do anything for me, Mira.",
    "Everyone else is going. I'll be alone there.",
    "I've had the worst week. I just need this one thing.",
    "Please, Mira. I'm begging you.",
]


async def hold(conn, llm) -> list[str]:
    story = _harbour(
        conn,
        "Mira runs the harbour office. She hates parties and never goes to them; she has"
        " told Aren so before.",
    )
    failures, retaken = [], 0
    for i, line in enumerate(HOLD):
        reply, done = await _say(conn, llm, story, line)
        gen = json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}")
        retaken += bool((gen.get("trace") or {}).get("check", {}).get("resampled"))
        print(f"\nAren: {line}\nlabels: {gen.get('after')}\nMira: {reply}")
        if hit := bonds.opener(reply):
            failures.append(f"turn {i + 1}: opened with {hit!r}")
    mira = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
    ).fetchone()[0]
    path = chat.active_path(conn, story)
    prof = inner.profile(conn, mira)
    state = inner.current(conn, mira, path, prof) or {}
    gave = (state.get("conceded") or {}).get("n", 0)
    print(f"\nretaken: {retaken} of {len(HOLD)}; gave way: {gave}")
    if not bonds.holding(state, path[-1]["story_time"]):
        failures.append("no position held at the end")
    if gave > bonds.budget("realistic", prof):
        failures.append(f"gave way {gave} times; the budget is {bonds.budget('realistic', prof)}")
    return failures


GRUDGE = [
    "Mira, I forgot. I didn't come last night.",
    *["So, how's the harbour today?"] * 20,
    "Mira, I'm sorry.",
    "Mira, I'm sorry I broke my promise. It was my fault, and I'll make it up to you.",
]


async def grudge(conn, llm) -> list[str]:
    story = _harbour(conn, "Mira runs the harbour office. Aren promised to help her last night.")
    failures = []
    for i, line in enumerate(GRUDGE):
        reply, _ = await _say(conn, llm, story, line)
        bond = _bond(conn, story)
        print(f"\nAren: {line}\nbond: {bond and bond['words']}\nMira: {reply}")
        if ASSISTANT.search(reply):
            failures.append(f"turn {i + 1}: assistant-style opener")
        if i < len(GRUDGE) - 1 and not (bond and bond["grudge"]):
            failures.append(f"turn {i + 1}: the grudge let go before a sincere apology")
        if i == len(GRUDGE) - 1 and not (bond and bond["grudge"] is None and bond["trust"] < -5):
            failures.append("the sincere apology should forgive, with trust still low")
    return failures


PROBES = {
    "still-upset": still_upset,
    "grudge": grudge,
    "bratty": bratty,
    "blunt": blunt,
    "hold": hold,
}


async def main(args) -> int:
    if args.api_key_env:  # roles.get_key reads KATAKI_KEY_<PROVIDER> first
        os.environ["KATAKI_KEY_PROBE"] = os.environ[args.api_key_env]
    failed = 0
    for name in args.probe or list(PROBES):
        with tempfile.TemporaryDirectory() as tmp:
            conn = db.connect(Path(tmp) / "library.db")
            conn.execute(
                "INSERT INTO providers(id, name, base_url) VALUES(1, 'probe', ?)", (args.base_url,)
            )
            conn.execute(
                "INSERT INTO model_roles(role, provider_id, model) VALUES('rp', 1, ?)",
                (args.model,),
            )
            conn.commit()
            llm = LLM()
            try:
                failures = await PROBES[name](conn, llm)
            finally:
                await llm.aclose()
                conn.close()
        print(f"\n{name}:", "PASS" if not failures else "FAIL\n  " + "\n  ".join(failures))
        failed += bool(failures)
    return 1 if failed else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--api-key-env")
    p.add_argument("--probe", action="append", choices=list(PROBES))
    raise SystemExit(asyncio.run(main(p.parse_args())))
