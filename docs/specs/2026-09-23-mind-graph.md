# Backstage · the Mind: how a reply came about

> The last piece of the second design handoff (`docs/kataki-design/kataki-design/`, screen 14
> `Scene-Backstage.html`). Slices 1–4 of that handoff are built (commits `0a2ffc8` … `38cfd18`).
> This spec covers the **Mind** graph and the Backstage re-layout around it. Status: **approved 2026-09-23** with the
> recommendations in §7: Mind 1–4 now, Appraise measured before it is decided.

## 0. Progress

- [x] Mind 1 · the graph from what is already recorded (§4.1, §5.1): `c25e23c` engine, then the panel; Backstage opens on it, Memory one switch away. Found: relationships never reach the reply prompt, so feelings show blue.
- [ ] Mind 2 · the turn's trace: why this speaker, the recall cue, timings (§4.2)
- [ ] Mind 3 · how she feels about you, across the story (§4.3)
- [ ] Mind 4 · Backstage re-laid: Mind on the left; Prompt, Cast, Engine on the right (§5.2)
- [ ] Mind 5 · (gated on §7.1) the Appraise step: a real inner step before the reply (§4.4)

## 1. What this is for

Backstage used to show *what a character remembers*. The design wants it to show *how a
character's mind produced the last reply*: what came in, what she noticed, what came back to her,
how she felt, and what she decided, with the path that won drawn in gold. Memory becomes one node,
with a "Memory · 41" link to the full list.

**The rule this spec is built on: the graph shows only what the engine really did.** Every node
and every number comes from a row the engine wrote while making that reply. A node the engine has
no data for is left out, not drawn with made-up numbers. Backstage is where the user goes to see
why the machine did something, so anything invented there does more harm than a gap.

That rule splits the mockup in two:

| Mockup node | Real today? | Where it comes from |
|---|---|---|
| IN · Heard | yes | the pending line(s) this speaker heard (`chat.heard_by`), and who said them |
| IN · Saw | yes | presence changes since their last line (`presence`) |
| IN · Place, Time | yes | the scene's place and time of day; the story date and the skip since their last line |
| SENSE · Perception ("a claim that clashes with what she knows") | **no** | the claim is only extracted *after* the reply |
| SENSE · Attention | partly | the engine's speaker choice has a reason (picked by you / addressed by name / last to speak / quietest); nothing about attention within the line |
| INSIDE · Recall | yes | `context_log.memories`: every candidate, its score (A), tier, and whether it was rendered, degraded or dropped |
| INSIDE · Feeling (warmth, trust, doubt) | yes (since 2026-09-23) | live `edges` from the speaker; now in the reply's prompt as `[How Mira feels]`, their ids logged with the tail; tones from slice 4, no numbers |
| INSIDE · Belief | yes | `knowledge.belief` below 0.7 on memories that reached the prompt |
| INSIDE · Goals | **no** | nothing records a goal |
| INSIDE · Persona | yes | the card and primer sections of the prompt (`context_log.sections`) |
| DECIDE · Intent | **no** | nothing records an intent |
| DECIDE · Expression | yes | the face call (`messages.expression`), for characters with sprites |
| SPOKE | yes | the reply, its model, time and tokens |

The nodes marked **no** exist only if the engine gains a real step that produces them (§4.4, Mind 5).
Until then they are simply not drawn.

## 2. What is already here

- `context_log` per reply: the prompt's sections with token counts and caps, every recalled memory
  with its activation parts (A, B, S, G, importance, fidelity, noise, effortful), what was
  rendered, and the prompt itself (the last 20 per story).
- `messages.gen`: role, model, finish, reasoning, usage, think_ms. `messages.expression`.
- `edges` (relationships, with `run_id`, `story_time`, `ended`), `knowledge` (belief, source),
  `presence` (arrivals and departures).
- `signals.py` already turns edges into tones (§2.7 of the UI spec and slice 4).
- Backstage today: the Memory panel (820 of 1392) with Prompt, Cast and Reading stacked on the
  right (`scene/Backstage.tsx`).

## 3. Words

- **A turn's mind**: the graph for one reply, `GET /messages/{id}/mind`.
- **Gold / the path that won**: whatever reached the prompt the reply was written from. Blue: what
  was considered and cut (a memory dropped for the budget, an edge whose section was evicted). This
  is an honest meaning of "won" that the engine can actually say.
- **Weight**: the number in a node's corner. It is the node's own real number: recall is the
  memory's activation squashed to 0–1, belief is `knowledge.belief`, heard is 1. A node with no
  honest number shows none; the design's bar under a node is drawn only when there is a weight.

## 4. Engine

### 4.1 The mind from what is recorded (Mind 1)

`mind.py`, read-only, like `signals.py`. `GET /messages/{id}/mind` (assistant lines only, else
404):

```json
{"message_id": 88, "speaker": {"id": 29, "name": "Mira"}, "clock": "Year 7, Day 1, 19:22",
 "date": "Six years after the storm",
 "nodes": [
   {"id": "heard", "column": "in", "kind": "heard", "title": "Heard",
    "text": "Aren: “buried it by the lighthouse”", "weight": 1, "gold": true},
   {"id": "m88", "column": "inside", "kind": "recall", "title": "Recall",
    "text": "Ledger · behind the bar · hazy", "weight": 0.42, "gold": true,
    "detail": {"memory_id": 88, "tier": "hazy", "A": -0.31, "rendered": "gist"}},
   ...],
 "links": [{"from": "heard", "to": "m88", "gold": true}],
 "spoke": {"text": "…", "model": "qwen3.5-9b", "ms": 1900, "tokens": 64}}
```

- **Columns** are fixed: `in`, `sense`, `inside`, `decide`. A column with no nodes is still drawn,
  labelled, and empty, so the absence shows.
- **Links**: the cue lines → each recalled memory; heard → belief when the recalled memory is the
  one the belief is about; every gold INSIDE node → expression and → spoke. No link is drawn
  without a real dependency behind it.
- Per node kind, at most: 4 recalls (gold first, then the best dropped), 3 feelings, 2 beliefs, 1
  persona. The rest are counted ("+ 6 more recalled") and one click away in the node's detail.
- **Tests** (`tests/test_mind.py`, on the ledger scene the signal tests use): a dropped memory is
  blue and a rendered one gold; a thought (audience `[]`) is not an IN node for anyone; a whisper
  reaches only its hearer's graph; belief appears only for a memory that reached the prompt; the
  narrator's graph has no feelings; a reply with no `context_log` row (an imported story) returns
  the IN and SPOKE nodes and nothing invented.

### 4.2 The turn's trace (Mind 2)

Three facts the engine decides but throws away. Record them in `context_log.trace` (a JSON column in the next free
migration: 9 today, unless the image work takes it first), written in `_generate`:

- **why this speaker**: `select_speaker` returns its reason with the id: `picked` / `named` /
  `last` / `quietest` / `narrator`. This becomes the SENSE · Attention node ("Answered because Aren
  named her").
- **the recall cue**: the text recall searched with (the last two lines the speaker heard). This
  becomes the SENSE · Cue node, gold-linked into each recalled memory.
- **timings**: `recall_ms`, `prompt_ms`, `first_token_ms`, `total_ms`, and the face call's `ms`.
  These fill the design's **Engine · this turn** panel (model, seconds, tokens, tok/s per job).
  Jobs that did not run this turn say "idle", as the mockup does.

Tests: each reason is recorded for the case that causes it; timings are present and ordered.

### 4.3 How she feels about you, across the story (Mind 3)

The design's chart shows warmth, trust and doubt as lines over story time. Edges carry no numbers,
so the chart is **derived, and says so**: at each extraction run, per tone, count the live edges
from the speaker to the persona (warm +1, feeling −1 for warmth; trust +1, distrust −1 for trust)
and the persona's claims she disbelieves (belief < 0.7) for doubt. The endpoint is
`GET /stories/{id}/feelings?about={entity}&who={entity}` and returns points per run, with the
story time and the date. Skips over a day are marked on the time axis, as the mockup marks "six
years later". The chart's caption says "from what she has come to feel, read by memory". Once Mind 5
exists, appraisal numbers replace the counts.

### 4.4 The Appraise step (Mind 5, only if §7.1 says yes)

The only honest way to get Perception, Goals and Intent is a real step that produces them and that
the reply then *uses*:

- A new job in Models, **Mind**: its own model pick like every other job, off by default.
- **Before** the reply, one short structured call on the speaker's side of the prompt:
  `{perceived, attention, warmth, trust, doubt, goal, intent}`, with every field capped short.
- Its output goes into the reply's prompt as a private block ("Inside Mira right now: …"), so the
  graph shows a cause and not a guess made afterwards. It is stored in `context_log.trace`.
- **Cost:** a second call before the first token. On the local 8 GB setup that is the same loaded
  model, so no extra VRAM, but it adds latency to every reply. Measure it on qwen3.5-9b before
  building the UI for it (the run protocol in `docs/images/rules-and-gotchas.md` applies to any
  GPU run). Expected: ~1–2 s at 150 output tokens. Gate: under 2 s, or it stays opt-in per story.
- Where appraisal ran, the chart (§4.3) plots its numbers instead of the derived counts.

## 5. UI

### 5.1 The graph (Mind 1)

- `scene/Mind.tsx`: an SVG, four fixed columns (the mockup's 864 × ~480). Nodes are HTML cards
  positioned over the SVG. Each card shows its kind in mono caps, the weight top right, one or two
  lines of text, and a weight bar. Links are cubic curves, gold `#ffd08a` for the path that won and
  blue `#8cc3ff` at 50% for the rest. No new dependency.
- Header: "MIND · LAST REPLY, 7:22 PM" and character tabs (each AI character here, plus the
  narrator) that pick whose last reply to show.
- **Spoke** under the graph: the reply in story type, with its time and tokens.
- Click a node for its detail in a side drawer ("what went in and out"): a recall shows its
  activation parts (the old Memory row's numbers), a feeling its edge and note, heard the full line.
- Footer: "Gold is the path that won. Click any part to see what went in and out of it."; then
  **Memory · 41**, which opens the current Memory panel as a full-height sheet, unchanged; and
  **Another take**, the existing regenerate. The mockup's "Replay this turn" is renamed because
  that is what it does.
- Reduced motion: no link animation. Keyboard: nodes are buttons in column order.

### 5.2 Backstage re-laid (Mind 4)

- Left: Mind (864 of 1392). Right, stacked: **Prompt** (unchanged), **Cast** (unchanged), and
  **Engine · this turn** (Mind 2's timings per job, then the memory reader's state with "Read what is
  waiting now", which is the old Reading panel folded in).
- The deep link `#/story/4/backstage/29` opens the Mind on character 29. "See her memories" (from
  the profile) opens the Memory sheet directly.

## 6. Not in this spec

- Editing a mind (changing a feeling or a goal by hand). The Memory sheet's Write and Pin stay as
  they are.
- A mind for the persona. You are the persona; the engine does not model you.
- Minds for lines before this spec (no trace). They show what `context_log` has, per §4.1.

## 7. Decisions (settled 2026-09-23: all three as recommended)

1. **The Appraise step (§4.4): build it, or keep the graph to what is traced?** It is the only way
   to get Perception, Goals and Intent honestly, and it changes how replies are written (for the
   better, probably: a character who has decided what she wants first writes with more intent).
   But it costs a model call before every reply. Recommendation: build Mind 1–Mind 4 now, then measure Mind 5
   on the real model before deciding.
2. **Backstage opens on the Mind, not Memory?** The design says yes. Memory stays one click away.
   Recommendation: yes.
3. **Derived feelings in the chart (§4.3), labelled as derived, until appraisal exists?**
   Recommendation: yes. The alternative is no chart until Mind 5.

## 8. Tasks (show first: Mind 1 is the picture)

1. **`mind.py` + `GET /messages/{id}/mind`** from existing rows, with the tests in §4.1. Verify:
   `pytest`, then the demo's last reply returns heard, 2–3 recalls, a belief and spoke.
2. **`Mind.tsx`** in the current Backstage, beside Memory, not replacing it yet. Verify: a
   screenshot against `Scene-Backstage.html`, shown to the user before step 3.
3. **Trace** (the next migration, `select_speaker` reasons, the cue, timings) and the Attention and Cue
   nodes. Verify: tests, and a reply on the fake model shows "Answered because…".
4. **Feelings chart** (§4.3). Verify: the demo's chart has a mark at the six-year skip.
5. **Re-lay Backstage** (§5.2): the Memory sheet, the Engine panel. Verify: the old Backstage checks
   (pin, write a memory, merge, read now) still pass through the new layout.
6. **Measure Appraise** on qwen3.5-9b (one scripted turn, time before first token, with and
   without) and report. Then build Mind 5 only on a yes.
