# Cognitive architectures for LLM-based believable agents and simulated humans (phase 1 landscape map)

Scope note: research run 2026-09-29. Sources are mostly arXiv abstracts, project pages and search-result summaries; full-paper reads were only possible for a few items. Where a fetch returned only an abstract, numbers such as LLM calls per turn are listed as gaps rather than guessed. Anything labelled "Inference" is my own reasoning, not a sourced fact.

## 1. Simulation-style architectures: Generative Agents, its follow-ups, Humanoid Agents, Project Sid/PIANO, AI Town

### Takeaway
Generative Agents (memory stream + reflection + planning) is still the reference design, and its ablation is the best human-evaluated evidence that memory, reflection and planning each raise believability. It was expensive (thousands of dollars for 25 agents over 2 days on gpt-3.5-turbo). Later systems either add drives/emotion (Humanoid Agents), run modules concurrently (PIANO), or replace the whole loop with interview-grounded memory (1,000-person simulation).

### Cited Findings
- Generative Agents ablation (TrueSkill believability): full architecture mu=29.89; no reflection 26.88; no reflection or planning 25.64; crowdworker humans 22.95; no memory/planning/reflection 21.21; effect size d=8.16 between the full and fully-ablated agent; observation, planning and reflection each matter. — [Generative Agents (arXiv 2304.03442) via search summary](https://arxiv.org/pdf/2304.03442)
- Generative Agents retrieval score sums recency (decay factor 0.995 per sandbox hour), importance (LLM-rated 1-10) and relevance (embedding similarity), all weights 1.0. Reflection fires when summed importance of recent events exceeds 150, roughly 2-3 reflections per agent per day. — [ar5iv full text](https://ar5iv.labs.arxiv.org/html/2304.03442)
- Cost: the 25-agent, 2-day simulation "cost thousands of dollars in token credits and took multiple days"; model was gpt-3.5-turbo. — [ar5iv full text](https://ar5iv.labs.arxiv.org/html/2304.03442)
- Documented failure modes: memory retrieval failures, hallucinated embellishment, overly formal instruction-tuned dialogue, excessive cooperativeness (rarely refusing suggestions), and "norm erosion" as memory grew (agents picked inappropriate locations). — [ar5iv full text](https://ar5iv.labs.arxiv.org/html/2304.03442)
- Generative Agent Simulations of 1,000 People (Park et al., Nov 2024): agents built from qualitative interviews of 1,052 real people replicated General Social Survey answers 85% as accurately as participants replicated their own answers two weeks later, and reduced accuracy bias across racial/ideological groups compared with demographic-description agents. Code: StanfordHCI/genagents. — [Search summary of arXiv 2411.10109](https://huggingface.co/papers/2411.10109); [repo](https://github.com/joonspk-research/genagents)
- Humanoid Agents (EMNLP 2023 demo) adds "System 1" state on top of Generative Agents: five basic needs (fullness, social, fun, health, energy), seven emotions (disgusted, afraid, sad, surprised, happy, angry, neutral), and four relationship-closeness levels; agents adapt daily activity and conversation to these; includes Unity WebGL front end and analytics dashboard. — [ACL Anthology](https://aclanthology.org/2023.emnlp-demo.15/); [arXiv 2310.05418](https://arxiv.org/abs/2310.05418)
- Project Sid / PIANO (Altera): 10 concurrent modules running at different speeds (memory, action awareness, goal generation, social awareness, talking, skill execution and others) that read/write a shared agent state; a Cognitive Controller bottlenecks the output so speech and action stay coherent ("say one thing, do another" failure). — [arXiv 2411.00114](https://arxiv.org/html/2411.00114v1)
- PIANO ablations: removing action awareness reduced Minecraft item progression (full system about 17 unique items in 30 min); social modules gave sentiment-inference correlation 0.807 with 5+ observers and, without them, relationships stayed neutral and roles did not persist. The authors state this performance was only enabled by GPT-4o and not older models. Runs of 1,000+ agents exceeded their Minecraft server constraints. — [arXiv 2411.00114](https://arxiv.org/html/2411.00114v1)
- Project Sid repo exists at altera-al/project-sid (licence and activity not checked). — [GitHub](https://github.com/altera-al/project-sid)
- AI Town (a16z-infra): 10.6k stars, MIT, inspired by Generative Agents; Convex backend, React/PixiJS front end; default local inference through Ollama with llama3 chat and mxbai-embed-large embeddings; vector-search memory; also OpenAI, Together and any OpenAI-compatible API. — [GitHub](https://github.com/a16z-infra/ai-town)
- A survey of LLM-based human simulation concludes such simulations "remain insufficiently reliable", blaming inherent LLM limits and simulation-design flaws. — [arXiv 2501.08579](https://arxiv.org/abs/2501.08579)

### Inferences
- Reflection and planning are the two components with direct human-eval evidence of gain; for a chat-driven roleplay app, reflection (a periodic, importance-triggered background call) is cheap relative to per-turn cost, while world-simulation planning is only relevant if characters act off-screen.
- PIANO's key transferable idea is not scale but the split between fast output modules and slow background modules joined by a single output gate.
- Humanoid Agents' needs/emotion/closeness state is small, discrete and cheap to update, so it fits a small local model better than free-form reflection.
- Per-step LLM-call counts of the above systems are high (Generative Agents had many calls per agent-step); exact counts were not found in fetched material.

### Gaps
- Exact LLM calls per agent step or per turn for Generative Agents, Humanoid Agents and PIANO were not found in the fetched text.
- The Generative Agents ACM full-text fetch returned 403; the reflection and cost figures come from ar5iv.
- Whether Generative Agents-style loops work on 7-12B local models: I found no direct evaluation. A generic web result says models of 1-7B "mostly fail at agentic tasks" and suggests 24-32B for multi-step work, but it is a blog-tier source. — [Futureagi](https://futureagi.com/blog/small-language-models-agentic-ai-2025/)
- Smallville derivatives beyond AI Town, and AgentSims, were not researched this round.

## 2. Classical and unified cognitive architectures (CoALA, Soar, ACT-R, LIDA/GWT) and LLM hybrids

### Takeaway
CoALA is the standard organising vocabulary: modular memory (working, episodic, semantic, procedural), an action space split into internal (reasoning, retrieval, learning) and external actions, and a decision cycle. It maps LLM agents onto Soar/ACT-R style production-system ideas. Several 2026 papers revisit hybrids, but I found no head-to-head believability evidence for classical-plus-LLM hybrids.

### Cited Findings
- CoALA (Princeton) decomposes a language agent into modular memory, a structured action space (internal and external actions) and a generalised decision-making procedure, explicitly drawing on Soar and ACT-R. — [arXiv 2309.02427](https://arxiv.org/abs/2309.02427); [summary](https://www.emergentmind.com/papers/2309.02427)
- Commentary describes classical architectures as strong at goal-directed decision-making and structured memory but lacking the semantic flexibility of neural models, motivating hybrids. — [search summaries incl. arXiv 2607.23942](https://arxiv.org/pdf/2607.23942)
- "Heartbeat-driven" autonomous thinking scheduling (Apr 2026) proposes a meta-learned scheduler that decides when to run cognitive modules such as planners and critics, aiming at proactive rather than reactive control. Stated result only that it learns to schedule from history and can integrate new modules. — [arXiv 2604.14178](https://arxiv.org/abs/2604.14178)

### Inferences
- For Kataki, CoALA is a design checklist (which memories, which internal actions) rather than something to implement wholesale.
- Global Workspace-style designs match PIANO's bottleneck/controller pattern, but I did not verify any LLM-GWT paper directly.

### Gaps
- No sourced material on LIDA or Global Workspace Theory LLM implementations, or on Soar/ACT-R + LLM systems with measured results; these need a dedicated pass.
- Heartbeat-scheduler evidence is abstract-level only.

## 3. Memory systems: MemGPT/Letta, Mem0, Zep/Graphiti, A-MEM, MemoryBank, HippoRAG, sleep-time compute, benchmarks

### Takeaway
Memory is the most mature and best-benchmarked component, but vendor benchmark numbers conflict and should not be trusted at face value. Retrieval-based memory cuts tokens about 3-4x versus full context; forgetting (MemoryBank) and offline consolidation (sleep-time compute, Auto-Dreamer) are the human-like additions most relevant to "remember and forget".

### Cited Findings
- MemGPT is now Letta: Apache-2.0, 24k+ GitHub stars, exposes core memory, archival memory and an inspectable memory editor (ADE). — [letta-ai/letta](https://github.com/letta-ai/letta); [search summary](https://vectorize.io/articles/mem0-vs-letta)
- Letta sleep-time agents share memory blocks with a primary agent and run in the background, rewriting memory asynchronously to turn "raw context" into "learned context"; offline compute helps most when future queries are predictable from existing context. — [Letta docs](https://docs.letta.com/guides/agents/architectures/sleeptime/); [Letta blog](https://www.letta.com/blog/sleep-time-compute/); [arXiv 2504.13171](https://arxiv.org/html/2504.13171v1)
- Auto-Dreamer (May 2026) learns offline memory consolidation for language agents; tested on ALFWorld, ScienceWorld, WebArena with Gemini-3-Flash and Qwen models; reported as matching or beating LightMem, MemAlpha and UMem with lower deployment-time cost (fetch summary only, no numbers). — [arXiv 2605.20616](https://arxiv.org/pdf/2605.20616)
- Zep/Graphiti: temporal knowledge graph that tracks validity periods of facts and invalidates contradicted ones rather than deleting; retrieval mixes semantic, keyword and graph traversal; paper claims up to 18.5% accuracy gain on LongMemEval temporal/cross-session tasks and 90% latency reduction. — [arXiv 2501.13956](https://arxiv.org/abs/2501.13956); [Zep blog](https://blog.getzep.com/state-of-the-art-agent-memory/)
- Mem0 paper LoCoMo table (GPT-4.1-mini): Mem0 34.20 overall at 1,764 tokens, Zep 32.40 at 1,602, MemGPT 18.51 at 16,977; full-context costs 25k+ tokens per call versus Mem0 under 7k. Mem0's own site claims 92.5 on LoCoMo and 94.4 on LongMemEval. Both are 90% faster than full-context. — [Mem0 paper](https://arxiv.org/pdf/2504.19413); [Mem0 research](https://mem0.ai/research); the SOTA claim is disputed by [Zep](https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/)
- A-MEM (Zettelkasten-style linked notes with LLM-generated keywords/tags and memory evolution): claims up to 6x gain on multi-hop reasoning and 85-93% fewer memory-operation tokens versus baselines. — [arXiv 2502.12110](https://arxiv.org/pdf/2502.12110); [summary](https://www.alphaxiv.org/overview/2502.12110)
- HippoRAG combines dense retrieval with a knowledge graph on hippocampal-indexing ideas; HippoRAG 2 reports 7% gain on associative-memory tasks (ICML 2025). — [arXiv 2405.14831](https://arxiv.org/pdf/2405.14831)
- MemoryBank applies an Ebbinghaus forgetting curve so memories decay with time and strengthen with reinforcement; demonstrated in the SiliconFriend companion chatbot; works with ChatGLM and ChatGPT; code public. — [arXiv 2305.10250](https://arxiv.org/abs/2305.10250); [repo](https://github.com/zhongwanjun/MemoryBank-SiliconFriend)
- LongMemEval (ICLR 2025): 500 questions over five abilities (extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention); commercial assistants and long-context LLMs show about a 30% accuracy drop over sustained interaction; proposes session decomposition, fact-augmented key expansion and time-aware query expansion. — [arXiv 2410.10813](https://arxiv.org/abs/2410.10813)
- Role-play-specific memory work exists: MOOM (ultra-long role-playing dialogue memory) and a 2026 graph-based "selective forgetting" framework. — [arXiv 2509.11860](https://arxiv.org/pdf/2509.11860); [arXiv 2608.28978](https://arxiv.org/pdf/2608.28978)

### Inferences
- Benchmark scores across Mem0, Zep and Letta are not comparable (different judges, models, and protocol disputes), so pick memory by architecture fit, not leaderboard rank.
- Decay-plus-reinforcement (MemoryBank) and temporal invalidation (Graphiti) together give a plausible recipe for "remember and forget"; sleep-time consolidation is the natural home for the "subconscious" requirement because it costs no user-facing latency.
- Memory extraction calls at write time are the main local-model cost; retrieval itself is embedding-only.

### Gaps
- Zep and Mem0 self-reported numbers were not independently verified; no independent head-to-head found.
- Local 7-12B viability for Mem0/Graphiti extraction (graph extraction is LLM-heavy) not sourced.
- MemGPT's per-turn call count (function-call loop) not sourced.
- Mem0 licence/stars not checked.

## 4. Inner monologue and thinking before speaking

### Takeaway
Explicit inner thought helps dialogue when it is structured and character-aware; raw reasoning-model traces hurt roleplay through attention diversion and formal style drift. Inner Thoughts (CHI 2025) is the best human-evaluated design for "think, then decide whether and when to speak".

### Cited Findings
- Inner Thoughts (CHI 2025): AI keeps a continuous covert train of thought in parallel with the conversation and models intrinsic motivation to voice it; built from a 24-participant formative study; beat a next-speaker-prediction+persona baseline on all seven metrics (turn appropriateness, coherence, anthropomorphism, engagement, intelligence, initiative, adaptability) and was preferred over 82% of the time; open-sourced with a playground app and the chatbot Swimmy. — [ACM](https://dl.acm.org/doi/10.1145/3706598.3713760); [arXiv 2501.00383](https://arxiv.org/abs/2501.00383); [repo](https://github.com/xybruceliu/inner_thoughts)
- RoleThink benchmark and MIRROR method: three-step thought generation (retrieve relevant memories, predict character reactions, synthesise motivations) outperforms prior methods at generating character inner thoughts. — [arXiv 2503.08193](https://arxiv.org/abs/2503.08193)
- Role-Aware Reasoning (Jun 2025): applying large reasoning models directly to characters causes "attention diversion" (forgetting the role) and "style drift" (formal reasoning that conflicts with personality); Role Identity Activation and Reasoning Style Optimization fix both. — [arXiv 2506.01748](https://arxiv.org/abs/2506.01748)
- Quiet-STaR trains a model to generate rationales at each token; zero-shot GSM8K 5.9% to 10.9% and CommonsenseQA 36.3% to 47.2%. It is a pretraining method and not a dialogue technique. — [arXiv 2403.09629](https://arxiv.org/abs/2403.09629)

### Inferences
- Inner Thoughts-style loops add at least one hidden LLM call per turn (thought generation, plus a scoring/decision step); exact call counts were not extracted.
- A short in-character hidden thought (few sentences, first person, in the character's voice) is the cheap version; long generic reasoning traces are the version the evidence warns against.
- Hidden vs shown thoughts: the papers above treat thoughts as private state; showing them is a product choice, not addressed in evidence.

### Gaps
- Inner Thoughts' number of LLM calls, models and latency not found (abstract-level fetch).
- No evidence found comparing hidden-thought pipelines on 7-12B local models.
- Quiet-STaR is not practically usable for Kataki (requires training); no dialogue-specific evidence.

## 5. Emotion and affect engines

### Takeaway
Appraisal-then-respond is the best-evidenced pattern: a cheap extra call that produces an emotional state which is stored and fed into the reply. Evidence is real but thin (one 30-participant study, gpt-3.5-turbo).

### Cited Findings
- Chain-of-Emotion (Croissant et al., 2024): 2 LLM calls per turn (an appraisal call, then the response call with the stored emotion chain), gpt-3.5-turbo at temperature 0; appraisal prompting reached 0.83 on STEU versus 0.57 baseline; in a 30-participant within-subject study, reactions rated more natural (F[2,84]=3.65, p=.03) and more emotion-sensitive (p=.04) than controls. Limits: single model, breakup scenario only, no memory retrieval. — [PMC11086867](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11086867/); [arXiv 2309.05076](https://arxiv.org/pdf/2309.05076)
- CPM-MultiAgent (Jul 2026): component-process-model appraisal by collaborating agents, with trigger extraction, appraisal and emotion-state update; claims effective dynamic emotional evolution via baselines, ablations and human evaluation; agent count and call count not stated in the abstract. — [arXiv 2607.07824](https://arxiv.org/abs/2607.07824)
- Also found: desire-driven emotional cognitive modelling for social simulation (Oct 2025), and a third-person appraisal agent (EMNLP Findings 2025). — [arXiv 2510.13195](https://arxiv.org/html/2510.13195v1); [search listing](https://arxiv.org/pdf/2607.07824)
- Humanoid Agents' discrete emotion and closeness state (see section 1). — [ACL Anthology](https://aclanthology.org/2023.emnlp-demo.15/)
- "Mind the Gaps: Mixture-of-Minds" (arXiv 2608.06115) turned out to be about predicting individual survey responses with adapters on a Gemma 4 12B base including chain-of-emotion augmentation, not a believable-character architecture; it is out of scope. — [arXiv 2608.06115](https://arxiv.org/abs/2608.06115)

### Inferences
- A combined design: appraisal call updates a small mood vector plus a decaying emotion stack; mood slowly integrates emotions (this layering is my design suggestion, not from a source).
- Appraisal can be merged into the same call as the inner thought to keep the per-turn count at 2.

### Gaps
- EmotionBench and "emotional intelligence of LLMs" evaluations were not retrieved this round.
- No sourced OCC/EMA + LLM hybrid results; no data on mood (long-timescale) modelling with LLMs.
- Chain-of-Emotion untested on newer or local models.

## 6. Multi-module "society of mind", id/ego/superego, dual-process and metacognition

### Takeaway
Dual-process designs have solid task-performance evidence (fast model first, slow model on metacognitive trigger) but I found no believability-specific evidence for id/ego/superego style personas. PIANO is the strongest realised multi-module example.

### Cited Findings
- SOFAI-LM: metacognitive module coordinates a fast LLM with a slower reasoning model, gives targeted iterative feedback, and matches or beats a standalone reasoning model with much lower inference time (graph colouring, code debugging). — [arXiv 2508.17959](https://arxiv.org/abs/2508.17959)
- SwiftSage: fast/slow-thinking generative agent for interactive tasks. — [arXiv 2305.17390](https://arxiv.org/pdf/2305.17390)
- PIANO's controller and concurrency (section 1). — [arXiv 2411.00114](https://arxiv.org/html/2411.00114v1)

### Inferences
- The fast/slow split maps onto Kataki's setting: a small local model for the spoken reply, a larger or slower pass in the background (reflection, consolidation).
- Id/ego/superego decompositions cost N calls per turn; no evidence they beat a single structured hidden thought.

### Gaps
- No sourced paper on id/ego/superego or subconscious/conscious LLM agents with human evaluation.
- No measured latency for these designs on consumer GPUs.

## 7. Game and industry systems (Inworld, Convai, NVIDIA ACE, Ubisoft NEO)

### Takeaway
Published architecture detail is marketing-level: personality, memory, goals and emotions managed by a "Character Brain" over many models. Nothing gives per-turn call counts or believability studies.

### Cited Findings
- Inworld Character Engine has three layers (Character Brain, Contextual Mesh, Real-Time AI); the Brain manages personality, memory, goals and emotions and syncs 30+ models (speech, emotion, gesture, animation); long-term memory resolves contradictions and duplicates across sessions. — [NVIDIA blog](https://blogs.nvidia.com/blog/generative-ai-npcs/); [Inworld blog](https://inworld.ai/blog/introducing-long-term-memory)
- NVIDIA ACE bundles ASR, the Nemotron small language model (a 4B on-device variant is cited), TTS and Audio2Face, designed to run on a local RTX GPU with cloud fallback. — [NVIDIA](https://www.nvidia.com/en-us/geforce/news/gfecnt/20241/nvidia-ace-architecture-ai-npc-personalities/); [NVIDIA dev blog](https://developer.nvidia.com/blog/build-on-device-ai-companions-with-the-nvidia-ace-game-agent-sdk-and-unreal-engine-5-plugins/)
- Ubisoft NEO NPCs (GDC 2024) were built with Inworld and NVIDIA; demos cover environmental awareness, reactions and conversation memory; per a 2026 blog, no Ubisoft game has shipped with it. — [Ubisoft press release](https://staticctf.ubisoft.com/8aefmxkxpxwl/Mw2s4KjssknqHHh1VIf8V/720296810ecc3deae51778a219732c7f/PRESS_RELEASE_GDC_UbisoftUnveilsNEONPC_190324.pdf); [Wanderfolk (blog-tier)](https://wanderfolk.ai/ai-npcs-in-games/)

### Inferences
- Industry evidence supports the pattern of small local model + cloud fallback + separate memory service, but gives no comparative believability data.

### Gaps
- Convai not researched; Inworld internals beyond marketing not found.
- No industry data on calls per turn, latency budgets or failure rates.

## 8. What measurably improves believability, and known failure modes

### Takeaway
Best human-eval evidence: memory + reflection + planning (Generative Agents), inner thoughts with turn-taking (Inner Thoughts, 82% preference), appraisal (Chain-of-Emotion, modest), social-awareness modules (PIANO). Known failure modes: cooperativeness/over-politeness, hallucinated embellishment, retrieval failure, reasoning-induced style drift, cost.

### Cited Findings
- See section 1 (ablation numbers), section 4 (inner-thought preference and role-aware reasoning failures) and section 5 (appraisal).
- LLM lying is studied mostly as a safety problem; TactfulToM finds even top LLMs are worse than humans at understanding white lies, especially the emotional motivation behind them. — [arXiv 2509.17054](https://arxiv.org/pdf/2509.17054)
- Liars' Bench (72,863 lie/honest examples from four open-weight models) and LieCraft (12 LLMs) evaluate deception detection and propensity; LLM-as-judge detects fact-checkable lies at about 0.91 balanced accuracy. — [arXiv 2511.16035](https://arxiv.org/pdf/2511.16035); [arXiv 2603.06874](https://arxiv.org/pdf/2603.06874)
- AI companion app evaluations exist (naturalness, safety), but not architecture ablations. — [arXiv 2605.08093](https://arxiv.org/pdf/2605.08093)

### Inferences
- A character that lies convincingly needs an explicit private ground truth (what it knows, what it will say, why), which fits the hidden-thought stage; I found no paper that tests this.
- "Mistakes" and forgetting can be produced by the memory layer (decay, imperfect retrieval) rather than by prompting.
- Cost explosion comes from per-turn multi-call pipelines; the mitigation in the evidence is moving work to background/sleep-time and keeping the per-turn path to 1-2 calls.

### Gaps
- No ablation study isolating emotion, inner thought or forgetting on believability with local models.
- No sourced drift-over-long-horizon measurements for role-play beyond the Generative Agents norm-erosion note.
- Character-consistent lying in roleplay has no dedicated sourced benchmark beyond those above.

## 9. Summary table: component, best-known approach, evidence, cost, local viability

### Takeaway
The cheapest high-value stack is: retrieval memory with decay, one hidden character-voiced thought plus appraisal per turn, and background reflection/consolidation. Cost and viability columns are my estimates unless the row cites a number.

### Cited Findings
- Sources for each row are listed in sections 1-8 above.

### Inferences
| Component | Best-known approach | Evidence | Cost (LLM calls) | Local viability (7-12B, 8 GB) |
|---|---|---|---|---|
| Memory store and retrieval | Generative Agents recency/importance/relevance score; Graphiti-style temporal facts | Ablation d=8.16 for full stack; Zep LongMemEval +18.5% (self-reported) | Write-time extraction 1 call per turn or batch; retrieval is embedding-only | Good for retrieval; extraction quality on small models unverified |
| Forgetting | MemoryBank Ebbinghaus decay with reinforcement | SiliconFriend demo, no human-eval numbers found | 0 (arithmetic) | Good |
| Reflection | Importance-triggered reflection (threshold 150, 2-3 per day) | Removing reflection lowers believability 29.89 to 26.88 | 1-3 background calls per trigger | Fine off the critical path |
| Offline consolidation / subconscious | Letta sleep-time agents; Auto-Dreamer | Letta blog and early paper; Auto-Dreamer abstract-level | Background only | Good if run when GPU idle |
| Inner thought | Short character-voiced thought (MIRROR/Inner Thoughts style) | Inner Thoughts 82% preference; RoleThink | +1 call per turn | Feasible; keep it short, avoid long reasoning traces |
| Emotion and mood | Appraisal call (Chain-of-Emotion) + discrete state (Humanoid Agents) | 30-participant study, p .03-.04 | +1 call (can merge with thought) | Feasible; untested on small models |
| Needs / drives | Humanoid Agents needs and closeness | Demo-level | 0-1 | Good (rule-based updates possible) |
| Concurrency and coherence | PIANO fast/slow modules + Cognitive Controller | Ablations on Minecraft, GPT-4o only | High (many modules) | Poor on one 8 GB GPU; borrow the fast/slow idea only |
| Lying / secrets | Private ground truth in hidden thought (my suggestion) | None found for roleplay; TactfulToM shows LLM weakness | +0 (part of thought) | Unknown |
| Dual-process routing | SOFAI-LM metacognitive router | Task benchmarks, not believability | 1 fast + occasional slow | Possible via cloud fallback |

### Gaps
- Costs are order-of-magnitude estimates; per-turn call counts for most systems were not published in the material retrieved.
- Local-model viability is inference throughout; no source directly tests these components on 7-12B models.
