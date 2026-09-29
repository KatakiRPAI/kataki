# Emotion, Mood and Anxiety Engine for Kataki Characters

Scope: science, papers, existing implementations and concrete design options for a character emotion / mood / anxiety engine in a local-first LLM roleplay app (7-14B local models on 8 GB VRAM, or cloud models via HF Inference Providers). Builds on the phase-1 notes ([01](01_what_makes_humans_human.md) section 2, [03](03_cognitive_architectures.md) section 5, [04](04_persona_fidelity.md)). As of September 2026.

Conventions: "Cited Findings" are sourced. "Inferences" are my reasoning or my design proposals; every numeric default in them (half-lives, weights, latencies, costs) is an unsourced starting value to be tuned, not a finding. WebSearch budget ran out mid-session, so some areas (Replika/Nomi, sampler-temperature evidence, emotion-regulation-in-LLM papers, attachment-anxiety detail) are thin; see Gaps.

---

## 1. Computational emotion models (OCC, EMA, FAtiMA, WASABI, ALMA, Scherer CPM) and LLM vs rule-based appraisal

### Takeaway
Classic models (OCC/EMA/FAtiMA/ALMA/WASABI) are hand-authored appraisal-rule systems; their durable ideas are the layering (emotion, mood, personality) and PAD-space dynamics, not the rule authoring. An LLM can replace the appraisal rules, and the best-evidenced pattern is a single short "appraise first, then speak" step feeding a persistent numeric state; multi-agent CPM pipelines (7-8 calls) add almost nothing on automatic metrics over a zero-shot call.

### Cited Findings
- ALMA layers three affect types by timescale: emotions (short-term, event-caused, decaying), mood (medium-term, diffuse, an average of emotional states) and personality (long-term, Big Five). Emotions come from OCC-style appraisal rules (24 emotion types in its EmotionEngine) and are mapped into PAD (Pleasure-Arousal-Dominance, each -1..1) space, where they push mood around. — [Gebhard, ALMA (AAMAS 2005)](https://alma.dfki.de/papers/aamas05.pdf)
- ALMA mood mechanics: active emotions form a "virtual emotion center" (intensity = average of active emotion intensities) in PAD space; the mood is pulled toward that center when it lies in the current mood octant (mood intensifies) and pushed away otherwise; mood then drifts back to the default mood. Their character used a usual mood-change time of 10 minutes and a return time of about 20 minutes; example emotion decay was configured as a 20-second linear decay in the demo config. — [ALMA](https://alma.dfki.de/papers/aamas05.pdf)
- ALMA default mood from Big Five (values -1..1): Pleasure = 0.21 E + 0.59 A + 0.19 N; Arousal = 0.15 O + 0.30 A - 0.57 N; Dominance = 0.25 O + 0.17 C + 0.60 E - 0.32 A. Eight mood octants are named by PAD signs, and "Anxious" is -P +A -D; "Hostile" -P +A +D; "Bored" -P -A -D; "Relaxed" +P -A +D; "Exuberant" +P +A +D. — [ALMA](https://alma.dfki.de/papers/aamas05.pdf)
- WASABI uses core affect in PAD space, with an emotion axis (short-term) and an orthogonal mood axis (longer-lasting, undirected) plus a third axis for boredom, categorised into discrete emotions; it distinguishes primary emotions (direct) from secondary emotions (need reasoning about experiences and expectations). — [Becker-Asano & Wachsmuth, AAMAS journal 2010](https://dl.acm.org/doi/10.1007/s10458-009-9094-9)
- EMA (Gratch & Marsella) is informed by Smith & Lazarus appraisal theory; it argues for a single automatic appraisal over the agent's current interpretation of its relationship to the environment, with dynamics coming from inference that updates that interpretation, and uses decision-theoretic planning / BDI representations to derive appraisals and coping potential. — [Marsella & Gratch, EMA (Cognitive Systems Research)](https://www.sciencedirect.com/science/article/abs/pii/S1389041708000314)
- FAtiMA Toolkit is a modular C# collection (Emotional Appraisal, Emotional Decision Making, Social Importance Dynamics, Role Play Character, authoring tool) aimed at Unity-style games; its README documents no decay mechanism and no LLM integration. — [FAtiMA Toolkit](https://github.com/GAIPS-INESC-ID/FAtiMA-Toolkit)
- Scherer's CPM appraises through four sequential checks: relevance, implications, coping potential, normative significance. The 2026 CPM-MultiAgent paper implements them as LLM agents. — [CPM-MultiAgent, arXiv 2607.07824](https://arxiv.org/html/2607.07824v1); background in [phase-1 note 01](01_what_makes_humans_human.md)
- CPM-MultiAgent: 7 agent roles (trigger analyzer, four CPM appraisers, integrator, critic), state = Likert-5 intensities over Plutchik's eight emotions, update = additive deltas `e_t,k = clip(e_{t-1,k} + delta_t,k)`; about 7-8 sequential invocations per turn on GPT-5.4; 11.0 s per turn with parallel appraisal (14.5 s sequential), 6.5 s with GPT-5.4-mini. 24 constructed trials only. Emotional Update Correctness 4.305 vs 4.261 for a zero-shot baseline (1-5 scale); 103 human annotators preferred it on reasoning quality (86 wins vs 7 losses against EQ-Negotiator). Removing trigger analysis cost 0.096, removing peer review 0.243 overall. — [CPM-MultiAgent](https://arxiv.org/html/2607.07824v1)
- Chain-of-Emotion (Croissant et al., PLOS One 2024): memory + a separate appraisal LLM call ("briefly describe how X feels now given the situation and their personality") stored and fed into the reply call: 2 calls per interaction, gpt-3.5-turbo, temperature 0. Situational Test of Emotional Understanding (42 items): no-memory 57%, memory 74%, Chain-of-Emotion 83%. User study N=30: "reactions were natural" p=0.03, "sensitive to emotions" p=0.04. Authors note it covers only the appraisal component, one model, short interactions. — [Chain-of-Emotion, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11086867/)
- CAREBench (May 2026; GPT-5.2, Claude-Sonnet-4.6, Llama 3.1-8B, Qwen 3.5-9B, two emotion-tuned models): LLMs do best on the appraisal dimensions relevance and congruence and struggle with accountability, control and certainty; negative emotions are recognised as well as human third-party observers, positive emotions are consistently weak; emotion-prediction accuracy overestimates true appraisal understanding; self-generated reasoning text hurt performance. — [CAREBench](https://arxiv.org/html/2605.17176)
- Search-summary-level (not read in full): GPT models align well with human appraisals but struggled with emotion intensity and coping response; another 2026 LREC paper finds expectation construction is the main contributor to accurate emotion prediction and isolated violation cues cause misattribution. — [GPT-4 appraisal annotation](https://arxiv.org/html/2503.16883v2); [Appraisal Theory-Informed Emotion Prediction](https://aclanthology.org/2026.lrec-1.887/)
- EmotionBench (400+ situations, eight emotions, 36 factors, 1,200+ human subjects, seven LLMs incl. GPT-4, Mixtral-8x22B, LLaMA-3.1): LLMs respond appropriately to some situations but fall short of human emotional behaviour and cannot connect similar situations. — [EmotionBench](https://arxiv.org/abs/2308.03656)
- EQ-Bench 4 now scores multi-turn persona roleplay on bond/rapport, authenticity, attunement, meeting needs, emotion sensemaking, emotion management using three LLM judges and Elo; it publishes no size-vs-score breakdown on its front page. — [EQ-Bench](https://eqbench.com/)
- "Feeling First, Speaking Second" (ACL CAS 2026): separates visceral appraisal from strategic verbal formulation; found strategic planning can override emotional authenticity under pressure, so affect must come first in the decision cycle. — [ACL Anthology](https://aclanthology.org/2026.cas-1.7/)
- Sentipolis (Jan 2026): continuous PAD state per agent with half-life decay, PAD-to-label translation and emotion-tagged memory; ablations show coupling emotion to memory/generation helps emotional continuity and decay helps believability. Six LLMs, LLM-judge (Sonnet-4.5) validated against humans, Pearson 0.94. — [Sentipolis](https://arxiv.org/pdf/2601.18027)

### Inferences
- The valuable, portable parts of the classic literature are: (a) three timescales (episode, mood, temperament) from ALMA, (b) PAD/valence-arousal as the continuous carrier, (c) appraisal variables from CPM/EMA (relevance, goal-congruence, coping potential, certainty). The authored rule bases (OCC rules, FAtiMA scripts) are what an LLM replaces.
- CPM-MultiAgent's gain over zero-shot on EUC (+0.044 on a 5-point scale) is far smaller than its cost (7-8 calls). For a 7-14B local model on 8 GB this is a rejected option; use one structured appraisal call (or fused output) and keep CPM as a *schema* (relevance, congruence, control, certainty, norm fit), not as a pipeline.
- CAREBench says the dimensions most relevant to anxiety (control = coping potential, certainty = uncertainty) are exactly where LLMs are weakest. So do not trust a small model's free-form judgement of "can she cope with this?": derive control/certainty largely from character traits and scene structure (e.g. waiting on an unanswered message is uncertain by construction), and let the LLM supply relevance, valence and target.
- EmotionBench's "cannot connect similar situations" is the argument for an external persistent state: consistency must live in code, not in the model's memory of how it felt.
- Zero-shot appraisal is the sensible baseline to beat; Kataki should A/B its engine against "persona prompt only" and "one-call appraisal" on its own scripted scenarios before adding anything else.

### Gaps
- No published results of any appraisal-based engine on 7-14B local models (Chain-of-Emotion used gpt-3.5; CPM-MultiAgent GPT-5.4/mini; Sentipolis frontier models); CAREBench includes 8-9B models but tests appraisal rating, not a full character loop.
- Details of OCC's full 22-type structure and EMA's decay parameters were not retrieved from primary sources.
- No source compares LLM appraisal to rule-based appraisal head to head on believability.

---

## 2. State representation: discrete vs VAD vs mood with inertia; update equations; half-lives; temperament

### Takeaway
Use a hybrid: continuous valence-arousal-(dominance) for mood and for the underlying carrier, a small stack of labelled emotion episodes for what the character can name, and exponential decay toward a per-character baseline computed on the story clock. Show the LLM a word, not a number.

### Cited Findings
- PAD model: pleasure-displeasure, arousal-nonarousal, dominance-submissiveness; circumplex: valence x arousal as core affect; Plutchik: eight primaries; Ekman six. Dimensional vs discrete remains a contested issue. — [Emotion classification overview](https://en.wikipedia.org/wiki/Emotion_classification)
- Sentipolis update rule: `s(t+dt) = s(t) * 2^(-dt/T_half)` on a PAD vector in [-1,1]^3, decaying toward neutral, T_half = 120 min in a 12-hour simulation stepped every 20 min. Removing decay lowered believability (delta -1.22) and communication (-1.11); removing the open-vocabulary description and label mapping lowered emotional continuity (-1.94, and -1.41 believability without KNN label); removing coupling to memory/generation lowered continuity (-1.72). — [Sentipolis](https://arxiv.org/pdf/2601.18027)
- Sentipolis does not feed raw PAD numbers to the LLM: it maps PAD to a Plutchik-style label plus a short description via kNN over real human PAD data and injects that. — [Sentipolis](https://arxiv.org/pdf/2601.18027)
- Emotion durations vary widely (the Sentipolis paper cites Verduyn et al. 2011 for highly variable emotion duration, and Kuppens et al. 2010 on emotional inertia and maladjustment in its references). — [Sentipolis](https://arxiv.org/pdf/2601.18027)
- CPM-MultiAgent state = per-emotion Likert-5 intensities updated by clipped additive deltas; multiple emotions coexist. — [CPM-MultiAgent](https://arxiv.org/html/2607.07824v1)
- ALMA's Big Five to PAD default-mood mapping and pull/push mood update (see section 1) is a ready-made baseline-temperament and mood-inertia recipe. — [ALMA](https://alma.dfki.de/papers/aamas05.pdf)
- Humanoid Agents: five needs, seven discrete emotions and four closeness levels, small and cheap to update. — [Humanoid Agents](https://aclanthology.org/2023.emnlp-demo.15/)
- Front Porch AI carries "emotion inertia" between turns to avoid jarring mood swaps, with bond/trust, Sims-style needs and "fixations" alongside. — [Front Porch AI README](https://github.com/linux4life1/front-porch-AI/blob/main/README.md)
- Anthropic's interpretability study found emotion representations organised by valence and arousal with related emotions clustering (fear with anxiety, joy with excitement), matching human psychology. — [Emotion Concepts in an LLM](https://arxiv.org/html/2604.07729v1)

### Inferences
- Clock: decay must run on story time (hours), not turn count, otherwise time skips and "she sulked overnight" cannot work. Closed form `x <- b + (x - b) * 2^(-dt/T)` handles any skip in O(1) with no LLM call.
- Suggested starting half-lives (design defaults): emotion episode 15-30 story-min; mood 3-12 story-h scaled by inertia trait; anxiety "worry" items do not decay on the clock but by resolution and slow habituation (see section 3). Sentipolis's 120 min is for a whole PAD vector, i.e. mood-like, which is consistent.
- Keep three dims (V, A, D): D separates fear/anxiety (low D) from anger (high D), which is the distinction Kataki most needs for anxious vs hostile sulking. ALMA's "Anxious" octant (-P +A -D) vs "Hostile" (-P +A +D) confirms this.
- Baseline temperament = ALMA formula from Big Five (or authored directly), plus per-character `reactivity` (gain on appraisal deltas) and `inertia` (mood half-life). Neuroticism raises reactivity to negative events and lengthens negative-mood half-life; do not make it a global mood offset.

### Gaps
- No sourced empirical half-lives for roleplay-scale moods; values above are tunable guesses.
- No source on how many concurrent emotion labels an LLM can usefully be conditioned on; 1-2 named emotions plus mood is my recommendation.

---

## 3. Anxiety: anticipatory worry, rumination, catastrophizing, reassurance-seeking, avoidance, attachment anxiety

### Takeaway
Anxiety should be a separate small module built on the *worry* construct (future-oriented, uncertainty-driven, avoidance-maintained) with rumination as its past-oriented sibling and attachment anxiety as a relationship-specific trigger set, all gated by a trait so most characters stay calm.

### Cited Findings
- Worry is a chain of negatively affect-laden, relatively uncontrollable thoughts and images about future events with uncertain, possibly negative outcomes; intolerance of uncertainty leads worriers to focus attention on possible negative outcomes; excessive worriers overestimate danger and magnify situations (catastrophizing). — [Worry](https://en.wikipedia.org/wiki/Worry)
- Borkovec's avoidance model: worry is verbal thought that inhibits vivid imagery and somatic arousal, and is negatively reinforced because most worries never occur, so the worrier feels they controlled the danger. — [Worry](https://en.wikipedia.org/wiki/Worry)
- Rumination is sustained repetition of negative thoughts, past/loss oriented; worry is future, problem-solving oriented; rumination sustains anxiety and depression. — [Rumination](https://en.wikipedia.org/wiki/Rumination_(psychology))
- Anxious-preoccupied attachment: seeks approval about relationship security, craves intimacy but worries others will not meet needs; delayed communication produces worry and feelings of rejection even in stable relationships. — [Attachment in adults](https://en.wikipedia.org/wiki/Attachment_in_adults)
- Attachment is now mostly measured as two dimensions, anxiety and avoidance (ECR / ECR-R). — [phase-1 note 01](01_what_makes_humans_human.md)
- ECBench (Aug 2026) applied ECR-R to 32 LLMs and found they show measurable attachment anxiety and avoidance in companionship scenarios, and tested whether prompting can shape them; details beyond the abstract were not read. — [ECBench, arXiv 2608.13168](https://arxiv.org/abs/2608.13168)
- Inner speech: anxiety (not depression) was uniquely related to evaluative/motivational inner speech and voices of others. — [phase-1 note 01](01_what_makes_humans_human.md)
- LLMs themselves shift under anxiety-inducing text: GPT-4 STAI-s score 30.8 baseline, 67.8 after traumatic narratives, 44.4 after mindfulness prompts (still ~50% above baseline); emotion-inducing prompts can bias outputs. Single model, human questionnaire. — [Ben-Zion et al., npj Digital Medicine 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11876565/)
- EmotionPrompt: adding emotional stimuli to prompts changed model performance (8% relative on Instruction Induction, ~10.9% average on generative tasks by human eval), showing emotional framing measurably alters outputs. — [EmotionPrompt](https://arxiv.org/abs/2307.11760)
- CompanionBench (28 agents): emotion regulation and calibrated challenge are common weaknesses; role-play-focused agents ranked low; dominant failure is surface warmth in place of relational support. — [CompanionBench](https://arxiv.org/abs/2608.02046)
- A Feb 2026 discourse study lists self-regulation difficulty as the most prevalent psychological risk from AI chatbot use. — [Risk and Dependency in AI Chatbot Use](https://arxiv.org/abs/2602.09339)

### Inferences
Proposed anxiety module (design, not from a source):
- Per character: `trait.anxiety` (0-1, mostly low), `attachment.anxiety`, `attachment.avoidance`, `coping` (0-1).
- State: up to 2 `worries[]`, each `{topic, kind: anticipatory|relational|ruminative, weight 0-1, since, resolvable:bool}`.
- A worry is *created* only when an appraisal has: high relevance (matters to them), low certainty (outcome unknown), negative expected valence, and low control. Because CAREBench shows LLMs are weak on certainty/control, compute those two by rules where possible: pending unanswered message, upcoming event with unknown result, ambiguous remark from someone they care about.
- Anxiety intensity `Anx = 1 - prod(1 - w_i * g)` with gain `g = f(trait.anxiety, attachment.anxiety for relational worries)`. Effects on core affect: V down, A up, D down; on speech: hedging, shorter or over-long replies, checking questions.
- Behaviours as *bias directives*, not scripts: reassurance-seeking (relational worry above threshold), avoidance (topic change, "it's fine", withdrawing, procrastinating, matching Borkovec: avoidance reduces felt worry short-term but keeps the worry item alive), catastrophizing (appraisal prompt line "assume the worst plausible reading" when trait is high), protest behaviour for attachment-anxious characters on delays.
- Reassurance: lowers worry weight immediately but with a rebound term (worry regrows after ~N story-hours unless truly resolved) - this reproduces the reassurance-seeking loop without extra LLM calls. Real resolution (the reply arrives, the exam goes well) deletes the worry and triggers a relief emotion.
- Rumination: after a high-intensity negative episode, add a `ruminative` worry pointing at the past event; it lengthens negative-mood half-life and is what surfaces in idle/time-skip/peek text ("replaying what he said"). Worry = future + problem-solving; rumination = past + loss (from the sources above).
- Not everyone neurotic: (1) gate on trait so a low-anxiety character (most of them) produces near-zero worry weight from the same trigger; (2) mood baseline pulls back; (3) max 2 concurrent worries; (4) habituation; (5) the appraisal prompt is told "most people would not worry about this unless X". Also because base models are warm/agreeable (CompanionBench), the risk is more often flat cheeriness than over-anxiety.
- Attachment anxiety belongs on the *relationship edge* (per character-user and character-character), reusing the bond/trust idea from Front Porch, rather than as global neuroticism. Time skips are the natural trigger: N hours of silence to an anxiously attached character with an open thread creates a relational worry.
- Product-safety note: clingy/anxious companions that reward reassurance-seeking could deepen dependency; keep a per-character/per-user intensity cap and a "calm" default.

### Gaps
- No source on tuning anxiety intensity for entertainment roleplay; no user study on "annoying" thresholds.
- No paper found specifically on simulating anxiety/rumination loops in LLM characters (only LLM-as-patient anxiety and attachment measurement).
- ECBench results beyond the abstract (which models are more anxious, effect of prompting) not read.

---

## 4. Emotion regulation (Gross): suppression vs reappraisal, masking, the peek feature

### Takeaway
Model regulation as a mapping from felt state to displayed state with a strategy per character; suppression should leak and cost something, reappraisal should actually change the felt state. The felt/displayed split is exactly what the peek view exposes, and there is interpretability evidence that LLMs already represent a hidden emotion separately from the expressed one.

### Cited Findings
- Gross's process model: situation selection, situation modification, attentional deployment, cognitive change (reappraisal), response modulation (suppression). Reappraisal reduces physiological, subjective and neural responding and correlates with better social outcomes; suppression reduces expressivity but is questionable at reducing negative feeling, correlates with reduced connection and more psychological disorders. — [Emotion regulation](https://en.wikipedia.org/wiki/Emotion_regulation)
- Suppression impairs memory for the event; it lowers outward expression without lowering felt emotion. — [phase-1 note 01, citing Gross 2002](01_what_makes_humans_human.md)
- In Anthropic's study, emotion concepts are represented internally even when the character masks them ("internal-external decoupling"), and a probe classified unexpressed emotions reasonably well in distribution; separate representations exist for present-speaker and other-speaker emotion. — [Emotion Concepts in an LLM](https://arxiv.org/html/2604.07729v1)
- "Feeling First, Speaking Second" operationalises feeling vs articulation as separate computations, with the risk that planning overrides felt emotion. — [ACL Anthology](https://aclanthology.org/2026.cas-1.7/)
- CompanionBench lists emotion regulation among the weakest capabilities of companion agents. — [CompanionBench](https://arxiv.org/abs/2608.02046)

### Inferences
- State fields: `felt` (label + V/A/D) and `displayed` (label + intensity + leak). `displayed = regulate(felt, strategy, capacity, context)`.
  - express: displayed = felt.
  - suppress: displayed intensity x (1 - capacity); each masked turn adds `regLoad`; leak probability rises with felt arousal and regLoad (short replies, clipped words, a tell); regLoad accumulates and eventually spills over (the character "snaps"); also degrades recall of the moment (Gross).
  - reappraise: costs one extra appraisal pass ("what else could this mean?"); succeeds only if `coping` is high enough, and then *lowers felt* intensity, not just display (cognitive change).
  - avoid/select situation: leave the room, change topic, mute; relevant for anxiety and for group scenes.
- Regulation strategy is a per-character trait (with context modifiers: social setting, power relation), giving natural "she says she's fine" behaviour and, crucially, a real gap to show in Peek: felt vs displayed, plus the worry loops.
- The felt/displayed split must be produced *before* the reply prompt is built so the reply LLM is told what to show and what to hide; otherwise the model's default candour will voice everything (the planning-overrides-feeling risk in the dual-process paper is the same failure mode).

### Gaps
- No paper retrieved on LLM roleplay agents implementing suppression vs reappraisal; the arXiv keyword searches returned nothing relevant on this exact combination.
- Quantitative leakage rates for suppression (facial/vocal) not retrieved; my leak function is arbitrary.

---

## 5. Emotional contagion and group mood in multi-character scenes

### Takeaway
Contagion emerges in LLM agents when each agent perceives and appraises the others' displayed emotion (no explicit transfer rule needed), but the outcome is strongly backend-dependent; implement it explicitly and cheaply with susceptibility traits over *displayed* emotion, and keep per-character state independent as Front Porch does.

### Cited Findings
- Durupinar (Jul 2026): affect propagates among LLM agents through perception, appraisal (personality, memory, current affect, situation) and expression loops with no hand-authored transfer; alarm spreads as a travelling front; personality distributions decide whether ambiguity produces panic or anger vs fear; results depend on the LLM backend, prompt variant and sampling temperature; tested only on sparse small crowds. Uses Big Five and Russell's circumplex. — [How Affect Propagates among LLM Agents](https://arxiv.org/abs/2607.25140)
- Bian et al. (2023) report LLMs mirror social-cognitive patterns including in-group bias, emotional positivity and emotion contagion when given external information. — [arXiv 2305.04812](https://arxiv.org/abs/2305.04812) (listing-level summary)
- Front Porch AI group chats keep independent Realism state (needs, decay, scene rewards) per full member; guests are stateless until promoted; group chats export starting Realism state including who trusts whom and everyone's mood. — [Front Porch README](https://github.com/linux4life1/front-porch-AI/blob/main/README.md); [FAQ](https://frontporchai.app/docs/faq/)
- Front Porch offers a "One-Shot Eval" mode that fuses the extra short evaluation queries into one when the backend supports it. — [FAQ](https://frontporchai.app/docs/faq/)
- Anthropic's work found separate internal representations for present-speaker and other-speaker emotion. — [Emotion Concepts in an LLM](https://arxiv.org/html/2604.07729v1)

### Inferences
- Explicit contagion rule (cheap, deterministic): for each observer i and each speaker j whose displayed emotion is salient, `mood_i += susceptibility_i * closeness_ij * intensity_displayed_j * pad(label_j)`, clipped. Because it uses displayed rather than felt emotion, masking is respected (a suppressor does not infect the room; an observer may still "read" leaks via a perceptiveness trait).
- The room: keep a derived `atmosphere` = intensity-weighted mean of displayed states, used as a UI strip and as a one-line prompt hint for characters with high susceptibility. Never make it authoritative over individual state.
- Cost in groups: appraisal is per-observer, so N characters means N appraisals. Batch all present characters into one structured call that returns an array (Front Porch's fused eval is precedent), and only for characters who actually act or are addressed this turn.
- Backend dependence (Durupinar) is a reason to keep the numbers in code, so behaviour does not change when the user swaps between a local model and a cloud model.

### Gaps
- No source on group-chat mood dynamics in roleplay products beyond Front Porch's per-member state.
- Susceptibility and closeness weights have no empirical grounding here.

---

## 6. How emotion state should modulate generation: prompt injection, sampler, control vectors, style tokens

### Takeaway
Prompt injection of a label plus behavioural directives is the evidenced baseline and works on any backend; activation steering has strong causal evidence (including on 7-13B open models) but is local-only, static per server in llama-server, and degrades coherence at high strength; sampler-temperature modulation has no evidence I could find and should not be relied on.

### Cited Findings
- Prompt injection: Sentipolis injects a label + description (not raw PAD) into prompts and the ablation shows open-vocabulary description supports emotional continuity. — [Sentipolis](https://arxiv.org/pdf/2601.18027). Chain-of-Emotion injects the appraisal text into the reply prompt and improves reaction naturalness. — [Chain-of-Emotion](https://pmc.ncbi.nlm.nih.gov/articles/PMC11086867/). Front Porch injects state through the system prompt with trust-based calibration. — [Front Porch README](https://github.com/linux4life1/front-porch-AI/blob/main/README.md)
- Emotional prompt stimuli measurably change outputs across six models incl. Llama 2 and Vicuna. — [EmotionPrompt](https://arxiv.org/abs/2307.11760)
- Activation steering, frontier scale: 171 emotion concepts in Claude located via sparse autoencoders satisfy activation, causal-steering and internal-external decoupling criteria; steering strength 0.5 relative to average residual norm at middle-to-late layers (about two-thirds through); amplifying "blissful" and suppressing "hostile" shifted expressed preferences; representations track the operative emotion in context rather than a persistent character-level state, and a "chronically represented state" probe generalised poorly. — [Emotion Concepts in an LLM](https://arxiv.org/html/2604.07729v1)
- Activation steering, small models: on Llama 2 (7B, 13B) and Mistral 7B, diff-of-means is the best extraction method over probes and patching; middle-to-late layers (10-20 of 32) work best; coefficients around 0.5-2.0; coherence degrades slightly at higher strengths while meaning is largely preserved. — [Extracting and Steering Emotion Representations in Small LMs, arXiv 2604.04064](https://arxiv.org/pdf/2604.04064)
- Tooling: repeng trains control vectors from paired contrastive prompts in under a minute, exports GGUF for llama.cpp, shows graduated strengths (-2.2, 1, 2.2) with degradation at the extreme, and does not work on MoE models. — [repeng](https://github.com/vgel/repeng). llama.cpp ships `cvector-generator` (PCA default or `--method mean`, CPU-capable, optional `-ngl`) and loads vectors with `--control-vector-scaled FILE 0.8 --control-vector-layer-range 10 31`, noting vectors work better on layers above 10. — [cvector-generator README](https://github.com/ggml-org/llama.cpp/blob/master/tools/cvector-generator/README.md)
- llama-server: control vectors are set by startup flags (`--control-vector`, `--control-vector-scaled`, `--control-vector-layer-range`) with no per-request control (LoRA adapters do have per-request `lora`); `temperature` and `logit_bias` are per request; `cache_prompt`, slot save/restore exist. — [llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
- Roleplay personas keep an Assistant-associated feature core in SAEs while story characters do not, and the Assistant can drift into and out of immersive simulation; this explains drift toward "assistant" warmth in emotional roleplay. — [Many Are My Names](https://arxiv.org/abs/2608.07852)
- A critique paper argues Claude's emotion representations are consistent and discrete but do not produce the dynamic reorganisation (attention, decision speed, motivation) of biological emotion; i.e. "functional" only. — [Do Large Language Models Have Emotions?](https://arxiv.org/abs/2606.14742)
- Persona drift toward the default Assistant is worst in intimate/emotional scenes; re-injecting persona near the end of context is the cheap counter. — [phase-1 note 04](04_persona_fidelity.md)

### Inferences
- Prompt shape (design): put the inner-state block late in context (near the last turn), as a short "how {name} feels right now, and how it shows" block containing: named felt emotion(s) and mood word, what to display vs hide and the tell, an active worry topic if any, and 2-4 style directives derived from V/A/D (e.g. low A: slower, shorter, trailing; high A: clipped, fast, punctuation; low V: less warmth, more deflection; low D: hedging, deferring, asking permission). State the "show, don't state" rule so emotions appear in behaviour rather than narration.
- Control vectors are a premium local-only option: one or two pre-baked axes (calm-anxious/tense, low-high arousal, or valence) at low coefficients (~0.5-1.0 in the small-model paper's terms), applied at server start. Because llama-server cannot change them per request, per-turn modulation would need either a small set of server profiles/restarts (slow, model reload) or in-process llama.cpp bindings (not verified here). A changed activation pass probably invalidates prefix-cache reuse (my inference). They add negligible VRAM (one vector per layer) but risk coherence loss, and they are unavailable on HF Inference Providers. Given Anthropic's finding that representations follow the operative emotion in context, steering is best seen as a *bias* that complements, not replaces, the prompt block.
- Sampler: no source found on emotion-conditioned temperature. If used at all, a tiny arousal-linked change (per-request `temperature`) is harmless and free but should be treated as untested cosmetics; `logit_bias` on tell-words is a similar untested idea.
- "Style tokens" / fine-tuned emotion control tokens: no source retrieved; skip for v1.

### Gaps
- No controlled evidence that emotion-conditioned sampler temperature improves perceived emotionality.
- No published test of control vectors for *character* emotion in multi-turn roleplay (Anthropic's and the small-model paper test output shifts/preferences), nor with dynamic per-turn scaling.
- Whether llama.cpp exposes runtime control-vector setting via its C API or a newer server endpoint was not verified (README snapshot says startup-only).

---

## 7. Cheap emotion classification of user messages: small classifiers vs asking the LLM

### Takeaway
A quantised GoEmotions ONNX model (about 125 MB, CPU, tens of ms to a few hundred ms) is a good free signal of the *user's* expressed emotion for contagion and event valence, but it is noisy (F1 ~0.45) and cannot do the character's subjective appraisal; use it as an input, not as the character's feeling.

### Cited Findings
- GoEmotions: 58k Reddit comments, 27 emotions plus neutral, BERT baseline average F1 0.46, "much room for improvement". — [GoEmotions](https://arxiv.org/abs/2005.00547)
- `SamLowe/roberta-base-go_emotions-onnx`: 28 labels; ONNX 499 MB vs INT8 125 MB; at the fixed 0.5 threshold, F1 0.450 (fp) vs 0.447 (INT8); INT8 about 2x faster than fp ONNX at batch 1 on an 8-core 11th-gen i7 and about 5x faster than standard Transformers. — [model card](https://huggingface.co/SamLowe/roberta-base-go_emotions-onnx)
- SillyTavern's expression extension default is a ~100 MB local sentiment model (`Cohee/distilbert-base-uncased-go-emotions-onnx`, 28 labels; also a 6-label BERT), or the connected LLM, or WebLLM; it returns only the top label to pick a sprite. — [SillyTavern docs](https://docs.sillytavern.app/extensions/expression-images/). That DistilBERT model is distilled from a zero-shot pipeline on unlabeled GoEmotions and is expected to perform below fully supervised models. — [model card](https://huggingface.co/Cohee/distilbert-base-uncased-go-emotions-onnx)
- Front Porch offers an LLM path (deeper accuracy) or a lightweight ONNX classifier (~300 ms, fully offline) for emotion classification from chat context. — [Front Porch README](https://github.com/linux4life1/front-porch-AI/blob/main/README.md)
- LLMs recognise negative emotions as well as human observers but positive ones poorly, and emotion-prediction scores overstate appraisal ability. — [CAREBench](https://arxiv.org/html/2605.17176)
- Hume EVI measures user expression from sentence-level expression measures and prosody, and adapts response tone to the user's detected vibe. — [Hume EVI docs](https://dev.hume.ai/docs/speech-to-speech-evi/overview)

### Inferences
- Where classifiers help: (1) user-affect input to the appraisal step (a 28-way score vector adds a grounded hint to the prompt at ~0 LLM cost), (2) gating: skip or trigger the LLM appraisal when the message is emotionally neutral vs salient, (3) UI expression sprites for the *displayed* state (a classifier over the character's own reply is what SillyTavern effectively does).
- Where they fail: Reddit-trained, so roleplay prose with `*asterisk actions*`, sarcasm, in-fiction subtext and cross-character speech are out of domain; single top label loses intensity; no notion of who the message is directed at or what it means *to this character* (a compliment is a threat to a character who distrusts kindness). So: classifier for the user's expression, LLM/rules for the character's appraisal.
- Classification on CPU also keeps the 8 GB GPU free for the reply model, unlike an LLM classification call that competes with generation.

### Gaps
- No Kataki-domain accuracy data; must be measured on roleplay text.
- No measured CPU latency for the exact target hardware (only the model card's relative speedups and Front Porch's ~300 ms).
- No head-to-head accuracy of a 7-14B LLM classifier vs GoEmotions models on roleplay text.

---

## 8. Existing products and projects

### Takeaway
No product publishes a validated design. Front Porch's Realism Engine is the closest open, local-first analogue (mood inertia, bond/trust, needs, per-member group state, optional ONNX classifier vs LLM evals); SillyTavern only classifies for sprites; Hume measures the *user's* affect; Inworld is marketing-level.

### Cited Findings
- Front Porch AI Realism Engine: tracks bond, trust, emotion with inertia, needs (hunger, energy, social, fun, hygiene, comfort), arousal/lust, fixations ("active emotional obsessions that colour every response"), likes/dislikes. State reaches the model through the system prompt; trust modulates openness. Runs extra short AI evaluations after each turn (One-Shot Eval fuses them, Auto/On/Off), or ONNX classifier path; off by default for singles, on by default for groups; sidebar shows bond/trust/arousal deltas as chips. Documentation gives no minimum model size or prompt-safety detail. — [README](https://github.com/linux4life1/front-porch-AI/blob/main/README.md); [FAQ](https://frontporchai.app/docs/faq/)
- SillyTavern expression classification: see section 7 (local 28-label DistilBERT default, LLM option, top label only). — [docs](https://docs.sillytavern.app/extensions/expression-images/)
- Hume EVI: user expression measures + prosody guide response tone; low latency through co-located fast models. — [Hume docs](https://dev.hume.ai/docs/speech-to-speech-evi/overview)
- Inworld Character Engine's "Character Brain" manages personality, memory, goals and emotions across 30+ models; public detail is marketing-level (per phase-1 research). — [NVIDIA blog](https://blogs.nvidia.com/blog/generative-ai-npcs/); [phase-1 note 03](03_cognitive_architectures.md)
- Humanoid Agents: needs + seven emotions + closeness on top of Generative Agents. — [ACL Anthology](https://aclanthology.org/2023.emnlp-demo.15/)

### Inferences
- Front Porch's "after each turn" evaluation is the same lagged-update pattern proposed below; its user-visible chips are a good UI precedent (small, delta-based, explained).
- The differentiators available to Kataki over Front Porch: story-clock decay through time skips, an explicit felt/displayed split with a Peek surface, the worry/rumination module, and displayed-emotion contagion in groups.

### Gaps
- Replika and Nomi: no reliable public description of their mood mechanics retrieved (search budget ran out). Treat as unknown.
- Front Porch's actual update maths and prompt text are not documented in the pages read (source code not inspected).

---

## 9. Recommended design for Kataki

### Takeaway
Build a deterministic affect core in code (temperament + decaying mood + emotion stack + worry list + felt/displayed regulation) updated by a cheap "lagged" appraisal; feed the reply model a short late-context block of words and behaviours; ship a zero-extra-LLM-call default and an opt-in premium mode with a structured pre-reply appraisal (and optional local control vectors).

### Cited Findings
(Design rests on the sourced findings in sections 1-8; nothing new is claimed here. Key anchors: Chain-of-Emotion two-call pattern [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11086867/); CPM-MultiAgent cost and marginal gain [arXiv](https://arxiv.org/html/2607.07824v1); Sentipolis decay and label-injection ablation [arXiv](https://arxiv.org/pdf/2601.18027); ALMA temperament/mood recipe [DFKI](https://alma.dfki.de/papers/aamas05.pdf); CAREBench weak control/certainty [arXiv](https://arxiv.org/html/2605.17176); steering evidence on 7-13B [arXiv](https://arxiv.org/pdf/2604.04064) and llama-server limitation [README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md); Front Porch precedent [GitHub](https://github.com/linux4life1/front-porch-AI/blob/main/README.md).)

### Inferences

**A. Options compared** (latency figures are my estimates for a 7-14B Q4 model on an 8 GB GPU at roughly 30-60 tok/s generation; cloud calls are typically 0.5-3 s; none measured)

| Option | Extra LLM calls/turn | Compute | Added latency (est.) | Works on 7-14B local | Quality evidence |
|---|---|---|---|---|---|
| 0. Persona prompt only (static mood text) | 0 | none | 0 | yes | baseline; state-blind flat characters ([note 01](01_what_makes_humans_human.md)) |
| 1. Rules + CPU classifier -> PAD dynamics (ALMA-like) | 0 | CPU ~10-300 ms | ~0 (hidden) | yes | ALMA design, plausibility studies old; Sentipolis shows PAD+decay helps continuity with big models |
| 2. Self-label tail: reply model appends a short `[feel: ...]` tag parsed into state | 0 (+10-20 output tokens) | GPU | +0.3 s | probably; small models may mislabel | no direct evidence; CAREBench warns about self-generated reasoning |
| 3. Lagged appraisal: one short JSON call after the reply, in background | 1 (off critical path) | GPU shared, ~60-120 output tokens | 0 visible, but occupies GPU and can delay next turn | yes | Chain-of-Emotion pattern (83% vs 57% STEU, small user study); Front Porch runs per-turn evals |
| 4. Pre-reply appraisal (CoE exactly) | 1 (critical path) | GPU | +1-3 s local | yes | same as above; freshest state |
| 5. CPM multi-agent | 7-8 | GPU heavy | 6-15 s even on cloud | impractical | +0.044 EUC over zero-shot, human preference in 24 trials |
| 6. Control vectors (added to any of the above) | 0 | tiny VRAM, per-token negligible | ~0 | yes (7-13B tested), local only, static per server, MoE unsupported | causal steering shown; coherence loss at high strength; not tested for character loops |
| 7. Sampler temperature by arousal | 0 | none | 0 | yes | none found |

**B. State schema** (per character, per scene; persist with the chat)

```
Temperament (authored/derived once)
  base:        {v, a, d}            // ALMA default mood from Big Five, or authored
  reactivity:  0..1                 // gain on appraisal deltas (higher with neuroticism)
  inertia:     mood half-life, story-hours (default 6; 2..24)
  anxiety:     0..1                 // trait; default low (most characters ~0.1-0.3)
  attachment:  {anxiety 0..1, avoidance 0..1}  // per-relationship overrides allowed
  coping:      0..1
  regulation:  {style: express|suppress|reappraise|avoid, capacity 0..1}
  susceptibility: 0..1              // contagion
AffectState
  t:           story timestamp of last update
  mood:        {v, a, d}            // slow
  emotions:    [{label, intensity 0..1, target, cause, t}]   // max 3, story-min half-life
  worries:     [{topic, kind: anticipatory|relational|ruminative, weight 0..1, since, resolvable}] // max 2
  regLoad:     0..1                 // suppression debt
  felt:        {label, v, a, d, intensity}     // derived
  displayed:   {label, intensity, leak?: string}  // derived via regulation
```
Relationship edge (already planned bond/trust): add `openThread` (unanswered message / pending outcome) and `lastContactT` so time skips can raise relational worry.

**C. Update rule** (all constants are tunable defaults)
1. Decay to a moment `t_now` (turn or time skip): `emotion.intensity *= 2^(-dt/T_e)` (T_e ~ 20 story-min); `mood = base + (mood - base) * 2^(-dt/T_m)` (T_m = inertia, lengthened when a ruminative worry exists); remove emotions below 0.05; worries follow their own rule (resolution or slow habituation, T ~ 1-3 days).
2. Appraisal event (from cheap rules, classifier, or LLM JSON): `{label, intensity 0..1, valence, relevance, congruence, target, cause, threat?{certainty, control}}`. Convert to a PAD delta with a small label-to-PAD table (ALMA-style anchors, own tuning) x intensity x `reactivity`.
3. Push into mood: `mood += k_m * (pad_delta - mood_component) `, or ALMA-style pull/push toward the emotion center; k_m ~ 0.15-0.3 per salient event; clip to [-1,1]. Add mood-congruent bias to the *next* appraisal (negative mood inflates threat and negative-valence intensity by a small factor).
4. Worry management (section 3): create/strengthen a worry only if relevance high, valence negative, certainty low, control low (control/certainty from rules first); apply reassurance rebound; resolution deletes the worry and emits relief.
5. Regulate: compute `displayed` from `felt` with the character's strategy; update `regLoad`; check spill-over threshold.
6. Contagion (groups): `mood_i += susceptibility_i * closeness_ij * displayed_j.intensity * pad(displayed_j.label)`.
7. Time skip: apply closed-form decay; if any worry or emotion above threshold, optionally make one "what happened offscreen" call (premium) or emit a templated line (default).

**D. How it reaches the prompt** (short, late in context, words not numbers)
```
[Inner state of {name} right now - show through behaviour, do not announce]
Feeling: {label1 (strong)}, {label2 (faint)}; overall mood: {mood word} since {cause}.
Outwardly: {displayed}. Hiding: {felt-but-masked}; tell: {leak}.
On their mind: {worry topic, kind}.
Voice: {2-4 directives from V/A/D and regulation, e.g. clipped, deflects questions, seeks confirmation}.
```
Label words come from a small PAD-to-word table (Sentipolis-style, without kNN data). Include only what changed materially; omit the block when the state is near baseline so calm characters stay natural. Re-inject every turn (Assistant-drift counter).

**E. UI**
- Scene: a small mood chip by the character (word + trend arrow, Front Porch-style delta chip), tinted by valence/arousal; expression art chosen from the *displayed* state.
- Peek: shows felt vs displayed side by side, the condensed inner-speech worry/rumination line, and what they are holding back; this is where masking becomes readable.
- Backstage: numbers (V/A/D sparkline over story time), emotion stack, worry list with "resolve" and "edit" controls, temperament sliders, and a "why did this change" line per delta; manual override for the user.
- Groups: an atmosphere strip and per-character chips; contagion arrows optional in Backstage only.

**F. Cheap default ("Mood Lite") - 0 extra LLM calls**
- CPU INT8 GoEmotions classifier on the user message -> user-affect vector.
- Rule-based appraisal from: user-affect valence, character likes/dislikes and triggers (authored), open-thread/time-gap for relational worry, keywords for known worry topics.
- Full state machine (decay, mood, worry, regulation, contagion) in code; templated prompt block; no gating LLM calls.
- Optional Option-2 tail tag if a given model handles it reliably (test on the user's models).
- Cost: ~100-300 ms CPU per message, ~120 MB model, no VRAM; latency hidden.

**G. Premium mode ("Mood Full")**
- Lagged or pre-reply appraisal call (one fused structured-JSON call covering all responding characters in a group), run on a cloud model (or local where latency allows), with rule-derived control/certainty passed in as given rather than asked.
- Offscreen call on time skips when worries/emotions are active; reappraisal pass for characters with that regulation style.
- Optional local control vectors (one arousal or tension axis) at low coefficients, fixed per server profile.
- Cost: +1 call per turn (short JSON, ~150-250 prompt + 60-120 output tokens; with prefix caching mostly output), +1 occasional; no CPM-style fan-out.
- Ship gating: only call the LLM appraisal when the classifier or rules flag a salient event, otherwise use the rule path (cuts most calls; my proposal).

**H. Build order** (thin vertical slices, per the show-first methodology): (1) state + decay + prompt block + mood chip with hand-set events; (2) classifier and rule appraisal; (3) Peek felt/displayed; (4) worry module and time-skip behaviour; (5) premium appraisal call; (6) group contagion; (7) control-vector experiment behind a flag. Evaluate against "persona only" and "zero-shot one call" baselines with a fixed scenario script (delayed reply, insult, good news, time skip, masked distress) and an LLM judge on continuity, proportionality and leakage, plus manual review.

### Gaps
- All constants (half-lives, gains, thresholds, leak curves, PAD anchors) need tuning against Kataki's own scenarios; none are validated.
- Behaviour on Kataki's actual local models is unmeasured for options 2-4; prototype before committing to the premium call's JSON schema.
- Whether prefix caching survives per-turn prompt-block changes at the end of context is expected (block is last) but not measured.
