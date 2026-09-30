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

from kataki import bonds, chat, db, inner

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


# --- the leak check (note 22 §2 step 11; note 13 §3.2 E) ---------------------------------------

END = re.compile(r"[.!?…]+[\"”’'*_)\]]*(?:\s+|$)|\n+")  # a sentence's end, closers and all
SURE_END = re.compile(r"[.!?…]+[\"”’'*_)\]]*\s+|\n+")  # ...that no later character can extend
SILENT = "…"  # what is left of a leak with no cover to put in its place


def _key(key: str) -> re.Pattern:
    body = r"\s+".join(re.escape(w) for w in key.split())
    return re.compile(rf"(?<!\w){body}(?:s|es)?(?!\w)", re.IGNORECASE)


def leak(text: str, keys: list[str]) -> str | None:
    """The first key the text says (whole words, any case, a plural too), or None."""
    return next((k for k in keys if _key(k).search(text)), None)


def _sentences(text: str) -> list[tuple[int, int]]:
    out, at = [], 0
    for m in END.finditer(text):
        if m.end() > at:
            out.append((at, m.end()))
            at = m.end()
    return out + ([(at, len(text))] if at < len(text) else [])


def _first(text: str, guards: list[tuple[list[str], str | None]]):
    """Where the first leaking sentence starts, its key and the cover to put there, or None."""
    for start, end in _sentences(text):
        for keys, cover in guards:
            if key := leak(text[start:end], keys):
                return start, key, cover
    return None


def _in_quotes(before: str, text: str, cover: str) -> str:
    """The cover in the reply's own quotes: closing an open one, or a pair if it uses them."""
    cover = cover.strip().strip('"“”')
    if before.count('"') % 2:
        return f'{cover}"'
    if before.count("“") > before.count("”"):
        return f"{cover}”"
    if "“" in text:
        return f"“{cover}”"
    return f'"{cover}"' if '"' in text else cover


def cover_up(before: str, text: str, cover: str | None) -> str:
    """What replaces a leak: the cover story, where the leaking sentence began."""
    return _in_quotes(before, text, cover) if cover else ("" if before.strip() else SILENT)


def scrub(text: str, guards: list[tuple[list[str], str | None]]) -> tuple[str, str | None]:
    """The text with its first leaking sentence replaced by the cover and the rest dropped (a
    reply that has started giving it away does not get to finish), and the key it said."""
    if (found := _first(text, guards)) is None:
        return text, None
    start, key, cover = found
    before = text[:start]
    return (before + cover_up(before, text, cover)).strip(), key


class Guard:
    """Holds a reply back a sentence at a time while a secret is on the table, so a sentence
    that says a key in front of the wrong person is caught before anyone sees it. `hit` is the
    key, `cover` what goes in its place, `shown` whether clean sentences went out before it.
    ponytail: whole sentences only; a key split across a sentence end is not seen."""

    def __init__(self, guards: list[tuple[list[str], str | None]]):
        self.guards = [(keys, cover) for keys, cover in guards if keys]
        self.held, self.hit, self.cover, self.shown, self.before = "", None, None, False, ""

    def _release(self, done: str) -> str:
        if found := _first(done, self.guards):
            start, self.hit, self.cover = found
            done = done[:start]
        self.shown = self.shown or bool(done.strip())
        self.before += done
        return done

    def feed(self, text: str) -> str:
        if self.hit:
            return ""
        if not self.guards:
            return text
        self.held += text
        cut = max((m.end() for m in SURE_END.finditer(self.held)), default=0)
        done, self.held = self.held[:cut], self.held[cut:]
        return self._release(done) if done else ""

    def flush(self) -> str:
        if self.hit or not self.guards:
            return ""
        done, self.held = self.held, ""
        return self._release(done)


# --- the gate and the decision, for one reply (note 22 §2 steps 5 and 7a) ----------------------

PRESSURE = 3  # ponytail: the third question on it in the asker's last six lines presses her
DOUBT = 0.5  # ponytail: a hearer's belief in her claim at or below this is doubt (extract.BELIEF)
RECENT = 3  # the pending line and the two before it put a secret on the table
TELLING = frozenset({"truth", "confess"})


def _close(conn, speaker_id: int, path: list, other: int | None) -> float:
    """How close she is to `other`, 0-1: where a pair starts, moved by her ledger (slice 2)."""
    moved = 0.0
    if other is not None:
        now = path[-1]["story_time"] if path else 0
        moved = bonds.standing(bonds.ledger(conn, speaker_id, path), other, now)["closeness"]
    return round(min(1.0, max(0.0, (bonds.START_CLOSENESS + moved) / 100)), 2)


def _told(path: list, speaker_id: int) -> dict[int, set[int]]:
    """Who each secret has been told to on this branch: those who heard her truth or confession."""
    out: dict[int, set[int]] = {}
    for m in path:
        if m["role"] == "assistant" and m["speaker_id"] == speaker_id and m["gen"]:
            said = json.loads(m["gen"]).get("honest") or {}
            if said.get("secret") and said.get("told"):
                out.setdefault(said["secret"], set()).update(said["told"])
    return out


def _doubted(conn, story_id: int, speaker_id: int, sec: dict, path: list, who: int) -> bool:
    """Does `who` doubt what she has claimed on this topic (their live belief in it, which
    extraction lowers when a contradiction is believed)?"""
    live = db.live_runs(conn, story_id, path[-1]["id"]) if path else set()
    where, args = db.live_filter(live, "k.run_id")
    rows = conn.execute(
        "SELECT m.id, m.detail, k.belief FROM knowledge k JOIN memories m ON m.id=k.memory_id"
        f" WHERE k.knower_id=? AND m.kind='claim' AND m.asserted_by=? AND {where}"
        " ORDER BY k.id",
        [who, speaker_id, *args],
    )
    latest = {r["id"]: r for r in rows}  # the latest live row per claim is its belief now
    return any(r["belief"] <= DOUBT for r in latest.values() if topical(sec, r["detail"]))


def read(conn: sqlite3.Connection, story_id: int, speaker_id: int, path: list, prof: dict):
    """What she does about the truth in this reply, or None when nothing is at stake:
    {"gate": codes, "hot": a secret is on the table, "guards": [(keys, cover)] for every secret
    kept from someone here, "directive": words for [Directive], "honest": gen.honest}."""
    if not path:
        return None
    scene_id = chat.scene_of(conn, story_id, path)
    here = [e["id"] for e in chat.present_entities(conn, scene_id, path) if e["id"] != speaker_id]
    persona = conn.execute(
        "SELECT persona_entity_id FROM stories WHERE id=?", (story_id,)
    ).fetchone()[0]
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)))
    heard = [m for m in path if m["id"] in chat.heard_by(conn, path, speaker_id)]
    last = heard[-1] if heard else None
    pending = last if last is not None and last["role"] == "user" else None
    asker = (pending["speaker_id"] if pending else None) or persona
    told = _told(path, speaker_id)
    guards, hot = [], []
    for sec in held(conn, speaker_id, path):
        hide = (
            here if sec["conceal_from"] == "all" else [i for i in sec["conceal_from"] if i in here]
        )
        hide = [i for i in hide if i not in told.get(sec["id"], set())]
        if not hide:
            continue  # nobody here it is kept from: nothing to decide, nothing to guard
        if not sec["sincere"]:
            guards.append((sec["keys"], sec["cover"]))
        if any(topical(sec, m["text"]) for m in heard[-RECENT:]):
            hot.append((sec, hide))
    close = _close(conn, speaker_id, path, asker)
    inputs = {"closeness": close, "honesty": inner.mean(prof, "honesty"),
              "candor": inner.mean(prof, "candor")}  # fmt: skip
    user = names.get(asker) or "them"
    gate, honest, words_ = [], None, ""
    if hot:
        sec, hide = max(hot, key=lambda h: h[0]["stakes"])
        gate = ["secret_topical"]
        probed = pending is not None and question(pending["text"])
        if probed:
            gate.append("probe")
        asked = [  # the asker's recent questions while it was on the table
            i for i, m in enumerate(heard)
            if m["role"] == "user" and m["speaker_id"] == asker and question(m["text"])
            and any(topical(sec, x["text"]) for x in heard[max(0, i - RECENT + 1) : i + 1])
        ]  # fmt: skip
        mine = [i for i, m in enumerate(heard) if m["role"] == "user" and m["speaker_id"] == asker]
        caught = None
        if pending is not None and ACCUSE.search(pending["text"]):
            caught = "accused"
        elif asker is not None and _doubted(conn, story_id, speaker_id, sec, path, asker):
            caught = "doubted"
        elif probed and len([i for i in asked if i in mine[-6:]]) >= PRESSURE:
            caught = "pressed"
        move = decide(sec, prof, close, probed or bool(caught), caught)
        said = claims(conn, story_id, speaker_id, sec, path) if move in LIES else []
        words_ = directive(sec, move, user, said, caught)
        honest = {
            "secret": sec["id"], "move": move, "why": "probe" if probed else "topical",
            "caught": caught, "to": asker, "inputs": {"stakes": sec["stakes"], **inputs},
            "told": sorted(hide) if move in TELLING and not sec["sincere"] else [],
        }  # fmt: skip
    elif pending is not None and FACE.search(pending["text"]):
        move = face_move(prof, close)
        words_ = directive(None, move, user, [], None)
        honest = {"secret": None, "move": move, "why": "face", "caught": None, "to": asker,
                  "inputs": {"stakes": None, **inputs}, "told": []}  # fmt: skip
    if not guards and honest is None:
        return None
    return {"gate": gate, "hot": bool(hot), "guards": guards, "directive": words_,
            "honest": honest}  # fmt: skip
