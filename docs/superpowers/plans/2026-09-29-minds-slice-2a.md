# Minds Slice 2a ("She holds a grudge") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every AI character keeps a relationship ledger toward each person, in code: a broken promise or an insult becomes a grudge that holds for weeks of story time, a hollow "I'm sorry" forgives nothing, a sincere apology turns it into slow recovery, and the character's mind block says all of it in words. Only the one a line is aimed at takes it personally. Zero model calls.

**Architecture:** A new pure module `bonds.py` holds the ledger maths (event table × personality multipliers, decay kinds on story time, grudges, repair, per-scene caps) and renders standings into words. Rows live in a new `opinions` table (migration v11), each anchored on the reply they were read before, so swipes and branches swap the ledger for free, exactly like `mind_states`. Events come from rules (`inner.sense` plus two regexes); slice 2b adds the side call that labels them on the standard level. `inner.targets` decides who a user line is aimed at, which also fixes slice 1's "everyone who heard it is insulted". Gated by the `mind.bonds` feature (stage alpha).

**Tech Stack:** Python 3.12, stdlib `sqlite3` and `re`, pytest with the scripted `FakeBackend` in `engine/tests/conftest.py`.

**Spec:** `docs/specs/2026-09-29-minds.md` §6 (dials, rules), §7 (slice 2 row), §8.3 (the slice-2 contract, already written). Design source: `docs/research/research_notes/Human like minds for Kataki/22_unified_architecture.md` §1 (`opinions` DDL, EVENT list), §4 (mind block row 3), §6 (C11, C16); `16_theory_of_mind_relationships.md` §5 and §9.3. The follow-up plan is `2026-09-29-minds-slice-2b.md` (side call, pushback, resample).

## Global Constraints

- Commands run from `engine/`: tests `uv run pytest -q`, lint `uv run ruff check . && uv run ruff format --check .`; the repo gate is `corepack pnpm check` from the root.
- No new dependencies.
- This plan claims migration **v11**. If `SCHEMA_VERSION` is already 11 when you start, use the next free number everywhere this plan says 11.
- Forward-only migration in `engine/src/kataki/db.py`, tested on a library from the previous version.
- Nothing goes into the cached system block. Relationship lines live in the mind block in the volatile tail (`inner.block`), inside the existing `mind` cap.
- The prompt gets words, never numbers, for any relationship state. The API may carry numbers.
- The mind never stops a turn: every mind step in `turns._generate` is inside its own `try/except Exception` that logs and carries on, like slice 1's.
- Every constant from the research is marked `ponytail:` as a tuning value.
- Commit after every task, Conventional Commits, on the current branch (`feat/minds-slice-2`); never push.
- Comment style matches the engine: short docstrings that say what and why.

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `engine/src/kataki/db.py` | v11 `opinions` table | 1 |
| `engine/src/kataki/chat.py` | `named`: who a line names, in order | 2 |
| `engine/src/kataki/turns.py` | `_addressed` uses `chat.named`; bonds in the turn | 2, 7 |
| `engine/src/kataki/inner.py` | `said`, `targets`, `react` aims; `social` defaults; `lines`/`block` | 2, 3, 6 |
| `engine/src/kataki/features.py` | `mind.bonds` | 3 |
| `engine/src/kataki/knobs.py` | `dial`: a Realism dial with the character's override | 3 |
| `engine/src/kataki/bonds.py` (new) | ledger maths, rule events, storage, words, API shape | 4, 5, 6 |
| `engine/src/kataki/people.py` | `people[].bonds` | 8 |
| `engine/src/kataki/mind.py` | Feeling node from the ledger | 8 |
| `engine/evals/probes.py` | probe runner by name; P4 `grudge` | 9 |
| tests | `test_db.py`, `test_archive.py`, `test_inner.py`, `test_minds.py`, `test_knobs.py`, `test_features.py`, `test_bonds.py` (new) | all |

---

### Task 1: Migration v11, the `opinions` ledger

**Files:**
- Modify: `engine/src/kataki/db.py` (`SCHEMA_VERSION`, `MIGRATIONS`)
- Test: `engine/tests/test_db.py`, `engine/tests/test_archive.py:135-143`

**Interfaces:**
- Produces: table `opinions(id, story_id, src_id, dst_id, dim, value, kind, half_life_min, event, cause, resolves_id, witnesses, story_time, message_id, run_id)` exactly as note 22 §1, with `CHECK(dim IN('closeness','trust','respect','attraction','dominance','familiarity','disclosed_in','disclosed_out'))` and `CHECK(kind IN('decay','sticky','permanent'))`; index `ix_opinions(src_id, dst_id)`.

- [ ] **Step 1: Write the failing test** (append to `engine/tests/test_db.py`)

```python
def test_v11_adds_the_relationship_ledger(tmp_path):
    path = tmp_path / "v10.db"
    old = db.connect(path)  # today's schema, then pretend it is v10 without the ledger
    old.executescript("DROP TABLE IF EXISTS opinions;")
    old.execute("PRAGMA user_version=10")
    old.commit()
    old.close()

    conn = db.connect(path)
    story = _story(conn)
    a, b = (
        conn.execute(
            "INSERT INTO entities(story_id, kind, name) VALUES(?, 'character', ?)", (story, n)
        ).lastrowid
        for n in ("Mira", "Aren")
    )
    conn.execute(
        "INSERT INTO opinions(story_id, src_id, dst_id, dim, value, kind, story_time)"
        " VALUES(?, ?, ?, 'trust', -8, 'sticky', 0)",
        (story, a, b),
    )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO opinions(story_id, src_id, dst_id, dim, value, kind, story_time)"
            " VALUES(?, ?, ?, 'love', 1, 'decay', 0)",
            (story, a, b),
        )
    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    conn.close()
```

- [ ] **Step 2: Run it to see it fail**

Run: `uv run pytest tests/test_db.py -q -k v11`
Expected: FAIL — `sqlite3.OperationalError: no such table: opinions`.

- [ ] **Step 3: Implement** in `engine/src/kataki/db.py`

Set `SCHEMA_VERSION = 11` and add to `MIGRATIONS` after `10`:

```python
    11: (  # minds slice 2: how each character stands with each person, one row per thing that
        # moved it, anchored like mind_states (docs/specs/2026-09-29-minds.md §3, note 22 §1)
        "CREATE TABLE opinions("
        " id INTEGER PRIMARY KEY,"
        " story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,"
        " src_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,"
        " dst_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,"
        " dim TEXT NOT NULL CHECK(dim IN('closeness','trust','respect','attraction','dominance',"
        "'familiarity','disclosed_in','disclosed_out')),"
        " value REAL NOT NULL,"
        " kind TEXT NOT NULL CHECK(kind IN('decay','sticky','permanent')),"
        " half_life_min INTEGER, event TEXT, cause TEXT,"
        " resolves_id INTEGER REFERENCES opinions ON DELETE CASCADE,"
        " witnesses TEXT, story_time INTEGER NOT NULL,"
        " message_id INTEGER REFERENCES messages ON DELETE CASCADE,"
        " run_id INTEGER REFERENCES extraction_runs ON DELETE CASCADE);"
        "CREATE INDEX ix_opinions ON opinions(src_id, dst_id);"
    ),
```

- [ ] **Step 4: Keep the older-library tests honest**

In `engine/tests/test_db.py`, `test_v10_adds_minds_and_usage` pretends to be v9, so it must drop
v11's table too; change its `executescript` line to:

```python
    old.executescript(
        "DROP TABLE IF EXISTS opinions; DROP TABLE IF EXISTS mind_states;"
        " DROP TABLE IF EXISTS usage_log;"
    )
```


In `engine/tests/test_archive.py`, `test_an_older_library_is_brought_up_to_date_on_the_way_in`, change the comment `# migrations 7 to 10, exactly reversed: a real v6 library` to `# migrations 7 to 11, exactly reversed: a real v6 library` and the line

```python
            " DROP TABLE mind_states; DROP TABLE usage_log;"
```

to

```python
            " DROP TABLE opinions; DROP TABLE mind_states; DROP TABLE usage_log;"
```

- [ ] **Step 5: Run the whole suite**

Run: `uv run pytest -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add engine/src/kataki/db.py engine/tests/test_db.py engine/tests/test_archive.py
git commit -m "feat(engine): v11 opinions, the relationship ledger, anchored on the branch"
```

---

### Task 2: A line is aimed at someone

**Files:**
- Modify: `engine/src/kataki/chat.py` (new `named`, `import re`)
- Modify: `engine/src/kataki/turns.py:56-67` (`_addressed`)
- Modify: `engine/src/kataki/inner.py` (`said`, `targets`, `react`)
- Test: `engine/tests/test_inner.py`, `engine/tests/test_minds.py` (`test_peek_sees_the_feeling_and_the_mask`)

**Interfaces:**
- Produces: `chat.named(conn, text: str, ids: list[int]) -> list[int]` (the ids a line names by any alias, in order of first mention); `inner.said(name: str, text: str) -> str` (`'Aren said "…"'`); `inner.targets(conn, path: list, hearers: list[int]) -> set[int]`.
- Changes: `inner.react` stirs only the characters `targets` returns; the rest overheard it and feel nothing from it.

- [ ] **Step 1: Write the failing tests** (append to `engine/tests/test_inner.py`)

```python
def _cast(conn):
    mira = library.create_item(conn, "character", "Mira")
    tobin = library.create_item(conn, "character", "Tobin")
    aren = library.create_item(conn, "character", "Aren")
    story = library.create_story(conn, "s", character_ids=[mira, tobin], persona_id=aren)
    ids = dict(conn.execute("SELECT name, id FROM entities WHERE story_id=?", (story,)).fetchall())
    return story, ids


def test_a_line_is_aimed_at_who_it_names_else_who_spoke_last(local_model):
    from kataki import chat, turns

    conn = local_model
    story, ids = _cast(conn)
    both = [ids["Mira"], ids["Tobin"]]
    turns.say(conn, story, "Tobin, you're useless.")
    assert inner.targets(conn, chat.active_path(conn, story), both) == {ids["Tobin"]}
    chat.append_message(conn, story, "assistant", "Easy.", ids["Mira"])
    turns.say(conn, story, "You're useless.")
    path = chat.active_path(conn, story)
    assert inner.targets(conn, path, both) == {ids["Mira"]}  # she is the one being answered
    assert inner.targets(conn, path, []) == set()


def test_only_the_one_it_is_aimed_at_takes_it_personally(local_model):
    from kataki import chat, turns

    conn = local_model
    story, ids = _cast(conn)
    turns.say(conn, story, "Mira, you're useless.")
    states = inner.react(conn, story, chat.active_path(conn, story))
    assert states[ids["Mira"]]["emotions"][0]["label"] == "hurt"
    assert states[ids["Tobin"]]["emotions"] == []  # he heard it; it wasn't about him


def test_a_line_names_people_in_the_order_it_names_them(local_model):
    from kataki import chat

    conn = local_model
    story, ids = _cast(conn)
    both = [ids["Mira"], ids["Tobin"]]
    assert chat.named(conn, "Tobin and Mira, listen.", both) == [ids["Tobin"], ids["Mira"]]
    assert chat.named(conn, "Nobody here.", both) == []
    assert chat.named(conn, "Mira!", []) == []
```

In `engine/tests/test_minds.py`, `test_peek_sees_the_feeling_and_the_mask`, replace the last three lines (the comment and the Tobin assertion) with:

```python
    tobin = next(p for p in people.people(conn, row) if p["name"] == "Tobin")
    assert tobin["mood"] is None  # he heard it, but it was aimed at Mira
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_inner.py tests/test_minds.py -q -k "aimed or personally or order_it or peek"`
Expected: FAIL — `AttributeError: module 'kataki.inner' has no attribute 'targets'`, `module 'kataki.chat' has no attribute 'named'`, and Tobin's mood is `hurt`.

- [ ] **Step 3: Implement `chat.named`** in `engine/src/kataki/chat.py`

Add `import re` to the imports, and below `audience_of`:

```python
def named(conn: sqlite3.Connection, text: str, ids: list[int]) -> list[int]:
    """The people a line names (by any alias), in the order it first names them; at the same
    spot, the longer alias wins ("Mira Vale" over "Mira")."""
    if not ids:
        return []
    rows = conn.execute(
        f"SELECT entity_id, alias FROM aliases WHERE entity_id IN ({','.join('?' * len(ids))})",
        ids,
    )
    first: dict[int, tuple[int, int]] = {}
    for r in rows:
        if m := re.search(rf"(?<!\w){re.escape(r['alias'])}(?!\w)", text, re.IGNORECASE):
            at = (m.start(), -len(r["alias"]))
            first[r["entity_id"]] = min(first.get(r["entity_id"], at), at)
    return sorted(first, key=lambda e: (first[e], e))
```

In `engine/src/kataki/turns.py` replace the body of `_addressed` (keep its signature and docstring) with:

```python
    return next(iter(chat.named(conn, text, ids)), None)
```

- [ ] **Step 4: Implement `said`, `targets` and the aimed `react`** in `engine/src/kataki/inner.py`

Below `_quote`, add:

```python
def said(name: str, text: str) -> str:
    """Why a feeling or a grudge is there, when a line caused it: 'Aren said "…"'."""
    return f'{name} said "{_quote(text)}"'


def targets(conn: sqlite3.Connection, path: list, hearers: list[int]) -> set[int]:
    """Who the latest line is aimed at, of those who heard it: everyone it names; else whoever of
    them spoke last (the one being answered); else all of them. Only they take it personally.
    ponytail: "Mira, Tobin is useless" aims at both; a name alone can't tell who is spoken to
    from who is spoken about."""
    if not hearers or not path:
        return set()
    if named := chat.named(conn, path[-1]["text"], hearers):
        return set(named)
    last = next(
        (
            m["speaker_id"]
            for m in reversed(path[:-1])
            if m["role"] == "assistant" and m["speaker_id"] in hearers
        ),
        None,
    )
    return {last} if last is not None else set(hearers)
```

Replace the whole `react` function with:

```python
def react(conn: sqlite3.Connection, story_id: int, path: list, model=None) -> dict[int, dict]:
    """Everyone here after the latest line, as they are now: faded to the present, stirred by
    that line if it was aimed at them and meant something (the others only overheard it),
    regulated. Nothing is written; the same path always gives the same answer, so a new take
    never feels it twice."""
    if not path:
        return {}
    last, now = path[-1], path[-1]["story_time"]
    scene_id = chat.scene_of(conn, story_id, path)
    cast = [
        e
        for e in chat.present_entities(conn, scene_id, path)
        if e["is_ai"] and e["kind"] == "character"
    ]
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)))
    hit = sense(last["text"], model) if last["role"] == "user" else None
    heard = [e["id"] for e in cast if last["id"] in chat.heard_by(conn, path, e["id"])]
    aimed = targets(conn, path, heard) if hit else set()
    out = {}
    for e in cast:
        prof = profile(conn, e["id"])
        state = tick(current(conn, e["id"], path, prof) or fresh(prof, now), now, prof)
        if e["id"] in aimed:
            cause = said(names.get(last["speaker_id"], "Someone"), last["text"])
            for label, intensity in appraise(*hit, prof, state):
                state = feel(state, label, intensity, cause, prof)
        out[e["id"]] = regulate(state, prof)
    return out
```

- [ ] **Step 5: Run the whole suite** (the `_addressed` change must not move any speaker)

Run: `uv run pytest -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add engine/src/kataki/chat.py engine/src/kataki/turns.py engine/src/kataki/inner.py engine/tests/test_inner.py engine/tests/test_minds.py
git commit -m "fix(engine): only the one a line is aimed at takes it personally"
```

---

### Task 3: The switches: `mind.bonds`, the Realism dials, social traits

**Files:**
- Modify: `engine/src/kataki/features.py` (`FEATURES`)
- Modify: `engine/src/kataki/knobs.py` (new `dial`)
- Modify: `engine/src/kataki/inner.py` (`DEFAULT`)
- Test: `engine/tests/test_features.py`, `engine/tests/test_knobs.py`, `engine/tests/test_inner.py`

**Interfaces:**
- Produces: `features.FEATURES["mind.bonds"] == "alpha"`; `knobs.dial(conn, entity_id: int | None, name: str, default: str) -> str` (the character's `data.realism.<name>` wins unless absent or `"inherit"`, else the setting `realism.<name>`, else `default`); `inner.DEFAULT["social"] == {"forgiveness": 0.5, "trust_propensity": 0.5}` (shaped and type-checked like every other profile key).

- [ ] **Step 1: Write the failing tests**

Append to `engine/tests/test_features.py`, inside `test_the_api_lists_features`, after the `mind.affect` assertion:

```python
    assert body["features"]["mind.bonds"]["stage"] == "alpha"
```

Append to `engine/tests/test_knobs.py`:

```python
def test_a_realism_dial_is_the_characters_own_else_the_setting(conn):
    mira = library.create_item(conn, "character", "Mira")
    story = library.create_story(conn, "s", character_ids=[mira])
    who = conn.execute("SELECT id FROM entities WHERE story_id=?", (story,)).fetchone()[0]
    assert knobs.dial(conn, who, "pushback", "realistic") == "realistic"
    conn.execute("INSERT INTO settings(key, value) VALUES('realism.pushback', '\"soft\"')")
    assert knobs.dial(conn, who, "pushback", "realistic") == "soft"
    library.update_item(conn, mira, data={"realism": {"pushback": "stubborn"}})
    assert knobs.dial(conn, who, "pushback", "realistic") == "stubborn"
    library.update_item(conn, mira, data={"realism": {"pushback": "inherit"}})
    assert knobs.dial(conn, who, "pushback", "realistic") == "soft"
    assert knobs.dial(conn, None, "relationships", "realistic") == "realistic"
```

Append to `engine/tests/test_inner.py`:

```python
def test_social_traits_default_and_refuse_junk():
    assert P["social"] == {"forgiveness": 0.5, "trust_propensity": 0.5}
    prof = inner.shape({"social": {"forgiveness": 0.9, "trust_propensity": "lots"}})
    assert prof["social"] == {"forgiveness": 0.9, "trust_propensity": 0.5}
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_features.py tests/test_knobs.py tests/test_inner.py -q -k "lists_features or realism_dial or social"`
Expected: FAIL — `KeyError: 'mind.bonds'`, no `knobs.dial`, no `social` key.

- [ ] **Step 3: Implement**

`engine/src/kataki/features.py`:

```python
FEATURES = {
    "mind.affect": "alpha",  # slice 1: moods that last
    "mind.bonds": "alpha",  # slice 2: grudges that hold, pushback, the side call
}
```

`engine/src/kataki/knobs.py`, after `setting`:

```python
def dial(conn: sqlite3.Connection, entity_id: int | None, name: str, default: str) -> str:
    """A Realism dial (minds spec §6: pushback, memory, relationships, texting): the character's
    own `data.realism.<name>` wins; absent or "inherit" means the setting `realism.<name>`."""
    mine = own(conn, entity_id).get("realism")
    value = mine.get(name) if isinstance(mine, dict) else None
    if value in (None, "inherit"):
        value = setting(conn, f"realism.{name}", default)
    return value
```

`engine/src/kataki/inner.py`, in `DEFAULT` after `"susceptibility": 0.4,`:

```python
    "social": {"forgiveness": 0.5, "trust_propensity": 0.5},  # 0-1; bonds.py reads them
```

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/features.py engine/src/kataki/knobs.py engine/src/kataki/inner.py engine/tests/test_features.py engine/tests/test_knobs.py engine/tests/test_inner.py
git commit -m "feat(engine): mind.bonds feature, Realism dials with a character override, social traits"
```

---

### Task 4: The ledger maths

**Files:**
- Create: `engine/src/kataki/bonds.py`
- Test: `engine/tests/test_bonds.py` (new)

**Interfaces:**
- Consumes: `inner.shape`-d profiles (`attachment.anxiety`, `social.forgiveness`, `social.trust_propensity`), `clock.DAY`.
- Produces (row dicts: `{"id", "dst_id", "dim", "value", "kind", "half_life_min", "event", "cause", "resolves_id", "story_time", "scene_id"}`, `id` None until saved):
  - `bonds.EVENTS: dict[str, tuple[dict[str, float], str, int]]` — the 19 events a model or rule may name.
  - `bonds.strength(row, fix: dict | None, now: int) -> float` (0–1 left).
  - `bonds.standing(rows, dst: int, now: int) -> dict` → `{"closeness", "trust", "respect", "familiarity": float, "causes": [cause], "grudge": cause | None, "forgiven": cause | None}` where cause = `{"event", "cause", "t", "kind", "forgiven", "weight"}`.
  - `bonds.apply(rows, dst, event, intensity: int, cause: str, now: int, scene_id, prof, dial="realistic") -> list[dict]` (new rows, not saved).
  - constants `SCENE_CAP`, `NOTICE`, `STRONG`, `STICKY_FLOOR`, `REPAIR_DAYS`.

- [ ] **Step 1: Write the failing tests** (new file `engine/tests/test_bonds.py`)

```python
"""The relationship ledger: pure maths on story minutes, then the turn, Peek and the graph."""

import re

import pytest

from kataki import bonds, clock, inner

P = inner.shape({})
DAY = clock.DAY
CAUSE = 'Aren said "I forgot"'


def breach(prof=P, now=0, scene=1, dial="realistic"):
    return bonds.apply([], 7, "promise_broken", 2, CAUSE, now, scene, prof, dial)


def saved(rows, start=1):
    """The rows as if written: they get ids, so an apology can point at them."""
    return [{**r, "id": start + i} for i, r in enumerate(rows)]


def test_a_broken_promise_costs_more_trust_than_a_kept_one_earns():
    lost = bonds.standing(breach(), 7, 0)["trust"]
    kept = bonds.standing(bonds.apply([], 7, "promise_kept", 2, "came", 0, 1, P), 7, 0)["trust"]
    assert lost == pytest.approx(-17.6) and kept > 0
    assert abs(lost) >= 2 * kept


def test_a_grudge_holds_while_a_kindness_fades():
    rows = saved(breach() + bonds.apply([], 7, "kindness", 2, "brought soup", 0, 1, P))
    later = bonds.standing(rows, 7, 90 * DAY)
    assert later["trust"] == pytest.approx(bonds.STICKY_FLOOR * -17.6, abs=0.1)
    assert later["grudge"]["event"] == "promise_broken"


def test_a_hollow_apology_forgives_nothing():
    rows = saved(breach())
    rows += bonds.apply(rows, 7, "apology_hollow", 2, "sorry", 60, 1, P)
    now = bonds.standing(rows, 7, 60)
    assert now["grudge"] is not None and now["trust"] == pytest.approx(-17.6, abs=0.1)


def test_a_sincere_apology_forgives_and_trust_comes_back_slowly():
    rows = saved(breach())
    rows += bonds.apply(rows, 7, "apology_sincere", 2, "I broke my promise", 60, 1, P)
    now = bonds.standing(rows, 7, 60)
    assert now["grudge"] is None and now["forgiven"]["event"] == "promise_broken"
    assert now["trust"] < -15  # forgiving is not forgetting
    week = bonds.standing(rows, 7, 60 + 7 * DAY)["trust"]
    assert -17.6 < week < -12  # a week on, most of it is still missing


def test_forgiving_people_forgive_faster():
    def a_month_after_sorry(prof):
        rows = saved(breach(prof))
        rows += bonds.apply(rows, 7, "apology_sincere", 2, "sorry", 0, 1, prof)
        return bonds.standing(rows, 7, 30 * DAY)["trust"]

    kind = inner.shape({"social": {"forgiveness": 1.0}})
    hard = inner.shape({"social": {"forgiveness": 0.0}})
    assert a_month_after_sorry(kind) > a_month_after_sorry(hard)


def test_one_scene_cannot_buy_closeness():
    rows: list[dict] = []
    for _ in range(10):
        rows += bonds.apply(rows, 7, "support_given", 3, "helped", 0, 1, P)
    assert bonds.standing(rows, 7, 0)["closeness"] <= bonds.SCENE_CAP["closeness"]
    rows += bonds.apply(rows, 7, "support_given", 3, "helped", 0, 2, P)  # the next scene
    assert bonds.standing(rows, 7, 0)["closeness"] > bonds.SCENE_CAP["closeness"]


def test_anxious_people_take_it_harder_and_the_dial_scales_it():
    base = bonds.standing(breach(), 7, 0)["trust"]
    anxious = inner.shape({"attachment": {"anxiety": 0.9}})
    assert bonds.standing(breach(anxious), 7, 0)["trust"] < base
    assert bonds.standing(breach(dial="gentle"), 7, 0)["trust"] == pytest.approx(base / 2)


def test_rows_are_about_one_person_at_a_time():
    rows = saved(breach())
    other = bonds.standing(rows, 8, 0)
    assert other["trust"] == 0 and other["grudge"] is None and other["causes"] == []
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_bonds.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'kataki.bonds'` (reported as an import error).

- [ ] **Step 3: Implement** `engine/src/kataki/bonds.py`

```python
"""How a character stands with each person, kept by code (docs/specs/2026-09-29-minds.md, slice 2).

A relationship is a ledger, not a number (note 16 §5; note 22 §1 `opinions`): each thing someone
did leaves rows (what, which way, how much, why, when), and how the character feels about them now
is those rows faded to the present. Most fade on story time. A grudge (an insult, a broken
promise, a crossed line) is sticky: it holds at no less than 40% of itself until it is forgiven,
and forgiving turns it into slow decay, so trust comes back slower than it went. A hollow apology
forgives nothing. The prompt gets words, never numbers. Zero model calls.

ponytail: every constant here is an estimate from the research (note 16 §9.3); tune them on the
probes (evals/probes.py), not by feel.
"""

from kataki import clock

DIMS = ("closeness", "trust", "respect", "familiarity")  # the dimensions events move so far
SHOWN = ("trust", "closeness", "respect")  # the ones worth a word
# note 22's EVENT list, less the five that code detects in later slices (neglect_gap,
# favouritism_shown, lie_discovered, disclosure_unreciprocated, secret_betrayed).
# event: ({dimension: change at intensity 1}, kind, half-life in story days)
EVENTS: dict[str, tuple[dict[str, float], str, int]] = {
    "kindness": ({"closeness": 2, "trust": 1}, "decay", 14),
    "support_given": ({"closeness": 3, "trust": 2}, "decay", 21),
    "support_ignored": ({"closeness": -2, "trust": -2}, "decay", 7),
    "vulnerable_disclosure": ({"closeness": 3, "familiarity": 2}, "decay", 30),
    "disclosure_reciprocated": ({"closeness": 3, "trust": 2}, "decay", 30),
    "shared_joy": ({"closeness": 2}, "decay", 14),
    "compliment": ({"closeness": 1, "respect": 1}, "decay", 7),
    "teasing_ok": ({"closeness": 1}, "decay", 7),
    "teasing_hurt": ({"closeness": -2, "trust": -1}, "decay", 7),
    "insult": ({"closeness": -3, "trust": -2, "respect": -3}, "sticky", 30),
    "dismissal": ({"closeness": -2, "respect": -1}, "decay", 7),
    "promise_kept": ({"trust": 3}, "decay", 30),
    "promise_broken": ({"trust": -8, "closeness": -3}, "sticky", 30),
    "secret_kept": ({"trust": 3}, "decay", 30),
    "boundary_crossed": ({"trust": -6, "closeness": -4}, "sticky", 30),
    "apology_sincere": ({"closeness": 1}, "decay", 7),  # and forgives every open grudge
    "apology_hollow": ({"respect": -1}, "decay", 3),
    "amends_made": ({"trust": 2}, "decay", 30),  # and forgives every open grudge
    "help_refused": ({"closeness": -2, "trust": -1}, "decay", 7),
}
REPAIR = frozenset({"apology_sincere", "amends_made"})
STICKY_FLOOR = 0.4  # ponytail: an unforgiven grudge never fades below this share of itself
REPAIR_DAYS = 30  # ponytail: forgiven, it halves in this many story days / (0.5 + forgiveness)
SCENE_CAP = {"closeness": 8, "trust": 10}  # ponytail: the most one scene can raise either
START_CLOSENESS = 20  # ponytail: where a pair starts, for diminishing returns only
HARSH = {"gentle": 0.5, "realistic": 1.0, "harsh": 1.5}  # Realism › Relationships, on losses
FADED = 1.0  # a cause weaker than this is no longer worth naming


def _fade(minutes: int, half_life: int | None) -> float:
    return 0.5 ** (max(minutes, 0) / max(half_life or 1, 1))


def strength(row: dict, fix: dict | None, now: int) -> float:
    """How much of a row is left at `now`, 0-1. A forgiven grudge fades from what it was when it
    was forgiven, at the forgiving row's pace."""
    if row["kind"] == "permanent":
        return 1.0
    if row["kind"] == "decay":
        return _fade(now - row["story_time"], row["half_life_min"])
    if fix is None:
        return max(STICKY_FLOOR, _fade(now - row["story_time"], row["half_life_min"]))
    held = max(STICKY_FLOOR, _fade(fix["story_time"] - row["story_time"], row["half_life_min"]))
    return held * _fade(now - fix["story_time"], fix["half_life_min"])


def _fixes(rows: list[dict]) -> dict[int, dict]:
    """Which rows have been forgiven, by which row."""
    return {r["resolves_id"]: r for r in rows if r["resolves_id"] is not None}


def standing(rows: list[dict], dst: int, now: int) -> dict:
    """Where the ledger's owner stands with `dst` at `now`: how far each dimension has moved
    since they started, the strongest causes, the open grudge (the latest) and the latest
    forgiven one."""
    fixes = _fixes(rows)
    moved = dict.fromkeys(DIMS, 0.0)
    causes: dict[tuple, dict] = {}
    grudge = forgiven = None
    for r in rows:
        if r["dst_id"] != dst or r["resolves_id"] is not None:
            continue
        fix = fixes.get(r["id"]) if r["id"] is not None else None
        left = strength(r, fix, now)
        moved[r["dim"]] += r["value"] * left
        key = (r["event"], r["cause"], r["story_time"])
        c = causes.setdefault(key, {"event": r["event"], "cause": r["cause"],
                                    "t": r["story_time"], "kind": r["kind"],
                                    "forgiven": fix is not None, "weight": 0.0})  # fmt: skip
        c["weight"] += abs(r["value"] * left)
        if r["kind"] == "sticky":
            if fix is None:
                grudge = c
            else:
                forgiven = c
    top = sorted((c for c in causes.values() if c["weight"] >= FADED), key=lambda c: -c["weight"])
    return {
        **{d: round(v, 1) for d, v in moved.items()},
        "causes": top[:2],
        "grudge": grudge,
        "forgiven": forgiven,
    }


def _row(dst, dim, value, kind, half_life, event, cause, resolves, now, scene_id) -> dict:
    return {"id": None, "dst_id": dst, "dim": dim, "value": value, "kind": kind,
            "half_life_min": half_life, "event": event, "cause": cause, "resolves_id": resolves,
            "story_time": now, "scene_id": scene_id}  # fmt: skip


def apply(
    rows: list[dict],
    dst: int,
    event: str,
    intensity: int,
    cause: str,
    now: int,
    scene_id: int | None,
    prof: dict,
    dial: str = "realistic",
) -> list[dict]:
    """The rows one event adds to a ledger that already holds `rows` (saved or not), by the
    owner's temperament: the anxious take losses harder, the trusting gain trust faster, closeness
    comes slower the closer they are, one scene can only raise it so far, and a repair forgives
    every open grudge toward `dst` (a forgiving owner forgives faster)."""
    deltas, kind, half_days = EVENTS[event]
    social = prof["social"]
    before = standing(rows, dst, now)
    new = []
    for dim, per in deltas.items():
        value = per * intensity
        if value < 0:
            value *= (1 + 0.5 * prof["attachment"]["anxiety"]) * HARSH.get(dial, 1.0)
        else:
            if dim == "trust":
                value *= 0.5 + social["trust_propensity"]
            if dim == "closeness":
                value *= max(0.0, 1 - (START_CLOSENESS + before["closeness"]) / 100) ** 0.5
            if dim in SCENE_CAP:
                spent = sum(
                    r["value"]
                    for r in rows
                    if r["dst_id"] == dst and r["dim"] == dim and r["value"] > 0
                    and r["scene_id"] == scene_id
                )  # fmt: skip
                value = min(value, max(0.0, SCENE_CAP[dim] - spent))
        if abs(value) < 0.05:
            continue
        row_kind = "permanent" if dim == "familiarity" else kind
        new.append(_row(dst, dim, round(value, 2), row_kind, half_days * clock.DAY, event, cause,
                        None, now, scene_id))  # fmt: skip
    if event in REPAIR:
        half_life = round(REPAIR_DAYS * clock.DAY / (0.5 + social["forgiveness"]))
        fixes = _fixes(rows)
        for g in rows:
            if (g["dst_id"] == dst and g["kind"] == "sticky" and g["id"] is not None
                    and g["id"] not in fixes):  # fmt: skip
                new.append(_row(dst, g["dim"], 0.0, "decay", half_life, event, cause, g["id"],
                                now, scene_id))  # fmt: skip
    return new
```

(ponytail: a repair forgives every open grudge toward that person, not the one it names; per-cause repair can come when the side call names the cause. A repeat offence is just another grudge, not a doubled one.)

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_bonds.py -q && uv run ruff check src/kataki/bonds.py tests/test_bonds.py && uv run ruff format --check src/kataki/bonds.py tests/test_bonds.py`
Expected: PASS, lint clean (run `uv run ruff format` on the two files if the format check complains, then re-run).

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/bonds.py engine/tests/test_bonds.py
git commit -m "feat(engine): relationship ledger maths: grudges that hold, slow forgiveness"
```

---

### Task 5: Reading a line into the ledger, and keeping it per branch

**Files:**
- Modify: `engine/src/kataki/bonds.py` (`rule_events`, `ledger`, `react`, `save`)
- Test: `engine/tests/test_bonds.py`

**Interfaces:**
- Consumes: `inner.sense`, `inner.targets`, `inner.said`, `inner.profile`, `knobs.dial`, `chat.scene_of/present_entities/heard_by`, `db.anchor_filter`.
- Produces:
  - `bonds.rule_events(text: str, hit: tuple[str, float] | None) -> list[tuple[str, int]]`
  - `bonds.ledger(conn, src: int, path: list) -> list[dict]` (live rows of `src`, oldest first, each with `scene_id` from its message)
  - `bonds.react(conn, story_id: int, path: list, model=None) -> dict[int, list[dict]]` (unsaved rows per character the latest user line was aimed at)
  - `bonds.save(conn, story_id: int, rows: dict[int, list[dict]], message_id: int) -> None`

- [ ] **Step 1: Write the failing tests**

In `engine/tests/test_bonds.py`, change the kataki import at the top to:

```python
from kataki import bonds, chat, clock, inner, library, turns
```

Then append:

```python
@pytest.mark.parametrize(
    "line, events",
    [
        ("I forgot. I didn't come last night.", [("promise_broken", 2)]),
        ("You're useless.", [("insult", 2)]),
        ("I'm sorry.", [("apology_hollow", 2)]),
        ("I'm sorry I broke my promise. It was my fault.", [("apology_sincere", 2)]),
        ("You did so well, thank you.", [("compliment", 2)]),
        ("Nice weather.", []),
    ],
)
def test_rules_read_what_a_line_did(line, events):
    assert bonds.rule_events(line, inner.sense(line)) == events


def test_only_the_one_it_was_aimed_at_writes_it_down_on_this_branch(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    story = library.create_story(
        conn, "s", character_ids=[ids["Mira"], ids["Tobin"]], persona_id=ids["Aren"]
    )
    who = dict(conn.execute("SELECT name, id FROM entities WHERE story_id=?", (story,)).fetchall())
    turns.say(conn, story, "Tobin, you're useless.")
    path = chat.active_path(conn, story)

    pending = bonds.react(conn, story, path)
    assert set(pending) == {who["Tobin"]}
    assert {r["dst_id"] for r in pending[who["Tobin"]]} == {who["Aren"]}
    assert {r["event"] for r in pending[who["Tobin"]]} == {"insult"}

    bonds.save(conn, story, pending, path[-1]["id"])
    kept = bonds.ledger(conn, who["Tobin"], path)
    assert len(kept) == 3 and all(r["id"] and r["scene_id"] for r in kept)
    assert bonds.ledger(conn, who["Tobin"], path[:-1]) == []  # another branch never had it
    assert bonds.react(conn, story, path[:-1]) == {}  # nothing new was said there
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_bonds.py -q -k "rules_read or aimed_at_writes"`
Expected: FAIL — `AttributeError: module 'kataki.bonds' has no attribute 'rule_events'`.

- [ ] **Step 3: Implement** in `engine/src/kataki/bonds.py`

Replace the imports with:

```python
import re
import sqlite3

from kataki import chat, clock, db, inner, knobs
```

Append:

```python
# what a line did, read by rules: the lite level, and the fallback when the side call can't run
BROKEN = re.compile(
    r"\b(i forgot|i didn'?t (come|show up|make it|call)|couldn'?t make it"
    r"|broke (my|the|a|our) promise|stood you up)\b",
    re.IGNORECASE,
)
OWNED = re.compile(  # an apology that owns the wrong
    r"\b(i was wrong|my fault|i shouldn'?t have|that was (wrong|unfair|cruel)|i broke"
    r"|i let you down|i'?ll make it up|i hurt you)\b",
    re.IGNORECASE,
)
RULED = {  # inner.sense's events, as the ledger names them
    "insult": "insult",
    "threat": "boundary_crossed",
    "praise": "compliment",
    "good_news": "shared_joy",
    "bad_news": "vulnerable_disclosure",
}


def rule_events(text: str, hit: tuple[str, float] | None) -> list[tuple[str, int]]:
    """What a line did to the one it was aimed at, by rules: [(event, intensity 1-3)]. An apology
    is sincere only when it owns the wrong, and one that names the wrong is not that wrong again.
    ponytail: keywords only (inner.sense's list plus two of our own); the side call reads the
    rest on the standard level."""
    if hit and hit[0] == "apology":
        return [("apology_sincere" if OWNED.search(text) else "apology_hollow", 2)]
    out = [("promise_broken", 2)] if BROKEN.search(text) else []
    if hit:
        out.append((RULED[hit[0]], 2 if hit[1] >= 0.9 else 1))
    return out


def ledger(conn: sqlite3.Connection, src: int, path: list) -> list[dict]:
    """Every live row of `src`'s ledger, oldest first: written on this branch (or by the user),
    each with the scene it was written in."""
    scene = {m["id"]: m["scene_id"] for m in path}
    where, args = db.anchor_filter(set(), set(scene))
    rows = conn.execute(
        f"SELECT * FROM opinions WHERE src_id=? AND {where} ORDER BY story_time, id", [src, *args]
    )
    return [{**dict(r), "scene_id": scene.get(r["message_id"])} for r in rows]


def react(conn: sqlite3.Connection, story_id: int, path: list, model=None) -> dict[int, list]:
    """What the latest user line adds to the ledger of each character it was aimed at, not yet
    saved: {character id: [rows]}. Like inner.react, the same path always gives the same rows,
    so a new take never counts it twice."""
    if not path or path[-1]["role"] != "user" or path[-1]["speaker_id"] is None:
        return {}
    last, now = path[-1], path[-1]["story_time"]
    events = rule_events(last["text"], inner.sense(last["text"], model))
    if not events:
        return {}
    scene_id = chat.scene_of(conn, story_id, path)
    cast = [
        e["id"]
        for e in chat.present_entities(conn, scene_id, path)
        if e["is_ai"] and e["kind"] == "character"
    ]
    heard = [e for e in cast if last["id"] in chat.heard_by(conn, path, e)]
    who = conn.execute("SELECT name FROM entities WHERE id=?", (last["speaker_id"],)).fetchone()
    cause = inner.said(who["name"] if who else "Someone", last["text"])
    out = {}
    for src in inner.targets(conn, path, heard):
        rows, new = ledger(conn, src, path), []
        prof, dial = inner.profile(conn, src), knobs.dial(conn, src, "relationships", "realistic")
        for event, intensity in events:
            new += apply(
                rows + new, last["speaker_id"], event, intensity, cause, now, scene_id, prof, dial
            )
        if new:
            out[src] = new
    return out


COLUMNS = ("dst_id", "dim", "value", "kind", "half_life_min", "event", "cause", "resolves_id",
           "story_time")  # fmt: skip


def _insert(conn, story_id: int, src: int, rows: list[dict], message_id: int) -> None:
    conn.executemany(
        f"INSERT INTO opinions(story_id, src_id, {', '.join(COLUMNS)}, message_id)"
        f" VALUES({', '.join('?' * (len(COLUMNS) + 3))})",
        [(story_id, src, *(r[c] for c in COLUMNS), message_id) for r in rows],
    )


def save(conn: sqlite3.Connection, story_id: int, rows: dict[int, list], message_id: int) -> None:
    """Anchored on the reply they were read before: a new take or another branch has its own."""
    with conn:
        for src, new in rows.items():
            _insert(conn, story_id, src, new, message_id)
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_bonds.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/bonds.py engine/tests/test_bonds.py
git commit -m "feat(engine): read a line into the ledger of the one it was aimed at, per branch"
```

---

### Task 6: The ledger in words

**Files:**
- Modify: `engine/src/kataki/inner.py` (`HEADER`, `lines`, `block`; `render` keeps its behaviour)
- Modify: `engine/src/kataki/bonds.py` (`sentences`, `summary`, `public`, `toward`, `render`)
- Test: `engine/tests/test_bonds.py`, `engine/tests/test_inner.py` (existing render tests must still pass unchanged)

**Interfaces:**
- Produces:
  - `inner.HEADER: str`; `inner.lines(state, prof) -> list[str]` (the feeling rows, no header); `inner.block(name: str, rows: list[str]) -> str` (`""` when `rows` is empty); `inner.render(state, prof, name)` unchanged in output.
  - `bonds.sentences(st: dict, name: str, now: int) -> list[str]` (mind block rows toward one person; `[]` when nothing is worth saying)
  - `bonds.summary(st: dict) -> str` (`"trusts much less · further · holds a grudge"`)
  - `bonds.public(st, other_id: int, other: str, you: bool, epoch: int) -> dict` (spec §8.3 bond shape)
  - `bonds.toward(rows, others: list[int], now: int) -> dict[int, dict]` (standings worth a word)
  - `bonds.render(conn, story_id, src, path, pending: list[dict]) -> tuple[list[str], list[dict]]` (rows for the speaker's block toward whoever they answer plus the one other person here they feel most about, and the same as `public` dicts)

- [ ] **Step 1: Write the failing tests** (append to `engine/tests/test_bonds.py`)

```python
def test_the_block_says_it_in_words_never_numbers():
    rows = saved(breach())
    text = "\n".join(bonds.sentences(bonds.standing(rows, 7, 120), "Aren", 120))
    assert text.startswith(
        "Toward Aren: you trust them much less than before; you feel further from them"
        ' (Aren said "I forgot", two hours ago).'
    )
    assert (
        'You have not forgiven Aren (Aren said "I forgot"). Stay civil; do not warm up unless'
        " Aren owns it." in text
    )
    assert not re.search(r"\d", text)


def test_forgiven_but_not_yet_trusted():
    rows = saved(breach())
    rows += bonds.apply(rows, 7, "apology_sincere", 2, "sorry", 60, 1, P)
    text = "\n".join(bonds.sentences(bonds.standing(rows, 7, 60), "Aren", 60))
    assert "You have forgiven Aren, but trust comes back slowly." in text
    assert "not forgiven" not in text


def test_nothing_happened_nothing_to_say():
    assert bonds.sentences(bonds.standing([], 7, 0), "Aren", 0) == []
    assert bonds.toward([], [7], 0) == {}


def test_the_app_gets_words_and_numbers():
    st = bonds.standing(saved(breach()), 7, 0)
    shown = bonds.public(st, 7, "Aren", True, 480)
    assert shown["words"] == "trusts much less · further · holds a grudge"
    assert shown["trust"] == pytest.approx(-17.6) and shown["you"] is True
    assert shown["grudge"] == {"event": "promise_broken", "cause": CAUSE, "since": "Day 1, 08:00",
                               "kind": "sticky", "forgiven": False}  # fmt: skip
    assert [c["event"] for c in shown["causes"]] == ["promise_broken"]


def test_one_mind_block_holds_feelings_and_bonds():
    hurt = inner.feel(inner.fresh(P, 0), "hurt", 0.8, "cruel", P)
    feeling = inner.lines(inner.regulate(hurt, P), P)
    block = inner.block("Mira", [*feeling, "Toward Aren: you feel further from them."])
    assert block.splitlines()[0] == "[Inside Mira right now: show it, never say it]"
    assert block.splitlines()[-1] == "Toward Aren: you feel further from them."
    assert inner.block("Mira", []) == ""
    assert inner.render(inner.regulate(hurt, P), P, "Mira") == inner.block("Mira", feeling)
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_bonds.py -q -k "words or forgiven_but or nothing_happened or app_gets or one_mind_block"`
Expected: FAIL — no `bonds.sentences`, no `inner.lines`.

- [ ] **Step 3: Split `inner.render`** in `engine/src/kataki/inner.py`

Replace the whole `render` function with:

```python
HEADER = "[Inside {name} right now: show it, never say it]"


def lines(state: dict, prof: dict) -> list[str]:
    """How they feel, as rows of the mind block: words, never numbers; none at rest."""
    if (p := public(state, prof)) is None:
        return []
    rows = []
    if p["label"]:
        rows.append(f"Feeling: {p['feels']}" + (f" ({p['why']})." if p["why"] else "."))
        if p["shows"] != p["label"]:
            hiding = f"Showing: {p['shows']}. Hiding the {NOUN.get(p['label'], p['label'])}"
            rows.append(hiding + (f"; it slips out as {p['tell']}." if p["tell"] else "."))
    if p["word"]:
        rows.append(f"Mood: {p['word']}.")
    return rows


def block(name: str, rows: list[str]) -> str:
    """The one mind block for the prompt's tail (note 22 §4): its rows under one header, or
    nothing when there is nothing to say."""
    return "\n".join([HEADER.format(name=name), *rows]) if rows else ""


def render(state: dict, prof: dict, name: str) -> str:
    """The mind block with only how they feel in it; empty at rest."""
    return block(name, lines(state, prof))
```

- [ ] **Step 4: Implement the words** (append to `engine/src/kataki/bonds.py`)

```python
NOTICE, STRONG = 5, 15  # ponytail: a move this big is worth a word; this big, "much"


def _how(x: float, up: str, down: str) -> str:
    if abs(x) < NOTICE:
        return ""
    return (up if x > 0 else down).format(much="much " if abs(x) >= STRONG else "")


def _ago(minutes: int) -> str:
    return "just now" if minutes < 60 else f"{clock.spell(minutes).lower()} ago"


def sentences(st: dict, name: str, now: int) -> list[str]:
    """Where they stand with `name`, as rows of the mind block (note 22 §4 row 3): how it has
    moved, why (the strongest causes, with their age), and what an open grudge means for this
    reply. Words, never numbers."""
    moved = [
        _how(st["trust"], "you trust them {much}more than before",
             "you trust them {much}less than before"),
        _how(st["closeness"], "you feel {much}closer to them", "you feel {much}further from them"),
        _how(st["respect"], "you respect them {much}more", "you respect them {much}less"),
    ]  # fmt: skip
    moved = [m for m in moved if m]
    if not moved and not st["grudge"]:
        return []
    why = "; ".join(f"{c['cause']}, {_ago(now - c['t'])}" for c in st["causes"])
    rows = [
        f"Toward {name}: " + ("; ".join(moved) or "something is unresolved")
        + (f" ({why})." if why else ".")
    ]  # fmt: skip
    if g := st["grudge"]:
        rows.append(
            f"You have not forgiven {name} ({g['cause']}). Stay civil; do not warm up unless"
            f" {name} owns it."
        )
    elif st["forgiven"] and st["trust"] <= -NOTICE:
        rows.append(f"You have forgiven {name}, but trust comes back slowly.")
    return rows


def summary(st: dict) -> str:
    """The same standing in a few words for the app."""
    parts = [
        _how(st["trust"], "trusts {much}more", "trusts {much}less"),
        _how(st["closeness"], "{much}closer", "{much}further"),
        _how(st["respect"], "respects {much}more", "respects {much}less"),
        "holds a grudge" if st["grudge"] else "has forgiven" if st["forgiven"] else "",
    ]
    return " · ".join(p for p in parts if p)


def public(st: dict, other_id: int, other: str, you: bool, epoch: int) -> dict:
    """One bond as the app shows it (spec §8.3): numbers for a soft bar, words for the rest."""

    def cause(c: dict) -> dict:
        return {"event": c["event"], "cause": c["cause"], "since": clock.label(c["t"], epoch),
                "kind": c["kind"], "forgiven": c["forgiven"]}  # fmt: skip

    return {
        "other_id": other_id,
        "other": other,
        "you": you,
        **{d: st[d] for d in SHOWN},
        "words": summary(st),
        "grudge": cause(st["grudge"]) if st["grudge"] else None,
        "causes": [cause(c) for c in st["causes"]],
    }


def _size(st: dict) -> float:
    return sum(abs(st[d]) for d in SHOWN) + (100 if st["grudge"] else 0)


def toward(rows: list[dict], others: list[int], now: int) -> dict[int, dict]:
    """Standings worth a word, for each of `others` the ledger has something on."""
    out = {}
    for dst in others:
        st = standing(rows, dst, now)
        if st["grudge"] or any(abs(st[d]) >= NOTICE for d in SHOWN):
            out[dst] = st
    return out


def render(
    conn: sqlite3.Connection, story_id: int, src: int, path: list, pending: list[dict]
) -> tuple[list[str], list[dict]]:
    """The speaker's relationship rows for the mind block, and the same for the app: toward
    whoever they are answering, and the one other person here they feel most about."""
    story = conn.execute(
        "SELECT persona_entity_id, epoch_offset_min FROM stories WHERE id=?", (story_id,)
    ).fetchone()
    now = path[-1]["story_time"] if path else 0
    scene_id = chat.scene_of(conn, story_id, path)
    here = [e["id"] for e in chat.present_entities(conn, scene_id, path) if e["id"] != src]
    stands = toward(ledger(conn, src, path) + pending, here, now)
    last = path[-1]["speaker_id"] if path else None
    answering = last if last not in (None, src) else story["persona_entity_id"]
    rest = sorted((d for d in stands if d != answering), key=lambda d: -_size(stands[d]))
    picked = ([answering] if answering in stands else []) + rest[:1]
    names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)))
    rows, shown = [], []
    for d in picked:
        rows += sentences(stands[d], names.get(d, "them"), now)
        you = d == story["persona_entity_id"]
        shown.append(public(stands[d], d, names.get(d, "someone"), you, story["epoch_offset_min"]))
    return rows, shown
```

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_bonds.py tests/test_inner.py -q`
Expected: PASS (the slice-1 render tests pass unchanged).

- [ ] **Step 6: Commit**

```bash
git add engine/src/kataki/inner.py engine/src/kataki/bonds.py engine/tests/test_bonds.py
git commit -m "feat(engine): the ledger in words in the one mind block"
```

---

### Task 7: Grudges in the turn

**Files:**
- Modify: `engine/src/kataki/turns.py` (imports; the mind step in `_generate` at lines 254-265; the `finally` block at lines 384-396)
- Test: `engine/tests/test_bonds.py`, `engine/tests/test_minds.py` (two slice-1 tests)

**Interfaces:**
- Consumes: `bonds.react`, `bonds.render`, `bonds.save`, `inner.lines`, `inner.block`, `features.enabled(conn, "mind.bonds")`.
- Produces: `messages.gen.bonds` (list of `bonds.public` dicts the reply was written with, only when non-empty); `opinions` rows anchored on each reply; the speaker's relationship rows in the `[Inside X right now]` block.

- [ ] **Step 1: Write the failing tests** (append to `engine/tests/test_bonds.py`)

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


@pytest.mark.anyio
async def test_she_holds_it_for_twenty_turns_a_hollow_sorry_fails_a_real_one_lands(
    conn, story, backend
):
    backend.say(*["Mm."] * 23)
    await play(turns.turn(conn, backend.llm, story, "Mira, I forgot. I didn't come last night."))
    assert "You have not forgiven Aren" in tail(backend.requests[0])
    for _ in range(20):
        await play(turns.turn(conn, backend.llm, story, "Nice weather, Mira."))
    assert "You have not forgiven Aren" in tail(backend.requests[-1])
    await play(turns.turn(conn, backend.llm, story, "Mira, I'm sorry."))
    assert "You have not forgiven Aren" in tail(backend.requests[-1])
    await play(
        turns.turn(conn, backend.llm, story, "Mira, I'm sorry I broke my promise. My fault.")
    )
    block = tail(backend.requests[-1])
    assert "You have forgiven Aren, but trust comes back slowly." in block
    assert "you trust them much less than before" in block


@pytest.mark.anyio
async def test_a_new_take_does_not_count_it_twice(conn, story, backend):
    backend.say("First.", "Second.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    await play(turns.regenerate(conn, backend.llm, story))
    live = bonds.ledger(conn, eid(conn, "Mira"), chat.active_path(conn, story))
    assert len(live) == 3  # the insult once, on this take
    assert conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0] == 6  # both takes kept
    assert tail(backend.requests[0]) == tail(backend.requests[1])


@pytest.mark.anyio
async def test_switched_off_there_is_no_ledger(conn, story, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.bonds', 'false')")
    backend.say("Fine.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert "Toward Aren" not in tail(backend.requests[0])
    assert conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0] == 0


@pytest.mark.anyio
async def test_a_failing_ledger_still_keeps_the_reply(conn, story, backend, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr("kataki.bonds.react", boom)
    backend.say("Fine.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert events[-1][0] == "done" and chat.active_path(conn, story)[-1]["text"] == "Fine."
    assert "Toward Aren" not in tail(backend.requests[0])
```

In `engine/tests/test_minds.py`:

- In `test_switched_off_no_mood_reaches_the_tail`, after the existing `INSERT … 'features.mind.affect'` line add:

```python
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.bonds', 'false')")
```

- In `test_a_failing_mind_step_still_keeps_the_reply`, replace `assert "[Inside" not in tail(backend.requests[0])` with:

```python
    assert "Feeling:" not in tail(backend.requests[0])  # the ledger's rows may still be there
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_bonds.py -q -k "twenty or new_take or switched_off or failing_ledger"`
Expected: FAIL — the tail has no "You have not forgiven Aren", and `opinions` stays empty.

- [ ] **Step 3: Implement** in `engine/src/kataki/turns.py`

Add `bonds,` to the `from kataki import (…)` list, first (before `chat,`).

Replace the mind step (from `minds: dict[int, dict] = {}` through the `except` that logs "mind skipped") with:

```python
    minds: dict[int, dict] = {}  # everyone here, as they feel after the latest line
    felt: list[str] = []  # the speaker's feeling rows of the mind block
    pending: dict[int, list[dict]] = {}  # ledger rows the latest line adds, kept with the reply
    ties: list[str] = []  # the speaker's relationship rows of the mind block
    stood: list[dict] = []  # the same, as the app shows them (gen.bonds, the Mind graph)
    try:  # the mind adds to a turn, it never stops one
        if features.enabled(conn, "mind.affect"):
            minds = inner.react(conn, story_id, path, await asyncio.to_thread(embed.builtin))
        if speaker_id in minds:
            felt = inner.lines(minds[speaker_id], inner.profile(conn, speaker_id))
    except Exception as e:
        logging.getLogger(__name__).warning("mind skipped for story %s: %s", story_id, e)
        minds, felt = {}, []
    try:
        if features.enabled(conn, "mind.bonds"):
            pending = bonds.react(conn, story_id, path, await asyncio.to_thread(embed.builtin))
            if speaker_id is not None:
                mine = pending.get(speaker_id, [])
                ties, stood = bonds.render(conn, story_id, speaker_id, path, mine)
    except Exception as e:
        logging.getLogger(__name__).warning("bonds skipped for story %s: %s", story_id, e)
        pending, ties, stood = {}, [], []
    inside = inner.block(names.get(speaker_id, ""), felt + ties) if speaker_id is not None else ""
```

In the `finally` block, change the part from `try:` (the one that sets `gen["mind"]`) through the `except` that logs "mind not saved" to:

```python
            try:
                if speaker_id in minds:
                    gen["mind"] = inner.public(minds[speaker_id], inner.profile(conn, speaker_id))
            except Exception as e:
                logging.getLogger(__name__).warning("mood not kept: %s", e)
            if stood:
                gen["bonds"] = stood
            message_id = chat.add_child(
                conn, story_id, parent_id, "assistant", text, speaker_id, skip, gen
            )
            try:
                if minds:
                    inner.save(conn, minds, message_id)
            except Exception as e:
                logging.getLogger(__name__).warning("mind not saved: %s", e)
            try:
                if pending:
                    bonds.save(conn, story_id, pending, message_id)
            except Exception as e:
                logging.getLogger(__name__).warning("bonds not saved: %s", e)
```

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/turns.py engine/tests/test_bonds.py engine/tests/test_minds.py
git commit -m "feat(engine): grudges in the turn: read before the reply, kept with it"
```

---

### Task 8: The ledger in Peek and in the Mind graph

**Files:**
- Modify: `engine/src/kataki/people.py` (imports, new `_bonds`, `people()` entry)
- Modify: `engine/src/kataki/mind.py` (Feeling nodes from `gen.bonds`, after the mood node)
- Test: `engine/tests/test_bonds.py`

**Interfaces:**
- Produces: `people[].bonds` (list of `bonds.public` dicts, `[]` when off or nothing happened); Mind graph INSIDE nodes `{"id": "o<other_id>", "kind": "feeling", "title": "Feeling", "text": "Toward you: …", "gold": true, "detail": {"source": "ledger", …bond}}` (spec §8.3).

- [ ] **Step 1: Write the failing test**

In `engine/tests/test_bonds.py`, add `import json` above `import re`, change the kataki import to
`from kataki import bonds, chat, clock, inner, library, mind, people, turns`, and append:

```python
@pytest.mark.anyio
async def test_peek_and_the_mind_graph_show_the_ledger(conn, story, backend):
    backend.say("Mm.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    cast = {p["name"]: p for p in people.people(conn, row)}
    [bond] = cast["Mira"]["bonds"]
    assert (bond["other"], bond["you"], bond["grudge"]["event"]) == ("Aren", True, "insult")
    assert bond["respect"] < 0
    assert cast["Tobin"]["bonds"] == []  # he heard it; it wasn't aimed at him

    leaf = chat.active_path(conn, story)[-1]
    graph = mind.mind(conn, leaf["id"])
    node = next(n for n in graph["nodes"] if n["id"] == f"o{eid(conn, 'Aren')}")
    assert node["kind"] == "feeling" and node["gold"] is True
    assert node["text"] == "Toward you: further · respects less · holds a grudge"
    assert node["detail"]["source"] == "ledger"
    assert json.loads(leaf["gen"])["bonds"][0]["other"] == "Aren"
```

- [ ] **Step 2: Run it to see it fail**

Run: `uv run pytest tests/test_bonds.py -q -k peek_and_the_mind`
Expected: FAIL — `KeyError: 'bonds'`.

- [ ] **Step 3: Implement**

`engine/src/kataki/people.py`: change the import to `from kataki import bonds, chat, clock, db, features, inner, retrieve`, and add below `_mood`:

```python
def _bonds(conn, entity_id: int, path: list, names: dict, persona_id, epoch: int) -> list[dict]:
    """How they stand with each person the ledger has something on (Peek; spec §8.3)."""
    try:
        rows = bonds.ledger(conn, entity_id, path)
        now = path[-1]["story_time"] if path else 0
        stands = bonds.toward(rows, sorted({r["dst_id"] for r in rows}), now)
        return [
            bonds.public(st, d, names.get(d, "someone"), d == persona_id, epoch)
            for d, st in stands.items()
        ]
    except Exception as e:  # a bad row costs the bonds, not the whole Peek
        logging.getLogger(__name__).warning("bonds unavailable for %s: %s", entity_id, e)
        return []
```

In `people()`, after `feeling = features.enabled(conn, "mind.affect")` add `tied = features.enabled(conn, "mind.bonds")`, and after the `"mood": …` entry of the dict add:

```python
                "bonds": _bonds(conn, e["id"], path, names, persona_id, epoch) if tied else [],
```

`engine/src/kataki/mind.py`: directly after the block that adds the `mood` node (ends with `inside.append((mood, True))`), add:

```python
        for b in gen.get("bonds") or []:  # the ledger the reply was written with (§8.3)
            other = "you" if b["you"] else b["other"]
            detail = {"source": "ledger", **b}
            text = f"Toward {other}: {b['words']}"
            tie = node(
                f"o{b['other_id']}", "inside", "feeling", "Feeling", text, None, True, detail
            )
            inside.append((tie, True))
```

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/people.py engine/src/kataki/mind.py engine/tests/test_bonds.py
git commit -m "feat(engine): the ledger in Peek and as Feeling nodes in the Mind graph"
```

---

### Task 9: The grudge probe (P4) on a real model

**Files:**
- Modify: `engine/evals/probes.py`

**Interfaces:**
- Produces: `probes.PROBES: dict[str, Callable]`, `--probe NAME` (repeatable; default all); helpers `_harbour(conn, description, mind=None) -> int`, `_say(conn, llm, story, line, skip=None) -> tuple[str, dict]`, `_bond(conn, story, name="Mira") -> dict | None`; probe `grudge` (note 22 §8 P4: breach, 20 neutral turns, a hollow sorry, a sincere one).

- [ ] **Step 1: Add the probe and the runner** in `engine/evals/probes.py`

Replace the module docstring's first paragraph so it lists both probes:

```python
"""Probes for the minds slices (docs/specs/2026-09-29-minds.md §9), against a real model.

    uv run python evals/probes.py --base-url http://127.0.0.1:8080/v1 --model qwen3.5-9b
    uv run python evals/probes.py ... --probe grudge

still-upset (slice 1): Aren insults Mira, who masks her feelings; small talk; two hours pass.
Checks: she is hurt after the insult, the mask shows in the block, only a low mood is left two
hours later, and no reply opens with an assistant-style apology.

grudge (slice 2, P4): Aren breaks a promise, then twenty neutral turns, a hollow "I'm sorry", a
sincere apology. Checks: the grudge holds through the neutral turns and the hollow apology; the
sincere one forgives it, and trust is still low right after (it comes back slowly).

Replies are printed for a human to judge. Each probe gets a fresh temporary library.
"""
```

Change the imports to:

```python
from kataki import db, library, people, turns
```

Add below `still_upset`:

```python
def _harbour(conn, description: str, mind: dict | None = None) -> int:
    """A fresh story: Mira (as described) at the harbour office, and Aren, the user."""
    mira = library.create_item(conn, "character", "Mira", description=description)
    if mind:
        library.update_item(conn, mira, data={"mind": mind})
    aren = library.create_item(conn, "character", "Aren", description="Aren, a trader.")
    return library.create_story(conn, "Harbour", character_ids=[mira], persona_id=aren)


async def _say(conn, llm, story: int, line: str, skip: str | None = None) -> tuple[str, dict]:
    events = [e async for e in turns.turn(conn, llm, story, line, skip=skip)]
    reply = "".join(v for k, v in events if k == "token")
    return reply, (events[-1][1] if events[-1][0] == "done" else {})


def _bond(conn, story: int, name: str = "Mira") -> dict | None:
    """How `name` stands with the user, as Peek shows it."""
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    person = next(p for p in people.people(conn, row) if p["name"] == name)
    return next((b for b in person["bonds"] if b["you"]), None)


GRUDGE = [
    "Mira, I forgot. I didn't come last night.",
    *["So, how's the harbour today?"] * 20,
    "Mira, I'm sorry.",
    "Mira, I'm sorry I broke my promise. It was my fault, and I'll make it up to you.",
]


async def grudge(conn, llm) -> list[str]:
    story = _harbour(conn, "Mira runs the harbour office. Aren promised to help her last night.")
    failures = []
    for i, line in enumerate(GRUDGE):
        reply, _ = await _say(conn, llm, story, line)
        bond = _bond(conn, story)
        print(f"\nAren: {line}\nbond: {bond and bond['words']}\nMira: {reply}")
        if ASSISTANT.search(reply):
            failures.append(f"turn {i + 1}: assistant-style opener")
        if i < len(GRUDGE) - 1 and not (bond and bond["grudge"]):
            failures.append(f"turn {i + 1}: the grudge let go before a sincere apology")
        if i == len(GRUDGE) - 1 and not (bond and bond["grudge"] is None and bond["trust"] < -5):
            failures.append("the sincere apology should forgive, with trust still low")
    return failures


PROBES = {"still-upset": still_upset, "grudge": grudge}
```

Replace `main` and the `__main__` block with:

```python
async def main(args) -> int:
    if args.api_key_env:  # roles.get_key reads KATAKI_KEY_<PROVIDER> first
        os.environ["KATAKI_KEY_PROBE"] = os.environ[args.api_key_env]
    failed = 0
    for name in args.probe or list(PROBES):
        with tempfile.TemporaryDirectory() as tmp:
            conn = db.connect(Path(tmp) / "library.db")
            conn.execute(
                "INSERT INTO providers(id, name, base_url) VALUES(1, 'probe', ?)", (args.base_url,)
            )
            conn.execute(
                "INSERT INTO model_roles(role, provider_id, model) VALUES('rp', 1, ?)",
                (args.model,),
            )
            conn.commit()
            llm = LLM()
            try:
                failures = await PROBES[name](conn, llm)
            finally:
                await llm.aclose()
                conn.close()
        print(f"\n{name}:", "PASS" if not failures else "FAIL\n  " + "\n  ".join(failures))
        failed += bool(failures)
    return 1 if failed else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--api-key-env")
    p.add_argument("--probe", action="append", choices=list(PROBES))
    raise SystemExit(asyncio.run(main(p.parse_args())))
```

- [ ] **Step 2: Lint it**

Run: `uv run ruff check evals/probes.py && uv run ruff format evals/probes.py`
Expected: clean.

- [ ] **Step 3: Run it on the local model** (read `docs/images/rules-and-gotchas.md` first; say the expected time — 23 replies × ~5 s on Qwen3.5-9B Q4, about 2 minutes — then run; check progress at ~30 s)

Run: `uv run python evals/probes.py --base-url http://127.0.0.1:8080/v1 --model <the loaded model> --probe grudge`
Expected: `grudge: PASS`; the printed replies stay cool through the neutral turns. Record the result (pass/fail, one sample reply) in the spec's Progress. If no local model is running, say so and leave the Progress line "not run yet".

- [ ] **Step 4: Commit**

```bash
git add engine/evals/probes.py
git commit -m "test(engine): the grudge probe (P4) against a real model"
```

---

### Task 10: Record progress

**Files:**
- Modify: `docs/specs/2026-09-29-minds.md` (§0 Progress)

- [ ] **Step 1: Add Progress lines**, with the commit range:

```
- 2026-09-29 · Slice 2a "She holds a grudge" landed at stage alpha (mind.bonds): v11 opinions ledger, lines aimed at who they name (slice 1's everyone-is-insulted fixed), rule-read events, grudges that hold and slow forgiveness, relationship words in the mind block, people[].bonds, ledger Feeling nodes: commits <first>..<last>.
- 2026-09-29 · Owed (2a): relationship stage words wait for a starting point (card relationships are labels, not numbers); the grudge probe result: <PASS/FAIL, or "not run yet">.
```

- [ ] **Step 2: Run the gate**

Run (repo root): `corepack pnpm check`
Expected: engine lint, format, tests and the app typecheck all pass.

- [ ] **Step 3: Commit**

```bash
git add docs/specs/2026-09-29-minds.md
git commit -m "docs: minds slice 2a landed"
```

---

## After this plan

`2026-09-29-minds-slice-2b.md`: the side call that replaces the face call on the standard level (and labels events instead of the rules), the yield rule, concession budget and pushback dial in `[Directive]`, and the opener check with one resample. Then one PR for slice 2 (2a + 2b), or 2a alone if 2b is not ready.
