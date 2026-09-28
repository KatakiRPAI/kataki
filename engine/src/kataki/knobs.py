"""What Settings › Memory and thinking, and each character's own profile, ask of the engine.

A character's own choice (their library item's `data.fade` / `data.doubt`) wins over the
setting; "inherit" or nothing means the setting.
"""

import json
import sqlite3
from dataclasses import replace

from kataki import activation

FADE = {"fast": 0.7, "lifelike": activation.DECAY, "slow": 0.35, "never": 0.0}


def setting(conn: sqlite3.Connection, key: str, default):
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return json.loads(row["value"]) if row else default


def _own(conn: sqlite3.Connection, entity_id: int | None) -> dict:
    """The character's library profile, if this story's person came from one."""
    if entity_id is None:
        return {}
    row = conn.execute(
        "SELECT l.data FROM entities e JOIN lib_items l ON l.id=e.lib_item_id WHERE e.id=?",
        (entity_id,),
    ).fetchone()
    return json.loads(row["data"]) if row else {}


def decay(conn: sqlite3.Connection, entity_id: int | None) -> float:
    """How fast this character's memories fade: the d of the activation maths."""
    fade = _own(conn, entity_id).get("fade")
    if fade in (None, "inherit"):
        fade = setting(conn, "memory.fade", "lifelike")
    return FADE.get(fade, activation.DECAY)


def can_doubt(conn: sqlite3.Connection, entity_id: int | None) -> bool:
    own = _own(conn, entity_id).get("doubt")
    return bool(setting(conn, "memory.canDoubt", True) if own is None else own)


def hear_all(conn: sqlite3.Connection) -> bool:
    """"Everyone hears everything": nobody is away and nothing is a whisper. Thoughts stay."""
    return setting(conn, "memory.hearing", "real") == "all"


def thinking(conn: sqlite3.Connection, ep):
    """Thinking before replying: None switches it off, A lot switches it on, hard. A role's
    own thinking setting (Settings › Models) wins."""
    level = setting(conn, "memory.thinking", "some")
    params = dict(ep.params)
    if level == "none" and "thinking" not in params:
        params["thinking"] = "disabled"
    elif level == "lot" and "thinking" not in params:
        params["thinking"] = "enabled"
        params.setdefault("reasoning_effort", "high")
    return replace(ep, params=params) if params != ep.params else ep
