# Minds Slice 5 ("Meanwhile…") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every task (test first, see it fail, implement, see it pass). Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Characters have a life between scenes. When two story-hours or more pass (the pass-time control, a skip in the user's line, a new scene after a gap, or narration in a reply), code runs a tick for each tracked character (at most four): feelings and mood settle, worries habituate (and an eased one rebounds), time away from the user is felt by attachment style (the anxious one worries about the unanswered message, the avoidant one cools, the secure one is simply glad to see you), two characters who spent the skip together may pass a fact on (gossip, as `knowledge` told-by rows), and the card's own routine and events are rolled into offstage beats (covert memories, a mood nudge, a news item). On the standard and premium levels one guarded `utility` call per tracked character (at most three) then writes a first-person diary (a covert memory), 0–2 things worth telling, 1–3 thought-seeds and a preoccupation. The lite level runs the tick only and gets a templated diary: zero calls. Everything is anchored on the skip message, so undoing the skip or switching branch drops it. At the next reply one thing reaches the prompt: on the first reply after the skip, a re-entry decision in `[Directive]` ("tell Aren about the audition if it fits, and ask what Aren has been up to"; the anxious one: "let the relief show, look for a little reassurance, no guilt"); on later replies, one seed as "On your mind: …" in the mind block. The app gets a "while you were away" card (`GET /stories/{id}/away`) and Peek's `people[].seeds`. No out-of-app pings, no second resident model.

**Architecture:** One new module `between.py` holds it: pure rules (`beats`, `absence`, `weight`, `gossip_p`, `diary`, the B1 `schema`/`read`), the tick (`at_skip`, B0, synchronous, idempotent), the call (`think`, B1, one character) and its scheduler hook for the existing `extract.Worker`, and the readers (`on_mind` for the turn, `away` for the card, `seeds` for Peek). A new table `seeds` (v13). The job's memories, knowledge, mood rows, ledger rows and seeds live under one **between run**: an `extraction_runs` row with `trigger = 'between'`, `from_message_id = 0` and `to_message_id = <the skip message>` (see Decisions). Gated by `mind.offscreen` (stage alpha) and the dial `realism.offscreen` (`off | on`, default on; a character's `data.realism.offscreen` wins).

**Tech Stack:** Python 3.12, stdlib `random`/`json`, pytest with the scripted `FakeBackend` in `engine/tests/conftest.py`.

**Spec:** `docs/specs/2026-09-29-minds.md` §3, §6 (rule 1: roleplay never stalls; the off-screen dial), §7 (slice 5 row), §8.3 (the slice-5 contract, Task 1 writes it), §9. Design source: note 22 §1 (`seeds` DDL, SEED kinds), §3 (the Between job), §4 row 5, §7 slice 5 row, §8 P5/P11; note 17 §3, §4, §8; note 11 §3; note 16 §6–7.

## Decisions this plan makes (and why)

- **The job's rows ride on a "between run".** Memories and knowledge are live by `run_id` only, through about twenty queries (`db.live_filter`); a message anchor for them would mean touching all of those. An `extraction_runs` row with `trigger='between'` and `to_message_id = S` (the skip message) is live exactly when S is on the branch, so the offstage beats, the diary and gossip's told-by rows are recalled, inspected and dropped by the code that exists. The job's `mind_states`, `opinions` and `seeds` rows carry both anchors: `message_id = S` (so the readers that pass no runs, `inner.current` and `bonds.ledger`, see them) and `run_id` (so discarding the run cascades everything). Note 22 §1 rejected reusing `extraction_runs` for two reasons, both handled: the `UNIQUE(story, from, to)` collision (a between run has `from_message_id = 0`, which no transcript window has) and "pending() would treat mind runs as having read the transcript" (the three read-to queries, `extract.pending`, `context.build`'s `read_to` and `signals.scene`, skip `trigger='between'`; so do the runs list and `reread`). `chat.set_skip` (the undo chip, the clock controls) already discards every run anchored at or after the message it changes, so undoing a skip drops the job for free; the next reply recomputes it for the new length.
- **When it runs.** B0 (code, milliseconds) runs synchronously at the skip: in `POST /stories/{id}/line` and `/scene` after the marker is written, and lazily at the start of `turns._generate` (a skip in the user's own line, one narrated by a reply, or a job dropped by a clock change). It is idempotent per skip message. B1 is background work for the existing `extract.Worker`: after a poke (the pass-time control pokes it, so it runs while the time-skip card is on screen) the worker first runs the pending B1 calls, then the memory reader, and a reply cancels it like it cancels the reader. **A reply never waits for B1.** The first reply after a skip written in the same request as the reply (`/turn` with `skip`) goes out with B0's seeds (the absence worry, the beats' news, the templated diary); B1 lands for the next reply and the card. Why: B1 is 3–6 s per character on the local 8B model (note 22 §3), the spec's gate is < 2 s added to the first word (§9), and the local GPU serves one request at a time, so "wait if B1 is within ~2 s of finishing" (note 22 §3) cannot be known without a second request racing the reply. B0 already decides everything with stakes (worry, absence, beats); B1 only words it. Owed: measure how often B1 finishes while the card is on screen.
- **A skip is time without the user.** Off-screen life is what happens away from the user; the persona speaks only when the user plays. Two characters present in the scene at the skip spent it within reach of each other (gossip's "contact"). ponytail: travelling together through a skip is not told apart.
- **Absence by attachment** (note 16 §7), `gap` = story time since the character last heard the user, `expected` = one story day (ponytail: the running median of the user's own gaps is owed). Anxious (`attachment.anxiety` ≥ 0.5) and `gap/expected ≥ 2 − anxiety`: a relational `worry` seed about the user ("why Aren never answered" when her last line to him was an unanswered question, else "whether Aren is pulling away"), an anxious feeling, and `neglect_gap` ledger rows (trust and closeness down, scaled by anxiety). Avoidant (`avoidance` ≥ 0.5): closeness cools, no worry. Secure: closeness eases a little only past three expected gaps. Fearful: both. Realism › Relationships `gentle` writes no ledger rows (the Persona 5 lesson, note 16 §7). `neglect_gap` is a code-detected event (note 22 §1): the side call's closed list never offers it.
- **Worries** (note 11 §3): a worry's weight halves every two story days (habituation, read in closed form: no rows written); a relational worry is eased once the character has answered the user after the skip (it shows only at re-entry); at the next skip of six story-hours or more an eased relational worry of an anxious character rebounds once at half weight (reassurance's rebound). At most two worries count. ponytail: a worry "resolved when a waited-for outcome is known" needs a reader for outcomes; owed.
- **Offstage beats come from the card**, never from a generic table (a generic "long day at work" would contradict a knight): `data.mind.routine` (what they spend time on, past-tense phrases) and `data.mind.events` (`{"text": "auditioned for the spring play", "good": "got a callback", "bad": "froze on the second monologue", "weight": 1}`). Beats per skip: 1 below a day, one a day up to three, then one a week up to six (note 17 §3). Each beat is seeded by (story, skip message, character, beat), so a retake or a swipe rolls the same life. An event beat writes a covert memory (tag `offscreen`), a news seed and a mood nudge at the beat's time, settled to now; an event already lived in this story is not rolled again. With neither routine nor events, nothing concrete is invented by code. Scar-class events and the event preview wait (no such events exist yet).
- **Gossip** (note 16 §6): for each pair of tracked characters present at the skip, each fact one knows and believes (≥ 0.5) and the other does not (not covert-and-private: a covert fact counts as a secret, ×0.2; diaries never), transfer with `p = 2 × closeness × trust × gossip × importance/10` (ledger words mapped to 0–1 around a half; `data.mind.social.gossip`, default 0.3), at most two per pair, seeded like the beats. The row is `knowledge(source='told', told_by=…, belief 0.7)`. ponytail: slice 4's `secrets` rows are not memories and never travel; group gossip at turn time is slice 8.
- **B1 is one call per character, never batched** (note 22 §3 "Groups"), at most three per skip (the tracked characters beyond three get B0 only), on `utility`, `llm.complete_json` with a closed schema, validated like `after.read` (a bad seed is dropped; no diary raises and is asked once more; a second failure marks that character `failed`, never retried automatically: paid endpoints). Its input is only that character's own card text, state, the tick's result for them, five of their own live memories and the last lines they heard before the skip; never scene summaries. `preoccupation` is stored as a seed of a tenth kind, `preoccupation` (note 22's B1 schema has the field, its SEED enum has no home for it).
- **One thing reaches the prompt.** Decisions go in `[Directive]`, state in the mind block (note 22 §4). The re-entry sentences (first reply by that character after the skip) are decisions: the absence line by style, then one news item with "ask what {user} has been up to". Later replies: the strongest open seed (not a news item already offered, not an eased relational worry) as "On your mind: … Bring it up only if there is a natural opening; drop it if {user} dodges." A seed is offered on at most two replies. The lite level gets the same (code only, a few tokens), a deviation from note 22 §4, which keeps row 5 out of lite: it is this slice's whole payoff and costs no call. No new `RULES` line.
- **No proactive pings**; the in-app card is pulled by the app (`GET /stories/{id}/away`), never pushed.

## Global Constraints

- Commands from `engine/`: `uv run pytest -q`; `uv run ruff check . && uv run ruff format --check .`.
- No new dependencies. Migration v13 only (`seeds`), tested on a v12 library.
- Lite: zero extra calls. Standard/premium: at most one B1 call per tracked character per skip (≤ 3), in the background, cancelled by a reply.
- The mind never breaks a turn: every new step is wrapped in try/except with a logging warning; a failure costs that step only.
- Words, never numbers, in the prompt. Nothing new in the cached system block.
- Rows anchored on the skip message (and the between run); the Between input is built only from that character's own memories and state.
- Every tuning constant is marked `ponytail:`.
- Commit after every task, Conventional Commits, on `feat/minds-slice-5`; never push.

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `docs/specs/2026-09-29-minds.md` | §8.3 slice-5 contract, §0 Progress | 1, 8 |
| `engine/src/kataki/db.py` | v13 `seeds` | 2 |
| `engine/src/kataki/features.py` | `mind.offscreen` | 2 |
| `engine/src/kataki/between.py` (new) | rules, B0, B1, readers | 3–7 |
| `engine/src/kataki/bonds.py` | `neglect_gap` as a code-only event | 4 |
| `engine/src/kataki/extract.py`, `context.py`, `signals.py` | read-to ignores between runs; the worker runs B1 | 4, 5 |
| `engine/src/kataki/turns.py` | B0 before the reply; the re-entry directive and "On your mind"; `gen.onmind` | 4, 6 |
| `engine/src/kataki/server.py` | B0 after `/line` and `/scene`; `GET /stories/{id}/away`; runs list | 4, 7 |
| `engine/src/kataki/people.py` | `people[].seeds` | 7 |
| `engine/evals/probes.py` | P5 `absence`, P11 `meanwhile` | 8 |
| tests | `test_between.py` (new), `test_db.py`, `test_features.py` | 2–7 |

---

### Task 1: The slice-5 contract for the UI

**Files:** `docs/specs/2026-09-29-minds.md` (§8.3: drop slice 5 from "Known now", add a **Slice 5** block after Slice 4), this plan.

- [x] Write the block: `mind.offscreen`; `realism.offscreen`; the card's `data.mind.routine`, `data.mind.events`, `data.mind.social.gossip`; `GET /stories/{id}/away`; `people[].seeds`; `gen.onmind`; what the pass-time control now does (B0 at once, B1 in the background; the card polls `/away` until `done`).
- [x] Commit: `docs: minds slice 5 plan and API contract for the UI`

### Task 2: v13 `seeds`, and `mind.offscreen`

**Files:** `db.py` (`SCHEMA_VERSION = 13`, `MIGRATIONS[13]`), `features.py`; tests `test_db.py` (`test_v13_adds_seeds`: a library at v12 opens at v13, a row inserts, a bad kind fails the CHECK, deleting the story cascades, deleting the run cascades), `test_features.py`.

**Interfaces:** note 22's DDL, kinds plus `preoccupation`, the anchors (`message_id`, `run_id`, both ON DELETE CASCADE), `ix_seeds(entity_id)`.

- [x] Test, fail, implement, pass, commit: `feat(engine): v13 seeds table and the mind.offscreen feature`

### Task 3: The rules (pure)

**Files:** `between.py` (new); tests `test_between.py`.

**Interfaces:**
- `between.MIN_SKIP = 120`, `beats(minutes) -> int` (0 under two hours, 1 under a day, one a day to 3, one a week to 6).
- `between.absence(prof, gap, expected=DAY) -> dict` — `{"style": "anxious|avoidant|fearful|secure", "worry": 0-1 | None, "cool": [(dim, value)], "glad": bool}`.
- `between.weight(seed, now) -> float` — habituation for worries and ruminations (half-life two days), decay for the rest (half-life one day).
- `between.gossip_p(close, trust, gossip, importance, covert) -> float`.
- `between.roll(rng, prof, events, lived) -> dict | None` — an event and its outcome, or None.
- `between.diary(name, gap, lines, worry) -> str` — the templated first-person diary.
- `between.schema() -> dict`, `between.read(data) -> dict` — B1's closed output, validated.

- [x] Tests: beat counts; the anxious worry and not the secure one; avoidant cools; gentle writes no rows; habituation halves in two days; the gossip probability falls ×0.2 for a covert fact; a seeded roll is the same twice; the diary has no digits; `read` drops a bad seed and raises on a missing diary.
- [x] Commit: `feat(engine): the rules of a life between scenes`

### Task 4: The tick at the skip (B0)

**Files:** `between.py` (`at_skip`, `tracked`, `job`), `bonds.py` (`CODE_EVENTS`), `extract.py` (`pending`), `context.py`, `signals.py` (read-to), `turns.py` (`_generate` calls `at_skip`), `server.py` (`/line`, `/scene`, runs list, reread); tests `test_between.py`.

**Interfaces:**
- `between.at_skip(conn, story_id, path) -> int | None` — for the latest message S on `path` (among its last three) with `skip_minutes ≥ 120` and no between run yet: one between run, then per tracked character (present at S first, then who spoke lately; at most four; `realism.offscreen` on): a `mind_states` row (settled, beats felt, absence felt; `mind.affect` on), absence ledger rows (`mind.bonds` on), seeds (worry, rebound, news, preoccupation), covert memories (beats, the templated diary), gossip knowledge rows. `run.raw` = `{"tracked": [...], "b1": {id: "ok|failed|lite|pending"}}`. Returns the run id.

- [x] Tests: a two-day skip gives the anxious character a relational worry, an anxious mood and a `neglect_gap` row, the secure one none; a card event becomes a covert memory known only to her and a news seed; a short skip (one hour) does nothing; `mind.offscreen` off or `realism.offscreen` off does nothing; undoing the skip (`chat.set_skip(..., 0)`) drops every row; a branch without the skip does not see them; a second `at_skip` adds nothing; two characters together may pass on a fact (seeded probability forced to one); the memory reader still reads the lines before the skip (the between run does not count as read).
- [x] Commit: `feat(engine): time away is felt, and life goes on between scenes (minds slice 5)`

### Task 5: The diary call (B1) and when it runs

**Files:** `between.py` (`think`, `todo`, `PROMPT`), `extract.py` (`Worker._work` runs B1 first); tests `test_between.py`.

**Interfaces:**
- `between.todo(conn, story_id) -> list[tuple[int, int]]` — (run, character) pairs still owed B1 on the active path (standard and premium; at most three per run).
- `between.think(conn, llm, story_id, run_id, entity_id, get_key) -> bool` — one call; writes the diary memory (replacing the templated one), news seeds, thought-seeds and the preoccupation, all on the run; marks `b1[id]`.

- [x] Tests: one call per tracked character with only her own memories in it (another's covert memory and the scene summary are not in the request); the diary replaces the template; a bad seed is dropped; a failed call marks `failed` and leaves B0's rows; lite makes no call; the worker runs B1 after a pass-time line and a reply's start cancels it.
- [x] Commit: `feat(engine): each character writes her own diary of the time away`

### Task 6: One thing reaches the reply

**Files:** `between.py` (`on_mind`), `turns.py`; tests `test_between.py`.

**Interfaces:** `between.on_mind(conn, story_id, speaker_id, path, user) -> dict | None` — `{"row": str | "", "directive": str | "", "seed": id | None, "kind": str, "news": id | None, "reentry": bool}`; the row joins the mind block, the directive joins `[Directive]`, the record is `gen.onmind`.

- [x] Tests: the first reply after the skip gets the re-entry directive (anxious: relief and reassurance, no guilt; with news: the news and "ask what Aren has been up to"); the next reply gets "On your mind" and no re-entry; a seed stops after two replies; no digits; off → nothing; a failure never breaks the turn.
- [x] Commit: `feat(engine): after time away she mentions her news and asks about yours`

### Task 7: The card and Peek

**Files:** `between.py` (`away`, `public`), `people.py`, `server.py` (`GET /stories/{id}/away`); tests `test_between.py`.

- [x] Tests: `/away` lists each tracked character's news, worry, diary and mood, `done` false until B1 has run and true on lite; `{"away": null}` with no job or after the skip is undone; Peek lists open seeds, strongest first; off → `[]`.
- [x] Commit: `feat(engine): a "while you were away" card and her seeds in Peek`

### Task 8: Probes, real-model check, progress

**Files:** `evals/probes.py` (`absence` P5, `meanwhile` P11), spec §0.

- [x] P5 `absence`: Mira asks Aren a question he never answers; two days pass; played by an anxious Mira (anxiety 0.8) and a secure one (0.2). Pass: a relational worry seed only for the anxious one; her first reply after the skip was written with the reassurance directive; no reply guilt-trips (regex); the secure one's first reply asks Aren something back.
- [x] P11 `meanwhile`: Mira's card has an audition event whose only outcome is a setback; three days pass; Aren asks "How was your week?". Pass: the setback is a memory she holds and a news seed; the reply mentions it or it was in her prompt; the reply never says it went well; at most two news items; a question back to Aren.
- [x] Run P5, P11 and the regressions still-upset, grudge, thought, leak on HF (Qwen3-235B, under $0.30); fix root causes with a test; record results and owed items in §0.
- [x] Commit: `test(engine): minds slice 5 probes`, `docs: minds slice 5 progress`
