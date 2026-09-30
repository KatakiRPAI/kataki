"""What a character does about the truth, decided by code (docs/specs/2026-09-29-minds.md slice 4;
note 22 §2 steps 0, 5, 7a and 11; note 13 §3 and §7).

A secret is something she keeps from someone, with a cover story she tells instead. When it is on
the table and someone it is kept from is listening, code picks the move (tell the truth, keep
quiet, hint, evade, deflect, lie with the cover, double down, confess) from what is at stake, how
close she is to the one asking, and how honest and candid she is; the reply only voices it. The
cover is the same every time, with her earlier claims on it recalled beside it. A reply that says
a secret's key words in front of the wrong person is caught here before it is shown, or covered.
A sincere out-of-character question is answered out of the fiction. Zero model calls.

ponytail: every threshold here is a design estimate (note 13 §3.3 has no fitted coefficients);
tune them on the probes (evals/probes.py `liar`, `leak`), not by feel.
"""

import json
import re
import sqlite3

from kataki import db

MOVES = (
    "truth", "soften", "hedge", "hint", "omit", "evade", "deflect", "exaggerate", "white_lie",
    "self_lie", "confess", "double_down",
)  # fmt: skip
MOTIVES = ("protect_self", "protect_other", "gain", "avoid_conflict", "kindness")
LIES = frozenset({"white_lie", "self_lie", "double_down"})


# --- secrets in a story -------------------------------------------------------------------------


def _words_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [w.strip() for w in value if isinstance(w, str) and w.strip()]


def seed(conn: sqlite3.Connection, story_id: int, cast: list[tuple[dict, int]]) -> None:
    """Each card's `data.mind.secrets` into the new story, as the user's own rows (no anchor):
    who it is kept from turns from library ids into this story's people. Inside the caller's
    transaction. A malformed entry is skipped, never fatal."""
    by_item = {item["id"]: e for item, e in cast}
    for item, owner in cast:
        mind = item["data"].get("mind")
        for s in (mind.get("secrets") if isinstance(mind, dict) else None) or []:
            if (
                not isinstance(s, dict)
                or not isinstance(s.get("text"), str)
                or not s["text"].strip()
            ):
                continue
            hide = s.get("conceal_from")
            ids = [by_item[i] for i in hide if i in by_item] if isinstance(hide, list) else []
            stakes = s.get("stakes", 0.5)
            stakes = min(1.0, max(0.0, float(stakes))) if isinstance(stakes, (int, float)) else 0.5
            cover = (
                s.get("cover") if isinstance(s.get("cover"), str) and s["cover"].strip() else None
            )
            conn.execute(
                "INSERT INTO secrets(story_id, owner_id, text, keys, topic, conceal_from, stakes,"
                " motive, cover, sincere, story_time) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                (
                    story_id,
                    owner,
                    s["text"].strip(),
                    json.dumps(_words_list(s.get("keys"))),
                    json.dumps(_words_list(s.get("topic"))),
                    json.dumps(ids if ids else "all"),
                    stakes,
                    s.get("motive") if s.get("motive") in MOTIVES else None,
                    cover and cover.strip(),
                    int(s.get("sincere") is True),
                ),
            )


def _json(text: str, default):
    try:
        return json.loads(text) if text else default
    except ValueError:
        return default


def held(conn: sqlite3.Connection, owner_id: int, path: list) -> list[dict]:
    """Her live secrets on this branch (written by the user, or anchored on it), a superseded one
    left out."""
    where, args = db.anchor_filter(set(), {m["id"] for m in path})
    rows = [
        dict(r)
        for r in conn.execute(
            f"SELECT * FROM secrets WHERE owner_id=? AND {where} ORDER BY id", [owner_id, *args]
        )
    ]
    gone = {r["supersedes_id"] for r in rows}
    out = []
    for r in rows:
        if r["id"] in gone:
            continue
        hide = _json(r["conceal_from"], "all")
        out.append(
            r
            | {
                "keys": _words_list(_json(r["keys"], [])),
                "topic": _words_list(_json(r["topic"], [])),
                "conceal_from": hide if isinstance(hide, list) else "all",
                "sincere": bool(r["sincere"]),
            }
        )
    return out


# --- is it on the table? ------------------------------------------------------------------------

STOP = frozenset(
    "the and but for not with you your what who whom whose when where why how did does was were are"
    " has have had about that this they them then than there here from into will would could"
    " should can him her his she its our out any all tell told said say know remember just very"
    " really been some more much like well back only also even over it's that's mine yours".split()
)


def _stem(w: str) -> str:
    w = w.removesuffix("'s").removesuffix("’s")
    return w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w


def words(text: str) -> set[str]:
    """Content words, lower-case, a possessive or plural s taken off: what a topic is made of."""
    found = re.findall(r"[a-z][a-z'’]*", (text or "").lower())
    return {_stem(w) for w in found if len(w) >= 3 and w not in STOP} - STOP


def topic(sec: dict) -> set[str]:
    """What puts a secret on the table: its topic words, its keys, and the words of its cover."""
    return words(" ".join([*sec.get("topic", []), *sec.get("keys", []), sec.get("cover") or ""]))


def topical(sec: dict, text: str) -> bool:
    """ponytail: words only; add the built-in embedder when the probes show rewordings missed."""
    return bool(topic(sec) & words(text))


QUESTION = re.compile(
    r"^\W*(who|whose|what|why|where|when|how|did|do|does|is|are|was|were|can|could|will|would"
    r"|tell me|say)\b",
    re.IGNORECASE,
)
ACCUSE = re.compile(  # ponytail: English phrases; the side call could label it later
    r"\b(liar|lying|lie to me|you lied|not true|admit it|i know (?:you|it|that|what)|saw you"
    r"|told me|don'?t believe|come clean|stop pretending|the truth)\b",
    re.IGNORECASE,
)


def question(text: str) -> bool:
    return "?" in text or bool(QUESTION.search(text))
