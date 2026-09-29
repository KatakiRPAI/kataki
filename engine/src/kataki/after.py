"""One small labelling call after the reply (docs/specs/2026-09-29-minds.md §3; note 22 §2
step 12): what the speaker felt, what was done to them and by whom, the stance they took,
whether they gave way, and the face they said it with. It replaces the face call, so a
character with sprites costs no extra call. Closed lists only: the model labels, code decides
what the labels do.

Standard and premium only; lite reads all of it by rules. Anything that goes wrong costs only
this call: the turn keeps what the rules read (`gen.after = "skipped"`).
"""

import sqlite3

from kataki import bonds, features, images, inner, knobs

PROMPT = """\
You label one exchange from a roleplay for the app that keeps the character's mind. Use only \
the values the schema allows.
- felt: what the character feels right after their reply. intensity: 1 a little, 2 clearly, \
3 very. about: the handle of the person it is about, or null. cause: at most 12 words.
- events: at most 3 things another person did to the character in this exchange: that \
person's handle (target), what it was (type) and how much (intensity 1-3). An apology is \
apology_sincere only if it owns what was done; otherwise apology_hollow. Leave it empty when \
nothing happened.
- position: a stance the character took or kept in the reply (at most 12 words; firm 1-3), \
or null.
- yielded: true only if the character gave in on a position, or to what someone pushed for.
- face: the character's facial expression while saying the reply."""
FELT = {1: 0.3, 2: 0.6, 3: 0.9}  # ponytail: intensity words -> the affect core's 0-1


def wanted(conn: sqlite3.Connection) -> bool:
    """Standard and premium ask the side call; lite reads everything by rules (spec §3)."""
    level = knobs.setting(conn, "mind.level", "standard")
    return features.enabled(conn, "mind.bonds") and level != "lite"


def schema(handles: list[str]) -> dict:
    """The labels, every list closed: feelings, events, faces, and only the people here."""
    level = {"type": "integer", "enum": [1, 2, 3]}
    return {
        "type": "object",
        "properties": {
            "felt": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "enum": list(inner.FEEL)},
                    "intensity": level,
                    "about": {"type": ["string", "null"], "enum": [*handles, None]},
                    "cause": {"type": "string"},
                },
                "required": ["label", "intensity", "about", "cause"],
                "additionalProperties": False,
            },
            "events": {
                "type": "array",
                "maxItems": 3 if handles else 0,
                "items": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "enum": handles or ["none"]},
                        "type": {"type": "string", "enum": list(bonds.EVENTS)},
                        "intensity": level,
                    },
                    "required": ["target", "type", "intensity"],
                    "additionalProperties": False,
                },
            },
            "position": {
                "anyOf": [
                    {"type": "null"},
                    {
                        "type": "object",
                        "properties": {"text": {"type": "string"}, "firm": level},
                        "required": ["text", "firm"],
                        "additionalProperties": False,
                    },
                ]
            },
            "yielded": {"type": "boolean"},
            "face": {"type": "string", "enum": list(images.EXPRESSIONS)},
        },
        "required": ["felt", "events", "position", "yielded", "face"],
        "additionalProperties": False,
    }


def _level(x) -> bool:
    return type(x) is int and 1 <= x <= 3


def _word(x, allowed) -> bool:
    return isinstance(x, str) and x in allowed


def read(data: dict, handles: list[str]) -> dict:
    """Validate the labels. Unusable as a whole (no feeling from the list, no face) raises
    ValueError, so the model is asked once more; a bad event is only dropped."""
    felt = data.get("felt")
    if not isinstance(felt, dict) or not _word(felt.get("label"), inner.FEEL):
        raise ValueError(f"felt.label must be one of {', '.join(inner.FEEL)}")
    if not _level(felt.get("intensity")):
        raise ValueError("felt.intensity must be 1, 2 or 3")
    if not _word(data.get("face"), images.EXPRESSIONS):
        raise ValueError(f"face must be one of {', '.join(images.EXPRESSIONS)}")
    events = data.get("events") if isinstance(data.get("events"), list) else []
    pos = data.get("position")
    text = pos.get("text") if isinstance(pos, dict) else None
    return {
        "felt": {
            "label": felt["label"],
            "intensity": felt["intensity"],
            "about": felt.get("about") if _word(felt.get("about"), handles) else None,
            "cause": str(felt.get("cause") or "")[:80],
        },
        "events": [
            {"target": e["target"], "type": e["type"], "intensity": e["intensity"]}
            for e in events[:3]
            if isinstance(e, dict)
            and _word(e.get("target"), handles)
            and _word(e.get("type"), bonds.EVENTS)
            and _level(e.get("intensity"))
        ],
        "position": (
            {"text": text.strip()[:80], "firm": pos["firm"]}
            if isinstance(text, str) and text.strip() and _level(pos.get("firm"))
            else None
        ),
        "yielded": data.get("yielded") is True,
        "face": data["face"],
    }
