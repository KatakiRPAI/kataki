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

from kataki import db, inner

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


# --- the move (note 13 §3.3-3.6; note 22 §2 step 7a, C7) ---------------------------------------

LIE_AT = 1.0  # ponytail: (1 - honesty) + stakes * (1 - closeness / 2) from here she lies
CANDID = 0.7  # ponytail: candor from which she refuses plainly rather than change the subject
LITTLE = 0.3  # ponytail: stakes below this are little to lose


def decide(sec: dict, prof: dict, close: float, probed: bool, caught: str | None) -> str:
    """What she does about a secret that is on the table, from what is at stake, how close she is
    to the one asking (0-1), how honest and candid she is, and whether she is caught out. Softer
    moves come before a falsehood (note 13 §3.3); a lie needs a cover story to tell."""
    honest, candid = inner.mean(prof, "honesty") / 100, inner.mean(prof, "candor") / 100
    stakes = sec["stakes"]
    if sec.get("sincere"):
        return "truth"  # as she believes it: the cover is her truth
    if caught:  # guilt grows with closeness; the stakes hold her back (note 13 §3.5)
        return "confess" if 0.6 * honest + 0.4 * close > stakes else "double_down"
    if not probed:
        return "hint" if candid >= CANDID and stakes < 0.5 else "omit"
    if honest >= 0.5 and stakes < LITTLE:
        return "truth"
    if sec.get("cover") and (1 - honest) + stakes * (1 - close / 2) >= LIE_AT:
        return "white_lie" if sec.get("motive") in ("protect_other", "kindness") else "self_lie"
    return "evade" if candid >= CANDID else "deflect"


FACE = re.compile(  # an opinion asked on the user's own work: a face threat (note 13 §3.6)
    r"(\b(what do you think|do you like|how do you like|your (honest )?opinion|be honest"
    r"|thoughts on)\b.*\b(my|i (wrote|made|cooked|drew|painted|sang|built))\b"
    r"|\b(my|i (wrote|made|cooked|drew|painted|sang|built))\b.*\b(what do you think|do you like"
    r"|be honest|your (honest )?opinion)\b)",
    re.IGNORECASE,
)


def face_move(prof: dict, close: float) -> str:
    """How she answers a request for her opinion on their work: plainly (candid), kindly first
    (warm or close), with a kind lie (warm and not honest), or carefully."""
    candid, warm = inner.mean(prof, "candor") / 100, inner.mean(prof, "warmth") / 100
    if candid >= CANDID:
        return "truth"
    if warm >= 0.6 and inner.mean(prof, "honesty") < 50:
        return "white_lie"
    return "soften" if warm >= 0.6 or close >= 0.5 else "hedge"


# --- the directive: the decision in words (note 22 §4 row 1; note 13 §4) -----------------------

MOTIVE = {
    "protect_self": "to protect yourself",
    "protect_other": "to protect someone else",
    "gain": "because keeping it gains you something",
    "avoid_conflict": "to avoid a fight",
    "kindness": "to spare their feelings",
}
CAUGHT = {
    "accused": "{user} accuses you of lying about it.",
    "doubted": "{user} does not believe what you said about it.",
    "pressed": "{user} keeps pressing you about it.",
}
FACE_SAY = {
    "truth": "Say plainly what you really think of it, the problem first, without cushioning.",
    "soften": "Start with something true and kind about it, then say what is wrong.",
    "hedge": "Say what you think of it carefully, with qualifiers.",
    "white_lie": "Tell {user} you like it, to spare their feelings.",
}


def _stake(x: float) -> str:
    return "a great deal" if x >= 0.7 else "something that matters" if x >= 0.4 else "little"


def directive(sec: dict | None, move: str, user: str, said: list[str], caught: str | None) -> str:
    """The decision for [Directive], in words: what she keeps from them and why (only when she
    acts on it), then the move as a positive instruction. `sec` None: an opinion on their work."""
    if sec is None:
        return FACE_SAY.get(move, FACE_SAY["hedge"]).format(user=user)
    if sec.get("sincere"):
        return f'You sincerely believe this: "{sec["cover"]}" If {user} asks, you say so.'
    if move == "omit":
        return f"You have a secret about this that you keep from {user}; talk about other things."
    why = MOTIVE.get(sec.get("motive"), "")
    out = [
        f"You are keeping this from {user}: {sec['text']}"
        + (f" You keep it {why}." if why else "")
        + f" If it came out you would lose {_stake(sec['stakes'])}."
    ]
    if caught:
        out.append(CAUGHT[caught].format(user=user))
    cover = sec.get("cover")
    if move in ("white_lie", "self_lie"):
        out.append(f'If {user} asks about it, you say: "{cover}" Keep to that story.')
    elif move == "double_down":
        out.append(
            f'Stick to your story ("{cover}"): add no new details, and show you are hurt or'
            " annoyed to be doubted."
            if cover
            else "Keep to what you have said and give nothing more away."
        )
    else:
        out.append(
            {
                "truth": f"You decide to tell {user} the truth about it, in your own way.",
                "confess": "You can't keep it up: admit the truth now, in your own way.",
                "hint": "Let a small hint of it show, without saying it outright.",
                "evade": f"If {user} asks about it, you say plainly that you won't talk about it.",
                "deflect": f"If {user} asks about it, you turn the talk to something else.",
                "soften": f"Tell {user} gently, softening the hard part.",
                "hedge": "Speak about it only vaguely, with qualifiers.",
            }.get(move, "")
        )
    if said and move in LIES:
        quoted = "; ".join(f'"{s}"' for s in said)
        out.append(f"You have already said: {quoted}. Add nothing that contradicts it.")
    return " ".join(p for p in out if p)


def claims(conn: sqlite3.Connection, story_id: int, owner_id: int, sec: dict, path: list,
           n: int = 3) -> list[str]:  # fmt: skip
    """Her last `n` claims on this secret's topic that memory holds (live on this branch), oldest
    first: what she already said, so a lie does not contradict itself (note 13 §3.4)."""
    live = db.live_runs(conn, story_id, path[-1]["id"]) if path else set()
    where, args = db.live_filter(live)
    rows = conn.execute(
        "SELECT detail FROM memories WHERE story_id=? AND kind='claim' AND asserted_by=?"
        f" AND hidden=0 AND {where} ORDER BY story_time, id",
        [story_id, owner_id, *args],
    )
    return [r["detail"] for r in rows if topical(sec, r["detail"])][-n:]
