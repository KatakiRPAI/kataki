"""How a reply sounds (docs/specs/2026-09-29-minds.md slice 10; note 18 §6, §8).

A per-line cue decided by code from what she shows (tone, how strongly, a pause before she
speaks, how fast), with at most one non-verbal tag: her own `*sighs*` first, else the side
call's. Nothing here reaches a prompt, and nothing runs in the turn but `untag` and `cue`: the
audio is made only when the app asks for it.

ponytail: the pause and speed numbers are starting points (note 18 gives none); tune by ear.
"""

import hashlib
import json
import re
import sqlite3

from kataki import features, knobs, media, roles

TONES = ("neutral", "warm", "cheerful", "excited", "anxious", "sad", "hurt", "cold", "angry",
         "flat")  # fmt: skip
TAGS = ("laugh", "chuckle", "sigh", "gasp", "sniff", "groan", "hum")
SHOWN = {  # what she shows (inner.FEEL) -> how it sounds
    "calm": "neutral", "content": "warm", "fond": "warm", "relieved": "warm",
    "glad": "cheerful", "amused": "cheerful", "excited": "excited", "surprised": "excited",
    "anxious": "anxious", "afraid": "anxious", "ashamed": "anxious", "sad": "sad",
    "hurt": "hurt", "annoyed": "cold", "angry": "angry", "bored": "flat",
}  # fmt: skip
WORD = {"low": "sad", "on edge": "anxious", "buzzing": "cheerful", "in a good mood": "warm"}
PACE = {  # ponytail: tone -> (pause before speaking in ms, speed) at clear strength
    "neutral": (250, 1.0), "warm": (300, 1.0), "cheerful": (200, 1.05),
    "excited": (150, 1.1), "anxious": (200, 1.08), "sad": (700, 0.9), "hurt": (600, 0.92),
    "cold": (400, 0.97), "angry": (150, 1.06), "flat": (400, 0.95),
}  # fmt: skip
STRONG = {1: (0.75, 0.5), 2: (1.0, 1.0), 3: (1.25, 1.5)}  # strength -> (pause x, speed shift x)
SPEED = (0.5, 2.0)
VERBS = {  # a one-word action of hers that is a sound: *sighs*, *laughs softly*
    "laugh": "laugh", "laughs": "laugh", "giggles": "laugh", "chuckle": "chuckle",
    "chuckles": "chuckle", "snorts": "chuckle", "sigh": "sigh", "sighs": "sigh",
    "gasp": "gasp", "gasps": "gasp", "sniff": "sniff", "sniffs": "sniff", "sniffles": "sniff",
    "groan": "groan", "groans": "groan", "hum": "hum", "hums": "hum",
}  # fmt: skip
ACTION = re.compile(r"\*([^*\n]{1,60})\*|_([^_\n]{1,60})_")
TAG = re.compile(r"[\[<]\s*(" + "|".join(sorted(VERBS, key=len, reverse=True)) + r")\s*[\]>]",
                 re.I)  # fmt: skip


def on(conn: sqlite3.Connection, entity_id: int | None) -> bool:
    """Is this character voiced? The feature, a `voice` model, and `voice.on` (her own
    `data.voice.on` wins; off by default on every level, lite included)."""
    if entity_id is None or not features.enabled(conn, "mind.voice"):
        return False
    if roles.resolve(conn, "voice", get_key=lambda _: None) is None:
        return False
    mine = knobs.own(conn, entity_id).get("voice")
    choice = mine.get("on") if isinstance(mine, dict) else None
    if choice in (None, "inherit"):
        choice = knobs.setting(conn, "voice.on", False)
    return choice is True


def untag(text: str) -> tuple[str, list[str]]:
    """Speech tags the model wrote (`[laughs]`, `<sigh>`) out of the visible reply, kept as
    tags. Only the closed list: `[OOC]` and anything else stays."""
    tags = [VERBS[m.group(1).lower()] for m in TAG.finditer(text)]
    if not tags:
        return text, []
    kept = TAG.sub("", text)
    kept = "\n".join(re.sub(r"[ \t]{2,}", " ", line).strip() for line in kept.splitlines())
    return re.sub(r"\n{3,}", "\n\n", kept).strip(), tags


def acted(text: str) -> str | None:
    """The first sound her own actions make: `*sighs*`, `*laughs softly*` (four words at most)."""
    for m in ACTION.finditer(text or ""):
        words = (m.group(1) or m.group(2)).lower().split()
        if len(words) <= 4 and (hit := next((VERBS[w] for w in words if w in VERBS), None)):
            return hit
    return None


def _strength(mood: dict) -> int:
    feels = str(mood.get("feels") or "")
    return 3 if feels.startswith("very ") else 1 if feels.startswith("a little ") else 2


def _num(x, default: float) -> float:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else default


def cue(gen, text: str, own: dict | None = None) -> dict:
    """The cue for one reply (spec §8.3 slice 10) from its `gen` (the mood it was said with,
    `after.voice`, stripped `voice.tags`), its text and her `data.voice` (speed)."""
    gen = gen if isinstance(gen, dict) else {}
    mood = gen.get("mind") if isinstance(gen.get("mind"), dict) else {}
    tone, strength = "neutral", 1
    shows = mood.get("shows")
    if shows in SHOWN and shows != "calm":
        tone = SHOWN[shows]
        strength = _strength(mood) if shows == mood.get("label") else 1
    elif not mood.get("label") and mood.get("word") in WORD:  # a mood with no feeling behind it
        tone = WORD[mood["word"]]
    after = gen.get("after") if isinstance(gen.get("after"), dict) else {}
    side = after.get("voice") if isinstance(after.get("voice"), dict) else {}
    by = "code"
    if side.get("tone") in TONES:
        tone, by = side["tone"], "side"
    kept = (gen.get("voice") or {}).get("tags") if isinstance(gen.get("voice"), dict) else None
    tag = acted(text) or next((t for t in kept or [] if t in TAGS), None)
    if tag is None and side.get("tag") in TAGS:
        tag, by = side["tag"], "side"
    pause, speed = PACE[tone]
    pause_x, shift_x = STRONG[strength]
    mine = _num((own or {}).get("speed"), 1.0) if isinstance(own, dict) else 1.0
    speed = min(max((1 + (speed - 1) * shift_x) * mine, SPEED[0]), SPEED[1])
    return {
        "tone": tone,
        "intensity": strength,
        "pause_ms": round(pause * pause_x),
        "speed": round(speed, 3),
        "tags": [tag] if tag else [],
        "by": by,
    }


# --- what is said, and the cache (spec §8.3 slice 10) ---------------------------------------

QUOTE = re.compile(r'"([^"\n]+)"|\u201c([^\u201d\n]+)\u201d')
SOUND = {  # a tag for a voice that has none (Kokoro): note 18 §6, degrade to text
    "laugh": "Ha!", "chuckle": "Heh.", "sigh": "Hah...", "gasp": "Oh!", "sniff": "",
    "groan": "Ugh.", "hum": "Hmm.",
}  # fmt: skip
TONE_WORDS = {
    "neutral": "evenly", "warm": "warmly", "cheerful": "brightly", "excited": "excitedly",
    "anxious": "nervously", "sad": "sadly, quietly", "hurt": "quietly, a little hurt",
    "cold": "coolly", "angry": "angrily", "flat": "flatly, without interest",
}  # fmt: skip
HOW_MUCH = {1: ", only slightly", 2: "", 3: ", strongly"}
DEFAULT_VOICE = "af_heart"  # Kokoro's; a role or a character names another
KEEP = 4  # renders kept per reply (another voice, an edited line)


def _sound(tag: str, mode: str) -> str:
    return {"brackets": f"[{tag}]", "angle": f"<{tag}>"}.get(mode, SOUND.get(tag, ""))


def speakable(text: str, cue: dict, mode: str = "text") -> str:
    """What she actually says: the quoted speech of prose (narration is not her voice), else
    the whole reply without actions; the cue's tag rendered for the engine (`mode`: text,
    brackets, angle) where she made the sound, or first. "" when there is nothing to say."""
    text, _ = untag(text or "")
    tag = (cue.get("tags") or [None])[0]
    token = _sound(tag, mode) if tag else ""
    placed = False
    quotes = [a or b for a, b in QUOTE.findall(text)]
    if quotes:
        said = " ".join(q.strip() for q in quotes)
    else:

        def act(m: re.Match) -> str:
            nonlocal placed
            if token and not placed and acted(m.group(0)) == tag:
                placed = True
                return f" {token} "
            return " "

        said = ACTION.sub(act, text)
    bare = " ".join(said.replace(token, " ").split()) if token else " ".join(said.split())
    if not bare:
        return ""
    if token and not placed:
        said = f"{token} {said}"
    return " ".join(said.split())


def instruct(cue: dict) -> str:
    """The tone as a sentence, for speech models that follow instructions (gpt-4o-mini-tts)."""
    return f"Speak {TONE_WORDS[cue['tone']]}{HOW_MUCH[cue['intensity']]}."


class Refused(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


async def render(conn: sqlite3.Connection, llm, message_id: int, get_key=roles.get_key) -> dict:
    """A reply's audio: from the cache when this line in this voice was made before (no call,
    no cost), else one call to the `voice` model, saved as media. Raises Refused."""
    m = conn.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
    if m is None or m["role"] != "assistant" or m["speaker_id"] is None:
        raise Refused(404, "Only a character's reply has a voice.")
    if not on(conn, m["speaker_id"]):
        raise Refused(409, "Voice is off for this character, or no voice model is set.")
    ep = roles.resolve(conn, "voice", m["story_id"], get_key)
    own = knobs.own(conn, m["speaker_id"]).get("voice")
    own = own if isinstance(own, dict) else {}
    gen = json.loads(m["gen"] or "{}")
    got = cue(gen, m["text"], own)
    said = speakable(m["text"], got, ep.params.get("tags", "text"))
    if not said:
        raise Refused(422, "This reply has nothing to say out loud.")
    name = str(own.get("name") or ep.params.get("voice") or DEFAULT_VOICE)
    fmt = ep.params.get("format", "mp3")
    told = instruct(got) if ep.params.get("instructions") else None
    key = hashlib.sha256(
        json.dumps([said, name, got["speed"], told, fmt, ep.model, ep.base_url]).encode()
    ).hexdigest()[:32]
    kept = gen.get("voice") if isinstance(gen.get("voice"), dict) else {}
    audio = kept.get("audio") if isinstance(kept.get("audio"), dict) else {}
    out = {"cue": got, "voice": name, "chars": len(said)}
    if key in audio and media.find(conn, audio[key]):
        return {"media": audio[key], "url": f"/media/{audio[key]}", "cached": True, **out}
    data = await llm.speech(ep, said, name, got["speed"], fmt, told)
    file = media.save(conn, data, media.sniff_audio(data))
    audio = {**dict(list(audio.items())[-(KEEP - 1) :]), key: file}
    with conn:
        conn.execute(
            "UPDATE messages SET gen=json_set(COALESCE(gen, '{}'), '$.voice.audio', json(?))"
            " WHERE id=?",
            (json.dumps(audio), message_id),
        )
    return {"media": file, "url": f"/media/{file}", "cached": False, **out}
