"""Probes for the minds slices (docs/specs/2026-09-29-minds.md §9), against a real model.

    uv run python evals/probes.py --base-url http://127.0.0.1:8080/v1 --model qwen3.5-9b

still-upset (slice 1): Aren insults Mira, who masks her feelings; small talk; two hours pass.
Checks: she is hurt after the insult, the mask shows in the block, only a low mood is left two
hours later, and no reply opens with an assistant-style apology. Replies are printed for a human
to judge whether the hurt shows through behaviour without being said. Fresh temporary library.
"""

import argparse
import asyncio
import os
import re
import tempfile
from pathlib import Path

from kataki import db, library, turns
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


async def main(args) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        conn = db.connect(Path(tmp) / "library.db")
        conn.execute(
            "INSERT INTO providers(id, name, base_url) VALUES(1, 'probe', ?)", (args.base_url,)
        )
        conn.execute(
            "INSERT INTO model_roles(role, provider_id, model) VALUES('rp', 1, ?)", (args.model,)
        )
        conn.commit()
        if args.api_key_env:  # roles.get_key reads KATAKI_KEY_<PROVIDER> first
            os.environ["KATAKI_KEY_PROBE"] = os.environ[args.api_key_env]
        llm = LLM()
        try:
            failures = await still_upset(conn, llm)
        finally:
            await llm.aclose()
            conn.close()
    print("\nstill-upset:", "PASS" if not failures else "FAIL\n  " + "\n  ".join(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--api-key-env")
    raise SystemExit(asyncio.run(main(p.parse_args())))
