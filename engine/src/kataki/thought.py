"""The character's inner voice (docs/specs/2026-09-29-minds.md slice 3; note 22 §2 step 10):
two private lines the reply model writes before the reply, in the same stream, inside the
think tags, so what Peek shows is what the reply was written from.

    <think>
    Mira thinks: I promised myself I wouldn't ask. Don't look at the ring.
    Mira wants: him to drop it
    </think>

The stream splitter (llm.ThinkSplitter) already sends a tagged header down the thought
channel; this module asks for it, reads it, keeps a header the model wrote as plain words out
of the visible reply, and checks the reply does not say the thought aloud.
"""

import re
import sqlite3

from kataki import features, knobs
from kataki.llm import Endpoint

WORDS = {"thinks": 25, "wants": 10}  # ponytail: note 22's caps; the model is told, code clips
ECHO_WORDS = 5  # ponytail: this many words of the thought in a row, in the reply, is an echo
ASK = (
    "First, before the reply, write {name}'s private thought in exactly this form:\n"
    "{open}\n{name} thinks: (in {name}'s own voice, at most 25 words)\n"
    "{name} wants: (from this moment, at most 10 words)\n{close}\n"
    "Then write the reply, which shows the thought only through what {name} says and does."
)
STRONGER = "Keep {name}'s thought private: never say it, or its words, aloud."


def mode(conn: sqlite3.Connection, ep: Endpoint, speaker_id: int | None) -> str | None:
    """How this reply gets its thought: "inline" (the header, standard and premium), "after"
    (a reasoning model thinking on its own: the side call writes an afterthought), or None
    (the narrator, lite, or `mind.thought` off)."""
    if speaker_id is None or not features.enabled(conn, "mind.thought"):
        return None
    if knobs.setting(conn, "mind.level", "standard") == "lite":
        return None
    return "after" if ep.thinks else "inline"


def ask(name: str, tags: tuple[str, str]) -> str:
    """The line appended to [Directive] that asks for the header."""
    return ASK.format(name=name, open=tags[0], close=tags[1])


def heads(name: str) -> tuple[str, ...]:
    """How a header line may start, lower-cased: "mira thinks:", "thinks:", ..."""
    who = [n.lower() for n in dict.fromkeys([name, *name.split()[:1]]) if n]
    return tuple(f"{n} {w}:" for n in who for w in WORDS) + tuple(f"{w}:" for w in WORDS)


def _bare(line: str) -> str:
    return line.lstrip(" \t*_>").lower()  # "**Mira thinks:**", "> Mira thinks:" count too


def is_head(line: str, name: str) -> bool:
    return _bare(line).startswith(heads(name))


def split(text: str, name: str, tags: tuple[str, str]) -> tuple[str, list[str]]:
    """Text without its header lines and stray tags, and the header lines it had."""
    for tag in tags:
        text = text.replace(tag, "")
    kept, found = [], []
    for line in text.split("\n"):
        (found if is_head(line, name) else kept).append(line)
    rest = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()
    return rest, [line.strip() for line in found]


def parse(lines: list[str], name: str) -> dict | None:
    """{"thinks", "wants"} from header lines (the first of each wins, clipped to its cap), or
    None when there is neither."""
    got: dict[str, str] = {}
    for line in lines:
        bare = line.lstrip(" \t*_>")
        head = next((h for h in heads(name) if bare.lower().startswith(h)), None)
        if head is None:
            continue
        key = "wants" if head.endswith("wants:") else "thinks"
        value = " ".join(bare[len(head) :].strip(' *_"“”').split()[: WORDS[key]])
        if value and key not in got:
            got[key] = value
    return {"thinks": got.get("thinks"), "wants": got.get("wants")} if got else None


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower().replace("’", "'"))


def echoed(thinks: str | None, reply: str) -> str | None:
    """The first run of ECHO_WORDS words the reply repeats from the thought, or None."""
    a, b = _words(thinks or ""), _words(reply)
    said = {tuple(b[i : i + ECHO_WORDS]) for i in range(len(b) - ECHO_WORDS + 1)}
    for i in range(len(a) - ECHO_WORDS + 1):
        if tuple(a[i : i + ECHO_WORDS]) in said:
            return " ".join(a[i : i + ECHO_WORDS])
    return None
