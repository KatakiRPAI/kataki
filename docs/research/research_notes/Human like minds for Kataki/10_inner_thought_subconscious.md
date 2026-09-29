# Inner thought, subconscious / background thinking, and fast-vs-slow cognition for Kataki characters

Scope: implementation-grade note for one aspect of the "human-like minds" research. Phase-1 notes (01, 03, 04) already cover the science summary, Inner Thoughts at abstract level, RoleThink/MIRROR at abstract level, Letta sleep-time at abstract level, SOFAI-LM, and the "thinking mode hurt villains" result. This note does not repeat those; it adds mechanism-level detail (pipelines, heuristics, formats, trigger rules), existing implementations, and cost/latency per option.

Conventions: "Cited Findings" carry a URL. Anything I derived or estimated is under "Inferences" and marked (est.) where numbers are mine. Web search budget ran out during this task, so a few leads are listed under Gaps as un-fetched pointers. No r/SillyTavernAI or r/LocalLLaMA thread was retrieved; practitioner evidence here is limited to the Stepped Thinking repo/wiki and Hugging Face model cards.

Kataki-side facts that matter (from repo specs, not web): the engine already streams a `thought` SSE event separate from `token`, routes `reasoning_content` and inline `<think>` tags to a collapsible thoughts block, never puts thoughts into rendered prompts/history/cached prefix, and has `rp`, `utility` and `reasoning` model roles plus scene-close consolidation and cadence runs — [D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md](file:///D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md). The peek/inner-thought channel therefore already has a transport and a UI slot; what is missing is a generator for it on standard (non-reasoning) models.

---

## 1. Hidden "thinking before speaking": how Inner Thoughts, MIRROR/RoleThink, Role-Aware Reasoning and SillyTavern extensions actually work, and the best format for a short character-voiced thought

### Takeaway
The best-evidenced recipe is a short (about 15-25 words), first-person, stimulus-grounded thought produced by a separate structured step and then used as private conditioning for the reply. Long generic reasoning traces are the version that hurts roleplay (attention diversion, style drift). Human-preference evidence exists for the thought-then-speak pattern (Inner Thoughts), but it is thin on ablations and untested on 7-14B models.

### Cited Findings
- Inner Thoughts pipeline has five stages: Trigger (fires on each new message, and after 10 s of silence), Memory Retrieval, Thought Formation, Thought Evaluation, Participation. — [arXiv 2501.00383 (HTML)](https://arxiv.org/html/2501.00383)
- Memory retrieval uses saliency = max(sim(memory, interpreted utterance), sim(memory, utterance)) x memory weight x decay, decay rate 0.95, keep memories above a 0.3 threshold. — [arXiv 2501.00383 (HTML)](https://arxiv.org/html/2501.00383)
- Thought formation is explicitly dual-process: System 1 thoughts are quick and based on the latest utterances; System 2 thoughts are deliberate and grounded in retrieved memory stimuli. Thoughts are under 15 words and annotated with the stimulus that caused them. The study configuration produced 1 System-1 + 2 System-2 thoughts per batch. — [arXiv 2501.00383 (HTML)](https://arxiv.org/html/2501.00383)
- Thought evaluation: an LLM gives each thought a 1-5 intrinsic-motivation score using structured CoT that lists two positive and two negative factors; the final score is a probability-weighted sum over top-5 sampled ratings, multiplied by a silence-growth factor (1.02 per unit). The eight heuristics from the 24-person think-aloud study, by mention count: Relevance 77, Information Gap 33, Balance 33, Dynamics 30, Coherence 30, Expected Impact 23, Originality 16, Urgency 14. — [arXiv 2501.00383 (HTML)](https://arxiv.org/html/2501.00383)
- Participation rule: open turns need score >= imThreshold; allocated turns use the highest-rated thought; overriding someone else's turn needs score >= interruptThreshold. Models used: GPT-3.5, GPT-4-turbo, GPT-4o. — [arXiv 2501.00383 (HTML)](https://arxiv.org/html/2501.00383)
- Inner Thoughts evaluation: 100 simulated conversations, 8 PersonaChat personas, 4 participants, 15 turns, 10 human raters on 7 metrics, 82% preference. Chatbot study "Swimmy" had only 12 participants. Authors admit: hyperparameters chosen empirically without formal ablation, baseline only next-speaker prediction, computational cost not quantified, scalability of many concurrent LLM calls is a concern. — [arXiv 2501.00383 (HTML)](https://arxiv.org/html/2501.00383)
- Code/repo: the project repo I could fetch (github.com/xybruceliu/inner_thoughts) contains only the static project webpage, not the implementation; the paper says a playground and Swimmy bot were open-sourced via the project site. I could not confirm a runnable code repo. — [GitHub xybruceliu/inner_thoughts](https://github.com/xybruceliu/inner_thoughts); [ACM DL](https://dl.acm.org/doi/10.1145/3706598.3713760)
- MIRROR (RoleThink benchmark, "Guess What I am Thinking"): three steps: (1) Memory Recall via cosine similarity of event and chunk embeddings (avg 2.6 related events per scenario), (2) Theory-of-Mind thinking about how other entities (characters, groups, environment) will react, (3) Reflection and summarisation that filters and organises into a character-aligned thought. Human-eval scores 3.0 vs 2.4 (gold set) and 4.4 vs 3.5 (silver set) over zero-shot profiling. On LifeChoice decision accuracy, adding MIRROR thoughts raised accuracy from 55.17% to 64.39%. Human experts found model thoughts had stronger logical links but "less emotional complexity" than original character monologues. — [arXiv 2503.08193 (HTML)](https://arxiv.org/html/2503.08193)
- Role-Aware Reasoning (RAR): Role Identity Activation (RIA) extracts emotion, experience, standpoint and motivation from the profile and injects them as explicit rule-like constraints during reasoning; Reasoning Style Optimization (RSO) uses contrastive learning to separate "logical analysis" from "vivid interaction" scenarios. 137,920 RoleBench-Train samples, teacher Qwen2-32B. CharacterBench 3.69 vs 3.57 for a distilled baseline; SocialBench 65.4 vs 61.1 (Role Style 72.6 vs 69.2). Its own traces score low on conciseness (1.81/5). — [arXiv 2506.01748 (HTML)](https://arxiv.org/html/2506.01748); [abstract](https://arxiv.org/abs/2506.01748)
- Independent evidence that generic reasoning is a risk: a 24-LLM, 6-benchmark study found "CoT may reduce role-playing performance" and reasoning-optimised LLMs are unsuitable for roleplay as-is; it recommends role-aware CoT and RL instead. — [arXiv 2502.16940](https://arxiv.org/abs/2502.16940)
- Newer role-aware CoT: "Psy-CoT" structures pre-response reasoning as Interaction Perception, Psychological Empathy, Logical Construction, plus RAPO RL; reported gains on CoSER, CharacterBench, CharacterEval (abstract only; model sizes not stated). — [arXiv 2606.27025](https://arxiv.org/abs/2606.27025)
- ToMATO uses "Inner Speech prompting": the roleplaying LLM verbalises its thoughts before each utterance, covering belief, intention, desire, emotion, knowledge (first and second order). Information asymmetry between agents (hidden thoughts) produces false beliefs; even GPT-4o-mini lags humans on false beliefs. — [arXiv 2501.08838](https://arxiv.org/abs/2501.08838)
- SillyTavern "Stepped Thinking" (cierru/st-stepped-thinking): a prompt-chaining extension that runs one or more thinking prompts before the normal generation, shows the result in a collapsible "CharName's thoughts" block, can be disabled or customised per character. Default prompts: "Pause your roleplay. Describe {{char}}'s thoughts at the current moment." (also a "plans" variant), answered as a 2-4 point markdown list. Community prompts include a one-to-three-point internal monologue, a relationship/conflict analysis across all present characters, and a six-step `<think> Okay, ...` sequence (context, emotion, interpretation, options, decision, mental rehearsal). — [GitHub cierru/st-stepped-thinking](https://github.com/cierru/st-stepped-thinking); [Prompts wiki](https://github.com/cierru/st-stepped-thinking/wiki/Prompts-for-thinking)
- A Hugging Face model card for a Qwen2.5-7B "thinking" fine-tune advertises compact, to-the-point reasoning blocks rather than long loopy ones, i.e. small-model roleplay-oriented think blocks exist. Vendor claim, not measured. — [DavidAU reasoning models page](https://huggingface.co/DavidAU/How-To-Use-Reasoning-Thinking-Models-and-Create-Them/tree/main)

### Inferences
- Best short-thought format for Kataki (synthesis, my design): 1 line of first-person voice (<=25 words), plus 3 machine-readable side fields (feeling, want, stance). The voice line follows Inner Thoughts (<15 words, stimulus-annotated) and Stepped Thinking (short); the side fields follow RAR's RIA (emotion, standpoint, motivation) and Chain-of-Emotion (already in note 03). Skip MIRROR's "reflection/summarise" as a separate step; fold retrieval into the prompt (Kataki already has recall) and fold ToM into one field ("they will probably ...").
- MIRROR's own reviewers found model thoughts too logical and not emotional enough; to counter that on a small model, force the voice line to start from a feeling or bodily impulse, not from analysis.
- The uncomfortable evidence (CoT can hurt roleplay, RAR fixes needed distillation training) argues against using a general reasoning model's raw trace as the peek content. If a reasoning model is in the `reasoning` role, keep its trace out of the peek and generate the character thought with a separate short call.
- Because the thought is generated before and fed into the reply, the peek shows what actually conditioned the reply (faithful by construction). Post-hoc explanation would not have that property.

### Gaps
- No runnable Inner Thoughts implementation code was retrieved, and the exact call count per turn is not published (only "1 S1 + 2 S2 thoughts per batch, each evaluated with top-5 sampling", which implies at least 3 generation calls plus 3 evaluation calls per trigger on GPT-class models).
- No measured comparison of thought-before-reply on 7-14B local models; every quantitative result above is on GPT-3.5/4-class or 32B-teacher setups.
- No r/SillyTavernAI or r/LocalLLaMA practitioner thread retrieved (search budget exhausted); the Stepped Thinking repo README and wiki are the only community evidence. Whether users report thinking prompts improving or damaging style is unverified.
- Quality of `<think>`-emitting roleplay fine-tunes (e.g. Qwen3-based RP tunes) was not verified; only a model-card claim was found.

---

## 2. Subconscious / background processing: sleep-time compute, mind-wandering, incubation, intrusive thoughts, idle rumination, Auto-Dreamer, and cheap scheduling

### Takeaway
Offline compute is well supported for consolidation and pre-computation when future needs are predictable from context (Letta: ~5x less test-time compute; Auto-Dreamer; Claude-Code-style dreaming). Nobody has measured "background rumination that surfaces later" for perceived human-likeness; that part is a design bet, supported only by psychology (note 01) and a few agent-simulation modules.

### Cited Findings
- Sleep-time compute: pre-reasoning about a context offline cut test-time compute ~5x for equal accuracy on Stateful GSM-Symbolic and Stateful AIME; scaling sleep-time compute added up to 13% (GSM) and 18% (AIME) accuracy; with multiple related queries, cost per query fell 2.5x. The gain correlated with query predictability from context and shrinks when queries are unpredictable. Models tested: GPT-4o/4o-mini, o1, o3-mini, Claude 3.7 extended thinking, DeepSeek-R1. — [arXiv 2504.13171 (HTML)](https://arxiv.org/html/2504.13171v1); [Letta blog](https://www.letta.com/blog/sleep-time-compute/); [code](https://github.com/letta-ai/sleep-time-compute)
- Letta ships sleep-time-enabled agents: a primary agent plus a sleep-time agent under the hood that share memory blocks and rewrite them asynchronously. — [Letta blog](https://www.letta.com/blog/sleep-time-compute/); [Letta docs](https://docs.letta.com/guides/agents/architectures/sleeptime/)
- Auto-Dreamer (May 2026): a learned offline consolidator that separates fast per-session memory acquisition from slow cross-session consolidation; treats a working region of a typed memory bank as read-only evidence, does bounded tool use, and writes a compact replacement set; trained with GRPO using downstream agent performance as reward. — [arXiv 2605.20616](https://arxiv.org/abs/2605.20616)
- A concrete, cheap "dreaming" spec (Hermes-agent feature proposal, not a paper): cron-triggered (default 3 AM), skipped if the user was active in the last 60 minutes; three phases (Light: scan transcripts and stage candidates; REM: extract themes and write a narrative dream diary; Deep: score and promote entries above a 0.6 threshold to permanent memory); max 50 candidates per cycle, 7-day lookback, opt-in. — [NousResearch/hermes-agent issue 25309](https://github.com/NousResearch/hermes-agent/issues/25309)
- Search-snippet-level only: recent agent work adds a "mind wandering / Wonder" module that randomly samples unrelated memories or prompts the agent to produce unrelated persona-based thoughts, and another line of work models Spontaneous Thought as 30-50% of waking hours, roughly 20% future planning, the rest memory replay. I could not open the source paper to confirm which paper, and the UXAgent PDF fetch failed, so attribution to UXAgent is unconfirmed. — [UXAgent, arXiv 2504.09407](https://arxiv.org/pdf/2504.09407); [Unified Mind Model, arXiv 2503.03459](https://arxiv.org/pdf/2503.03459); [Why do we think? PMC11210302](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11210302/)
- Search-snippet-only pointer for scheduling: IdleSpec (May 2026) studies exploiting idle time in LLM agents via speculative planning. Not read. — [arXiv 2605.22154](https://arxiv.org/html/2605.22154)

### Inferences
- Mapping to Kataki: three distinct background jobs, each with a different trigger and cost.
  1. Post-reply afterthought (during the user's read/type time): the slow "Reasoner" step of Talker-Reasoner (see section 3). Zero perceived latency, but the next turn sees it (delayed view).
  2. Offstage pass at time skip or scene close: per present character, "what has been on their mind since": preoccupations, unfinished business, a plan, occasionally an intrusive thought. This is the incubation mechanism: write a thought-seed, let it decay, resurface it in a later scene. It fits the existing scene-close consolidation run, so it can piggy-back on the same call to keep the count flat.
  3. Consolidation (Letta/Auto-Dreamer/dream-diary style): already largely present as scene-close consolidation; add a scoring threshold and candidate cap from the Hermes-style spec so it stays bounded.
- Sleep-time compute's own limitation applies: it pays off when the next queries are predictable from context. Roleplay user messages are mostly not predictable, so do not pre-write replies; pre-compute state (moods, seeds, beliefs, open loops) instead, which is context-predictable.
- Intrusive thoughts: cheapest implementation needs no extra LLM call to select: sample one low-weight memory or seed at random with salience-weighted probability, inject it as a "faint unspoken pull" into the thought call's stimulus list, and let the model decide whether it colours the reply. Probability is a per-character trait (anxious characters higher). Design suggestion; no source evaluates it.
- Scheduling cheaply on 8 GB: run background jobs only when (a) no generation in flight, (b) the user has been idle N seconds or the scene just closed / skip was pressed, (c) the job is preemptible (llama.cpp cancel on new user message; discard partial work, do not block the reply). Batch all characters into one prompt with one JSON array output to amortise prefill. On cloud, use the cheap `utility` model. Do not schedule wall-clock cron dreaming for a desktop app that may be closed; trigger on scene close and app-idle instead (the Hermes 60-minute-idle guard is the right pattern, cron is not).

### Gaps
- No study measures whether surfaced background thoughts (worry that resurfaces, incubated idea) raise perceived human-likeness in roleplay; evidence is psychological plus system descriptions only.
- Letta's default sleep-time trigger frequency and per-step cost were not retrieved (search budget exhausted); docs page linked but not fetched.
- The mind-wandering / Wonder module source paper and any evaluation were not confirmed.
- No 7-14B local measurement of background-pass latency; estimates below are mine.

---

## 3. Dual-process: fast gut reaction versus deliberate override (SOFAI, SwiftSage, Talker-Reasoner); when to "think hard"; heuristic triggers

### Takeaway
Every credible dual-process agent uses a cheap default path plus a rule-based or metacognitive trigger for the expensive path; none has a solved automatic detector. Talker-Reasoner's key trick for chat is asynchrony: the fast talker answers with the latest stored belief while the slow reasoner updates state in the background, and only waits when the situation demands it.

### Cited Findings
- SwiftSage switches from the fast Swift module to the slow Sage module by a heuristic when any of four conditions hold: Stuck (K=5 consecutive zero-reward steps), Invalid (Swift's proposed action is invalid), Critical (the action is a critical decision such as giving a final answer), Unexpected (observation shows an exception). It reverts to Swift when the action buffer is empty. — [SwiftSage, arXiv 2305.17390 (HTML)](https://arxiv.org/html/2305.17390); [GitHub SwiftSage](https://github.com/SwiftSage/SwiftSage)
- Talker-Reasoner (Google DeepMind, 2024): Talker (Gemini 1.5 Flash in the paper) is fast, retrieves memory, and produces the conversational reply; Reasoner does multi-step planning, tool calls and belief-state updates. They share a memory: the Reasoner writes beliefs, the Talker reads the latest available ones and does not wait, so "the Talker therefore might operate with a delayed view of the world". For complex planning requests the Talker waits for the Reasoner, i.e. System 2 overrides. Automatic detection of when System 2 is needed is stated as an open problem. — [arXiv 2410.08328 (HTML)](https://arxiv.org/html/2410.08328v1); [abstract](https://arxiv.org/abs/2410.08328)
- Inner Thoughts embeds a System 1 / System 2 split at thought level (quick reaction to recent utterances vs deliberate thought from retrieved memories) and exposes a tunable probability of System-1 thoughts: `system1Prob` 0.7 = "non-stop chatter", 0.2 = "active contributor", 0 = "selective participant". — [arXiv 2501.00383 (HTML)](https://arxiv.org/html/2501.00383)
- Evans and Stanovich frame Type 1 as producing default responses unless Type 2 intervenes (already in note 01). SOFAI-LM (note 03) matches a standalone reasoning model with much lower inference time using metacognitive routing.
- Effect of forcing System 2 on roleplay is negative on average: reasoning-optimised models and CoT reduced roleplay scores in a 24-model study, and thinking mode slightly lowered villain-play scores (note 04, arXiv 2511.04962). — [arXiv 2502.16940](https://arxiv.org/abs/2502.16940)

### Inferences
- SwiftSage's four triggers translate directly to roleplay (my mapping):
  - Critical: the turn forces a decision that changes the plot or relationship (confess, refuse, betray, reveal, accept). Detect from the character's stated goals/flags plus a cheap classifier over the user message.
  - Unexpected: the user's action violates the character's expectation (violation of appraisal prediction; big valence/arousal delta versus mood).
  - Invalid: the fast reply fails a check (leaks a held-back fact, contradicts a state flag, out-of-character by a validator, repeats the last reply). Regenerate through the slow path instead of blind retry.
  - Stuck: K turns without a state change (no new goal progress, mood flat, loop). Trigger a slow pass that injects a want or complication.
  - Extra roleplay-specific: a secret or held-back fact is topical (highest value, this is where masks matter), a direct question to a character with a stake, first meeting or relationship-stage boundary, an emotionally charged user message, the user asks "why" or opens peek.
- Fast path for everything else; keep the fast path to a single call with the inline thought header (option O1 in section 7). That also means most turns cost about the same as today.
- Talker-Reasoner asynchrony gives the cheapest "override without latency": after the reply is streamed, run the slow call while the user reads and types, write its output to shared state (belief, mask, next-turn intent), and let the next fast turn read it. Accept the delayed view; escalate to a blocking slow call only when the Critical/secret triggers fire. Because Kataki has a `reasoning` role already, the slow step is the natural home of that role.
- Do not use a general reasoning model's raw chain-of-thought as the slow path's output for the reply. Use it only to produce structured state (stance, intent, hold-back list), then feed that into a normal-voice reply call. That keeps the style-drift finding from biting.

### Gaps
- No published detector for "when should a character think hard" in roleplay; the triggers above are adapted from SwiftSage, not evaluated for chat.
- No believability-specific evidence for dual-process routing (only task accuracy/latency papers); consistent with the phase-1 note.
- No measured false-positive/negative rates for any trigger.

---

## 4. Thoughts that disagree with speech: lying, sugarcoating, suppression; keeping speech consistent with private thought without leaking

### Takeaway
Separating private "thought" from public "speech" is an established research setup and the natural mechanism for masks, but I found no paper that measures leak rates or gives a tested anti-leak method for roleplay. The practical approach is structural: give the thought an explicit stance field, generate the reply from intent (not from the raw thought), keep a hold-back list, and check the output.

### Cited Findings
- ToMATO builds conversations with information asymmetry by hiding agents' verbalised thoughts from each other, which creates false beliefs and mental states that contradict expressed utterances; models (even GPT-4o-mini) lag humans on false beliefs. — [arXiv 2501.08838](https://arxiv.org/abs/2501.08838)
- The OpenDeception framework separates causal "thought" from "speech" to assess both deceptive intention and realised deception in multi-turn dialogue (search-snippet description via an aggregator; original not opened). — [Emergent Mind: Deceptive LLM Behavior](https://www.emergentmind.com/topics/deceptive-llm-behavior)
- Alignment-driven positivity is the failure mode that blocks deceitful characters: villain play degrades most at the selfish/deceitful levels and thinking mode slightly worsens it (note 04). — [arXiv 2511.04962](https://arxiv.org/html/2511.04962v1)
- Recursive-contemplation work on Avalon (deception game) forms first-order and second-order thoughts about others' beliefs before acting; it is a hidden-role game, not open roleplay. Title and topic only, not read. — [arXiv 2310.01320](https://arxiv.org/pdf/2310.01320)
- Aggregator claim (weak source): chain-of-thought text can be unfaithful to the model's real computation. — [Emergent Mind: Deceptive LLM Behavior](https://www.emergentmind.com/topics/deceptive-llm-behavior); [When Thinking LLMs Lie, arXiv 2506.04909](https://arxiv.org/pdf/2506.04909)
- Goffman's front-stage/back-stage and face-threat weighing already map "backstage/peek" to sugarcoating, hedging and bluntness from one mechanism (note 01).

### Inferences
- Mechanism (design, not sourced): the thought record carries `stance` in {honest, soften, deflect, withhold, lie} and `hold_back` (fact ids or short phrases). The reply prompt receives "what you feel (private, never state it)", "what you want them to believe/do", "stance", "do not mention". Generate the reply from `want` + `stance`, not by paraphrasing the thought; paraphrase is what causes leaks.
- Consistency comes from ordering: thought is generated first (or inline first) and is in context when the reply is generated, so the reply cannot drift arbitrarily. For inline single-call generation this is automatic; for two-call it is explicit.
- Leak checks, cheapest first: (1) lexical: any hold_back phrase or rare content-word overlap between thought and reply above a small threshold; (2) embedding cosine between the reply and the hold-back fact; (3) only if flagged, a 1-call yes/no judge. On flag, regenerate with a stronger "do not reveal" line (this is the SwiftSage "Invalid" trigger).
- Controlled leakage is a feature, not a bug: allow a `tell` field (a micro-behaviour: voice cracks, changes subject, too-quick denial) that the reply may show. That is how humans leak and it makes lies detectable by an attentive user. This is my design proposal; no source tested it.
- Small models tend to echo their own thought; keep thought text out of the reply-visible history (Kataki already never puts thoughts into history or cached prefix) and show only the structured side fields (stance/want/tell) to the reply generator, not the verbatim voice line, if echo shows up in testing.
- Choose villain-capable models for the `rp` role for lying/withholding characters; prompting alone will not overcome alignment positivity (note 04).

### Gaps
- No measured leak rate (how often a small model states a held-back fact) for any prompt pattern; needs a Kataki eval.
- OpenDeception and Avalon work were not opened; only snippet-level.
- No evidence on whether users perceive characters as more human when speech and thought visibly diverge (peek), only the market-scan observation that no competitor shows it.

---

## 5. Group scenes: whose thoughts, how often, avoiding N x cost

### Takeaway
Do not run N thought pipelines per turn. Only the speaker needs a blocking thought; the others get thoughts lazily (when triggered, on peek, or in a batched ensemble call that also decides who speaks). Inner Thoughts is the reference for speaker selection by thought score but is expensive as published.

### Cited Findings
- In Inner Thoughts, each trigger produces several thoughts per agent (1 System-1 + 2 System-2 in the study), each evaluated with top-5 sampling, and the highest-scoring thought decides who speaks or whether to interrupt; the authors state cost was not quantified and concurrent calls are a scalability concern. — [arXiv 2501.00383 (HTML)](https://arxiv.org/html/2501.00383)
- Speaker selection alternatives in multi-agent chat frameworks: LLM-selected speaker (an extra call per turn), round-robin (linear, context-blind), and eagerness-score/priority selection with a stochastic element. — [AutoGen group chat docs](https://microsoft.github.io/autogen/0.2/docs/notebooks/agentchat_groupchat_customized/); [AutoGen paper](https://arxiv.org/pdf/2308.08155)
- Stepped Thinking has a community prompt that analyses conflicts and emotional states of all present characters in one call, i.e. a single shared thought pass rather than per-character calls. — [Prompts wiki](https://github.com/cierru/st-stepped-thinking/wiki/Prompts-for-thinking)
- Search-snippet-only pointer: GroupGPT (Mar 2026) is a token-efficient multi-user chat framework; not read. — [arXiv 2603.01059](https://arxiv.org/pdf/2603.01059)

### Inferences
- Tiered group policy (my design):
  - Speaker(s) this turn: inline thought (O1), 0 extra calls.
  - Non-speaking characters: no LLM call by default. Keep last thought and mood as state; run a cheap trigger (name mentioned, their secret/flag topical, relationship to speaker, mood delta) to decide "wants to speak" and to justify a lazy thought.
  - Ensemble call at most once per user turn, only in groups of 3+, only when the speaker is not obvious: one prompt, one JSON array with one 15-word thought plus an urgency 1-5 per present character, then pick the max (Inner Thoughts logic collapsed into one call). Cost about N x 25 output tokens in one call, not N calls; prefix is shared.
  - Peek on a non-speaking character: generate on demand and cache; label as "what they were thinking" (post-hoc is acceptable here because they did not speak, so there is no reply to be inconsistent with).
  - Scene close: one batched offstage call for all characters (section 2).
- Inner Thoughts' "silence growth" trick (score rises with silence duration) is a cheap way to make quiet characters eventually speak, with zero extra calls.

### Gaps
- No published per-turn cost for multi-character thought pipelines; cost numbers below are my estimates.
- Whether ensemble-in-one-call thoughts are as good as separate per-character calls is untested (attention crosstalk between characters is likely on 7-14B).

---

## 6. Evidence: which of these measurably improves perceived human-likeness?

### Takeaway
Thought-before-speak has human-rated support (Inner Thoughts: 82% preference and gains on anthropomorphism/coherence, but simulated conversations, GPT-class models, no ablation); short structured role-aware thinking has benchmark support (RAR, MIRROR, Psy-CoT); generic reasoning has negative evidence for roleplay. Background thinking, mind-wandering, dual-process routing and thought/speech gaps have essentially no perceived-human-likeness measurements.

### Cited Findings
- Inner Thoughts: preferred 82% in a 100-conversation human-rated study, significant gains on anthropomorphism, coherence, intelligence and turn-taking appropriateness; but the baseline was only next-speaker prediction, no ablations, and the chatbot study had 12 participants; raters needed animated typing-speed replays to perceive timing. — [arXiv 2501.00383 (HTML)](https://arxiv.org/html/2501.00383); [search summary](https://arxiv.org/abs/2501.00383)
- MIRROR-style thoughts improved downstream decision accuracy on LifeChoice from 55.17% to 64.39% and human-rated thought quality; experts noted less emotional complexity than real monologues. — [arXiv 2503.08193 (HTML)](https://arxiv.org/html/2503.08193)
- RAR: +0.12 on CharacterBench average and +4.3 on SocialBench average versus a distilled baseline; benchmark scores, not human-likeness ratings. — [arXiv 2506.01748 (HTML)](https://arxiv.org/html/2506.01748)
- CoT/reasoning reduces roleplay scores in a broad benchmark sweep. — [arXiv 2502.16940](https://arxiv.org/abs/2502.16940)
- Chain-of-Emotion (appraisal then reply) gave modest but significant naturalness and emotion-sensitivity gains in a 30-person study (note 03). — [PMC11086867](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11086867/)
- Sleep-time compute evidence is accuracy/cost on math tasks, not human-likeness. — [arXiv 2504.13171](https://arxiv.org/html/2504.13171v1)

### Inferences
- Ranking by evidence strength for "feels more human": (1) a short thought that shapes the reply and timing (Inner Thoughts, appraisal); (2) character-aware structuring (RAR/Psy-CoT); (3) everything else unproven. The proactive/turn-taking component of Inner Thoughts (the character speaks up or holds back, interrupts, and waits) was the main human-rated win, not the thought text itself, so for Kataki group scenes the thought score as a speak/stay-silent driver is likely worth more than inner monologue quality.
- Kataki should A/B its own variants because none of the evidence transfers cleanly to 7-14B models. Cheap harness: fixed 20 scripted scenes, blind pairwise preference by the owner, and a leak-rate counter.

### Gaps
- No ablation of thought vs no thought on a small local model with human ratings.
- No perceived-human-likeness study for offstage/background thoughts or thought-seeds resurfacing.
- No study of whether visible peek (thought shown to the user) changes perceived human-likeness or trust.

---

## 7. Design options for Kataki: cost, latency, small-model fit, and the recommended design

### Takeaway
Cheap default: one inline structured thought in the same generation (0 extra calls, about +40 tokens), a rule-based gate that upgrades to a slow structured pass on critical turns, an asynchronous post-reply afterthought, and batched offstage seed generation at time skips and scene close. Premium: a blocking slow pass every turn on a cloud model, ensemble group call, and richer offstage passes.

### Cited Findings
- Evidence for each row is in sections 1-6; this section is design synthesis, so the table below is Inferences, not cited facts. Only the mechanism sources are listed here for traceability: [Inner Thoughts](https://arxiv.org/html/2501.00383), [MIRROR](https://arxiv.org/html/2503.08193), [RAR](https://arxiv.org/html/2506.01748), [Talker-Reasoner](https://arxiv.org/html/2410.08328v1), [SwiftSage](https://arxiv.org/html/2305.17390), [Sleep-time compute](https://arxiv.org/html/2504.13171v1), [Stepped Thinking](https://github.com/cierru/st-stepped-thinking), [Hermes dreaming spec](https://github.com/NousResearch/hermes-agent/issues/25309).

### Inferences

Assumptions for the numbers (all estimates, not measured, not sourced): 8B-class Q4 model on an 8 GB GPU generates about 40-70 tok/s, 12-14B Q4 about 20-40 tok/s (slower if partly offloaded); prompt processing hundreds to a few thousand tok/s, so re-prefilling a 3-6k-token context costs about 1-5 s unless the KV prefix is reused; cloud small model about 0.3-1 s time to first token plus 50-150 tok/s. A short thought is 25-60 output tokens.

| # | Option | Extra LLM calls / turn | Extra tokens | Latency added to visible reply (est.) | Works on 7-14B local | What quality it buys |
|---|--------|------------------------|--------------|---------------------------------------|----------------------|----------------------|
| O0 | Baseline, no thought | 0 | 0 | 0 | yes | none; assistant-positive drift is unmitigated |
| O1 | Inline thought header in the reply generation (`thought`, `feeling`, `want`, `stance` fields, then reply; grammar-constrained or tagged) | 0 | +40-80 out | +1-2 s local (thought must finish before first reply word; streamed hidden), ~+0.5 s cloud | yes for 8B+ with json_schema/GBNF; partly on 3-4B | Subtext, tone coherence, mask/stance, faithful peek content; the best cost/benefit |
| O2 | Two-call Stepped-Thinking style: call 1 thought (non-streamed), call 2 reply conditioned on it | +1 | +40-100 out, +context re-read (prefix reuse helps) | +2-4 s local, +1 s cloud | yes | Same as O1 with cleaner separation and per-call temperature (e.g. higher for thought), easier debugging; worse on 8 GB due to extra prefill |
| O3 | Appraisal + thought + stance merged, structured JSON (Chain-of-Emotion style merged into thought call) | +0 to +1 | +80-150 out | +2-4 s local | yes on 8B+; partly below | Persistent mood/emotion state update plus thought; best paired with the gate as the "slow" path |
| O4 | MIRROR-style 3-step (recall, ToM about others, reflect) as a template in one call or three calls | +1 to +3 | +150-400 out | +4-10 s local, +2-4 s cloud | partly (7B loses coherence on long templates; 12-14B ok) | Better decision-grade thoughts on hard turns (LifeChoice +9 points in the paper); more logic than emotion |
| O5 | Full Inner Thoughts (S1+S2 thoughts, per-thought scoring, threshold participation) | +3 to +6 per agent per trigger | +300-800 per agent | +5-15 s local per agent | no for groups; partly for 1:1 with N=1 | Turn-taking realism, proactivity; only with a cloud model or a collapsed one-call version (see O9) |
| O6 | Dual-process router: gate decides O1 vs O3/O4 | +0 typical, +1 on gated turns (est. 10-25% of turns) | avg +10-30 | avg +0.3-1 s | yes (gate is code, not an LLM) | Keeps average cost near O1 while deep thinking happens where it matters |
| O7 | Async afterthought (Talker-Reasoner): after the reply, run the slow structured pass in the background; next turn reads it | +1 on chosen turns | +80-200 out, off the critical path | 0 if the user takes >3 s to reply; else a blocked next turn (cancel and skip) | yes (preemptible) | Continuity of intent, beliefs, mask across turns without adding latency |
| O8 | Offstage pass at time skip / scene close: one batched call, all present characters, outputs thought-seeds (worry, plan, unfinished, intrusive, idea) with salience | +1 per skip/close (not per turn) | +100-300 out total | 0 turn latency; +3-10 s in the skip animation local | yes, one batched JSON call | "Life off-screen", incubation, resurfacing later; the subconscious feature |
| O9 | Ensemble group call: one JSON with a 15-word thought and urgency 1-5 per present character, choose max; also drives peek for silent characters | +1 per user turn (groups of 3+, only when speaker not obvious) | +25 x N out | +2-5 s local | partly (3-4 characters ok on 12-14B; watch crosstalk) | Inner Thoughts speaker-selection/interrupt behaviour at 1 call instead of 3N |
| O10 | Wonder / intrusive-thought injection: random salience-weighted seed sampled in code and offered as a faint stimulus to O1/O3 | 0 | +15-30 in | ~0 | yes | Intrusions and topic drift; near free; effect unmeasured |
| O11 | Sleep-time consolidation, scored and capped (Auto-Dreamer / dream-diary pattern), on scene close and app idle | +1 per scene close | +200-600 out | 0 turn latency | partly (needs a decent `utility` model; summarisation quality matters) | Cleaner memory, thought-seeds promoted or dropped; already partly in Kataki |
| O12 | Premium: cloud reasoning model as the slow step, structured output only (no raw trace shown, no raw trace fed to reply) | +1 per gated or every turn | 300-2000 thinking tokens | +3-15 s | not applicable (cloud) | Best decision quality for hard turns, but reasoning models risk style drift (CoT-hurts evidence), so keep them out of the reply voice |

Recommended design (cheap default + premium mode):

Cheap default (fits 8 GB, average cost about one call per turn):
1. Every turn, speaker only: O1 inline thought header. Same generation, hidden by the existing `thought` SSE route; never in history or prefix. Peek shows it verbatim (faithful).
2. Gate (code, no LLM): compute triggers from existing state: secret/flag topical, direct question with stake, critical decision word or goal, mood/valence delta above threshold, first meeting or relationship stage change, K turns with no state change (stuck), leak or continuity check failure (invalid), user opened peek. On fire: run the slow path (O3 structured appraisal + stance + hold_back) as a blocking call before the reply, at most once per 2 turns per character and with a per-session budget.
3. After every gated turn (and every ~5th ordinary turn): O7 async afterthought writes updated intent/beliefs/mask to state, preemptible, skipped if the user is already typing.
4. Time skip and scene close: O8 batched offstage call producing 1-3 thought-seeds per character; fold O11 consolidation into the same call or same cycle. Seeds decay; at the next scene start, pick 0-2 by salience x freshness with random jitter (O10), pass them as "on your mind, unspoken".
5. Groups: speaker gets O1; silent characters get state-only; ensemble O9 only for speaker selection in groups of 3+ when needed; peek on a silent character is generated lazily and cached.
6. Reply-side leak check (lexical/embedding, then optional 1-call judge on flag) and regenerate through the slow path on fail.
7. Use a non-reasoning model with thinking disabled for all thought calls (the existing `utility` ladder: thinking off + `json_schema`). If a reasoning model is the `rp` model, its own trace goes to the collapsible block as-is; the character thought call is still separate.

Premium mode (cloud via HF providers or a larger local model):
- O3 slow structured pass every turn (stance, want, hold_back, tell, mood) as a blocking call, then the reply call (O2 pattern) at higher temperature.
- O9 ensemble every group turn with the Inner Thoughts silence-growth and interrupt threshold.
- O8 offstage per-character passes at every time skip, plus O12 reasoning model for critical turns, output constrained to the structured record.
- Cost order of magnitude: about 2-3 calls per turn plus one batched call per skip; still far below Inner Thoughts as published (3+ generation and 3+ evaluation calls per agent per trigger).

Prompt and data-shape sketch (design proposal, not tested):

```jsonc
// Thought record (stored per turn per speaking character; never enters history or cached prefix)
{
  "turn_id": 412, "char_id": 7,
  "source": "inline",          // inline | slow | afterthought | offstage | wonder | peek_lazy
  "thought": "He noticed the ring. Say nothing. Change the subject before I flinch.",  // <=25 words, 1st person, character voice, starts from a feeling/impulse
  "feeling": {"label": "dread", "valence": -0.6, "arousal": 0.7},
  "want": "make him drop the subject",
  "stance": "deflect",         // honest | soften | deflect | withhold | lie
  "hold_back": ["fact:ring_was_sold"],
  "tell": "answers too fast, laughs a beat late",   // optional, reply may show it
  "stimuli": ["mem:112", "seed:33"],                 // what triggered it (Inner Thoughts-style annotation)
  "gate": ["secret_topical", "critical"]             // why the slow path ran, if it did
}
// Thought-seed (offstage / wonder / afterthought residue)
{ "char_id": 7, "kind": "worry|plan|unfinished|intrusive|idea",
  "text": "Should have told her about the debt before the trip.",
  "salience": 0.7, "decay_per_scene": 0.85, "origin_scene": 18,
  "last_surfaced_scene": null }
```

```text
INLINE (O1) system suffix, output constrained by json_schema, thought fields first:
  Write {{char}}'s private thought first, then the spoken reply.
  "thought": one or two short sentences, first person, in {{char}}'s own voice, starting from a feeling or impulse, not from analysis. Max 25 words.
  "stance": how {{char}} will handle what they feel: honest | soften | deflect | withhold | lie.
  "want": what {{char}} wants the other person to think or do.
  Faint unspoken pulls (may colour tone, need not be voiced): {{seeds}}
  Facts {{char}} is holding back (do not state or hint directly): {{hold_back}}
  Then "reply": what {{char}} says and does. Act on want and stance. Never quote or paraphrase the thought.

OFFSTAGE (O8) one batched call at skip/close:
  For each character present, in one JSON array: what has been on their mind since the last scene, given their profile, mood, open goals and the last scene summary.
  Return 1-3 seeds each with kind and salience. Keep each under 20 words, first person.
```

Kataki integration notes: emit the inline thought on the existing `thought` SSE event; store thought records in a new table keyed by message id (kept out of `messages` content, consistent with "thoughts never reach RP text, history or cached prefix"); run offstage inside the scene-close run; add `gate` as a pure function over existing state so it is unit-testable; add a leak-rate eval and a thought-on/thought-off blind A/B before shipping (no external evidence transfers to 7-14B).

### Gaps
- All latency/token numbers in the table and premium-cost estimate are my engineering estimates, not measurements; they need a llama.cpp benchmark on the target GPU (state expected time, check step rate at ~30 s per the project GPU protocol).
- Whether inline thought (O1) on 8B-class models produces good voice-lines with grammar-constrained JSON, versus degraded prose when constrained, is untested; the M1 spec notes grammar-constrained decoding conflicts with think blocks on some backends (not an issue for non-reasoning models but should be checked).
- The gate's trigger thresholds and cooldowns are unvalidated design values.
- Not fetched due to search budget: Letta sleep-time docs details, GroupGPT, IdleSpec, Affordable Generative Agents (arXiv 2402.02053), OpenDeception original, and any r/SillyTavernAI / r/LocalLLaMA practitioner reports; these are the highest-value next reads.
