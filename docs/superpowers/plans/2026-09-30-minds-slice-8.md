# Minds Slice 8 ("She changes, slowly") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every task (test first, see it fail, implement, see it pass). Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** A character changes over a long story, slowly, on evidence, and the user can see and veto every change. After a big skip (a week or more of story time, forty new memories, or a closed chapter) the Between call she already makes for the skip grows a deep section: how she has come to see the people closest to her, a line about herself, and up to two candidate growth rings ("learned to ask for help"), each citing the memories it rests on. Code gates every line mechanically (cited handles only, no new names or numbers, hard length caps) and drops what fails with a visible warning. A ring enters as a `seed`; it becomes a `ring` only when later scenes reinforce it (three memories from two scenes after it); only then may it nudge one personality axis, by a step code sets and caps, in this story only. Peek shows every reflection with its evidence and the drift it causes; the user accepts, rejects (the drift goes with it) or locks each one. At most one reflection line reaches the mind block, in words. In a group, when nobody is named, a seeded score picks who answers (someone stirred, someone with something to say, or whoever has spoken least) in place of the old "whoever spoke last" / "the quietest" fallbacks, and a retake keeps the same speaker. The owed "reject a grudge in Peek" lands too.

**Architecture:** A new module `growth.py` owns the `reflections` rows (v16, note 22's DDL, anchored like every minds table, append-only versions linked by `supersedes_id`): the deep trigger, the working set of handles for the call, the anti-drift gate, writing, reinforcement, trait drift, the user's accept/reject/lock, the mind-block line and Peek's view. `between.py` decides the trigger in the code tick (B0, zero calls, recorded in the run's `raw.deep`), adds the deep section to the one B1 call's schema and prompt when it holds, and hands the answer to `growth.write`; the tick also reinforces seeds. `inner.profile` applies the capped drift. `turns.speaker_why` gains the score (with `mind.growth` on). `bonds.reject` resolves a grudge. Gated by `mind.growth` (stage alpha).

**Tech Stack:** Python 3.12, stdlib only, pytest with the scripted `FakeBackend`.

**Spec:** `docs/specs/2026-09-29-minds.md` §1 decision 1 (reflection cycles allowed as the Between job's deep pass, gated and inspectable), §3, §6 rule 6, §7 slice 8 row, §8.3 (Task 1 writes the contract), §9. Design source: note 22 §1 (`reflections` DDL), §3 (B2), §4, §6 (C2, C3, C5, C9, C16, C17), §7 slice 8, §8 (P11, P12, P14); note 12 §7 (growth caps); note 17 §6 (rings); note 16 §6 (speaker score, gossip).

## Decisions this plan makes (and why)

- **No second call.** The deep section rides in slice 5's B1 call for that character (note 22 §3), added to its schema only when a deep trigger holds. B1 already runs in the background worker, after the story has been quiet for a few seconds, and steps aside for every reply; a reply never waits for it. That is "idle-only" on standard. Lite has no B1, so no deep pass and zero extra calls.
- **Triggers, decided by code in B0** (recorded as `raw.deep = {character: reason}` on the between run): `long_skip` (the skip is 7 story-days or more; 1 day on premium), `memories` (40 or more memories she holds, dated after her last deep pass), `arc` (a chapter on this branch closed since her last deep pass). Her last deep pass is the latest between run on the path whose `raw.deep` has her. An arc closed with no skip after it waits for the next skip (owed: a between run on chapter close).
- **What the call sees** is a closed working set (note 22 §3, note 14 §6): at most 30 of her own memories as handles `M<id>` (her strongest and newest, never another's), the people she knows as `P<id>`, and her card's name and description. Never an earlier reflection (C3: regenerate from raw sources). What it returns: `relationship` (0-2: `about`, `line` ≤ 25 words in her voice, `sources`), `self` (`line` ≤ 6 sentences / 80 words, `sources`) or null, `rings` (0-2: `kind` stance|habit|skill|scar|belief, `claim` ≤ 15 words, `sources`, `trait` from a closed list of directions or `none`).
- **The gate is mechanical** (note 14 §6), per item: at least one source, every source a handle it was given, an `about` it was given, the length caps, no digit and no number word that is not in the cited memories, no capitalised word (outside a sentence's first word and "I") that is not a name in the story or a word of the memories it was shown. A ring also needs three distinct sources from two scenes (note 17 §6: a scene is the memory's scene, or its story-day when it has none). A failed item is dropped and named in `raw.deep_warnings[character]`, which Peek shows; a failed call or a missing deep section is one warning too. Never an empty box without a reason.
- **Append-only versions.** A reflection's status changes by a new row that `supersedes_id` the one before, carrying the same text, sources and delta: anchored on a skip's run when code changes it (reinforcement, a seed let go), unanchored when the user does (accept, reject, lock: the user's own rows hold on every branch, like a pinned memory). The current reflection is a live row no live row supersedes. A new deep pass's relationship line about someone supersedes her previous one about them, and a new self line the previous self line; rings only add (a new ring never supersedes one).
- **Statuses.** Lines (`self`, `relationship`) are in force at once (`ring`). Rings enter as `seed`; at a later skip's tick (zero calls, every level) a seed reinforced by three memories from two scenes dated after it, sharing a content word with its claim, becomes a `ring`; a seed unreinforced after 30 story-days becomes `past` (kept, viewable). `accept` makes a seed a `ring` at once; `lock` keeps it for good (never superseded by code); `reject` makes it `rejected` (anything it did is undone). `fading` is not written yet.
- **Trait drift by code.** The model may name a direction for a ring (`warmer, colder, bolder, meeker, franker, more_guarded, more_honest, less_honest, softer, firmer, calmer, touchier`, or `none`); code maps it to one axis and a step of 2 points (note 12 §7) stored in `trait_delta`. A delta counts only while its ring is `ring` or `locked`; per axis the sum is capped at ±10 (note 12: at most ±10 per arc); it applies in this story only (reflections belong to the story's entity), inside `inner.profile`, so moods, pushback and honesty follow it. Rejecting the ring removes it. The prompt never sees a number; Peek gets the delta and words ("a little warmer").
- **One line in the mind block** (note 22 §4 row 3; C17: LLM relationship lines only from the deep pass): her relationship line about whoever she is answering, else her strongest `ring`/`locked` ring's claim, as "How you have come to see Aren: “…”" or "Something that has changed in you: …". Stored as `gen.growth`; a Mind graph INSIDE node. No RULES line.
- **The speaker score** (note 16 §6, C9): picked and named stay hard rules. With two or more candidates and `mind.growth` on, each gets `balance` (1 if she is the one being answered, minus 2 × her share of the last 12 replies), `urgent` (1.5 when her strongest feeling right now is a bad one at "quite" or more, from slice 1's state), `wants_in` (talkativeness − 0.5, plus 1 when the line names the cue of a goal she is pursuing); the next speaker is drawn from a softmax over the scores with an RNG seeded by the story and the line being answered, so the same path always gives the same speaker. The reason is `urgent` when her urgent term fired, else `wants_in` when her wants term is 0.5 or more, else `balance`. With one candidate the old `last`/`quietest` stay. Zero calls.
- **Gossip** is slice 5's B0 transfer, unchanged; P14 checks it (only between those who spent the skip together, as a told belief below certainty, never a secret kept from the hearer).
- **Reject a grudge.** `POST /opinions/{id}/reject` writes, for each row of that grudge, an unanchored row resolving it with event `rejected`; the ledger then skips the grudge entirely (not "forgiven": it never happened). Peek's `grudge` gains its row `id`.
- **P12** (drift at 50 turns, the cheapest honest version): 24 small-talk lines, an eight-day skip (the deep pass runs on the real model), 24 more; the built-in embedder scores each reply against Mira's card voice (description plus example lines); pass when the mean of the last five is at least the mean of the first five minus 0.1, and no reply opens like an assistant. The deep pass's rows and warnings are printed; any line in them is checked again against the gate.

## Global Constraints

- Commands from `engine/`: `uv run pytest -q`; `uv run ruff check . && uv run ruff format --check .`.
- No new dependencies. Migration v16 only, tested on a v15 library.
- The mind never breaks a turn and never loses a reply: every new step is guarded.
- Words, never numbers, in the prompt. Nothing new in the cached system block (no RULES line).
- Rows append-only and anchored (message, run, or the user's own). Truth rows never mutated.
- Lite makes zero extra calls; the deep pass never blocks a reply.
- Every tuning constant is marked `ponytail:`. Commit after every task on `feat/minds-slice-8`; never push.

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `docs/specs/2026-09-29-minds.md` | §8.3 slice-8 contract, §0 Progress | 1, 9 |
| `engine/src/kataki/db.py`, `features.py`, `chat.py`, `library.py` | v16 `reflections`, `mind.growth`, clock shift, merge | 2 |
| `engine/src/kataki/growth.py` (new) | gate, trait drift, rows, versions, accept/reject/lock, reinforcement, line, Peek | 3, 5, 6, 7 |
| `engine/src/kataki/inner.py` | the profile carries the capped drift | 3 |
| `engine/src/kataki/between.py` | the trigger in B0, the deep section of B1, reinforcement at the tick | 4, 5 |
| `engine/src/kataki/turns.py`, `mind.py` | the mind-block line, `gen.growth`, the node; the speaker score | 6, 8 |
| `engine/src/kataki/people.py`, `server.py`, `bonds.py` | `people[].growth`, `POST /reflections/{id}`, `POST /opinions/{id}/reject` | 7 |
| `engine/evals/probes.py` | P12 `drift`, P14 `group` | 9 |

---

### Task 1: The slice-8 contract for the UI

- [ ] §8.3 **Slice 8** block: `mind.growth`; `people[].growth` (reflections with evidence, trait and status; drift; warnings); `POST /reflections/{id}` accept/reject/lock; `gen.growth` and the Growth node; the speaker reasons `urgent | wants_in | balance`; `POST /opinions/{id}/reject` and `grudge.id`.
- [ ] Commit: `docs: minds slice 8 plan and API contract for the UI`

### Task 2: v16 `reflections` and `mind.growth`

**Files:** `db.py` (`SCHEMA_VERSION = 16`), `features.py`, `chat.py` (a clock edit shifts a between run's reflections), `library.py` (merge remaps `knower_id`, `subject_id`); tests `test_db.py` (`test_v16_adds_reflections`: a v15 library opens at v16, a row inserts, a bad kind/status fails the CHECK, deleting the anchoring run cascades), `test_features.py`.

- [ ] Commit: `feat(engine): v16 reflections, and the mind.growth feature`

### Task 3: Growth rules: the gate, trait drift, versions, the user's say

**Files:** `growth.py` (`gate`, `step`, `drift`, `live`, `current`, `write`, `act`), `inner.py` (`profile` adds the drift); tests `test_growth.py` (new).

- [ ] Tests: the gate passes a cited, short, plain line and fails each of: no source, an unknown handle, an unknown `about`, too long, a new number, a new proper noun; a ring needs three sources from two scenes; a direction maps to one axis and a 2-point step, `none` to nothing; drift counts only `ring`/`locked`, is capped at ±10 per axis, and is gone when rejected; accept/reject/lock write a new unanchored version and never touch the old row; current skips superseded rows and rows of another branch; `inner.profile` carries the drift only with the feature on.
- [ ] Commit: `feat(engine): growth rings are gated, capped and reversible`

### Task 4: The deep pass

**Files:** `between.py` (`at_skip` records the trigger; `schema`, `read`, `_ask`, `_write` gain the deep section), `growth.py` (`trigger`, `working`, `take`); tests `test_between.py`, `test_growth.py`.

- [ ] Tests: an eight-day skip triggers it, a two-day one does not, forty new memories or a closed chapter do; lite has no deep pass and makes no call; with a trigger the one B1 call's schema has `deep`, its prompt lists her own memories as handles and no one else's, and no earlier reflection; good items become rows on the run (lines in force, rings as seeds with the code's delta), bad ones are dropped with warnings; a failed call leaves a warning and the tick's rows; undoing the skip drops them; a failure never breaks the diary.
- [ ] Commit: `feat(engine): after a long time away she reflects, on evidence (minds slice 8)`

### Task 5: Reinforcement

**Files:** `growth.py` (`reinforce`), `between.py` (the tick calls it); tests `test_growth.py`.

- [ ] Tests: a seed with three matching memories from two later scenes becomes a ring at the next skip (anchored on it), with fewer it stays a seed, after thirty days unreinforced it is past; a locked or rejected one is never touched; its drift starts counting only as a ring; zero calls, on lite too.
- [ ] Commit: `feat(engine): a growth ring takes hold only when later scenes bear it out`

### Task 6: One line in the mind block

**Files:** `growth.py` (`line`), `turns.py` (`gen.growth`), `mind.py` (Growth node); tests `test_growth.py`, `test_mind.py`.

- [ ] Tests: the relationship line about the one she answers wins, else the strongest ring; a seed, a rejected or past one never reaches the prompt; one line at most, no digits; off → nothing; a failure never breaks the turn; the node shows it.
- [ ] Commit: `feat(engine): what she has come to feel reaches her reply, in one line`

### Task 7: Peek and the user's say

**Files:** `people.py` (`growth`), `server.py` (`POST /reflections/{id}`, `POST /opinions/{id}/reject`), `bonds.py` (`reject`, `grudge.id`), `growth.py` (`public`); tests `test_api.py`, `test_bonds.py`.

- [ ] Tests: Peek lists reflections with sources, evidence, trait words and warnings; accept/reject/lock through the route (404 unknown, 422 bad action); rejecting a ring takes its drift away; rejecting a grudge removes it from the ledger's words and the mind block, on every branch; off → `growth: null`.
- [ ] Commit: `feat(engine): Peek shows how she has changed, and you can accept, reject or lock it`

### Task 8: The group speaker score

**Files:** `turns.py` (`speaker_why`, `_score`), `mind.py` (`WHY`); tests `test_turns.py`.

- [ ] Tests: picked and named still win; with two who heard, the stirred one is picked (`urgent`), the one whose goal was named (`wants_in`), else the one who spoke less (`balance`); the same path gives the same speaker every time; one candidate keeps `last`/`quietest`; off → the old rules.
- [ ] Commit: `feat(engine): in a group, who answers is weighed, not just whoever spoke last`

### Task 9: Probes, real-model check, progress

- [ ] P12 `drift` and P14 `group` in `evals/probes.py`.
- [ ] Run P12, P14 and the regressions still-upset, grudge, leak, absence, wants on HF (under $0.40); fix root causes with a test; record in §0.
- [ ] Commit: `test(engine): minds slice 8 probes`, `docs: minds slice 8 progress`
