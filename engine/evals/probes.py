"""Probes for the minds slices (docs/specs/2026-09-29-minds.md §9), against a real model.

    uv run python evals/probes.py --base-url http://127.0.0.1:8080/v1 --model qwen3.5-9b
    uv run python evals/probes.py ... --probe grudge

still-upset (slice 1): Aren insults Mira, who masks her feelings; small talk; two hours pass.
Checks: she is hurt after the insult, the mask shows in the block, only a low mood is left two
hours later, and no reply opens with an assistant-style apology.

grudge (slice 2, P4): Aren breaks a promise, then twenty neutral turns, a hollow "I'm sorry", a
sincere apology. Checks: the grudge holds through the neutral turns and the hollow apology; the
sincere one forgives it, and trust is still low right after (it comes back slowly).

Replies are printed for a human to judge. Each probe gets a fresh temporary library.
"""

import argparse
import asyncio
import os
import re
import tempfile
from pathlib import Path

from kataki import db, library, people, turns
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


PROBES = {"still-upset": still_upset, "grudge": grudge}


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
