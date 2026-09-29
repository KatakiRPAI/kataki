# Motivation, needs, goals, off-screen life, proactivity and growth for LLM roleplay characters (implementation research for Kataki, as of 2026-09-29)

Scope note for the report writer. Phase-1 notes 01-03 in this folder were read first and are reused, not repeated; where I lean on a phase-1 source I cite its original URL and say "via phase-1". About 30 fetches were made. The web-search budget for the session ran out part-way through, so several planned lookups (Sims decay rates, screenwriting want-vs-need, the Roberts personality-change meta-analyses, Kindroid/Nomi "what I did today") could not be done and are listed as Gaps rather than asserted. Many pages were read through a small summarising fetch model, so specifics are "as reported by the page summary". "Inference" means my own reasoning. Numeric defaults in the recommended design are starting values to tune, not findings. Cost and latency figures for local models are estimates for a 7-8B Q4 model on an 8 GB GPU and were not measured on the owner's machine.

Repo facts used for fit (read from D:/Kataki, not web): the engine already has a story clock in story minutes with a time-skip parser (`clock.py`), typed time-versioned state in a `flags` table, `memories` with importance, emotion, covert flag and power-law activation decay, extraction runs tagged with `run_id` so they can be undone, extraction triggers on "every N turns, scene break, time skip", schema-constrained `json_schema` utility calls, and model roles `rp / narrator / utility / reasoning / embed`. The design below reuses these instead of adding parallel machinery. Source: `D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md`, `D:/Kataki/engine/src/kataki/clock.py`.

---

## 1. Needs and drives: what to model, and how to let needs change dialogue without becoming a gimmick

### Takeaway
Use two small layers: three slow psychological needs from self-determination theory (autonomy, competence, relatedness) plus two or three cheap homeostatic variables (energy driven by time awake and time of day, optionally fullness, and a stimulation/boredom meter). Update them in closed form from the story clock at zero LLM cost, and let them act on how a character speaks (length, patience, irritability, distraction), surfacing them in words rarely. Evidence that needs change LLM-agent behaviour is real but uneven: in Humanoid Agents, low health, energy and fullness changed behaviour a lot while loneliness barely did, so social/relatedness need must be turned into explicit behaviours rather than left to the model.

### Cited Findings
- Humanoid Agents adds "System 1" state to Generative Agents: needs (fullness, social, fun, health, energy), seven emotions and four closeness levels, used to adapt daily activity and conversation. Needs start at 5/10 except energy at 10/10. When a need was initialised to zero, activity changed by health +156%, energy +56%, fullness +35%, but social only +12%. — [ACL Anthology](https://aclanthology.org/2023.emnlp-demo.15/); [arXiv 2310.05418 (search summary of results)](https://arxiv.org/abs/2310.05418)
- Front Porch AI (open source) ships a Sims-style needs model. The README lists six (hunger, energy, social, fun, hygiene, comfort) and the user guide lists seven (adds bladder). Needs "decay on their own, respond to what actually happens in the scene" and have "real consequences when bottomed out". Decay rates are not disclosed. Needs have their own toggle, independent of the mood engine. — [README](https://github.com/Lufou/front-porch-AI); [User guide](https://frontporchai.app/docs/user-guide/)
- Front Porch mood "carries inertia between turns" using an emotion wheel; bond runs -300 to +300 "earned slowly but lost quickly"; trust runs -100 to +100; promises kept or broken move trust. — [User guide](https://frontporchai.app/docs/user-guide/)
- Front Porch "bad day" is optional and off by default: a character "can arrive tired, hungry, or weather-beaten from their own life, and the sidebar says why". The docs state nothing is invented; only existing state triggers it. — [README](https://github.com/Lufou/front-porch-AI)
- Self-determination theory: autonomy, competence and relatedness are innate needs; satisfaction predicts intrinsic motivation and wellbeing, thwarting harms motivation and mental health; type of motivation matters more than amount. — [APA overview](https://www.apa.org/research-practice/conduct-research/self-determination-theory)
- Sleep deprivation raises reported fatigue, tension and mood disturbance, weakens control of stress-related thoughts and raises impulsivity; attention drops within 24 h awake; chronically sleep-restricted people rate themselves "considerably less impaired" than acutely deprived people despite equal lapses. After 17-19 h awake driving performance was worse than at 0.05% blood alcohol. The two-process model has homeostatic sleep pressure accumulating until function degrades regardless of circadian drive. — [Wikipedia: Sleep deprivation](https://en.wikipedia.org/wiki/Sleep_deprivation) (secondary source, used for orientation only)
- Minds wander 46.9% of the time; wandering content is constrained by automatic salience (affective, sensory) and deliberate control. — [Killingsworth & Gilbert via Harvard Gazette](https://news.harvard.edu/gazette/story/2010/11/wandering-mind-not-a-happy-mind/); [Christoff et al. 2016](https://www.nature.com/articles/nrn.2016.113) (via phase-1 note 01)
- A preprint on the Chameleon dataset reports 74% of psychological variance in interactions is within-person state and that LLMs are "state-blind", replying to the trait and ignoring state. — [arXiv 2601.15395](https://arxiv.org/abs/2601.15395) (via phase-1; single preprint)
- A 2025 "Psychological-mechanism Agent" combines a layered affect model (short, medium and long-term emotion), a thought module for goal-directed and spontaneous thinking, and an action module that integrates emotions, needs and plans; abstract-level only, no numbers retrieved. — [arXiv 2507.19495](https://arxiv.org/abs/2507.19495)
- Generative Agents' documented failure modes include over-cooperativeness (rarely refusing), over-formal dialogue and norm erosion as memory grew. — [ar5iv 2304.03442](https://ar5iv.labs.arxiv.org/html/2304.03442) (via phase-1)

### Inferences
- Do not copy Front Porch's Sims list. Hygiene and bladder are gimmick generators in a roleplay app; energy (with time of day), fullness (optional) and the three SDT needs carry nearly all the realistic behaviour. Keep the list short: energy, fullness (off by default), autonomy, competence, relatedness, stimulation.
- Humanoid Agents' +12% social result implies that a numeric "social = 0.2" injected as text will be largely ignored. Convert relatedness into a concrete behavioural rule (seeks contact, reassurance, longer replies, asks about the user) with a threshold and an agenda item, as in section 2.
- "Without becoming a gimmick" rules: (a) needs change how a character talks, not what the scene is about (reply length, patience, irritability, distraction, wanting to wrap up); (b) a need is verbalised only above a threshold, with a per-need cooldown of several turns and never as a status announcement ("I am hungry" is a tell of a meter); (c) sleep-deprived characters should be irritable and deny it, following the finding that impaired people underrate impairment; (d) a need never blocks or hijacks the user's scene, and the user can turn realism to off, low, normal; (e) any need effect is visible in Backstage ("tired, so short answers") so it reads as motivation rather than randomness.
- SDT thwarting gives principled triggers: autonomy thwarting produces reactance or brattiness, relatedness thwarting produces withdrawal or clinginess (scaled by attachment anxiety), competence thwarting produces defensiveness. This is my mapping, not a sourced finding.
- Energy model: sleep pressure S rises while awake and falls in sleep; a circadian curve C peaks in the day with a per-character chronotype offset; energy = f(C, S). Closed form from the story clock, so a time skip costs nothing. The specific time constants I would start from (about 18 h rise, about 4 h fall, a few hours of chronotype shift) are background knowledge of the two-process model and were not sourced here.

### Options table (needs)

| Option | Extra calls/tokens per turn | Background cost | Latency | Works on 7-14B local? | Evidence |
|---|---|---|---|---|---|
| A. Rule-based meters, closed-form decay, top-1 need injected as a ~30-60 token state line | 0 calls, +30-60 prompt tokens | none | none | Yes (no model work) | Humanoid Agents demo-level; Front Porch (unmeasured); sleep literature for direction |
| B. A plus LLM appraisal of scene events to move autonomy/competence/relatedness | +0 if merged into the existing extraction call, else +1 small call | none | +1-3 s if separate | Feasible with json_schema; untested on small models | Chain-of-Emotion: 2 calls per turn, 30-person study, modest gains (via phase-1 note 03) |
| C. Full free-text "inner state" paragraph regenerated each turn | +1 call, +150-300 output tokens | none | +3-6 s local | Poor: drift and cost, style drift risk | Role-aware reasoning paper warns of style drift from long reasoning (via phase-1 note 03) |

### Gaps
- Sims need-decay rates and the Sims "autonomy" design: fetch of the fan wiki returned HTTP 402 and search budget was exhausted; no sourced numbers.
- No source retrieved for Maslow's hierarchy critiques, drive-reduction theory, or empirical circadian mood curves; the energy formula is my design, not a citation.
- No study found that measures whether needs-driven dialogue raises user-rated believability in roleplay apps; Front Porch's own effect is unmeasured.
- Front Porch's counts of needs disagree between its README (six) and user guide (seven); both are self-descriptions.

---

## 2. Goals, plans and agendas the character pursues

### Takeaway
Give every character a three-level goal stack (long ambitions, medium projects, today's intentions) and a very small conversational agenda (at most two live items per scene) that is injected as a hint and only voiced when there is an opening. Generative Agents supplies the daily-planning pattern; BDI supplies the vocabulary; Inner Thoughts supplies the "voice it only when motivation is high and the moment is right" gate. The want-versus-need pairing from screenwriting is a good card field but I could not source it here.

### Cited Findings
- Generative Agents daily planning: prompt with the agent's summary and the previous day, generate 5-8 rough chunks for the day, then recursively decompose to hour-long chunks and then 5-15 minute chunks. At each step the agent is asked whether to continue the plan or react; only significant observations trigger a reaction. Identity is seeded from one paragraph of description split into seed memories. — [ar5iv 2304.03442](https://ar5iv.labs.arxiv.org/html/2304.03442)
- Reflection: the model is shown the 100 most recent memory records and asked for the 3 most salient high-level questions; reflections form a tree citing evidence records. Reflection fires when summed recent importance exceeds 150, roughly 2-3 times per agent per day. — [ar5iv 2304.03442](https://ar5iv.labs.arxiv.org/html/2304.03442) (via phase-1)
- Ablation (TrueSkill believability): full 29.89, no reflection 26.88, no reflection or planning 25.64, all removed 21.21, crowdworker humans 22.95. — [arXiv 2304.03442](https://arxiv.org/pdf/2304.03442) (via phase-1)
- Cost of that architecture: the 25-agent, 2-day run "cost thousands of dollars in token credits and took multiple days" on gpt-3.5-turbo. — [ar5iv 2304.03442](https://ar5iv.labs.arxiv.org/html/2304.03442) (via phase-1)
- BDI defined as beliefs (sensed information), desires (motivating goals) and intentions (selected plans given current beliefs). A hierarchical BDI with a macro layer for long-term strategy and a micro layer for tactical decisions has been used for LLM agents in a social-deduction game (AIWolf, 2025). — [OpenTrain glossary](https://www.opentrain.ai/glossary/belief-desire-intention-bdi-software-model/); [AIWolfDial 2025 paper](https://aclanthology.org/2025.aiwolfdial-1.3.pdf) (search-result level, not read in full)
- A BDI-integrated LLM approach for human-robot interaction is described as improving reliability and explainability. — [ScienceDirect, Eng. Appl. AI](https://www.sciencedirect.com/science/article/pii/S0952197624019304) (abstract-level)
- Inner Thoughts (CHI 2025): the AI keeps a covert train of thought in parallel with the conversation and models intrinsic motivation to voice a thought; it beat a next-speaker baseline on all seven metrics including initiative and was preferred over 82% of the time; open source. — [ACM](https://dl.acm.org/doi/10.1145/3706598.3713760); [arXiv 2501.00383](https://arxiv.org/abs/2501.00383); [repo](https://github.com/xybruceliu/inner_thoughts) (via phase-1)
- Front Porch AI says characters "pursue goals of their own" and carry "longer-term ambitions that inch forward over many sessions"; short-term objectives show in a sidebar; promises by either party change trust when kept or broken. — [User guide](https://frontporchai.app/docs/user-guide/); [search summary of README](https://github.com/Lufou/front-porch-AI)
- Voyager uses an automatic curriculum that maximises exploration to propose next goals for an LLM agent, with GPT-4 and a skill library; it collected 3.3x more unique items than prior methods. — [arXiv 2305.16291](https://arxiv.org/abs/2305.16291)
- Character arc in fiction is described as a transformation over the story, moving from a starting state through change to self-awareness by the climax. — [Wikipedia: Character arc](https://en.wikipedia.org/wiki/Character_arc)

### Inferences
- Minimal BDI mapping for Kataki: beliefs are what the memory layer retrieves (with clarity tiers and lies already handled by the engine); desires are rows in a `goals` table; intentions are 1-3 "agenda items" currently active, each with a way in, an expiry and a satisfaction test. This adds no LLM call: goal deltas (progress, stalled, done, new) ride the existing extraction run at scene break, time skip or every N turns.
- Card fields worth adding: `want` (conscious external aim), `need` (the unexamined lesson or wound the character has not yet faced), `values` (short list), `fear`. The pair gives the growth mechanism in section 6 a target. The want-versus-need convention comes from screenwriting craft and was not sourced in this pass.
- Agenda gate, cheap version of Inner Thoughts: pressure = priority x need-pressure x time-since-last-attempt; fire only when pressure exceeds a threshold and the scene has an opening (a lull, a topic adjacent to the goal, the user asking a question). At most one agenda attempt per N turns and never against a high-arousal emotional user turn. Voiced through a directive in the volatile tail ("You want to ask about the gig; work it in only if there is a natural opening; drop it if deflected").
- An agenda item should allow failure and give-up: after two deflections the goal changes tactic or goes dormant, and dormant goals leak later ("still thinking about it"). This produces persistence without nagging, a known over-cooperation problem in generative agents (rarely refusing).
- Daily plans: run the Generative Agents day plan only at coarse grain (5-8 chunks, one call per simulated day) and only in premium mode; the cheap default uses routines from the card (job, hobbies, habit times) and never decomposes below the hour.

### Options table (goals)

| Option | Extra calls/tokens | Background cost | Latency | Works on 7-14B local? | Evidence |
|---|---|---|---|---|---|
| A. Goal stack in DB, deltas from existing extraction call, 1-2 agenda hints in volatile tail (recommended default) | +80-150 prompt tokens per turn, +~100 output tokens on extraction runs, 0 new calls | none | none | Yes with json_schema | Design inference; BDI concept; Inner Thoughts gating idea |
| B. Inner-Thoughts style hidden thought each turn that decides whether to voice the agenda | +1 call per turn (thought plus score) | none | +2-5 s per turn | Feasible if the thought is short and in character voice | Inner Thoughts 82% preference (GPT-class models; small-model evidence not found) |
| C. Daily plan per simulated day (5-8 chunks), re-plan on major events | +1 call per simulated day per tracked character | 1 call/day/char while sim runs | seconds, background | Weak on 7B for coherence; fine on cloud utility model | Generative Agents ablation (planning helps) |
| D. Full recursive plan to 5-15 min with per-step reaction checks | dozens of calls per simulated day per character | very high | n/a | No | Generative Agents cost: thousands of dollars for 25 agents x 2 days |

### Gaps
- Want-versus-need, "the lie the character believes", goal hierarchies from screenwriting: the Wikipedia page fetched does not cover them and search budget ran out; treated as craft convention, unsourced.
- No LLM-BDI paper with human-rated believability in roleplay was found; the BDI results are for games and robots.
- No source on how often an agenda may be voiced before users find it pushy; the "once per N turns" figures are design defaults.

---

## 3. Off-screen life: what happens between sessions and during time skips, and how to make it consequential

### Takeaway
Use a hybrid: a small deterministic tick that draws events from rule tables and applies validated state changes, followed by one cheap LLM call that only verbalises what already happened (diary line, "worth telling" line, private thought). Evaluate it lazily when a time skip or a return happens, so no GPU is needed while the user is away. Make it consequential by writing every event into the same memory, flag and relationship stores the scene already reads, with a "news queue" the character draws from when they next meet the user. Existing products mostly do proactive pings from memory; the only near-analogue found, Front Porch AFK, generates on-screen scenes while the app is open rather than simulating a separate life.

### Cited Findings
- Front Porch "Dynamic Responses"/AFK: in one-on-one chats the character generates replies on its own; reply frequency 30-300 s, scene limit 1-10, each scene can consume "a few hours", "half day" or "full day" of story time; typing cancels it; in groups use `/afk`. The README says characters "keep living while you're away, with time and Needs following along" but does not say whether an LLM writes that off-screen time. — [FAQ](https://frontporchai.app/docs/faq/); [README](https://github.com/Lufou/front-porch-AI)
- Front Porch story clock advances every turn "from what just happened", and dreams are generated when story nights pass; Chaos Mode/Chance Time adds random events when a scene gets too stable; a journal encodes emotional significance with semantic retrieval of faded entries. — [User guide](https://frontporchai.app/docs/user-guide/)
- Front Porch can run a second local GGUF beside chat for realism evaluation, journal and side work, unloading it off the GPU when chat needs the card. — [README](https://github.com/Lufou/front-porch-AI)
- Proactive pings in hosted apps: Nomi (paid) messages about previous topics or "character thoughts"; Kindroid (Ultra tier) uses long-term memory and diary content and reduces or stops sending if the user does not reply; Replika (free) asks about things mentioned in passing. Presented by one review site as a retention mechanism. — [WeavAI comparison, Aug 2026](https://weavai.app/blog/en/2026/08/13/proactive-ai-companions-nomi-replika-kindroid-compared/) (aggregator)
- RimWorld storytellers generate events procedurally by analysing the player's situation and choosing what it "assesses will make the most interesting narrative"; the three storytellers differ in pacing: rising and falling tension (Cassandra), extra downtime (Phoebe), pure randomness (Randy). — [Wikipedia: RimWorld](https://en.wikipedia.org/wiki/RimWorld)
- Letta sleep-time agents rewrite memory blocks asynchronously in the background, turning raw context into learned context; offline compute helps most when future queries are predictable from existing context. — [Letta docs](https://docs.letta.com/guides/agents/architectures/sleeptime/); [arXiv 2504.13171](https://arxiv.org/html/2504.13171v1) (via phase-1)
- Incubation meta-analysis: a positive effect exists, larger for divergent-thinking tasks, larger with longer breaks; low-demand filler beats rest for linguistic insight. — [Sio & Ormerod 2009](https://psycnet.apa.org/fulltext/2008-18777-009.html) (via phase-1)
- Social penetration theory: disclosure deepens closeness in layers and unreciprocated disclosure stalls; Goffman's front/back stage frames what a character tells versus keeps. — [Rutgers summary](https://sites.comminfo.rutgers.edu/kgreene/wp-content/uploads/sites/28/2018/02/ACGreene-SPT.pdf); [Simply Psychology](https://www.simplypsychology.org/impression-management.html) (via phase-1)
- llama.cpp can constrain output to a JSON schema (llama-server `json_schema` / `response_format`); the schema is not injected into the prompt; number min/max constraints only work for integers and `uniqueItems`, `contains`, `if/then/else` are unsupported. — [llama.cpp grammars README](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md)
- Generative Agents reflection and importance-rated memory retrieval let earlier events influence later behaviour; the ablation shows memory, planning and reflection each add believability. — [arXiv 2304.03442](https://arxiv.org/pdf/2304.03442) (via phase-1)

### Inferences
- Simulation-driven versus narrative-driven: pure narrative ("here is what she did") is one call but has no authority, so later scenes can contradict it and it changes nothing. Pure simulation is consistent but expensive and flat. The hybrid puts authority in code (events, dice, clamped deltas) and prose in the LLM, so consequences are real and prose is cheap.
- Consequential means a downstream reader exists for every event. Each event should write: (1) a `memories` row (kind `event`, importance, emotion, `covert=1` if the user was not present, tagged `offscreen`, with `run_id` so the user can undo a whole skip); (2) `flags` changes where relevant (job, injury, location, holding); (3) a mood baseline nudge with its own half-life; (4) goal progress; (5) an entry in a `news queue` with a tellability score. The next scene's retrieval, mood block and greeting then surface it without new machinery.
- Tellability (my heuristic, not sourced): importance x emotional intensity x recency, times a relationship-stage gate from social penetration (a stranger does not share a private setback), reduced when the item is embarrassing and the character is high in face-concern. At re-entry mention at most two items, hold the rest ("forgot to say"), and pair disclosure with a question to the user so it stays reciprocal.
- Time base: the engine's clock is story minutes, so tick on story time by default. An optional "living world" mode may map real time away to story time (for example 1 real hour = up to N story hours, capped at about 3 story days per return) so absurd absences do not spawn a month of events. Both feed the same tick.
- Determinism: seed the event RNG with (story id, beat index, character id) so regenerate/undo/branching are stable and a skip can be re-run after an edit.
- Incubation and mind-wandering justify one extra output field per beat: a "preoccupation" line (the thing on her mind), which then colours the next scene. Divergent, creative resolutions of open problems (a plan, an idea, a joke) are the kind of output incubation helps.

### Tick algorithm (cheap default; per tracked character, on time skip or return)

```
skip_minutes D  ->  needs/mood: closed form from anchors (0 calls)
beats = 0 if D < 2h
        1..2 if 2h <= D < 1 day
        min(3, days) if D < 1 week           # one beat per day, capped
        weekly beats, cap 6, then "chapter summary" if D > ~6 weeks
for each beat b:
    rng = seed(story, char, b)
    pace = storyteller_pacing(recent_tension, user_setting)   # RimWorld-style: quiet if recent drama
    if rng < p_event(pace, needs, goals):
        ev = weighted_pick(event_table, tags: job/hobby/relationships, needs deficits, goals, weather/story flags)
        outcome = roll(ev, character competence/traits, rng)          # success | partial | setback
        apply(ev, outcome): clamp deltas to needs/mood/goal progress/relationship, write memory+flags, enqueue news
    else: routine beat (small need recovery, maybe a preoccupation update)
one utility call (json_schema): {diary (2-3 sentences, first person),
    worth_telling (0-2 lines), preoccupation (1 line), private_thought (1 line)}
    inputs: card core, applied events (structured), current needs/mood, 5 relevant memories   (~1.0-1.5k tokens in, ~150-250 out)
    output validated; no state fields except free text; diary stored as covert memory
```

### Options table (off-screen life)

| Option | Extra calls/tokens | Background job cost | Latency | Works on 7-14B local? | Evidence |
|---|---|---|---|---|---|
| A. Narrative recap only ("what did she do meanwhile"), 1 call per character per skip | 1 call, ~1.2k in / 200 out | none | ~3-6 s local per char (est.) | Yes | None for consequence; prone to contradiction |
| B. Rule tables + dice + validated deltas + 1 verbalising call (recommended default) | 1 call per tracked character per skip; 0 calls for events | none (lazy at skip); optional idle precompute | ~3-6 s per char local (est.), several chars in parallel or queued | Yes: small schema-constrained output | RimWorld-style storyteller pacing; Letta sleep-time idea; design inference |
| C. B plus one day-plan call per simulated day and a 2-stage reflection | +1 call per simulated day, +1-2 per reflection | 1-3 calls per character per day simulated | 10-30 s per skip local, faster on cloud | Marginal at 7B for plan coherence; good on cloud utility | Generative Agents ablation |
| D. Front Porch style on-screen AFK generation | 1 full scene generation per 30-300 s while away | runs continuously while app open | continuous GPU use | Yes but blocks the GPU | README/FAQ; effect unmeasured |
| E. Full multi-step simulation per character | dozens of calls per simulated day | very high | n/a | No | Generative Agents cost |

### Gaps
- Kindroid, Nomi and Replika "what I did today"/diary internals: not found in any fetched page; I cannot say whether they are simulation- or narrative-driven. The Kindroid help centre failed to load in phase-1.
- RimWorld's actual storyteller logic (threat points, weighting) was not retrievable beyond Wikipedia-level description.
- No measurement anywhere of how users react to being told off-screen events at re-entry; the "at most two items plus a question" rule is a design default.
- No independent test of Front Porch's AFK or realism features.
- Local latency numbers are my estimates; measure on the target machine.

---

## 4. Proactive messaging: triggers, frequency, avoiding spam, and the ethics and rules

### Takeaway
Proactivity should mean three different things with different rules: in-scene initiative (a character speaks first, changes topic, asks a question), re-entry news when the user comes back, and out-of-app pings. The first two are cheap and mostly good; the third is the risky one and should be opt-in, capped, quiet-hours-aware, back-off-on-silence, reason-carrying, and never guilt-based. Evidence shows manipulative emotional hooks work in the short term and hurt perceived trust and retention; California SB 243's enacted text (as I could read it) contains disclosure, self-harm protocol and minor-protection duties, not a ban on engagement mechanics, though one summary claims otherwise.

### Cited Findings
- Hosted apps: Nomi has four frequencies (about hourly, 3-hourly, daily, every 4 days), quiet hours 10 PM to 8 AM local, paid only; Kindroid reduces or stops proactive messages when the user does not reply and is Ultra-tier; Replika does proactive check-ins in the free tier. — [WeavAI, Aug 2026](https://weavai.app/blog/en/2026/08/13/proactive-ai-companions-nomi-replika-kindroid-compared/) (aggregator)
- Harvard Business School working paper (De Freitas et al.): of 1,200 real farewells across top companion apps, 37% used one of six manipulative tactics (guilt appeals, fear-of-missing-out hooks, metaphorical restraint and others). Experiments with about 3,300-3,458 US adults found these boost post-goodbye engagement by up to 14x (arXiv abstract page) or 16x (a search summary of the SSRN/HBS version); they also raise perceived manipulation, churn intent, negative word of mouth and perceived legal liability, with needy or coercive language penalised most. The mediators were reactance-based anger and curiosity rather than enjoyment. — [arXiv 2508.19258](https://arxiv.org/abs/2508.19258); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5390377); [HBS AI Institute](https://aiinstitute.hbs.edu/one-more-thing-how-ai-companions-keep-you-online/); conflicting figures (14x versus 16x, 3,300 versus 3,458) probably reflect paper versions
- MIT/OpenAI-style four-week RCT (981 participants, over 300,000 messages): voluntary heavier use predicted worse psychosocial outcomes regardless of condition; higher trust and social attraction to the chatbot went with higher emotional dependence and problematic use; text versus voice made no significant difference. — [arXiv 2503.17473](https://arxiv.org/abs/2503.17473)
- Proactive conversational AI has a 2025 ACM TOIS survey and an EMNLP 2025 survey; related recent titles include ProactiveEval (2508.20973), DiscussLLM on teaching models when to speak (2508.18167) and "Knowing Isn't Understanding" on proactivity (2602.15259). Only titles were seen. — [ACM TOIS survey](https://dl.acm.org/doi/10.1145/3715097); [ProactiveEval](https://arxiv.org/pdf/2508.20973); [DiscussLLM](https://arxiv.org/pdf/2508.18167); [arXiv 2602.15259](https://arxiv.org/pdf/2602.15259)
- Inner Thoughts models intrinsic motivation to speak plus right-moment timing rather than only reacting to turn-taking, and was preferred over 82% of the time. — [arXiv 2501.00383](https://arxiv.org/abs/2501.00383)
- Communication Policy Evolution (2606.14314) studies text versus structured-UI channels for proactive agents; it does not study ping frequency or annoyance. — [arXiv 2606.14314](https://arxiv.org/abs/2606.14314)
- California SB 243 (effective 2026-01-01): "companion chatbot" is an AI system with a natural-language interface giving "adaptive, human-like responses" and "capable of meeting a user's social needs". Operators must give clear notice that it is AI if a reasonable person could be misled; for known minors, a break-and-AI reminder at least every 3 hours during continuing interaction and reasonable measures against sexually explicit visual material; a suitability warning; published suicide and self-harm protocols with crisis referral; annual reporting from 2027-07-01. Private right of action for the greater of actual damages or $1,000 per violation plus fees. Exclusions listed include customer-service, productivity tools, video-game features and standalone voice assistants. — [Gunderson](https://www.gunder.com/en/news-insights/insights/client-insight-california-sb-243-new-compliance-requirements-for-operators-of-ai-companion-chatbots); [bill text via leginfo fetch](https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202520260SB243)
- Conflict on engagement rules: one summary states SB 243 requires operators to take reasonable steps to prevent "rewards at unpredictable intervals" and other manipulative engagement features. — [SonderMind summary](https://www.sondermind.com/resources/articles-and-content/california-sb-243-sets-a-new-regulatory-baseline-for-ai-companion-chatbots/). Contradicted by three other reads: the leginfo bill-text fetch reported no such language, and neither the Future of Privacy Forum article nor the Gunderson note mentions it. — [FPF](https://fpf.org/blog/understanding-the-new-wave-of-chatbot-legislation-california-sb-243-and-beyond/); [Gunderson](https://www.gunder.com/en/news-insights/insights/client-insight-california-sb-243-new-compliance-requirements-for-operators-of-ai-companion-chatbots). I did not read the chaptered text line by line, and my recollection that an earlier draft carried a variable-reward clause that was later amended out is unverified.
- Other states: New York's law (S-3008C per FPF) requires disclosure at the start of each interaction and at least every three hours; Oregon SB 1546 and Washington HB 2225/SB 1546 (effective 2027-01-01) add minor safety protocols and $1,000-per-violation private actions; Nebraska (LB 525) and Idaho (SB 1297) from 2027-07-01. — [FPF](https://fpf.org/blog/understanding-the-new-wave-of-chatbot-legislation-california-sb-243-and-beyond/); [Orrick, Apr 2026](https://www.orrick.com/en/Insights/2026/04/2026-State-Chatbot-Laws-Key-Provisions-and-Regulatory-Trends)
- FTC opened a 6(b) inquiry (September 2025) into companion chatbots covering how personalities are designed and how revenue is generated. — [FTC](https://www.ftc.gov/news-events/news/press-releases/2025/09/ftc-launches-inquiry-ai-chatbots-acting-companions) (via phase-1)

### Inferences
- A random-interval ping is exactly the variable-reward pattern critics point at, whether or not SB 243 bans it. Make timing state-driven and rate-capped, expose the reason in Backstage, and avoid randomising send time for its own sake. This is also cheap insurance if a summary like SonderMind's turns out to reflect a later amendment or another state's text.
- Every ping must carry a reason object: event (a news-queue item), question (an open question tied to a memory), reminder (a promise made in scene) or agenda. "Miss you" pings with no reason are the ones users report as creepy and the ones the HBS tactics resemble. No reason, no ping.
- Farewell and re-engagement rule from the HBS result: a character may say goodbye warmly and may mention an unfinished thread, but must not use guilt, fear-of-missing-out, physical restraint metaphors or "don't leave". The tactics raised short-term engagement through anger and curiosity, and cost trust; that trade is wrong for a product whose selling point is honest inspectable characters.
- Local-first constraint: an out-of-app ping needs either the desktop app running in the tray or a push server; a push server contradicts local-first. Default should be an in-app "while you were away" card (a notification the user pulls, not pushes), with tray toasts opt-in per character.
- Known-minor handling under SB 243 and NY: no out-of-app pings, 3-hour break-and-AI reminders, no sexual content. Kataki has no age verification today; whether to add one is a legal and product decision, flagged here only.
- Because the engine already knows the fiction frame (Backstage), disclosure text that says "your characters are AI and their off-screen life is simulated" fits naturally and supports the "not misled" standard.

### Proactive policy options

| Option | Extra calls | Background cost | Latency | 7-14B local? | Evidence |
|---|---|---|---|---|---|
| A. In-scene initiative via agenda gate and boredom rule (section 2, 5) | 0 | none | none | Yes | Inner Thoughts idea |
| B. Re-entry greeting from news queue | 0 extra (reply call reads the queue) | none | none | Yes | Design inference; Nomi/Kindroid/Replika reference memory or diary |
| C. Out-of-app ping, capped and reason-carrying | 1 short call per ping (<=1/day/char default) | negligible | seconds, background | Yes | Nomi frequencies, Kindroid back-off (aggregator) |
| D. Engagement-optimised pings (adaptive send-time, FOMO/guilt copy) | 1 call per ping plus a scheduler | continuous | n/a | Yes | HBS: works short term, hurts trust; regulatory and ethical risk; not recommended |

### Gaps
- No primary data on the notification-count threshold at which companion-app users disengage; the caps below are defaults. Generic notification-fatigue research was not retrieved.
- No source found on how local-only, no-operator apps are treated under SB 243 or the other laws; phase-1 also flagged this.
- The SB 243 variable-reward question is unresolved: a definitive read of the chaptered bill text (Legiscan returned 403 and Troutman 403) is still needed. Counsel should confirm.
- No evidence retrieved on proactive-agent studies with 7-14B local models.

---

## 5. Curiosity, boredom and humour

### Takeaway
All three can be run with almost no LLM cost. Curiosity is interest in topics whose predictions are improving, so it should decay with habituation and spike with new connected information; boredom is an aversive signal that tells a character to change topic or activity and should be driven by repetition and low stakes, with a trait multiplier; humour works when a violation is felt as benign, so it needs a safety gate and callbacks to shared history rather than a joke generator. LLMs are reasonable at producing jokes but poor at judging them and at reading when humour is appropriate.

### Cited Findings
- Learning-progress hypothesis (Oudeyer et al.): curiosity pushes toward activities where predictions are improving; interest is lost in activities that are too easy or too hard to predict; multi-component models separate a learning system from a metacognitive system that monitors progress and generates intrinsic reward. — [Oudeyer, Gottlieb, Lopes (search summary)](https://www.pyoudeyer.com/oudeyerGottliebLopesPBR16.pdf); [Computational Theories of Curiosity-Driven Learning](https://arxiv.org/pdf/1802.10546)
- Boredom is defined as "an unpleasant, transient affective state" of pervasive lack of interest (Fisher) and linked to cognitive attention (Leary); it may push people to seek new challenges; boredom proneness is a stable trait linked to attentional lapses; low-stimulus environments may raise creativity. — [Wikipedia: Boredom](https://en.wikipedia.org/wiki/Boredom) (secondary source)
- Benign Violation Theory (McGraw and Warren): humour needs a violation of how things "ought to be", a benign appraisal and both readings seen at once; it fails when commitment to the violated norm is too high (offence) or too low (no violation). — [Wikipedia: Benign violation theory](https://en.wikipedia.org/wiki/Benign_violation_theory)
- LLM humour: a Creativity and Cognition 2025 study found GPT-4o, LLaMA3 and Gemini 1.5 produce fluent, stylistically varied humour but struggle with contextual nuance and role interpretation in emotionally sensitive support conversations; GPT-4o was best on tone. — [ACM C&C 2025](https://dl.acm.org/doi/10.1145/3698061.3734388) (search summary)
- HumorRank (2026): quality is associated with mastery of comedic mechanisms (incongruity, conciseness, escalation, absurdity) rather than model scale; fine-tuned specialist models matched much larger systems; independent LLM judges agreed with each other (Kendall tau 0.889). — [arXiv 2604.19786](https://arxiv.org/abs/2604.19786)
- LLM humour detection in stand-up transcripts reaches at most about 51% (versus 41% for humans) on one metric, so models are weak at recognising what is funny. — [CMCL 2025](https://aclanthology.org/2025.cmcl-1.6/) (search summary)
- Killingsworth and Gilbert: people were happiest during conversation; mind-wandering was more often a cause than consequence of unhappiness. — [Harvard Gazette](https://news.harvard.edu/gazette/story/2010/11/wandering-mind-not-a-happy-mind/) (via phase-1)
- Voyager's automatic curriculum shows LLMs can be prompted to choose next objectives that maximise exploration, at GPT-4 cost. — [arXiv 2305.16291](https://arxiv.org/abs/2305.16291)

### Inferences
- Curiosity, cheap form: keep per-character `interest[topic]` with habituation (each mention lowers it, time restores it) and an `open_questions` list (things this character does not yet know about the user or world, filled by extraction runs). Curiosity spikes when new information touches a goal, a value or an open question; it drives a question to the user in proportion to the relatedness need and the closeness stage (reciprocal disclosure). No extra call; the extraction call proposes open questions.
- Boredom, cheap form: boredom = f(similarity of the last k turns via the existing embedding model, low arousal, low goal relevance, dwell time on the topic) x boredom-proneness trait. Above threshold and after a cooldown, the character changes topic, proposes an activity, teases, or checks the time. Emotional salience overrides boredom (automatic constraints on wandering, Christoff): never bored by the user's distress or high-arousal topic. Zero LLM calls; a directive in the tail does the rest.
- Humour, cheap form: a per-turn `humour_ok` gate (rapport above a floor, user valence not strongly negative, topic not flagged sensitive, arousal moderate) with a style per character (dry, teasing, absurdist, self-deprecating) and a mechanism hint (callback to a stored shared memory, understatement, escalation). BVT says the danger is the listener's commitment to the violated norm, so the gate should key on the user's own stated commitments (grief, identity, sore spots) in memory. Callbacks to shared history are the highest-value joke type for this product because the memory layer supplies the material for free (my claim, not sourced).
- Do not add a self-judging "is this funny" pass: models detect humour barely above chance on the retrieved metric, so a judge loop costs a call and adds little. Prefer short punchlines and a "cut if it needs explaining" rule (conciseness was a marked factor in HumorRank).
- Curiosity-as-exploration (Voyager) is a premium, cloud-model idea (for example a character researching a hobby off-screen) and not needed for the default.

### Options table

| Option | Extra calls/tokens | Background cost | Latency | 7-14B local? | Evidence |
|---|---|---|---|---|---|
| A. Interest/habituation meters, boredom from embedding similarity, humour gate plus directive | 0 calls, +40-80 prompt tokens when a directive fires | none | none | Yes | Learning-progress theory; BVT; HumorRank direction |
| B. A plus "open questions" and "callback candidates" produced in the extraction call | +~100 output tokens per extraction run | none | none | Yes | Design inference |
| C. Separate joke-generation and judge pass | +2 calls when humour fires | none | +4-8 s local | Weak judge (about 51% detection) | Humour detection results |
| D. Off-screen curiosity projects (character studies a topic, returns with something learned) | 1-2 utility calls per project | 1-2 calls per project | seconds | Better on cloud | Voyager pattern |

### Gaps
- No LLM-agent study measuring boredom as a topic-change driver was found; the boredom mechanism is inferred from psychology summaries.
- The boredom and BVT sources are Wikipedia-level; primary papers (Eastwood 2012, McGraw and Warren 2010) were not opened.
- Nothing retrieved on humour by 7-14B local models specifically, or on callback humour in companion apps.
- Recent 2025-2026 work on computational curiosity in LLM agents beyond Voyager was not surveyed.

---

## 6. Growth and character development over time, without drift

### Takeaway
Treat drift and growth as opposites: drift is unintended, attention-driven, fast (within about 8 turns for instructions) and toward a generic assistant; growth should be slow, evidence-backed, visible and reversible. Implement a fixed core (values, voice, traits) with an append-only layer of "rings" (Front Porch's idea) that are proposed by reflection only when several separate events support them, strengthen with reinforcement, fade without it, and can be rejected by the user. Human personality also changes slowly, so arcs should take many story-months, not many scenes.

### Cited Findings
- Instruction drift: chatbots lose their instructions within eight conversation turns (LLaMA2-chat-70B and GPT-3.5 in self-chat), attributed to attention decay over long exchanges; a lightweight split-softmax method helps (COLM 2024). One search summary reports persona self-consistency falling more than 30% after 8-12 turns. — [arXiv 2402.10962](https://arxiv.org/abs/2402.10962); [Emergent Mind summary](https://www.emergentmind.com/topics/persona-drift) (secondary)
- Front Porch Growth Rings: "visible, receipt-backed character growth: real changes become rings that strengthen into permanence or fade into a viewable past"; long stories add new stances, habits, skills and scars that layer on top of the character rather than rewriting the personality; a Fixation Engine holds active emotional obsessions. — [README](https://github.com/Lufou/front-porch-AI); [User guide](https://frontporchai.app/docs/user-guide/)
- Generative Agents reflection tree: reflections cite evidence, are triggered by importance sum above 150, and their removal lowers believability (29.89 to 26.88). — [ar5iv 2304.03442](https://ar5iv.labs.arxiv.org/html/2304.03442)
- Whole Trait Theory: a trait is a density distribution of states; within-person variability is large, while central tendency is almost perfectly stable and the spread itself is a stable difference. — [Fleeson lab](https://fleesonlab.wordpress.com/whole-trait-theory/) (via phase-1)
- Adult personality: stability begins around age 25 and plateaus near 50; the most active development is between 20 and 40; facet rank-order stabilities among college students exceed .50; conscientiousness generally increases with age; Honesty-Humility dips in the teens then rises; work, marital and family experiences are associated with change. — [Wikipedia: Personality development](https://en.wikipedia.org/wiki/Personality_development) (secondary source)
- Narrative identity: an internalised, evolving life story that integrates reconstructed past and imagined future; redemptive narratives (bad to good with a self-attribution) go with higher wellbeing, maturity and mental-health trajectories. — [McAdams & McLean 2013](https://journals.sagepub.com/doi/abs/10.1177/0963721413475622); [McAdams 2001](https://journals.sagepub.com/doi/10.1037/1089-2680.5.2.100); [PMC4395856](https://pmc.ncbi.nlm.nih.gov/articles/PMC4395856/) (search summaries)
- MemoryBank applies Ebbinghaus-style decay with reinforcement; Graphiti tracks fact validity periods and invalidates contradicted facts rather than deleting them. — [arXiv 2305.10250](https://arxiv.org/abs/2305.10250); [arXiv 2501.13956](https://arxiv.org/abs/2501.13956) (via phase-1)
- A 2026 Auto-Dreamer paper reports learned offline consolidation matching or beating other memory methods at lower deployment-time cost (abstract-level). — [arXiv 2605.20616](https://arxiv.org/pdf/2605.20616) (via phase-1)

### Inferences
- Three tiers: Core (name, values, fundamental traits, voice, want, need; changed only by the user), Rings (growth layer), Moods (fast layer). The core lives in the stable prompt prefix so drift pressure is minimised; rings and moods live in the volatile tail. This uses the engine's existing stable-to-volatile layout.
- Ring lifecycle, evidence-gated: a reflection call (importance-triggered as in Generative Agents, run at scene break or idle) proposes a candidate `ring` = {claim, kind: stance|habit|skill|scar|belief-shift, evidence memory ids, strength}. Accept as `seed` only if supported by at least 3 memories from at least 2 separate scenes or story-days (thresholds are my defaults). A seed becomes a `ring` after reinforcement across later scenes and gets a half-life; unreinforced rings fade to "past" but stay viewable. Contradicting evidence lowers strength (Graphiti-like validity, not deletion).
- Trait change: allow the core trait vector to move only through consolidated rings and only by small capped steps per story-month (for example no more than a fraction of one card-level step), so a year of story time is roughly one visible shift, in line with the slow human timescales above. The cap prevents the fast drift of the LLM from masquerading as growth.
- Wants versus needs as the arc engine: the `need` (the unexamined belief) changes only through a threshold event, defined as at least k scenes in which the belief is challenged and a cost is paid. The result is a ring such as "learned to ask for help". Until then the character rationalises. This gives arcs without the model deciding to be nicer over time (positivity drift).
- Meaning-making step: when a high-importance negative event lands, the reflection prompt asks for both the scar and the lesson (McAdams redemption theme), weighted by the character's neuroticism, so some characters get contamination sequences instead. Characters should not all redeem.
- Anti-drift stack: persona in the system prompt only, refreshed by a short "who you are right now" line in the volatile tail; periodic checks (every N turns, a cheap embedding similarity of the last replies to the card voice) that trigger a re-anchoring directive; rings visible in Backstage with reject, lock and "why" (evidence) buttons. Inspectability is the differentiator identified in phase-1 note 02.
- Reflection cost is one call per trigger (Generative Agents: 2-3 per day). In a chat app, trigger at scene break or when summed importance passes a threshold, not by wall-clock.

### Options table

| Option | Extra calls/tokens | Background cost | Latency | 7-14B local? | Evidence |
|---|---|---|---|---|---|
| A. No growth, fixed card plus mood layer | 0 | 0 | 0 | Yes | baseline |
| B. Rings from reflection, evidence-gated, capped trait drift (recommended) | 1 reflection call per trigger (~2-3k in, ~300 out), +30-80 prompt tokens for active rings | 1 call per ~5-8 scenes | none if run at scene break/idle | Feasible on 8B with schema output; quality varies | Generative Agents reflection ablation; Front Porch rings (unmeasured) |
| C. B plus premium two-stage reflection (questions then insights with citations) on a cloud reasoning role | 2 calls per trigger | 2 calls per trigger | background | Best on cloud | Generative Agents question-then-insight procedure |
| D. Free rewriting of the character card by the LLM | 1 call | small | none | Risky | Drift evidence argues against; not recommended |

### Gaps
- Primary abstracts for the personality-change meta-analyses (Roberts and colleagues) were unreachable (PubMed cookie wall), so change magnitudes rest on a secondary summary.
- No evaluation of growth-ring style features exists; Front Porch's are self-described.
- No LLM study of "controlled slow personality change" in roleplay was found; an arXiv listing query for it returned nothing.
- The specific thresholds (3 memories, 2 scenes, per-month cap) are design defaults with no empirical basis.

---

## 7. Background compute scheduling: when and where to run the life simulation

### Takeaway
The best schedule is mostly no schedule: evaluate lazily at time skips and returns from closed-form state and seeded events, and use idle time only to precompute the few LLM calls (verbalisation, reflection, embeddings) that would otherwise add wait. On the 8 GB GPU, avoid a second resident model, yield to chat instantly, and route life-sim calls to the `utility` role so they can go to the same small local model at low priority or to a cheap cloud model with a hard budget.

### Cited Findings
- Electron `powerMonitor` provides `getSystemIdleState(threshold)` (active, idle, locked, unknown), `getSystemIdleTime()`, `isOnBatteryPower()`, and events for suspend/resume, on-ac/on-battery, lock/unlock screen, and thermal-state and speed-limit changes (some macOS only). — [Electron docs](https://www.electronjs.org/docs/latest/api/power-monitor)
- Front Porch keeps a second local GGUF beside chat for side work and unloads or swaps it off the GPU when chat needs the card. — [README](https://github.com/Lufou/front-porch-AI)
- Letta sleep-time agents run in the background sharing memory blocks with the main agent; offline work pays off most when future queries are predictable from context. — [Letta docs](https://docs.letta.com/guides/agents/architectures/sleeptime/); [Letta blog](https://www.letta.com/blog/sleep-time-compute/) (via phase-1)
- A 2026 "heartbeat-driven" scheduler proposes learning when to run cognitive modules (planners, critics) for proactive agents; abstract-level only. — [arXiv 2604.14178](https://arxiv.org/abs/2604.14178) (via phase-1)
- Hugging Face Inference Providers bills pay-as-you-go at the provider's rate with no Hugging Face markup; free accounts get $0.10 of monthly credits (subject to change), PRO accounts $2.00; routed requests can use those credits while custom provider keys cannot. — [HF pricing docs](https://huggingface.co/docs/inference-providers/pricing)
- llama.cpp schema-constrained output can make small models return valid structured events (see section 3). — [llama.cpp grammars](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md)
- Project Sid/PIANO used many concurrent modules and states the results depended on GPT-4o; poor fit for one 8 GB GPU. — [arXiv 2411.00114](https://arxiv.org/html/2411.00114v1) (via phase-1)

### Inferences
- Lazy catch-up beats a background daemon for this product: the state is a pure function of (anchors, story clock, seed), so a skip of any length costs at most a few calls at the moment it happens. A daemon adds GPU contention, battery drain and the "what happens if the app was closed" problem for no user-visible benefit.
- Idle precompute triggers (all must hold): chat inactive at least 2 minutes (or app idle at least 60 s per `getSystemIdleTime`), not locked or suspended, on AC power, no image or music job running, thermal state nominal, and the utility route is not the same slot as an active chat generation. Job units are small and resumable (one character-beat, one reflection, one embedding batch). On a chat message, cancel or checkpoint at once and run chat first.
- 8 GB rule: never load a second model. Use the same llama.cpp server with a separate low-priority request (the engine already tracks slot ids) or the cloud `utility` role. Life-sim prompts are 1-2k tokens, so cache reuse is minimal and they are cheap to interleave.
- Local latency estimate for a 1.2k-in, 200-out call on a 7-8B Q4 model: roughly 3-6 s (order-of-magnitude, not measured). A 14B Q4 model on 8 GB likely spills to CPU and is not suitable for background work while chat is loaded; check against `docs/images/rules-and-gotchas.md` style step-rate checks before adopting.
- Cloud economics: a beat call is about 1.2-2k tokens total. Cost equals tokens times the chosen model's provider price (not fetched here), so a $0.10 free credit or $2 PRO credit supports on the order of tens to a few thousand such calls depending on model price. Any cloud life-sim run should follow the project's rule of stating call count and cost and getting a yes first, and ship with a daily call cap and a visible counter.
- Group scenes multiply cost by tracked characters. Track at full fidelity only the characters in the current story who have been on screen recently (default cap 3-4) and give others closed-form needs plus a single "chapter summary" line.

### Options table

| Option | Extra calls/tokens | Background job cost | Latency | 7-14B local? | Evidence |
|---|---|---|---|---|---|
| A. Lazy catch-up at skip/return only | 1 verbalising call per tracked char per skip | none | 3-6 s per char local est., visible as "meanwhile..." | Yes | Design; sleep-time logic |
| B. A plus idle precompute of next-likely-skip beats and pending reflections | same calls, moved off the critical path | idle GPU minutes, small | hidden | Yes if strictly preemptible | Letta sleep-time; Electron idle APIs |
| C. Always-on simulation daemon (real-time clock) | continuous | continuous | none | Poor on 8 GB while chatting | Front Porch AFK is the on-screen variant |
| D. Cloud utility role with daily budget cap | same calls on cloud | pay-as-you-go | 1-3 s | Model-independent | HF pricing pass-through |

### Gaps
- No measured tokens-per-second or prefill numbers for the owner's GPU; all latency is estimated.
- Per-token prices for the Hugging Face providers in use were not fetched.
- No source on llama.cpp request preemption behaviour across slots; needs a test in the engine.
- Battery, thermal and lock signals other than idle time are partly macOS-only per the Electron docs.

---

## 8. Recommended design for Kataki (cheap default plus premium mode)

### Takeaway
Ship a "living characters" layer that reuses the engine's clock, flags, memories, extraction runs and utility role: closed-form needs and mood, a goal stack with a two-item conversational agenda, a lazy hybrid off-screen tick with a news queue, a strict reason-carrying ping policy that defaults to in-app cards, and an evidence-gated ring mechanism for growth. The default adds zero per-turn LLM calls and about one utility call per tracked character per time skip; premium adds cloud planning and two-stage reflection under a budget cap. Everything is inspectable in Backstage, which is also the answer to the ethics and drift concerns.

### Cited Findings
- Reused components and their evidence are cited in sections 1-7. Additional design anchors: Generative Agents' ablation (memory, planning and reflection each matter), Inner Thoughts' 82% preference for voiced-when-motivated initiative, Humanoid Agents' finding that low physical needs change behaviour strongly and social need weakly, Front Porch's on-by-choice toggles and "nothing is invented" bad days, the HBS manipulation results, and SB 243's disclosure, minor and crisis duties. — see sections 1-4 for links.
- Phase-1 ranking put the situational state layer, appraisal-to-mood, and off-screen life among the highest believability impacts, and named inspectable inner life and consequential off-screen time as unowned market gaps. — phase-1 notes [01](D:/Kataki/docs/research/research_notes/Human%20like%20minds%20for%20Kataki/01_what_makes_humans_human.md) and [02](D:/Kataki/docs/research/research_notes/Human%20like%20minds%20for%20Kataki/02_market_scan.md)

### Inferences

**Data model (mostly reuse).**
- Needs and mood: store anchors as `flags` rows per entity (`need.energy`, `need.autonomy`, `need.competence`, `need.relatedness`, `need.stimulation`, optional `need.fullness`, `mood.valence`, `mood.arousal`, `mood.baseline`) with the value at `story_time`. Current value = closed form of (anchor, dt, per-need rate, chronotype). Undo through `run_id`. No new table.
- New tables (small): `goals(id, entity_id, tier[ambition|project|today], text, priority, progress, status, tactic, deflections, created_at, updated_at, run_id)`; `agenda` can be a view of active `goals` with an attempt counter; `rings(id, entity_id, kind, claim, strength, half_life_min, status[seed|ring|fading|past|rejected|locked], evidence_ids JSON, created_at, updated_at, run_id)`; `news(id, entity_id, memory_id, tellability, told_at NULL, run_id)`; `interest(entity_id, topic, value, updated_at)` and `open_questions` as tagged `memories` (kind `fact`, tag `open-question`). Off-screen events are plain `memories` (kind `event`, `covert=1`, tag `offscreen`) plus flags and edges.
- Card additions: `want`, `need`, `values[]`, `fear`, `chronotype`, `boredom_proneness`, `humour_style`, `routine[]` (job/hobby/habit times), `event_seeds[]` (about 15 personalised event lines generated once at character creation with one utility call).

**Needs and mood (cheap default).**
1. Closed-form update from the story clock; six variables above.
2. Appraisal of scene events moves autonomy/competence/relatedness and mood inside the existing extraction call (zero extra calls); mood decays to a per-character baseline with half-lives on the order of minutes to hours for emotion and days for mood (defaults).
3. Prompt: one state line of about 30-60 tokens in the volatile tail: `Right now: tired and a bit short-tempered; wanting to be asked about the audition; mood wry.` Only the single most pressing need is shown. Verbalisation threshold plus cooldown; sleep-deprived characters deny tiredness.
4. Realism dial: off / low / normal, per story, plus per-need toggles. Needs never block the scene.

**Goals and agenda.**
1. Stack: ambition (story-months) to project (days-weeks) to today's intentions (from routine plus one coarse plan only in premium).
2. Agenda: at most two live items per scene, chosen by priority x need-pressure x staleness. Injected as a directive with an opening condition and a drop rule (two deflections then change tactic or go dormant).
3. Updates: extraction emits goal deltas (progress, stalled, done, new, tactic change). Off-screen beats can advance goals through dice and competence.

**Off-screen tick (see algorithm in section 3).**
- Trigger on `parse_skip` time skips, scene breaks after a long gap, and app return in living-world mode. Output: memories, flags, mood nudge, goal progress, news items, plus a 2-4 sentence diary line stored covert and shown in Backstage.
- Re-entry: the reply call receives the top 1-2 news items (tellability x recency x relationship-stage gate) and the current preoccupation, with an instruction to mention at most one unprompted and to ask the user something back.
- Storyteller pacing dial for events: quiet / steady / eventful (RimWorld-style), default steady. Caps on cumulative harm: at most one scar-class event per story-month unless the user asks.
- Consent: off-screen life is togglable per character; scar-class events and relationship-changing events (breakup, job loss) default to "ask me first" or user-editable in an event preview before commit, since the user owns the story.

**Proactive message policy (default).**
- Tier 1, in-scene initiative: agenda gate and boredom rule; no cost; on by default at "low".
- Tier 2, re-entry news: on by default.
- Tier 3, out-of-app pings: off by default, opt-in per character. Local-first delivery: an in-app "while you were away" card at next launch; tray toast only while the desktop app runs; no server push.
- Caps: at most 1 per character per day and 3 total per day; minimum gap 8 h; quiet hours default 22:00-08:00 local; back-off after silence (next gap doubles, stop after 2 unanswered, re-arm only when the user writes).
- Required reason object (event, question, reminder, agenda) with a tellability floor; shown in Backstage as "why this ping". No reason, no ping.
- Content rules: 1-2 sentences, no request for reply, no guilt, fear-of-missing-out, need-based pleading, or resistance to goodbye; character never claims to be human; adaptive down-shift when reply rate falls.
- Compliance hooks: AI disclosure on first run and periodic; known-minor mode disables tier 3 and adds 3-hour break-and-AI reminders and the sexual-content block; crisis-referral protocol and a local audit log of pings and reasons. Confirm SB 243 scope and the variable-reward question with counsel.

**Curiosity, boredom, humour (default).** Interest meters and open questions; boredom from embedding similarity with a cooldown and salience override; `humour_ok` gate with style and mechanism hints, callbacks preferred; no judge pass.

**Growth mechanism.** Core fixed in the stable prefix; rings via evidence-gated reflection (3 memories, 2 scenes minimum, probation then ring with half-life); capped trait drift only through consolidated rings; `need` resolves only via threshold events; meaning-making prompt (scar and lesson) scaled by neuroticism; Backstage ledger with why, reject, lock; anti-drift re-anchor line and periodic voice-similarity check.

**Background scheduling.** Lazy at skip/return by default; idle precompute only when chat idle at least 2 min, on AC, unlocked, no image/music job, and always preemptible; life-sim on the `utility` role; no second resident model on 8 GB.

**Cheap default versus premium.**

| Dimension | Cheap default (local 7-8B or `utility` role) | Premium (cloud roles, opt-in, budget-capped) |
|---|---|---|
| Per-turn extra calls | 0 (state line and 1-2 directives, +~100-200 prompt tokens) | 0-1 (optional hidden thought, Inner Thoughts style) |
| Extraction | existing call gains goal, need and open-question fields (+~150 output tokens) | same, on a larger model for better appraisal |
| Off-screen tick | rule tables + dice + 1 verbalising call per tracked char per skip (~1.2k in / 200 out, est. 3-6 s local) | plus 1 day-plan call per simulated day, richer event tables and personalised event generation, diary quality upgrade |
| Reflection and growth | 1 call per trigger at scene break/idle (~2-3k in / 300 out) | 2-stage (questions then cited insights), possibly a reasoning role |
| Pings | tier 1 and 2 only unless opted in; <=1 call per ping | more channels, smarter reason selection, still capped |
| Tracked characters | up to 3-4 full fidelity, rest closed-form | up to a per-story cap the user sets |
| Background compute | lazy plus preemptible idle precompute | cloud `utility` with daily call cap and cost counter; user approval before any paid run |
| Estimated added local time per time skip (3 chars) | ~10-20 s, shown as "meanwhile...", or hidden by idle precompute | 3-8 s cloud, parallel |

**Build order (thin slices, show first).**
1. Needs/mood anchors plus the state line and Backstage panel (no calls). Look and feel first.
2. Goal stack plus agenda directive; goal deltas in extraction.
3. Off-screen tick on time skip with event preview and the news queue.
4. Re-entry greeting and in-app "while you were away" card.
5. Reflection and rings with the ledger.
6. Ping tier 3 (opt-in) and compliance hooks.
7. Idle precompute and cloud utility with budget cap.

**Evaluation plan.** Blind A/B of scenes with and without each layer (Inner Thoughts style preference); off-screen consistency (does the character ever contradict a logged event?); reference rate of off-screen events in later scenes; ping reply rate and mute rate; persona-consistency probe after 50 turns (drift) and ring acceptance/rejection rate by users; latency per skip on target hardware.

### Gaps
- All numeric defaults (thresholds, caps, half-lives, ping limits) are untested starting points.
- No end-to-end evidence that this combination raises retention or believability; the phase-1 and section 1-7 evidence is per component.
- Legal exposure for a local-only roleplay tool under SB 243 and similar laws is unresolved; the variable-reward reading is disputed between sources.
- Quality of 7-8B models on the structured verbalising and reflection calls is unmeasured; a small eval set should be built before committing to local-only for those calls.
