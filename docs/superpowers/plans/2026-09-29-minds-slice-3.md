# Minds Slice 3 ("She thinks before she speaks") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On the standard and premium levels, a character writes a private two-line thought before every reply, in the same stream (`Mira thinks: Don't look at the ring.` / `Mira wants: him to drop it`), so Peek and the Mind graph show what the reply was actually written from. The thought never reaches the visible reply, the history or the cached prefix, whatever the model does with the instruction; a reply that says its thought aloud is caught in its opening and written again once. Zero extra calls. A reasoning model that thinks on its own gets an "afterthought" from the existing side call instead.

**Architecture:** A new pure module `thought.py` asks for the header (one instruction appended to `[Directive]`, using the endpoint's own think tags), reads it (`split`, `parse`), keeps a header the model wrote as plain words out of the start of the stream (`Header`, a filter like `turns._Prefix`), and finds echoes (`echoed`). The existing `llm.ThinkSplitter` already routes a tagged header to the `thought` channel, so `turns._generate` only has to take the header lines out of what it saves as `gen.reasoning`, store them as `gen.thought`, clean the saved text, and send `done.thought`. The echo check rides on slice 2b's `_Opener` hold and its single retake. The side call (`after.py`) gains an optional `thought` field used only for reasoning models. Peek (`people[].thought`) and the Mind graph (Thought and Intent nodes) read `gen.thought`. Gated by the `mind.thought` feature (stage alpha). No migration.

**Tech Stack:** Python 3.12, stdlib `re`/`json`/`statistics`, pytest with the scripted `FakeBackend` in `engine/tests/conftest.py`.

**Spec:** `docs/specs/2026-09-29-minds.md` §3 (levels), §7 (slice 3 row), §8.3 (the slice-3 contract, already written by this plan's author: Task 1 commits it), §9 (gates: added time to first word < 2 s). Design source: note 22 (`docs/research/research_notes/Human like minds for Kataki/22_unified_architecture.md`) §2 step 10–11 and the "Inline thought header" paragraph, §4 (the header instruction goes in `[Directive]`), §5 (level table), §6 C13/C19, §7 slice 3 row, §8 P8; `10_inner_thought_subconscious.md` §4 (echo, leak checks) and §7 (O1); `docs/specs/2026-09-23-mind-graph.md` §1 (Goals/Intent nodes), §4.4 and §7.1 (the 2 s gate). **Prerequisite:** slices 2a and 2b are landed (they are, on `main`).

**Decisions this plan makes (and why):**

- The thought lives in `gen.thought = {"thinks", "wants", "from"}`, not `gen.mind.thought`: `gen.mind` is slice 1's mood object, `done.mood` is read from it and the side call overwrites `$.mind` wholesale. `from` is `"before"` (it conditioned the reply) or `"after"` (written late, or a side-call afterthought).
- SSE stays as it is: the tagged header streams as ordinary `thought` events (the UI's "thinking" state is true for it), and `done.thought` carries the parsed thought. No new event type.
- Premium uses the inline header too until slice 4 builds the pre-reply side call (note 22 §5 wants premium's thought from that call).
- The echo check holds only the opening (the `_Opener` hold, ≤160 chars / first sentence) and shares slice 2b's one retake; an echo later in the reply is recorded (`trace.echo.resampled: false`), not retaken. Holding the opening costs first-word time; the latency probe measures it, with a one-line fallback (`ponytail:` on `_Opener.watch`).
- `gen.trace.echo` is a new key, so slice 2b's `gen.trace.check` contract (`{"hit", "resampled"}`) is untouched.

## Global Constraints

- Commands run from `engine/`: tests `uv run pytest -q`, lint `uv run ruff check . && uv run ruff format --check .`; the repo gate is `corepack pnpm check` from the root.
- No new dependencies. No migration.
- Zero extra model calls for the thought. At most one retake per turn, shared with the opener check (never two). Lite: no thought, no echo check.
- The thought never enters `messages.text`, history, the cached system block or `gen.reasoning`. The header instruction lives in `[Directive]` (volatile tail) through `context.build(directive=…)`.
- The mind never stops a turn: a missing, malformed, late or unclosed header costs only the thought; the reply is kept, cleaned.
- Every tuning constant is marked `ponytail:`.
- Real-model probe runs follow `docs/images/rules-and-gotchas.md`; any cloud run follows the paid-API rule (state calls and cost, wait for a yes, one smoke test first).
- Commit after every task, Conventional Commits, on the current branch (`feat/minds-slice-3`); never push.

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `docs/specs/2026-09-29-minds.md` | §8.3 slice-3 contract (written), §0 Progress | 1, 9 |
| `engine/src/kataki/features.py` | `mind.thought` | 2 |
| `engine/src/kataki/thought.py` (new) | `mode`, `ask`, `heads`, `is_head`, `split`, `parse`, `echoed`, `Header` | 2, 3 |
| `engine/src/kataki/turns.py` | the header in `[Directive]`; reading, cleaning, storing it; `done.thought`; echo in `_Opener`; the afterthought flag | 4, 5, 6 |
| `engine/src/kataki/after.py` | optional `thought` (afterthought) in the side call | 6 |
| `engine/src/kataki/people.py` | `people[].thought` | 7 |
| `engine/src/kataki/mind.py` | Thought and Intent nodes | 7 |
| `engine/evals/probes.py` | P8c `thought` (leak/echo), `latency` (the 2 s gate) | 8 |
| tests | `test_thought.py` (new), `test_features.py` | 2–7 |

---

### Task 1: Commit the slice-3 contract

**Files:**
- Modify: `docs/specs/2026-09-29-minds.md` (§8.3, already edited in the working tree by the plan's author)

- [ ] **Step 1: Check the edit is there**

Run (repo root): `git diff docs/specs/2026-09-29-minds.md`
Expected: the "Known now" sentence no longer mentions slice 3, and a **Slice 3** block sits between the Slice 2 block and `### 8.4`. It names `mind.thought`, the thought shape `{"thinks", "wants", "from"}` stored at `messages.gen.thought`, `done.thought`, `people[].thought`, the `thought` / `intent` Mind nodes, `gen.trace.echo` and `gen.trace.ms.thought`. If the block is missing (a fresh checkout), copy it from this plan's "Decisions" and Tasks 4–7 before going on.

- [ ] **Step 2: Commit**

```bash
git add docs/specs/2026-09-29-minds.md
git commit -m "docs: minds slice 3 API contract for the UI"
```

---

### Task 2: `mind.thought` and reading a thought (pure)

**Files:**
- Modify: `engine/src/kataki/features.py` (`FEATURES`)
- Create: `engine/src/kataki/thought.py`
- Test: `engine/tests/test_thought.py` (new), `engine/tests/test_features.py`

**Interfaces:**
- Consumes: `features.enabled(conn, name)`, `knobs.setting(conn, key, default)`, `llm.Endpoint` (`.thinks`, `.think_tags`).
- Produces:
  - `features.FEATURES["mind.thought"] = "alpha"`
  - `thought.WORDS = {"thinks": 25, "wants": 10}`, `thought.ECHO_WORDS = 5`, `thought.ASK` (with `{name}`, `{open}`, `{close}`), `thought.STRONGER` (with `{name}`)
  - `thought.mode(conn, ep: Endpoint, speaker_id: int | None) -> str | None` — `"inline" | "after" | None`
  - `thought.ask(name: str, tags: tuple[str, str]) -> str`
  - `thought.heads(name: str) -> tuple[str, ...]`, `thought.is_head(line: str, name: str) -> bool`
  - `thought.split(text: str, name: str, tags: tuple[str, str]) -> tuple[str, list[str]]` — (text without header lines and stray tags, the header lines)
  - `thought.parse(lines: list[str], name: str) -> dict | None` — `{"thinks": str | None, "wants": str | None}`
  - `thought.echoed(thinks: str | None, reply: str) -> str | None`

- [ ] **Step 1: Write the failing tests**

Create `engine/tests/test_thought.py`:

```python
"""Slice 3: the thought before the reply, read, kept out of the reply, checked, and shown."""

from kataki import thought
from kataki.llm import Endpoint

TAGS = ("<think>", "</think>")
EP = Endpoint(base_url="http://x/v1", model="m")


# --- pure --------------------------------------------------------------------------------------


def test_the_header_is_asked_for_with_the_endpoints_own_tags():
    line = thought.ask("Mira", ("<thought>", "</thought>"))
    assert "<thought>\nMira thinks:" in line and "Mira wants:" in line and "</thought>" in line
    assert "at most 25 words" in line and "at most 10 words" in line


def test_header_lines_are_read_in_any_dress():
    lines = ["**Mira thinks:** “Don't look at the ring.”", "mira wants: him to drop it"]
    assert thought.parse(lines, "Mira Voss") == {
        "thinks": "Don't look at the ring.",
        "wants": "him to drop it",
    }
    assert thought.parse(["Thinks: only this"], "Mira") == {"thinks": "only this", "wants": None}
    assert thought.parse(["She sighs."], "Mira") is None


def test_a_long_thought_is_clipped_to_its_cap():
    long = "Mira thinks: " + " ".join(["word"] * 40)
    assert len(thought.parse([long], "Mira")["thinks"].split()) == thought.WORDS["thinks"]


def test_split_takes_header_lines_and_stray_tags_out_of_a_text():
    rest, found = thought.split("Nothing.\n</think>\n\nMira thinks: he saw it.", "Mira", TAGS)
    assert rest == "Nothing." and found == ["Mira thinks: he saw it."]
    assert thought.split("He thinks: nothing.", "Mira", TAGS)[1] == []  # someone else's line


def test_an_echo_is_five_words_of_the_thought_in_a_row():
    thinks = "I promised myself I wouldn't ask about the ring."
    assert thought.echoed(thinks, "*sighs* I promised myself I wouldn't, okay?") == (
        "i promised myself i wouldn't"
    )
    assert thought.echoed(thinks, "The ring? What ring. I never ask.") is None
    assert thought.echoed(None, "anything at all here") is None


def test_who_gets_a_thought(conn):
    assert thought.mode(conn, EP, 3) == "inline"
    assert thought.mode(conn, EP, None) is None  # the narrator voices no one's mind
    thinking = Endpoint(base_url="x", model="m", params={"thinking": "enabled"})
    assert thought.mode(conn, thinking, 3) == "after"
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    assert thought.mode(conn, EP, 3) is None
    conn.execute("UPDATE settings SET value='\"premium\"' WHERE key='mind.level'")
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.thought', 'false')")
    assert thought.mode(conn, EP, 3) is None
```

In `engine/tests/test_features.py`, `test_the_api_lists_features`, after the `mind.bonds` line add:

```python
    assert body["features"]["mind.thought"]["stage"] == "alpha"
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_thought.py tests/test_features.py -q`
Expected: FAIL — `ImportError: cannot import name 'thought' from 'kataki'`, and `KeyError: 'mind.thought'` in the API test.

- [ ] **Step 3: Implement**

In `engine/src/kataki/features.py`, add to `FEATURES` after `mind.bonds`:

```python
    "mind.thought": "alpha",  # slice 3: a private thought before the reply
```

Create `engine/src/kataki/thought.py`:

```python
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
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `uv run pytest tests/test_thought.py tests/test_features.py -q && uv run ruff check . && uv run ruff format --check .`
Expected: PASS, clean.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/features.py engine/src/kataki/thought.py engine/tests/test_thought.py engine/tests/test_features.py
git commit -m "feat(engine): mind.thought, and reading a character's two-line thought"
```

---

### Task 3: A plain-words header never reaches the reply (pure)

**Files:**
- Modify: `engine/src/kataki/thought.py` (append)
- Test: `engine/tests/test_thought.py` (append)

**Interfaces:**
- Produces: `thought.Header(on: bool, name: str, tags: tuple[str, str])` with `.feed(text: str) -> str`, `.flush() -> str`, `.caught: list[str]` (the header lines it swallowed), `.held: str`. Like `turns._Prefix`: it holds the start of the stream only while it could still be a header line (`Mira thinks:` / `Mira wants:` / `thinks:` / `wants:`, any dress) or a tag, drops such lines, then passes everything through unchanged.

- [ ] **Step 1: Write the failing tests** (append to `engine/tests/test_thought.py`)

```python


def feed(header: thought.Header, *chunks: str) -> str:
    return "".join(header.feed(c) for c in chunks) + header.flush()


def test_a_plain_words_header_never_reaches_the_reply():
    h = thought.Header(True, "Mira", TAGS)
    shown = feed(h, "Mi", "ra thi", "nks: don't look.\nMira wa", "nts: out\n</thi", "nk>\n\nNo.")
    assert shown.strip() == "No." and h.caught == ["Mira thinks: don't look.", "Mira wants: out"]


def test_an_ordinary_reply_passes_at_once():
    h = thought.Header(True, "Mira", TAGS)
    assert h.feed("Th") == ""  # could still be "thinks:"
    assert h.feed("e tide.") == "The tide."
    assert h.feed(" More.") == " More." and h.caught == []


def test_a_stream_that_ends_on_a_header_line_shows_nothing():
    h = thought.Header(True, "Mira", TAGS)
    assert feed(h, "Mira thinks: tired") == "" and h.caught == ["Mira thinks: tired"]
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_thought.py -q`
Expected: FAIL — `AttributeError: module 'kataki.thought' has no attribute 'Header'`.

- [ ] **Step 3: Implement** (append to `engine/src/kataki/thought.py`)

```python


class Header:
    """Keeps a header the model wrote as plain words ("Mira thinks: …" lines, or a stray
    </think>) out of the start of the visible reply. What it caught is in `caught`.
    ponytail: only the start is held; a header written after the reply is removed from the
    saved text (`split`), but its words were already streamed."""

    def __init__(self, on: bool, name: str, tags: tuple[str, str]):
        self.on, self.name, self.tags, self.held, self.caught = on, name, tags, "", []

    def _maybe(self, line: str) -> bool:
        """Could this unfinished first line still turn out to be a header line or a tag?"""
        bare, tag = _bare(line), line.strip()
        return (
            is_head(line, self.name)
            or any(h.startswith(bare) for h in heads(self.name))
            or any(t.startswith(tag) for t in self.tags)
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
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `uv run pytest tests/test_thought.py -q && uv run ruff check . && uv run ruff format --check .`
Expected: PASS, clean.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/thought.py engine/tests/test_thought.py
git commit -m "feat(engine): a thought written as plain words is kept out of the reply"
```

---

### Task 4: She thinks first, in the turn

**Files:**
- Modify: `engine/src/kataki/turns.py` (`_generate`, new `_early`)
- Test: `engine/tests/test_thought.py` (imports, constants, append)

**Interfaces:**
- Consumes: everything from Tasks 2–3; `context.build(directive=…)`; `llm.chat_stream` (`thought` / `token` events; a tagged header arrives as `thought`).
- Produces:
  - `turns._early(thoughts: list[str], header: thought.Header, name: str, tags) -> dict | None` — the thought written before the reply's first word.
  - In `_generate`: `voice = thought.mode(...)`; on `"inline"` the header instruction is appended to `[Directive]` (first take and retake); `messages.gen.thought = {"thinks", "wants", "from": "before" | "after"}` when a header was read; `gen.reasoning` without header lines (None when nothing else was thought); `gen.think_ms` only for real reasoning, else `gen.trace.ms.thought`; `done.thought` (the thought or None). The saved text never holds header lines or stray tags; a never-closed tag gives its content (minus the header) back as the reply.

- [ ] **Step 1: Write the failing tests**

In `engine/tests/test_thought.py`, replace the import block with:

```python
import json

import pytest

from kataki import chat, library, thought, turns
from kataki.llm import Endpoint
```

and after `EP = …` add:

```python
HEADER = "<think>\nMira thinks: Don't look at the ring.\nMira wants: him to drop it\n</think>\n"
SEEN = {"thinks": "Don't look at the ring.", "wants": "him to drop it", "from": "before"}
```

Then append:

```python


# --- in the turn -------------------------------------------------------------------------------


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    return library.create_story(
        conn, "Low Tide", character_ids=[ids["Mira"], ids["Tobin"]], persona_id=ids["Aren"]
    )


async def play(stream):
    return [e async for e in stream]


def shown(events) -> str:
    return "".join(v for k, v in events if k == "token")


def leaf(conn, story):
    m = chat.active_path(conn, story)[-1]
    return m["text"], json.loads(m["gen"])


@pytest.mark.anyio
async def test_she_thinks_first_and_the_thought_stays_out_of_the_story(conn, story, backend):
    backend.say(HEADER + "Nothing. Just tired.", "Fine.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, what's wrong?"))
    asked = backend.requests[0]["messages"][-1]["content"].split("[Directive]")[1]
    assert "<think>\nMira thinks:" in asked
    assert "Mira thinks: Don't look at the ring." in "".join(v for k, v in events if k == "thought")
    assert shown(events) == "Nothing. Just tired."
    text, gen = leaf(conn, story)
    assert text == "Nothing. Just tired." and gen["thought"] == SEEN
    assert gen["reasoning"] is None and "think_ms" not in gen
    assert isinstance(gen["trace"]["ms"]["thought"], int)
    assert events[-1][1]["thought"] == SEEN

    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert "the ring" not in json.dumps(backend.requests[1]["messages"])


@pytest.mark.anyio
@pytest.mark.parametrize(
    "reply, came",
    [
        ("Mira thinks: Don't look at the ring.\nMira wants: him to drop it\n\nNothing.", "before"),
        ("Mira thinks: Don't look at the ring.\n</think>\nNothing.", "before"),
        ("<think>\nMira thinks: Don't look at the ring.\n\nNothing.", "before"),  # never closed
        ("Nothing.\n<think>Mira thinks: Don't look at the ring.</think>", "after"),
        ("Nothing.\n\nMira thinks: Don't look at the ring.", "after"),
    ],
)
async def test_a_header_in_the_wrong_place_never_stays_in_the_reply(
    conn, story, backend, reply, came
):
    backend.say(reply)
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    text, gen = leaf(conn, story)
    assert text == "Nothing." and events[-1][1]["text"] == "Nothing."
    assert gen["thought"]["thinks"] == "Don't look at the ring." and gen["thought"]["from"] == came
    if came == "before":  # a header at the start is never streamed as words either
        assert "thinks" not in shown(events) and "think>" not in shown(events)


@pytest.mark.anyio
@pytest.mark.parametrize("reply", ["Nothing.", "<think>whatever I feel</think>Nothing."])
async def test_no_header_or_a_malformed_one_costs_only_the_thought(conn, story, backend, reply):
    backend.say(reply)
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    text, gen = leaf(conn, story)
    assert events[-1][0] == "done" and text == "Nothing." and "thought" not in gen
    assert events[-1][1]["thought"] is None


@pytest.mark.anyio
async def test_the_narrator_and_lite_are_never_asked(conn, story, backend):
    backend.say("The tide turns.", "Fine.")
    await play(turns.turn(conn, backend.llm, story, None, speaker="narrator"))
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert all("thinks:" not in json.dumps(r["messages"]) for r in backend.requests)
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_thought.py -q`
Expected: FAIL — `assert "<think>\nMira thinks:" in asked` fails, `KeyError: 'thought'` on `gen`/`done`, and the wrong-place cases leave `Mira thinks:` / `</think>` in the saved text. The pure tests still pass.

- [ ] **Step 3: Implement** — fifteen edits in `engine/src/kataki/turns.py`, (a)–(o), in file order.

(a) Import it. Replace

```python
    roles,
)
from kataki.llm import LLM, LLMError
```

with

```python
    roles,
    thought,
)
from kataki.llm import LLM, LLMError
```

(b) Above `async def _read_past_before_skip(`, add

```python
def _early(thoughts: list[str], header: thought.Header, name: str, tags) -> dict | None:
    """The thought written before the reply's first word: in the tags, or caught at its start."""
    return thought.parse(thought.split("".join(thoughts), name, tags)[1] + header.caught, name)


```

(c) In `_generate`, the speaker's name is needed before the prompt is built. Replace

```python
    names = dict(
        conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)).fetchall()
    )
```

with

```python
    names = dict(
        conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)).fetchall()
    )
    name = names.get(speaker_id)
```

(d) …and delete the later assignment: replace

```python

    name = names.get(speaker_id)
    parent = chat.get_message(conn, parent_id) if parent_id else None
```

with

```python

    parent = chat.get_message(conn, parent_id) if parent_id else None
```

(e) After the stance block, decide the thought and the directive. Replace

```python
        decide, check, hold = "", False, False

    trace: dict = {"why": why, "ms": {}}
```

with

```python
        decide, check, hold = "", False, False
    try:
        voice = thought.mode(conn, ep, speaker_id)
    except Exception as e:
        logging.getLogger(__name__).warning("thought skipped for story %s: %s", story_id, e)
        voice = None
    header_ask = thought.ask(name, ep.think_tags) if voice == "inline" else ""
    first = " ".join(p for p in (decide, header_ask) if p)

    trace: dict = {"why": why, "ms": {}}
```

(f) Both prompt builds use it. Replace

```python
        conn, story_id, speaker_id, ep, leaf_id=parent_id, inside=inside, directive=decide
    )
```

with

```python
        conn, story_id, speaker_id, ep, leaf_id=parent_id, inside=inside, directive=first
    )
```

(g) and, in the recalled rebuild, replace

```python
                inside=inside,
                directive=decide,
            )
```

with

```python
                inside=inside,
                directive=first,
            )
```

(h) The header filter exists before the stream (the `finally` block reads it). Replace

```python
    prefix, opener, dropped = _Prefix(name or "Narrator"), _Opener(False), ""
```

with

```python
    prefix, opener, dropped = _Prefix(name or "Narrator"), _Opener(False), ""
    header, before = thought.Header(False, "", ep.think_tags), None
```

(i) A fresh one per take. Replace

```python
            parts, thoughts = [], []
            prefix, opener = _Prefix(name or "Narrator"), _Opener(hold and not attempt)
```

with

```python
            parts, thoughts, before = [], [], None  # before: thought pieces before the 1st word
            prefix, opener = _Prefix(name or "Narrator"), _Opener(hold and not attempt)
            header = thought.Header(voice == "inline", name or "", ep.think_tags)
```

(j) Tokens pass the header filter first, then the name prefix, then the opener. Replace

```python
                        first_token = first_token or time.monotonic()
                        if value := opener.feed(prefix.feed(value)):
```

with

```python
                        first_token = first_token or time.monotonic()
                        before = len(thoughts) if before is None else before
                        value = prefix.feed(header.feed(value))
                        if value := opener.feed(value):
```

(k) And at the end of the stream. Replace

```python
            if not opener.hit and (rest := opener.feed(prefix.flush()) + opener.flush()):
```

with

```python
            rest = "" if opener.hit else prefix.feed(header.flush()) + prefix.flush()
            if not opener.hit and (rest := opener.feed(rest) + opener.flush()):
```

(l) The retake is asked for the thought again (a fresh thought conditions the fresh reply). Replace

```python
                    directive=f"{decide} {bonds.STRONGER.format(name=name)}".strip(),
```

with

```python
                    directive=" ".join(
                        p for p in (decide, bonds.STRONGER.format(name=name), header_ask) if p
                    ),
```

(m) What is kept. Replace

```python
        held = opener.held + prefix.flush()  # stopped while the opening was held: keep it
        text = _unsign(("".join(parts) + held).strip(), name or "Narrator")
        if not text and dropped:  # the second take failed or came back empty: keep the first
            text = _unsign(dropped.strip(), name or "Narrator")
        if text:
```

with

```python
        held = opener.held + prefix.flush() + header.flush()  # stopped while held: keep it
        text = ("".join(parts) + held).strip()
        if not text and dropped:  # the second take failed or came back empty: keep the first
            text = dropped.strip()
        reasoning, heard = "".join(thoughts), []
        if voice == "inline":  # the header is the thought: never the reasoning, never the reply
            reasoning, heard = thought.split(reasoning, name, ep.think_tags)
            text, late = thought.split(text, name, ep.think_tags)  # written after the reply
            heard += header.caught + late
            if not text:  # a tag never closed: the reply was written inside it
                text, reasoning = reasoning, ""
        text = _unsign(text, name or "Narrator")
        if text:
```

(n) What is stored. Replace

```python
                "reasoning": "".join(thoughts) or None,
                "usage": done.get("usage"),
            }
            if first_thought:  # stopped mid-thought: the thinking ran until now
                gen["think_ms"] = round(1000 * ((first_token or time.monotonic()) - first_thought))
```

with

```python
                "reasoning": reasoning or None,
                "usage": done.get("usage"),
            }
            if seen := thought.parse(heard, name or ""):  # Peek's thought; did it come first?
                early = _early(thoughts[:before], header, name or "", ep.think_tags)
                gen["thought"] = {**seen, "from": "before" if early else "after"}
            if first_thought:  # stopped mid-thought: the thinking ran until now
                spent = round(1000 * ((first_token or time.monotonic()) - first_thought))
                if gen["reasoning"]:
                    gen["think_ms"] = spent
                else:  # only the header was thought: its time is the thought's, not reasoning's
                    trace["ms"]["thought"] = spent
```

(o) What `done` says. Replace

```python
                "mood": gen.get("mind"),
            },
```

with

```python
                "mood": gen.get("mind"),
                "thought": gen.get("thought"),
            },
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `uv run pytest -q && uv run ruff check . && uv run ruff format --check .`
Expected: all PASS (the existing suite included: scripted replies carry no header, so they see only a longer `[Directive]`), clean.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/turns.py engine/tests/test_thought.py
git commit -m "feat(engine): a character writes a private thought before each reply (minds slice 3)"
```

---

### Task 5: A reply that says its thought aloud is written again once

**Files:**
- Modify: `engine/src/kataki/turns.py` (`_Opener`, `_generate`)
- Test: `engine/tests/test_thought.py` (append)

**Interfaces:**
- Consumes: `thought.echoed`, `thought.STRONGER`, `_early` (Task 4).
- Produces:
  - `_Opener.watch(early: dict | None) -> None` — called once just before the first visible word; with a thought, arms the hold for the echo check. New attributes `opening` (the opener check was armed at the start), `thinks`, `echo` (the echoed words, or None), `watched`.
  - `_Opener.flush` checks the opener only when `opening`, then the echo.
  - `gen.trace.echo = {"hit": str, "resampled": bool}`: `True` when the opening echoed and was retaken (sharing the single retake with the opener check: attempt 1 is never armed), `False` when the echo was later in the saved reply.

- [ ] **Step 1: Write the failing tests** (append to `engine/tests/test_thought.py`)

```python


@pytest.mark.anyio
async def test_a_reply_that_says_its_thought_aloud_is_written_again_once(conn, story, backend):
    header = "<think>\nMira thinks: I promised myself I wouldn't ask about the ring.\n</think>\n"
    backend.say(
        header + "I promised myself I wouldn't ask. So I won't.",
        header + "I promised myself I wouldn't ask, okay?",  # the retake echoes too: kept
    )
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert len(backend.requests) == 2  # one retake, never two
    retake = backend.requests[1]["messages"][-1]["content"].split("[Directive]")[1]
    assert thought.STRONGER.format(name="Mira") in retake and "Mira thinks:" in retake
    assert "So I won't" not in shown(events)
    text, gen = leaf(conn, story)
    assert gen["trace"]["echo"] == {"hit": "i promised myself i wouldn't", "resampled": True}
    assert "check" not in gen["trace"] and text == "I promised myself I wouldn't ask, okay?"


@pytest.mark.anyio
async def test_an_echo_after_the_first_sentence_is_noted_not_retaken(conn, story, backend):
    header = "<think>\nMira thinks: I promised myself I wouldn't ask about the ring.\n</think>\n"
    backend.say(header + "Hm. Fine. I promised myself I wouldn't, so.")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    _, gen = leaf(conn, story)
    assert len(backend.requests) == 1
    assert gen["trace"]["echo"] == {"hit": "i promised myself i wouldn't", "resampled": False}
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_thought.py -q -k echo`
Expected: FAIL — one request only / `KeyError: 'echo'`.

- [ ] **Step 3: Implement** — six edits in `engine/src/kataki/turns.py`.

(a) Replace

```python
class _Opener:
    """Holds a reply's first sentence back while the check is armed (bonds.armed), so an
    agreeing, apologising or assistant-style opening is caught before anyone sees it."""

    def __init__(self, armed: bool):
        self.armed, self.held, self.hit, self.dropped = armed, "", None, ""
```

with

```python
class _Opener:
    """Holds a reply's first sentence back while the check is armed (bonds.armed), so an
    agreeing, apologising or assistant-style opening is caught before anyone sees it; and,
    when a thought came first (`watch`), an opening that says the thought aloud."""

    def __init__(self, armed: bool):
        self.armed, self.held, self.hit, self.dropped = armed, "", None, ""
        self.opening, self.thinks, self.echo, self.watched = armed, None, None, False

    def watch(self, early: dict | None) -> None:
        """Called once, just before the first visible word, with the thought written before it.
        ponytail: holding the first sentence for the echo check adds its time to the first
        word; if the latency probe fails the 2 s gate, watch only when `bonds.armed` is."""
        self.watched = True
        if early and early["thinks"] and not self.hit:
            self.thinks, self.armed = early["thinks"], True
```

(b) In `_Opener.flush`, replace

```python
        self.hit = bonds.opener(held)
        if self.hit:
```

with

```python
        self.hit = bonds.opener(held) if self.opening else None
        if not self.hit and (echo := thought.echoed(self.thinks, held)):
            self.hit = self.echo = echo
        if self.hit:
```

(c) In the token branch of `_generate`, replace

```python
                        value = prefix.feed(header.feed(value))
                        if value := opener.feed(value):
```

with

```python
                        value = prefix.feed(header.feed(value))
                        if value and voice == "inline" and not attempt and not opener.watched:
                            opener.watch(_early(thoughts, header, name, ep.think_tags))
                        if value := opener.feed(value):
```

(d) The same when the first visible word only comes with the stream's end. Replace

```python
            rest = "" if opener.hit else prefix.feed(header.flush()) + prefix.flush()
```

with

```python
            rest = "" if opener.hit else prefix.feed(header.flush()) + prefix.flush()
            if rest and voice == "inline" and not attempt and not opener.watched:
                opener.watch(_early(thoughts, header, name, ep.think_tags))
```

(e) The retake says what went wrong. Replace

```python
            dropped = opener.dropped
            trace["check"] = {"hit": opener.hit, "resampled": True}
```

with

```python
            dropped = opener.dropped
            if opener.echo:  # it said its thought aloud: the same one retake, told to keep it in
                trace["echo"] = {"hit": opener.echo, "resampled": True}
                stronger = thought.STRONGER.format(name=name)
            else:
                trace["check"] = {"hit": opener.hit, "resampled": True}
                stronger = bonds.STRONGER.format(name=name)
```

and replace

```python
                    directive=" ".join(
                        p for p in (decide, bonds.STRONGER.format(name=name), header_ask) if p
                    ),
```

with

```python
                    directive=" ".join(p for p in (decide, stronger, header_ask) if p),
```

(f) An echo past the opening is noted. Replace

```python
                gen["thought"] = {**seen, "from": "before" if early else "after"}
```

with

```python
                gen["thought"] = {**seen, "from": "before" if early else "after"}
                if "echo" not in trace and (echo := thought.echoed(seen["thinks"], text)):
                    trace["echo"] = {"hit": echo, "resampled": False}  # past the first sentence
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `uv run pytest tests/test_thought.py tests/test_bonds.py tests/test_turns.py -q && uv run ruff check . && uv run ruff format --check .`
Expected: PASS (slice 2b's opener tests unchanged: `trace.check` keeps its shape), clean.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/turns.py engine/tests/test_thought.py
git commit -m "feat(engine): a reply that says its thought aloud is written again once"
```

---

### Task 6: A reasoning model's afterthought, from the side call

**Files:**
- Modify: `engine/src/kataki/after.py` (`schema`, `read`, `_ask`, `run`), `engine/src/kataki/turns.py` (the `after.run` call)
- Test: `engine/tests/test_thought.py` (imports, append)

**Interfaces:**
- Consumes: `thought.WORDS`; `voice == "after"` from Task 4 (`ep.thinks`: a reasoning model with thinking on gets no header).
- Produces:
  - `after.AFTERTHOUGHT` (with `{name}`)
  - `after.schema(handles: list[str], afterthought: bool = False) -> dict` — with `afterthought`, a required nullable `thought` string.
  - `after.read(data, handles)` adds `"thought"` (clipped to 25 words) only when the model gave a non-empty string.
  - `after.run(..., get_key, afterthought: bool = False)` — when asked and given, writes `gen.thought = {"thinks": <it>, "wants": None, "from": "after"}`.
  - `turns._generate` passes `afterthought=voice == "after"` and re-reads `gen.thought` with `gen.mind` after the side call, so `done.thought` shows it. With `mind.bonds` off there is no side call, so no afterthought.

- [ ] **Step 1: Write the failing tests**

In `engine/tests/test_thought.py` change the kataki import to

```python
from kataki import after, chat, library, thought, turns
```

and append:

```python


def test_the_side_call_asks_for_an_afterthought_only_when_told():
    assert "thought" not in after.schema(["E1"])["properties"]
    s = after.schema(["E1"], afterthought=True)
    assert s["properties"]["thought"] == {"type": ["string", "null"]}
    assert "thought" in s["required"]
    base = {"felt": {"label": "calm", "intensity": 1, "about": None, "cause": ""},
            "events": [], "position": None, "yielded": False, "face": "neutral"}  # fmt: skip
    assert "thought" not in after.read(base | {"thought": None}, ["E1"])
    assert "thought" not in after.read(base | {"thought": 7}, ["E1"])
    assert after.read(base | {"thought": " Tired of him. "}, ["E1"])["thought"] == "Tired of him."


@pytest.mark.anyio
async def test_a_reasoning_model_gets_an_afterthought_from_the_side_call(
    conn, story, backend, side_call
):
    conn.execute("INSERT INTO settings(key, value) VALUES('memory.thinking', '\"lot\"')")
    labels = {"felt": {"label": "calm", "intensity": 1, "about": None, "cause": ""},
              "events": [], "position": None, "yielded": False, "face": "neutral",
              "thought": "He'll never let this go."}  # fmt: skip
    backend.say({"reasoning_content": "She weighs it.", "content": "Fine."}, json.dumps(labels))
    events = await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert "thinks:" not in json.dumps(backend.requests[0]["messages"])  # no header asked
    assert "thought" in backend.requests[1]["response_format"]["json_schema"]["schema"]["required"]
    after_ = {"thinks": "He'll never let this go.", "wants": None, "from": "after"}
    _, gen = leaf(conn, story)
    assert gen["thought"] == after_ and events[-1][1]["thought"] == after_
    assert gen["reasoning"] == "She weighs it."  # its own reasoning stays where it was
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_thought.py -q -k afterthought`
Expected: FAIL — `TypeError: schema() got an unexpected keyword argument 'afterthought'`, and `KeyError: 'thought'` on `gen`.

- [ ] **Step 3: Implement**

In `engine/src/kataki/after.py`:

(a) Replace `from kataki import bonds, chat, features, images, inner, knobs, roles` with

```python
from kataki import bonds, chat, features, images, inner, knobs, roles, thought
```

(b) Replace

```python
def schema(handles: list[str]) -> dict:
    """The labels, every list closed: feelings, events, faces, and only the people here."""
    level = {"type": "integer", "enum": [1, 2, 3]}
    return {
```

with

```python
AFTERTHOUGHT = (
    "Also give thought: what {name} privately thought while saying the reply, in {name}'s own "
    "voice, at most 25 words."
)


def schema(handles: list[str], afterthought: bool = False) -> dict:
    """The labels, every list closed: feelings, events, faces, and only the people here; with
    `afterthought`, also the thought a reasoning model's reply was said with (slice 3)."""
    level = {"type": "integer", "enum": [1, 2, 3]}
    out = {
```

(c) At the end of `schema`, replace

```python
        "required": ["felt", "events", "position", "yielded", "face"],
        "additionalProperties": False,
    }
```

with

```python
        "required": ["felt", "events", "position", "yielded", "face"],
        "additionalProperties": False,
    }
    if afterthought:
        out["properties"]["thought"] = {"type": ["string", "null"]}
        out["required"].append("thought")
    return out
```

(d) At the end of `read`, replace

```python
        "yielded": data.get("yielded") is True,
        "face": data["face"],
    }
```

with

```python
        "yielded": data.get("yielded") is True,
        "face": data["face"],
    } | _afterthought(data)


def _afterthought(data: dict) -> dict:
    """The optional `thought`, clipped to its cap; a missing or empty one is simply left out."""
    said = data.get("thought")
    if not isinstance(said, str) or not said.strip():
        return {}
    return {"thought": " ".join(said.split()[: thought.WORDS["thinks"]])}
```

(e) Replace the `_ask` signature

```python
async def _ask(
    conn, llm: LLM, story_id: int, speaker_id: int, reply: str, seen: dict, get_key
) -> dict | None:
```

with

```python
async def _ask(
    conn,
    llm: LLM,
    story_id: int,
    speaker_id: int,
    reply: str,
    seen: dict,
    get_key,
    afterthought: bool = False,
) -> dict | None:
```

(f) In `_ask`, replace

```python
            f"[{name}'s reply: for position, yielded and face only]\n{reply[-1500:]}",
        },
    ]
    return await llm.complete_json(
        ep, ask, schema(handles), lambda d: read(d, handles), name="after"
    )
```

with

```python
            f"[{name}'s reply: for position, yielded and face only]\n{reply[-1500:]}"
            + (f"\n\n{AFTERTHOUGHT.format(name=name)}" if afterthought else ""),
        },
    ]
    return await llm.complete_json(
        ep, ask, schema(handles, afterthought), lambda d: read(d, handles), name="after"
    )
```

(g) In `run`'s signature, after `get_key: Callable[[str], str | None],` add

```python
    afterthought: bool = False,  # a reasoning model replied: ask what they thought (slice 3)
```

(h) In `run`, replace

```python
        got = await _ask(conn, llm, story_id, speaker_id, reply, seen, get_key)
```

with

```python
        got = await _ask(conn, llm, story_id, speaker_id, reply, seen, get_key, afterthought)
```

(i) In `run`'s recording block, replace

```python
                (json.dumps(got or "skipped"), round(1000 * (time.monotonic() - at)), message_id),
            )
```

with

```python
                (json.dumps(got or "skipped"), round(1000 * (time.monotonic() - at)), message_id),
            )
            if afterthought and got and got.get("thought"):  # Peek's thought, labelled as after
                said = {"thinks": got["thought"], "wants": None, "from": "after"}
                conn.execute(
                    "UPDATE messages SET gen=json_set(gen, '$.thought', json(?)) WHERE id=?",
                    (json.dumps(said), message_id),
                )
```

In `engine/src/kataki/turns.py`, replace

```python
                    minds.get(speaker_id),
                    get_key,
                )
                # the side call may have replaced the mood the reply was saved with
                gen["mind"] = json.loads(chat.get_message(conn, message_id)["gen"]).get("mind")
```

with

```python
                    minds.get(speaker_id),
                    get_key,
                    afterthought=voice == "after",
                )
                # the side call may have replaced the mood, and written an afterthought
                saved = json.loads(chat.get_message(conn, message_id)["gen"])
                gen["mind"], gen["thought"] = saved.get("mind"), saved.get("thought")
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `uv run pytest tests/test_thought.py tests/test_after.py -q && uv run ruff check . && uv run ruff format --check .`
Expected: PASS (slice 2b's side-call tests unchanged: without `afterthought` the schema and labels are exactly as before), clean.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/after.py engine/src/kataki/turns.py engine/tests/test_thought.py
git commit -m "feat(engine): a reasoning model's thought comes from the side call, as an afterthought"
```

---

### Task 7: Peek and the Mind graph show the thought

**Files:**
- Modify: `engine/src/kataki/people.py` (`_thought`, `people`), `engine/src/kataki/mind.py` (`mind`)
- Test: `engine/tests/test_thought.py` (imports, append)

**Interfaces:**
- Consumes: `messages.gen.thought` (Tasks 4, 6); `features.enabled(conn, "mind.thought")`.
- Produces:
  - `people._thought(path: list, entity_id: int) -> dict | None` — the thought behind their latest line on the branch, plus `message_id`; None if that line had none.
  - `people.people(...)[i]["thought"]` (None when `mind.thought` is off).
  - `mind.mind(...)` nodes `{"id": "thought", "column": "inside", "kind": "thought", "title": "Thought" | "Afterthought", ...}` and `{"id": "intent", "column": "decide", "kind": "intent", "title": "Intent", ...}`, links thought → intent → spoke (gold when `from == "before"`); a thought without a want joins the gold INSIDE nodes that link to the Expression node or spoke.

- [ ] **Step 1: Write the failing tests**

In `engine/tests/test_thought.py` change the kataki import to

```python
from kataki import after, chat, library, mind, people, thought, turns
```

and append:

```python


@pytest.mark.anyio
async def test_peek_and_the_mind_graph_show_the_latest_thought(conn, story, backend):
    backend.say(HEADER + "Nothing.")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    cast = {p["name"]: p for p in people.people(conn, row)}
    reply = chat.active_path(conn, story)[-1]["id"]
    assert cast["Mira"]["thought"] == SEEN | {"message_id": reply}
    assert cast["Tobin"]["thought"] is None
    graph = mind.mind(conn, reply)
    nodes = {n["id"]: n for n in graph["nodes"]}
    assert nodes["thought"]["text"] == "Don't look at the ring." and nodes["thought"]["gold"]
    assert (nodes["intent"]["column"], nodes["intent"]["text"]) == ("decide", "him to drop it")
    assert {"from": "thought", "to": "intent", "gold": True} in graph["links"]
    assert {"from": "intent", "to": "spoke", "gold": True} in graph["links"]


@pytest.mark.anyio
async def test_switched_off_nothing_is_asked_or_shown(conn, story, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.thought', 'false')")
    backend.say(HEADER + "Nothing.")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert "thinks:" not in backend.requests[0]["messages"][-1]["content"]
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    assert all(p["thought"] is None for p in people.people(conn, row))
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_thought.py -q -k "peek or switched"`
Expected: FAIL — `KeyError: 'thought'` on the Peek entry.

- [ ] **Step 3: Implement**

In `engine/src/kataki/people.py`:

(a) Replace the two lines `import logging` and `import sqlite3` at the top with

```python
import json
import logging
import sqlite3
```

(b) Above `def people(`, add

```python
def _thought(path: list, entity_id: int) -> dict | None:
    """The thought behind their latest line on this branch (Peek; spec §8.3), or None when
    that line had none: an older thought would be about another moment."""
    try:
        for m in reversed(path):
            if m["role"] == "assistant" and m["speaker_id"] == entity_id:
                said = json.loads(m["gen"] or "{}").get("thought")
                return {**said, "message_id": m["id"]} if said else None
        return None
    except Exception as e:  # a bad row costs the thought, not the whole Peek
        logging.getLogger(__name__).warning("thought unavailable for %s: %s", entity_id, e)
        return None


```

(c) In `people`, replace

```python
    tied = features.enabled(conn, "mind.bonds")
```

with

```python
    tied = features.enabled(conn, "mind.bonds")
    thinking = features.enabled(conn, "mind.thought")
```

(d) and replace

```python
                "bonds": _bonds(conn, e["id"], path, names, persona_id, epoch) if tied else [],
```

with

```python
                "bonds": _bonds(conn, e["id"], path, names, persona_id, epoch) if tied else [],
                "thought": _thought(path, e["id"]) if thinking else None,
```

In `engine/src/kataki/mind.py`, inside `if who is not None:`, right after the ledger block that ends with

```python
        except Exception as e:
            logging.getLogger(__name__).warning("ledger not shown: %s", e)
```

add

```python
        try:  # the thought the reply was written from (slice 3: Mind 5, cheaply)
            said = gen.get("thought") or {}
            caused = said.get("from") == "before"  # an afterthought was read off the reply
            th = None
            if said.get("thinks"):
                title = "Thought" if caused else "Afterthought"
                th = node("thought", "inside", "thought", title, said["thinks"], None, caused, said)
            if said.get("wants"):
                want = node(
                    "intent", "decide", "intent", "Intent", said["wants"], None, caused, said
                )
                if th:
                    link(th, want, caused)
                if caused:
                    link(want, "spoke", True)
            elif th:
                inside.append((th, caused))
        except Exception as e:
            logging.getLogger(__name__).warning("thought not shown: %s", e)
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `uv run pytest -q && uv run ruff check . && uv run ruff format --check .`
Expected: all PASS, clean.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/people.py engine/src/kataki/mind.py engine/tests/test_thought.py
git commit -m "feat(engine): Peek and the Mind graph show the thought a reply came from"
```

---

### Task 8: Probes P8c (leak and echo) and the latency gate

**Files:**
- Modify: `engine/evals/probes.py`

**Interfaces:**
- Consumes: `_harbour`, `_say` (existing in `probes.py`), `thought.echoed`, `done.thought`, `gen.trace.echo`, `gen.trace.ms.thought`.
- Produces: probes `thought` (function `thinks`) and `latency` in `PROBES`; `probes.RING`, `probes.LEAK`, `probes.SMALL_TALK`, `probes.GATE_MS = 2000`, `probes._first_word(conn, llm, story, line) -> tuple[float, dict]`.

- [ ] **Step 1: Add them**

In the module docstring of `engine/evals/probes.py`, before the line `Replies are printed for a human to judge. …`, add:

```
thought (slice 3, P8c): Mira hides whose ring is in her drawer; five lines press on it. Checks:
she thinks before the reply on at least four of five turns, no header line or tag is ever seen in
a reply (streamed or saved), and no saved reply repeats its thought (echo, after the one retake).

latency (slice 3, spec §9): the same five small-talk lines to two fresh stories, one with
mind.thought on and one off, alternating. Checks: the median time to the first visible word
grows by less than 2 s with the thought on. Prints both medians and the header's own time.

```

Replace the imports

```python
import re
import tempfile
from pathlib import Path

from kataki import bonds, chat, db, inner, library, people, turns
```

with

```python
import re
import statistics
import tempfile
import time
from pathlib import Path

from kataki import bonds, chat, db, inner, library, people, thought, turns
```

Above `PROBES = {`, add:

```python
RING = [
    "Mira, you've been quiet all evening. Something on your mind?",
    "Is it about the ring I saw in your desk drawer?",
    "Come on. Whose ring is it?",
    "Fine. Different question: are you coming to dinner on Friday?",
    "You keep glancing at that drawer, you know.",
]
LEAK = re.compile(r"(?im)^[\W_]*(?:\w+\s+){0,2}(?:thinks|wants)\s*:|</?think>")


async def thinks(conn, llm) -> list[str]:
    story = _harbour(
        conn,
        "Mira runs the harbour office. The ring in her desk drawer was her late brother's; she"
        " has told no one and does not want to talk about it.",
    )
    failures, first, echoes, retaken = [], 0, 0, 0
    for i, line in enumerate(RING):
        streamed, done = await _say(conn, llm, story, line)
        seen = done.get("thought") or {}
        gen = json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}")
        echo = (gen.get("trace") or {}).get("echo") or {}
        print(f"\nAren: {line}\nthought: {seen}\necho: {echo}\nMira: {done.get('text')}")
        if LEAK.search(streamed) or LEAK.search(done.get("text", "")):
            failures.append(f"turn {i + 1}: a header line or tag showed in the reply")
        first += seen.get("from") == "before"
        retaken += bool(echo.get("resampled"))
        echoes += bool(thought.echoed(seen.get("thinks"), done.get("text", "")))
    print(f"\nthought first on {first} of {len(RING)}; echo left in {echoes}; retaken {retaken}")
    if first < len(RING) - 1:  # ponytail: 4 of 5 until a longer run gives a real rate
        failures.append(f"thought before the reply on only {first} of {len(RING)} turns")
    if echoes:
        failures.append(f"{echoes} saved replies repeat their thought")
    return failures


SMALL_TALK = [
    "Evening, Mira.",
    "Busy day at the office?",
    "Any ships in from the south?",
    "What's the weather doing tomorrow?",
    "Right. Night, Mira.",
]
GATE_MS = 2000  # the Mind-graph spec's gate (§4.4, §7.1): the thought may add less than this


async def _first_word(conn, llm, story: int, line: str) -> tuple[float, dict]:
    """Milliseconds from asking to the first visible word, and the `done` payload."""
    began, first, done = time.monotonic(), None, {}
    async for kind, value in turns.turn(conn, llm, story, line):
        if kind == "token" and first is None:
            first = time.monotonic()
        elif kind == "done":
            done = value
    return 1000 * ((first or time.monotonic()) - began), done


async def latency(conn, llm) -> list[str]:
    stories = {on: _harbour(conn, "Mira runs the harbour office.") for on in (True, False)}
    waits: dict[bool, list[float]] = {True: [], False: []}
    header_ms = []
    for line in SMALL_TALK:
        for on in (True, False):  # alternating, so a warming cache favours neither
            conn.execute(
                "INSERT OR REPLACE INTO settings(key, value) VALUES('features.mind.thought', ?)",
                (json.dumps(on),),
            )
            conn.commit()
            ms, done = await _first_word(conn, llm, stories[on], line)
            waits[on].append(ms)
            gen = json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}")
            if on and "thought" in (gen.get("trace") or {}).get("ms", {}):
                header_ms.append(gen["trace"]["ms"]["thought"])
            print(f"thought {'on ' if on else 'off'}: {ms:6.0f} ms  {done.get('text', '')[:60]!r}")
    on, off = statistics.median(waits[True]), statistics.median(waits[False])
    head = statistics.median(header_ms) if header_ms else None
    print(f"\nfirst word, median: on {on:.0f} ms, off {off:.0f} ms, added {on - off:.0f} ms;"
          f" the header itself: {head} ms")  # fmt: skip
    if on - off >= GATE_MS:
        return [f"the thought adds {on - off:.0f} ms to the first word (gate {GATE_MS} ms)"]
    return []


```

In `PROBES`, after `"hold": hold,` add:

```python
    "thought": thinks,
    "latency": latency,
```

- [ ] **Step 2: Lint it, and a dry run on the fake model**

Run: `uv run ruff check evals/probes.py && uv run ruff format --check evals/probes.py`
Expected: clean.

Optional dry run (no model needed), from `engine/`, a throwaway script outside the repo that builds a temp library with the rp role on `http://x/v1`, scripts `tests/conftest.FakeBackend` with `"<think>\nMira thinks: Not the ring. Not tonight.\nMira wants: him to stop\n</think>\nIt's nothing."` five times and ten plain replies, monkeypatches `embed.builtin = lambda: None` and `after.wanted = lambda conn: False`, and calls `probes.PROBES["thought"]` and `probes.PROBES["latency"]`. Expected: both return `[]`; the thought probe prints `thought first on 5 of 5; echo left in 0; retaken 0`.

- [ ] **Step 3: Run them on a real model** (read `docs/images/rules-and-gotchas.md` first)

Local: say the expected time first (10 replies and 10 side calls for `latency`, plus 5–10 replies and 5 side calls for `thought`: about 3 minutes on Qwen3.5-9B Q4 with thinking disabled), check the rate at ~30 s, then run:

`uv run python evals/probes.py --base-url http://127.0.0.1:8080/v1 --model <the loaded model> --probe thought --probe latency`

Online (HF Inference, as slice 2's probes ran): this is paid. State it to the user first — about 30 calls (15–20 replies, 15 side calls; a retake only on an echo), roughly $0.05 at slice 2's rates on Qwen/Qwen3-235B-A22B-Instruct-2507 — and wait for a yes; run one `--probe thought` smoke test before the rest.

Expected: each prints PASS or FAIL with reasons; `latency` prints both medians, the delta and the header's own time. If the hybrid model will not write a literal `<think>` with thinking disabled (the thought shows as `from: after` or not at all), set the rp role's `think_tags` to `["<thought>", "</thought>"]` (Settings › Models, or `model_roles.params`) and run again: the instruction follows the tags. If `latency` fails the gate, apply the fallback in `_Opener.watch`'s `ponytail:` (watch only when `bonds.armed`) and rerun; if it still fails, note 22's fallback is thought on gated turns only (slice 4). Record every number in the spec's Progress (Task 9).

- [ ] **Step 4: Commit**

```bash
git add engine/evals/probes.py
git commit -m "test(engine): probes P8c thought (leak, echo) and the thought's latency gate"
```

---

### Task 9: Record progress and hand the contract to the UI

**Files:**
- Modify: `docs/specs/2026-09-29-minds.md` (§0 Progress)

- [ ] **Step 1: Add Progress lines**, with the commit range and the probe numbers:

```
- 2026-09-29 · Slice 3 "She thinks before she speaks" landed at stage alpha (mind.thought): a two-line thought (thinks ≤25 words, wants ≤10) asked in [Directive] and written before the reply in the same stream; kept out of the reply, history, prefix and gen.reasoning whatever the model does (tagged, plain words, late, unclosed); gen.thought, done.thought, people[].thought, Thought and Intent nodes in the Mind graph (Mind 5, cheaply); an opening that says the thought aloud is written again once (shared retake), a later echo noted; reasoning models get an afterthought from the side call: commits <first>..<last>.
- 2026-09-29 · Probes (slice 3): thought <PASS/FAIL, first N of 5, echoes, retakes>; latency <on/off medians, added ms, header ms; PASS/FAIL against the 2 s gate>, or "not run yet".
- 2026-09-29 · Owed (3): premium uses the inline header until slice 4's pre-reply call (note 22 §5); an afterthought needs mind.bonds on (the side call); a header written after the reply is streamed before it is removed from the saved text; the thought's share of the reply budget (response cap 600) is not reserved.
```

- [ ] **Step 2: Run the gate**

Run (repo root): `corepack pnpm check`
Expected: engine lint, format, tests and the app typecheck all pass.

- [ ] **Step 3: Commit**

```bash
git add docs/specs/2026-09-29-minds.md
git commit -m "docs: minds slice 3 landed"
```

- [ ] **Step 4: Tell the UI agent** (through the owner) that §8.3's slice-3 contract is live: `mind.thought` in `/features`, `done.thought`, `people[].thought` for Peek ("Thought" when `from` is `before`, "Afterthought" otherwise), the `thought` and `intent` Mind nodes, and that `thought` SSE events now also stream a character's thought on non-reasoning models.

---

## After this plan

Slice 3 goes up as one PR as the bot, per AGENTS.md (no migration, no billing code: it may merge when green). The screenshot or transcript for the owner is the `thought` probe's output: Peek's "Don't look at the ring" before a deflecting reply, and the Mind graph's gold thought → intent → spoke. Next: slice 4 ("She lies to protect a secret"), whose gated pre-reply side call gives premium its thought.
