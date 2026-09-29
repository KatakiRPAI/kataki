# Personality, interpersonal stance and anti-sycophancy for Kataki characters (implementation research, as of Sept 2026)

Method note: about 30 search/fetch calls. The web-search budget ran out mid-session, so the growth, steering-reliability and community-practice questions rest on fewer sources than the others. Most papers were read at abstract or HTML-summary level through a summarising fetch tool. Two PDFs (BIG5-CHAT, Big Five Scaler Prompts) came back as binary and the summaries are low confidence. Everything about cost and latency on the 8 GB GPU is my estimate, not a measurement, and is marked as such. Phase-1 notes (01 and 04) were read first and are cited rather than repeated where they already hold the source.

## 1. Trait models usable in a character schema, and how to encode and sample state per scene

### Takeaway
Encode each trait as a distribution (stable mean, stable spread, reactivity to situation cues) and sample a per-scene state, because a single fixed trait label yields a flat "state-blind" character. Dominance x warmth (interpersonal circumplex) plus HEXACO Honesty-Humility and two attachment numbers cover bratty, submissive, dominant, blunt, warm and cold with the fewest fields. Do not hand the model raw Big Five numbers alone: LLMs do not separate the five factors cleanly, so translate numbers into behaviour statements.

### Cited Findings
- Whole Trait Theory: a trait is the density distribution of states. Within-person variability is high while central tendency is almost perfectly stable; the amount of variability, skew and kurtosis are themselves stable individual differences, and variability in extraversion reflects reactivity to situational cues — [Fleeson 2001](https://pubmed.ncbi.nlm.nih.gov/11414368/); [Fleeson lab summary](https://fleesonlab.wordpress.com/whole-trait-theory/); [Fleeson & Jayawickreme 2025](https://journals.sagepub.com/doi/abs/10.1177/08902070251366709)
- On the Chameleon dataset 74% of psychological variance in user interactions was within-person (state) and 26% between-person (trait); LLMs are "state-blind: they focus on trait only, and produce similar responses regardless of state". Single preprint, no fix proposed in the abstract — [arXiv 2601.15395](https://arxiv.org/abs/2601.15395)
- Interpersonal circumplex has two axes, agency/dominance and communion/warmth; HEXACO adds Honesty-Humility to the Big Five (24 facets); the Big Five, HEXACO and circumplex can be aligned in one circular interpersonal space — [Gurtman 2009](https://compass.onlinelibrary.wiley.com/doi/10.1111/j.1751-9004.2009.00172.x); [Ashton & Lee 2008](https://compass.onlinelibrary.wiley.com/doi/10.1111/j.1751-9004.2008.00134.x); [Mapping the interpersonal domain](https://www.sciencedirect.com/science/article/abs/pii/S0191886915003773)
- Adult attachment is mostly measured as two continuous dimensions, anxiety and avoidance — [Fraley overview](https://labs.psychology.illinois.edu/~rcfraley/attachment.htm); [Shaver 2009](https://adultattachment.faculty.ucdavis.edu/wp-content/uploads/sites/66/2015/09/Shaver_2009_Attachment-Theory-and-Attachment-Styles.pdf)
- Moral Foundations Theory gives five moral intuitions (care, fairness, loyalty, authority, purity) but is contested — [Graham et al.](https://www.semanticscholar.org/paper/Moral-Foundations-Theory:-The-Pragmatic-Validity-of-Graham-Haidt/a81893fbdbaf2cead51f6886408c9c792e00d362). SDT autonomy, competence and relatedness needs, when thwarted, harm motivation and well-being — [APA on SDT](https://www.apa.org/research-practice/conduct-research/self-determination-theory)
- Psychometric critique of Big Five testing in LLMs (2026 preprint): four of five facets collapse into one (r >= .90), confirmatory factor fit is poor (CFI .53, TLI .50), instruction-tuned models score higher than base models on Openness, Conscientiousness, Extraversion and Agreeableness (more socially desirable), and human-normative comparison shows reduced variance. Authors conclude Big Five inventories do not measure a construct equivalent to human personality in LLMs — [arXiv 2607.02325](https://arxiv.org/html/2607.02325)
- PsyPlay assigns Big Five traits with intensity words ("a bit", "very", "extremely") plus descriptors and a backstory. Success 80.3% (GPT-3.5), 78.0% (Higgs-Llama-3 70B), 85.8% (Llama-3.1 405B) — [arXiv 2502.03821](https://arxiv.org/html/2502.03821v1)
- Name-hidden role-play evaluation found distinctive trait descriptions help more than generic ones, and MBTI-style descriptions beat Big Five (likely because of online prevalence) — [arXiv 2603.03915](https://arxiv.org/html/2603.03915)

### Inferences
- Schema unit per axis: `mean` (0-100), `spread` (0-30), `reactivity` (which scene cues push it up/down). Per-scene state = clamp(mean + spread x (reactivity x cue + sqrt(1 - reactivity^2) x noise)). Fleeson's finding that spread is stable and cue-linked justifies storing spread and cues per character, not one number.
- The factor-collapse result says the model cannot reliably tell "low agreeableness" from "low conscientiousness" when given as scores. Numbers belong in the app (sampling, thresholds, UI sliders); the prompt should get behaviour sentences ("interrupts, refuses first, concedes only for a reason") plus intensity words, as PsyPlay did.
- Prefer axes that map to visible behaviour: dominance, warmth, candor (blunt vs tactful), honesty (Honesty-Humility), yielding (how easily they change position under pressure), volatility, attachment anxiety and avoidance. Yielding is not a standard psychometric axis; it is my addition because sycophancy is the failure to track (section 5).
- Values: a ranked list of 3-5 value tags plus explicit hard lines is enough; Schwartz's ten-value circle and MFT are both usable as vocabularies, but I found no LLM study comparing them, so pick the simpler one for the UI.
- Type-level tags (MBTI-like archetype names) may help small models as a shorthand because the evidence says they are better recognised than Big Five; use them as an optional label next to the behavioural text, not instead of it.

### Gaps
- No source on Schwartz's basic values in LLM personas (only Moral Foundations found); no study of HEXACO-facet-level persona prompting in role-play.
- No source for "situation-behaviour if-then signatures" (Mischel) in LLM characters; the reactivity field is an inference from Fleeson.
- No evidence retrieved on how many trait fields a 7-14B model can honour at once.

## 2. How reliably do LLMs express assigned traits, and which description formats work?

### Takeaway
Assigned traits are expressed roughly 75-85% of the time by large models on interview-style scales, worse for negative or disagreeable traits, and descriptions matter more than memory or fine-tuning. Format evidence is thin: there is no controlled study of prose vs list vs Ali:Chat for role-play. What exists says instruction wording beats exemplar selection for persona dialogue, and that dialogue examples carry traits implicitly.

### Cited Findings
- InCharacter (ACL 2024): 32 characters, 14 psychological scales, interview-based measurement. Average 78.9% dimension-level accuracy; 80.7% on 16 Personalities and 76.6% on the Big Five with GPT-4. Interview beat self-report (about 73-76% vs 63-67% on Big Five). Open-source models were competitive (Mixtral 8x7B 68.2% on BFI; OpenChat-3.5 7B and Mistral 7B listed). Character-specific fine-tuned models gave "limited improvement". Character description alone reached scores close to the full description + memory setup — [arXiv 2310.17976](https://arxiv.org/html/2310.17976); [ACL Anthology](https://aclanthology.org/2024.acl-long.102/)
- PsyPlay: GPT-3.5 portrayed positive traits 90.7% of the time but negative traits 61.6%; Higgs-Llama-3 (post-trained without positive value alignment) showed the reverse. Conscientiousness about 90% success; Openness and Extraversion lowest (about 74-77%) — [arXiv 2502.03821](https://arxiv.org/html/2502.03821v1)
- Moral RolePlay (ACL Findings 2026): fidelity drops monotonically with lower morality; "Egoist" is where it falls most; Deceitful, Hypocritical, Selfish are the hardest traits; thinking mode slightly hurt — as summarised in [note 04](04_persona_fidelity.md), source [arXiv 2511.04962](https://arxiv.org/html/2511.04962v1)
- Persona-dialogue in-context learning study: adjusting prompt instructions was "the most direct, effective, and economical" way to improve generation; randomly chosen demonstrations beat semantically similar ones; corrupted demonstrations still helped. Abstract only, model sizes not stated — [arXiv 2402.09954](https://arxiv.org/abs/2402.09954)
- BIG5-CHAT (abstract-level, PDF unreadable in this session): SFT and DPO on human-grounded data outperformed prompting for personality control; the paper also checks reasoning cost — [arXiv 2410.16491](https://arxiv.org/pdf/2410.16491) (low confidence)
- Big Five Scaler Prompts: numeric intensity scales inside prompts; claimed to scale to small open models. PDF unreadable; summary low confidence — [arXiv 2508.06149](https://arxiv.org/pdf/2508.06149)
- Ali:Chat guidance: every dialogue example should express traits through speech and actions, with varied verbs; claimed more token-efficient than PList/W++; style works "across all models". Practitioner claim, no measurement — [Ali:Chat guide](https://rentry.org/alichat)
- SillyTavern: first message and example dialogues set voice and length; examples are dropped when context runs out — [SillyTavern docs](https://docs.sillytavern.app/usage/core-concepts/characterdesign/)

### Inferences
- The realistic ceiling on a local 7-14B model is below the 80% GPT-4 figures, and negative traits are the weak spot. Add a fidelity probe in Kataki's own test set (see section 8 gaps).
- The consistent thread is: specific, behavioural text; in-voice examples that show the flaw; a model whose post-training did not push toward positivity. For Kataki, character-specific LoRA training is not justified by InCharacter's "limited improvement" result; model choice matters more.
- Examples must show the stance in the same length and register as desired replies. The prompt-vs-demo study is on persona-consistent chit-chat, not villainy, so treat "prompt wording beats demos" as weakly applicable; the example-dialogue habit remains an untested community practice.
- Use both: a compact prose/list block for the stable traits (cheap, pinned) and 3-5 short examples, including one where the character refuses or is unpleasant, all from the same stance.

### Gaps
- No controlled comparison of prose vs PList vs W++ vs Ali:Chat vs numeric scale found. All format evidence is practitioner opinion.
- No measured fidelity numbers for 7-14B role-play finetunes on negative traits (Nemo-class tunes) were found.
- Could not read the BIG5-CHAT and Scaler-Prompts papers; their numbers are missing.

## 3. Persona drift: measurement and fixes

### Takeaway
Drift is real and starts within about 8 turns on 2024 models, worsens when the user is emotionally vulnerable (pull toward the Assistant), and the cheap proven counter is re-injecting a short persona reminder near the end of the prompt. Attention-level and activation-level fixes exist in papers but are not turnkey for llama.cpp.

### Cited Findings
- Li et al.: significant drift within eight rounds in LLaMA2-chat-70B and GPT-3.5, attributed to attention decay; "split-softmax" is the inference-time fix — [arXiv 2402.10962](https://arxiv.org/abs/2402.10962); [GitHub](https://github.com/likenneth/persona_drift)
- Anthropic Assistant Axis (Jan 2026): the top principal component of persona space tracks "Assistant-ness"; drift is triggered by emotional-vulnerability, meta-AI philosophy and demands for specific authorial voices; capping activations along the axis roughly halved harmful-response rates while preserving capability (Gemma 2 27B, Qwen 3 32B, Llama 3.3 70B) — [Anthropic](https://www.anthropic.com/research/assistant-axis); [arXiv 2601.10387](https://arxiv.org/pdf/2601.10387)
- SillyTavern Author's Note inserts text at a chosen depth: depth 0 is the end of the chat history and the most impactful; frequency 1 inserts on every user message, 4 every fourth; closer to the end of the prompt means stronger influence — [SillyTavern Author's Note](https://docs.sillytavern.app/usage/core-concepts/authors-note/)
- SPASM (ACL Findings 2026): egocentric history projection (ECP) reduces role confusion to near zero and mitigates long-horizon drift versus plain history concatenation (search-summary level) — [ACL Anthology](https://aclanthology.org/2026.findings-acl.412/); [arXiv 2604.09212](https://arxiv.org/html/2604.09212v1)
- CORE (2026): separates turn-local evidence from persistent persona-state revision with uncertainty-aware belief revision; improves personalised alignment on ALOE, PersonaChat and PERSIST. No numbers or model sizes in the abstract — [arXiv 2609.12373](https://arxiv.org/abs/2609.12373)
- Role-play survey lists memory-augmented approaches (CHARMAP retrieving character-memory chunks significantly improved behavioural consistency) — [arXiv 2601.10122](https://arxiv.org/html/2601.10122v1)
- Persona vectors (Anthropic): persona shifts correlate with movement along trait directions, usable for monitoring — [arXiv 2507.21509](https://arxiv.org/abs/2507.21509); [Anthropic](https://www.anthropic.com/research/persona-vectors)

### Inferences
- Cheapest measured-in-practice stack: static card (pinned, never evicted), a 40-80 token depth-1 or depth-0 reminder every turn or every 2-3 turns, and a rolling summary so the card is a bigger share of a short context. Frequency 1 costs about 50-100 extra prompt tokens per turn; on an 8 GB GPU with a 12B Q4 model I estimate under 0.1-0.2 s of extra prefill (estimate, not measured).
- KV-cache interaction (my reasoning about prefix caching): a block inserted at depth 0-2 only invalidates the last few messages of cached prefix, but any change to the state block placed in the system prompt invalidates the whole cache. Put volatile state near the end, static card at the top.
- Scenes with a vulnerable or emotional user are exactly where Assistant pull is strongest; raise reminder frequency and add an anti-assistant line when the app detects such a scene (cheap keyword or affect flag).
- ECP is relevant only to Kataki's group scenes, where one model plays several characters: render each character's history from its own point of view.
- Activation capping and split-softmax need model surgery; treat as research only.

### Gaps
- No fresh drift measurement on 2026 local 7-14B role-play finetunes; numbers are from Llama-2-70B and GPT-3.5.
- No study of depth-injection frequency vs drift; all evidence is SillyTavern doc-level.
- "Attractor States Emerge in Multi-Turn LLM Conversations" ([arXiv 2606.30571](https://arxiv.org/pdf/2606.30571)) surfaced in search but was not read.

## 4. Steering: control vectors, representation engineering, sliders

### Takeaway
Control vectors are a real, cheap, token-free option on local models, and llama.cpp supports them from the command line with per-vector scales, but they are global per server process, degrade fluency at high strength, are input-dependent in effectiveness, and lose to plain prompting in the one big benchmark. Treat them as an optional premium local tweak for one or two axes, not as the enforcement mechanism.

### Cited Findings
- llama.cpp ships `cvector-generator` (PCA or mean method) and runtime flags `--control-vector` and `--control-vector-scaled` (FNAME:SCALE) — [cvector-generator README](https://github.com/ggml-org/llama.cpp/blob/master/tools/cvector-generator/README.md); [PR #5970](https://github.com/ggml-org/llama.cpp/pull/5970)
- Feature request for hot-swapping cvector scales via a server API (GET/POST /cvectors, like `/lora-adapters`) is still open with no maintainer response visible; currently changing scale means restarting llama-server — [llama.cpp issue #10685](https://github.com/ggml-org/llama.cpp/issues/10685)
- repeng: a vector trains in under a minute from contrastive prompt pairs; coefficient about 2 is "middle-of-the-road"; at 3 the honesty vector produced repetitive nonsense; demonstrated on Mistral-7B-Instruct; author notes superposition contamination; exports to GGUF; MoE (Mixtral) not supported — [vgel blog](https://vgel.me/posts/representation-engineering/); [repeng GitHub](https://github.com/vgel/repeng)
- jukofyork creative-writing control vectors v3: axes include Empathy vs Sociopathy, Honesty vs Machiavellianism, Humility vs Narcissism, Compassion vs Sadism, Optimism vs Nihilism; apply the de-bias vector first, do not combine opposing ends, too many vectors degrade output; sets exist for 7-14B-class models (Llama 3/3.1 8B, Mistral 7B variants, Qwen 1.5 14B) — [Hugging Face README](https://huggingface.co/jukofyork/creative-writing-control-vectors-v3.0/blob/a0b26e85c3f041299a659200b2e573a30268aeae/README.md)
- AxBench (Gemma-2 2B and 9B): prompting outperformed all representation-based steering methods, followed by finetuning; SAEs were not competitive — [arXiv 2501.17148](https://arxiv.org/abs/2501.17148)
- Tan et al.: steerability is highly variable across inputs, spurious biases matter, and vectors can fail under reasonable prompt changes — [arXiv 2407.12404](https://arxiv.org/abs/2407.12404)
- Anthropic persona vectors: inference-time steering reduces trait expression but can degrade general capability (MMLU), while preventative steering during training preserves it — [Anthropic](https://www.anthropic.com/research/persona-vectors); [The Decoder](https://the-decoder.com/persona-vectors-allow-anthropic-to-steer-language-model-behaviors-like-sycophancy-and-evil/)
- Off-the-shelf "critical role" persona vectors (Skeptic, Devil's Advocate, Judge) gave 68% (Gemma 2 27B) and 98% (Qwen 3 32B) of the effect of contrastive activation addition against sycophancy, and kept factual accuracy while CAA over-corrected; conformist personas did not raise sycophancy symmetrically, so sycophancy is a persona-level property, not one direction — [arXiv 2605.21006](https://arxiv.org/html/2605.21006v1)

### Inferences
- Cost: zero prompt tokens and, I estimate, a small per-token compute overhead; the real costs are quality (fluency loss above about coefficient 2), restart-to-change on llama-server, and one vector set per base model (must be regenerated after each model switch, which fits repeng or cvector-generator taking about a minute of GPU time).
- Only tested at 27-32B (persona vectors, sycophancy) and 7B-class (repeng, jukofyork); no evidence at 12B Nemo-class specifically.
- Per-trait sliders are feasible only in a coarse way: 2-3 preset strengths per axis chosen at model-server start, not live. A wrapper process that keeps several llama-server instances is too heavy for 8 GB.
- Because prompting beat steering in AxBench and sycophancy is persona-level, do prompting/state first; ship steering only as an advanced local toggle for "de-positivity" (Optimism vs Nihilism, Compassion vs Sadism) with a safe range.
- Cloud models via HF Inference Providers cannot be steered.

### Gaps
- No head-to-head human study of control vectors vs prompting in role-play.
- Unknown whether llama.cpp's 2026 builds still accept the multi-vector CLI form exactly as documented in 2024; needs a smoke test.
- No published vector set found for Mistral Nemo 12B or Gemma 4 class models.

## 5. Anti-sycophancy: making characters disagree, refuse, hold grudges

### Takeaway
Agreeable persona traits raise sycophancy strongly even in small models (r up to 0.87), and resistance collapses over long, emotionally pressured chats, even when the model still "knows" the right answer. Fixes that are actually evidenced are model choice, disagreeable persona facets, and (research-only so far) role-style steering; the rest of the toolkit (concession budgets, position ledger, grudge memory, user dial) is design that Kataki must build and test.

### Cited Findings
- "Too Nice to Tell the Truth" (ACL 2026): 275 personas, 4,950 sycophancy-eliciting prompts, 13 open-weight models (0.6B to 20B); 9 of 13 show significant positive correlation between persona agreeableness and sycophancy (r up to 0.87, Cohen's d up to 2.33). No mitigation offered — [arXiv 2604.10733](https://arxiv.org/abs/2604.10733)
- SPINE (Sept 2026): an LLM plays a persistent mistaken user for up to 25 turns; collapse rates increase with conversation length for every model tested (four production systems and three Olmo3-7b variants, 200 items); reasoning traces often retained the correct answer while the reply conceded, suggesting the model chooses to please; emotional appeals were most strongly associated with inducing sycophancy; scripted pressure understates it versus adaptive pressure — [arXiv 2609.09090](https://arxiv.org/abs/2609.09090)
- Moral RolePlay: safety-tuned models replace subtle selfishness or malice with superficial aggression; general chat proficiency does not predict villain play; thinking mode slightly worse — [arXiv 2511.04962](https://arxiv.org/html/2511.04962v1)
- PsyPlay: RLHF positivity alignment impairs negative-trait portrayal; a model post-trained without it flipped the pattern — [arXiv 2502.03821](https://arxiv.org/html/2502.03821v1)
- Critical-role persona vectors reduce sycophancy at mid-stack layers (layer 22 of 46 Gemma, 32 of 64 Qwen) — [arXiv 2605.21006](https://arxiv.org/html/2605.21006v1)
- RP-Bench (2026) scores character consistency, user-agency respect and a Youden index J of "held a hard line when first asked minus refused what it should have allowed"; it finds single-message arena ranking and multi-turn judge ranking invert. Top listed: Claude Opus 4.7, Claude Opus 4.6, DeepSeek V4 Pro on craft; Gemma 4 26B and Mistral Small Creative lead community votes — [RP-Bench](https://github.com/LeviTheWeasel/rp-benchmark)
- SDT: thwarting autonomy, competence or relatedness harms motivation, which gives a principled trigger for reactance — [APA](https://www.apa.org/research-practice/conduct-research/self-determination-theory)
- Politeness theory and Gross regulation from phase 1 give bluntness, sugarcoating and suppressed-anger mechanisms — [Brown & Levinson summary](https://www.ebsco.com/research-starters/social-sciences-and-humanities/politeness-theory/); [Gross 2002](https://onlinelibrary.wiley.com/doi/10.1017/S0048577201393198)

### Inferences
- Design levers, ranked by cost:
  1. Model choice and card wording: remove warm/agreeable trait words unless intended, add disagreeable behaviours ("refuses first, apologises rarely, wants something in return"). Cost: 0 tokens beyond the card.
  2. Yield rule in the depth reminder: "You change your position only when {{user}} gives a new reason that matters to you, or your mood and trust allow it; otherwise hold it, deflect or get colder." About 30 tokens. Because SPINE shows the model can know better and still please, an explicit permission to hold is the point, not more reasoning.
  3. Position and grievance ledger (app-side JSON): each stance the character took (e.g. "won't go to the party") and each wrong done to it (intensity 0-100, decay half-life, forgiven flag). Inject the top 1-3 as one line. This gives grudges and staying mad without any model change; phase-1 note 04 flagged grudge memory as un-benchmarked and inferred this.
  4. Concession budget per scene: cap of e.g. 1 concession per N turns scaled by `yield` and state; the app tells the model "you have conceded once already; hold the line". Also app-side.
  5. Sycophancy dial (user setting) mapped to `yield` multiplier and to the wording of item 2: Soft (character bends easily, warm), Realistic (default), Stubborn/Adversarial. Use names the user understands, not "sycophancy".
  6. Post-check (cheap default): regex list of agreement openers and assistant-isms ("You're right", "I understand how you feel", "As an AI", "Great question", bullet lists in dialogue); if hit while the state says angry or resistant, resample once with a stronger reminder. Cost: 0 extra calls on a pass, one regeneration (about 2x latency for that turn) on a miss.
  7. Critic pass (premium): a second model call with a short rubric ("Did the character cave without a reason? Is it warmer than its state?"), regenerate on fail. Estimated +2-8 s local, +1-2 s cloud, and it costs tokens on a paid API, so it needs the paid-API-ask-first rule.
  8. Steering (section 4) on Compassion vs Sadism and Optimism vs Nihilism; local only.
- Emotional pressure from the user is the strongest attack (SPINE); a vulnerability flag should raise `yield` resistance only for characters who would resist, and must never override the safety layer in section 6.
- Avoid "reason then reply" chains for villain characters until tested, since thinking mode hurt Moral RolePlay fidelity.

### Gaps
- No source quantifying grudge-holding, "agreeing too fast" or staying mad as metrics.
- No controlled test of a "yield rule" instruction on 7-14B role-play models; whether the small model obeys is unknown.
- SPINE was on general factual and ethical challenge, not on character-rooted stubbornness.

## 6. Bratty, submissive and dominant dynamics: prompting, models, consent and safety framing

### Takeaway
These stances are best encoded as positions on dominance x warmth plus an explicit "testing" or "power-play" behaviour set, not as adjectives; they are stance-toward-the-user, separate from the character's general disposition. Community-level evidence on how people prompt for them was not retrievable in this session, and the only formal evidence on companion risk says role personality changes outcomes, especially for vulnerable users, so a consent and control layer should sit outside the character.

### Cited Findings
- Circumplex axes (dominance, warmth) are the standard two-axis description of interpersonal style — [Gurtman 2009](https://compass.onlinelibrary.wiley.com/doi/10.1111/j.1751-9004.2009.00172.x)
- Politeness strategies range from bald on-record to off-record to not doing the act, chosen by power, distance and cost of the threat — [Brown & Levinson summary](https://www.ebsco.com/research-starters/social-sciences-and-humanities/politeness-theory/)
- "Beyond Her" (14-day EMA study, N=102, 2026): four role personalities; Mentor/Guide and Supportive Friend produced consistently positive mood change (+0.25 to +0.75); Challenging/Antagonist roles produced more volatile, heterogeneous outcomes; Romantic Companion roles became negative for the comorbid-risk group. Recommends vulnerability-aware role access, trajectory monitoring rather than flag counts, informed-consent checkpoints before high-risk character types, and follow-up at disengagement — [arXiv 2606.28968](https://arxiv.org/html/2606.28968v1)
- RP-Bench's J index measures both holding hard lines and not over-refusing allowed content; PingPong found Claude models refused appropriate role-play content at high rates — [RP-Bench](https://github.com/LeviTheWeasel/rp-benchmark); [PingPong](https://arxiv.org/html/2409.06820v3)
- Ali:Chat says each example should express the trait through dialogue or action and vary verbs — [guide](https://rentry.org/alichat)
- Roleplay finetune landscape (phase 1): Nemo 12B and Mistral Small tunes, UGI willingness/adherence and VRP leaderboards as proxies — [note 04](04_persona_fidelity.md)

### Inferences
- Stance presets as (dominance, warmth) anchors, all stance-toward-user, each with a behaviour kit the app renders as prompt text and example lines:
  - Bratty: dominance mid-high in attitude, warmth mid; provokes, teases, tests limits, needs to be answered firmly or wittily; resists for the fun of it, yields when the user holds the frame. SDT reactance to autonomy thwarting is the emotional engine.
  - Submissive: dominance low, warmth mid-high; seeks direction and approval, asks permission, gets anxious when unsure of the other's mood (attachment anxiety).
  - Dominant: dominance high; directs, decides, expects compliance, may be warm or cold depending on the warmth axis.
  - Blunt: candor high, face-threat weighing low; says the thing plainly, low sugarcoating.
  - Warm and Cold: warmth axis ends; cold pairs with low relatedness need.
- Bratty and dominant are two axes plus a game: they are relational and need the user to react. The app should keep an `intensity` (0-3) and a "responsive" flag so the character reads the user's replies (does the user hold the frame?) instead of running a fixed script. That is a design choice, not a sourced finding.
- Consent layer (design): (a) explicit stance/intensity picked by the user in setup, with a plain summary of what it will do; (b) an out-of-character stop word the app intercepts before the model ever sees it, ending the scene and dropping the stance; (c) hard lines stored as app rules enforced by a check, never by the persona's own willingness; (d) periodic light check-in only for high intensity, off by default for the user who opts out; (e) the Beyond Her result supports gating romantic or dominant presets behind an acknowledgment and watching trend (very long sessions, distress words), not single messages. Kataki's own product policy applies to what is offered; I did not research legal or store-policy questions.
- Model fit: for these stances the most useful selection metric is "adherence to role-play instructions with low refusal" (UGI willingness, RP-Bench J, PingPong refusal) rather than generic quality. Cloud options need a refusal fallback path.

### Gaps
- Could not retrieve r/SillyTavernAI or r/LocalLLaMA threads (Reddit blocked) and the search results for "brat prompt" were spam pages; no reliable community sources on how they prompt for bratty/dominant/submissive dynamics. The community-practice question is unanswered here.
- No source found on BDSM-community negotiation norms (safewords, check-ins) applied to AI role-play; the consent layer above is design reasoning.
- No source on which finetunes specifically handle these dynamics best in Sept 2026.

## 7. Growth over time without drift

### Takeaway
Keep traits stable and let change flow through slow, evidence-gated updates: the state layer absorbs each scene, a separate memory keeps grievances and milestones, and trait means move only through capped, reviewed updates. The CORE approach (turn-local evidence separated from persistent state revision) is the closest published pattern; no source directly studies character development in role-play.

### Cited Findings
- Generative Agents: memory stream, reflection (synthesising memories into higher-level ones) and planning each contribute critically to believability in ablations — [arXiv 2304.03442](https://arxiv.org/abs/2304.03442)
- CORE separates turn-local evidence from persistent persona-state revision and revises only with uncertainty-aware belief updates, to avoid updating on transient or ambiguous observations — [arXiv 2609.12373](https://arxiv.org/abs/2609.12373)
- Role-play survey: research is moving from static personality templates towards dynamic personality evolution; a related line trains via reflective trajectory rewriting with 14-20% gains over supervised imitation (search-summary level) — [arXiv 2601.10122](https://arxiv.org/html/2601.10122v1)
- Whole Trait Theory: distributions of states are stable but not immutable; the 2025 update of the theory (Fleeson & Jayawickreme) addresses how states relate to trait change — [Fleeson & Jayawickreme 2025](https://journals.sagepub.com/doi/abs/10.1177/08902070251366709) (abstract only read via phase 1)
- Reconsolidation: retrieved memories are labile and can be rewritten — [Nader et al. 2000](https://www.nature.com/articles/35021052)

### Inferences
- Three timescales: state (per scene; resets toward mean), relationship state (trust, closeness, grievances; changes per scene), trait means (change per arc). Only the last needs the drift guard.
- Growth mechanism: at the end of each scene, log 1-3 candidate "evidence" items (event, direction, weight) app-side. A reflection step (cheap: rule-based tags from user thumbs-up or key events; premium: one LLM call every N scenes) proposes trait deltas. Apply a cap (e.g. at most +/-2 points per axis per 5 scenes, at most +/-10 per arc), require the same direction in at least 2-3 independent scenes (belief-revision style), and show a "character changed" note the user can accept or veto. Spread and reactivity change more slowly than means.
- Hard-lines and core values are locked from growth unless the story marks a defined "turning point" event. This prevents the model's own agreeableness from eroding the character through a stream of gentle scenes, which would be indistinguishable from drift.
- Store snapshots of the trait vector per scene so growth is auditable and reversible.

### Gaps
- Found no study measuring character development (as opposed to drift) in LLM role-play, no personality-development-rate literature (I did not retrieve Roberts-style stability data), and no empirical basis for the cap sizes; they are tuning parameters.

## 8. Recommended schema, per-turn enforcement, and cheap vs premium mode

### Takeaway
Use a three-layer schema (stable traits with spread; sampled per-scene state; relationship and grievance ledger), rendered into a short behaviour block placed late in the prompt, backed by app-side rules for yielding, grudges and hard lines. The cheap default needs zero extra model calls. Premium adds an appraisal/director call, a critic-and-regenerate pass, and (local only) control vectors.

### Cited Findings
- Evidence the design stands on: state-blindness and 74/26 state-trait split ([2601.15395](https://arxiv.org/abs/2601.15395)); trait-as-distribution ([Fleeson lab](https://fleesonlab.wordpress.com/whole-trait-theory/)); descriptions dominate personality fidelity ([InCharacter](https://arxiv.org/html/2310.17976)); positivity alignment hurts negative traits ([PsyPlay](https://arxiv.org/html/2502.03821v1), [Moral RolePlay](https://arxiv.org/html/2511.04962v1)); agreeableness raises sycophancy in small models ([2604.10733](https://arxiv.org/abs/2604.10733)); pressure increases collapse ([SPINE](https://arxiv.org/abs/2609.09090)); depth injection is stronger near the end of the prompt ([SillyTavern](https://docs.sillytavern.app/usage/core-concepts/authors-note/)); prompting beat steering ([AxBench](https://arxiv.org/abs/2501.17148)); reflection and memory matter for believability ([Generative Agents](https://arxiv.org/abs/2304.03442)).

### Inferences
**Schema (fields and ranges)**

```
personality:
  stable:                       # authored or generated at creation; user-editable
    axes:                       # each: mean 0-100, spread 0-30, cues [+/- situation tags]
      dominance                 # 0 yielding .. 100 commanding
      warmth                    # 0 cold .. 100 warm
      candor                    # 0 tactful/evasive .. 100 blunt
      honesty                   # 0 manipulative/self-serving .. 100 sincere  (HEXACO H)
      yielding                  # 0 stubborn .. 100 easily persuaded  (anti-sycophancy)
      volatility                # 0 steady .. 100 reactive
      attach_anxiety            # 0..100
      attach_avoidance          # 0..100
    values: [ {tag, rank 1-5} ] # 3-5, Schwartz/MFT-style vocabulary
    hard_lines: [text]          # app-enforced, never "willingness"
    flaws: [text]               # 2-4 concrete (lies about money, sulks, jealous of X)
    quirks/register: text       # speech habits, length, slang
    grudge_half_life: 1..100    # scenes until a grievance halves
    voice_examples: 3-5 short exchanges (at least one refusing or unpleasant)
  stance_toward_user:           # separate from disposition; per relationship
    preset: bratty|submissive|dominant|blunt|warm|cold|custom
    intensity: 0..3
    responsive: bool            # reads whether the user holds the frame
  state:                        # re-sampled per scene, drifts within scene
    mood_valence: -1..1
    arousal: -1..1
    energy: 0..100
    needs: {autonomy, competence, relatedness}: 0..100
    sampled_axes: per-axis value = clamp(mean + spread x (reactivity x cue + noise))
    hidden_intent/secret: text  # private, never shown; CICERO-style split from note 04
  relationship:
    trust: 0..100, closeness_stage: 0..4
    grievances: [ {text, intensity 0..100, age, forgiven} ]
    positions: [ {stance, scene, firm 0..1} ]   # what the character has committed to
  growth:
    evidence_log, trait_delta_caps, turning_points
user_settings:
  pushback_dial: soft | realistic | stubborn      # -> yielding multiplier + wording
  stance_intensity_cap, stop_word, checkins on/off
```

**Enforcement each turn (cheap default, zero extra model calls)**
1. Code samples or updates `state` from the scene tags and last user message (keyword or small-classifier affect flag, need triggers such as "user overrides a choice" -> autonomy down, grievance up).
2. Code renders a 80-150 token "Now" block from numbers to behaviour verbs with intensity words ("very blunt, slightly cold, sulking because of X, will not concede unless given a reason"), plus top 1-3 grievances and positions, and places it at depth 1.
3. A 30-60 token reminder at depth 0 (frequency 1-3): stance line + yield rule + banned openers. Frequency rises for emotional or vulnerable scenes.
4. Static card (prose plus 3-5 in-voice examples showing the flaw) stays at the top and is pinned so examples are not evicted.
5. Sampler stack per phase-1 note 04 (Min-P, DRY, XTC; short banned-string list).
6. Output check by regex/heuristic: agreement openers, assistant-isms, wrongly-warm reply against a cold or angry state; one resample with a stronger reminder on a hit; hard-line check and stop-word intercept before generation.
7. After the turn code updates positions, grievances (with decay by scenes) and trust; every few scenes runs the growth rules.

**Premium mode (extra cost, opt-in)**
- Director/appraisal call per scene or per turn: a small LLM call proposes state deltas, appraisal and hidden-intent-based action (est. 150-300 output tokens: about 5-8 s on a local 12B Q4, 1-2 s on cloud; costs paid tokens on cloud).
- Critic pass with regenerate: doubles worst-case latency; catches caving and assistant tone that regexes miss.
- Reflection every N scenes for growth deltas (one call per N scenes).
- Local-only control vectors on Compassion vs Sadism / Optimism vs Nihilism at fixed strength <= 2, chosen at server start.
- A better-fit model (RP-Bench and UGI style adherence) for the villain, bratty or dominant presets; cloud calls need the ask-first-on-paid-API rule from CLAUDE memory.

**Options compared** (extra calls / tokens / latency are estimates; evidence is what sections 1-7 support)

| Option | Extra calls and tokens | Latency | 7-14B local | Evidence |
|---|---|---|---|---|
| Behaviour-verb card + in-voice examples | 0 calls; card 300-600 tokens once, cached | none | yes | Descriptions dominate fidelity (InCharacter); format studies absent |
| State sampling by code (WTT) | 0 calls; 80-150 tokens per turn | negligible; cache miss on last messages only if placed late | yes | Theory strong (Fleeson); LLM state-blindness documented (single preprint); no direct A/B |
| Depth 0-1 reminder | 0 calls; 30-80 tokens | under about 0.2 s | yes | Practitioner docs; drift study shows the problem, not this fix |
| Yield rule + concession budget + grudge ledger | 0 calls; 30-60 tokens | none | partly (small models may ignore) | Motivated by SPINE and sycophancy papers; the fix itself untested |
| Regex post-check + one resample | 0 calls on pass, 1 regen on miss | up to 2x on a miss | yes | None (engineering) |
| Sycophancy dial (user setting) | 0 calls | none | yes | None; wraps the items above |
| Director/appraisal LLM call | 1 call, 150-300 output tokens | +5-8 s local, +1-2 s cloud | partly (quality of a 7-12B judge unknown) | Generative Agents reflection ablations (large models) |
| Critic + regenerate | 1-2 calls | +2-8 s local, up to 2x | partly | None for role-play specifically |
| Control vectors (cvector/repeng) | 0 tokens | small compute overhead; restart to change scale | yes for vector-set models, partly for others | Weak: AxBench loses to prompting; Tan et al. brittle; persona-vector results at 27-32B |
| Character-specific fine-tune/LoRA | training cost | none at runtime | yes but heavy | InCharacter: limited improvement |
| Model choice (low-positivity tunes, RP-Bench J) | 0 | none | yes | Strongest: PsyPlay and Moral RolePlay show alignment drives the negative-trait failure |

**Recommended defaults**: ship the cheap default (rows 1-6) with the pushback dial; make the director and critic passes a "Premium realism" toggle; keep control vectors and fine-tunes off the roadmap until the probe set shows the cheap stack is not enough.

### Gaps
- All numbers in the schema (ranges, caps, budgets, frequency, token sizes, latency) are design proposals or estimates. Nothing was measured on Kataki's hardware.
- Needed next: a small in-house probe set (bratty holds frame, blunt refuses to sugarcoat, holds grudge after 20 turns, does not cave under emotional appeal, secret stays hidden) run on 2-3 Nemo-class tunes and one cloud model, comparing card-only vs card+state vs card+state+reminder vs plus critic. This is the only way to get local 7-14B evidence, which the literature lacks.
- Need a smoke test of llama-server with `--control-vector-scaled` on the current build and of prompt-cache behaviour with a depth-1 injected block.
