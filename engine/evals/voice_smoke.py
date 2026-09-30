"""One spoken line against a real speech server (minds slice 10, spec §8.3), in a throwaway
library: a hurt reply with a sigh, rendered, then asked again (the replay must be free).

    uv run python evals/voice_smoke.py --base-url http://127.0.0.1:8880/v1 --model kokoro

Any server of OpenAI's /v1/audio/speech shape works (a local Kokoro on the CPU costs nothing).
A paid endpoint is one call: state its price and get the owner's yes first.
"""

import argparse
import asyncio
import functools
import os
import tempfile
import time
from pathlib import Path

from kataki import chat, db, library, media, speech, usage
from kataki.llm import LLM


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", default="kokoro")
    ap.add_argument("--voice", default="af_heart")
    ap.add_argument("--api-key-env", default="")
    ap.add_argument("--keep", help="copy the audio here")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        conn = db.connect(Path(tmp) / "library.db")
        conn.execute("INSERT INTO providers(id, name, base_url) VALUES(1, 'tts', ?)", (a.base_url,))
        conn.execute(
            "INSERT INTO model_roles(role, provider_id, model, params) VALUES('voice', 1, ?, ?)",
            (a.model, f'{{"voice": "{a.voice}"}}'),
        )
        conn.execute("INSERT INTO settings(key, value) VALUES('voice.on', 'true')")
        conn.commit()
        lib = library.create_item(conn, "character", "Mira")
        story = library.create_story(conn, "Smoke", character_ids=[lib])
        who = conn.execute("SELECT id FROM entities WHERE name='Mira'").fetchone()["id"]
        line = chat.add_child(conn, story, None, "user", "You forgot again, didn't you?", None)
        mood = {"label": "hurt", "shows": "hurt", "feels": "very hurt", "word": "low"}
        text = '*sighs* "No. I remembered. I just hoped you would, for once."'
        reply = chat.add_child(conn, story, line, "assistant", text, who, 0, {"mind": mood})
        key = os.environ.get(a.api_key_env) if a.api_key_env else None
        llm = LLM()
        llm.on_usage = functools.partial(usage.record, conn)
        try:
            at = time.monotonic()
            first = await speech.render(conn, llm, reply, get_key=lambda _: key)
            took = time.monotonic() - at
            at = time.monotonic()
            again = await speech.render(conn, llm, reply, get_key=lambda _: key)
            replay = time.monotonic() - at
        finally:
            await llm.aclose()
        path = media.find(conn, first["media"])
        size = path.stat().st_size
        print(f"cue: {first['cue']}")
        print(f"spoke {first['chars']} chars as {first['voice']}: {size} bytes in {took:.2f} s")
        print(f"replay cached={again['cached']} in {replay * 1000:.0f} ms")
        used = conn.execute("SELECT role, prompt_tokens FROM usage_log").fetchall()
        print(f"usage rows: {[tuple(r) for r in used]}")
        if a.keep:
            Path(a.keep).write_bytes(path.read_bytes())
        ok = not first["cached"] and again["cached"] and size > 1000 and len(used) == 1
        print("PASS" if ok else "FAIL")
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())
