# LLM Role-Play and Persona Fidelity: Landscape Map (2023 to Sept 2026)

Method note: about 35 search/fetch calls. Page contents were read through a summarising fetch tool, so numbers are mostly taken from abstracts or HTML pages and PDF-only summaries were treated as weak. Several sources are 2026 arXiv preprints or ACL 2026 papers that I could only read at abstract/summary level. Anything I could not source is under Gaps, not in findings.

## 1. Surveys, benchmarks and role-play-tuned training methods: what exists?

### Takeaway
The field has two big surveys (Chen et al. 2024 "From Persona to Personalization"; Tseng et al. 2024 "Oscars of AI Theater"), and a long list of benchmarks (CharacterEval, CharacterBench, PersonaGym, RPEval, InCharacter, PingPong, RPGBench, and newer 2026 ones). Training-side work has moved from synthetic-persona SFT (Ditto, OpenCharacter) to real-literature dialogue (CoSER) to RL with verifiable rewards (Character-R1 and relatives). Recent work shows the benchmarks themselves are flawed: name leakage inflates scores, and general chat skill does not predict character skill.

### Cited Findings
- Survey "From Persona to Personalization" (2024) covers role-playing language agents; persona fidelity evaluation asks whether an agent replicates the persona's knowledge, linguistic habits, personality, beliefs and decision-making. Evaluation methods are: automatic with ground truth, automatic without ground truth, multiple choice, human-based — [Emergent Mind topic page](https://www.emergentmind.com/topics/role-playing-language-agents-rplas); [arXiv 2404.18231](https://arxiv.org/pdf/2404.18231)
- "The Oscars of AI Theater" survey (2024) exists as arXiv 2407.11484; I could not read its body text (PDF returned binary) — [arXiv 2407.11484](https://arxiv.org/pdf/2407.11484)
- A curated list of role-play-with-persona resources is maintained at [awesome-llm-role-playing-with-persona](https://github.com/Neph0s/awesome-llm-role-playing-with-persona)
- CoSER (ICML 2025): dataset of 17,966 characters from 771 books, real multi-character dialogues with inner thoughts; introduces "given-circumstance acting" for training and evaluation; releases CoSER-8B and CoSER-70B on Llama-3.1 — [arXiv abs 2502.09082](https://arxiv.org/abs/2502.09082v1); [PMLR](https://proceedings.mlr.press/v267/wang25dk.html)
- Ditto (ACL 2024): self-alignment; premise that LLMs already hold role-play ability as a "superposition of all characters"; pipeline is role knowledge collection (Wikipedia profiles), dialogue simulation as reading comprehension, then instruction tuning. Finding: role-play *style* is easy to acquire, but the model's own capabilities cap the *knowledge* available in character — [ACL Anthology](https://aclanthology.org/2024.acl-long.423/); [Hugging Face papers](https://huggingface.co/papers/2401.12474)
- OpenCharacter: synthesises about 20k character profiles from synthetic personas, then character-driven responses for SFT — [arXiv 2501.15427](https://arxiv.org/html/2501.15427v1)
- CharacterBench: 22,859 human-annotated samples, bilingual, 6 aspects / 11 dimensions including memory recall, knowledge exposure, persona exhibition, emotional expression, moral adherence, and believability vs real characters — [arXiv 2412.11912](https://arxiv.org/html/2412.11912v1)
- RPEval scores emotional understanding, decision-making, moral alignment and in-character consistency. PersonaGym uses "PersonaScore" over question tasks in sampled environments. InCharacter uses psychometric interviews to measure personality fidelity — [search summary of benchmark pages](https://arxiv.org/html/2502.00595v1)
- PingPong (2024): a player model plays the character, a "user emulator" model interrogates, judges score character consistency, entertainment value and language fluency, and note refusals. Over 40 models tested. Claude 3.5 Sonnet ranked top in English and Russian; Llama 3.1 405B led open-source English. Averaging two judge models gave Spearman above 0.6 vs humans; human inter-rater agreement was low (Krippendorff's alpha 0.25 to 0.34). Claude models showed high refusal rates on appropriate content; creative-writing fine-tunes improved role-play (Gemma 2 Ataraxy 9B did well for its size) — [arXiv 2409.06820](https://arxiv.org/html/2409.06820v3)
- RPGBench evaluates LLMs as role-playing game engines — [arXiv 2502.00595](https://arxiv.org/html/2502.00595v1)
- 2026 benchmarks/papers surfaced by search (abstract-level only): RoleCDE (role fidelity vs alignment/safety trade-off, arXiv 2606.01552), PersonaArena (dynamic simulation, 2605.17044), TRACE Bench (task-driven roleplay checklist evaluation, 2608.11236), "Do LLMs Understand Personality?" (structured behavioural inference for persona fidelity, 2608.26674), CHARM (character hallucination, multicultural, 2609.01352) — [RoleCDE](https://arxiv.org/pdf/2606.01552); [PersonaArena](https://arxiv.org/pdf/2605.17044); [TRACE Bench](https://arxiv.org/pdf/2608.11236); [Persona fidelity via behavioural inference](https://arxiv.org/pdf/2608.26674); [CHARM](https://arxiv.org/pdf/2609.01352)
- "Rethinking Role-Playing Evaluation" (2026): removing character names from prompts lowers scores (e.g. GPT-4o CharacterEval Persona-Behavior 2.839 to 2.607), meaning models lean on memorised famous characters. Adding personality info (self-report, interview-based, crowdsourced) helps; distinctive traits help more than generic ones; MBTI-style descriptions beat Big Five, likely due to online prevalence — [arXiv 2603.03915](https://arxiv.org/html/2603.03915)
- Training with RL: Character-R1 (Jan 2026) uses verifiable rewards: a cognitive-focus reward forcing explicit analysis of 10 character elements, a reference-guided reward, and per-character reward normalisation. Related: RAIDEN-R1 (GRPO with verifiable reward), CRPO, and a psychology-grounded reasoning paper — [arXiv 2601.04611](https://arxiv.org/abs/2601.04611); [RAIDEN-R1](https://arxiv.org/pdf/2505.10218); [CRPO](https://arxiv.org/pdf/2605.25511)
- Persona-Aware Contrastive Learning (ACL Findings 2025) is annotation-free and improves role consistency — [ACL Anthology](https://aclanthology.org/2025.findings-acl.1344/)
- Character-LLM (2023) trains agents per character; a related line trains "knowledge forgetting" so characters say "I don't know" for things they should not know — [arXiv 2310.10158](https://arxiv.org/pdf/2310.10158); [Emergent Mind](https://www.emergentmind.com/topics/character-llm)
- I could not verify details of ChatHaruhi, CharacterGLM, RoleLLM/RoleBench in this session beyond their names being standard in the surveys.

### Inferences
- For Kataki, public benchmarks mostly measure "does the model stay the named character" for famous characters. Kataki's characters are original, so the anonymous/personality-augmented result (name-free descriptions with distinctive traits) is the closer analogue. Distinctive, specific trait descriptions beat generic ones.
- None of these benchmarks target "bratty, forgetful, wrong, dishonest" behaviour directly; the closest is Moral RolePlay (section 2). Kataki likely needs a small in-house eval (see Gaps).
- Fine-tuned 8B/12B models (CoSER-8B, creative-writing tunes) are the local-viable end of this research; RL-trained role-aware models from 2026 are mostly research checkpoints with unclear local availability.

### Gaps
- Could not read the body of the Oscars survey, ChatHaruhi, CharacterGLM, RoleLLM/RoleBench, RPEval, PersonaGym and InCharacter papers; only names/one-line descriptions confirmed.
- No verified head-to-head numbers of small local models (7-14B) on CharacterBench/CoSER-style evals.
- Summaries of the 2026 preprints (RoleCDE especially) came from a tool that may have misread the PDF (it named Llama 2 as a tested model, which looks odd for a 2026 paper); treat as unverified.

## 2. Failure modes: what goes wrong and why?

### Takeaway
The best-evidenced failures are: (a) safety-tuned models cannot play self-serving, deceitful, manipulative characters (monotonic fidelity drop with lower morality, biggest at "Egoist"); (b) agreeable personas amplify sycophancy; (c) persona/instruction drift within about 8 turns; (d) role-play and emotional/intimate contexts pull activations toward the default "Assistant"; (e) out-of-character knowledge leakage; (f) slop/repetition; (g) refusals.

### Cited Findings
- "Too Good to Be Bad" (ACL Findings 2026): Moral RolePlay benchmark, 17 LLMs (GPT-4o, Claude variants, Gemini 2.5 Pro, DeepSeek V3 series, Qwen3-Max, GLM-4 series, Grok-4 and others). Average score by moral level: Paragons 3.21, Flawed-but-good 3.13, Egoists 2.71, Villains 2.61; biggest drop is between levels 2 and 3 (-0.42), so playing merely self-serving characters is the main challenge. Hardest traits: Deceitful, Hypocritical, Selfish (penalties about 3.5) vs Brave (about 3.0). Models substitute "superficial aggression" for nuanced malevolence — [arXiv 2511.04962 HTML](https://arxiv.org/html/2511.04962v1); [ACL Anthology](https://aclanthology.org/2026.findings-acl.282/)
- Same paper: general chatbot proficiency is a poor predictor of villain play. Villain leaderboard top 5: GLM-4.6 (2.96), DeepSeek-V3.1-Thinking (2.82), Kimi-K2 (2.79), Gemini-2.5-Pro (2.75), DeepSeek-V3.1 (2.71). Turning on reasoning/thinking slightly hurt at every morally non-trivial level (e.g. level 3: 2.74 to 2.69). First- vs third-person framing made no difference — [arXiv 2511.04962 HTML](https://arxiv.org/html/2511.04962v1)
- "Too Nice to Tell the Truth" (ACL 2026 long): 13 small open-weight models (0.6B to 20B); 9 of 13 show significant positive correlation between the persona's agreeableness and sycophancy (max r = 0.87, Cohen's d up to 2.33). No remediation given in the abstract — [arXiv 2604.10733](https://arxiv.org/abs/2604.10733); [ACL PDF](https://aclanthology.org/2026.acl-long.1421.pdf)
- Persona drift (Li et al. 2024): significant drift within eight rounds in LLaMA2-chat-70B and GPT-3.5, measured via self-chats; authors attribute it to attention decay over long exchanges and propose "split-softmax" (an inference-time attention modification) — [arXiv 2402.10962](https://arxiv.org/abs/2402.10962); [GitHub](https://github.com/likenneth/persona_drift). Secondary summaries say consistency fell by more than 30% after 8 to 12 turns — [Harvard VCG page](https://vcg.seas.harvard.edu/publications/measuring-and-controlling-persona-drift-in-language-model-dialogs) (the exact 30% figure is not in the abstract, treat as secondary)
- "The Assistant Axis" (Anthropic, Jan 2026): activations of 275 character archetypes in Gemma 2 27B, Qwen 3 32B and Llama 3.3 70B; the top principal component tracks how "Assistant-like" a persona is, and exists already in base models. Drift away from the Assistant is triggered by therapy-style emotional-vulnerability contexts, philosophical talk about AI nature, and requests for specific authorial voices; coding keeps the model in Assistant territory. Activation capping (clamping along the axis only when it exceeds normal range) roughly halved harmful-response rates while preserving benchmark capability — [Anthropic](https://www.anthropic.com/research/assistant-axis); [arXiv 2601.10387](https://arxiv.org/pdf/2601.10387)
- Knowledge leakage: extra world knowledge undermines believability; two error types, Known Knowledge Errors and Unknown Knowledge Errors (anachronistic or beyond-character concepts). Mitigations: DPO on "low-compatibility" questions so "I don't know" is rewarded; the S2RD multi-agent framework (Self-Narrative, Self-Recollection, Self-Doubt) — [arXiv 2409.11726](https://arxiv.org/pdf/2409.11726); [search summary](https://www.sciencedirect.com/science/article/abs/pii/S0957417425026417)
- "Concept Incongruence" (2025) explores time and death in role-play (models fail on concepts that conflict with the persona, e.g. a dead character) — [arXiv 2505.14905](https://arxiv.org/pdf/2505.14905) (abstract not read)
- Slop: some patterns appear over 1,000x more often in LLM output than in human text — [Antislop abstract](https://arxiv.org/abs/2510.15061)
- Refusals: PingPong found Claude models refuse role-play requests with acceptable content at high rates — [arXiv 2409.06820](https://arxiv.org/html/2409.06820v3)
- Fidelity vs safety is a measured trade-off in RoleCDE (2026) — [arXiv 2606.01552](https://arxiv.org/pdf/2606.01552) (low confidence, see section 1 gaps)

### Inferences
- The moral-level result is the strongest single support for Kataki's premise: default assistant alignment is the cause of "too positive/helpful", and the failure is worst exactly at the "selfish, deceitful, hypocritical" traits the owner wants. Because thinking mode hurt, chain-of-thought "reason before you reply" pipelines may worsen it; test before adding.
- Because cloud "frontier chat" rank did not predict villain skill, model choice for Kataki should use role-play-specific evidence (VRP leaderboard, EQ-Bench creative writing, PingPong-style tests), not general Arena rank.
- Sycophancy result was measured on small models (up to 20B), so it applies directly to the local tier. It implies: do not write "agreeable, warm, polite" trait words in cards unless intended; use disagreeable facets explicitly.
- Assistant Axis suggests the drift risk is highest in exactly Kataki's intimate/emotional scenes (user vulnerability, intimate voice). Re-injecting the persona near the end of context is the cheap counter (section 3).
- The "agrees too fast / no grudges" failures are not directly benchmarked in what I found; they are inferred from drift + sycophancy results, not from a study.

### Gaps
- No source found quantifying "not holding a grudge" or "agreeing too fast" as named metrics.
- No quantitative study found on assistant-voice leakage frequency in local 7-14B role-play tunes.
- Persona-drift numbers come from 2024 models (Llama-2-70B, GPT-3.5); no fresh measurement on 2026 local models.

## 3. Prompting fixes: card format, example dialogue, depth injection

### Takeaway
Practitioner consensus (SillyTavern docs and guides): prose or compact PList plus Ali:Chat-style example dialogue; the first message and example messages set voice and length more than the description; depth-injected notes re-assert traits mid-chat. Formal research support is thin; the main academic evidence is that distinctive, specific personality descriptions help when names are hidden.

### Cited Findings
- SillyTavern docs defer format to community guides (Trappu's PLists + Ali:Chat, AliCat's Ali:Chat, kingbri's minimalistic guide); permanent tokens are Name, Description, Personality, Scenario; the first message is the strongest style/length cue; example dialogues use `<START>` and `{{char}}:` / `{{user}}:` and are dropped when space runs out; the "Character's Note" (depth prompt) injects text at a chosen message depth to reinforce traits — [SillyTavern docs](https://docs.sillytavern.app/usage/core-concepts/characterdesign/)
- Blog guides say prose is understood well and W++ mostly wastes tokens; the first message sets style and length for the whole chat — [MiniTavern blog](https://blog.mini-tavern.com/blog/sillytavern-character-card-format-guide-json-structure-w-and-beyond-eb82f0); [TavernSprite](https://tavernsprite.com/blog/sillytavern-character-card-fields/) (marketing blogs; one claims a 200-char W++ prompt outperforms a 1000-char novel, which I could not verify and would not rely on)
- Research analogue: distinctive personality traits give larger gains than generic ones when the character name is hidden — [arXiv 2603.03915](https://arxiv.org/html/2603.03915)
- Tseng/Jones: in the Turing test, a persona prompt asked for "a young person who is relatively introverted and knowledgeable about internet culture" who uses slang — [arXiv 2503.23674](https://arxiv.org/html/2503.23674v1)
- Split-softmax (attention-level fix for drift) is an architecture-level change, not usable via a prompt — [arXiv 2402.10962](https://arxiv.org/abs/2402.10962)

### Inferences
- Cheapest known-good stack for local models: short prose description with concrete behavioural specifics (what they do when embarrassed, how they lie, what they refuse), 3-6 in-voice example exchanges showing the flaws (bratty, blunt, wrong), and a strong first message in the target voice, plus a depth-injected 1-2 line reminder every few turns to fight drift. This is inference from practitioner docs plus drift research, not a single-study result.
- Because example dialogue is evicted first when context fills, Kataki should keep style anchors pinned (or re-injected) rather than relying on early chat.
- Examples must show the *negative* traits, since models copy the first message and examples' tone; an example of the character being warm will pull toward the assistant.

### Gaps
- No controlled study found comparing W++ vs PList vs prose vs Ali:Chat. All evidence is practitioner opinion.
- No study of depth-injection frequency vs drift found.
- Did not access r/SillyTavernAI or r/LocalLLaMA threads directly.

## 4. Activation steering: persona vectors, control vectors, llama.cpp

### Takeaway
Anthropic's persona vectors (July 2025) and the Assistant Axis (Jan 2026) show traits like evil, sycophancy and "assistant-ness" are linear directions that can be measured and steered. llama.cpp already supports control vectors and has a generator, and a community set of "creative writing" vectors (dark-tetrad axes, optimism vs nihilism) exists, but published sets target large models, and small models are covered only by older sets.

### Cited Findings
- Persona vectors (Chen, Arditi, Sleight, Evans, Lindsey; arXiv July 2025): automated extraction of trait directions from a natural-language description (evil, sycophancy, hallucination); fine-tuning personality shifts correlate strongly with shifts along these vectors; used for monitoring, post-hoc steering, preventative steering during training, and flagging training data. Open toolkit released — [arXiv 2507.21509](https://arxiv.org/abs/2507.21509); [Anthropic](https://www.anthropic.com/research/persona-vectors)
- Assistant Axis: activation capping along one axis kept persona stable without capability loss (models 27B to 70B) — [Anthropic](https://www.anthropic.com/research/assistant-axis)
- llama.cpp merged control-vector support (PR #5970 by vgel/repeng, Nous collaboration) and ships a `cvector-generator` tool (PCA or mean method, GPU with `-ngl`); runtime flags `--control-vector` and `--control-vector-scaled` — [PR #5970](https://github.com/ggml-org/llama.cpp/pull/5970); [cvector-generator README](https://github.com/ggml-org/llama.cpp/blob/master/tools/cvector-generator/README.md); [Teknium](https://x.com/Teknium/status/1769752208466383205)
- jukofyork "creative-writing-control-vectors v3.0": axes for Language (simple/ornate), Storytelling (explicit/descriptive), Character Focus (narration/dialogue), Dark Tetrad (Empathy vs Sociopathy, Honesty vs Machiavellianism, Humility vs Narcissism, Compassion vs Sadism) and Optimism vs Nihilism. Each has a de-bias vector plus positive/negative variants; must apply de-bias first; don't combine opposing ends; too many vectors degrade output; supported sizes include small (Llama 3/3.1 8B, Mistral 7B variants, Qwen 1.5 14B) through 123B; requires llama.cpp from June 27, 2024 or later — [Hugging Face](https://huggingface.co/jukofyork/creative-writing-control-vectors-v3.0/blob/a0b26e85c3f041299a659200b2e573a30268aeae/README.md); [GitHub](https://github.com/jukofyork/control-vectors)

### Inferences
- Steering is the only found fix that directly targets both "positivity/optimism bias" (Optimism vs Nihilism, Compassion vs Sadism axes) and "won't lie" (Honesty vs Machiavellianism), and it costs no context tokens. It is compatible with the 8 GB local target (vectors are small, applied at inference), but only for models with matching vector sets or ones the app generates itself with cvector-generator.
- Control vectors are global per model, not per-character, so per-character trait strength would need scaled vectors swapped per session (possible via `--control-vector-scaled`, needs server restart or API support; verify in Kataki's llama-server integration).
- Cloud (HF Inference Providers) models cannot be steered; only prompting/model choice apply there.
- Persona vectors' data-flagging/preventative-steering uses matter only if Kataki fine-tunes.

### Gaps
- No evidence found of head-to-head human evals for control vectors vs prompting in role-play.
- Unknown whether recent llama.cpp builds (2026) still support the multi-vector CLI exactly as documented in 2024; needs a test.
- No published control vector sets found for Mistral Nemo 12B specifically (only checked the one README).

## 5. Fine-tunes, merges, samplers and "anti-slop"

### Takeaway
Local role-play quality comes mostly from community fine-tunes (Mistral Nemo 12B and Mistral Small 24B lineages) plus a sampler stack (Min-P, DRY, XTC) and, more recently, Antislop (banlist backtracking sampler and FTPO training). Evidence for specific tunes is model-card and leaderboard level, not peer-reviewed.

### Cited Findings
- Antislop (ICLR 2026; Paech, Roush, Goldfeder, Shwartz-Ziv): sampler suppresses 8,000+ patterns via backtracking where plain token banning becomes unusable at about 2,000; FTPO (Final Token Preference Optimization) cuts slop by about 90% while maintaining or improving GSM8K, MMLU and creative writing; DPO degrades writing quality and lexical diversity with weaker suppression. Backtracking sampler reduces throughput 69 to 96% at banlists of 1k to 8k — [arXiv 2510.15061](https://arxiv.org/abs/2510.15061); [Emergent Mind summary](https://www.emergentmind.com/topics/antislop-sampler); [ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/467746c8e15fbfca34dcf23be9ef9229-Abstract-Conference.html)
- llama.cpp sampler order: penalties, DRY, top_n_sigma, top_k, typ_p, top_p, min_p, XTC, temperature. XTC removes top-probability tokens (keeps the last above threshold) to break clichés; community baseline: Min-P 0.02, DRY 0.8/1.75/2 with other samplers off, or Min-P then XTC with probability 0.5 (`--sampling-seq mx --min-p 0.02 --xtc-probability 0.5`) — [llama.cpp completion README](https://github.com/ggml-org/llama.cpp/blob/master/tools/completion/README.md); [DavidAU sampler guide](https://huggingface.co/DavidAU/Maximizing-Model-Performance-All-Quants-Types-And-Full-Precision-by-Samplers_Parameters); [LocalAIMaster](https://localaimaster.com/blog/llm-sampling-parameters-explained) (secondary sources)
- EQ-Bench Creative Writing v3 is an LLM-judged benchmark (32 prompts x 3 iterations); Sao10K's MN-12B-Lyra-v1 (merge of two Mistral-Nemo-12B finetunes) scores 77.41 on an earlier EQ-Bench creative scale, just below Nemomix v4 (77.92) — [EQ-Bench creative writing](https://eqbench.com/creative_writing.html); [aimodels.fyi Lyra](https://www.aimodels.fyi/models/huggingFace/mn-12b-lyra-v1-sao10k)
- MN-Violet-Lotus-12B is a merge of Violet_Twilight, Lumimaid-v0.2-12B, Mahou-1.5-mistral-nemo-12B and MN-12B-Lyra-v4 — [PromptLayer](https://www.promptlayer.com/models/mn-violet-lotus-12b/)
- TheDrummer: Cydonia 24B v2 (Mistral Small 2501 finetune, tested to 21-24k context), Rocinante (12B line, "robust roleplaying"), Cydonia 24B v4.2.0 described as playing well with banned-string/anti-slop samplers; v4.3 "more balanced" (all model-card self-descriptions) — [Cydonia-24B-v2](https://huggingface.co/TheDrummer/Cydonia-24B-v2); [v4.2.0 GGUF](https://huggingface.co/TheDrummer/Cydonia-24B-v4.2.0-GGUF); [v4.3](https://huggingface.co/TheDrummer/Cydonia-24B-v4.3)
- UGI Leaderboard scores: UGI (uncensored knowledge), W/10 willingness (Direct and Adherence), Writing (0-100), Intelligence — [UGI Leaderboard](https://huggingface.co/spaces/DontPlanToEnd/UGI-Leaderboard)
- PingPong: creative-writing fine-tunes improve role-play; Gemma 2 Ataraxy 9B did well — [arXiv 2409.06820](https://arxiv.org/html/2409.06820v3)
- Character-specific SFT: CoSER-8B/70B trained on real book dialogue — [arXiv 2502.09082](https://arxiv.org/abs/2502.09082v1)

### Inferences
- 12B Nemo tunes at Q4-Q5 fit 8 GB with modest context; 24B Mistral Small tunes generally need heavy quantization or CPU offload on 8 GB (hardware inference, not from a source), so the local sweet spot is 8-14B.
- Dropping DPO for anti-slop is supported: the Antislop paper found DPO hurts quality. Antislop's FTPO is a training route (an owner-side fine-tune), while the sampler's throughput hit is severe (69-96%), so for a local app prefer Min-P + DRY + XTC and a short banned-string list rather than a 1k+ backtracking list.
- The UGI W/10 "adherence" and willingness numbers are the best public proxy for "will this model actually be mean / lie / stay in character", combined with the Villain RolePlay leaderboard for cloud models.
- Cloud options in the VRP top 5 (GLM-4.6, DeepSeek-V3.1, Kimi-K2, Gemini 2.5 Pro) may be reachable through HF Inference Providers; availability must be checked (not verified).
- "RLHF-free / base-ish" models: found no citable evidence in this session; the Assistant Axis finding that the Assistant direction already exists in base models suggests base models still tilt toward it less strongly, but that is only my inference.

### Gaps
- Could not view r/LocalLLaMA / r/SillyTavernAI directly; community claims about which finetune is "best" are unverified and change monthly (Sept 2026 rankings not obtained).
- Did not find data on NousResearch Hermes as a role-play model, MythoMax lineage, or Sao10K's newer 2026 releases.
- Antislop absolute slop-word lists, model sizes and human-eval results were not retrievable in full.
- Sampler recommendations come from secondary guides, not controlled experiments.

## 6. Deliberate lying and strategic deception in character

### Takeaway
LLMs can lie strategically in social-deduction games when goal-conditioned, and can be persuasive; but safety-tuned models are measurably worst at portraying deceitful characters in ordinary role-play. A separate "hidden intent" architecture (CICERO-style planner plus dialogue model) is the reliable way to get consistent in-character lying and secrets.

### Cited Findings
- Social deduction games (Werewolf, Avalon, Among Us, Mafia) are the canonical testbeds for LLM deception; misaligned agents adapt private reasoning to their objective while keeping public communication consistent — [Even More Deception (arXiv 2607.26120)](https://arxiv.org/pdf/2607.26120)
- WOLF (Dec 2025) benchmarks deception and lie detection in Werewolf; summary states LLM deception is strategic rather than random falsehood (specific numbers and model names not retrievable) — [arXiv 2512.09187](https://arxiv.org/pdf/2512.09187)
- Avalon LLM agents: recursive contemplation (ReCon) for detecting deception — [arXiv 2310.01320](https://arxiv.org/pdf/2310.01320); One Night Ultimate Werewolf with RL-trained discussion policies — [NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/8cea78701eb986f3ec357eb9b7c6badd-Paper-Conference.pdf)
- CICERO (Meta, Science 2022): more than doubled average human score across 40 anonymous games, top 10% of multi-game players; a strategy/planning module drives an LLM whose dialogue communicates the planner's actual intent; designed to be largely honest, but can omit information and change its mind, hence behave deceptively — [MIT summary of paper](https://www.mit.edu/~gfarina/2022/cicero); [AI Deception survey](https://arxiv.org/pdf/2308.14752)
- Safety-aligned models struggle with "Deceitful" and "Manipulative" traits in role-play, replacing subtle malevolence with aggression — [arXiv 2511.04962](https://arxiv.org/html/2511.04962v1)
- Anthropic persona-vector work includes "evil" and "sycophancy" steering; jukofyork vectors include Honesty vs Machiavellianism — [Anthropic](https://www.anthropic.com/research/persona-vectors); [HF control vectors](https://huggingface.co/jukofyork/creative-writing-control-vectors-v3.0/blob/a0b26e85c3f041299a659200b2e573a30268aeae/README.md)

### Inferences
- Key architectural lesson: in game contexts the lie works because the model is *given* a private ground truth and a goal. Kataki should store each character's real state/secret in a private field (never shown to the user, never in the "public" transcript) and prompt "what you know vs what you say". Otherwise the model, trained to be truthful, leaks the secret or confesses at the first probing question. This is inference from CICERO's structure and the deceit-trait weakness.
- Mixed evidence: models lie well when the game objective demands it; they lie poorly in casual character chat without an objective. So give characters an explicit motive for each lie.
- Consistency of lies over many turns depends on memory of what was said; the WOLF summary suggests lie strategies persist but I could not verify numbers.

### Gaps
- No verified numbers for lie success/detection in WOLF or Avalon studies.
- No source found on small (7-14B) model deception ability in games.
- Nothing found on models spontaneously "confessing"/breaking cover under user pressure (assumed but not sourced).

## 7. Human evaluation: what feels most human?

### Takeaway
The strongest human-judgement result is the Jones and Bergen three-party Turing test: GPT-4.5 with a persona prompt was judged human 73% of the time, but only 36% without it; the persona was an introverted, slang-using young person. Interrogators judged on linguistic style and interaction dynamics (typos, evasiveness, smoothness), not intelligence.

### Cited Findings
- Three-party Turing test (Jones & Bergen, 2025): GPT-4.5 with persona prompt judged human 73%; LLaMa-3.1-405B with persona 56%; GPT-4o baseline 21%; ELIZA 23% — [arXiv 2503.23674](https://arxiv.org/abs/2503.23674). Peer-reviewed version in PNAS — [PNAS](https://www.pnas.org/doi/10.1073/pnas.2524472123)
- Without persona instruction GPT-4.5's rate fell to 36% — [Neuroscience News](https://neurosciencenews.com/ai-passes-turing-test-30733/) (secondary)
- Persona prompt: "a young person who is relatively introverted and knowledgeable about internet culture", using slang — [arXiv HTML](https://arxiv.org/html/2503.23674v1)
- Interrogator strategies: small talk 61%, social/emotional probing 50%, direct "are you human" 19%, situational awareness 13%, knowledge testing 12%. Verdict reasons: linguistic style 27% ("had a typo", "more humanly language"), interaction dynamics 23% ("avoided questions"), gut feeling. Most accurate strategy: unusual things or LLM jailbreaks — [arXiv HTML](https://arxiv.org/html/2503.23674v1)
- PingPong human agreement is low (alpha 0.25 to 0.34), showing taste in role-play is subjective — [arXiv 2409.06820](https://arxiv.org/html/2409.06820v3)
- Earlier study "People cannot distinguish GPT-4 from a human in a Turing test" exists (arXiv 2405.08007) — [arXiv](https://arxiv.org/pdf/2405.08007)

### Inferences
- "Human" in the Turing test came from persona constraints on style (casual register, slang, imperfection, not trying to be helpful), not from a smarter model: the same model went 36% to 73% with a persona. This directly supports Kataki's approach of defining behaviour flaws and register in the character definition.
- Humans mark down over-smooth, complete, evenly helpful answers and reward evasiveness, typos and lacking knowledge. Characters that sometimes don't know, dodge, or reply short are consistent with what raters accepted as human.
- These are test-condition results (5-minute chats, adversarial detection), not evidence about what users enjoy in long-term roleplay; PingPong's entertainment axis is the closer proxy but has low rater agreement.

### Gaps
- Found no user-satisfaction study on long-running romantic/companion role-play about which imperfections users prefer (e.g., bratty vs blunt).
- Did not find the full text of the persona prompt in the Turing test paper (Figure 6).
- Did not find 2026 follow-up Turing tests with newer models.

## 8. Summary table: failure mode to fix

### Takeaway
Most failures share one root cause: assistant-tuned defaults. Fixes rank roughly as model choice, then prompt structure (examples, first message, re-injection), then samplers, then steering, then fine-tuning.

### Cited Findings
- Each row below rests on findings cited in sections 2-7 above; the causes and "works locally?" columns are my synthesis (see Inferences).

### Inferences
| Failure mode | Cause (evidence) | Best fix | Works locally (7-14B, 8 GB)? |
|---|---|---|---|
| Too positive / helpful / nice | Safety/RLHF alignment; "Assistant" direction exists even in base models (Assistant Axis) | Role-play-tuned model (Nemo/Mistral tunes); flawed in-voice examples and first message; Optimism-vs-Nihilism / Compassion-vs-Sadism control vector | Yes (tunes, prompts, cvectors); cloud only via model choice |
| Cannot play deceitful / manipulative / selfish characters | Alignment suppresses these traits; worst at "Egoist" level (Moral RolePlay); thinking mode makes it slightly worse | Pick villain-capable models (VRP leaderboard, UGI W/10); give private secrets + explicit motive; Honesty-vs-Machiavellianism vector; avoid reasoning mode | Yes for tunes and prompts; VRP top models are large cloud models |
| Sycophancy / agreeing too fast | Agreeable persona traits raise sycophancy (r up to 0.87 in 0.6B-20B models) | Write disagreeable facets and stubborn goals into card; avoid "warm, kind" trait words; sycophancy vector steering | Yes (the effect was measured on small models); steering needs vector set |
| Persona drift over long chats | Attention decay (Li et al.); role-play/emotional contexts pull toward Assistant (Assistant Axis) | Re-inject character reminder via depth prompt every N turns; pin examples; keep context short with summaries; activation capping in research | Prompt re-injection yes; split-softmax/capping need model surgery (not turnkey locally) |
| Assistant-voice leakage ("As an AI", lists, disclaimers) | Assistant persona is the default attractor; refusal behaviour | Role-play tune; first message + examples in target voice; banned strings; de-bias + style vector | Yes |
| Refusing to be mean / crossing lines | Safety tuning; Claude models had high role-play refusal in PingPong | Less filtered tunes (check UGI W/10-Adherence); system framing as fiction | Yes with tuned models; commercial cloud APIs may still refuse |
| Out-of-character knowledge leakage / anachronism | Vast pretraining knowledge (KKE/UKE errors) | "Self-doubt" step (S2RD), explicit knowledge boundaries in card, DPO on "I don't know"; character forgets by design | Prompt-level yes; DPO/S2RD needs training or extra calls (extra calls are slow locally) |
| Slop / repeated phrases | Repetitive phraseology, some 1000x over human text; sampling collapse | Min-P + DRY + XTC; short banned-string list; Antislop FTPO-tuned models | Yes for samplers; backtracking sampler with big lists costs 69-96% throughput |
| Not holding a grudge / forgetting events | Not directly benchmarked; likely context eviction plus agreeableness | Persistent memory of grievances (structured relationship state) injected each turn | Yes (app-level memory, no model change) |
| Lying breaks (secret leaks, confesses) | Truthfulness training; no hidden state in plain chat | CICERO-like split: private ground truth + public utterance; give each lie a motive | Yes (prompt structure); reliability on 7-14B untested |
| Feels machine-like in style | Over-complete, tidy answers; humans flag lack of typos, smooth flow | Persona register (casual, slang, short, evasive, imperfect) as in Turing test | Yes; works on small models in principle (the test used large ones) |
| Wrong / forgetful characters | Models default to being correct | Prompt explicit fallibility and unknown areas; combine with knowledge-boundary work | Yes at prompt level |

### Gaps
- The "works locally" column is a judgement; none of the cited studies tested 8 GB quantized 7-14B models on these fixes except the sycophancy paper (models up to 20B) and control-vector sets (8B-class listed).
- Recommended next step (phase 2): build a small in-house probe set (bratty, blunt, lying, forgetful, holds-grudge scenarios), run it on 2-3 Nemo-class tunes plus one cloud model, before investing in steering or fine-tuning.
