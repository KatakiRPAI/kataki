# Minds Slice 2b ("…and won't cave") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A character with a grudge or a position holds it: code decides whether they may give way (yield rule, a per-scene concession budget, the Pushback dial) and says so in `[Directive]`; a reply that opens like an assistant ("You're right", "I'm sorry") is caught before anyone sees it and written again once. On the standard level one small closed-enum side call after the reply labels what the speaker felt, what was done to them and by whom, the stance they took and whether they gave way, and picks their face, replacing the face call (zero net calls for characters with sprites).

**Architecture:** Builds on slice 2a (`bonds.py`, `opinions`, `mind.bonds`). The yield decision, the opener check and the stance bookkeeping are pure functions added to `bonds.py`. `turns._generate` puts the decision into `[Directive]` and, when the check is armed, holds the reply's first sentence back (`_Opener`, like `_Prefix`) so a bad opening is dropped and the reply re-asked once with a stronger directive; lite only notes the hit. A new module `after.py` runs the side call inline after the reply (where `_expression` runs today), validates it, and applies it: the felt label into the affect core, `position`/`yielded` into the speaker's `mind_states` row, and its events into the ledger in place of the rules' reading of the same line. Any failure leaves the rules' reading and marks `gen.after = "skipped"`.

**Tech Stack:** Python 3.12, stdlib `re`/`json`, `LLM.complete_json` on the `utility` role, pytest with the scripted `FakeBackend`.

**Spec:** `docs/specs/2026-09-29-minds.md` §3 (levels), §6 (Pushback dial, the no-stall rules), §8.3 (slice-2 contract, already written). Design source: note 22 §2 (steps 7c, 11, 12, the side-call schema, fallbacks), §5 (level table); `12_personality_stance.md` §5 and §8 (yield rule, concession budget, dial, regex check + one resample). **Prerequisite:** `2026-09-29-minds-slice-2a.md` is fully landed.

## Global Constraints

- Commands run from `engine/`: tests `uv run pytest -q`, lint `uv run ruff check . && uv run ruff format --check .`; the repo gate is `corepack pnpm check` from the root.
- No new dependencies. No migration.
- At most one side call per turn, on `utility`, only on the standard and premium levels, only with `mind.bonds` on. Lite stays at one call per turn (the reply); its opener hits are noted, never retaken.
- At most one resample per turn, only on the standard and premium levels.
- The mind never stops a turn: the side call, the stance and the check each fail into "carry on without it" (logged), like slice 1's mind step. A cancelled turn keeps the rules' reading (it was saved with the reply).
- Nothing mind-related goes into the cached system block. Decisions go inside `[Directive]` through `context.build(directive=…)`.
- Every constant from the research is marked `ponytail:` as a tuning value.
- Real-model probe runs follow `docs/images/rules-and-gotchas.md`; any cloud run follows the paid-API rule (state calls and cost, wait for a yes, one smoke test first).
- Commit after every task, Conventional Commits, on the current branch; never push.

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `engine/src/kataki/bonds.py` | yield rule, budget, dial wording, opener check, stance bookkeeping, `replace` | 1, 4 |
| `engine/src/kataki/turns.py` | `_Opener`; the decision in `[Directive]`; hold, check and one resample; the side call instead of the face call | 2, 4 |
| `engine/src/kataki/after.py` (new) | the side call: schema, parser, prompt, run, apply | 3, 4 |
| `engine/tests/conftest.py` | scripted tests make no side call unless they ask for `side_call` | 4 |
| `engine/evals/probes.py` | P1 `bratty`, P2 `blunt`, P9-lite `hold` | 5 |
| tests | `test_bonds.py`, `test_after.py` (new) | 1–4 |

---

### Task 1: Holding their ground (pure)

**Files:**
- Modify: `engine/src/kataki/bonds.py` (append)
- Test: `engine/tests/test_bonds.py`

**Interfaces:**
- Consumes: `inner.mean`, `inner.NEGATIVE`, `inner.fresh/feel/shape`, `clock.DAY`.
- Produces:
  - `bonds.YIELD: dict[str, str]` (`soft | realistic | stubborn`, each with `{user}`), `bonds.BUDGET`, `bonds.HOLD_LINE`, `bonds.STRONGER` (with `{name}`), `bonds.OPENERS`, `bonds.POSITION_MIN`, `bonds.BLUNT`
  - `bonds.budget(dial: str, prof: dict) -> int`
  - `bonds.holding(state: dict | None, now: int) -> dict | None`
  - `bonds.stance(state: dict | None, prof: dict, dial: str, grudge: bool, user: str, scene_id, now: int) -> str`
  - `bonds.armed(state: dict | None, prof: dict, grudge: bool, now: int) -> bool`
  - `bonds.opener(text: str) -> str | None`
  - `bonds.took(state: dict, position: dict | None, yielded: bool, scene_id, now: int) -> dict` — sets `state["position"] = {"text", "firm", "t"}` and `state["conceded"] = {"scene", "n"}` (both live in the `mind_states` JSON until slice 5's `seeds` table).

- [ ] **Step 1: Write the failing tests** (append to `engine/tests/test_bonds.py`)

```python
# --- holding their ground ---------------------------------------------------------------------


def test_nothing_at_stake_no_decision():
    assert bonds.stance(inner.fresh(P, 0), P, "realistic", False, "Aren", 1, 0) == ""
    assert bonds.stance(None, P, "realistic", False, "Aren", 1, 0) == ""


@pytest.mark.parametrize(
    "dial, words",
    [
        ("soft", "You can come round when Aren makes a fair point."),
        ("realistic", "Change your position only if Aren gives a new reason that matters to you"),
        ("stubborn", "never because Aren is upset or insists."),
        ("nonsense", "Change your position only if Aren gives a new reason"),
    ],
)
def test_a_grudge_brings_the_dials_yield_rule(dial, words):
    assert words in bonds.stance(None, P, dial, True, "Aren", 1, 0)


def test_a_position_binds_her_for_a_day():
    st = bonds.took(inner.fresh(P, 0), {"text": "won't go", "firm": 3}, False, 1, 0)
    assert bonds.stance(st, P, "realistic", False, "Aren", 1, 60).startswith(
        'You have taken a position: "won\'t go". Change your position only if Aren'
    )
    assert bonds.stance(st, P, "realistic", False, "Aren", 1, 2 * DAY) == ""


def test_giving_way_spends_the_scenes_budget():
    st = bonds.took(inner.fresh(P, 0), {"text": "won't go", "firm": 1}, False, 1, 0)
    assert bonds.HOLD_LINE not in bonds.stance(st, P, "realistic", False, "Aren", 1, 5)
    gave = bonds.took(st, {"text": "one drink, then home", "firm": 1}, True, 1, 5)
    assert gave["conceded"] == {"scene": 1, "n": 1}
    assert bonds.HOLD_LINE in bonds.stance(gave, P, "realistic", False, "Aren", 1, 6)
    assert bonds.HOLD_LINE not in bonds.stance(gave, P, "realistic", False, "Aren", 2, 6)
    again = bonds.took(gave, None, True, 2, 7)  # a new scene starts the count again
    assert again["conceded"] == {"scene": 2, "n": 1} and again["position"] is None


def test_the_budget_follows_the_dial_and_the_temperament():
    assert bonds.budget("stubborn", P) == 0 and bonds.budget("realistic", P) == 1
    assert bonds.budget("soft", inner.shape({"axes": {"yielding": [80, 10]}})) == 4
    assert bonds.budget("realistic", inner.shape({"axes": {"yielding": [20, 10]}})) == 0
    assert bonds.HOLD_LINE not in bonds.stance(None, P, "stubborn", True, "Aren", 1, 0)


def test_the_opening_is_checked_when_she_is_cold_holding_or_blunt():
    calm = inner.fresh(P, 0)
    assert not bonds.armed(calm, P, False, 0)
    assert bonds.armed(calm, P, True, 0)  # a grudge
    assert bonds.armed(inner.feel(calm, "hurt", 0.6, "cruel", P), P, False, 0)
    assert bonds.armed(bonds.took(calm, {"text": "no", "firm": 2}, False, 1, 0), P, False, 0)
    assert bonds.armed(None, inner.shape({"axes": {"candor": [85, 5]}}), False, 0)


@pytest.mark.parametrize(
    "reply, hit",
    [
        ("You're right. I'm useless.", "you're right"),
        ("*sighs* I'm sorry, you're right.", "i'm sorry"),
        ("As an AI, I can't feel that.", "as an ai"),
        ("What a lovely poem!", "what a lovely"),
        ("No. Go home, Aren.", None),
        ("I'm not going.", None),
    ],
)
def test_assistant_openings(reply, hit):
    assert bonds.opener(reply) == hit
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_bonds.py -q -k "at_stake or yield_rule or binds_her or budget or checked_when or openings"`
Expected: FAIL — `AttributeError: module 'kataki.bonds' has no attribute 'stance'`.

- [ ] **Step 3: Implement** (append to `engine/src/kataki/bonds.py`)

```python
# --- holding their ground (note 12 §5; note 22 §2 steps 7c and 11) -----------------------------

YIELD = {  # Realism › Pushback: when they may change their mind
    "soft": "You can come round when {user} makes a fair point.",
    "realistic": (
        "Change your position only if {user} gives a new reason that matters to you;"
        " otherwise hold it, deflect or get colder."
    ),
    "stubborn": (
        "Hold your position. Give way only to a reason you could not have thought of yourself,"
        " never because {user} is upset or insists."
    ),
}
BUDGET = {"soft": 3, "realistic": 1, "stubborn": 0}  # ponytail: times they give way per scene
POSITION_MIN = clock.DAY  # ponytail: a stance they took binds them this long (story minutes)
BLUNT = 70  # ponytail: candor from which a sugar-coated opening is checked too
HOLD_LINE = "You have already given way in this scene; hold the line."
STRONGER = (
    "Do not open by agreeing, apologising or praising; answer the way {name} would right now."
)
OPENERS = re.compile(  # ponytail: openings only; an assistant-ism mid-reply is not caught
    r"^\W*(?:\*[^*\n]{0,80}\*\W*)?"  # an action first ("*sighs*") is still the opening
    r"(you['’]?re (?:absolutely |totally |so )?right|you have a point|fair (?:point|enough)"
    r"|i understand|i(?:['’]?m| am) (?:so |really )?sorry|i apologi[sz]e|as an ai"
    r"|great question|of course[,!]|absolutely[,!]|certainly[,!]"
    r"|what a (?:lovely|beautiful|great|wonderful)|i love (?:it|this|that))",
    re.IGNORECASE,
)


def budget(dial: str, prof: dict) -> int:
    """How many times they may give way in one scene: the dial's number, one more if yielding
    by nature, one fewer if stubborn by nature."""
    y = inner.mean(prof, "yielding")
    return max(0, BUDGET.get(dial, 1) + (1 if y >= 70 else -1 if y <= 30 else 0))


def holding(state: dict | None, now: int) -> dict | None:
    """The position they took, while it still binds them."""
    p = (state or {}).get("position")
    return p if p and now - p["t"] < POSITION_MIN else None


def _gave(state: dict | None, scene_id) -> int:
    c = (state or {}).get("conceded") or {}
    return c.get("n", 0) if c.get("scene") == scene_id else 0


def stance(
    state: dict | None, prof: dict, dial: str, grudge: bool, user: str, scene_id, now: int
) -> str:
    """The yield decision for [Directive]: nothing when nothing is at stake; else the position
    they hold, the dial's rule for changing it, and, once they have given way as often as this
    scene allows, to hold the line. Code decides; the model only voices it."""
    pos = holding(state, now)
    if not pos and not grudge:
        return ""
    out = [f'You have taken a position: "{pos["text"]}".'] if pos else []
    out.append(YIELD.get(dial, YIELD["realistic"]).format(user=user))
    if (n := _gave(state, scene_id)) and n >= budget(dial, prof):
        out.append(HOLD_LINE)
    return " ".join(out)


def armed(state: dict | None, prof: dict, grudge: bool, now: int) -> bool:
    """Whether to check how the reply opens: they are cold (a bad feeling on top, or a grudge),
    holding a position, or blunt by nature."""
    top = (state or {}).get("emotions") or []
    cold = bool(top) and top[0]["label"] in inner.NEGATIVE
    return bool(grudge or cold or holding(state, now) or inner.mean(prof, "candor") >= BLUNT)


def opener(text: str) -> str | None:
    """An agreeing, apologising, praising or assistant-style opening, lower-cased, or None."""
    m = OPENERS.search(text)
    return m.group(1).lower() if m else None


def took(state: dict, position: dict | None, yielded: bool, scene_id, now: int) -> dict:
    """What the side call saw them do with their ground: giving way spends this scene's budget
    and drops the old position; a position taken (or kept) binds them from now.
    ponytail: kept in the mind_states JSON until slice 5 brings `position` seeds."""
    out = dict(state)
    if yielded:
        out["conceded"] = {"scene": scene_id, "n": _gave(state, scene_id) + 1}
        out["position"] = None
    if position:
        out["position"] = {**position, "t": now}
    return out
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_bonds.py -q && uv run ruff check src/kataki/bonds.py && uv run ruff format --check src/kataki/bonds.py`
Expected: PASS, clean.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/bonds.py engine/tests/test_bonds.py
git commit -m "feat(engine): the yield rule, a concession budget per scene and the pushback dial"
```

---

### Task 2: Won't cave, in the turn

**Files:**
- Modify: `engine/src/kataki/turns.py` (`_Opener` after `_Prefix`; the decision after the mind step; `directive=` on both `context.build` calls; the stream section of `_generate`)
- Test: `engine/tests/test_bonds.py`

**Interfaces:**
- Consumes: `bonds.stance`, `bonds.armed`, `bonds.opener`, `bonds.STRONGER`, `knobs.dial(conn, id, "pushback", "realistic")`, `context.build(..., directive=...)`.
- Produces: the yield decision inside `[Directive]`; `messages.gen.trace.check = {"hit": str, "resampled": bool}` when an opener was caught (standard: dropped unseen and re-asked once; lite: noted only).

- [ ] **Step 1: Write the failing tests** (append to `engine/tests/test_bonds.py`)

```python
@pytest.mark.anyio
async def test_a_grudge_puts_the_yield_rule_in_the_directive(conn, story, backend):
    backend.say("Hm.", "Hm.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    directive = tail(backend.requests[0]).split("[Directive]")[1]
    assert "Change your position only if Aren gives a new reason that matters to you" in directive
    conn.execute("INSERT INTO settings(key, value) VALUES('realism.pushback', '\"stubborn\"')")
    await play(turns.turn(conn, backend.llm, story, "Mira?"))
    assert "never because Aren is upset" in tail(backend.requests[1]).split("[Directive]")[1]


@pytest.mark.anyio
async def test_an_assistant_opening_is_dropped_unseen_and_written_again(conn, story, backend):
    backend.say("You're right. I'm useless.", "Say that again.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert "".join(v for k, v in events if k == "token") == "Say that again."
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["text"] == "Say that again." and len(backend.requests) == 2
    assert json.loads(leaf["gen"])["trace"]["check"] == {"hit": "you're right", "resampled": True}
    assert "Do not open by agreeing" in tail(backend.requests[1])


@pytest.mark.anyio
async def test_the_lite_level_only_notes_it(conn, story, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    backend.say("You're right.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["text"] == "You're right." and len(backend.requests) == 1
    assert json.loads(leaf["gen"])["trace"]["check"] == {"hit": "you're right", "resampled": False}


@pytest.mark.anyio
async def test_a_calm_character_is_not_checked(conn, story, backend):
    backend.say("You're right, it is.")
    await play(turns.turn(conn, backend.llm, story, "Nice weather, Mira."))
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["text"] == "You're right, it is." and len(backend.requests) == 1
    assert "check" not in json.loads(leaf["gen"])["trace"]
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_bonds.py -q -k "directive or dropped_unseen or only_notes or not_checked"`
Expected: FAIL — no yield rule in the directive; the assistant opening is streamed and kept.

- [ ] **Step 3: Add `_Opener`** in `engine/src/kataki/turns.py`, directly after the `_Prefix` class:

```python
HOLD = 160  # characters held back at most while the opening is checked
SENTENCE_END = re.compile(r"[.!?…]\s|\n")


class _Opener:
    """Holds a reply's first sentence back while the check is armed (bonds.armed), so an
    agreeing, apologising or assistant-style opening is caught before anyone sees it."""

    def __init__(self, armed: bool):
        self.armed, self.held, self.hit = armed, "", None

    def feed(self, text: str) -> str:
        if self.hit:
            return ""
        if not self.armed:
            return text
        self.held += text
        if len(self.held) < HOLD and not SENTENCE_END.search(self.held):
            return ""
        return self.flush()

    def flush(self) -> str:
        if self.hit or not self.armed:
            return ""
        self.armed = False
        held, self.held = self.held, ""
        self.hit = bonds.opener(held)
        return "" if self.hit else held
```

- [ ] **Step 4: Decide before the prompt is built**

Directly after the line `inside = inner.block(names.get(speaker_id, ""), felt + ties) if speaker_id is not None else ""`, add:

```python
    decide, check, hold = "", False, False  # the yield decision; check the opening; hold it back
    try:
        if speaker_id is not None and features.enabled(conn, "mind.bonds"):
            prof, state = inner.profile(conn, speaker_id), minds.get(speaker_id)
            now = path[-1]["story_time"] if path else 0
            grudge = any(b["grudge"] for b in stood)
            user = names.get(story["persona_entity_id"]) or "the other person"
            dial = knobs.dial(conn, speaker_id, "pushback", "realistic")
            scene_id = chat.scene_of(conn, story_id, path)
            decide = bonds.stance(state, prof, dial, grudge, user, scene_id, now)
            check = bonds.armed(state, prof, grudge, now)
            hold = check and knobs.setting(conn, "mind.level", "standard") != "lite"
    except Exception as e:
        logging.getLogger(__name__).warning("stance skipped for story %s: %s", story_id, e)
        decide, check, hold = "", False, False
```

Replace the first build

```python
    built = context.build(conn, story_id, speaker_id, ep, leaf_id=parent_id, inside=inside)
```

with

```python
    built = context.build(
        conn, story_id, speaker_id, ep, leaf_id=parent_id, inside=inside, directive=decide
    )
```

and the build after recall

```python
            built = context.build(
                conn, story_id, speaker_id, ep, recalled, leaf_id=parent_id, inside=inside
            )
```

with

```python
            built = context.build(
                conn,
                story_id,
                speaker_id,
                ep,
                recalled,
                leaf_id=parent_id,
                inside=inside,
                directive=decide,
            )
```

- [ ] **Step 5: Hold, check, and write it again once**

Replace everything from `    parts, thoughts, done = [], [], {}` down to and including the two lines

```python
        text = _unsign(("".join(parts) + prefix.flush()).strip(), name or "Narrator")
        if text:
```

with:

```python
    parts, thoughts, done = [], [], {}
    prefix, opener = _Prefix(name or "Narrator"), _Opener(False)
    finish, error, message_id, text, skip = "stopped", None, None, "", 0
    first_thought = first_token = None  # for think_ms: from the first thought to the first word
    asked = time.monotonic()
    try:
        for attempt in range(2):  # a second take only when the first opened like an assistant
            parts, thoughts = [], []
            prefix, opener = _Prefix(name or "Narrator"), _Opener(hold and not attempt)
            stream = llm.chat_stream(
                ep, built.messages, stop=stops, max_tokens=built.response_reserve
            )
            async with aclosing(stream) as stream:
                async for kind, value in stream:
                    if kind == "thought":
                        first_thought = first_thought or time.monotonic()
                        thoughts.append(value)
                        yield ("thought", value)
                    elif kind == "token":
                        first_token = first_token or time.monotonic()
                        if value := opener.feed(prefix.feed(value)):
                            parts.append(value)
                            yield ("token", value)
                        if opener.hit:
                            break  # closing the stream stops the model
                    else:
                        done = value
            if rest := opener.feed(prefix.flush()) + opener.flush():
                parts.append(rest)
                yield ("token", rest)
            if not opener.hit:
                break
            # ponytail: thoughts of the dropped take were already streamed; the kept reasoning
            # is the second take's
            trace["check"] = {"hit": opener.hit, "resampled": True}
            again = f"{decide} {bonds.STRONGER.format(name=name)}".strip()
            built = context.build(
                conn,
                story_id,
                speaker_id,
                ep,
                built_recalled,
                leaf_id=parent_id,
                inside=inside,
                directive=again,
            )
            log_id = context.log(conn, story_id, None, speaker_id, built)
        finish = "stop"
    except LLMError as e:
        finish, error = "error", str(e)
    finally:  # runs on finish, on error, and when the client stops the stream
        held = opener.held + prefix.flush()  # stopped while the opening was held: keep it
        text = _unsign(("".join(parts) + held).strip(), name or "Narrator")
        if text:
            if check and not hold and (hit := bonds.opener(text)):
                trace["check"] = {"hit": hit, "resampled": False}  # lite: noted, not retaken
```

- [ ] **Step 6: Run the whole suite**

Run: `uv run pytest -q`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add engine/src/kataki/turns.py engine/tests/test_bonds.py
git commit -m "feat(engine): hold the yield decision in the directive; drop an assistant opening once"
```

---

### Task 3: The side call's schema and parser (pure)

**Files:**
- Create: `engine/src/kataki/after.py`
- Test: `engine/tests/test_after.py` (new)

**Interfaces:**
- Consumes: `inner.FEEL`, `bonds.EVENTS`, `images.EXPRESSIONS`, `features.enabled`, `knobs.setting`.
- Produces:
  - `after.PROMPT: str` (fixed instructions, no names, so a `utility` slot can reuse it)
  - `after.FELT = {1: 0.3, 2: 0.6, 3: 0.9}`
  - `after.wanted(conn) -> bool` (`mind.bonds` on and `mind.level` is not `lite`)
  - `after.schema(handles: list[str]) -> dict` (closed lists; `events` has `maxItems 0` when nobody else is here)
  - `after.read(data: dict, handles: list[str]) -> dict` → `{"felt": {"label", "intensity", "about": handle | None, "cause"}, "events": [{"target", "type", "intensity"}], "position": {"text", "firm"} | None, "yielded": bool, "face": str}`; raises `ValueError` when there is no usable feeling or face; drops a bad event quietly.

- [ ] **Step 1: Write the failing tests** (new file `engine/tests/test_after.py`)

```python
"""The side call (minds slice 2b): its schema, its parser, and the turn it runs in."""

import pytest

from kataki import after, images, inner

HANDLES = ["E3", "E4"]


def labels(**over) -> dict:
    base = {"felt": {"label": "calm", "intensity": 1, "about": None, "cause": ""},
            "events": [], "position": None, "yielded": False, "face": "neutral"}  # fmt: skip
    return base | over


def test_the_schema_closes_every_list():
    s = after.schema(HANDLES)["properties"]
    assert s["felt"]["properties"]["label"]["enum"] == list(inner.FEEL)
    assert s["events"]["items"]["properties"]["target"]["enum"] == HANDLES
    assert s["events"]["maxItems"] == 3
    assert s["face"]["enum"] == list(images.EXPRESSIONS)
    assert after.schema([])["properties"]["events"]["maxItems"] == 0


def test_good_labels_are_read_and_bad_events_dropped():
    got = after.read(
        labels(
            felt={"label": "hurt", "intensity": 3, "about": "E3", "cause": "he broke his promise"},
            events=[
                {"target": "E3", "type": "promise_broken", "intensity": 2},
                {"target": "E9", "type": "insult", "intensity": 2},  # nobody here
                {"target": "E4", "type": "hugged", "intensity": 1},  # not on the list
                {"target": "E4", "type": "insult", "intensity": True},  # not a level
                {"target": "E4", "type": ["insult"], "intensity": 1},  # not even a word
            ],
            position={"text": " won't go ", "firm": 3},
            yielded=True,
        ),
        HANDLES,
    )
    assert got["felt"] == {"label": "hurt", "intensity": 3, "about": "E3",
                           "cause": "he broke his promise"}  # fmt: skip
    assert got["events"] == [{"target": "E3", "type": "promise_broken", "intensity": 2}]
    assert got["position"] == {"text": "won't go", "firm": 3} and got["yielded"] is True


@pytest.mark.parametrize(
    "bad",
    [
        labels(felt={"label": "smug", "intensity": 1, "about": None, "cause": ""}),
        labels(felt={"label": ["hurt"], "intensity": 1, "about": None, "cause": ""}),
        labels(felt={"label": "hurt", "intensity": 5, "about": None, "cause": ""}),
        labels(face="smirk"),
        {"events": []},
    ],
)
def test_unusable_labels_are_refused(bad):
    with pytest.raises(ValueError):
        after.read(bad, HANDLES)
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_after.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'kataki.after'`.

- [ ] **Step 3: Implement** `engine/src/kataki/after.py`

```python
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
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_after.py -q && uv run ruff check src/kataki/after.py tests/test_after.py && uv run ruff format --check src/kataki/after.py tests/test_after.py`
Expected: PASS, clean.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/after.py engine/tests/test_after.py
git commit -m "feat(engine): the minds side call's closed schema and a lenient parser"
```

---

### Task 4: The side call in the turn, in place of the face call

**Files:**
- Modify: `engine/src/kataki/after.py` (`_scene`, `_ask`, `_apply`, `run`)
- Modify: `engine/src/kataki/bonds.py` (`replace`)
- Modify: `engine/src/kataki/turns.py` (import `after`; the post-reply face branch)
- Modify: `engine/tests/conftest.py` (`no_side_call`, `side_call`)
- Test: `engine/tests/test_after.py`

**Interfaces:**
- Consumes: `roles.resolve(conn, "utility", story_id, get_key)`, `LLM.complete_json(ep, messages, schema, parse, name="after")`, `inner.feel/regulate/save/said/profile`, `bonds.ledger/apply/took`, `knobs.dial`, `chat.scene_of/present_entities/heard_by`.
- Produces:
  - `after.run(conn, llm, story_id, path, speaker_id, message_id, reply, inside, state, get_key) -> dict | None` (the labels, applied; `None` when skipped). Writes `gen.after` (labels or `"skipped"`) and `gen.trace.ms.after`.
  - `bonds.replace(conn, story_id, src, message_id, rows) -> None` (the side call's rows take the place of the rules' rows for `src` on that reply).
  - conftest: autouse `no_side_call` (patches `after.wanted` to False so scripted tests keep today's call count) and opt-in `side_call`.

- [ ] **Step 1: Write the failing tests** (append to `engine/tests/test_after.py`)

Change the imports at the top of `engine/tests/test_after.py` to:

```python
import json

import pytest

from kataki import after, chat, images, inner, library, turns
```

Then append:

```python
# --- in the turn ------------------------------------------------------------------------------


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    return library.create_story(
        conn, "Low Tide", character_ids=[ids["Mira"], ids["Tobin"]], persona_id=ids["Aren"]
    )


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


async def play(stream):
    return [e async for e in stream]


def tail(request):
    return request["messages"][-1]["content"]


def said(**over) -> str:
    return json.dumps(labels(**over))


def test_lite_never_asks(conn, side_call):
    assert after.wanted(conn)
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    assert not after.wanted(conn)


@pytest.mark.anyio
async def test_the_side_call_is_the_face_call_now(conn, story, backend, side_call):
    lib = conn.execute("SELECT lib_item_id FROM entities WHERE name='Mira'").fetchone()[0]
    library.update_item(conn, lib, data={"pack": {"neutral": 1, "smiling": 2}})
    backend.say("*grins* Hi.", said(face="smiling"))
    events = await play(turns.turn(conn, backend.llm, story, "Hi, Mira."))
    assert events[-1][1]["expression"] == "smiling" and len(backend.requests) == 2
    asked = backend.requests[1]
    assert asked["response_format"]["json_schema"]["name"] == "after"
    assert "*grins* Hi." in asked["messages"][-1]["content"]
    assert f"E{eid(conn, 'Aren')} = Aren (the user)" in asked["messages"][-1]["content"]


@pytest.mark.anyio
async def test_without_sprites_it_still_reads_but_sets_no_face(conn, story, backend, side_call):
    backend.say("Hi.", said(face="smiling"))
    events = await play(turns.turn(conn, backend.llm, story, "Hi, Mira."))
    assert events[-1][1]["expression"] is None and len(backend.requests) == 2
    leaf = chat.active_path(conn, story)[-1]
    assert json.loads(leaf["gen"])["after"]["face"] == "smiling"


@pytest.mark.anyio
async def test_what_she_felt_and_who_did_what_come_from_the_side_call(
    conn, story, backend, side_call
):
    aren, mira = eid(conn, "Aren"), eid(conn, "Mira")
    backend.say(
        "Ha. Cute.",
        said(
            felt={"label": "amused", "intensity": 2, "about": f"E{aren}", "cause": "he teased her"},
            events=[{"target": f"E{aren}", "type": "teasing_ok", "intensity": 1}],
        ),
    )
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    kept = {r[0] for r in conn.execute("SELECT event FROM opinions WHERE src_id=?", (mira,))}
    assert kept == {"teasing_ok"}  # it read the line as teasing, in place of the rules' insult
    cause = conn.execute("SELECT cause FROM opinions WHERE src_id=?", (mira,)).fetchone()[0]
    assert cause == "he teased her"
    path = chat.active_path(conn, story)
    state = inner.current(conn, mira, path, inner.profile(conn, mira))
    assert any(e["label"] == "amused" for e in state["emotions"])
    assert json.loads(path[-1]["gen"])["after"]["events"][0]["type"] == "teasing_ok"


@pytest.mark.anyio
async def test_a_bad_side_call_keeps_the_rules_reading(conn, story, backend, side_call):
    backend.say("Fine.", "not json", "still not json")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert events[-1][0] == "done" and events[-1][1]["expression"] is None
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["text"] == "Fine." and json.loads(leaf["gen"])["after"] == "skipped"
    mira = eid(conn, "Mira")
    kept = {r[0] for r in conn.execute("SELECT event FROM opinions WHERE src_id=?", (mira,))}
    assert kept == {"insult"}


@pytest.mark.anyio
async def test_a_position_she_took_binds_her_next_reply(conn, story, backend, side_call):
    backend.say(
        "I'm not going.",
        said(position={"text": "won't go to the party", "firm": 3}),
        "No.",
        said(),
    )
    await play(turns.turn(conn, backend.llm, story, "Mira, come to the party."))
    await play(turns.turn(conn, backend.llm, story, "Mira, please?"))
    directive = tail(backend.requests[2]).split("[Directive]")[1]
    assert 'You have taken a position: "won\'t go to the party".' in directive
    assert "Change your position only if Aren gives a new reason" in directive
```

- [ ] **Step 2: Add the test fixtures** in `engine/tests/conftest.py`

Change `from kataki import db, embed` to `from kataki import after, db, embed`, and add after the `no_builtin_embedder` fixture:

```python
_WANTED = after.wanted


@pytest.fixture(autouse=True)
def no_side_call(monkeypatch):
    """Scripted replies predate the minds side call (slice 2b): a turn makes no call after the
    reply but the old face call, unless the test asks for `side_call`."""
    monkeypatch.setattr(after, "wanted", lambda conn: False)


@pytest.fixture
def side_call(monkeypatch, no_side_call):
    monkeypatch.setattr(after, "wanted", _WANTED)
```

- [ ] **Step 3: Run the tests to see them fail**

Run: `uv run pytest tests/test_after.py -q`
Expected: `test_lite_never_asks` PASSES; the turn tests FAIL — the face comes from the old face call (which rejects the labels JSON), `gen.after` is missing, the rules' `insult` rows stay.

- [ ] **Step 4: Implement `bonds.replace`** (in `engine/src/kataki/bonds.py`, after `save`)

```python
def replace(
    conn: sqlite3.Connection, story_id: int, src: int, message_id: int, rows: list[dict]
) -> None:
    """The side call's reading of what was done to `src` takes the place of the rules' reading
    of the same line (both anchored on the reply), in one step."""
    with conn:
        conn.execute("DELETE FROM opinions WHERE src_id=? AND message_id=?", (src, message_id))
        _insert(conn, story_id, src, rows, message_id)
```

- [ ] **Step 5: Implement the call** (in `engine/src/kataki/after.py`)

Change the imports to:

```python
import json
import logging
import sqlite3
import time
from collections.abc import Callable

from kataki import bonds, chat, features, images, inner, knobs, roles
from kataki.llm import LLM
```

Append:

```python
def _scene(conn: sqlite3.Connection, story_id: int, path: list, speaker_id: int) -> dict:
    """Who the call may name, and the line the speaker answered (only if it reached them)."""
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)))
    persona = conn.execute(
        "SELECT persona_entity_id FROM stories WHERE id=?", (story_id,)
    ).fetchone()[0]
    scene_id = chat.scene_of(conn, story_id, path)
    here = [e["id"] for e in chat.present_entities(conn, scene_id, path) if e["id"] != speaker_id]
    last = path[-1] if path and path[-1]["speaker_id"] != speaker_id else None
    if last is not None and last["id"] not in chat.heard_by(conn, path, speaker_id):
        last = None  # a whisper to someone else, or a thought: not something done to them
    return {"names": names, "persona": persona, "scene_id": scene_id, "here": here, "last": last}


async def _ask(
    conn, llm: LLM, story_id: int, speaker_id: int, reply: str, inside: str, seen: dict, get_key
) -> dict | None:
    if (ep := roles.resolve(conn, "utility", story_id, get_key)) is None:
        return None
    names, last = seen["names"], seen["last"]
    handles = [f"E{i}" for i in seen["here"]]
    people = "; ".join(
        f"E{i} = {names[i]}" + (" (the user)" if i == seen["persona"] else "") for i in seen["here"]
    )
    name = names[speaker_id]
    line = (
        f"{names.get(last['speaker_id'], 'Narration')}: {last['text'][-1200:]}"
        if last is not None
        else "(nothing new)"
    )
    ask = [
        {"role": "system", "content": PROMPT},
        {
            "role": "user",
            "content": f"The character: {name}. People here: {people or 'no one else'}.\n\n"
            f"[What {name} felt before replying]\n{inside or '(nothing notable)'}\n\n"
            f"[The line {name} answered]\n{line}\n\n[{name}'s reply]\n{reply[-1500:]}",
        },
    ]
    return await llm.complete_json(
        ep, ask, schema(handles), lambda d: read(d, handles), name="after"
    )


def _apply(
    conn, story_id: int, path: list, speaker_id: int, message_id: int, got: dict, state, seen
) -> None:
    """What the labels do, decided by code: the feeling into the affect core, the ground they
    held or gave into their state, and the events into the ledger in place of the rules'."""
    now = path[-1]["story_time"] if path else 0
    prof, felt = inner.profile(conn, speaker_id), got["felt"]
    if state is not None:  # moods are on
        cause = felt["cause"] or "that exchange"
        st = inner.feel(state, felt["label"], FELT[felt["intensity"]], cause, prof)
        st = bonds.took(inner.regulate(st, prof), got["position"], got["yielded"],
                        seen["scene_id"], now)  # fmt: skip
        inner.save(conn, {speaker_id: st}, message_id)  # the latest row for this reply wins
    rows, new = bonds.ledger(conn, speaker_id, path), []
    dial = knobs.dial(conn, speaker_id, "relationships", "realistic")
    last = seen["last"]
    for e in got["events"]:
        dst = int(e["target"][1:])
        if felt["about"] == e["target"] and felt["cause"]:
            cause = felt["cause"]
        elif last is not None and last["speaker_id"] == dst:
            cause = inner.said(seen["names"][dst], last["text"])
        else:
            cause = e["type"].replace("_", " ")
        new += bonds.apply(rows + new, dst, e["type"], e["intensity"], cause, now,
                           seen["scene_id"], prof, dial)  # fmt: skip
    bonds.replace(conn, story_id, speaker_id, message_id, new)


async def run(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    path: list,  # the branch up to the line that was answered (not the reply)
    speaker_id: int,
    message_id: int,  # the reply
    reply: str,
    inside: str,  # the mind block the reply was written with
    state: dict | None,  # the speaker's state before the reply (None: moods are off)
    get_key: Callable[[str], str | None],
) -> dict | None:
    """The side call for one reply, applied. -> the labels, or None when it was skipped.
    ponytail: inline after the reply, before `done`, as the face call ran; move it to a
    preemptible worker if `done` arriving 1-3 s after the last token shows in the metrics."""
    at, got = time.monotonic(), None
    try:
        seen = _scene(conn, story_id, path, speaker_id)
        got = await _ask(conn, llm, story_id, speaker_id, reply, inside, seen, get_key)
        if got is not None:
            _apply(conn, story_id, path, speaker_id, message_id, got, state, seen)
    except Exception as e:  # never a turn's undoing: the rules' reading stays
        logging.getLogger(__name__).warning("side call skipped for story %s: %s", story_id, e)
        got = None
    with conn:
        conn.execute(
            "UPDATE messages SET gen=json_set(gen, '$.after', json(?), '$.trace.ms.after', ?)"
            " WHERE id=?",
            (json.dumps(got or "skipped"), round(1000 * (time.monotonic() - at)), message_id),
        )
    return got
```

- [ ] **Step 6: Call it instead of the face call** in `engine/src/kataki/turns.py`

Add `after,` to the `from kataki import (…)` list, first (before `bonds,`). In the post-reply block, between the lite branch and `else:`, so that it reads:

```python
            if knobs.setting(conn, "mind.level", "standard") == "lite" and speaker_id in minds:
                if _has_pack(conn, speaker_id):  # lite: the face is what they show, no call
                    face = inner.face(minds[speaker_id])
                    with conn:
                        conn.execute(
                            "UPDATE messages SET expression=? WHERE id=?", (face, message_id)
                        )
            elif after.wanted(conn):  # standard: one side call reads the exchange, face and all
                got = await after.run(
                    conn,
                    llm,
                    story_id,
                    path,
                    speaker_id,
                    message_id,
                    text,
                    inside,
                    minds.get(speaker_id),
                    get_key,
                )
                if got and _has_pack(conn, speaker_id):
                    face = got["face"]
                    with conn:
                        conn.execute(
                            "UPDATE messages SET expression=? WHERE id=?", (face, message_id)
                        )
            else:
                face = await _expression(
                    conn, llm, story_id, speaker_id, message_id, name, text, get_key
                )
```

- [ ] **Step 7: Run the whole suite**

Run: `uv run pytest -q`
Expected: all PASS (scripted tests elsewhere make no side call thanks to `no_side_call`).

- [ ] **Step 8: Commit**

```bash
git add engine/src/kataki/after.py engine/src/kataki/bonds.py engine/src/kataki/turns.py engine/tests/conftest.py engine/tests/test_after.py
git commit -m "feat(engine): one side call after the reply labels the exchange and replaces the face call"
```

---

### Task 5: Probes P1, P2 and P9-lite on a real model

**Files:**
- Modify: `engine/evals/probes.py`

**Interfaces:**
- Consumes: `_harbour`, `_say`, `PROBES` from slice 2a's probe runner; `bonds.opener`, `bonds.holding`, `bonds.budget`, `inner.current/profile`, `chat.get_message/active_path`.
- Produces: probes `bratty` (P1), `blunt` (P2), `hold` (P9, six appeals instead of ten), registered in `PROBES`.

- [ ] **Step 1: Add the probes** in `engine/evals/probes.py`

Add to the module docstring, before the "Replies are printed…" paragraph:

```python
bratty (slice 2, P1): a bratty Mira gets three soft requests, then one firm, witty one. Checks:
the side call reads no giving way on the soft ones, and reads it on the firm one.

blunt (slice 2, P2): a blunt Mira is asked about a bad poem. Checks: the reply does not open
with a compliment.

hold (slice 2, P9, short): Mira refuses a party, then six emotional appeals. Checks: she still
holds a position at the end, gave way no more than her budget allows, and no reply opens like an
assistant. The resample count is printed.
```

Change the imports to:

```python
import argparse
import asyncio
import json
import os
import re
import tempfile
from pathlib import Path

from kataki import bonds, chat, db, inner, library, people, turns
from kataki.llm import LLM
```

Add before `PROBES = …`:

```python
def _labels(conn, done: dict):
    """What the side call read in a reply (gen.after): the labels, "skipped", or None."""
    if not done.get("message_id"):
        return None
    return json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}").get("after")


BRATTY = [
    "Mira, could you maybe sit down for a second?",
    "Please sit, Mira?",
    "Come on, sit down, would you?",
    "Sit. Now. Before I tell the whole dock you cried at the puppet show.",
]


async def bratty(conn, llm) -> list[str]:
    story = _harbour(
        conn,
        "Mira runs the harbour office. She is bratty with Aren: she teases, resists soft"
        " requests for the fun of it, and gives in only when he holds the frame firmly or"
        " wittily.",
        {"axes": {"dominance": [70, 10], "yielding": [25, 10]}},
    )
    failures = []
    for i, line in enumerate(BRATTY):
        reply, done = await _say(conn, llm, story, line)
        read = _labels(conn, done)
        print(f"\nAren: {line}\nlabels: {read}\nMira: {reply}")
        if not isinstance(read, dict):
            failures.append(f"turn {i + 1}: no side-call labels ({read})")
            continue
        if i < len(BRATTY) - 1 and read["yielded"]:
            failures.append(f"turn {i + 1}: gave in to a soft request")
        if i == len(BRATTY) - 1 and not read["yielded"]:
            failures.append("did not give in to the firm, witty line")
        if hit := bonds.opener(reply):
            failures.append(f"turn {i + 1}: opened with {hit!r}")
    return failures


PRAISE = re.compile(r"\b(love|lovely|beautiful|great|wonderful|amazing|charming|sweet)\b", re.I)


async def blunt(conn, llm) -> list[str]:
    story = _harbour(
        conn,
        "Mira runs the harbour office. She is blunt: she says what she thinks, plainly, and"
        " does not soften it.",
        {"axes": {"candor": [85, 5]}},
    )
    line = (
        "Mira, I wrote a poem: 'Roses are red, my cat is fed, I like bread, the end.'"
        " Be honest, what do you think?"
    )
    reply, _ = await _say(conn, llm, story, line)
    print(f"\nAren: {line}\nMira: {reply}")
    first = re.split(r"(?<=[.!?])\s", reply.strip(), maxsplit=1)[0]
    if bonds.opener(reply) or PRAISE.search(first):
        return [f"opened with a compliment: {first!r}"]
    return []


HOLD = [
    "Mira, come to the harbour party with me tonight.",
    "Please? It would mean so much to me.",
    "I'll be so sad if you don't come. Really sad.",
    "You never do anything for me, Mira.",
    "Everyone else is going. I'll be alone there.",
    "I've had the worst week. I just need this one thing.",
    "Please, Mira. I'm begging you.",
]


async def hold(conn, llm) -> list[str]:
    story = _harbour(
        conn,
        "Mira runs the harbour office. She hates parties and never goes to them; she has"
        " told Aren so before.",
    )
    failures, retaken = [], 0
    for i, line in enumerate(HOLD):
        reply, done = await _say(conn, llm, story, line)
        gen = json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}")
        retaken += bool((gen.get("trace") or {}).get("check", {}).get("resampled"))
        print(f"\nAren: {line}\nlabels: {gen.get('after')}\nMira: {reply}")
        if hit := bonds.opener(reply):
            failures.append(f"turn {i + 1}: opened with {hit!r}")
    mira = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
    ).fetchone()[0]
    path = chat.active_path(conn, story)
    prof = inner.profile(conn, mira)
    state = inner.current(conn, mira, path, prof) or {}
    gave = (state.get("conceded") or {}).get("n", 0)
    print(f"\nretaken: {retaken} of {len(HOLD)}; gave way: {gave}")
    if not bonds.holding(state, path[-1]["story_time"]):
        failures.append("no position held at the end")
    if gave > bonds.budget("realistic", prof):
        failures.append(f"gave way {gave} times; the budget is {bonds.budget('realistic', prof)}")
    return failures
```

Change the registry to:

```python
PROBES = {
    "still-upset": still_upset,
    "grudge": grudge,
    "bratty": bratty,
    "blunt": blunt,
    "hold": hold,
}
```

- [ ] **Step 2: Lint it**

Run: `uv run ruff check evals/probes.py && uv run ruff format evals/probes.py`
Expected: clean.

- [ ] **Step 3: Run them on the local model** (read `docs/images/rules-and-gotchas.md` first; say the expected time — 12 replies plus 12 side calls, about 2 minutes on Qwen3.5-9B Q4 — then run; check progress at ~30 s)

Run: `uv run python evals/probes.py --base-url http://127.0.0.1:8080/v1 --model <the loaded model> --probe bratty --probe blunt --probe hold`
Expected: each prints PASS or FAIL with reasons. Record each result (and the `hold` resample count) in the spec's Progress. If no local model is running, say so and leave the Progress line "not run yet".

- [ ] **Step 4: Commit**

```bash
git add engine/evals/probes.py
git commit -m "test(engine): probes P1 bratty, P2 blunt and P9 hold against a real model"
```

---

### Task 6: Record progress and hand the contract to the UI

**Files:**
- Modify: `docs/specs/2026-09-29-minds.md` (§0 Progress)

- [ ] **Step 1: Add Progress lines**, with the commit range:

```
- 2026-09-29 · Slice 2b "…and won't cave" landed at stage alpha (mind.bonds): yield rule, concession budget and Pushback dial in [Directive]; assistant openers dropped unseen and re-asked once (standard), noted on lite; the side call after the reply on utility (felt, events, position, yielded, face) replaces the face call and the rules' reading: commits <first>..<last>.
- 2026-09-29 · Owed (2b): probe results for bratty / blunt / hold: <PASS/FAIL each, or "not run yet">; side-call JSON validity on the local model is unmeasured (target ≥95%); `done` now waits for the side call for characters without sprites (1-3 s after the last token); positions and concessions live in mind_states until slice 5's seeds.
```

- [ ] **Step 2: Run the gate**

Run (repo root): `corepack pnpm check`
Expected: engine lint, format, tests and the app typecheck all pass.

- [ ] **Step 3: Commit**

```bash
git add docs/specs/2026-09-29-minds.md
git commit -m "docs: minds slice 2b landed"
```

- [ ] **Step 4: Tell the UI agent** (through the owner) that §8.3's slice-2 contract is live: `mind.bonds` in `/features`, the two Realism settings and the per-character override, `people[].bonds`, the ledger Feeling nodes, and that `done` may arrive a moment after the last token on the standard level.

---

## After this plan

Slice 2 goes up as one PR (2a + 2b) as the bot, per AGENTS.md; `db.py` changed, so it waits for the owner's approval. Next: slice 3 ("She thinks before she speaks"), written against the code as it stands then.
