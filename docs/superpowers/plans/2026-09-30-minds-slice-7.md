# Minds Slice 7 ("She wants something") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every task (test first, see it fail, implement, see it pass). Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** A character wants things and has a body. The card's `want` becomes a goal she pursues in conversation: at a natural opening (the user touches its topic, asks what is new, or the talk lulls) code puts it on her agenda, at most once every four of her replies, never on an emotional line and never when a heavier decision (a secret, a re-entry, a self-correction) already fills `[Directive]`. When the user dodges it twice it goes dormant; half a story-day later it can come back ("still on your mind"). Her `need` and `fear` are kept as goals she does not pursue (inspectable, and read by the Between job). Needs are code: circadian energy from her chronotype on the story clock, and the SDT drives autonomy, competence, relatedness and stimulation, which drift in closed form and move with what is said to her. The single most pressing one, only when it is below its threshold and not shown in her last three replies, becomes one line of behaviour in the mind block; a tired character is short-tempered and denies being tired. A skip's diary call may move one goal (progress, done, dropped, revived). Peek shows `goals` and `needs`; the Mind graph gains Goal and Body nodes.

**Architecture:** A new module `goals.py` owns the goal rows (v15 `goals`, append-only versions per `key`, anchored like every minds table), the opening, the agenda pick, the judgment of the user's answer and Peek's view. Needs live in `inner.py` beside the mood they share `mind_states.state` with (`state.needs`), plus `energy()` from the clock. `turns._generate` runs the judgment and the pick (step 7f) and the need row (row 6), records `gen.agenda`, `gen.goal`, `gen.need`; `after.py` gains the closed `agenda` outcome; `between.py`'s B1 call gains an optional `goal` change. Gated by `mind.goals` (stage alpha).

**Tech Stack:** Python 3.12, stdlib only, pytest with the scripted `FakeBackend`.

**Spec:** `docs/specs/2026-09-29-minds.md` §3, §6 (rule 1: goals shape how she talks, never whether), §7 slice 7 row, §8.3 (Task 1 writes the contract), §9. Design source: note 22 §1 (goals DDL, needs in `mind_states.state.needs`, profile `want/need/fear/chronotype_h`), §2 steps 7f and 13, §3 (goal_changes), §4 rows 5 and 6, §7 slice 7, §8 P10; note 17 §1, §2, §8; note 12 on SDT reactance.

## Decisions this plan makes (and why)

- **Goal deltas come from the side call's closed `agenda` outcome, not from extraction.** The agenda's counters are per turn: whether her reply raised the item, whether the user's very next line dodged it. Extraction runs every few turns over a batch of lines, after the fact, so it cannot count "two deflections" on time, and note 22 keeps per-turn social fields out of it so its schema and JSON validity do not grow. The side call already reads the user's line and her reply every standard turn; it gains one field, asked only on a turn that raised an item (`tried | not_tried`) or that answers one (`deflected | progressed | done`): closed enums, and absent otherwise, so the side call's JSON is unchanged on most turns. **Rules decide first on every level** (lite included, zero calls): an item is tried when the reply names one of its cue words; the answer took it up when the user's line does, else it dodged it. On standard the side call's label then replaces the rules' judgment row (the model sees "I'd rather not talk about boats" as a dodge that names the cue). Longer-term progress comes from the Between call (one change per skip).
- **Goals are versions, judgments are anchored on the user's line.** A judgment is a new `goals` row for that key anchored on the line that answered her (a swipe of her reply keeps it; editing that line drops it). Seeded goals are the user's own rows (no anchor, like card secrets). A Between change rides on the skip's run. The current goal = the latest live row per key by `(story_time, id)`.
- **The opening is code** (note 17 §2, a cheap Inner Thoughts gate): `topic` (the user's line names a cue word), `asked` (an open question: "what's new", "how are you", "how was your day"...), `lull` (a short line, six words or fewer, with no question). No opening, no agenda. Never on a line that carried an event (the rules' `inner.sense` or a ledger event): an emotional line is not the moment.
- **Rate, drop, rest.** At most one offer every `EVERY = 4` of her replies (counted from `gen.agenda` on the path, so branches count their own). After `DROP = 2` dodges the goal is `dormant`; a dormant goal can be offered again once `REST = 12` story-hours have passed since it went dormant (it "resurfaces": the directive says she let it drop before). Taken up (`progressed`) resets the dodges and adds a little progress; `done` ends it. All `ponytail:` constants.
- **One item at a time** (note 22 row 5): when the agenda fires, slice 5's "On your mind" seed row stays out of that reply. The agenda is a decision (code chose the moment), so it goes in `[Directive]`: "You want to X. Aren's line gives you an opening: answer him first, then work it in once, lightly, in your own words; if he doesn't take it up, let it go for now."
- **need and fear are goals she does not pursue.** `need` (the unexamined lesson) and `fear` are seeded as `dormant` ambitions with keys `need` and `fear`: never offered (she does not know she is pursuing them), shown in Peek, and given to the Between call as context. The card may also list explicit `goals` (`[{"text", "cue", "tier", "priority"}]`); `want` may be a string or `{"text", "cue"}`. Without a `cue`, content words of the text are used (stop words and people's names removed).
- **Needs in closed form, shown as behaviour.** `state.needs = {autonomy, competence, relatedness, stimulation}` (0 = starved, 1 = met), created on a character's first turn with `mind.goals` on. `inner.tick` drifts each toward its resting level with a 12 story-hour half-life (relatedness rests lower for the anxiously attached); `inner.react` moves them by what the line did to her (insult: competence and relatedness down; threat or an order: autonomy down; praise: competence up; good news: stimulation up; being talked to at all: a little relatedness; a very short line: a little less stimulation). Energy is never stored: `energy(minute_of_day, chronotype_h)` is a circadian curve (peak mid-afternoon, trough before dawn) minus sleep pressure after sixteen hours awake, shifted by `chronotype_h`. Below threshold (`TIRED = 0.3`, `LOW = 0.3`), the lowest one is shown as one row, outside a three-reply cooldown (`gen.need` on the path). Needs need `mind.affect` for the drives (they live in its state); energy needs nothing. Words only.
- **The Between call moves at most one goal.** When she has goals, B1's schema gains an optional `goal`: `{"goal": "G<id>", "change": "progressed|stalled|done|dropped|revived", "tactic": "<=12 words"}` or null; code writes one row on the run (`stalled` writes only a new tactic). Lite has no B1, so no progress between scenes (the rest still works).
- **Lite: zero extra calls.** Judgment, pick, needs and energy are code. **No RULES line**: the mind block's header already says "show it, never say it". Nothing enters the cached system block.
- **Stories made before v15 have no goals** (the card is copied at creation, like secrets); editing goals in Backstage is §6 rule 6, owed.

## Global Constraints

- Commands from `engine/`: `uv run pytest -q`; `uv run ruff check . && uv run ruff format --check .`.
- No new dependencies. Migration v15 only, tested on a v14 library.
- The mind never breaks a turn: each new step is guarded (a failure costs that step).
- Words, never numbers, in the prompt. Nothing new in the cached system block.
- Rows append-only and anchored (message or run); swipes and branches swap them.
- Roleplay never stalls: the agenda and needs shape how she talks, never whether.
- Every tuning constant is marked `ponytail:`. Commit after every task on `feat/minds-slice-7`; never push.

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `docs/specs/2026-09-29-minds.md` | §8.3 slice-7 contract, §0 Progress | 1, 8 |
| `engine/src/kataki/db.py`, `features.py`, `chat.py`, `library.py` | v15 `goals`, `mind.goals`, clock shift, merge, seeding | 2, 3 |
| `engine/src/kataki/goals.py` (new) | seed, live, opening, pick, judge, Peek | 3, 4 |
| `engine/src/kataki/inner.py` | needs, energy, the need row | 5 |
| `engine/src/kataki/turns.py`, `after.py` | step 7f, row 6, `gen.agenda/goal/need`, the `agenda` outcome | 4, 5 |
| `engine/src/kataki/between.py` | B1 `goal` change | 6 |
| `engine/src/kataki/people.py`, `mind.py` | `people[].goals/needs`, Goal and Body nodes | 7 |
| `engine/evals/probes.py` | P10 `wants` | 8 |

---

### Task 1: The slice-7 contract for the UI

- [ ] §8.3 **Slice 7** block: `mind.goals`; card fields; `people[].goals`, `people[].needs`; `gen.agenda`, `gen.goal`, `gen.need`; the side call's `agenda`; the Mind graph Goal and Body nodes; B1's goal change.
- [ ] Commit: `docs: minds slice 7 plan and API contract for the UI`

### Task 2: v15 `goals` and `mind.goals`

**Files:** `db.py` (`SCHEMA_VERSION = 15`), `features.py`, `chat.py` (a clock edit shifts a between run's goal rows), `library.py` (merge remaps them); tests `test_db.py` (`test_v15_adds_goals`: a v14 library opens at v15, a row inserts, bad tier/status fail the CHECK, deleting the anchoring message cascades), `test_features.py`.

- [ ] Commit: `feat(engine): v15 goals, and the mind.goals feature`

### Task 3: Goals from the card

**Files:** `goals.py` (`seed`, `cues`, `live`), `library.py` (seed at story creation); tests `test_goals.py` (new).

- [ ] Tests: want (string or dict), need, fear and explicit goals become rows (need/fear dormant); a malformed entry is skipped, never fatal; cue words drop stop words and names; `live` gives the latest version per key on this branch.
- [ ] Commit: `feat(engine): a character's want, need and fear become her goals`

### Task 4: The agenda

**Files:** `goals.py` (`opening`, `pick`, `judge`, `tried`, `relabel`), `turns.py`, `after.py` (`agenda` outcome); tests `test_goals.py`.

- [ ] Tests: the opening (topic, asked, lull, none; none on an event); an offer only at an opening, at most once every four of her replies, with a directive that names no number; not when a secret, re-entry or repair directive is there; the seed row stays out when it fires; tried by the cue; a dodge is judged on the user's line (anchored there), two dodges make it dormant and it is not offered again until it has rested, then it resurfaces; taken up resets the dodges; the side call's label replaces the rules' judgment; lite makes no extra call; off → nothing; a failure never breaks the turn.
- [ ] Commit: `feat(engine): she brings up what she wants at an opening, and lets it go when you dodge it (minds slice 7)`

### Task 5: Needs and energy

**Files:** `inner.py` (`NEEDS`, `energy`, `drive`, `tick` drift, `need_row`), `turns.py`; tests `test_inner.py`, `test_goals.py`.

- [ ] Tests: energy is high mid-afternoon, low before dawn, shifted by chronotype; drives drift to rest in closed form and move with insults, orders and praise; the most pressing need below threshold becomes one row, not within three replies of the last; the tired row says to deny it; no digits; off → nothing.
- [ ] Commit: `feat(engine): she gets tired late at night and has needs of her own, shown, never announced`

### Task 6: Goals between scenes

**Files:** `between.py` (`schema(goals)`, `read`, `_ask`, `_write`), `goals.py` (`change`); tests `test_between.py`.

- [ ] Tests: with goals the call's schema has one optional `goal`; a change writes one row on the run (undone with the skip); a bad handle is dropped; without goals the call is unchanged.
- [ ] Commit: `feat(engine): time away can move one of her goals`

### Task 7: Peek and the Mind graph

**Files:** `people.py` (`goals`, `needs`), `mind.py` (Goal and Body nodes), `goals.public`; tests `test_api.py`, `test_mind.py`.

- [ ] Commit: `feat(engine): Peek shows what she wants and needs, and the Mind graph shows the goal a reply pursued`

### Task 8: Probe, real-model check, progress

- [ ] P10 `wants`: Mira wants Aren to come and see the boat she built (cue: boat, sail, launch); ten lines, every raise dodged, then the next day. Pass: every offer at an opening; no two offers within four of her replies; the first offer is tried; two dodges → dormant, and no offer while dormant; the next day it resurfaces at an opening.
- [ ] Run P10 and the regressions still-upset, grudge, leak, absence, slip on HF (under $0.30); fix root causes with a test; record in §0.
- [ ] Commit: `test(engine): minds slice 7 probe`, `docs: minds slice 7 progress`
