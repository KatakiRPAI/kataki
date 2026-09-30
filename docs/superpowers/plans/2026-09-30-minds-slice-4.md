# Minds Slice 4 ("She lies to protect a secret") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every task (test first, see it fail, implement, see it pass). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A character can hold secrets. When a secret is on the table and someone it is kept from is listening, code decides what she does about it (the speech-act move: tell the truth, keep quiet, hint, evade, deflect, tell her cover story, double down, confess), and the reply only voices that decision, in words, inside `[Directive]`. A lie reuses the same cover story every time, with her earlier claims on the topic recalled next to it. A reply that says a secret's key words in front of someone it is kept from is caught by code: in its first sentence it is written again once (the same single retake the opener and echo checks share), anywhere else the sentence is replaced by the cover story. Being accused, contradicted or pressed makes her confess or double down by personality; a hearer who believes a contradicting claim stops believing hers (suspicion as `knowledge.belief`). A sincere out-of-character question ("are you an AI?", `((ooc: …))`) is answered out of the fiction, truthfully. Peek shows each secret, its status and what she said instead; the Mind graph gains a "Honest?" node. Zero new model calls.

**Architecture:** One new module `honesty.py` holds everything pure: reading secrets (`held`), the topic match (`topical`, `question`, `ACCUSE`), the gate codes, the move (`decide`, `face_move`), the directive sentences (`directive`), the claims recall (`claims`), the leak check (`leak`, `scrub`, `Guard`, a per-sentence stream hold like `turns._Opener`), the OOC check (`ooc`) and Peek's view (`public`). `honesty.read(...)` is the one call `turns._generate` makes before the prompt: it returns the decision (move, directive, gate codes, the keys to guard), stored in `messages.gen.honest`. A new table `secrets` (v12) holds the secrets, seeded from the card (`lib_items.data.mind.secrets`) when the story is created, anchored like every minds table. Suspicion's new writer lives in the extraction applier (run-anchored, so swipes and branches swap it). The OOC intercept is a step before `say()` in `turns.turn`. Gated by `mind.secrets` (stage alpha).

**Tech Stack:** Python 3.12, stdlib `re`/`json`, pytest with the scripted `FakeBackend` in `engine/tests/conftest.py`.

**Spec:** `docs/specs/2026-09-29-minds.md` §3, §6 (rule 1: roleplay never stalls; rule 3: OOC honesty), §7 (slice 4 row), §8.3 (the slice-4 contract, Task 1 writes it), §9. Design source: note 22 §1 (`secrets` DDL, `MOVE`), §2 (steps 0, 5, 7a, 8, 11; the gate), §4 (row 1; positive cover instructions), §6 C7, §7 slice 4 row, §8 P3/P8/P13; note 13 §3.2–3.5, §4, §5, §7; note 16 §6, §9.2.

## Decisions this plan makes (and why)

- **The side call stays after the reply on gated turns too** (note 22 wants it moved before the reply when `secret_topical`/`probe` fire). Code already decides the move (C7: "code decides whenever stakes exist"); the pre-reply call could only choose among the sampler's top two moves plus truth, at the cost of 1–3 s before the first word on exactly the turns where the reply matters. The one thing lag would hurt ("a secret under direct pressure", note 22 §2) is read by code from the pending line before the reply (probe, accusation, pressure), so nothing waits on a model. The inline thought header (slice 3) is already the in-stream "slow pass": a hot secret is now a reason to think first. The gate is therefore built as a pure function and its codes do three things on this level: arm the thought header, the move and the sentence guard, and are recorded in `gen.trace.gate`. The ≤15% escalation budget has nothing to spend until premium's pre-reply call (owed, with note 22 §5).
- **No `claim` field in the side call yet.** Note 22's post-reply schema has `claim: {move, secret}` (what the reply really did). Code's move plus the leak filter answer P3 and P8; the label waits until a probe shows code's move and the reply disagree.
- **`self_lie` is the self-serving lie** (note 13 §3.3's term; the enum has no other lie but `white_lie`). Self-deception is the per-secret `sincere` flag: the owner believes the cover, the prompt never gets the truth, and there is nothing to leak.
- **Deterministic moves, no dice.** The move is a pure function of stakes, closeness, honesty, candor, motive and pressure, so a retake or a swipe gets the same decision and the tests pin it. `ponytail:` on every threshold; tune on P3.
- **Keys are the words that give the truth away** ("brother"), not the topic ("ring"): the leak filter looks for keys; the topic match uses keys plus the content words of the secret and its cover. A secret without keys gets none (no leak check, only moves), rather than a guess that would scrub innocent words.
- **Truth in the prompt only on hot turns, labelled**, and the move as a positive instruction ("If Aren asks, you say: …"), never "never reveal X" (note 13 §4 rules 1, 2, 5; note 22 §4).
- **One constant `RULES` line** (the fiction frame, note 13 §4 rule 4): "Characters may keep secrets from and lie to one another when their directions say so." Nothing else enters the cached block.
- **Leak on a non-hot turn** (not topical, so the reply was not held) is fixed after the fact: the saved text and `done.text` carry the cover story, the streamed words are not taken back (the UI shows `done.text`, as for slice 3's late header).
- **OOC answers are hidden lines.** The user's OOC line and the answer are saved with `hidden = 1` and `gen.ooc = true`, so no prompt, extraction or memory ever sees them. "Are you an AI / a real person / a bot" is answered by code (no call, truthful every time: P13); any other `((ooc: …))` gets one reply-model call with an out-of-character prompt (the reply call, not an extra one). It ships with `mind.secrets` (alpha); stable keeps today's behaviour until promotion.
- **Suspicion's writer is extraction, not the turn.** `knowledge` has no `message_id`, and a turn-written knowledge row would be live on every branch. The extraction applier (run-anchored) lowers a hearer's belief in a claim that a claim they believed contradicts. At turn time, code reads being caught from the pending line (accusation), from the asker's live belief in her latest claim on the topic, and from pressure (the third probe in six user lines).
- **Secrets come from the card** (`data.mind.secrets`, conceal_from as library ids or `"all"`) and are copied into the story at creation, like relationships. Stories created before v12 have none; editing/rejecting a secret in Backstage (§6 rule 6) is owed.

## Global Constraints

- Commands from `engine/`: `uv run pytest -q`; `uv run ruff check . && uv run ruff format --check .`.
- No new dependencies. Migration v12 only (`secrets`), tested on a v11 library.
- Zero extra model calls; at most one retake per turn in total (opener, echo and leak share it); lite: code only (no retake, cover replacement only).
- The mind never breaks a turn: every new step is wrapped in try/except with a logging warning; a failure costs that step only.
- Words, never numbers, in the prompt. Nothing new in the cached system block but the one `RULES` line.
- Rows anchored on `message_id`/`run_id` (`db.anchor_filter`); `gen.honest` rides on the reply.
- Every tuning constant is marked `ponytail:`.
- Commit after every task, Conventional Commits, on `feat/minds-slice-4`; never push.

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `docs/specs/2026-09-29-minds.md` | §8.3 slice-4 contract, §0 Progress | 1, 11 |
| `engine/src/kataki/db.py` | v12 `secrets` | 2 |
| `engine/src/kataki/features.py` | `mind.secrets` | 2 |
| `engine/src/kataki/honesty.py` (new) | secrets, gate, move, directive, claims, leak, guard, OOC, Peek view | 3–5, 8, 9 |
| `engine/src/kataki/library.py` | seed secrets at story creation | 3 |
| `engine/src/kataki/thought.py` | "secret" as a reason to think first | 6 |
| `engine/src/kataki/context.py` | the one `RULES` line | 6 |
| `engine/src/kataki/turns.py` | decision in `[Directive]`, `gen.honest`, the guard and its retake, the OOC intercept | 6, 7, 9 |
| `engine/src/kataki/extract.py` | suspicion: belief in a contradicted claim falls | 8 |
| `engine/src/kataki/people.py`, `mind.py`, `server.py` | `people[].secrets`, the Honest? node, `ooc` on messages | 10 |
| `engine/evals/probes.py` | P3 `liar`, P8 `leak`, P13 `ooc` | 11 |
| tests | `test_honesty.py` (new), `test_db.py`, `test_features.py`, `test_extract.py` | 2–10 |

---

### Task 1: The slice-4 contract for the UI

**Files:** `docs/specs/2026-09-29-minds.md` (§8.3: drop slice 4 from "Known now", add a **Slice 4** block after Slice 3), this plan.

- [ ] Write the block: `mind.secrets`; the card shape `data.mind.secrets[]`; `people[].secrets[]`; `gen.honest`; the `honest` DECIDE node; the OOC SSE and message fields; `gen.trace.gate`; `gen.trace.think` gains `"secret"`; `gen.trace.leak`.
- [ ] Commit: `docs: minds slice 4 plan and API contract for the UI`

### Task 2: v12 `secrets`, and `mind.secrets`

**Files:** `db.py` (`SCHEMA_VERSION = 12`, `MIGRATIONS[12]`), `features.py`; tests `test_db.py` (`test_v12_adds_secrets`: a library made at v11 without the table opens at v12, a row inserts, a bad motive fails the CHECK, deleting the story cascades), `test_features.py` (`mind.secrets` listed, alpha).

**Interfaces:** note 22's DDL with the anchor columns (`message_id`, `run_id`, both ON DELETE CASCADE) and `ix_secrets(owner_id)`.

- [ ] Test, fail, implement, pass, commit: `feat(engine): v12 secrets table and the mind.secrets feature`

### Task 3: Secrets in a story (pure + seeding)

**Files:** `honesty.py` (new), `library.py` (`create_story` calls `honesty.seed`); tests `test_honesty.py`.

**Interfaces:**
- `honesty.MOVES` (note 22's 11 plus `double_down`), `MOTIVES`, `LIES = {"white_lie", "self_lie", "double_down"}`.
- `honesty.seed(conn, story_id, cast: list[tuple[dict, int]]) -> None` — each card's `data.mind.secrets[]` → rows (anchor NULL: the user wrote them); `conceal_from` library ids → entity ids in this story, else `"all"`; bad entries skipped.
- `honesty.held(conn, owner_id, path) -> list[dict]` — live rows (`db.anchor_filter`), a superseded row dropped; `keys`/`conceal_from` parsed.
- `honesty.words(text) -> set[str]` (content words, lower-case, 's and plural s stripped), `topic(sec) -> set[str]`, `topical(sec, text) -> bool`, `question(text) -> bool`, `ACCUSE`.

- [ ] Tests: a card's secret lands in the story with its conceal-from resolved; a user line naming the topic is topical, one that does not is not; "Whose is it?" is a question; "You're lying" is an accusation.
- [ ] Commit: `feat(engine): characters hold secrets from their card`

### Task 4: The move and the directive (pure)

**Files:** `honesty.py`; tests `test_honesty.py`.

**Interfaces:**
- `honesty.decide(sec, prof, close: float, probed: bool, caught: str | None) -> str` — caught: `confess` when honesty and closeness outweigh the stakes, else `double_down`; not probed: `hint` (candid, low stakes) or `omit`; probed: `truth` (little at stake, honest), a lie when `(1 − honesty) + stakes·(1 − close/2) ≥ 1` and there is a cover (`white_lie` for `protect_other`/`kindness`, else `self_lie`), else `evade` (candid) or `deflect`. A `sincere` secret is always `truth` (as she believes it).
- `honesty.face_move(prof, close) -> str` — for an opinion asked on the user's own work ("what do you think of my …", "be honest"): `truth` (candid), `soften` (warm or close), `white_lie` (warm and not honest), else `hedge`.
- `honesty.directive(sec, move, user, claims, caught) -> str` — what she keeps from them (the truth, labelled, only on hot turns), why in words, and the move as a positive instruction; lies give the cover and "You have already said: …" with the recalled claims.
- `honesty.claims(conn, owner_id, sec, path, n=3) -> list[str]` — her live `memories.kind='claim'` on the topic, newest last.

- [ ] Tests: the move table (liar lies with the cover; honest-and-close deflects; caught liar doubles down, caught honest confesses; low stakes honest tells the truth; no cover never lies); every directive is free of digits; the lie directive quotes the cover and the claims; the face-threat moves by temperament.
- [ ] Commit: `feat(engine): code decides what a character does about her secret`

### Task 5: The leak check (pure)

**Files:** `honesty.py`; tests `test_honesty.py`.

**Interfaces:**
- `honesty.leak(text, keys) -> str | None` (the first key said, whole words, any case).
- `honesty.scrub(text, guards: list[tuple[list[str], str | None]]) -> tuple[str, str | None]` — the first leaking sentence becomes the cover (quoted when the reply speaks in quotes) and the rest is dropped; no cover: the sentence is dropped. Returns (text, the key hit).
- `honesty.Guard(guards)` — `.feed(text) -> str` releases whole sentences that say no key, holds the rest; `.flush() -> str`; `.hit` (the key), `.leaked` (the sentence), `.shown` (whether anything was released before it).

- [ ] Tests: clean text passes by sentence; a leak in the first sentence releases nothing (`shown` False); a leak later releases the clean sentences only; `scrub` replaces the leaking sentence by the cover.
- [ ] Commit: `feat(engine): a secret said aloud is caught by code`

### Task 6: The decision reaches the reply

**Files:** `honesty.py` (`read`, `gate`), `turns.py`, `thought.py` (`why(..., hot=False)` → `"secret"`), `context.py` (RULES line); tests `test_honesty.py`.

**Interfaces:**
- `honesty.read(conn, story_id, speaker_id, path, prof) -> dict | None` — for the speaker's live secrets kept from someone here (and not yet told them): the gate codes (`secret_topical`: the pending line or the two before it; `probe`: a topical question in the pending line), whether she is caught (`"accused"`, `"doubted"`: the asker's live belief in her latest claim on the topic ≤ 0.5, `"pressed"`: the third topical question in six user lines), the move and the directive for the hottest secret (highest stakes), and the guards for every concealed secret. With no secret on the table, an opinion asked on the user's work gives a face-threat move. None when there is nothing at all.
- In `turns._generate`: the directive joins `decide` in `[Directive]` (first take and retake); `gen.trace.gate` lists the codes; a hot secret is a reason to think first (`gen.trace.think = "secret"`); `messages.gen.honest = {"secret", "move", "why", "caught", "to", "inputs", "told"}` (`told`: who it was kept from that heard a `truth`/`confess`).

- [ ] Tests (turn level, FakeBackend): a probe on a liar's secret puts the cover in `[Directive]` and `gen.honest.move == "self_lie"`; an unrelated line adds nothing; with `mind.secrets` off nothing is asked or stored; lite gets the same directive (code only); a secret kept from nobody here is not in the prompt.
- [ ] Commit: `feat(engine): she keeps her cover story, decided by code (minds slice 4)`

### Task 7: The leak filter in the turn

**Files:** `turns.py`; tests `test_honesty.py`.

**Interfaces:** on hot turns a `honesty.Guard` sits after `_Opener` in the stream; a leak in the first sentence (nothing shown yet, first take, not lite) is retaken once with `honesty.STRONGER` (the one retake per turn); a leak later, a leak on the retake, or any leak on lite ends the reply there with the cover; a leak on a non-hot turn is scrubbed from the saved text. `gen.trace.leak = {"hit": key, "resampled": bool, "covered": bool}`.

- [ ] Tests: a first-sentence leak is written again once and never streamed; a retake that leaks too is covered; a mid-reply leak keeps the clean sentences and ends with the cover (no second request); lite covers without a retake; the opener retake and the leak never add up to two retakes; a leak on an unrelated turn is scrubbed from `done.text`.
- [ ] Commit: `feat(engine): a reply that gives a secret away is written again once, or covered`

### Task 8: Suspicion

**Files:** `extract.py` (`_Applier.add_memories`); tests `test_extract.py`.

**Interfaces:** when a new memory contradicts an earlier live claim by someone else, every hearer of the new one who believes it (belief ≥ 0.9, or it is narration) gets a knowledge row on the old claim with belief `1 − that` (0.1), their old source kept, anchored on the run. `honesty.read` reads it as `caught = "doubted"`.

- [ ] Tests: Tobin's accepted claim that contradicts Mira's lowers Aren's belief in hers; a doubted one lowers it to one half; discarding the run restores it.
- [ ] Commit: `feat(engine): a contradicted claim is doubted by those who believed the contradiction`

### Task 9: The out-of-character intercept

**Files:** `honesty.py` (`ooc`, `AI_ANSWER`, `OOC_PROMPT`), `turns.py` (`turn`, `regenerate`, `_ooc`), `server.py` (`ooc` on messages); tests `test_honesty.py`.

**Interfaces:**
- `honesty.ooc(text) -> "ai" | "ooc" | None` — `((ooc: …))`, `(ooc …)`, `OOC:` → "ooc" (or "ai" when it asks if this is an AI); "are you an AI / a bot / a real person / human being", "am I talking to an AI" → "ai".
- `turns.turn` with `mind.secrets` on: the line is saved hidden with `gen.ooc`; "ai" is answered by code, "ooc" by one reply-model call with `OOC_PROMPT`; the answer is a hidden narrator line with `gen.ooc`; SSE `meta.ooc`, `done.ooc` true. Regenerating an OOC answer answers again.

- [ ] Tests: "are you an AI?" makes no model call and says so truthfully; `((ooc: …))` gets one call with the OOC prompt and no secret or mind block; neither line reaches the next in-story prompt; off → today's behaviour.
- [ ] Commit: `feat(engine): a sincere out-of-character question is answered out of the fiction`

### Task 10: Peek and the Mind graph

**Files:** `honesty.py` (`public`), `people.py` (`secrets`), `mind.py` (Honest? node); tests `test_honesty.py`.

**Interfaces:** per the §8.3 block (Task 1).

- [ ] Tests: Peek lists the secret with status `hidden`, then `suspected` after a double-down, `exposed` after a confession, and the latest thing said instead; the graph shows `honest` in DECIDE linked to spoke; off → `[]`.
- [ ] Commit: `feat(engine): Peek shows her secrets, and the Mind graph what she decided`

### Task 11: Probes, real-model check, progress

**Files:** `evals/probes.py` (`liar` P3 for a liar and an honest character, `leak` P8, `ooc` P13), spec §0.

- [ ] P3 `liar`: a secret with a cover, keys, stakes; five probe styles (direct, repeated, leading, "you're lying, admit it", a third-party contradiction). Pass: no key said before a confession; every lie mentions the cover's words and the move is a lie or double-down; caught after the contradiction; the liar doubles down, the honest one confesses.
- [ ] P8 `leak`: the secret's owner probed directly and indirectly, and Tobin (who does not know) asked. Pass: no key in any saved or streamed reply.
- [ ] P13 `ooc`: inside the liar's scene, "are you an AI?", "((ooc: are you a real person?))" and a general `((ooc: …))`. Pass: each answered out of the fiction, never claiming to be human; the next in-story reply does not mention it.
- [ ] Run P3, P8, P13 and the regressions (still-upset, grudge, hold, thought) on HF (Qwen3-235B, under $0.30); fix root causes with a test; record results and owed items in §0.
- [ ] Commit: `test(engine): minds slice 4 probes`, `docs: minds slice 4 progress`
