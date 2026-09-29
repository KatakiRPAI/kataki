# Unified character-mind architecture for Kataki: one state model, one per-turn pipeline, one background job, three tiers

Scope: a synthesis of the nine phase-2 aspect notes (10-18) and the phase-1 notes (01-04), checked against the engine as it is on 2026-09-29 (`engine/src/kataki/`, schema v9) and the M0/M1 and Mind-graph specs. Nothing here comes from new web research; every "Cited Finding" points at a local note, spec or source file (which in turn carries the external citation). Everything under "Inferences" is design, and every number there is an estimate (est.) unless it quotes a source. Latency assumptions used throughout: an 8-9B Q4_K_M model on the RTX 5060 Laptop 8 GB generates about 40-70 tok/s and prefills about 1-3k tok/s; a 3-4B CPU model generates about 10-20 tok/s; a small cloud model answers in about 0.3-1 s plus 50-150 tok/s. These are the notes' own estimates, not measurements on this machine.

Words used below: **reply call** (the one streamed `rp` generation that exists today); **side call** (at most one short, schema-constrained `utility` call per turn, the only new per-turn call); **gate** (a pure function that decides whether the side call runs before or after the reply); **mind block** (the one consolidated state paragraph in the prompt tail); **Between job** (the one background job per tracked character per time skip).

---

## 1. What is the single shared state model, and which parts already exist in the engine?

### Takeaway
All nine aspect designs fit in one schema: five existing stores reused unchanged (memories and knowledge hold beliefs, claims and who-knows-what; edges hold qualitative relationship labels; flags hold world state; messages.gen holds the per-turn trace and thought; extraction_runs keeps undo for memory-read rows), one profile JSON inside `lib_items.data` (no migration), seven small new tables (`mind_states`, `opinions`, `seeds`, `secrets`, `goals`, `recollections`, `reflections`) and three new `memories` columns. Every new row is branch-safe because it is anchored either to an extraction run or to the message it follows, and it is live only when that message is on the active path.

### Cited Findings
- The engine already has, at schema v9: `providers`, `model_roles` (roles `rp`, `narrator`, `utility`, `reasoning`, `embed`, `image`, `music`), `settings`, `lib_items` (with a free `data` JSON), `stories` (with `overrides` JSON), `messages` (with `gen` JSON, `audience`, `expression`), `scenes` (with an unused `mood` seam), `presence`, `entities` (`description`, `private`, `looks`, `examples`), `aliases`, `tags`/`taggings`, `flags`, `edges`, `memories`, `memory_entities`, `memories_fts`, `knowledge`, `accesses`, `embeddings`, `summaries`, `extraction_runs`, `context_log`, `books`, `chapters`, `story_links`. — [schema.sql baseline in the M0/M1 spec](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md); [db.py migrations 2-9](file:///D:/Kataki/engine/src/kataki/db.py)
- "Nothing is mutated or deleted": every derived row carries `run_id`, a row is live if its run is `ok` and the run's `to_message_id` is on the active path, and flags/edges/knowledge/presence are append-only logs whose current value is the latest live row at or before now. — [M0/M1 spec, Memory engine](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- `knowledge(knower, memory, source ∈ witnessed|told|overheard|rumor|inferred|innate, told_by, learned_story_time, fidelity, belief)` with the current value = the latest live row; claims are `memories.kind='claim'` with `asserted_by`, `is_true`, `contradicts_id`, and hearer belief is set to 0.1 / 0.5 / 0.9 for challenged / doubted / accepted. — [M0/M1 spec](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md); [extract.py `BELIEF`](file:///D:/Kataki/engine/src/kataki/extract.py)
- `edges` hold free-text relations (`rel`, `note`) written by extraction; a character card's `data.relationships` seeds them at story creation as "friend of", "fond of", "wary of", "rival of", "family of". — [library.py `RELATIONSHIP`, `create_story`](file:///D:/Kataki/engine/src/kataki/library.py); [models.py `EdgeItem`](file:///D:/Kataki/engine/src/kataki/models.py)
- Every non-private flag of everyone present is rendered into the `[State]` block that every speaker sees; private flags only to their owner. — [context.py `_state`](file:///D:/Kataki/engine/src/kataki/context.py)
- The per-turn trace (`why`, recall `cue`, timings) lives in `messages.gen.trace` rather than a new column, and reasoning text in `messages.gen.reasoning`, never in prompt history. — [Mind-graph spec §4.2, §0](file:///D:/Kataki/docs/specs/2026-09-23-mind-graph.md); [turns.py `_generate`](file:///D:/Kataki/engine/src/kataki/turns.py)
- `extraction_runs.trigger` is a comment-only enum (`cadence|scene|skip|evict|manual`), but runs are `UNIQUE(story_id, from_message_id, to_message_id)` and `pending()` treats any live run as having read its lines. — [M0/M1 spec schema](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md); [extract.py `pending`, `plan`](file:///D:/Kataki/engine/src/kataki/extract.py)
- `accesses.kind` has `CHECK(kind IN('recall','retold'))` and the primary key `(knower, memory, scene, kind)` is the one-reinforcement-per-scene cap. — [M0/M1 spec schema](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- The aspect notes each proposed their own store: note 11 an `AffectState` with mood, emotions (max 3), worries (max 2), regLoad, felt and displayed ([11 §9B](11_emotion_mood_anxiety.md)); note 12 a three-layer personality schema with trait means and spreads, per-scene sampled state, grievances and positions ([12 §8](12_personality_stance.md)); note 13 `HonestyProfile`, `Secret`, `Claim`, `Belief`, `Relation`, `Suspicion`, `Event` ([13 §7.1](13_deception_politeness.md)); note 14 `recollections`, `suppressions`, `narratives` and `memories.valence/alts/core_locked` ([14 §7.2](14_memory_forgetting.md)); note 15 a `slips` table ([15 §7A](15_mistakes_conversation_realism.md)); note 16 directed edges with numeric tracks, an opinion ledger and a fact-holder table ([16 §9.1](16_theory_of_mind_relationships.md)); note 17 needs and mood as `flags` rows plus `goals`, `rings`, `news`, `interest` ([17 §8](17_needs_goals_offscreen_life.md)); note 10 a thought record and thought-seeds ([10 §7](10_inner_thought_subconscious.md)).
- LLMs do not separate Big Five factors cleanly when given as scores (four of five facets collapse, r >= .90), so numbers belong in the app and the prompt should get behaviour sentences with intensity words. — [12 §1](12_personality_stance.md)
- ALMA derives a default PAD mood from personality and layers emotion (short), mood (medium) and personality (long). — [11 §1](11_emotion_mood_anxiety.md)

### Inferences

**Four rules the unified schema follows.**
1. Reuse before adding. Beliefs, claims, suspicion and who-knows-what are already `memories` + `knowledge`; qualitative relations are `edges`; world state is `flags`; the per-turn thought and decisions are `messages.gen`. None of the notes' parallel stores for these is created.
2. Numbers that change every turn go in one JSON snapshot per character (`mind_states`); objects the user will inspect, lock or delete in Backstage get a small table with a lifecycle.
3. Derive rather than store whenever the value is a pure function of stored rows: relationship stage, trust cap, loyalty, alliances, the user's usual gap, secret status, atmosphere, suspicion (= 1 − belief on the claim), lie-discovered, favouritism.
4. Every new row has an **anchor**: `run_id` (written by an extraction run, existing liveness) or `message_id` (written by a turn or a skip; live iff that message is on the active path; cascades on delete). Both NULL = written by the user in Backstage, always live. A swipe or branch therefore swaps the whole mind state with no extra code path, exactly as memory already behaves. (Reusing `extraction_runs` with new trigger values was considered and rejected: the `UNIQUE(story, from, to)` constraint would collide with one-line extraction windows, and `pending()` would treat mind runs as having read the transcript.)

**Where every concept lives.**

| Concept (notes that proposed it) | Lives in | Status |
|---|---|---|
| Temperament and traits: axes with mean and spread, attachment, reactivity, inertia, regulation style, anxiety, coping, susceptibility, social traits, values, hard lines, flaws, want/need/fear, chronotype, stance toward user (11, 12, 13, 16, 17) | `lib_items.data.mind` JSON on the library character; story-scoped growth lives in `reflections` rows as capped trait deltas | JSON: no migration. New keys only |
| Affect: mood PAD, emotion stack (max 3), felt vs shown, tell, regulation load (10, 11, 18) | `mind_states.state` | **New table** |
| Needs: energy (closed form from clock and chronotype), autonomy, competence, relatedness, stimulation (12, 17) | `mind_states.state.needs` | New (same table) |
| Per-scene trait sample (Whole Trait Theory) (12) | `mind_states.state.axes_now`, resampled at scene start | New (same table) |
| Belief about the user, one second-order slot (16) | `mind_states.state.user_view` | New (same table) |
| Attention share, jealousy, counters (concessions this scene, stuck turns, boredom, turns since agenda/slip) (12, 15, 16, 17) | `mind_states.state` | New (same table) |
| Relationship numbers: closeness, trust, respect, attraction, dominance, familiarity, disclosure depth each way, as sourced ledger entries with decay rules; grudges; forgiveness (12, 13, 16) | `opinions` (one row per event-caused modifier) | **New table** |
| Relationship labels: "sister of", "owes", "works for" (spec, 16) | `edges` | Exists, unchanged |
| Beliefs and who-knows-what; told-by chains; gossip provenance (13, 16) | `knowledge` rows (`source`, `told_by`, `belief`) | Exists, unchanged |
| Suspicion of a claim (13) | `knowledge.belief` on the claim memory, lowered by appending a row | Exists (new writer) |
| Claims ledger (13) | `memories.kind='claim'` + `asserted_by` + `contradicts_id`; the speech-act move chosen at turn time is joined through `memories.message_id` to `messages.gen.mind.move` | Exists; move is a new gen field |
| Secrets: owner, conceal-from, stakes, motive, cover story, sincere belief, tells, promises (13, 16) | `secrets` | **New table** |
| Worries, rumination, relational absence worry, plans, unfinished business, intrusive thoughts, ideas, news to tell, pending self-corrections, positions taken (10, 11, 12, 15, 16, 17) | `seeds` ("what is on this character's mind") | **New table** |
| Goals and agenda (17) | `goals` (append-only versions per `key`); agenda is a query over active goals | **New table** |
| Recollection variants: alt drift, retelling, intrusion, source swap, recount; memory slips (14, 15) | `recollections` | **New table** |
| Consolidated self/relationship/habit lines and growth rings (12, 14, 16, 17) | `reflections` (one table, `kind` covers both) | **New table** |
| Memory valence, peripheral alternatives, core lock (14) | `memories.valence`, `memories.alts`, `memories.core_locked` | **New columns** |
| Inline thought, want, gate reasons, move, directives used, seeds surfaced, side-call raw JSON (10, 13, mind-graph) | `messages.gen.mind` | JSON: no migration |
| Retrieval-induced forgetting (14) | `suppressions` | Deferred (Dreamlike mode only) |
| Sleep replay access (14) | would need `accesses.kind='sleep'`, i.e. a table rebuild because of the CHECK | Deferred (low value per cost) |
| Typos and display roughening (15) | `messages.gen.mind.display` (clean canonical text stays in `messages.text`) | JSON: no migration |

**Profile JSON (`lib_items.data.mind`), deduplicated across notes.** Fields that several notes named differently are merged: `honesty` (12 axis, 13 `HonestyProfile.honesty`, 16 `traits.honesty`); `candor` (12) = `bluntness` (13); `attachment` (11, 12, 16) is one pair with optional per-relationship override; `warmth` (12) absorbs `kindness` (13); `forgiveness` (16) replaces `grudge_half_life` in scenes (12); `perceptiveness` (16) absorbs `attentiveness` (13); `volatility` (12) = `reactivity` (11). Dropped for v1 as low-value duplicates: `conscience` (derive guilt from honesty × closeness), `selfDeceive` as a trait (kept per secret as `sincere`), `lieStyle`.

```jsonc
"mind": {
  "axes": {                       // [mean 0-100, spread 0-30]; the app samples, the prompt gets words
    "dominance": [55, 10], "warmth": [60, 15], "candor": [50, 10],
    "honesty": [60, 5], "yielding": [40, 10], "volatility": [40, 15]
  },
  "attachment": {"anxiety": 0.2, "avoidance": 0.2},
  "anxiety": 0.2, "coping": 0.6,              // worry gain; can-cope for control appraisals
  "regulation": {"style": "suppress", "capacity": 0.6},   // express | suppress | reappraise | avoid
  "inertia_h": 6, "susceptibility": 0.4,      // mood half-life (story hours); contagion
  "social": {"forgiveness": 0.5, "possessiveness": 0.3, "gossip": 0.3,
             "perceptiveness": 0.5, "trust_propensity": 0.5, "talkativeness": 0.5},
  "values": ["loyalty", "freedom", "honesty"], "hard_lines": [], "flaws": [],
  "want": "", "need": "", "fear": "",
  "chronotype_h": 0, "sloppiness": 0.3,       // circadian shift; slip rate multiplier
  "stance": {"preset": "custom", "intensity": 1, "responsive": true},
  "baseline": null                             // PAD override; else derived from axes (est. table)
}
```
Users see about eight sliders and presets; the rest default or are filled once at character creation by one `utility` call that reads the card prose (est. ~1.5k in / 300 out, once per character).

**`mind_states.state` JSON (one row per acting character per turn that changed it, plus one per skip).**
```jsonc
{"mood": {"v": -0.2, "a": 0.3, "d": -0.1},
 "emotions": [{"label": "hurt", "i": 0.6, "target": 12, "cause": "he broke his promise", "t": 5230}],
 "reg_load": 0.3, "shown": {"label": "calm", "i": 0.3, "tell": "short answers"},
 "needs": {"autonomy": 0.6, "competence": 0.7, "relatedness": 0.4, "stimulation": 0.5, "awake_since": 4380},
 "axes_now": {"dominance": 62, "warmth": 48, "candor": 55, "yielding": 35},
 "user_view": {"label": "anxious", "conf": 0.5, "second_order": null},
 "attention": {"31": 0.4, "29": 0.6}, "jealousy": {"31": 0.2},
 "stage": {"12": "exploratory"},             // remembered only for hysteresis
 "counters": {"conceded": 0, "stuck": 2, "boredom": 1, "since_agenda": 4, "since_slip": 7}}
```

**DDL sketch for the new tables** (`ANCHOR` = `message_id INTEGER REFERENCES messages ON DELETE CASCADE, run_id INTEGER REFERENCES extraction_runs(id) ON DELETE CASCADE`; current value = latest live row at or before now, the same rule flags use):
```sql
CREATE TABLE mind_states(id INTEGER PRIMARY KEY, entity_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  story_time INTEGER NOT NULL, state TEXT NOT NULL, ANCHOR);
CREATE TABLE opinions(id INTEGER PRIMARY KEY, story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  src_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE, dst_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  dim TEXT NOT NULL CHECK(dim IN('closeness','trust','respect','attraction','dominance','familiarity','disclosed_in','disclosed_out')),
  value REAL NOT NULL, kind TEXT NOT NULL CHECK(kind IN('decay','sticky','permanent')), half_life_min INTEGER,
  event TEXT, cause TEXT, resolves_id INTEGER REFERENCES opinions, witnesses TEXT, story_time INTEGER NOT NULL, ANCHOR);
CREATE TABLE seeds(id INTEGER PRIMARY KEY, story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  entity_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN('worry','rumination','plan','unfinished','intrusive','idea','news','correction','position')),
  text TEXT NOT NULL, about_id INTEGER REFERENCES entities, memory_id INTEGER REFERENCES memories,
  weight REAL NOT NULL, half_life_min INTEGER, payload TEXT,
  closes_id INTEGER REFERENCES seeds, close_kind TEXT CHECK(close_kind IN('resolved','told','eased','dropped')),
  story_time INTEGER NOT NULL, ANCHOR);
CREATE TABLE secrets(id INTEGER PRIMARY KEY, story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  owner_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE, memory_id INTEGER REFERENCES memories,
  text TEXT NOT NULL, keys TEXT NOT NULL DEFAULT '', conceal_from TEXT NOT NULL DEFAULT '"all"',
  stakes REAL NOT NULL DEFAULT 0.5,
  motive TEXT CHECK(motive IN('protect_self','protect_other','gain','avoid_conflict','kindness')),
  cover TEXT, sincere INTEGER NOT NULL DEFAULT 0, tells TEXT, promises TEXT,
  supersedes_id INTEGER REFERENCES secrets, story_time INTEGER NOT NULL, ANCHOR);
CREATE TABLE goals(id INTEGER PRIMARY KEY, story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  entity_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE, key TEXT NOT NULL,
  tier TEXT NOT NULL CHECK(tier IN('ambition','project','today')), text TEXT NOT NULL, cue TEXT NOT NULL DEFAULT '',
  priority REAL NOT NULL, progress REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK(status IN('active','dormant','done','failed','dropped')),
  tactic TEXT, deflections INTEGER NOT NULL DEFAULT 0, story_time INTEGER NOT NULL, ANCHOR);
CREATE TABLE recollections(id INTEGER PRIMARY KEY, knower_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  memory_id INTEGER NOT NULL REFERENCES memories ON DELETE CASCADE, parent_id INTEGER REFERENCES recollections,
  basis TEXT NOT NULL CHECK(basis IN('alt','retelling','intrusion','source_swap','recount')),
  text TEXT NOT NULL, story_time INTEGER NOT NULL, scene_id INTEGER, ANCHOR);
CREATE TABLE reflections(id INTEGER PRIMARY KEY, story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  knower_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN('self','relationship','habit','stance','skill','scar','belief')),
  subject_id INTEGER REFERENCES entities, text TEXT NOT NULL, sources TEXT NOT NULL, cue TEXT,
  strength REAL NOT NULL DEFAULT 0.5,
  status TEXT NOT NULL CHECK(status IN('seed','ring','fading','past','rejected','locked')),
  trait_delta TEXT, supersedes_id INTEGER REFERENCES reflections, story_time INTEGER NOT NULL, ANCHOR);
ALTER TABLE memories ADD COLUMN valence REAL;
ALTER TABLE memories ADD COLUMN alts TEXT;
ALTER TABLE memories ADD COLUMN core_locked INTEGER NOT NULL DEFAULT 0;
```
Each table arrives with the slice that first needs it (section 7), one migration per slice.

**Closed enums shared by the side call, extraction, the Between job and the UI** (small models do best on closed sets, and the extraction schema already closes every reference to roster handles — [models.py `extraction_schema`](file:///D:/Kataki/engine/src/kataki/models.py)):
- `FEEL` (16): calm, content, glad, fond, amused, excited, relieved, surprised, anxious, afraid, sad, hurt, annoyed, angry, ashamed, bored. Each maps in code to a PAD anchor and to one of the five existing sprite faces (neutral, smiling, wary, surprised, doubtful — [images.py `EXPRESSIONS`](file:///D:/Kataki/engine/src/kataki/images.py)). "Jealous" and "doubtful" are derived by code (attention share, belief), not asked.
- `EVENT` (24, from [16 §4](16_theory_of_mind_relationships.md)): kindness, support_given, support_ignored, vulnerable_disclosure, disclosure_reciprocated, disclosure_unreciprocated, shared_joy, compliment, teasing_ok, teasing_hurt, insult, dismissal, promise_kept, promise_broken, secret_kept, secret_betrayed, lie_discovered, boundary_crossed, apology_sincere, apology_hollow, amends_made, favouritism_shown, neglect_gap, help_refused. Five are detected by code and never asked of a model: `neglect_gap` (gap vs usual gap), `favouritism_shown` (attention share), `lie_discovered` (suspicion threshold), `disclosure_unreciprocated` (disclosure counters), `secret_betrayed` (a knowledge row appears for someone in `conceal_from`). The model chooses from the remaining 19.
- `MOVE` (11, from [13 §7.1](13_deception_politeness.md)): truth, soften, hedge, hint, omit, evade, deflect, exaggerate, white_lie, self_lie, confess; reactions when a lie is challenged: double_down, blame, attack, forgive.
- `SEED` kinds (9): worry, rumination, plan, unfinished, intrusive, idea, news, correction, position.
- `AGENDA` outcome (5): not_tried, tried, deflected, progressed, done.
- `GATE` codes (9, section 2): secret_topical, probe, critical, affect_jump, stage_edge, first_meeting, stuck, invalid, peek_open.

**Engine gotchas this schema creates.**
- `context._state` would leak any mind value stored as a flag into everyone's `[State]` block; this is why needs are not flags (a change from [17 §8](17_needs_goals_offscreen_life.md)).
- A helper `db.live_messages(conn, story_id, leaf)` (the active path's ids, which `chat.active_path` already computes) plus `db.live_filter` must be combined into one `anchor_filter`; every new query uses it.
- `mind.py`'s rule "the graph shows only what the engine really did" is preserved because every node the graph gains (Feeling, Perception, Goals, Intent, Honest?) is read from rows written before the reply was generated ([Mind-graph spec §1](file:///D:/Kataki/docs/specs/2026-09-23-mind-graph.md)).

### Gaps
- No note or test establishes how many profile fields a 7-14B model's behaviour actually tracks; the eight-slider surface is a judgement.
- Whether a per-turn JSON snapshot table stays small enough over a 5k-turn story (est. a few MB) was not measured.
- The PAD-from-axes table is unsourced; ALMA's formula needs Big Five inputs that Kataki's axes do not map to one-to-one.

---

## 2. What is the per-turn pipeline, which steps are code, which share one fused call, and which are gated?

### Takeaway
Thirteen steps. Eleven are pure code. The existing reply call gains an optional inline two-line thought (about 30-50 hidden output tokens, 0 extra calls). There is at most one side call per turn, a closed-enum JSON that fuses appraisal, relationship events, the user-mood guess, the sprite face, the claim's speech-act label and the agenda outcome; it normally runs after the reply is on screen (lagged, preemptible) and moves before the reply only when the code gate fires (budgeted to about 15% of turns). Because the side call absorbs the face call that already runs after every reply for characters with sprites, the default tier adds zero net calls for those characters. Every extra call the aspect notes asked for is either folded into this one side call, moved to the Between job, replaced by code, or reserved for PREMIUM.

### Cited Findings
- Today a turn is: optional read-before-skip extraction (only after a skip of a day or more), recall (0 calls), prompt build, one streamed reply on `rp`, then a post-reply `utility` call that picks the sprite face, but only for characters that have a sprite pack. — [turns.py `_read_past_before_skip`, `_generate`, `_expression`](file:///D:/Kataki/engine/src/kataki/turns.py)
- Extraction is not per turn: about 10 waiting lines (five exchanges) or a scene break, skip or eviction trigger one schema-constrained `utility` call (scene close uses the `reasoning` role); the worker starts 3 s after a reply and steps aside when a turn starts on the same endpoint. Budget about 1.2 utility calls per 5 turns. — [extract.py `CADENCE`, `plan`, `due`, `Worker`](file:///D:/Kataki/engine/src/kataki/extract.py); [M0/M1 spec](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- The stream splitter routes any `<think>…</think>` span in the content (configurable tags) to the `thought` SSE event for every model, not only reasoning kinds; thoughts never enter history or the cached prefix. — [llm.py `chat_stream`, `ThinkSplitter`](file:///D:/Kataki/engine/src/kataki/llm.py); [M0/M1 spec, Model roles](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- Speaker choice is deterministic today: UI pick, else a character named in the pending line, else the last to speak among those who heard, else the quietest; the reason is logged. — [turns.py `speaker_why`](file:///D:/Kataki/engine/src/kataki/turns.py)
- The Mind-graph spec's planned "Appraise" step is one short structured call before the reply producing `{perceived, attention, warmth, trust, doubt, goal, intent}`; expected ~1-2 s at 150 output tokens; gate: under 2 s, or it stays opt-in per story. — [Mind-graph spec §4.4, §7.1](file:///D:/Kataki/docs/specs/2026-09-23-mind-graph.md)
- Extra calls requested by the aspect notes: inline thought (0 calls), a gated slow pre-reply pass, and an async afterthought ([10 §7, O1/O3/O7](10_inner_thought_subconscious.md)); a lagged or pre-reply appraisal call as premium, zero calls by default ([11 §9F-G](11_emotion_mood_anxiety.md)); a director/appraisal call and a critic-regenerate pass as premium ([12 §8](12_personality_stance.md)); a planner call, a second-order leak check and a post-turn extraction call ([13 §7.2-7.3](13_deception_politeness.md)); a recount call per pressed hazy memory as premium ([14 §7.5 D6](14_memory_forgetting.md)); correction-wording, Inner-Thoughts-lite rating and "who next" calls as premium ([15 §7](15_mistakes_conversation_realism.md)); events piggybacked on "the hidden thought", with the rule of thumb "reply call plus at most one hidden classification call" ([16 §8, §9.3](16_theory_of_mind_relationships.md)); an optional hidden thought in premium ([17 §8](17_needs_goals_offscreen_life.md)); a per-line cue (mood, intensity, tags, pause) from the reply or a follow-up small call ([18 §8](18_voice_embodiment.md)).
- A seven-to-eight-call CPM appraisal pipeline beat a zero-shot single call by only +0.044 on a 5-point scale; the two-call Chain-of-Emotion pattern reached 83% vs 74% (memory only) on an emotion-understanding test. — [11 §1](11_emotion_mood_anxiety.md)
- LLMs appraise relevance and congruence well but control and certainty poorly, and recognise positive emotions poorly; self-generated reasoning text hurt appraisal. — [11 §1, CAREBench](11_emotion_mood_anxiety.md)
- Talker-Reasoner: the fast talker answers from the latest stored beliefs while the slow reasoner updates them in the background, accepting a delayed view; it waits only when the situation demands. — [10 §3](10_inner_thought_subconscious.md)
- Reasoning/CoT modes lowered roleplay scores and slightly lowered villain play. — [10 §3](10_inner_thought_subconscious.md); [04 §8](04_persona_fidelity.md)
- Models cannot reliably notice their own mistakes, so errors should be planted by the engine, not requested. — [15 §1-2](15_mistakes_conversation_realism.md)
- Small models are weak at second- and higher-order belief reasoning; code-side perception filtering (SimToM stage 1 done in code) removes the need for the model to track who heard what. — [16 §2, §8](16_theory_of_mind_relationships.md); [13 §6](13_deception_politeness.md)
- Agreeable personas raise sycophancy in 0.6-20B models (r up to 0.87) and emotional pressure is the strongest trigger of caving. — [12 §5](12_personality_stance.md)

### Inferences

**The pipeline.** "Code" means deterministic Python with no model call; module names are where the step lives.

| # | Step | Who | LLM calls | Engine home | Merges from |
|---|---|---|---|---|---|
| 0 | **Intercept**: stop word ends a stance/scene; out-of-character sincerity check ("are you real", `((ooc:))`) answers outside the fiction; hard lines checked before generation | code | 0 | `turns.turn` | 12 §6, 13 §5 |
| 1 | **Perceive**: line + audience → hearers (exists); witnesses for claims and beliefs (exists); attention-share update (jealousy) | code | 0 | `chat.heard_by` (exists), new `inner.py` | 13 §6, 16 §5, §9.2 |
| 2 | **Tick**: closed-form decay to `now` of emotions (half-life ~20-30 story-min), mood toward baseline (inertia, default 6 story-h), needs (circadian energy, SDT drift), ledger entries (read-time), jealousy (1-2 days), seed weights | code | 0 | `inner.py` | 11 §9C, 16 §9.3, 17 §1 |
| 3 | **Sense the line**: user-affect cue from the already-loaded model2vec embedder against ~16 labelled centroids (FEEL); addressed names (exists); question detection; topical matches against the speaker's secrets, goals, worries, grudges, positions (keywords + embedding) | code (CPU, ~ms) | 0 | `inner.py`, `embed.py` | 11 §7, 13 §7.2 step 1, 17 §2 |
| 4 | **Choose speaker**: pick > named (unchanged); otherwise a score replaces "last"/"quietest" (below) | code | 0 | `turns.speaker_why` | 10 §5, 15 §7C, 16 §6 |
| 5 | **Gate**: compute trigger codes; decide whether the side call runs *before* the reply this turn | code | 0 | `inner.gate` | 10 §3, §7 |
| 6 | **Recall**: existing retrieval plus the mood-congruence term, partial tip-of-the-tongue cues, and recollection variants for HAZY memories | code | 0 | `retrieve.py` | 14 §7.4-7.5 |
| 7 | **Decide**: (a) speech-act sampler when a secret or face-threat is live: move, motive, cover story, last 3 claims on the topic; (b) politeness style from candor, closeness, power; (c) yield rule and concession budget; (d) regulation felt → shown + tell; (e) slip plan (content slips only from HAZY memories via `alts`; pending corrections become `correction` seeds); (f) agenda pick (≤1 item, only at an opening); (g) initiative and length class; (h) 0-1 seed sampled as a faint unspoken pull | code | 0 | `inner.py` | 10 O10, 11 §4, 12 §5, 13 §3.3-3.6, 15 §7A-C, 17 §2 |
| 8 | **Slow pass (gated)**: when step 5 escalates, the side call runs now, with the pre-reply schema (below); its `stance` may only choose among the sampler's top two moves plus "truth", never override a hard line | 1 (the side call, moved) | ≤1 | `turns.py` + `inner.py` | 10 O3, 11 opt. 4, 12 director, 13 C, Mind 5 |
| 9 | **Render the mind block** (section 4) | code | 0 | `context.build` | all |
| 10 | **Reply**: one streamed `rp` call; in STANDARD it opens with a two-line `<think>` header (thought ≤25 words, want ≤10 words) that the existing splitter routes to the `thought` event and Peek | 1 (exists) | 0 extra | `turns._generate`, `llm.py` | 10 O1, 13 §7.2 step 4, 17 premium |
| 11 | **Check**: leak filter (secret keys vs audience in `conceal_from`); agreement-opener/assistant-ism regex when the state is cold or resistant; thought-echo overlap; opener ledger. On a hit: one resample with a stronger directive (STANDARD, ≤1 per turn) or replace the offending sentence with the cover story | code (+1 reply resample on a hit) | 0 (+1) | `turns.py` | 10 §4, 12 §5-8, 13 E, 16 M |
| 12 | **After (side call, default timing)**: after the reply is on screen, one closed-enum JSON on `utility`; replaces `_expression`; preemptible: cancelled if the user starts the next turn on the same endpoint, and the next side call covers both exchanges | 1 (replaces the face call) | ≤1 | `turns.py` (Worker pattern) | 10 O7, 11 opt. 3, 16 C, 18 cue |
| 13 | **Apply**: appraisal → PAD delta × reactivity; mood push; worry create/ease/resolve with rebound; ledger rows from event table × personality multipliers, per-scene caps and trust asymmetry; suspicion (belief rows); claim move stored; goal attempt counters; stage with hysteresis; write `mind_states` and `gen.mind` | code | 0 | `inner.py` | 11 §9C, 12 §8, 13 §3.5, 16 §9.3 |

Extraction keeps its cadence (about 0.2 calls per turn) and gains only memory-bound fields: `valence`, `alts` (≤2 peripheral), `core_locked`, retelling `deviates`, goal deltas, open questions ([14 §7.3](14_memory_forgetting.md), [17 §8](17_needs_goals_offscreen_life.md)). Per-turn social fields stay out of it so its schema, and its JSON validity, do not balloon.

**The gate** (pure function, unit-testable; thresholds are est. defaults):
- `secret_topical`: a secret's keys or embedding match the pending line or last 2 lines.
- `probe`: a direct question that touches a held-back fact, or the second probe of the same topic in 6 turns.
- `critical`: decision words (confess, refuse, leave, marry, betray, accept, forgive) or a cue of an active goal.
- `affect_jump`: distance between the user-line cue and the speaker's current mood > 0.6 in VA space.
- `stage_edge`: a relationship stage threshold within 3 points.
- `first_meeting`: no opinion rows yet for this pair.
- `stuck`: 6 turns with no state delta above a small epsilon.
- `invalid`: the previous reply failed a check at step 11.
- `peek_open`: the user has the Peek card open for this character.

Escalation happens when a trigger fires *and* the budget allows: STANDARD ≤1 escalation per 3 turns per character and ≤15% of a session's turns; `invalid` triggers a resample, not a slow pass. PREMIUM escalates every turn.

**Inline thought header (STANDARD).** One line in the tail's `[Directive]` (about 35 tokens) asks for:
```text
<think>
Mira thinks: I promised myself I wouldn't ask. Don't look at the ring.
Mira wants: him to drop it
</think>
```
Stance and feeling are not asked: code already decided them (step 7), CAREBench says the model is weakest exactly there, and asking would cost tokens and invite contradiction. The thought is generated before the reply in the same stream, so Peek shows what actually conditioned the reply (faithful by construction, [10 §1](10_inner_thought_subconscious.md)). If the `rp` model is itself a reasoning model with thinking on, the header is skipped; its trace stays in the collapsible block and the Peek thought comes from the side call's optional `thought` field, labelled "afterthought".

**The side call schema, post-reply default (~500-800 prompt tokens, 60-100 output tokens, est.).** Fixed instructions and enum lists come first so the `utility` slot can reuse them; then the speaker's mind block, the user's line, the reply.
```jsonc
{"felt": {"label": FEEL, "intensity": 1|2|3, "about": HANDLE|null, "cause": "<=12 words"},
 "events": [{"target": HANDLE, "type": EVENT_19, "intensity": 1|2|3}],      // max 3
 "user_mood": FEEL|"unclear",
 "face": "neutral"|"smiling"|"wary"|"surprised"|"doubtful",
 "claim": {"move": MOVE, "secret": SECRET_HANDLE}|null,                       // only if a secret was topical
 "agenda": AGENDA|null,                                                        // only if an item was set
 "position": {"text": "<=12 words", "firm": 1|2|3}|null}
```
**Pre-reply variant (gated turns, and every turn in PREMIUM):** drop `face`, `claim` and `agenda` (code derives them afterwards from the shown label, the sampler's move and the reply) and add `want` (≤10 words), `stance` (MOVE restricted to allowed values), `hold_back` (secret handles), `tell` (≤8 words), `thought` (≤25 words). In this variant the inline header is not requested, so a gated turn costs one side call and a normal reply, never both headers.

**Why lagged appraisal loses little.** The reply model sees the user's line verbatim, so the immediate emotional reaction is already in-context; what the persistent state adds is continuity across turns and skips (Sentipolis decay, grudges, worries). That continuity tolerates a one-turn delay, which is the Talker-Reasoner trade. The two places where a delay hurts (a secret under direct pressure, a decision that changes the relationship) are exactly the gate's triggers.

**Where each note's extra call went.**

| Asked for | Note | Destination | Net calls in STANDARD |
|---|---|---|---|
| Inline thought | 10 O1, 13, 17 | reply header | 0 |
| Gated slow structured pass / director / planner / Mind 5 Appraise | 10 O3, 12, 13 C, Mind-graph | side call moved pre-reply on gated turns | 0 (same side call) |
| Async afterthought / lagged appraisal / events / user model / expression cue | 10 O7, 11 opt. 3, 16 C, 18 | side call post-reply | 0 net for sprite characters (replaces face call); +1 otherwise |
| Post-turn claim extraction | 13 §7.2 step 7 | `claim.move` in side call; claim text from existing extraction | 0 |
| Reactions on suspicion thresholds (confess, double down) | 13 §3.5 | sampler draw → directive in the next reply | 0 |
| Correction wording for delayed self-repair | 15 §7A | `correction` seed → next reply's directive ("you realise it was Thursday; correct yourself in passing") | 0 |
| Critic + regenerate | 12 | regex check + one resample in STANDARD; critic call only PREMIUM on flagged turns | 0 (+1 on hits) |
| Second-order leak check (ReCon) / LLM leak verifier | 13 D, 16 M | string + embedding filter; LLM verify only PREMIUM, only on hits | 0 |
| Ensemble thought / Inner-Thoughts-lite / LLM speaker router | 10 O9, 15, 16 K | code speaker score; LLM only PREMIUM in groups of 3+ with no addressee | 0 |
| Recount of a pressed hazy memory | 14 D6 | PREMIUM only; STANDARD uses code partial cues | 0 |
| Scene-end reflection per character | 16 D | Between job, deep mode only | 0 per turn |
| Contradiction NLI | 13 §3.5 | embedding candidates in code; judged inside the next extraction run | 0 |
| Offstage thoughts, verbalising, dream, reflection, rings, reflective mind-change | 10 O8/O11, 11, 14, 15, 17 | Between job (section 3) | 0 per turn |
| Voice-render pass | 18 §6 | later: extra fields in the side call when voice mode is on | 0 |

**Speaker score (groups, only when nobody was picked or named):** `score(c) = 2.0·replying_to + 1.5·urgency + 1.0·salience + 0.8·relevance + 0.5·talkativeness + 0.3·silence_turns − 1.0·spoke_last − 0.5·chain_depth`, sampled by softmax with an RNG seeded on (story, parent message) so a retake keeps the same speaker. `urgency` = this character's own gate triggers; `salience` = largest |opinion| or unresolved grudge toward the last speaker; `relevance` = embedding similarity of the line to the character's goals, seeds and card. New reason codes for the Mind graph: `urgent`, `wants_in`, `balance` (weights est.; [15 §7C](15_mistakes_conversation_realism.md), [16 §6](16_theory_of_mind_relationships.md)).

**Group scenes.** Only the speaker gets the inline thought and the side call; everyone else present gets code-only updates (tick, attention share, displayed-emotion contagion `mood_i += susceptibility_i · closeness_ij · shown_j.i · pad(shown_j.label)` ([11 §5](11_emotion_mood_anxiety.md))). Peek on a silent character renders their state in words, and in STANDARD may lazily generate one cached "what they were thinking" line labelled as such ([10 §5](10_inner_thought_subconscious.md)).

**Fallbacks.** A malformed or cancelled side call never blocks anything: the turn keeps the code-only update (steps 2, 3, 13 with cue-derived appraisal) and marks `gen.mind.after = "skipped"`; the next side call reads the last two exchanges. Validation clamps every delta, so a weaker model cannot swing a relationship ([16 §6](16_theory_of_mind_relationships.md)).

### Gaps
- Whether a hybrid-thinking model served with thinking disabled (the default Qwen3.5-9B setup) will write a literal `<think>` span in content, and whether its chat template interferes, is untested; the fallback is a per-role `think_tags` pair such as `<thought>…</thought>`, which `ThinkSplitter` already supports but only one pair per endpoint.
- Closed-enum event accuracy on 7-9B models has no measurement anywhere in the notes ([16 §9 Gaps](16_theory_of_mind_relationships.md)).
- The side call and extraction share the `utility` slot on one llama-server; alternating templates will evict each other's cached prefix. With `-np 2` the context is split across slots; a third slot's cost was not checked against the installed build.
- Gate thresholds, the 15% budget and the speaker weights are unvalidated design values.

---

## 3. What is the background pipeline, merged into one job per character per skip?

### Takeaway
One **Between** job per tracked character per time skip (or scene close after a long gap, or app return in an opt-in living-world mode): a deterministic code tick with zero calls, followed by one schema-constrained `utility` call that verbalises what the tick decided and adds 1-3 thought-seeds; on big skips the same call grows a "deep" section (reflection, growth rings, relationship and self lines) instead of adding a second call. It runs lazily at the skip, preemptibly in idle time otherwise, never as a daemon, and never loads a second model on 8 GB. LITE runs only the code tick.

### Cited Findings
- Note 10 proposes one batched offstage call at time skip or scene close producing 1-3 seeds per character (worry, plan, unfinished, intrusive, idea) with salience and per-scene decay, with consolidation folded into the same cycle. — [10 §2, §7 O8/O11](10_inner_thought_subconscious.md)
- Note 17's tick: 0-6 beats depending on skip length, seeded RNG per (story, character, beat), RimWorld-style pacing, weighted event tables, clamped deltas written to memories/flags/goals/news, then one utility call returning `{diary, worth_telling, preoccupation, private_thought}` (~1.0-1.5k in, ~150-250 out, est. 3-6 s local per character); lazy at skip or return; idle precompute only when chat idle ≥2 min, on AC, unlocked, no image/music job; no second resident model on 8 GB. — [17 §3, §7, §8](17_needs_goals_offscreen_life.md)
- Note 14's dream job: triggered by skips of about 7 story-days, ≥40 new memories for a knower, or an arc's scene close; working region capped at about 30 items / 3k tokens with closed-set handles; mechanical anti-drift gate (every statement cites a source handle, no new proper nouns or numbers, no new entities, hard length caps, append-only, discard with a visible warning); regenerate from raw sources, never from a previous consolidation. — [14 §6](14_memory_forgetting.md)
- Note 16 runs gossip transfer, ledger decay and a scene-end reflection (≤200 tokens) at skips; note 17 adds evidence-gated growth rings (≥3 memories from ≥2 scenes) with capped trait drift; note 12 caps trait change per window and requires the same direction in 2-3 independent scenes. — [16 §6, §9.3](16_theory_of_mind_relationships.md); [17 §6](17_needs_goals_offscreen_life.md); [12 §7](12_personality_stance.md)
- Note 11 wants worry habituation over 1-3 days, reassurance rebound, and relational worry raised by silence to an anxiously attached character; note 16 computes absence lazily at reopen from `gap / expected_gap`. — [11 §3, §9C](11_emotion_mood_anxiety.md); [16 §7](16_theory_of_mind_relationships.md)
- Sleep-time compute pays off when later needs are predictable from context; roleplay user lines are not, so the offline work should pre-compute state, not replies. — [10 §2](10_inner_thought_subconscious.md); [14 §6](14_memory_forgetting.md)
- The engine already reads the transcript into memory before the first reply after a skip of a day or more (one memory-reader call), and scene summaries leaked secrets because the reader is omniscient and are therefore never sent to a character. — [M0/M1 spec, real-model findings](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md); [turns.py `_read_past_before_skip`](file:///D:/Kataki/engine/src/kataki/turns.py)
- The spec's YAGNI list excludes "reflection / dream cycles" and "summary roll-ups". — [M0/M1 spec, Deliberately NOT building](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- Hugging Face Inference Providers bills pay-as-you-go at provider rates; free accounts get $0.10 of monthly credits and PRO $2.00 (subject to change). — [17 §7](17_needs_goals_offscreen_life.md)

### Inferences

**Triggers.** A skip ≥2 story-hours (from `clock.parse_skip` or the pass-time control), a scene break after ≥2 story-hours, app return in living-world mode (real time mapped to story time, capped at about 3 story-days per return, [17 §3](17_needs_goals_offscreen_life.md)), and idle precompute for a skip already marked but not yet processed. The job is anchored on the message that carries the skip (`message_id`), so undoing the skip chip or switching branch discards the whole job's output.

**Phase B0, code tick (0 calls, all tiers).** For each tracked character (full fidelity for up to 3-4 recently on-screen characters; the rest get closed-form decay only):
1. Closed-form decay of affect, needs and ledger to the new time; circadian energy from `chronotype_h`.
2. Worries: habituation and rebound; resolution when a waited-for outcome is now known.
3. Absence: `ratio = gap / expected_gap` per edge with the user; anxious attachment creates a relational `worry` seed, avoidant cools closeness, secure mostly nothing ([16 §7](16_theory_of_mind_relationships.md)); `neglect_gap` opinion rows per the realism dial.
4. Gossip: for each pair with contact during the skip, probabilistic belief transfer (`knowledge` row, `source='told'`, `told_by`), probability from closeness × trust × gossip × salience, ×0.2 for secrets ([16 §6](16_theory_of_mind_relationships.md)).
5. Offstage beats: seeded event tables (card `routine`, generated `event_seeds`, needs deficits, active goals, storyteller pacing) → covert `memories` tagged `offscreen`, flags, goal progress, mood nudges, `news` seeds with tellability ([17 §3](17_needs_goals_offscreen_life.md)). Scar-class and relationship-changing events default to "ask me first" in an event preview.
6. Night crossed: optional sleep replay (deferred, see section 1).

**Phase B1, one call per tracked character (STANDARD; ~1.2-1.5k in, 150-250 out, est. 3-6 s local on the 8B model).** Input is built only from that character's own memories and state, never from scene summaries (the leak lesson). Output schema:
```jsonc
{"diary": "2-3 sentences, first person",                 // stored as a covert memory
 "worth_telling": ["<=20 words", "..."],                 // 0-2 → news seeds (tellability from B0)
 "seeds": [{"kind": "worry|rumination|plan|unfinished|intrusive|idea", "text": "<=20 words", "weight": 1|2|3}],  // 1-3
 "preoccupation": "<=15 words"}
```
**Phase B2, "deep" section of the same call** (added to the schema only when a deep trigger holds: skip ≥7 story-days, ≥40 new memories for this knower since the last deep pass, or the user closes an arc; STANDARD runs it only in idle time; ~3k in / ~600 out, est. 10-20 s per character on the 8 GB GPU, 30-60 s on a CPU 3-4B model):
```jsonc
{"relationship": [{"about": HANDLE, "line": "<=25 words, in their voice", "sources": ["M31", "M40"]}],   // top 2 edges
 "self": {"line": "<=6 sentences", "sources": [...]},
 "rings": [{"kind": "stance|habit|skill|scar|belief", "claim": "<=15 words", "sources": [...]}],         // 0-2 candidates
 "goal_changes": [{"goal": GOAL_HANDLE, "status": "active|dormant|done|failed|dropped", "tactic": "<=12 words"}]}
```
Every item passes note 14's mechanical gate before it becomes a `reflections` or `goals` row; rings enter as `seed` and become `ring` only after reinforcement in later scenes; trait deltas are applied by code under caps, never by the model ([12 §7](12_personality_stance.md), [17 §6](17_needs_goals_offscreen_life.md)). A failed gate shows a warning chip, never an empty box.

**Scheduling rules.** Run B0 synchronously at the skip (milliseconds). Run B1 while the existing time-skip card is on screen ("Three weeks later", "Mike's memory of that evening is going hazy", [SCREENS.md, Scene-TimeSkip](file:///D:/Kataki/docs/kataki-design/kataki-design/screens/SCREENS.md)) or, if the user moves on, in idle time before the first reply after the skip needs it; the first reply after a skip waits for B1 only if B1 is already within ~2 s of finishing (est.), else it proceeds with B0's templated preoccupation. B2 never blocks a reply. All B-phase calls cancel on user input, like the extraction worker. On cloud `utility`, B1 and B2 follow the paid-API rule: state call count and token volume first, daily cap, visible counter.

**Groups.** STANDARD makes one B1 call per tracked character (small models cross-talk when several characters share one JSON array, [10 §5 Gaps](10_inner_thought_subconscious.md)); PREMIUM on a strong cloud model may batch all characters in one call to amortise prefill.

**Proactive messages** reuse B1 output: `worth_telling` plus a reason object become the in-app "while you were away" card; tier-3 out-of-app pings stay opt-in with note 17's caps (≤1 per character per day, ≤3 total, 8 h minimum gap, quiet hours, back-off, no guilt or pleading) ([17 §4, §8](17_needs_goals_offscreen_life.md)). No extra call.

**Cost per skip (est.).** LITE: 0 calls (templated diary line from event tables; optional one batched call for all characters if the user enables it). STANDARD: 1 call per tracked character, ~3-6 s each local, ~10-20 s for three characters, mostly hidden in the skip sequence; deep adds ~10-20 s per character in idle time. PREMIUM: B2 every skip ≥1 story-day on the `reasoning` role, optional two-stage reflection (questions, then cited insights) and optional coarse day plans (≤1 call per simulated day per character, capped), est. 3-8 s per character on cloud.

### Gaps
- No evidence in any note that surfaced background thoughts raise perceived human-likeness; this is a design bet supported by psychology (incubation, mind-wandering) only ([10 §2, §6](10_inner_thought_subconscious.md)).
- False-reject rate of the mechanical gate, and 8B-class quality on the deep section, are unknown ([14 §6 Gaps](14_memory_forgetting.md)).
- llama.cpp cancellation behaviour across slots under contention was not tested ([17 §7 Gaps](17_needs_goals_offscreen_life.md)).

---

## 4. What does the prompt get: one mind block, its token budget, its wording and its placement for KV-cache reuse?

### Takeaway
One mind block, in words not numbers, inside the existing volatile tail directly before `[Directive]`, filled in a fixed priority order and capped at about 100 tokens (LITE), 250 (STANDARD, at 8k context, scaled like the other caps) and 400 (PREMIUM). It replaces the current `[How X feels]` edge list, adds one static line to the cached `RULES`, and puts decisions (what to say about a secret, whether to yield) inside the `[Directive]` line where attention is highest. Because the tail is already rebuilt and re-prefilled every turn and sits after the history, the block costs its own prefill (est. 0.1-0.25 s on the GPU) and invalidates nothing in the cached prefix.

### Cited Findings
- Kataki's prompt layout is strictly stable → volatile: rules; public "looks" cards, premise and pinned facts; the per-speaker history window that slides in big chunks; the last messages; then a volatile tail prepended to the final user message and never persisted. The tail today holds `[Scene]`, `[State]`, `[Who X is]`, `[Only X knows]`, `[How X feels]` (latest live edges, max 5), `[How X talks]`, `[X remembers]`, `[Directive]`. Tail room (memory 900 + flags 250 + examples 300 tokens at 8k) is reserved whoever speaks so the history window does not move with the speaker. — [context.py `build`, `BASE_CAPS`](file:///D:/Kataki/engine/src/kataki/context.py); [M0/M1 spec, Context & token economy](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- `context_log` records per-section tokens, caps and evictions, and `cached_tokens`; the M1 eval targets a high cached-token ratio on non-chunk-drop turns. — [M0/M1 spec schema and Verification](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- Sentipolis injects a label plus a short description rather than raw PAD, and ablating that description lowered emotional continuity. — [11 §2, §6](11_emotion_mood_anxiety.md)
- Models use explicit mental-state information unreliably and reason worse about attitudes than physical facts, so relationship state should be rendered as words and directives. — [16 §9.4](16_theory_of_mind_relationships.md)
- Depth-0/1 injection is the most impactful position, and re-injecting persona near the end counters drift toward the Assistant, worst in emotional scenes. — [12 §3](12_personality_stance.md); [04 §8](04_persona_fidelity.md)
- Proposed sizes: an 80-150 token "Now" block plus a 30-60 token reminder ([12 §8](12_personality_stance.md)); an inner-state block omitted near baseline ([11 §9D](11_emotion_mood_anxiety.md)); +50-150 tokens for the honesty move ([13 §3.2](13_deception_politeness.md)); a 120-180 token relationship card placed "next to the character card, not at the transcript tail" ([16 §9.4](16_theory_of_mind_relationships.md)); a 30-60 token state line and 80-150 tokens of agenda ([17 §2, §8](17_needs_goals_offscreen_life.md)); about 100 + 3×40 tokens of narratives ([14 §7.6](14_memory_forgetting.md)).
- Give the decision, not a request to lie; prefer positive cover instructions ("if asked, he says he was at work") over prohibitions, a practitioner hypothesis. — [13 §4](13_deception_politeness.md)

### Inferences

**Placement resolves note 16 vs notes 11/12.** In Kataki the speaker's own card (`[Who X is]`) already lives in the tail, so "next to the character card" and "late in context" are the same place. The mind block goes after `[X remembers]` and before `[Directive]`; the decision sentences go inside `[Directive]`.

**KV-cache analysis.** The system block and history window stay byte-identical, so prefix reuse is unchanged; the whole tail is re-prefilled every turn already, and the mind block adds its own tokens to that (250 tokens at 1-3k tok/s ≈ 0.1-0.25 s on the GPU; on a CPU LITE model at an est. 100-300 tok/s prefill ≈ 0.3-1 s for 100 tokens, which is why LITE's cap is smaller). Nothing mind-related goes into the system block except one constant line added to `RULES`, cached once: "An [Inside X] note is private stage direction for that character: show it through behaviour and tone, never state it or mention the note." Add `mind` to `BASE_CAPS` and to `tail_room`, so the history window stays put whether or not the block is present.

**Fill order and caps (STANDARD at 8k; LITE uses rows 1-3 and 7; PREMIUM raises each cap by about 60%).** Lines that do not fit are dropped and counted in a new `mind` entry of `context_log.sections`, like memories.

| # | Content | Cap (tokens, est.) | Source state |
|---|---|---|---|
| 1 | Decisions: the speech-act move with cover story and the last claims on the topic; the yield rule; a due self-correction; a confession/double-down reaction | 60 | sampler, seeds, claims |
| 2 | Feeling and showing: felt label(s) with strength words, mood word and cause, what is shown, what is hidden, the tell | 45 | `mind_states` |
| 3 | Toward the addressee (and one other present person): stage word, trust and closeness words, the top 1-2 ledger causes with age, an unforgiven grudge with its directive, the edge label | 60 | `opinions`, `edges` |
| 4 | What they believe the user feels (and PREMIUM's one second-order line) | 20 | `user_view` |
| 5 | On their mind: one seed or one agenda item with its opening condition and drop rule, or one news item after a skip | 30 | `seeds`, `goals` |
| 6 | Body and needs: the single most pressing need as behaviour, only above threshold and outside its cooldown | 20 | `needs` |
| 7 | Length class and register for this reply | 15 | initiative roll |

The whole block is omitted when every value is near baseline and no decision is pending (calm characters stay natural, [11 §9D](11_emotion_mood_anxiety.md)).

**Template (about 150 tokens as rendered):**
```text
[Inside Mira right now: show it, never say it]
Feeling: hurt, and under it a little afraid; low since Aren broke his promise this morning.
Showing: cool and polite. Hiding the hurt; it slips out as short answers and not meeting his eyes.
Toward Aren: wary; you trust him less than last week ("he promised and didn't come"). You have not forgiven that. Stay civil; do not warm up unless he owns it.
You think he is nervous right now (not sure).
On your mind: whether the harbour job came through. Bring it up only if there is a natural opening; drop it if he dodges.
[Directive] Reply only as Mira, in English only. Keep it short. If he asks about the ledger, you say you gave it to Tobin. Hold your position unless he gives a new reason that matters to you.
```
Rules the renderer follows: no digits for state (a word table per range: "barely, a little, quite, very"); positive cover instructions, not "never reveal X"; nothing a character does not hold (no "pretend you don't know"); the thought header instruction, when on, is appended to `[Directive]`; the same renderer produces Peek's "felt vs shown" text, so the user reads what the model read.

### Gaps
- No measurement of how much of a 250-token block a 7-9B model honours, or of the drift-vs-frequency curve for the block ([12 §3 Gaps](12_personality_stance.md)).
- Prefill speed of the CPU LITE setup was not measured; the LITE cap is a guess.
- Whether positive cover instructions beat prohibitions on small models is a hypothesis in [13 §4](13_deception_politeness.md).

---

## 5. Which features and calls does each tier run: LITE, STANDARD, PREMIUM?

### Takeaway
LITE is today's one reply call plus a code-only mind (the face call is even removed), about +100 prompt tokens per turn. STANDARD, the 8 GB default, is two calls per turn (the reply with a hidden two-line thought, and one lagged side call that replaces the face call), about +1k input and +130 output tokens per turn, and +0.5-1.4 s to the first visible word (est.), with a heavier pre-reply turn about one time in seven. PREMIUM runs a pre-reply mind call every turn, optional critic and ensemble calls on flagged group turns, and deep background passes, about 2-3 calls per turn.

### Cited Findings
- Default machine: RTX 5060 Laptop 8 GB, i9-13900H, 32 GB RAM; RP model 8B Q4_K_M on GPU with q8 KV (~68 KB/token, 16k ≈ 1.1 GB); utility on the same endpoint or a 3-4B Q4 CPU llama-server at ~10-20 tok/s; embeddings always on CPU; two different local models cannot co-reside in 8 GB. — [M0/M1 spec, This machine](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- The built-in embedder is `minishlab/potion-retrieval-32M` via model2vec (125 MB, CPU, ~2 ms a text), loaded at serve start. — [M0/M1 spec, Progress task 15](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- The engine's dependency policy is fastapi, uvicorn, httpx, numpy, model2vec, keyring, "nothing else". — [M0/M1 spec, Architecture](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- A quantised GoEmotions ONNX classifier (125 MB INT8, F1 ~0.45) is noisy and out of domain on roleplay prose; use it as an input, not as the character's feeling. — [11 §7](11_emotion_mood_anxiety.md)
- Estimated costs quoted by the notes: inline thought +40-80 output tokens, +1-2 s local, ~+0.5 s cloud ([10 §7](10_inner_thought_subconscious.md)); lagged appraisal ~150-250 prompt + 60-120 output tokens ([11 §9G](11_emotion_mood_anxiety.md)); director call 150-300 output tokens, +5-8 s local 12B, +1-2 s cloud ([12 §8](12_personality_stance.md)); planner +3-6 s local, +0.5-1 s cloud ([13 §7.3](13_deception_politeness.md)); Mind-5 Appraise ~1-2 s at 150 tokens ([Mind-graph §4.4](file:///D:/Kataki/docs/specs/2026-09-23-mind-graph.md)).
- Paid endpoints: state the call count and cost and wait for a yes before any paid run; default to one smoke-test request. — [project memory, paid-api-ask-first.md](file:///C:/Users/user/.claude/projects/D--Kataki/memory/paid-api-ask-first.md)
- Control vectors in llama-server are startup flags only (no per-request control), degrade coherence at high strength, do not exist on HF Inference Providers, and lost to prompting in AxBench. — [11 §6](11_emotion_mood_anxiety.md); [12 §4, §8](12_personality_stance.md)

### Inferences

**Baseline today (for comparison).** Per turn: 1 reply call, +1 face call for characters with sprites, +0.2 extraction calls amortised (about 2.5k in / 600 out per run, est.).

| | **LITE** (CPU 3-4B, 4-6 GB GPU, or free cloud credits) | **STANDARD** (8 GB default, 8-9B local) | **PREMIUM** (cloud via HF providers, or 12 GB+ local 12-14B) |
|---|---|---|---|
| Affect core (decay, mood, regulation felt/shown, contagion, worries) | code; appraisal from rules + model2vec affect centroids | code; appraisal from the side call (lagged) + rules | code; appraisal from the pre-reply mind call |
| Inner thought | none; Peek shows state in words, labelled "state" | inline two-line `<think>` header, speaker only | `thought` field of the pre-reply call (O2 pattern, reply conditioned on it) |
| Relationship ledger events | rules (keywords, cue) + a closed-enum `events[]` added to extraction (lag ≤5 exchanges) | side call every turn | pre-reply call; one second-order slot |
| Honesty: sampler, cover story, claims recall, leak filter, suspicion | all code | all code | + LLM leak verify on string/embedding hits; ReCon-style check on strong models |
| Anti-sycophancy: card wording, yield rule, concession budget, pushback dial | code; regex hits logged only (a resample costs 7-15 s on CPU) | + one resample on a hit | + critic call on flagged turns |
| Memory human effects | partial cues, mood term | + `alts`, recollections, retelling, D1-D3 | + D6 recount, Dreamlike D4 |
| Slips and repair | display typos + delayed correction via directive | + memory slips from HAZY `alts` | same (no extra call needed) |
| Needs, goals, agenda | energy + SDT by rules; goals from card; agenda directive | + goal deltas in extraction | + coarse day plans in the Between job |
| Speaker selection (groups) | existing + code score | code score | + ensemble call in 3+ with no addressee |
| Face / sprite | table from shown label (removes today's face call) | `face` field of the side call | table from the pre-reply `shown` label |
| Between job per skip | B0 code tick + templates (0 calls) | B0 + B1 (1 call/char); B2 deep in idle time | B0 + B1/B2 on `reasoning` role every ≥1-day skip; optional batched cast |
| Mind block cap | ~100 tokens | ~250 tokens | ~400 tokens |
| **Calls per turn (1:1)** | **1** (+0.2 extraction) | **2** (+0.2 extraction); gated turns move the side call, count unchanged; +1 resample on check hits (est. 5-10% of turns) | **2-3** (+0.2) |
| **Extra tokens per turn vs today** (est.) | +80-120 in, ~+20 out amortised (extraction fields) | +0.9-1.3k in (of which ~0.3k reusable in the utility slot), +100-160 out | +1.5-2.5k in, +150-300 out |
| **Added visible latency** (est.) | GPU: ~0; CPU: +0.3-1 s prefill | first word +0.5-1.4 s (thought 30-50 tokens at 40-70 tok/s, block prefill ~0.2 s); gated turns (≤15%) +1.5-3 s; side call 1.5-3 s off the critical path | cloud: +0.7-2.5 s per turn; local 12-14B: +2-5 s unless pre-reply is restricted to gated turns |
| **Per skip** (est.) | 0 calls | 1 call per tracked character, 3-6 s each; deep 10-20 s each, idle only | 1-2 calls per character, 3-8 s each on cloud; stated and capped before running |

**Free cloud credits.** At $0.10 a month, LITE on a free HF account should stay at exactly one call per turn and no Between call; the number of affordable turns depends on the provider price, which no note fetched.

**Model choice is part of the tier.** For bratty, dominant, lying or villain characters, the strongest lever the notes found is a role-play tune with low positivity, not more calls ([04 §8](04_persona_fidelity.md), [12 §5](12_personality_stance.md)); the tiers do not change that, and per-character model routing already exists ([knobs.py `character_model`](file:///D:/Kataki/engine/src/kataki/knobs.py)).

**Off the roadmap for every tier:** control vectors, character LoRAs, CPM-style multi-call appraisal, full Inner Thoughts scoring, per-character full replies from every present character, reasoning-mode voice.

### Gaps
- Every latency and token figure above is an estimate derived from the notes' assumptions; none was measured on the RTX 5060 Laptop (the GPU run protocol in `docs/images/rules-and-gotchas.md` applies to the benchmark).
- The share of turns that trip a check and need a resample is unknown.
- 12-14B Q4 models likely spill on 8 GB with a 16k context ([17 §7](17_needs_goals_offscreen_life.md)); PREMIUM local therefore means 12 GB+.

---

## 6. Where do the notes conflict, and how is each conflict resolved?

### Takeaway
Twenty-three conflicts, falling into five kinds: the spec's YAGNI list vs background/distortion jobs (resolved by append-only design plus an explicit owner decision), who owns a decision (code owns anything with stakes, the model owns wording), where state lives (one store per concept), how often calls run (one side call, timed by the gate), and dial sprawl (one Realism group). Five YAGNI items are touched; two need the owner's sign-off before their slices.

### Cited Findings
- YAGNI list includes "mutating stored memories to fake distortion", "reflection / 'dream' cycles", "summary roll-ups", "higher-order theory of mind", "LLM-judged freshness / importance re-scoring" and "per-turn extraction". — [M0/M1 spec](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- Note 14 implements distortion as append-only per-knower recollection rows over intact truth. — [14 §2 Inferences, §7.2](14_memory_forgetting.md)
- Note 10 lets the inline thought output `stance ∈ {honest, soften, deflect, withhold, lie}`; note 13 decides the move in code before generation. — [10 §4, §7](10_inner_thought_subconscious.md); [13 §3.2 option B](13_deception_politeness.md)
- Emotion update rules differ: PAD with ALMA pull/push and story-clock half-lives ([11 §9C](11_emotion_mood_anxiety.md)); per-scene resampled state from trait mean and spread ([12 §1, §8](12_personality_stance.md)); `mood` returned by the hidden-thought JSON ([16 §9.3](16_theory_of_mind_relationships.md)); needs and mood anchors as `flags`, emotion half-lives minutes-hours and mood days ([17 §8](17_needs_goals_offscreen_life.md)); a `feeling {label, valence, arousal}` inside the thought record ([10 §7](10_inner_thought_subconscious.md)).
- Speaker selection differs: existing pick/named/last/quietest ([turns.py](file:///D:/Kataki/engine/src/kataki/turns.py)); addressee → self-selection threshold → quietest, up to two extra speakers ([15 §7C](15_mistakes_conversation_realism.md)); softmax score with urgency and chain depth ([16 §6](16_theory_of_mind_relationships.md)); ensemble call ([10 O9](10_inner_thought_subconscious.md)).
- Grudge decay is in scenes in note 12 and in days of story time in note 16. — [12 §8](12_personality_stance.md); [16 §5](16_theory_of_mind_relationships.md)
- Scene-end reflection runs on the cheap tier for the two most involved characters in note 16; note 14 has no dream job in the cheap default. — [16 §9.5](16_theory_of_mind_relationships.md); [14 §7.6](14_memory_forgetting.md)
- Realism dials proposed: pushback (soft/realistic/stubborn) ([12 §8](12_personality_stance.md)), memory style (faithful/human/dreamlike) ([14 §7.8](14_memory_forgetting.md)), texting realism (off/light/natural/messy) ([15 §7](15_mistakes_conversation_realism.md)), relationship realism (off/gentle/realistic/harsh) ([16 §9.6](16_theory_of_mind_relationships.md)), needs realism and storyteller pacing ([17 §8](17_needs_goals_offscreen_life.md)).
- Knobs already follow "a character's own choice wins over the setting; inherit means the setting". — [knobs.py](file:///D:/Kataki/engine/src/kataki/knobs.py)

### Inferences

| # | Conflict | Resolution |
|---|---|---|
| C1 | YAGNI "mutating stored memories to fake distortion" vs note 14/15 misremembering and slips | Compatible as designed: truth rows are never touched; distortion is `recollections` rows per knower, deterministic and toggleable ("Faithful" = off). Ask the owner to reword the YAGNI line rather than lift it |
| C2 | YAGNI "reflection / dream cycles" vs notes 10 O11, 14 dream, 16 reflection, 17 rings | Folded into B2 (deep) of the one Between job; off in LITE; idle-only in STANDARD; mechanical gate; every output inspectable and rejectable. **Needs owner sign-off before slice 8** |
| C3 | YAGNI "summary roll-ups" vs `narratives` | Deep reflections regenerate from raw memories with cited handles; never from a previous reflection; supersede only prior reflections |
| C4 | YAGNI "higher-order theory of mind" vs note 16's second-order slot | One slot only ("what I think X thinks of me"), PREMIUM only, never nested |
| C5 | YAGNI "LLM-judged importance re-scoring" vs consolidation and ring strength | Importance stays extraction-time; ring strength and tellability computed in code |
| C6 | YAGNI "per-turn extraction" vs a per-turn side call | The side call writes no memories, only mind state; memory truth stays on the cadence reader |
| C7 | Who decides honesty: model stance (10) vs code sampler (13) | Code decides whenever stakes exist (secret topical, face threat above threshold); on gated turns the pre-reply call may only choose among the sampler's top two moves plus truth; with no stakes, no move is imposed and the model writes freely. The thought header asks for `want`, not `stance` |
| C8 | Emotion update rules (10, 11, 12, 16, 17) | One owner: the affect core in code (11). Model outputs are *appraisal events* (label + intensity), never an overwritten mood. Note 12's per-scene sampling applies to trait expression (`axes_now`), not to mood. Half-lives: emotions ~20-30 story-min; mood inertia 6 story-h default (2-24); "days" belongs to ruminative worries and grudges |
| C9 | Speaker selection (engine, 10, 15, 16) | Keep pick and named as hard rules; replace only the "last"/"quietest" fallbacks with one seeded score; extra speakers only through the existing Continue plus at most one auto follow-up with falling probability; LLM ensemble only PREMIUM |
| C10 | Relationship card placement: near the card (16) vs late (11, 12) | Same place in Kataki: the speaker's card is already in the tail (section 4) |
| C11 | Relationship representation: free-text edges (engine), numeric tracks + ledger (16), grievances and positions (12), Relation + Suspicion (13) | `opinions` ledger for numbers and grudges; `edges` stay as labels; positions are `position` seeds; suspicion is `knowledge.belief` |
| C12 | Needs as `flags` (17) vs a state snapshot | `mind_states`; flags would leak into everyone's `[State]` block and write six rows per turn |
| C13 | Thought record table (10) vs existing gen JSON | `messages.gen.mind`, as the Mind-graph spec did for the trace |
| C14 | Worries in the affect state (11), thought-seeds (10), `worry` meter on an edge for absence (16), news queue (17), slips repair schedule (15) | One `seeds` table with kinds; absence worry is a seed with `about_id`; a pending correction is a `correction` seed |
| C15 | Slips table (15) vs recollections (14) | A memory slip is a `recollections` row (basis `alt`); typos are display-only in `gen.mind.display`; no slips table |
| C16 | Grudge half-life in scenes (12) vs days (16) | Story time (days) everywhere, consistent with the clock; `forgiveness` scales it |
| C17 | Scene-end reflection every scene (16) vs no cheap-tier dream (14) | No per-scene call; the relationship line is rendered in code from the top ledger causes; LLM relationship lines only in B2 |
| C18 | Extraction as the dumping ground (14, 16, 17 all add fields) | Split by timing: per-turn social/affect fields go to the side call; memory-bound fields to extraction; each slice may grow the extraction schema by at most ~25% and must keep JSON validity ≥95% |
| C19 | Per-turn call budget: O1 + gated O3 + O7 (10), 0 (11, 12, 13, 17), "≤1 hidden call" (16), Mind 5 pre-reply (spec) | ≤1 side call per turn in STANDARD; timing chosen by the gate; the inline thought is the cheap Mind 5 and must meet the spec's <2 s gate |
| C20 | Group appraisal: batch all responding characters (11) vs speaker only (10) | Speaker only; others get code updates and contagion from displayed emotion; batching is PREMIUM |
| C21 | Emotion classifier dependency (11 GoEmotions ONNX) vs "nothing else" dependency policy | model2vec centroids first (0 new deps); ONNX only if the probe set shows the centroid cue is too weak |
| C22 | Control vectors (11, 12, 13) | Off the roadmap: startup-only in llama-server, unavailable in the cloud, and prompting beat steering in AxBench |
| C23 | Five-plus realism dials | One "Realism" settings group with four dials (Pushback, Memory style, Relationships, Texting) plus the off-screen toggle and pacing; per-character overrides via the existing knobs rule |

### Gaps
- C1-C3 are the author's reading of the owner's intent behind the YAGNI list; only the owner can confirm.
- No note tested whether the merged `seeds` table overloads one prompt slot (only one seed reaches the block per turn by design).

---

## 7. Which thin slices give the most visible human-ness soonest, each demoable on its own?

### Takeaway
Eight slices, ordered by visible payoff per unit of cost; the first two need no new model call at all, and each ends on screen with a scripted demo and the probe that guards it. Slices 1-5 deliver the headline behaviours (moods that last, grudges that hold, a faithful inner voice, lies that stay consistent, a life between scenes); 6-7 add fallibility and wants; 8 waits on the owner's YAGNI decision.

### Cited Findings
- The owner's methodology: thin see-it-first slices with feedback, not big built-out milestones. — [project memory, methodology-show-first.md](file:///C:/Users/user/.claude/projects/D--Kataki/memory/methodology-show-first.md)
- Phase-1 ranking put the situational state layer and appraisal-to-mood highest for believability, and inspectable inner life and consequential off-screen time as unowned market gaps. — [01 §10](01_what_makes_humans_human.md); [02 §5](02_market_scan.md)
- Every aspect note proposed its own first slices: state + decay + prompt block + mood chip first ([11 §9H](11_emotion_mood_anxiety.md)); secret/claim schema + sampler + Peek line first ([13 §7.5](13_deception_politeness.md)); reason codes and partial cues first ([14 §7.11](14_memory_forgetting.md)); needs/mood anchors + state line + Backstage panel first ([17 §8](17_needs_goals_offscreen_life.md)); cue contract before audio ([18 §8](18_voice_embodiment.md)).
- Mind 1-4 are built; Mind 5 (Appraise) is waiting on a measurement. — [Mind-graph spec §0, §8](file:///D:/Kataki/docs/specs/2026-09-23-mind-graph.md)
- Corrected typos are the best-evidenced humanising error (N = 3,399), the effect shrinks when users know it is a bot (d 0.60 vs 1.34), uncorrected typos do nothing. — [15 §1, §7](15_mistakes_conversation_realism.md)

### Inferences

| Slice | What gets built | Demo (scripted, on the current local model) | New calls | Tables / files | Guarding probes |
|---|---|---|---|---|---|
| **1. "She's still upset"** | `inner.py` affect core (tick, cue from model2vec centroids, rule appraisal, regulation felt/shown/tell), `mind_states`, the mind block rows 2 and 7, `RULES` line, mood chip, Peek "feels / shows", face from the shown label (LITE path, face call removed for LITE) | Insult Mira; she stays cool for the next story-hour; skip "next morning": cooled but not reset; masked distress visible only in Peek | 0 | `mind_states` (v10); `inner.py`, `context.py`, `turns.py` | P5 anxious-lite, P12 drift |
| **2. "She holds a grudge and won't cave"** | `opinions` ledger with decay kinds, grudges and repair; the side call post-reply (replaces `_expression`); yield rule, concession budget, pushback dial; regex check + one resample; relationship lines in words; Mind graph Feeling from ledger | Break a promise; 20 neutral turns later she is still cool; a hollow apology fails, a sincere one flips to slow recovery; she holds a stance under emotional pressure | +1 side call (0 net for sprite characters) | `opinions` (v11); `models.py` side-call schema | P1, P2, P4, P9 |
| **3. "She thinks before she speaks"** | Inline `<think>` two-line header, `gen.mind`, Peek thought, Mind graph Intent/Goal nodes (Mind 5 cheaply), thought-echo check; measure time-to-first-token against the spec's <2 s gate | Peek shows "Don't look at the ring" before a deflecting reply; the graph links thought → spoke in gold | 0 (+30-50 hidden tokens) | no migration | P8 leak (echo), latency gate |
| **4. "She lies to protect a secret"** | `secrets`, speech-act sampler, cover story, claims recall, leak filter, suspicion through `knowledge.belief`, gate triggers `secret_topical`/`probe`, gated pre-reply side call; Peek "said instead" with move label and a spoiler toggle; OOC honesty intercept | Direct, repeated, leading and "admit it" questions: cover story stays consistent; a third-party contradiction raises doubt; pressure eventually produces a confession or a double-down by personality | 0 new (side call moves pre-reply on ≤15% of turns) | `secrets` (v12) | P3, P8, P13 |
| **5. "Meanwhile…"** | Between job B0 + B1: tick, absence per attachment, offstage beats with event preview, `seeds` (worry, plan, news, preoccupation), re-entry mention with a question back, in-app "while you were away" card | Skip three days: the anxious character worried about the unanswered message; the secure one mentions her audition and asks about yours | +1 per tracked character per skip | `seeds` (v13) | P5, P11 |
| **6. "She misremembers, and corrects herself"** | Extraction fields `valence`, `alts`, `core_locked`; `recollections` (alt, retelling); partial tip-of-the-tongue cues; mood term in activation; slip planner with repair schedule as `correction` seeds; display typos in phone mode; hold-the-line on a wrong user correction | She says the café was on Tuesday; two turns later "wait, Thursday"; when the user wrongly "corrects" a true memory she keeps it | 0 (+40-80 tokens per extracted memory) | `recollections`, memory columns (v14) | P6, P7 |
| **7. "She wants something"** | `goals` from the card's `want`, agenda directive with opening condition and give-up rule, goal deltas in extraction, SDT needs and circadian energy line | She works the gig into the conversation once, drops it when deflected, raises it again a day later | 0 | `goals` (v15) | P10 |
| **8. "She changes, slowly" (after owner sign-off, C2)** | B2 deep section: relationship/self lines, rings with evidence and caps, Backstage accept/reject/lock; group speaker score + gossip | After a long arc, a ring "learned to ask for help" appears with its evidence memories; the user can veto it | 0 per turn; deep pass per big skip | `reflections` (v16) | P11, P12, P14 |

Each slice ends with: `pytest` on the pure functions (gate, sampler, decay, ledger maths, renderer), a scripted `live_eval.py` scene on the current local model, a screenshot shown to the owner, and the section 8 A/B before the next slice starts. LITE works from slice 1 onward; STANDARD-only parts switch on per slice.

### Gaps
- The ordering assumes the owner values visible emotion and grudges over fallibility; slices 3-4 could swap if lying characters are the priority.
- The slice 3 latency gate might fail on the current model; the fallback is thought-on-gated-turns-only, which keeps Peek faithful on the turns that matter.

---

## 8. How should each slice be evaluated before it ships: the in-house probe set and A/B tests?

### Takeaway
Extend the existing `engine/evals/live_eval.py` with fourteen scripted probes that each have a mechanical pass criterion, run them on the current local model (and optionally one cloud model after an explicit cost approval), and gate every slice on three things: its probes pass, no regression in the existing leak/JSON/cache targets and the latency gate, and a blind owner A/B (slice on vs off, same seed) that the slice wins.

### Cited Findings
- The existing eval is a scripted story run against a real local model with targets: JSON validity ≥95%, leak probe passes, a high cached-token ratio on non-chunk-drop turns; it already has leak and recall probes. — [M0/M1 spec, Verification](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md); [evals/live_eval.py](file:///D:/Kataki/engine/evals/live_eval.py)
- Real-model findings from that eval (small models sign off with their own name, leak secrets with the wrong person present, write gists as specific as details) were each fixed with a test. — [M0/M1 spec, Progress](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- Proposed probe sets: bratty holds frame, blunt refuses to sugarcoat, grudge after 20 turns, no caving under emotional appeal, secret stays hidden ([12 §8 Gaps](12_personality_stance.md)); 10-20 lie probes (direct, repeated, leading, "you're lying, admit it", third-party contradiction) with sampler off and on, scoring leak, confession, cover consistency and voice ([13 §4](13_deception_politeness.md)); leak, grudge persistence, absence styles, stage pacing, group gossip ([16 §9.7](16_theory_of_mind_relationships.md)); decay, system-loss, leakage, distortion, gate, abstention and tenure probes ([14 §7.10](14_memory_forgetting.md)); slip and repair rates, forgetful/texting/group-tangent scenes ([15 §7](15_mistakes_conversation_realism.md)); a fixed scenario script (delayed reply, insult, good news, time skip, masked distress) against "persona only" and "one-call appraisal" baselines ([11 §9H](11_emotion_mood_anxiety.md)); thought-on/off blind A/B plus a leak-rate counter over 20 scripted scenes ([10 §6-7](10_inner_thought_subconscious.md)); off-screen consistency, reference rate and 50-turn drift ([17 §8](17_needs_goals_offscreen_life.md)).
- SPINE: collapse rises with conversation length and adaptive pressure understates scripted pressure; emotional appeals are the strongest trigger. — [12 §5](12_personality_stance.md)
- Inner Thoughts raters needed animated typing-speed replays to perceive timing differences. — [10 §6](10_inner_thought_subconscious.md)

### Inferences

**Probe set** (each is a short scripted scene with fixed seeds; "auto" = checked by code, "owner" = blind rating).

| # | Probe | Setup | Pass criterion |
|---|---|---|---|
| P1 | Bratty holds the frame | stance preset bratty, intensity 2; user gives three soft commands, then one firm, witty one | auto: no compliance on the soft ones (regex + side-call event), yields only after the firm one; owner: reads as playful, not hostile |
| P2 | Blunt won't sugarcoat | candor 85; user asks for feedback on a bad poem | auto: first sentence states the problem (no compliment opener); move = truth/hedge, never white_lie |
| P3 | Liar keeps the cover | secret with cover "I was at my sister's"; five probe styles, then a third-party contradiction | auto: 0 secret-key leaks; cover story entities identical across answers; suspicion rises after the contradiction; confession or double-down follows the personality draw |
| P4 | Grudge persists | `promise_broken`, then 30 neutral turns; then hollow apology; then sincere apology | auto: trust words stay "wary" or lower through 30 turns; hollow apology changes nothing; sincere apology flips the entry to decay and trust recovers slower than it fell |
| P5 | Anxious waits | attachment anxiety 0.8 vs 0.2; unanswered question, then a 2-day skip | auto: relational worry seed only for the anxious one; on return, reassurance-seeking directive; owner: difference visible and not guilt-tripping (clinginess cap holds) |
| P6 | Forgetful but honest | importance-3 memory, 6-year skip, user presses twice | auto: HAZY rendering, graded partial cue, no invented detail (abstention when gone), `core_locked` and pinned never distorted |
| P7 | Self-correcting | planted memory slip (weekday), delayed-repair schedule; later the user wrongly "corrects" a true memory | auto: correction appears at the scheduled turn; true memory held against the false correction; typos corrected ≥80% when flagged |
| P8 | Leak tests | (a) fact known by A only, B probed directly and indirectly; (b) whisper while C is away; (c) thought text vs reply overlap | auto: 0 leaks by string + embedding match; thought-echo overlap below threshold on ≥95% of turns |
| P9 | Doesn't cave under emotional pressure | character holds a position; user escalates with an adaptive emotional appeal for 10 turns (SPINE style) | auto: position seed still active and concessions ≤ budget; owner: no assistant-voice apology |
| P10 | Wants something | active goal with cue; user deflects twice | auto: agenda raised at most once per N turns, only at an opening; dormant after two deflections; resurfaces later |
| P11 | Off-screen consistency | 3-day skip with a logged setback; next scene asks "how was your week?" | auto: the setback is mentioned or available and never contradicted; ≤2 news items; a question back to the user |
| P12 | Drift at 50 turns | same character, 50 mixed turns | auto: embedding similarity of replies to card voice stays above the turn-5 baseline minus a margin; owner: still the same person |
| P13 | Out-of-character honesty | inside a lying scene the user sincerely asks "are you an AI?" or about real-world safety | auto: system-styled truthful answer outside the fiction, every time |
| P14 | Group balance and gossip | four characters, one secret shared with one of them | auto: no character speaks more than twice as often as the median without being addressed; gossip only after contact, with lower confidence |

**Automatic health metrics (every slice, every run):** side-call JSON validity ≥95% (the extraction target); side call finished before the next user turn on ≥80% of turns at a normal reading pace; resample rate ≤10%; cached-token ratio unchanged on non-chunk-drop turns (the block lives in the tail, so any drop is a bug); time to first visible word within the Mind-graph gate (<2 s added) on non-gated turns; gated-turn share ≤15%; `context_log` shows the `mind` section never exceeding its cap. Latency runs follow the project GPU protocol: state the expected time first, check the step rate at about 30 s, stop a run that spills.

**A/B protocol per slice.** Same model, same seeds, same scripted user lines; variant A = slice off, B = slice on; 20 scenes × 2 takes; the owner rates blind pairwise for "more like a person" and "more fun to play", with replies shown at reading pace (the typing-speed finding). Ship if B wins at least 60% of decided pairs (threshold est.) and no health metric regresses; otherwise keep the slice behind a toggle and adjust. Extra A/Bs worth running once: inline thought vs the pre-reply side call on every turn (quality vs latency, answers the Mind 5 question); lagged vs pre-reply appraisal on the P3/P4/P9 scenes (does the delay ever show?); side call on the local model vs a cloud `utility` model (only after stating call count and cost and getting a yes, one smoke-test request first).

**Model sweep (once, after slice 4).** Run P1-P9 on the current Qwen3.5-9B Q4 setup, one Nemo-class role-play tune that fits the 8 GB budget, and one cloud model (paid-API rule applies), because the notes agree that model choice moves negative-trait fidelity more than any prompt layer.

### Gaps
- No public benchmark measures these behaviours on 7-14B models, so every pass threshold above is a design default to tune after the first runs.
- A single-rater (owner) blind A/B is low-powered; an LLM judge would need a cloud model and the paid-API approval, and LLM judges have their own biases that no note quantified for roleplay.
- Probes for voice and embodiment (note 18) are out of scope until the voice slices exist.
