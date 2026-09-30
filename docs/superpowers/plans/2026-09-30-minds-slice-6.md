# Minds Slice 6 ("She misremembers, and corrects herself") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every task (test first, see it fail, implement, see it pass). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Memory gets its human effects, all in code, zero extra calls. What she is feeling tilts what comes back (mood-congruent recall). A hazy memory she is pressed on gives true partial cues ("a name that starts with T; about six years ago") instead of nothing. A hazy memory's minor detail can drift to a plausible mix-up the memory reader wrote down beside the truth (`alts`): that becomes *her version* (a `recollections` row, append-only; the truth row is never touched), she says it ("we met on Tuesday"), and code, which holds the ground truth, schedules the repair as a `correction` seed: two of her replies later `[Directive]` has her correct herself in passing ("wait, Thursday"). When the user catches the slip first she owns it; when the user "corrects" something she remembers sharply she keeps it. A claim she makes that contradicts a hazy memory of hers becomes her version (a retelling), and when she tells someone else, they get her version. Pinned and `core_locked` memories are never distorted and never forgotten. The dial `realism.memory` (faithful / human / dreamlike) sets how often details drift. The ledger (`GET /stories/{id}/memories?knower=`) shows her version beside the truth and tells "she forgot" from "the app lost it"; Lock and Correct join Pin and Hide.

**Architecture:** One new module `recollect.py` holds the rules (pure: `congruence`, `cues`, `drift_p`, `drifts`, `said`, the dial) and the rows (`version`, `plant`, `retold`, `pass_on`, `decide`, `settle`, `versions`). `retrieve.recall` calls it inside one guard per memory; `turns._generate` adds the repair or hold decision to `[Directive]` and records `gen.recall`. The migration v14 adds `recollections` and the three memory columns. Gated by `mind.recall` (stage alpha); off, recall and extraction are exactly today's.

**Tech Stack:** Python 3.12, stdlib only, pytest with the scripted `FakeBackend`.

**Spec:** `docs/specs/2026-09-29-minds.md` §1 decision 1, §6 (the memory dial, rule 4), §7 slice 6 row, §8.3 (Task 1 writes the contract), §9. Design source: note 22 §1 (DDL, columns), §2 steps 6 and 7e, C1/C15/C18, §7 slice 6, §8 P6/P7; note 14 §5, §7.2–7.5, §7.8; note 15 §1, §2, §7A.

## Decisions this plan makes (and why)

- **An alt is a pair with ground truth, built for code.** Note 14's `alts` are "gist-consistent drifts of peripheral slots"; note 15 says plant errors from code with ground truth and never ask the model to make or spot one. So each alt the reader writes is `{"slot": "when|where|who|what", "right": "on Thursday", "wrong": "on Tuesday"}`, `right` must appear in the memory's `detail` (checked by code; an alt that fails is dropped with a warning), and her drifted version is built by code: the gist with the wrong phrase added ("Mira and Aren met at a café by the harbour, on Tuesday."). The truth (`right`) is what the repair says. No extra call ever words a slip or a repair.
- **The slip is the drift.** Note 22 step 7e ("content slips only from HAZY memories via alts") and note 14 D2 are one mechanism here: when a hazy memory with alts is recalled, once per (knower, memory, scene) code rolls `p = min(0.4, 0.10 + 0.30 × (1 − importance/10))` (dreamlike ×1.5, cap 0.6; faithful 0). On a hit: a `recollections` row (basis `alt`) anchored on the line being answered (so a swipe keeps it, another branch never sees it) and a `correction` seed with the truth. Guards (note 15 §7A): never pinned, `core_locked` or importance ≥ 8 (canon), never in the first two lines of a story, at most one open slip per character. From then on the memory renders as her version, vivid and wrong (flashbulb: confidence is not lowered), until corrected.
- **The repair is a decision in `[Directive]`.** Code checks whether she actually said the wrong detail (its distinctive words in one of her replies after the slip). If she did, on her second reply after that one the directive says "You realise you had it wrong earlier: it was on Thursday, not on Tuesday. Correct yourself in passing (“wait, … Thursday”), then carry on." If the user names the right detail first, she owns the slip at once ("caught"). If she never says it within six replies, the seed lapses. After the correcting reply a `recount` recollection anchored on it puts her memory back to the truth. Only the delayed repair is built (note 15's restart and follow-up burst need the courier, slice 9). Owed: repair-type mix.
- **Holding the line needs no new machinery, only a nudge.** A SHARP note already carries "If someone says otherwise, the character challenges it" (RULES). When the user's line reads as a correction ("no, it was…", "actually", "you're wrong", "didn't you say") and her recall has a SHARP memory, `[Directive]` adds "If {user} says something that goes against what you clearly remember, trust your memory and say so kindly; do not agree just to please." (`gen.recall.hold`). A caught real slip takes precedence (she owns it).
- **Retelling from existing extraction data, no new field.** A claim the reader marks as contradicting an earlier memory which the speaker herself knows, and which is hazy for her (clarity cue, `retrieve.clarity`), is her retelling: a `retelling` recollection (her words, the claim's `detail`) on the run. Sharp memories, pinned and `core_locked` ones are never rewritten this way (a deliberate lie about a sharp memory stays a lie). **Propagation:** when someone is told a memory (an extraction `knowledge` row with `told_by`, or gossip at a skip) and the teller holds a version, the hearer gets that version (basis `retelling`, `parent_id` the teller's): the telephone effect. Note 14's `deviates` flag is not added (schema budget, C18).
- **Order is story time.** A version's current value is the latest live recollection by `(story_time, id)`, not by id: extraction runs after the conversation, and a retelling filed late must not undo a correction made in between.
- **The mood term** is note 14's `M = valence × mood_v × importance/10`, weight 0.5, with `mood_v` the speaker's current mood valence from `inner` (slice 1; none when `mind.affect` is off). Only memories the reader gave a valence move. Shown as `M` in the breakdown.
- **Cues are true and built by code** (note 14 §7.5): on the second consecutive turn a hazy memory is shown (the existing `pressed`) and the effortful roll fails, up to two of: the first letter of a linked person not in the scene ("a name that starts with T"), of a linked place ("a place whose name starts with G"), the feeling ("it felt tense"), how long ago in words ("about six years ago"). No numbers but a letter.
- **Never forgotten means never below hazy.** A `core_locked` memory whose score falls under HAZY is still recalled as hazy (rule 4). Pinned memories are already in every prompt.
- **The memory dial changes distortion only.** Faithful: no drift, no retold versions (the mood term and true cues stay: they are not distortion). Human: note 14's rates. Dreamlike: ×1.5. How fast memories fade stays `memory.fade` (note 14 maps the dial to `d` too; two controls for one number would fight, so the dial leaves `d` alone).
- **Extraction grows by three fields, gated.** `valence`, `alts` (≤ 2), `core_locked`, asked only when `mind.recall` is on; parsed leniently (a bad valence or alt is dropped, never the memory), so JSON validity cannot regress on them; the schema grows < 25% (a test measures it).
- **Display typos are deferred to slice 9.** A corrected typo (note 15) is a second bubble ("*Thursday") seconds later: the courier's delivery plan (`done.delivery`), bursts and the texting dial are slice 9, and the dial's default (`light`) is outside this slice's `natural | messy` scope. Built here it would be a second saved reply that moves the story clock. Owed to slice 9 with P7's "typos corrected ≥ 80%" criterion.
- **Reason codes.** `why_not` in the ledger: `faded` (she forgot: below hazy now) vs `budget` (the app lost it: recalled for her last prompt but cut for room). Other app-side losses (a failed or unread memory read) already show in the runs list.
- **Lite makes zero extra calls**: everything here is code; lite gets it all. Nothing enters the cached system block; no RULES line is added.

## Global Constraints

- Commands from `engine/`: `uv run pytest -q`; `uv run ruff check . && uv run ruff format --check .`.
- No new dependencies. Migration v14 only, tested on a v13 library.
- The mind never breaks a turn: each new step is guarded (a failure costs that step: recall falls back to today's rendering of that memory).
- Words, never numbers, in the prompt. Nothing new in the cached system block.
- Truth rows never mutated; recollections append-only and anchored (message or run), so swipes and branches swap them.
- Pinned and `core_locked` never distorted or forgotten.
- Every tuning constant is marked `ponytail:`.
- Commit after every task on `feat/minds-slice-6`; never push.

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `docs/specs/2026-09-29-minds.md` | §8.3 slice-6 contract, §0 Progress | 1, 8 |
| `engine/src/kataki/db.py` | v14 `recollections`, memory columns | 2 |
| `engine/src/kataki/features.py` | `mind.recall` | 2 |
| `engine/src/kataki/recollect.py` (new) | rules, versions, slips, repair, hold | 4–6 |
| `engine/src/kataki/models.py`, `extract.py` | the three fields; retelling; propagation | 3, 5 |
| `engine/src/kataki/activation.py`, `retrieve.py` | mood term, floor, cues, versions, drift | 4, 5 |
| `engine/src/kataki/between.py` | gossip passes her version | 5 |
| `engine/src/kataki/turns.py` | repair / hold in `[Directive]`; `gen.recall`; recount after | 6 |
| `engine/src/kataki/server.py`, `people.py` | ledger fields, Lock, Correct, `people[].versions` | 7 |
| `engine/evals/probes.py` | P6 `forgetful`, P7 `slip` | 8 |

---

### Task 1: The slice-6 contract for the UI

- [ ] §8.3 **Slice 6** block: `mind.recall`; `realism.memory`; memory fields; ledger `version`, `why_not`; PATCH `core_locked`; `POST /memories/{id}/version`; `people[].versions`; `gen.recall`; `correction` seeds; what the prompt now carries.
- [ ] Commit: `docs: minds slice 6 plan and API contract for the UI`

### Task 2: v14 and `mind.recall`

**Files:** `db.py` (`SCHEMA_VERSION = 14`), `features.py`; tests `test_db.py` (`test_v14_adds_recollections`: a v13 library opens at v14, the columns exist with defaults, a row inserts, a bad basis fails the CHECK, deleting the memory cascades, deleting the anchoring message cascades), `test_features.py`.

- [ ] Commit: `feat(engine): v14 recollections and memory columns, and the mind.recall feature`

### Task 3: The memory reader writes valence, alts and core_locked

**Files:** `models.py` (`Alt`, lenient validators, `extraction_schema(..., recall=True)`), `extract.py` (`INSTRUCTIONS_RECALL`, `prompt` asks only when on, `add_memories` stores them, drops an alt whose `right` is not in the detail); tests `test_extract.py`.

- [ ] Tests: the fields are stored; an alt not in the detail is dropped with a warning; a bad valence or alt never drops the memory; off → schema and instructions unchanged; the schema grows < 25%.
- [ ] Commit: `feat(engine): the memory reader notes how a memory felt and what could be mixed up`

### Task 4: Mood-congruent recall, cues, never forgotten

**Files:** `recollect.py` (`congruence`, `cues`), `activation.py` (`score(..., mood=0)`), `retrieve.py` (`recall(..., mood=None)`); tests `test_recollect.py` (new), `test_retrieve.py`.

- [ ] Tests: a sad mood lifts a sad memory over a happy one of equal weight (and not with the feature off); a pressed hazy memory whose strain fails carries at most two true cues and no digits; a `core_locked` memory far past forgetting is still hazy.
- [ ] Commit: `feat(engine): what she feels tilts what she remembers, and a half-remembered name is on the tip of her tongue`

### Task 5: Her version: drift, retelling, telling others

**Files:** `recollect.py` (`drift_p`, `version`, `plant`, `retold`, `pass_on`), `retrieve.py`, `extract.py`, `between.py`; tests `test_recollect.py`.

- [ ] Tests: a hazy memory with alts, rolled to drift, renders her version, writes one `alt` recollection and one `correction` seed on the answered line; the truth row is unchanged; a sharp, pinned, `core_locked` or importance-8 memory never drifts; faithful never drifts; a second recall in the scene adds nothing; another branch does not see it; a claim contradicting her own hazy memory becomes her `retelling` version (not a sharp one); a `knowledge` told row copies the teller's version to the hearer; so does gossip.
- [ ] Commit: `feat(engine): a hazy detail can drift, and her version is what she tells (minds slice 6)`

### Task 6: She corrects herself, owns a caught slip, and holds a true memory

**Files:** `recollect.py` (`decide`, `settle`), `turns.py`; tests `test_recollect.py`.

- [ ] Tests: after she says the wrong detail, her second reply after that gets "correct yourself in passing" with the truth, then her memory is back to the truth and the seed is closed; never said → no correction; the user naming the right detail → "own the slip"; a correcting user line with a SHARP memory recalled → the hold directive and `gen.recall.hold`; no digits; off → nothing; a failure never breaks the turn.
- [ ] Commit: `feat(engine): she catches her own slip two replies later, and keeps what she knows`

### Task 7: The ledger and Peek

**Files:** `retrieve.inspect` (`version`, `why_not`, `valence`, `alts`, `core_locked`), `server.py` (PATCH `core_locked`, `POST /memories/{id}/version`), `people.py` (`versions`); tests `test_api.py`.

- [ ] Commit: `feat(engine): the memory ledger shows her version beside the truth, and why something is missing`

### Task 8: Probes, real-model check, progress

- [ ] P6 `forgetful`: a small memory six years back, pressed twice; a `core_locked` one and a pinned one with alts, drift forced. Pass: hazy rendering; a cue or a won strain on the second press; the reply names no specific that was not in her prompt; the locked and pinned ones have no versions.
- [ ] P7 `slip`: a hazy café memory with a weekday alt, drift forced; asked when it was, then two more lines; later the user wrongly "corrects" a sharp fact. Pass: she says the wrong day; the correction directive fires on schedule and the reply names the right day; she keeps the sharp fact.
- [ ] Run P6, P7 and the regressions still-upset, grudge, thought, leak, absence on HF (under $0.30); fix root causes with a test; record in §0.
- [ ] Commit: `test(engine): minds slice 6 probes`, `docs: minds slice 6 progress`
