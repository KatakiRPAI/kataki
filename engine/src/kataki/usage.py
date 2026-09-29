"""What every model call used (docs/specs/2026-09-29-minds.md §4): one row per call, in both
products. On the desktop it answers "what did this story cost me?"; online the same numbers bill.
"""

import sqlite3

from kataki.llm import Endpoint


def record(conn: sqlite3.Connection, ep: Endpoint, usage: dict) -> None:
    # ponytail: llama.cpp reports cache hits in `timings.cache_n`, not here; context_log keeps
    # those for replies, and local calls cost nothing to bill
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
    with conn:
        conn.execute(
            "INSERT INTO usage_log(story_id, role, model, prompt_tokens, cached_tokens,"
            " completion_tokens) VALUES(?, ?, ?, ?, ?, ?)",
            (
                ep.story_id,
                ep.role or "other",
                ep.model,
                usage.get("prompt_tokens") or 0,
                cached,
                usage.get("completion_tokens") or 0,
            ),
        )
