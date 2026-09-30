"""What every model call used (docs/specs/2026-09-29-minds.md §4): one row per call, in both
products. On the desktop it answers "what did this story cost me?"; online the same numbers bill.
"""

import json
import sqlite3
import uuid

from kataki.llm import Endpoint

MILLION = 1_000_000


def table(conn: sqlite3.Connection) -> dict:
    """The library's own `prices` setting (the desktop's; online the host brings the service's)."""
    row = conn.execute("SELECT value FROM settings WHERE key='prices'").fetchone()
    return json.loads(row[0]) if row else {}


def cost(prices: dict, model: str, role: str, used: dict) -> float | None:
    """Dollars for one call, or None when its model has no usable price. `prices` is
    {model: {"input", "cached", "output"}} in $ per million tokens (cached defaults to input), or
    {model: {"char"}} in $ per million characters for speech (role `voice` counts characters
    in prompt_tokens). A malformed entry prices nothing: it never breaks a call."""
    try:
        p = prices.get(model)
        prompt = used.get("prompt_tokens") or 0
        if role == "voice":
            rates = [float(p["char"])]
            spent = prompt * rates[0]
        else:
            rates = [float(p["input"]), float(p.get("cached", p["input"])), float(p["output"])]
            cached = min(
                (used.get("prompt_tokens_details") or {}).get("cached_tokens") or 0, prompt
            )
            spent = (prompt - cached) * rates[0] + cached * rates[1]
            spent += (used.get("completion_tokens") or 0) * rates[2]
    except (AttributeError, KeyError, TypeError, ValueError):
        return None
    return spent / MILLION if min(rates) >= 0 else None


def record(conn: sqlite3.Connection, ep: Endpoint, usage: dict, prices: dict | None = None) -> dict:
    """One usage_log row for one model call, priced now; returns it as the host's meter gets it
    (§8.4). `prices` None: the library's own table."""
    # ponytail: llama.cpp reports cache hits in `timings.cache_n`, not here; context_log keeps
    # those for replies, and local calls cost nothing to bill
    row = {
        "story_id": ep.story_id,
        "role": ep.role or "other",
        "model": ep.model,
        "prompt_tokens": usage.get("prompt_tokens") or 0,
        "cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0,
        "completion_tokens": usage.get("completion_tokens") or 0,
        "cost": cost(table(conn) if prices is None else prices, ep.model, ep.role, usage),
        "estimated": bool(usage.get("estimated")),
        "usage_id": uuid.uuid4().hex,
    }
    with conn:
        conn.execute(
            "INSERT INTO usage_log(story_id, role, model, prompt_tokens, cached_tokens,"
            " completion_tokens, cost, estimated, usage_id) VALUES(:story_id, :role, :model,"
            " :prompt_tokens, :cached_tokens, :completion_tokens, :cost, :estimated, :usage_id)",
            row,
        )
    return row
