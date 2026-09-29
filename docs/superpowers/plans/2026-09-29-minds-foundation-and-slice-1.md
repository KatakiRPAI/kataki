# Minds: Foundation + Slice 1 ("She's still upset") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every AI character a mood kept by code between turns (hurt now, low for hours after, a mask that leaks), plus the foundation every later slice and the online product need: library safety, feature flags with channels, anchored rows, and a usage record for every model call.

**Architecture:** A new pure module `inner.py` holds the affect core (fade, appraise, feel, regulate, render) with zero model calls. `turns._generate` asks it how everyone present feels after the latest line, renders the speaker's state into a `[Inside X right now]` block in the existing volatile tail, and stores one `mind_states` row per character anchored on the reply, so swipes and branches swap moods for free. `features.py` gates it by channel. `LLM.on_usage` records every call in `usage_log`.

**Tech Stack:** Python 3.12, stdlib `sqlite3`, numpy, model2vec (already installed), FastAPI, pytest with the scripted `FakeBackend` in `engine/tests/conftest.py`.

**Spec:** `docs/specs/2026-09-29-minds.md` (read §2–§6 and §8.1–§8.2 first). Design source: `docs/research/research_notes/Human like minds for Kataki/22_unified_architecture.md` §1, §2, §4 and `11_emotion_mood_anxiety.md` §9.

## Global Constraints

- Commands run from `engine/`: tests `uv run pytest -q`, lint `uv run ruff check . && uv run ruff format --check .`; the repo gate is `pnpm check` from the root.
- No new dependencies (numpy and model2vec are already there).
- Schema changes are forward-only migrations in `engine/src/kataki/db.py`, each with a test on a library from the previous version. This plan claims **v10**; if `SCHEMA_VERSION` is already 10 when you start, use the next free number everywhere this plan says 10.
- Nothing mind-related goes into the cached system block except the one constant `RULES` line (Task 8). The mind block lives in the volatile tail.
- The prompt gets words, never numbers, for any mind state.
- Commit after every task, Conventional Commits (`feat(engine): …`, `test(engine): …`), on the current branch; never push (AGENTS.md).
- Comment style matches the engine: short docstrings that say what and why; `ponytail:` comments on deliberate simplifications.

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `engine/src/kataki/db.py` | refuse newer libraries, back up before migrating, v10 tables, `live_messages`, `anchor_filter` | 1, 2 |
| `engine/src/kataki/__main__.py` | say `LIBRARY_TOO_NEW` and exit 3 | 1 |
| `engine/src/kataki/features.py` (new) | stages, channel, `enabled`, `listing` | 3 |
| `engine/src/kataki/server.py` | `GET /features`, `/health` channel+host, usage recorder wiring | 3, 4 |
| `engine/src/kataki/llm.py` | `Endpoint.role`, `Endpoint.story_id`, `LLM.on_usage` | 4 |
| `engine/src/kataki/roles.py` | stamp role and story on the endpoint | 4 |
| `engine/src/kataki/usage.py` (new) | one `usage_log` row per call | 4 |
| `engine/src/kataki/knobs.py` | `_own` becomes public `own` | 5 |
| `engine/src/kataki/inner.py` (new) | profile, baseline, affect core, sense, render, storage, `react` | 5, 6, 7, 8, 9 |
| `engine/src/kataki/context.py` | `inside` block, `mind` cap, `RULES` line | 8 |
| `engine/src/kataki/turns.py` | wire `react` into the turn; `gen.mind`; `done.mood`; lite face | 10 |
| `engine/src/kataki/people.py` | `mood` per character | 11 |
| `engine/src/kataki/mind.py` | Mood node | 11 |
| `engine/evals/probes.py` (new) | slice-1 probe against a real model | 12 |
| tests | `test_db.py`, `test_features.py`, `test_usage.py`, `test_inner.py`, `test_minds.py` | all |

---

### Task 1: Library safety (refuse newer, back up before migrating)

**Files:**
- Modify: `engine/src/kataki/db.py:1-71`
- Modify: `engine/src/kataki/__main__.py:41` (the `db.connect` in `serve`)
- Test: `engine/tests/test_db.py`

**Interfaces:**
- Produces: `db.LibraryTooNew(Exception)`; `db.connect(path)` raises it when `user_version > SCHEMA_VERSION`, and writes `backups/library-before-v{SCHEMA_VERSION}-from-v{old}.db` beside the library before migrating an existing one.

- [ ] **Step 1: Write the failing tests** (append to `engine/tests/test_db.py`)

```python
def test_a_library_from_a_newer_kataki_is_refused_and_left_alone(tmp_path):
    path = tmp_path / "new.db"
    newer = sqlite3.connect(path)
    newer.execute(f"PRAGMA user_version={db.SCHEMA_VERSION + 1}")
    newer.commit()
    newer.close()

    with pytest.raises(db.LibraryTooNew):
        db.connect(path)

    check = sqlite3.connect(path)
    assert check.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION + 1
    check.close()


def test_an_older_library_is_copied_before_it_is_migrated(tmp_path):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript((db.files("kataki") / "schema.sql").read_text(encoding="utf-8"))
    old.execute("PRAGMA user_version=1")
    old.execute("INSERT INTO stories(title) VALUES('kept')")
    old.commit()
    old.close()

    db.connect(path).close()

    [copy] = (tmp_path / "backups").glob("library-before-*.db")
    assert copy.name == f"library-before-v{db.SCHEMA_VERSION}-from-v1.db"
    saved = sqlite3.connect(copy)
    assert saved.execute("PRAGMA user_version").fetchone()[0] == 1
    assert saved.execute("SELECT title FROM stories").fetchone()[0] == "kept"
    saved.close()


def test_a_new_library_needs_no_copy(tmp_path):
    db.connect(tmp_path / "fresh.db").close()
    assert not (tmp_path / "backups").exists()
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_db.py -q -k "newer or copied or no_copy"`
Expected: FAIL — `AttributeError: module 'kataki.db' has no attribute 'LibraryTooNew'` and no backups folder.

- [ ] **Step 3: Implement** in `engine/src/kataki/db.py`

Add below `MIGRATIONS`:

```python
class LibraryTooNew(Exception):
    """The library was written by a newer Kataki. Opening it here could undo a migration it
    already has, so it is left exactly as it is."""


def _copy_before_migrating(conn: sqlite3.Connection, path: Path, version: int) -> None:
    """A copy of the library as it was, beside it, before any migration touches it. It lands in
    the backups folder, so Settings › Backups lists it and can restore it."""
    folder = Path(path).parent / "backups"
    folder.mkdir(parents=True, exist_ok=True)
    dest = sqlite3.connect(folder / f"library-before-v{SCHEMA_VERSION}-from-v{version}.db")
    try:
        conn.backup(dest)
    finally:
        dest.close()
```

Replace the body of the `try:` in `connect` with:

```python
        conn.execute("PRAGMA journal_mode=WAL")  # the first read of the file, and so the first
        conn.execute("PRAGMA foreign_keys=ON")  # per-connection, not just per migration
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise LibraryTooNew(
                f"This library is from a newer Kataki (schema {version}; this one reads up to"
                f" {SCHEMA_VERSION}). Update Kataki to open it."
            )
        if version == 0:
            conn.executescript(files("kataki").joinpath("schema.sql").read_text(encoding="utf-8"))
            version = 1
        elif version < SCHEMA_VERSION:
            _copy_before_migrating(conn, Path(path), version)
        for target in range(version + 1, SCHEMA_VERSION + 1):
            conn.executescript(MIGRATIONS[target])
        conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
```

In `engine/src/kataki/__main__.py`, replace `conn = db.connect(db_path)` inside `serve` with:

```python
    try:
        conn = db.connect(db_path)
    except db.LibraryTooNew as e:  # the shell reads this second line and says it
        print(json.dumps({"error": {"code": "LIBRARY_TOO_NEW", "message": str(e)}}), flush=True)
        sys.exit(3)
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_db.py -q`
Expected: all PASS (the existing migration test still passes; it now also leaves a copy in `tmp_path/backups`).

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/db.py engine/src/kataki/__main__.py engine/tests/test_db.py
git commit -m "feat(engine): refuse a newer library and copy an older one before migrating"
```

---

### Task 2: Migration v10 and anchored rows

**Files:**
- Modify: `engine/src/kataki/db.py` (`SCHEMA_VERSION`, `MIGRATIONS`, new `live_messages`, `anchor_filter`)
- Test: `engine/tests/test_db.py`

**Interfaces:**
- Produces: tables `mind_states(id, entity_id, story_time, state TEXT JSON, message_id, run_id)` and `usage_log(id, story_id, role, model, prompt_tokens, cached_tokens, completion_tokens, at)`; `db.live_messages(conn, story_id, leaf_id=None) -> set[int]`; `db.anchor_filter(runs: set[int], messages: set[int]) -> tuple[str, list[int]]`.

- [ ] **Step 1: Write the failing tests** (append to `engine/tests/test_db.py`)

```python
def test_v10_adds_minds_and_usage(tmp_path):
    path = tmp_path / "v9.db"
    old = db.connect(path)  # today's schema, then pretend it is v9 without the new tables
    old.executescript("DROP TABLE IF EXISTS mind_states; DROP TABLE IF EXISTS usage_log;")
    old.execute("PRAGMA user_version=9")
    old.commit()
    old.close()

    conn = db.connect(path)
    tables = {t["name"] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"mind_states", "usage_log"} <= tables
    conn.close()


def _msg(conn, story_id, parent_id, text):
    return conn.execute(
        "INSERT INTO messages(story_id, parent_id, role, text, story_time) VALUES(?, ?, 'user', ?, 0)",
        (story_id, parent_id, text),
    ).lastrowid


def test_anchored_rows_follow_the_branch(conn):
    story = _story(conn)
    root = _msg(conn, story, None, "root")
    kept = _msg(conn, story, root, "this take")
    other = _msg(conn, story, root, "another take")
    conn.execute("UPDATE stories SET active_leaf_id=? WHERE id=?", (kept, story))
    entity = conn.execute(
        "INSERT INTO entities(story_id, kind, name) VALUES(?, 'character', 'Mira')", (story,)
    ).lastrowid
    for anchor in (kept, other, None):
        conn.execute(
            "INSERT INTO mind_states(entity_id, story_time, state, message_id) VALUES(?, 0, ?, ?)",
            (entity, json.dumps({"anchor": anchor}), anchor),
        )

    live = db.live_messages(conn, story)
    assert live == {root, kept}
    where, args = db.anchor_filter(set(), live)
    seen = [
        json.loads(r["state"])["anchor"]
        for r in conn.execute(f"SELECT state FROM mind_states WHERE {where} ORDER BY id", args)
    ]
    assert seen == [kept, None]  # the other take's row is not on this branch
```

Add `import json` at the top of `test_db.py` if it is not there.

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_db.py -q -k "v10 or anchored"`
Expected: FAIL — `no such table: mind_states`.

- [ ] **Step 3: Implement** in `engine/src/kataki/db.py`

Set `SCHEMA_VERSION = 10` and add to `MIGRATIONS`:

```python
    10: (  # minds (docs/specs/2026-09-29-minds.md): how each character feels, anchored on the
        # message or run that wrote it; and what every model call used, in both products
        "CREATE TABLE mind_states("
        " id INTEGER PRIMARY KEY,"
        " entity_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,"
        " story_time INTEGER NOT NULL, state TEXT NOT NULL,"
        " message_id INTEGER REFERENCES messages ON DELETE CASCADE,"
        " run_id INTEGER REFERENCES extraction_runs ON DELETE CASCADE);"
        "CREATE INDEX ix_mind_states ON mind_states(entity_id, story_time);"
        "CREATE TABLE usage_log("
        " id INTEGER PRIMARY KEY,"
        " story_id INTEGER REFERENCES stories ON DELETE SET NULL,"
        " role TEXT NOT NULL, model TEXT NOT NULL,"
        " prompt_tokens INTEGER NOT NULL DEFAULT 0, cached_tokens INTEGER NOT NULL DEFAULT 0,"
        " completion_tokens INTEGER NOT NULL DEFAULT 0,"
        " at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);"
        "CREATE INDEX ix_usage_story ON usage_log(story_id);"
    ),
```

Replace `live_runs` with a shared path CTE and add the two helpers:

```python
def _path_cte(story_id: int, leaf_id: int | None) -> tuple[str, list[int]]:
    """A recursive CTE `up(id, parent_id)`: the branch that ends at `leaf_id` (default: the
    story's active leaf), leaf to root."""
    start = "SELECT id, parent_id FROM messages WHERE id=?"
    if leaf_id is None:
        start = "SELECT m.id, m.parent_id FROM messages m JOIN stories s ON s.active_leaf_id=m.id"
        start += " WHERE s.id=?"
    cte = (
        f"WITH RECURSIVE up(id, parent_id) AS ({start}"
        " UNION ALL SELECT m.id, m.parent_id FROM messages m JOIN up ON m.id=up.parent_id)"
    )
    return cte, [story_id if leaf_id is None else leaf_id]


def live_runs(conn: sqlite3.Connection, story_id: int, leaf_id: int | None = None) -> set[int]:
    """Runs whose rows count right now: finished ok, and extracted on the branch that ends at
    `leaf_id` (default: the active leaf).

    Every memory query filters through `live_filter`, which is why a swipe or a branch
    switch never has to touch memory.
    """
    cte, args = _path_cte(story_id, leaf_id)
    rows = conn.execute(
        f"{cte} SELECT r.id FROM extraction_runs r WHERE r.story_id=? AND r.status='ok'"
        " AND r.to_message_id IN (SELECT id FROM up)",
        (*args, story_id),
    )
    return {r["id"] for r in rows}


def live_messages(conn: sqlite3.Connection, story_id: int, leaf_id: int | None = None) -> set[int]:
    """The messages on the branch that ends at `leaf_id` (default: the active leaf)."""
    cte, args = _path_cte(story_id, leaf_id)
    return {r["id"] for r in conn.execute(f"{cte} SELECT id FROM up", args)}


def anchor_filter(runs: set[int], messages: set[int]) -> tuple[str, list[int]]:
    """SQL condition + args for rows anchored the minds way (spec §3): written by the user (no
    anchor), by a message on this branch, or by a live run. A swipe or branch switch therefore
    swaps the whole mind with no code of its own."""
    parts, args = ["(message_id IS NULL AND run_id IS NULL)"], []
    if messages:
        parts.append(f"message_id IN ({','.join('?' * len(messages))})")
        args += sorted(messages)
    if runs:
        parts.append(f"run_id IN ({','.join('?' * len(runs))})")
        args += sorted(runs)
    return "(" + " OR ".join(parts) + ")", args
```

- [ ] **Step 4: Run the whole engine suite** (the refactor of `live_runs` must not change behaviour)

Run: `uv run pytest -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/db.py engine/tests/test_db.py
git commit -m "feat(engine): v10 mind_states and usage_log, rows anchored on the branch"
```

---

### Task 3: Feature flags and channels

**Files:**
- Create: `engine/src/kataki/features.py`
- Modify: `engine/src/kataki/server.py` (`/health` at ~line 430; add `/features` beside it)
- Test: `engine/tests/test_features.py`

**Interfaces:**
- Produces: `features.STAGES`, `features.FEATURES: dict[str, str]`, `features.channel() -> str`, `features.enabled(conn, name, chan=None) -> bool`, `features.listing(conn, chan=None) -> dict`. Feature names used by this plan: `"mind.affect"`.

- [ ] **Step 1: Write the failing tests** (`engine/tests/test_features.py`)

```python
"""Which features are on: stage vs channel, and the user's own switch."""

import pytest

from kataki import features


@pytest.fixture
def staged(monkeypatch):
    monkeypatch.setattr(features, "FEATURES", {"a": "alpha", "b": "beta", "s": "stable"})


def on(conn, chan):
    return {name for name in features.FEATURES if features.enabled(conn, name, chan)}


def test_each_channel_gets_its_stage_and_everything_past_it(conn, staged):
    assert on(conn, "alpha") == {"a", "b", "s"}
    assert on(conn, "beta") == {"b", "s"}
    assert on(conn, "stable") == {"s"}


def test_the_user_can_switch_off_anywhere_and_on_early_except_on_stable(conn, staged):
    conn.execute("INSERT INTO settings(key, value) VALUES('features.s', 'false')")
    conn.execute("INSERT INTO settings(key, value) VALUES('features.a', 'true')")
    assert on(conn, "beta") == {"a", "b"}
    assert on(conn, "stable") == set()


def test_the_channel_comes_from_the_build(monkeypatch):
    monkeypatch.setenv("KATAKI_CHANNEL", "beta")
    assert features.channel() == "beta"
    monkeypatch.setenv("KATAKI_CHANNEL", "nonsense")
    assert features.channel() == "stable"  # an unknown value errs toward the safe side
    monkeypatch.delenv("KATAKI_CHANNEL")
    assert features.channel() == "alpha"  # a source checkout sees everything


def test_listing_says_stage_and_state(conn, staged):
    listed = features.listing(conn, "beta")
    assert listed["channel"] == "beta"
    assert listed["features"]["a"] == {"stage": "alpha", "on": False}
```

- [ ] **Step 2: Run to see it fail**

Run: `uv run pytest tests/test_features.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'kataki.features'`.

- [ ] **Step 3: Implement** `engine/src/kataki/features.py`

```python
"""Which features are on (docs/specs/2026-09-29-minds.md §5).

Every feature has a stage; every build (desktop) or account (online) has a channel. A feature
is on when its stage is at or past the channel's: alpha gets everything, beta gets beta and
stable, stable gets stable. The user can switch any feature off, and an earlier-stage one on
unless they are on stable. One registry serves the desktop app and Kataki online.
"""

import os
import sqlite3

from kataki import knobs

STAGES = ("alpha", "beta", "stable")
FEATURES = {
    "mind.affect": "alpha",  # slice 1: moods that last
}


def channel() -> str:
    """The build's channel. Electron sets KATAKI_CHANNEL from the app version (-alpha.N, -beta.N,
    else stable); a source checkout or a headless engine without it is alpha."""
    value = os.environ.get("KATAKI_CHANNEL", "alpha")
    return value if value in STAGES else "stable"


def enabled(conn: sqlite3.Connection, name: str, chan: str | None = None) -> bool:
    chan = chan or channel()
    choice = knobs.setting(conn, f"features.{name}", None)
    if choice is False:
        return False
    if choice is True and chan != "stable":
        return True
    return STAGES.index(FEATURES[name]) >= STAGES.index(chan)


def listing(conn: sqlite3.Connection, chan: str | None = None) -> dict:
    chan = chan or channel()
    return {
        "channel": chan,
        "features": {
            name: {"stage": stage, "on": enabled(conn, name, chan)}
            for name, stage in FEATURES.items()
        },
    }
```

In `engine/src/kataki/server.py`, add `features` to the `from kataki import …` line, change the health handler's return to
`{"status": "ok", "version": __version__, "schema": schema, "channel": features.channel(), "host": "desktop"}`, and add next to it:

```python
    @app.get("/features")
    async def list_features():
        return features.listing(conn)
```

Add one API test to `engine/tests/test_features.py`:

```python
def test_the_api_lists_features(conn):
    from fastapi.testclient import TestClient

    from kataki.server import create_app

    client = TestClient(create_app(conn, "t"), headers={"Authorization": "Bearer t"})
    body = client.get("/features").json()
    assert body["features"]["mind.affect"]["stage"] == "alpha"
    assert client.get("/health").json()["host"] == "desktop"
```

(If `create_app`'s positional order differs, match `engine/tests/test_api.py`'s client fixture.)

- [ ] **Step 4: Run**

Run: `uv run pytest tests/test_features.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/features.py engine/src/kataki/server.py engine/tests/test_features.py
git commit -m "feat(engine): feature stages and release channels"
```

---

### Task 4: A usage row for every model call

**Files:**
- Modify: `engine/src/kataki/llm.py` (`Endpoint`, `LLM.__init__`, `chat_stream`, `_complete`, `embed`)
- Modify: `engine/src/kataki/roles.py:85-91` (`resolve`)
- Create: `engine/src/kataki/usage.py`
- Modify: `engine/src/kataki/server.py` (`create_app`, right after `llm = llm or LLM()`)
- Test: `engine/tests/test_usage.py`

**Interfaces:**
- Consumes: `usage_log` (Task 2).
- Produces: `Endpoint.role: str = ""`, `Endpoint.story_id: int | None = None`; `LLM.on_usage: Callable[[Endpoint, dict], None] | None`; `usage.record(conn, ep, usage) -> None`. Track B (online) replaces `on_usage` with the host's meter.

- [ ] **Step 1: Write the failing tests** (`engine/tests/test_usage.py`)

```python
"""Every model call leaves one usage row: role, model, tokens."""

import functools

import pytest

from kataki import library, roles, turns, usage
from kataki.llm import Endpoint

pytestmark = pytest.mark.anyio


def rows(conn):
    return [
        tuple(r)
        for r in conn.execute(
            "SELECT story_id, role, model, prompt_tokens, completion_tokens FROM usage_log"
        )
    ]


async def test_a_reply_is_recorded_with_its_story_and_role(local_model, backend):
    conn = local_model
    mira = library.create_item(conn, "character", "Mira")
    aren = library.create_item(conn, "character", "Aren")
    story = library.create_story(conn, "s", character_ids=[mira], persona_id=aren)
    llm = backend.llm
    llm.on_usage = functools.partial(usage.record, conn)
    backend.say({"content": "Hello.", "usage": {"prompt_tokens": 120, "completion_tokens": 3}})

    [event async for event in turns.turn(conn, llm, story, "Hi, Mira.")]

    assert rows(conn) == [(story, "rp", "rp-model", 120, 3)]


async def test_a_json_call_is_recorded_too(conn, backend):
    llm = backend.llm
    seen = []
    llm.on_usage = lambda ep, used: seen.append((ep.role, used["completion_tokens"]))
    backend.say({"content": '{"x": 1}', "usage": {"prompt_tokens": 9, "completion_tokens": 4}})
    ep = Endpoint("http://fake/v1", "u", role="utility")

    await llm.complete_json(ep, [{"role": "user", "content": "x"}], {"type": "object"}, dict)

    assert seen == [("utility", 4)]


def test_resolve_stamps_the_role_and_story(local_model):
    ep = roles.resolve(local_model, "utility", 7)
    assert (ep.role, ep.story_id) == ("utility", 7)
```

- [ ] **Step 2: Run to see it fail**

Run: `uv run pytest tests/test_usage.py -q`
Expected: FAIL — `ImportError: cannot import name 'usage'`.

- [ ] **Step 3: Implement**

In `engine/src/kataki/llm.py`, add two fields at the end of `Endpoint` (after `params`):

```python
    role: str = ""  # which job asked (rp, utility, embed…): usage rows and online billing
    story_id: int | None = None  # the story it was for, if any
```

In `LLM.__init__`, after `self._rejected = …`:

```python
        # called with (endpoint, usage) after every call that reports usage: the desktop
        # records it in usage_log, Kataki online bills it (spec §4)
        self.on_usage: Callable[[Endpoint, dict], None] | None = None
```

(`Callable` is already imported for `complete_json`; if not, import it from `collections.abc`.)

Add a method to `LLM`:

```python
    def _used(self, ep: Endpoint, usage: dict | None) -> None:
        if usage and self.on_usage:
            self.on_usage(ep, usage)
```

In `chat_stream`, just before `yield ("done", …)`:

```python
        # ponytail: a reply stopped mid-stream never gets the final usage chunk, so it is not
        # recorded; Kataki online meters those from streamed length (track B3)
        self._used(ep, usage)
```

In `_complete`: build the body with `self._body(ep, messages if strict else told, stream=True, stream_options={"include_usage": True})`; before the `try:` set `usage = None`; inside the chunk loop add `usage = chunk.get("usage") or usage`; right before `return "".join(text)` add `self._used(ep, usage)`.

In `embed`, before the `return`: `self._used(ep, r.json().get("usage"))`.

In `engine/src/kataki/roles.py` `resolve`, add `role=role, story_id=story_id,` to the `Endpoint(...)` call.

Create `engine/src/kataki/usage.py`:

```python
"""What every model call used (docs/specs/2026-09-29-minds.md §4): one row per call, in both
products. On the desktop it answers "what did this story cost me?"; online the same numbers bill.
"""

import sqlite3

from kataki.llm import Endpoint


def record(conn: sqlite3.Connection, ep: Endpoint, usage: dict) -> None:
    # ponytail: llama.cpp reports cache hits in `timings.cache_n`, not here; context_log keeps
    # those for replies, and local calls cost nothing to bill
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
    with conn:
        conn.execute(
            "INSERT INTO usage_log(story_id, role, model, prompt_tokens, cached_tokens,"
            " completion_tokens) VALUES(?, ?, ?, ?, ?, ?)",
            (
                ep.story_id,
                ep.role or "other",
                ep.model,
                usage.get("prompt_tokens") or 0,
                cached,
                usage.get("completion_tokens") or 0,
            ),
        )
```

In `engine/src/kataki/server.py` `create_app`, right after `llm = llm or LLM()`:

```python
    if llm.on_usage is None:  # the host may bring its own meter (Kataki online)
        llm.on_usage = functools.partial(usage.record, conn)
```

(add `import functools` and `usage` to the imports).

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -q`
Expected: all PASS. If a test compares a request body exactly and now sees `stream_options` in a JSON call, add it to that expected body.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/llm.py engine/src/kataki/roles.py engine/src/kataki/usage.py engine/src/kataki/server.py engine/tests/test_usage.py
git commit -m "feat(engine): record the role, model and tokens of every model call"
```

---

### Task 5: The mind profile

**Files:**
- Modify: `engine/src/kataki/knobs.py` (rename `_own` → `own`, 3 call sites in the file)
- Create: `engine/src/kataki/inner.py` (first part)
- Test: `engine/tests/test_inner.py`

**Interfaces:**
- Produces: `knobs.own(conn, entity_id) -> dict`; `inner.DEFAULT: dict`; `inner.shape(own: dict) -> dict` (defaults merged one level deep); `inner.profile(conn, entity_id) -> dict`; `inner.mean(prof, axis) -> float`; `inner.baseline(prof) -> dict[str, float]` with keys `v`, `a`, `d` in [-1, 1].

- [ ] **Step 1: Write the failing tests** (`engine/tests/test_inner.py`)

```python
"""The affect core: pure functions, story minutes, no model."""

import re

import numpy as np
import pytest

from kataki import inner, library


def test_a_profile_fills_what_the_card_leaves_out():
    p = inner.shape({"axes": {"dominance": [80, 10]}, "regulation": {"style": "suppress"}})
    assert inner.mean(p, "dominance") == 80
    assert inner.mean(p, "warmth") == 50  # default kept beside the override
    assert p["regulation"] == {"style": "suppress", "capacity": 0.5}


def test_warm_people_start_brighter_and_dominant_ones_stronger():
    cold = inner.baseline(inner.shape({"axes": {"warmth": [20, 10]}}))
    warm = inner.baseline(inner.shape({"axes": {"warmth": [80, 10]}}))
    boss = inner.baseline(inner.shape({"axes": {"dominance": [90, 10]}}))
    assert warm["v"] > cold["v"]
    assert boss["d"] > 0.2


def test_the_profile_is_read_from_the_library_character(conn):
    mira = library.create_item(conn, "character", "Mira")
    library.update_item(conn, mira, data={"mind": {"anxiety": 0.8}})
    story = library.create_story(conn, "s", character_ids=[mira])
    entity = conn.execute(
        "SELECT id FROM entities WHERE name='Mira' AND story_id=?", (story,)
    ).fetchone()["id"]
    assert inner.profile(conn, entity)["anxiety"] == 0.8
```

- [ ] **Step 2: Run to see it fail**

Run: `uv run pytest tests/test_inner.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'kataki.inner'`.

- [ ] **Step 3: Implement**

In `engine/src/kataki/knobs.py`, rename `def _own(` to `def own(` and update its three callers in the same file (`decay`, `can_doubt`, `character_model`). Keep the docstring.

Create `engine/src/kataki/inner.py`:

```python
"""How a character feels right now, kept by code between turns (docs/specs/2026-09-29-minds.md).

Emotions fade on story time (half-life ~25 story-minutes); mood follows them and drifts back to
the character's baseline over hours; what they show can differ from what they feel, and a mask
held too long leaks as a tell. The model never sets any of this: code reads what happened to
them, and the prompt gets the result in words. Zero model calls.

ponytail: every constant here is an estimate from the research (note 11 §9); tune them on the
probes (evals/probes.py), not by feel.
"""

import sqlite3

from kataki import knobs

DEFAULT = {  # research note 22 §1; the profile editor fills the rest later
    "axes": {  # [mean 0-100, spread 0-30]
        "dominance": [50, 10],
        "warmth": [50, 10],
        "candor": [50, 10],
        "honesty": [60, 5],
        "yielding": [50, 10],
        "volatility": [40, 10],
    },
    "attachment": {"anxiety": 0.2, "avoidance": 0.2},
    "anxiety": 0.2,
    "coping": 0.6,
    "regulation": {"style": "express", "capacity": 0.5},  # express|suppress|reappraise|avoid
    "inertia_h": 6,  # mood half-life, story hours
    "susceptibility": 0.4,
}


def shape(own: dict) -> dict:
    """The defaults with a character's own values laid over them, one level deep."""
    prof = {k: dict(v) if isinstance(v, dict) else v for k, v in DEFAULT.items()}
    for key, value in own.items():
        if isinstance(prof.get(key), dict) and isinstance(value, dict):
            prof[key] = {**prof[key], **value}
        else:
            prof[key] = value
    return prof


def profile(conn: sqlite3.Connection, entity_id: int) -> dict:
    """The character's mind profile: their library item's `data.mind` over the defaults."""
    return shape(knobs.own(conn, entity_id).get("mind") or {})


def mean(prof: dict, axis: str) -> float:
    return prof["axes"].get(axis, [50, 10])[0]


def _clamp(x: float) -> float:
    return round(max(-1.0, min(1.0, x)), 3)


def baseline(prof: dict) -> dict[str, float]:
    """Resting mood in PAD space (valence, arousal, dominance), from temperament."""
    if b := prof.get("baseline"):
        return {"v": b[0], "a": b[1], "d": b[2]}
    warm, vol, dom = mean(prof, "warmth"), mean(prof, "volatility"), mean(prof, "dominance")
    anx = prof["anxiety"]
    return {
        "v": _clamp(0.6 * (warm - 50) / 100 - 0.3 * anx + 0.1),
        "a": _clamp(0.4 * (vol - 50) / 100 + 0.3 * anx - 0.1),
        "d": _clamp(0.8 * (dom - 50) / 100),
    }
```

- [ ] **Step 4: Run**

Run: `uv run pytest tests/test_inner.py tests/test_knobs.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/knobs.py engine/src/kataki/inner.py engine/tests/test_inner.py
git commit -m "feat(engine): mind profiles with defaults and a resting mood"
```

---

### Task 6: Feelings that fade, and a mask that leaks

**Files:**
- Modify: `engine/src/kataki/inner.py`
- Test: `engine/tests/test_inner.py`

**Interfaces:**
- Consumes: `shape`, `baseline`, `mean` (Task 5).
- Produces (all pure): `FEEL: dict[label, ((v, a, d), face)]`, `NEGATIVE: frozenset[str]`, `TELLS: dict[str, str]`, `fresh(prof, now) -> State`, `tick(state, now, prof) -> State`, `appraise(event, strength, prof, state) -> list[tuple[str, float]]`, `feel(state, label, intensity, cause, prof) -> State`, `regulate(state, prof) -> State`. `State` is a dict: `{"mood": {"v","a","d"}, "emotions": [{"label","i","cause","t"}], "reg_load": float, "shown": None | {"label","i","tell"}, "t": int}`.

- [ ] **Step 1: Write the failing tests** (append to `engine/tests/test_inner.py`)

```python
P = inner.shape({})


def hurt(prof=P, i=0.8, now=0):
    return inner.feel(inner.fresh(prof, now), "hurt", i, "Aren said something cruel", prof)


def test_an_emotion_halves_every_half_life_and_then_is_gone():
    state = hurt()
    assert inner.tick(state, 25, P)["emotions"][0]["i"] == pytest.approx(0.4, abs=0.01)
    assert inner.tick(state, 300, P)["emotions"] == []


def test_mood_stays_low_for_hours_and_settles_within_a_day():
    base = inner.baseline(P)["v"]
    state = hurt()
    assert state["mood"]["v"] < base - 0.2
    assert inner.tick(state, 120, P)["mood"]["v"] < base - inner.MOOD_SHOWS
    assert inner.tick(state, 24 * 60, P)["mood"]["v"] > base - inner.MOOD_SHOWS


def test_an_insult_hurts_the_meek_and_angers_the_dominant():
    meek = inner.shape({"axes": {"dominance": [30, 10]}})
    boss = inner.shape({"axes": {"dominance": [80, 10]}})
    assert inner.appraise("insult", 1.0, meek, inner.fresh(meek, 0))[0][0] == "hurt"
    assert inner.appraise("insult", 1.0, boss, inner.fresh(boss, 0))[0][0] == "angry"


def test_an_anxious_person_also_gets_anxious():
    worrier = inner.shape({"anxiety": 0.8})
    labels = [label for label, _ in inner.appraise("insult", 1.0, worrier, inner.fresh(worrier, 0))]
    assert labels == ["hurt", "anxious"]


def test_an_apology_only_relieves_someone_who_is_hurting():
    assert inner.appraise("apology", 1.0, P, inner.fresh(P, 0)) == []
    state = hurt()
    [(label, _)] = inner.appraise("apology", 1.0, P, state)
    eased = inner.feel(state, label, 0.4, "Aren apologised", P)
    assert eased["emotions"][0]["label"] in ("hurt", "relieved")
    assert next(e for e in eased["emotions"] if e["label"] == "hurt")["i"] < 0.8


def test_at_most_three_feelings_are_held():
    state = inner.fresh(P, 0)
    for label in ("hurt", "anxious", "sad", "annoyed"):
        state = inner.feel(state, label, 0.5, "x", P)
    assert len(state["emotions"]) == 3


def test_a_suppressor_looks_calm_then_leaks_then_the_mask_slips():
    p = inner.shape({"regulation": {"style": "suppress", "capacity": 0.5}})
    first = inner.regulate(hurt(p, 0.7), p)
    assert first["shown"] == {"label": "calm", "i": 0.3, "tell": None}
    second = inner.regulate(first, p)
    assert second["shown"]["tell"] == inner.TELLS["hurt"]
    third = inner.regulate(second, p)
    assert third["shown"]["label"] == "hurt"


def test_good_feelings_are_never_masked():
    p = inner.shape({"regulation": {"style": "suppress", "capacity": 0.5}})
    glad = inner.feel(inner.fresh(p, 0), "glad", 0.6, "good news", p)
    assert inner.regulate(glad, p)["shown"]["label"] == "glad"
```

- [ ] **Step 2: Run to see them fail**

Run: `uv run pytest tests/test_inner.py -q`
Expected: FAIL — `AttributeError: module 'kataki.inner' has no attribute 'feel'`.

- [ ] **Step 3: Implement** (append to `engine/src/kataki/inner.py`)

```python
EMOTION_HALF_MIN = 25  # story minutes
LOAD_HALF_MIN = 60  # how fast holding a mask stops costing
MAX_EMOTIONS = 3
FLOOR = 0.08  # weaker than this, the feeling is gone
PUSH = 0.5  # how far one feeling moves mood toward its own anchor
MOOD_SHOWS = 0.05  # a mood this far from resting is worth a word
AROUSED = 0.15  # and this much more wound up than resting makes a low mood "on edge"

FEEL = {  # label -> ((valence, arousal, dominance), the sprite face it shows as)
    "calm": ((0.3, -0.4, 0.2), "neutral"),
    "content": ((0.5, -0.2, 0.3), "smiling"),
    "glad": ((0.6, 0.3, 0.3), "smiling"),
    "fond": ((0.6, 0.1, 0.1), "smiling"),
    "amused": ((0.5, 0.4, 0.3), "smiling"),
    "excited": ((0.6, 0.7, 0.3), "smiling"),
    "relieved": ((0.4, -0.3, 0.1), "smiling"),
    "surprised": ((0.1, 0.6, -0.1), "surprised"),
    "anxious": ((-0.4, 0.5, -0.4), "wary"),
    "afraid": ((-0.6, 0.7, -0.6), "wary"),
    "sad": ((-0.6, -0.3, -0.3), "neutral"),
    "hurt": ((-0.6, 0.2, -0.3), "wary"),
    "annoyed": ((-0.4, 0.3, 0.2), "doubtful"),
    "angry": ((-0.6, 0.7, 0.4), "wary"),
    "ashamed": ((-0.5, 0.2, -0.5), "wary"),
    "bored": ((-0.2, -0.6, 0.0), "neutral"),
}
NEGATIVE = frozenset(label for label, ((v, _, _), _) in FEEL.items() if v < 0)
TELLS = {  # how a masked feeling leaks
    "anxious": "over-explaining and fidgeting",
    "afraid": "glancing away",
    "sad": "going quiet, slower to answer",
    "hurt": "short answers, not meeting their eyes",
    "annoyed": "a flat tone",
    "angry": "clipped words",
    "ashamed": "steering away from the subject",
    "bored": "half-listening",
}


def fresh(prof: dict, now: int) -> dict:
    return {"mood": baseline(prof), "emotions": [], "reg_load": 0.0, "shown": None, "t": now}


def tick(state: dict, now: int, prof: dict) -> dict:
    """Time passes: feelings fade, mood settles back toward resting, a held mask costs less.
    Closed form, so a six-year skip costs the same as a minute."""
    dt = max(now - state["t"], 0)
    if not dt:
        return state
    fade = 0.5 ** (dt / EMOTION_HALF_MIN)
    settle = 0.5 ** (dt / (prof["inertia_h"] * 60))
    base = baseline(prof)
    return {
        **state,
        "emotions": [
            {**e, "i": round(e["i"] * fade, 3)}
            for e in state["emotions"]
            if e["i"] * fade >= FLOOR
        ],
        "mood": {c: round(base[c] + (state["mood"][c] - base[c]) * settle, 3) for c in "vad"},
        "reg_load": round(state["reg_load"] * 0.5 ** (dt / LOAD_HALF_MIN), 3),
        "t": now,
    }


def appraise(event: str, strength: float, prof: dict, state: dict) -> list[tuple[str, float]]:
    """What something that happened to them makes them feel, by temperament: the same insult
    hurts the meek and angers the dominant. -> [(label, intensity 0-1)]"""
    dom, warm = mean(prof, "dominance"), mean(prof, "warmth")
    hurting = any(e["label"] in ("hurt", "angry", "annoyed") for e in state["emotions"])
    felt = {
        "insult": [("angry" if dom >= 60 else "hurt", 0.7)],
        "threat": [("angry" if dom >= 70 else "afraid", 0.8)],
        "bad_news": [("sad", 0.3 + 0.4 * warm / 100)],
        "apology": [("relieved", 0.4)] if hurting else [],
        "good_news": [("glad", 0.5)],
        "praise": [("glad", 0.4 + 0.3 * warm / 100)],
    }[event]
    if event in ("insult", "threat") and prof["anxiety"] >= 0.5:
        felt.append(("anxious", 0.6 * prof["anxiety"]))
    gain = strength * (0.6 + 0.8 * mean(prof, "volatility") / 100)
    return [(label, round(min(1.0, i * gain), 3)) for label, i in felt]


def feel(state: dict, label: str, intensity: float, cause: str, prof: dict) -> dict:
    """Add one feeling: the strongest three are held, and mood moves toward it."""
    if prof["regulation"]["style"] == "reappraise" and label in NEGATIVE:
        intensity *= 1 - 0.4 * prof["regulation"]["capacity"]  # reappraisal really lowers it
    emotions = [dict(e) for e in state["emotions"]]
    if label == "relieved":  # relief eases what was hurting
        for e in emotions:
            if e["label"] in NEGATIVE:
                e["i"] = round(e["i"] * 0.6, 3)
    same = next((e for e in emotions if e["label"] == label), None)
    if same:
        same.update(i=max(same["i"], round(intensity, 3)), cause=cause, t=state["t"])
    else:
        emotions.append({"label": label, "i": round(intensity, 3), "cause": cause, "t": state["t"]})
    emotions = sorted((e for e in emotions if e["i"] >= FLOOR), key=lambda e: -e["i"])
    anchor = dict(zip("vad", FEEL[label][0], strict=True))
    mood = {
        c: round(state["mood"][c] + PUSH * intensity * (anchor[c] - state["mood"][c]), 3)
        for c in "vad"
    }
    return {**state, "emotions": emotions[:MAX_EMOTIONS], "mood": mood}


def regulate(state: dict, prof: dict) -> dict:
    """What they let show. Good feelings show. A bad one shows, or is masked or avoided by their
    regulation style; holding a mask builds up, first leaking as a tell, then slipping."""
    top = state["emotions"][0] if state["emotions"] else None
    style, capacity = prof["regulation"]["style"], prof["regulation"]["capacity"]
    load = state["reg_load"]
    if top is None:
        shown = None
    elif top["label"] not in NEGATIVE or style in ("express", "reappraise"):
        shown = {"label": top["label"], "i": top["i"], "tell": None}
    else:
        load = round(load + 0.5 * top["i"], 3)
        if load > 1.5 * capacity:  # the mask slips
            shown = {"label": top["label"], "i": top["i"], "tell": None}
        else:
            tell = TELLS.get(top["label"]) if load > capacity else None
            if style == "avoid":
                tell = "changing the subject"
            shown = {"label": "calm", "i": 0.3, "tell": tell}
    return {**state, "shown": shown, "reg_load": load}
```

- [ ] **Step 4: Run**

Run: `uv run pytest tests/test_inner.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/inner.py engine/tests/test_inner.py
git commit -m "feat(engine): feelings that fade, moods that linger, masks that leak"
```

---

### Task 7: Reading what a line meant to them

**Files:**
- Modify: `engine/src/kataki/inner.py`
- Test: `engine/tests/test_inner.py`

**Interfaces:**
- Produces: `EVENTS: tuple[str, ...]`, `SEEDS: dict[str, list[str]]`, `sense(text, model=None) -> tuple[str, float] | None`. `model` is anything with `encode(list[str]) -> array` (the built-in model2vec model, `embed.builtin()`), or None.

- [ ] **Step 1: Write the failing tests** (append)

```python
def test_words_say_what_a_line_was():
    assert inner.sense("Honestly, you're useless.") == ("insult", 1.0)
    assert inner.sense("I'm sorry, my dog died this morning.") == ("bad_news", 1.0)
    assert inner.sense("I'm sorry, I was wrong.") == ("apology", 1.0)
    assert inner.sense("The tide is out.") is None


class Meaning:
    """A stand-in for the built-in model: 'dirt' means an insult, nothing else means anything."""

    def encode(self, texts):
        return np.array(
            [[1.0, 0.0] if t in inner.SEEDS["insult"] or "dirt" in t else [0.0, 0.0] for t in texts]
        )


def test_meaning_catches_what_the_word_list_misses():
    assert inner.sense("You're dirt to me.", Meaning()) == ("insult", 1.0)
    assert inner.sense("The tide is out.", Meaning()) is None
```

- [ ] **Step 2: Run to see them fail**

Run: `uv run pytest tests/test_inner.py -q -k "words or meaning"`
Expected: FAIL — `AttributeError: … no attribute 'sense'`.

- [ ] **Step 3: Implement** (append to `inner.py`; add `import re` and `import numpy as np` at the top)

```python
EVENTS = ("threat", "insult", "bad_news", "apology", "good_news", "praise")  # first match wins
WORDS = {
    "threat": r"\b(i'?ll|i will|gonna) (kill|hurt|end) you\b|\bor else\b|\byou'?ll regret\b",
    "insult": r"\b(idiot|stupid|useless|pathetic|worthless|loser|moron|shut up|hate you"
    r"|disgusting|liar)\b",
    "bad_news": r"\b(died|passed away|got fired|lost my|broke up|bad news|in (the )?hospital)\b",
    "apology": r"\b(i'?m sorry|i apologi[sz]e|forgive me|my fault|i was wrong)\b",
    "good_news": r"\b(got the job|got in|we won|good news|i passed|engaged|promoted)\b",
    "praise": r"\b(thank you|thanks|proud of you|amazing|brilliant|beautiful|love you|well done"
    r"|you'?re the best)\b",
}
PATTERNS = {event: re.compile(words, re.IGNORECASE) for event, words in WORDS.items()}
SEEDS = {  # a few lines per event; their mean vector is what "means that" looks like
    "threat": ["I'll make you regret this.", "Do it or you'll get hurt.", "Watch your back."],
    "insult": ["You're worthless.", "Nobody could stand you.", "You're a joke."],
    "bad_news": ["Something terrible happened.", "We lost everything.", "She's gone."],
    "apology": ["I shouldn't have said that.", "That was unfair of me.", "Can you forgive me?"],
    "good_news": ["It worked out!", "They said yes!", "Guess what, we did it."],
    "praise": ["You did so well.", "I really admire you.", "You're wonderful."],
}
SENSE_MIN = 0.5  # cosine to an event's centre before it counts
_centres: dict[int, tuple[list[str], np.ndarray]] = {}


def _centre(model) -> tuple[list[str], np.ndarray]:
    key = id(model)  # ponytail: one entry per loaded model object; there is one per process
    if key not in _centres:
        names = list(SEEDS)
        m = np.stack([np.asarray(model.encode(SEEDS[n]), dtype=float).mean(axis=0) for n in names])
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        _centres[key] = names, np.divide(m, norms, out=np.zeros_like(m), where=norms > 0)
    return _centres[key]


def sense(text: str, model=None) -> tuple[str, float] | None:
    """What a line was, to the one who heard it: (event, strength 0-1), or None. A word list
    first (precise); then, with an embedding model, closeness in meaning (catches rewordings).
    ponytail: no negation handling ("you're not stupid" reads as an insult); slice 2's side call
    labels events on the standard level."""
    for event in EVENTS:
        if PATTERNS[event].search(text):
            return event, 1.0
    if model is None or not text.strip():
        return None
    names, centres = _centre(model)
    vec = np.asarray(model.encode([text]), dtype=float)[0]
    if not (norm := np.linalg.norm(vec)):
        return None
    sims = centres @ (vec / norm)
    best = int(np.argmax(sims))
    return (names[best], round(float(sims[best]), 3)) if sims[best] >= SENSE_MIN else None
```

- [ ] **Step 4: Run**

Run: `uv run pytest tests/test_inner.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/inner.py engine/tests/test_inner.py
git commit -m "feat(engine): read what a line meant, by words and by meaning"
```

---

### Task 8: The mind block, in words, in the tail

**Files:**
- Modify: `engine/src/kataki/inner.py`
- Modify: `engine/src/kataki/context.py` (`RULES`, `BASE_CAPS`, `build`)
- Test: `engine/tests/test_inner.py`, `engine/tests/test_context.py`

**Interfaces:**
- Produces: `inner.public(state, prof) -> dict | None` with keys `label, feels, shows, tell, word, why` (the §8.2 API shape); `inner.render(state, prof, name) -> str` ("" at rest); `inner.face(state) -> str` (one of `images.EXPRESSIONS`); `context.build(..., inside: str = "")`; a `mind` section in `Built.sections`.

- [ ] **Step 1: Write the failing tests**

Append to `engine/tests/test_inner.py`:

```python
def test_at_rest_there_is_nothing_to_say():
    assert inner.render(inner.fresh(P, 0), P, "Mira") == ""
    assert inner.public(inner.fresh(P, 0), P) is None


def test_the_block_is_words_never_numbers():
    block = inner.render(inner.regulate(hurt(), P), P, "Mira")
    assert block.startswith("[Inside Mira right now: show it, never say it]")
    assert "Feeling: very hurt (Aren said something cruel)." in block
    assert "Mood: low." in block
    assert not re.search(r"\d", block)


def test_a_mask_is_in_the_block_and_in_the_api():
    p = inner.shape({"regulation": {"style": "suppress", "capacity": 0.5}})
    state = inner.regulate(inner.regulate(hurt(p, 0.7), p), p)
    assert "Showing: calm. Hiding the hurt; it slips out as short answers" in inner.render(state, p, "Mira")
    mood = inner.public(state, p)
    assert (mood["label"], mood["shows"], mood["word"]) == ("hurt", "calm", "low")
    assert inner.face(state) == "neutral"  # the face shows the mask, not the feeling


def test_hours_later_only_the_mood_is_left():
    later = inner.tick(hurt(), 120, P)
    block = inner.render(later, P, "Mira")
    assert "Feeling:" not in block and "Mood: low." in block
```

Append to `engine/tests/test_context.py` (it already has the `story` fixture, the `EP` endpoint and `eid`):

```python
def test_the_inside_block_sits_before_the_directive_and_is_capped(conn, story):
    inside = "[Inside Mira right now: show it, never say it]\nFeeling: hurt."
    built = context.build(conn, story, eid(conn, "Mira"), EP, inside=inside)
    tail = built.messages[-1]["content"]
    assert tail.index("[Inside Mira") < tail.index("[Directive]")
    mind = next(s for s in built.sections if s["name"] == "mind")
    assert 0 < mind["tokens"] <= mind["cap"]
    assert "never state it" in built.messages[0]["content"]  # the one RULES line
```

- [ ] **Step 2: Run to see them fail**

Run: `uv run pytest tests/test_inner.py tests/test_context.py -q`
Expected: FAIL — `no attribute 'render'`, and `build() got an unexpected keyword argument 'inside'`.

- [ ] **Step 3: Implement**

Append to `inner.py`:

```python
NOUN = {"angry": "anger", "afraid": "fear", "anxious": "worry", "sad": "sadness",
        "ashamed": "shame", "annoyed": "annoyance", "bored": "boredom"}  # fmt: skip


def _strength(i: float) -> str:
    return "a little " if i < 0.3 else "very " if i >= 0.6 else ""


def mood_word(state: dict, prof: dict) -> str:
    base = baseline(prof)
    dv = state["mood"]["v"] - base["v"]
    da = state["mood"]["a"] - base["a"]
    if dv <= -MOOD_SHOWS:
        return "on edge" if da > AROUSED else "low"
    if dv >= MOOD_SHOWS:
        return "buzzing" if da > AROUSED else "in a good mood"
    return ""


def public(state: dict, prof: dict) -> dict | None:
    """The mood as the app shows it (spec §8.2); None at rest. `feels` is private (Peek);
    `shows` and `tell` are what anyone in the room could see."""
    emotions, word = state["emotions"], mood_word(state, prof)
    if not emotions and not word:
        return None
    top = emotions[0] if emotions else None
    shown = state.get("shown")
    return {
        "label": top and top["label"],
        "feels": ", and ".join(f"{_strength(e['i'])}{e['label']}" for e in emotions[:2]) or word,
        "shows": shown["label"] if shown else "calm",
        "tell": shown and shown["tell"],
        "word": word,
        "why": top and top["cause"],
    }


def render(state: dict, prof: dict, name: str) -> str:
    """The mind block for the prompt's tail: words, never numbers; empty at rest."""
    if (p := public(state, prof)) is None:
        return ""
    lines = [f"[Inside {name} right now: show it, never say it]"]
    if p["label"]:
        lines.append(f"Feeling: {p['feels']}" + (f" ({p['why']})." if p["why"] else "."))
        if p["shows"] != p["label"]:
            hiding = f"Showing: {p['shows']}. Hiding the {NOUN.get(p['label'], p['label'])}"
            lines.append(hiding + (f"; it slips out as {p['tell']}." if p["tell"] else "."))
    if p["word"]:
        lines.append(f"Mood: {p['word']}.")
    return "\n".join(lines)


def face(state: dict) -> str:
    """The sprite for what they show (the lite level's face, no model call)."""
    shown = state.get("shown")
    return FEEL[shown["label"]][1] if shown else "neutral"
```

In `engine/src/kataki/context.py`:

1. Append one line to `RULES` (end of the string):
   `\nAn [Inside …] note is private stage direction for that character: show it through behaviour and tone, never state it or mention the note.`
2. Add `"mind": 250,` to `BASE_CAPS`.
3. Add the parameter `inside: str = "",` to `build` after `directive`.
4. Change `tail_room = caps["memory"] + caps["flags"] + caps["examples"]` to include `+ caps["mind"]`.
5. After the `if memory_lines:` block and before `directive = f"{LENGTHS…`, add:

```python
    mind_text, mind_clipped = _clip(inside, caps["mind"], ratio)
    if mind_text:
        state.append(mind_text)
```

6. Add to `sections`, before the `tail` entry:

```python
        {
            "name": "mind",
            "tokens": estimate(mind_text, ratio) if mind_text else 0,
            "cap": caps["mind"],
            "evicted": mind_clipped,
        },
```

- [ ] **Step 4: Run the whole suite** (the history window moves a little because `tail_room` grew; prefix-stability tests must still pass)

Run: `uv run pytest -q`
Expected: all PASS. If a test asserts an exact history-token number, recompute it with the new `tail_room`.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/inner.py engine/src/kataki/context.py engine/tests/test_inner.py engine/tests/test_context.py
git commit -m "feat(engine): the mind block, in words, in the prompt's tail"
```

---

### Task 9: Remembering how they felt, per branch

**Files:**
- Modify: `engine/src/kataki/inner.py`
- Test: `engine/tests/test_inner.py`

**Interfaces:**
- Consumes: `db.anchor_filter` (Task 2), `chat.scene_of`, `chat.present_entities`, `chat.heard_by`.
- Produces: `inner.current(conn, entity_id, path, prof) -> dict | None`; `inner.react(conn, story_id, path, model=None) -> dict[int, dict]` (entity id → regulated state, nothing written); `inner.save(conn, states, message_id) -> None`.

- [ ] **Step 1: Write the failing test** (append)

```python
def test_react_hurts_whoever_heard_it_and_save_anchors_it(local_model):
    from kataki import chat, turns

    conn = local_model
    mira = library.create_item(conn, "character", "Mira")
    tobin = library.create_item(conn, "character", "Tobin")
    aren = library.create_item(conn, "character", "Aren")
    story = library.create_story(conn, "s", character_ids=[mira, tobin], persona_id=aren)
    ids = dict(conn.execute("SELECT name, id FROM entities WHERE story_id=?", (story,)).fetchall())
    turns.say(conn, story, "Tobin, you're useless.", audience=[ids["Tobin"]])  # a whisper

    path = chat.active_path(conn, story)
    states = inner.react(conn, story, path)
    assert states[ids["Tobin"]]["emotions"][0]["label"] == "hurt"
    assert states[ids["Mira"]]["emotions"] == []  # she didn't hear it

    inner.save(conn, states, path[-1]["id"])
    kept = inner.current(conn, ids["Tobin"], path, inner.profile(conn, ids["Tobin"]))
    assert kept["emotions"][0]["cause"] == 'Aren said "Tobin, you\'re useless."'
    assert inner.current(conn, ids["Tobin"], path[:-1], inner.shape({})) is None  # other branch
```

- [ ] **Step 2: Run to see it fail**

Run: `uv run pytest tests/test_inner.py -q -k react`
Expected: FAIL — `no attribute 'react'`.

- [ ] **Step 3: Implement** (append to `inner.py`; add `import json` and change the kataki import to `from kataki import chat, db, knobs`)

```python
def _quote(text: str, n: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def current(conn: sqlite3.Connection, entity_id: int, path: list, prof: dict) -> dict | None:
    """Their latest state on this branch (anchored on a message of `path`, or written by the
    user), or None when they have felt nothing yet. Not ticked to now."""
    where, args = db.anchor_filter(set(), {m["id"] for m in path})
    row = conn.execute(
        f"SELECT state FROM mind_states WHERE entity_id=? AND {where}"
        " ORDER BY story_time DESC, id DESC LIMIT 1",
        [entity_id, *args],
    ).fetchone()
    return json.loads(row["state"]) if row else None


def react(conn: sqlite3.Connection, story_id: int, path: list, model=None) -> dict[int, dict]:
    """Everyone here after the latest line, as they are now: faded to the present, stirred by
    that line if they heard it and it meant something, regulated. Nothing is written; the same
    path always gives the same answer, so a new take never feels it twice."""
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
    out = {}
    for e in cast:
        prof = profile(conn, e["id"])
        state = tick(current(conn, e["id"], path, prof) or fresh(prof, now), now, prof)
        if hit and last["id"] in chat.heard_by(conn, path, e["id"]):
            cause = f'{names.get(last["speaker_id"], "Someone")} said "{_quote(last["text"])}"'
            for label, intensity in appraise(*hit, prof, state):
                state = feel(state, label, intensity, cause, prof)
        out[e["id"]] = regulate(state, prof)
    return out


def save(conn: sqlite3.Connection, states: dict[int, dict], message_id: int) -> None:
    """One row per character, anchored on the reply they were part of."""
    with conn:
        conn.executemany(
            "INSERT INTO mind_states(entity_id, story_time, state, message_id) VALUES(?, ?, ?, ?)",
            [(eid, s["t"], json.dumps(s), message_id) for eid, s in states.items()],
        )
```

- [ ] **Step 4: Run**

Run: `uv run pytest tests/test_inner.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/inner.py engine/tests/test_inner.py
git commit -m "feat(engine): moods kept per branch, felt only by who heard"
```

---

### Task 10: Moods in the turn

**Files:**
- Modify: `engine/src/kataki/turns.py` (imports; `_expression` split; `_generate`)
- Test: `engine/tests/test_minds.py`

**Interfaces:**
- Consumes: `features.enabled`, `inner.react/profile/render/public/save/face`, `embed.builtin`.
- Produces: `gen.mind` on replies (the §8.2 mood object for the speaker); SSE `done["mood"]`; `messages.expression` from the shown feeling when `mind.level` is `lite` (no face call).

- [ ] **Step 1: Write the failing tests** (`engine/tests/test_minds.py`)

```python
"""Slice 1 end to end: moods that last, per branch, in the prompt, in the API."""

import json

import pytest

from kataki import chat, library, people, turns

pytestmark = pytest.mark.anyio


@pytest.fixture
def story(local_model):
    conn = local_model
    ids = {n: library.create_item(conn, "character", n) for n in ("Mira", "Tobin", "Aren")}
    library.update_item(
        conn, ids["Mira"], data={"mind": {"regulation": {"style": "suppress", "capacity": 0.5}}}
    )
    gull = library.create_item(conn, "place", "The Gull")
    return library.create_story(
        conn, "Low Tide", character_ids=[ids["Mira"], ids["Tobin"]], place_id=gull,
        persona_id=ids["Aren"],
    )  # fmt: skip


def eid(conn, name):
    return conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()["id"]


async def play(stream):
    return [e async for e in stream]


def tail(request):
    return request["messages"][-1]["content"]


async def test_an_insult_is_felt_before_the_reply_and_still_felt_after(conn, story, backend):
    backend.say("...", "Fine.")
    events = await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert "[Inside Mira right now" in tail(backend.requests[0])
    assert "Hiding the hurt" in tail(backend.requests[0])  # she suppresses
    assert events[-1][1]["mood"]["label"] == "hurt"

    await play(turns.turn(conn, backend.llm, story, "Anyway, Mira."))
    assert "Feeling:" in tail(backend.requests[1])  # a few story-minutes on, still there


async def test_two_hours_later_only_a_low_mood_is_left(conn, story, backend):
    backend.say("...", "Morning.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    await play(turns.turn(conn, backend.llm, story, "Mira?", skip="two hours later"))
    block = tail(backend.requests[1])
    assert "Feeling:" not in block and "Mood: low." in block


async def test_a_new_take_does_not_feel_it_twice(conn, story, backend):
    backend.say("First.", "Second.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    await play(turns.regenerate(conn, backend.llm, story))
    a, b = (
        json.loads(r["state"])
        for r in conn.execute(
            "SELECT state FROM mind_states WHERE entity_id=? ORDER BY id", (eid(conn, "Mira"),)
        )
    )
    assert a["emotions"] == b["emotions"]


async def test_switched_off_the_prompt_is_as_it_was(conn, story, backend):
    conn.execute("INSERT INTO settings(key, value) VALUES('features.mind.affect', 'false')")
    backend.say("Fine.")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    assert "[Inside" not in tail(backend.requests[0])
    assert conn.execute("SELECT COUNT(*) FROM mind_states").fetchone()[0] == 0


async def test_the_lite_level_picks_the_face_without_a_call(conn, story, backend):
    lib = conn.execute("SELECT lib_item_id FROM entities WHERE name='Tobin'").fetchone()[0]
    library.update_item(conn, lib, data={"pack": {"neutral": 1}})
    conn.execute("INSERT INTO settings(key, value) VALUES('mind.level', '\"lite\"')")
    backend.say("Hey.")  # one reply and nothing else: a face call would find no script
    await play(turns.turn(conn, backend.llm, story, "Tobin, you're useless."))
    leaf = chat.active_path(conn, story)[-1]
    assert leaf["expression"] == "wary"  # Tobin expresses: hurt shows as wary
    assert len(backend.requests) == 1
```

- [ ] **Step 2: Run to see them fail**

Run: `uv run pytest tests/test_minds.py -q`
Expected: FAIL — no `[Inside` block in the prompt.

- [ ] **Step 3: Implement** in `engine/src/kataki/turns.py`

Imports: add `import asyncio` and extend `from kataki import …` with `features, inner`.

Split the pack check out of `_expression`:

```python
def _has_pack(conn: sqlite3.Connection, speaker_id: int) -> bool:
    row = conn.execute(
        "SELECT l.data FROM entities e JOIN lib_items l ON l.id = e.lib_item_id WHERE e.id=?",
        (speaker_id,),
    ).fetchone()
    return bool(row and json.loads(row["data"]).get("pack"))
```

and make `_expression` start with `if not _has_pack(conn, speaker_id): return None` instead of its own query.

In `_generate`, right after the `names = dict(...)` statement:

```python
    minds: dict[int, dict] = {}  # everyone here, as they feel after the latest line
    if features.enabled(conn, "mind.affect"):
        minds = inner.react(conn, story_id, path, await asyncio.to_thread(embed.builtin))
    inside = ""
    if speaker_id in minds:
        inside = inner.render(minds[speaker_id], inner.profile(conn, speaker_id), names[speaker_id])
```

Pass `inside=inside` to **both** `context.build(...)` calls in `_generate`.

In the `finally:` block, just before `message_id = chat.add_child(...)`:

```python
            if speaker_id in minds:
                gen["mind"] = inner.public(minds[speaker_id], inner.profile(conn, speaker_id))
```

and right after `message_id = chat.add_child(...)`:

```python
            if minds:
                inner.save(conn, minds, message_id)
```

Replace the face block after a successful reply:

```python
        face = None  # the reply is already on screen; its face follows a moment later
        if speaker_id is not None:
            at = time.monotonic()
            if knobs.setting(conn, "mind.level", "standard") == "lite" and speaker_id in minds:
                if _has_pack(conn, speaker_id):  # lite: the face is what they show, no call
                    face = inner.face(minds[speaker_id])
                    with conn:
                        conn.execute(
                            "UPDATE messages SET expression=? WHERE id=?", (face, message_id)
                        )
            else:
                face = await _expression(
                    conn, llm, story_id, speaker_id, message_id, name, text, get_key
                )
            if face:  # the face's time joins the trace
                with conn:
                    conn.execute(
                        "UPDATE messages SET gen=json_set(gen, '$.trace.ms.face', ?) WHERE id=?",
                        (ms(at), message_id),
                    )
```

Add to the `done` payload: `"mood": (json.loads(chat.get_message(conn, message_id)["gen"]) or {}).get("mind"),`

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -q`
Expected: all PASS. Older tests that send lines with words like "sorry" or "thanks" now also carry an `[Inside` block in the tail; that is expected. If one asserts the exact tail, update it.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/turns.py engine/tests/test_minds.py
git commit -m "feat(engine): characters carry their mood from turn to turn"
```

---

### Task 11: Mood in Peek and in the Mind graph

**Files:**
- Modify: `engine/src/kataki/people.py` (`people`)
- Modify: `engine/src/kataki/mind.py` (INSIDE, after the feelings loop)
- Test: `engine/tests/test_minds.py`

**Interfaces:**
- Produces: `people()[i]["mood"]` (§8.2 shape or None); Mind graph node `{"id": "mood", "kind": "mood", …}`.

- [ ] **Step 1: Write the failing tests** (append to `test_minds.py`)

```python
async def test_peek_sees_the_feeling_and_the_mask(conn, story, backend):
    backend.say("...")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    mira = next(p for p in people.people(conn, row) if p["name"] == "Mira")
    assert (mira["mood"]["label"], mira["mood"]["shows"]) == ("hurt", "calm")
    tobin = next(p for p in people.people(conn, row) if p["name"] == "Tobin")
    # he heard it too, and appraisal doesn't know yet who a line is about; he expresses, so
    # what he shows is what he feels. slice 2: only the one it is about is insulted
    assert (tobin["mood"]["label"], tobin["mood"]["shows"]) == ("hurt", "hurt")


async def test_the_mind_graph_draws_the_mood_it_replied_with(conn, story, backend):
    from kataki import mind

    backend.say("...")
    await play(turns.turn(conn, backend.llm, story, "Mira, you're useless."))
    graph = mind.mind(conn, chat.active_path(conn, story)[-1]["id"])
    node = next(n for n in graph["nodes"] if n["kind"] == "mood")
    assert node["text"] == "very hurt · showing calm"
```

- [ ] **Step 2: Run to see them fail**

Run: `uv run pytest tests/test_minds.py -q -k "peek or graph"`
Expected: FAIL — `KeyError: 'mood'`.

- [ ] **Step 3: Implement**

`engine/src/kataki/people.py`: import `features, inner` from kataki; add a helper

```python
def _mood(conn: sqlite3.Connection, entity_id: int, path: list, now: int) -> dict | None:
    """How they feel now, faded to the present (Peek; spec §8.2)."""
    prof = inner.profile(conn, entity_id)
    state = inner.current(conn, entity_id, path, prof)
    return state and inner.public(inner.tick(state, now, prof), prof)
```

In `people()`, compute `feeling = features.enabled(conn, "mind.affect")` once before the loop and add to each entry:
`"mood": _mood(conn, e["id"], path, now) if feeling else None,`

`engine/src/kataki/mind.py`: inside `if who is not None:`, right after the `if len(shown) > FEELS:` lines, add:

```python
        if felt := gen.get("mind"):  # the mood the reply was written with (minds spec §8.2)
            text = f"{felt['feels']} · showing {felt['shows']}"
            mood = node("mood", "inside", "mood", "Mood", text, None, True, felt)
            inside.append((mood, True))
```

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/kataki/people.py engine/src/kataki/mind.py engine/tests/test_minds.py
git commit -m "feat(engine): mood in Peek and in the Mind graph"
```

---

### Task 12: The slice-1 probe on a real model

**Files:**
- Create: `engine/evals/probes.py`

**Interfaces:**
- Consumes: the same CLI flags as `evals/live_eval.py` (`--base-url`, `--model`, `--api-key-env`).
- Produces: a printed report for probe `still-upset` (P5-lite in note 22 §8): the mind block per turn, each reply, and three mechanical checks.

- [ ] **Step 1: Write the probe**

```python
"""Probes for the minds slices (docs/specs/2026-09-29-minds.md §9), against a real model.

    uv run python evals/probes.py --base-url http://127.0.0.1:8080/v1 --model qwen3.5-9b

still-upset (slice 1): Aren insults Mira, who masks her feelings; small talk; two hours pass.
Checks: she is hurt after the insult, the mask shows in the block, only a low mood is left two
hours later, and no reply opens with an assistant-style apology. Replies are printed for a human
to judge whether the hurt shows through behaviour without being said. Fresh temporary library.
"""

import argparse
import asyncio
import os
import re
import tempfile
from pathlib import Path

from kataki import db, library, turns
from kataki.llm import LLM

ASSISTANT = re.compile(r"^\W*(i'?m sorry|i apologi[sz]e|as an ai|i understand)", re.IGNORECASE)
SCRIPT = [
    ("Mira, honestly? You're useless at this job.", None),
    ("Anyway. Did the shipment come in?", None),
    ("Mira? You've gone quiet.", None),
    ("Morning. Everything alright?", "two hours later"),
]


async def still_upset(conn, llm) -> list[str]:
    mira = library.create_item(conn, "character", "Mira", description="Mira runs the harbour office.")
    library.update_item(conn, mira, data={"mind": {"regulation": {"style": "suppress", "capacity": 0.5}}})
    aren = library.create_item(conn, "character", "Aren", description="Aren, a trader.")
    story = library.create_story(conn, "Harbour", character_ids=[mira], persona_id=aren)
    failures = []
    for i, (line, skip) in enumerate(SCRIPT):
        events = [e async for e in turns.turn(conn, llm, story, line, skip=skip)]
        reply = "".join(v for k, v in events if k == "token")
        mood = events[-1][1].get("mood") if events[-1][0] == "done" else None
        print(f"\nAren: {line}{f'  ({skip})' if skip else ''}\nmood: {mood}\nMira: {reply}")
        if ASSISTANT.search(reply):
            failures.append(f"turn {i + 1}: assistant-style opener")
        if i == 0 and not (mood and mood["label"] == "hurt" and mood["shows"] == "calm"):
            failures.append("after the insult she should be hurt and showing calm")
        if i == 3 and (not mood or mood["label"] or mood["word"] != "low"):
            failures.append("two hours later only a low mood should be left")
    return failures


async def main(args) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        conn = db.connect(Path(tmp) / "library.db")
        conn.execute("INSERT INTO providers(id, name, base_url) VALUES(1, 'probe', ?)", (args.base_url,))
        conn.execute("INSERT INTO model_roles(role, provider_id, model) VALUES('rp', 1, ?)", (args.model,))
        conn.commit()
        if args.api_key_env:  # roles.get_key reads KATAKI_KEY_<PROVIDER> first
            os.environ["KATAKI_KEY_PROBE"] = os.environ[args.api_key_env]
        llm = LLM()
        try:
            failures = await still_upset(conn, llm)
        finally:
            await llm.aclose()
            conn.close()
    print("\nstill-upset:", "PASS" if not failures else "FAIL\n  " + "\n  ".join(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--api-key-env")
    raise SystemExit(asyncio.run(main(p.parse_args())))
```

- [ ] **Step 2: Lint it**

Run: `uv run ruff check evals/probes.py && uv run ruff format evals/probes.py`
Expected: clean.

- [ ] **Step 3: Run it on the local model** (read `docs/images/rules-and-gotchas.md` first; say the expected time — about 4 replies × ~5 s on Qwen3.5-9B Q4 — then run; check progress at ~30 s)

Run: `uv run python evals/probes.py --base-url http://127.0.0.1:8080/v1 --model <the loaded model>`
Expected: `still-upset: PASS`, and the printed replies read as hurt-but-masked. Record the result (pass/fail, one sample reply) in the spec's Progress.

- [ ] **Step 4: Commit**

```bash
git add engine/evals/probes.py
git commit -m "test(engine): the still-upset probe against a real model"
```

---

### Task 13: Record progress and hand the contract to the UI

**Files:**
- Modify: `docs/specs/2026-09-29-minds.md` (§0 Progress)
- Modify: `docs/specs/2026-09-18-m0-m1-design.md` ("Deliberately NOT building": the three superseded items)

- [ ] **Step 1: Update the M0/M1 YAGNI list**

In `docs/specs/2026-09-18-m0-m1-design.md`, in "Deliberately NOT building (YAGNI)", replace
`mutating stored memories to fake distortion`, `reflection / "dream" cycles` and `higher-order theory of mind` with:
`(superseded 2026-09-29 by docs/specs/2026-09-29-minds.md §1: distortion as append-only recollections, dream cycles as the Between deep pass, one second-order slot)`.

- [ ] **Step 2: Add Progress lines** to `docs/specs/2026-09-29-minds.md` §0, one per landed task group, with commit hashes: foundation F1–F6, slice 1, probe result on the local model.

- [ ] **Step 3: Run the gate**

Run (repo root): `corepack pnpm check`
Expected: engine lint, format, tests and the app typecheck all pass.

- [ ] **Step 4: Commit**

```bash
git add docs/specs/2026-09-29-minds.md docs/specs/2026-09-18-m0-m1-design.md
git commit -m "docs: minds foundation and slice 1 landed"
```

- [ ] **Step 5: Tell the UI agent** (through the owner) that §8.1 and §8.2 of the minds spec are live: `GET /features`, `/health` channel+host, `people[].mood`, `done.mood`, the Mood node, `LIBRARY_TOO_NEW`.

---

## After this plan

Next plans, one per item, each written against the code as it stands when it starts (spec §7):
slice 2 ("grudge and won't cave": `opinions` v11, the side call replacing `_expression`, the
pushback dial, targets for appraisal so only the one a line is about is insulted), then slice 3,
and track B1–B3 in parallel (Host seam, prices and spend, credit gate).
