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


def _head_re(name: str, bare: bool = True) -> re.Pattern:
    """A header line's start, in any dress: "Mira thinks:", "**Mira thinks**:", "> mira wants —",
    and (bare=True) the name-less "thinks:"."""
    who = "|".join(re.escape(n) for n in dict.fromkeys([name, *name.split()[:1]]) if n)
    named = rf"(?:(?:{who})\s+)" if who else ""
    return re.compile(
        rf"^[\s*_>]*{named}{'?' if bare else ''}(thinks|wants)[\s*_]*(?::|—|–)[\s*_]*", re.I
    )


def heads(name: str) -> tuple[str, ...]:
    """The plain forms a header line may start with, lower-cased: "mira thinks:", "thinks:"..."""
    who = [n.lower() for n in dict.fromkeys([name, *name.split()[:1]]) if n]
    return tuple(f"{n} {w}:" for n in who for w in WORDS) + tuple(f"{w}:" for w in WORDS)


def is_head(line: str, name: str, bare: bool = True) -> bool:
    return _head_re(name, bare).match(line) is not None


def _could_be_head(line: str, name: str) -> bool:
    """Is this unfinished line still a possible start of a header line?"""
    cut = re.sub(r"[*_>]", "", line).lstrip().lower()
    return any(f"{h[:-1]}{t}".startswith(cut) for h in heads(name) for t in (":", "—", "–"))


def split(text: str, name: str, tags: tuple[str, str]) -> tuple[str, list[str]]:
    """Text without its header lines and stray tags, and the header lines it had. Lines that
    name the character go wherever they are; the name-less "Wants: ..." only in the header
    block at the start or end of the text."""
    for tag in tags:
        text = text.replace(tag, "")
    lines = text.split("\n")
    drop = {i for i, ln in enumerate(lines) if is_head(ln, name, bare=False)}
    for order in (range(len(lines)), range(len(lines) - 1, -1, -1)):
        for i in order:
            if not lines[i].strip():
                continue
            if not is_head(lines[i], name):
                break
            drop.add(i)
    kept = [ln for i, ln in enumerate(lines) if i not in drop]
    found = [lines[i].strip() for i in sorted(drop)]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip(), found


def parse(lines: list[str], name: str) -> dict | None:
    """{"thinks", "wants"} from header lines (the first of each wins, clipped to its cap), or
    None when there is neither."""
    got: dict[str, str] = {}
    for line in lines:
        m = _head_re(name).match(line)
        if m is None:
            continue
        key = m.group(1).lower()
        value = " ".join(line[m.end() :].strip(' *_"“”').split()[: WORDS[key]])
        if value and key not in got:
            got[key] = value
    return {"thinks": got.get("thinks"), "wants": got.get("wants")} if got else None


def _words(text: str) -> list[str]:
    return re.findall(r"[\w']+", text.lower().replace("’", "'"))


def echoed(thinks: str | None, reply: str) -> str | None:
    """The first run of ECHO_WORDS words the reply repeats from the thought, or None."""
    a, b = _words(thinks or ""), _words(reply)
    said = {tuple(b[i : i + ECHO_WORDS]) for i in range(len(b) - ECHO_WORDS + 1)}
    for i in range(len(a) - ECHO_WORDS + 1):
        if tuple(a[i : i + ECHO_WORDS]) in said:
            return " ".join(a[i : i + ECHO_WORDS])
    return None


class Header:
    """Keeps a header the model wrote as plain words ("Mira thinks: …" lines, or a stray
    </think>) out of the start of the visible reply. What it caught is in `caught`.
    ponytail: only the start is held; a header written after the reply is removed from the
    saved text (`split`), but its words were already streamed."""

    def __init__(self, on: bool, name: str, tags: tuple[str, str]):
        self.on, self.name, self.tags, self.held, self.caught = on, name, tags, "", []

    def _maybe(self, line: str) -> bool:
        """Could this unfinished first line still turn out to be a header line or a tag?"""
        return (
            is_head(line, self.name)
            or _could_be_head(line, self.name)
            or any(t.startswith(line.strip()) for t in self.tags)
        )

    def feed(self, text: str) -> str:
        if not self.on:
            return text
        self.held += text
        while True:
            line, nl, rest = self.held.lstrip().partition("\n")
            if not nl:
                return "" if self._maybe(line) else self.flush()
            if is_head(line, self.name):
                self.caught.append(line.strip())
            elif line.strip() not in self.tags:
                return self.flush()
            self.held = rest

    def flush(self) -> str:
        self.on = False
        held, self.held = self.held.lstrip(), ""  # the reply's start: no blank line before it
        if is_head(held.strip(), self.name):  # the stream ended on a header line
            self.caught.append(held.strip())
            return ""
        return "" if held.strip() in self.tags else held
