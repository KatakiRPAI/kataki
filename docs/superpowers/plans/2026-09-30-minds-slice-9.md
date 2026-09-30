# Minds Slice 9 ("She texts like a person") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every task (test first, see it fail, implement, see it pass). Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** In a chat-style story a reply arrives the way a person texts: split into a few bubbles, each after a pause and a typing indicator whose length follows what she writes, how she feels and how hard the moment is; now and then one word has a typo that she corrects in the next bubble ("*forgotten"). How long she answers and in what register (warm, clipped, guarded, animated) is chosen by code from her state and the user's line, and reaches the prompt in words. Prose roleplay is never split or roughened. Local models get an anti-slop sampler preset (min-p, DRY, XTC) that a backend refusing it never notices.

**Architecture:** A new pure module `delivery.py` (the note 15 §7B "courier"): `style` picks the length class and register from state, `chatty` tells a chat line from prose, `plan` splits, times (Jones and Bergen's formula, scaled down and clamped) and plants at most one corrected display typo, seeded by the reply so the same reply always gets the same plan. `turns._generate` asks it before the prompt (length and register into `[Directive]` through a new `context.build(length=…)`), and after the reply is final and clean (the plan into `gen.delivery` and `done.delivery`; the dial into `meta.texting`). `llm.chat_stream` takes an optional `samplers` dict that goes under the role's own body and is dropped on a 400/422; `llm.anti_slop(ep, xtc)` builds it from the role's `samplers` param. Gated by `mind.texting` (stage alpha) and the dial `realism.texting`.

**Tech Stack:** Python 3.12, stdlib only, pytest with the scripted `FakeBackend`.

**Spec:** `docs/specs/2026-09-29-minds.md` §0 (owed display typos from slice 6, P7's typo check, the thought-header placeholder from slice 3, the leak-streaming note from slice 4), §6 (the texting dial, rule 5), §7 slice 9 row, §8.3 (Task 1 writes the contract), §9. Design source: note 15 §1 (corrected typos only), §3 and §7B (the courier, the delay formula, register, length class), §5 (samplers); note 22 §2 step 7g, §4 row 7, C15 (typos display-only), C23 (the dial); note 04 (min-p, DRY, XTC).

## Decisions this plan makes (and why)

- **Chat or prose is decided per reply, by code, on the final clean text.** Kataki has no "phone mode"; a story is prose or chat by how it is played. A reply is chat-style (`mode: "text"`) when it has no `*`/`_` action markup, no double-quoted speech, does not open with a third-person pronoun (she/he/they/her/his/their) and does not name the speaker herself (narration names its subject; a text message does not). Anything else is prose and gets `bursts: []`: never split, retimed or given a typo. A false "prose" costs only the texting effect; a false "text" would mangle a story, so every doubt reads as prose.
- **Bursts split the model's own lines first**, then sentences, and merge the shortest neighbours until the dial's cap: light 2 (newlines only), natural 3, messy 4. Abbreviations (Mr., Dr., St.) and ellipses do not end a sentence. Joined back, the bursts are the saved text word for word (a property test).
- **Timing (Jones and Bergen 2025, note 15 §3):** first burst `delay_ms` = reading the user's line (30 ms a character, capped) + a right-skewed think term (Gamma(2.5, 0.25) s, seeded), times a pace from her mood (wound up: ×0.8; low, hurt or sad: ×1.3; tired: ×1.2) and effort (a decision in `[Directive]`: a secret move, a correction, holding her ground: ×1.5); later bursts 300–900 ms. `typing_ms` = characters × 55 ms (the Turing test's 300 ms per character drags in a long roleplay; note 15 §3 says keep it well below) times the same pace. Clamped: typing 400–6000 ms, a delay at most 8000 ms (note 15: 1.5–8 s). These are hints; the engine never sleeps (§6 rule 5); the UI subtracts the time the model already took from the first delay.
- **Typos: only corrected ones** ("Imperfectly Human": uncorrected typos do nothing). At `natural` one reply in ten, at `messy` one in five, never at `light`; never in her first two replies of the story, within four replies of her last typo, on a turn with a decision in `[Directive]` (secret, correction, hold, agenda), or on a line that stirred her. One lowercase word of four or more letters (never a capitalised word or a name) gets one keyboard-plausible error (swap, drop, double, a neighbouring key), and the next burst is `*right`. P7's "typos corrected ≥ 80%" is met by construction (100%); a "leaves typos" persona is not built (owed, characterisation only).
- **Display only (C15):** `messages.text`, `done.text` and every prompt keep the clean reply; the plan is in `gen.delivery` and `done.delivery`. Seeded from the parent id and the text (a CRC), so the plan is deterministic per reply and a retake gets its own.
- **Length class and register (note 22 §2 step 7g, §4 row 7) replace the "Reply length" line only when texting is on.** The class starts from the user's setting (short/medium/long) and moves one step shorter for a curt user line (four words or fewer), a low, hurt, sad or on-edge mood, or tiredness (energy below slice 7's threshold), one step longer for a long user line (forty words or more), net −2…+1, into `brief | short | medium | long`, each a sentence of words. Register from what she shows and the ledger toward the one she answers: `clipped` (shows anger or annoyance, or holds a grudge against them), `guarded` (trust fell by ten or more), `animated` (buzzing), `warm` (closeness rose by ten or more), else `plain` (no line: calm characters stay natural). It follows what she *shows*, so a masked hurt is not given away by the register. The narrator keeps the setting's line. Relationship stage words are still owed (2a), so closeness and trust movement stand in for stage.
- **Initiative, read-without-reply and double-texting are not built.** Slices 5 and 7 already give her re-entry questions and an agenda at openings; a silence timer needs a wall-clock "phone mode" that §6 rule 5 keeps on story time. Owed with the evidence gap (note 15 §3 Gaps: none found).
- **Anti-slop preset (note 15 §5, note 04):** min-p 0.05 + DRY 0.8/1.75/2 with breakers (newline, colon, quote, asterisk) on every reply; XTC 0.5/0.1 added only on a turn with no decision in `[Directive]` and no memory recalled (note 15: XTC hurts factual slots). A role param `samplers` (`auto | anti-slop | off`), default `auto` = on only for a loopback base URL (llama.cpp and KoboldCpp, the local stack, take all three; hosted OpenAI-style APIs may refuse unknown keys). The preset goes under the role's own body (the user's JSON wins). A 400/422 with the preset is retried once at once without it and that endpoint is remembered (like the `response_format` ladder), so no provider breaks. Reply streams only; JSON calls never carry it.
- **Slice 3's placeholder:** `thought.parse` drops a header value that is the template's own placeholder (in parentheses, or "at most N words"), so the copied template is never kept as a thought.
- **No RULES line, nothing in the cached system block.** Length and register ride in `[Directive]` (the tail). Zero extra calls on every level: delivery is pure code.

## Global Constraints

- Commands from `engine/`: `uv run pytest -q`; `uv run ruff check . && uv run ruff format --check .`.
- No new dependencies, no migration.
- The mind never breaks a turn or loses a reply: every new step is guarded (a failure costs only the delivery, the length line, or the samplers).
- Words, never numbers, in the prompt. Nothing new in the cached system block.
- Lite: zero extra calls. Delays are hints, never server-side sleeps.
- Every tuning constant is marked `ponytail:`. Commit after every task on `feat/minds-slice-9`; never push.

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `docs/specs/2026-09-29-minds.md` | §8.3 slice-9 contract, §0 Progress | 1, 7 |
| `engine/src/kataki/features.py` | `mind.texting` | 2 |
| `engine/src/kataki/delivery.py` (new) | `style`, `chatty`, `split`, `plan` (timing, typo) | 2, 3 |
| `engine/src/kataki/context.py` | `build(length=…)` in place of the setting's line | 4 |
| `engine/src/kataki/turns.py` | length and register into `[Directive]`, `meta.texting`, `gen.delivery`, `done.delivery`, samplers | 4, 5 |
| `engine/src/kataki/llm.py` | `anti_slop`, `chat_stream(samplers=…)` with the refusal fallback | 5 |
| `engine/src/kataki/thought.py` | the placeholder is no thought | 6 |
| `engine/evals/probes.py` | `texting` probe | 7 |

---

### Task 1: The slice-9 contract for the UI

- [x] §8.3 **Slice 9** block: `mind.texting`, `realism.texting`; `meta.texting` and the hold-until-prose rule; `done.delivery` (mode, dial, length, register, bursts with typing/delay, typo and its correction burst); length and register in `[Directive]`; `gen.delivery`; the role param `samplers`.
- [x] Commit: `docs: minds slice 9 plan and API contract for the UI`

### Task 2: `mind.texting`, and length and register from state

**Files:** `features.py`, `delivery.py` (`style`, `LENGTH_WORDS`, `REGISTER_WORDS`); tests `test_delivery.py` (new), `test_features.py`.

- [ ] Tests: the setting is the start (short/medium/long); a curt line, a low mood, tiredness each shorten by one, a long line lengthens by one, and the net shift stays in −2…+1; register follows what she shows (a masked hurt stays plain), a grudge or anger is clipped, fallen trust guarded, buzzing animated, closeness warm; `plain` gives no words; the words have no digits; bad inputs never raise.
- [ ] Commit: `feat(engine): how long and in what tone she answers comes from how she is (minds slice 9)`

### Task 3: The courier

**Files:** `delivery.py` (`chatty`, `split`, `plan`); tests `test_delivery.py`.

- [ ] Tests: prose (actions, quoted speech, a pronoun opening, her own name) gets no bursts; chat text splits on its lines, then sentences, up to the dial's cap (light 2, natural 3, messy 4), never at "Mr." or "..."; joined, the bursts are the text; the first delay grows with the user's line, typing with the burst's length, a low mood and effort slow both, all clamped; a typo only at natural/messy, never when not allowed, on a lowercase word of four letters or more, always followed by `*right`; the same text and seed give the same plan; off gives None.
- [ ] Commit: `feat(engine): a courier splits, times and roughens chat replies, display only`

### Task 4: The turn uses it

**Files:** `context.py` (`build(length=…)`), `turns.py`; tests `test_turns.py`, `test_context.py`.

- [ ] Tests: with the dial on, the character's `[Directive]` carries the class's words instead of the setting's, and a register line when not plain; the narrator keeps the setting's; `meta.texting` is the dial; `done.delivery` and `gen.delivery` hold the plan; `messages.text` and `done.text` are clean when a typo is planted; a prose reply gets `mode: "prose"` and no bursts; off (feature or dial) is slice 8 exactly (no `delivery`, the setting's words, `meta.texting` null); a delivery failure never breaks the turn; the typo gate (first replies, a recent typo, a decision) holds.
- [ ] Commit: `feat(engine): replies carry a delivery plan, and their length and tone are decided by code`

### Task 5: Anti-slop samplers

**Files:** `llm.py` (`anti_slop`, `chat_stream(samplers=…)`), `turns.py`; tests `test_llm.py`, `test_turns.py`.

- [ ] Tests: `auto` is on for 127.0.0.1/localhost and off elsewhere, `anti-slop` on, `off` off; XTC only when asked; the role's body wins over the preset; a 400 with the preset is retried without it and the endpoint remembered (the next request has none); a 400 without it is still an error; JSON calls never carry it; the reply turn sends it for a local role.
- [ ] Commit: `feat(engine): an anti-slop sampler preset for local models, dropped by backends that refuse it`

### Task 6: The thought template is never a thought

**Files:** `thought.py` (`parse`); tests `test_thought.py`.

- [ ] Tests: "Mira thinks: (in Mira's own voice, at most 25 words)" and "Mira wants: (from this moment, at most 10 words)" parse to None; a real thought still parses.
- [ ] Commit: `fix(engine): the thought header's placeholder is never kept as her thought`

### Task 7: Probe, real-model check, progress

- [ ] `texting` probe in `evals/probes.py`: a chat-style Mira (natural dial, then messy), eight texting lines and two prose lines; checks: every chat reply's bursts join to the saved text, no more than the cap, delays within bounds; every typo is followed by its correction and the saved text never has it; prose replies get no bursts; the length class moves with a curt line; the anti-slop preset forced on for one reply reaches the provider or falls back without an error.
- [ ] Run texting and the regressions still-upset, grudge, leak, slip, wants on HF (under $0.20); fix root causes with a test; record in §0.
- [ ] Commit: `test(engine): minds slice 9 probe`, `docs: minds slice 9 progress`
