"""What every model call used (docs/specs/2026-09-29-minds.md §4): one row per call, in both
products. On the desktop it answers "what did this story cost me?"; online the same numbers bill.
"""

import json
import sqlite3
import uuid

from kataki import knobs, roles
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


def spend(conn: sqlite3.Connection, story_id: int, prices: dict) -> dict:
    """What a story's calls cost, by role and by day (GET /stories/{id}/spend). A row recorded
    before any price was set is priced at today's table; one still unpriced is counted apart."""
    out = {"calls": 0, "cost": 0.0, "unpriced": 0, "estimated": 0, "by_role": {}, "by_day": []}
    days: dict[str, dict] = {}
    for r in conn.execute("SELECT * FROM usage_log WHERE story_id=? ORDER BY id", (story_id,)):
        used = dict(r)
        used["prompt_tokens_details"] = {"cached_tokens": r["cached_tokens"]}
        spent = r["cost"] if r["cost"] is not None else cost(prices, r["model"], r["role"], used)
        role = out["by_role"].setdefault(
            r["role"],
            {"calls": 0, "cost": 0.0, "prompt_tokens": 0, "cached_tokens": 0,
             "completion_tokens": 0},
        )  # fmt: skip
        day = days.setdefault(r["at"][:10], {"day": r["at"][:10], "calls": 0, "cost": 0.0})
        for part in (out, role, day):
            part["calls"] += 1
            part["cost"] += spent or 0
        for key in ("prompt_tokens", "cached_tokens", "completion_tokens"):
            role[key] += r[key]
        out["unpriced"] += spent is None
        out["estimated"] += bool(r["estimated"])
    out["by_day"] = sorted(days.values(), key=lambda d: d["day"])
    return out


# ponytail: call shapes per turn beside the reply, from note 21 §2 (Arch B): (role, calls a
# turn, tokens in, tokens out); replace with this library's own averages once it has them
READ = ("utility", 0.2, 2000, 300)  # a memory read every fifth turn
SIDE = ("utility", 1.0, 1000, 150)  # the side call after each reply
LEVELS = {
    "lite": [READ],
    "standard": [READ, SIDE, ("utility", 0.05, 3000, 600)],  # a diary call now and then
    "premium": [READ, SIDE, ("utility", 0.1, 3000, 600)],  # deep passes more often
}
REPLY = (4000, 300)  # ponytail: a reply's size before the story has one of its own


def per_turn(conn: sqlite3.Connection, story_id: int, prices: dict) -> dict:
    """What one turn costs at each mind level (the UI shows it beside the level), in dollars, or
    None for a level when a model it uses has no price. The reply is sized from this story."""
    last = conn.execute(
        "SELECT coalesce(actual_tokens, est_tokens), cached_tokens FROM context_log"
        " WHERE story_id=? ORDER BY id DESC LIMIT 1",
        (story_id,),
    ).fetchone()
    out = conn.execute(
        "SELECT avg(completion_tokens) FROM usage_log WHERE story_id=? AND role='rp'"
        " AND NOT estimated",
        (story_id,),
    ).fetchone()[0]
    reply = {
        "prompt_tokens": (last and last[0]) or REPLY[0],
        "prompt_tokens_details": {"cached_tokens": (last and last[1]) or 0},
        "completion_tokens": out or REPLY[1],
    }

    def priced(role: str, used: dict) -> float | None:
        ep = roles.resolve(conn, role, story_id, get_key=lambda _: None)
        return cost(prices, ep.model, role, used) if ep else None

    first = priced("rp", reply)
    got = {"level": knobs.setting(conn, "mind.level", "standard")}
    for level, calls in LEVELS.items():
        parts = [first] + [
            priced(role, {"prompt_tokens": i, "completion_tokens": o}) for role, _, i, o in calls
        ]
        weights = [1.0] + [n for _, n, _, _ in calls]
        ok = None not in parts
        got[level] = sum(w * p for w, p in zip(weights, parts, strict=True)) if ok else None
    return got
