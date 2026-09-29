# Human-like memory and forgetting for Kataki characters (implementation-grade note, Sept 2026)

> Method note. WebSearch hit its session budget partway, so most facts below come from fetched pages (arXiv HTML/abs, docs, HF model cards, Wikipedia for psychology basics). Several fetches were summarised by a small model; where a summary was vague or the PDF could not be parsed I say so in Gaps. Vendor benchmark numbers conflict and are flagged. Anything I could not source is under Inferences or Gaps, never Cited Findings.
> Important repo fact found late: Kataki M1 already ships most of a human-like memory engine (per-knower knowledge, ACT-R-style decay, gist/detail tiers, effortful recall, contradiction handling, static-embedding retrieval). Section 7 is therefore a delta on that engine, not a greenfield design. Repo sources: `D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md`, `D:/Kataki/engine/src/kataki/activation.py`, `embed.py`, `schema.sql`.

## 1. Existing memory systems and benchmarks: how they work, what they cost, what actually wins

### Takeaway
Every serious system is a variation on: write (LLM extracts facts or notes) -> store (vectors, sometimes graph) -> retrieve (cosine + keyword, sometimes graph/rerank) -> optionally consolidate offline. Retrieval memory cuts tokens 3-15x versus full context at a small accuracy cost, but leaderboard numbers are self-reported and not comparable, no benchmark scores forgetting, and every method is weak at conflict resolution. Kataki's zero-LLM-per-turn retrieval is at the cheap end of the cost spectrum; the LLM-heavy write paths (Mem0, A-MEM, Graphiti) are what cost tokens.

### Cited Findings
**Generative Agents (memory stream)**
- Retrieval score = recency + importance + relevance, all alphas 1, min-max normalised; recency = exponential decay over sandbox hours since last retrieval with factor 0.995; importance = LLM rating 1-10 ("brushing teeth" = 1, "a break up" = 10); relevance = cosine similarity of embeddings. — [Generative Agents (ar5iv)](https://ar5iv.labs.arxiv.org/html/2304.03442)
- Records hold natural-language description, creation timestamp, last-access timestamp. Reflection fires when summed importance of recent events exceeds 150 (about 2-3 times per simulated day): questions from the 100 most recent records, retrieval per question, insights with cited evidence. 25 agents for two days cost "thousands of dollars" in tokens. — [Generative Agents (ar5iv)](https://ar5iv.labs.arxiv.org/html/2304.03442)
- Failure modes reported: retrieval failures, hallucinated embellishment, norm erosion as memory grew; ablation: full architecture beat no-reflection and no-memory variants on believability. — [Phase-1 note 03](D:/Kataki/docs/research/research_notes/Human like minds for Kataki/03_cognitive_architectures.md)

**MemoryBank (Ebbinghaus)**
- Retention R = e^(-t/S); S is a discrete strength starting at 1; on recall "increase S by 1 and reset t to 0". No explicit forgetting threshold is specified. Event and personality summaries are LLM-generated; retrieval is dense (FAISS, MiniLM for English open models). — [MemoryBank (ar5iv)](https://ar5iv.labs.arxiv.org/html/2305.10250)
- Simple exponential forms "were not found to provide a good fit" to human data; Ebbinghaus's own fit was logarithmic-power (b = 100k/(log t)^c + k, c=1.25, k=1.84). — [Forgetting curve (Wikipedia)](https://en.wikipedia.org/wiki/Forgetting_curve)

**MemGPT / Letta**
- Main context (system prompt, working-context block, FIFO queue with recursive summary of evicted messages) plus external recall storage (message DB) and archival storage; the LLM moves data via function calls. Memory-pressure warning at 70% of context; at 100% flush evicts about 50% of the queue and writes a new recursive summary. `request_heartbeat` chains multiple calls per user turn. — [MemGPT (arXiv HTML)](https://arxiv.org/html/2310.08560)
- DMR accuracy depends heavily on the model driving the function calls: GPT-3.5 Turbo 38.7% -> 66.9% with MemGPT, GPT-4 32.1% -> 92.5%. — [MemGPT (arXiv HTML)](https://arxiv.org/html/2310.08560)
- Letta sleep-time agents: background subagents review recent conversations and update memory, triggered every N completed steps or on context compaction; proposals can optionally be reviewed before applying. — [Letta docs](https://docs.letta.com/guides/agents/architectures/sleeptime/)
- Sleep-time compute paper: about 5x less test-time compute for equal accuracy, +13% (GSM-Symbolic) and +18% (AIME) from scaling sleep-time compute, 2.5x lower average cost per query when queries share context; gap widens as queries become more predictable from context. — [Sleep-time Compute (arXiv HTML)](https://arxiv.org/html/2504.13171v1)
- Letta's own test: agents given plain files with grep/search/open scored 74.0% on LoCoMo (GPT-4o mini) versus 68.5% for Mem0's reported score. Conclusion: LLMs use familiar tools better than bespoke memory APIs. (Vendor-authored.) — [Letta blog](https://www.letta.com/blog/benchmarking-ai-agent-memory)

**Mem0 (+graph)**
- Per message: 1 LLM extraction call (inputs: stored conversation summary, last 10 messages, current pair) then one LLM tool call per extracted fact choosing ADD / UPDATE / DELETE / NOOP. Mem0g adds a Neo4j graph (entities, labeled triplets, GPT-4o-mini extraction). — [Mem0 paper (arXiv HTML)](https://arxiv.org/html/2504.19413)
- LoCoMo LLM-judge scores from the Mem0 paper (single-hop / multi-hop / temporal / open-domain; total latency p50/p95; tokens per query): Mem0 67.1 / 51.2 / 55.5 / 72.9, 0.71s/1.44s, ~1,764 tok. Mem0g 65.7 / 47.2 / 58.1 / 75.7, 1.09s/2.59s, ~3,616 tok. Zep 61.7 / 41.4 / 49.3 / 76.6, 1.29s/2.93s, 600k+ tok (as measured by Mem0). LangMem 62.2 / 47.9 / 23.4 / 71.1, search p50 17.99s / p95 59.82s. OpenAI memory 63.8 / 42.9 / 21.7 / 62.3. A-Mem 39.8 / 18.9 / 49.9 / 54.1. Full context: open-domain 72.9, 9.87s/17.12s, ~26,031 tok. — [Mem0 paper (arXiv HTML)](https://arxiv.org/html/2504.19413) (authored by a competitor of Zep, LangMem and A-Mem)
- Open-source defaults: `gpt-5-mini` LLM, `text-embedding-3-small`, local Qdrant (library) or Postgres+pgvector (self-hosted), SQLite history; all overridable. — [Mem0 OSS docs](https://docs.mem0.ai/open-source/overview)

**Zep / Graphiti (temporal knowledge graph)**
- Three subgraphs: raw episodes (non-lossy), semantic entities/edges, communities (label propagation + summaries). Bi-temporal edges: t_valid/t_invalid (when true) and t_created/t_expired (when the system learned/retired it). New edges are compared by an LLM against related existing edges; contradicted edges get t_invalid set, not deleted. — [Zep paper (arXiv HTML)](https://arxiv.org/html/2501.13956)
- Ingestion: entity extraction with n=4 message context, 1024-d embeddings, cosine + full-text candidate search, LLM dedupe. Retrieval: cosine + BM25 + BFS, reranked by RRF, MMR, episode-mentions, node distance or cross-encoder (highest cost). — [Zep paper (arXiv HTML)](https://arxiv.org/html/2501.13956)
- LongMemEval (avg 115k tokens): GPT-4o-mini 63.8% vs 55.4% baseline, latency 3.20s vs 31.3s, 1.6k vs 115k context tokens; GPT-4o 71.2% vs 60.2%; categories: preference +184%, temporal +38.4%, multi-session +30.7%, knowledge update +6.5%, single-session-assistant -17.7%. — [Zep paper (arXiv HTML)](https://arxiv.org/html/2501.13956)

**A-MEM (Zettelkasten)**
- Note = content, timestamp, LLM keywords, LLM tags, LLM context description, embedding, links. Each new memory costs 3 LLM calls (note construction, link generation, evolution of neighbouring notes). About 1,200 tokens per operation, about $0.0003 on commercial APIs; claims 85-93% fewer tokens than baselines. Own LoCoMo F1 (GPT-4o-mini): single-hop 44.65, multi-hop 27.02, temporal 45.85, open-domain 12.14, adversarial 50.03. — [A-MEM (arXiv HTML)](https://arxiv.org/html/2502.12110); Mem0's independent-ish run scored A-Mem far lower (above), so results conflict.

**HippoRAG 2**
- Phrase nodes plus passage nodes in a KG, LLM "recognition memory" filter on retrieved triples, personalized PageRank. Indexing 11,656 passages: 9.2M input + 3.0M output tokens, 99.5 min; query 1.2s (NV-Embed-v2: 0.3s); 9.9 GB GPU for QA; average F1 59.8 vs 57.0 (NV-Embed-v2), +7% on associative-memory tasks. It targets document RAG, not chat logs. — [HippoRAG 2 (arXiv HTML)](https://arxiv.org/html/2502.14802)

**LangMem, Cognee**
- LangMem: semantic memory as collections or single updated profiles, episodic memory (situation/reasoning/outcome), procedural memory (behaviour rules evolving from feedback); formation either "hot path" (adds latency) or background (post-conversation). — [LangMem guide](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/)
- Cognee v1 exposes remember / recall / improve / forget over relational (provenance), vector and graph stores with lightweight local defaults. — [Cognee docs](https://docs.cognee.ai/core-concepts/overview)

**Forgetting-aware and consolidation research (2026)**
- FadeMem: strength v(t) = v0 * exp(-lambda * (t - tau)^beta), lambda = 0.1 * exp(-mu * importance); beta 0.8 for long-term layer (half-life about 11.25 days at importance 0) and 1.2 for short-term layer (about 5.02 days); promote at 0.7, demote at 0.3 (hysteresis); LLM classifies conflicts (compatible / contradictory / subsumes / subsumed); fusion of memories at cosine 0.75. LoCoMo multi-hop F1 29.43 vs Mem0 28.37 vs MemGPT 9.46; 45% storage reduction with 82.1% critical-fact retention. Used GPT-4o-mini for conflict and fusion; call frequency not stated. — [FadeMem (arXiv HTML)](https://arxiv.org/html/2601.18642v1)
- FSFM: three strategies (passive decay e^(-lambda t), active deletion incl. user requests/privacy, adaptive reinforcement); evaluated on ~440k government records, not dialogue. — [FSFM (arXiv HTML)](https://arxiv.org/html/2604.20300)
- Auto-Dreamer: typed bank (semantic + procedural), each entry has provenance links to source trajectories; consolidation every k sessions over a "working region" (new entries plus older entries recently retrieved); old entries are read-only evidence, a replacement set supersedes the region; trained with GRPO; banks 6-12x smaller; consolidator Qwen3-14B, task agent Qwen3.5-9B; evaluated only on ScienceWorld/ALFWorld/WebArena, no seed variance. — [Auto-Dreamer (arXiv HTML)](https://arxiv.org/html/2605.20616v1)
- Retrieval-driven reconsolidation (arXiv 2609.16053): update a memory when retrieved; reported about 2-3 extra LLM calls per retrieval event (20-35% more calls overall), versioning and anchor retention as safeguards, and the paper itself flags error compounding across chained updates. — [arXiv 2609.16053](https://arxiv.org/pdf/2609.16053) (small-model summary of a PDF; treat numbers as unverified)
- A "Dreaming" feature request for an open-source agent proposes light/REM/deep phases, a weighted score (relevance 30%, frequency 24%, query diversity 15%, recency 15%, consolidation 10%, richness 6%), promotion at 0.6 with min 2 occurrences, nightly cron skipped if the user was active in the last 60 min. It is a proposal, not shipped. — [hermes-agent issue 25309](https://github.com/NousResearch/hermes-agent/issues/25309)

**SillyTavern and companion apps (baseline the market lives with)**
- Summarize: triggers every X messages or words (whichever first), modes raw blocking / raw non-blocking / classic blocking, injected before/after main prompt or in-chat; docs warn summaries "lose some important details or contain hallucinations". — [ST Summarize docs](https://docs.sillytavern.app/extensions/summarize/)
- World Info: regex keys, AND/NOT filters, scan depth, sticky / cooldown / delay timed effects, probability, inclusion groups with weights, recursion, token budget, several insertion positions. — [ST World Info docs](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- Nomi, Kindroid, Replika, Character.AI, Paradot memory features, and the "memory is the #1 complaint" finding are in [Phase-1 note 02](D:/Kataki/docs/research/research_notes/Human like minds for Kataki/02_market_scan.md) (Kindroid journal cap 500 entries, 3 recalled per message; Replika memory dashboard 2026; Nomi Mind Map 2.0 graph + editable table).

**Benchmarks**
- LoCoMo: ~300 turns / ~9k tokens / ~35 sessions per conversation; does not explicitly score knowledge updates. LongMemEval: five abilities (extraction, multi-session reasoning, temporal reasoning, knowledge update, abstention), S ~115k tokens, M ~500 sessions; primarily tests retrieval, write quality barely measured. BEAM (ICLR 2026): 1M and 10M-token tracks, 2,000 questions, ten abilities; Mem0 self-reports 64.1% (1M) and 48.6% (10M). Self-reported LoCoMo: Mem0 92.5%, Zep 94.7% (claimed) vs 75.1% (tested by a competitor); LongMemEval: Mem0 94.4%, Zep 71.2%. The same source states no public benchmark adequately tests memory write quality, forgetting/eviction dynamics or token-budgeted efficiency. — [Mem0 benchmark guide](https://mem0.ai/blog/ai-memory-benchmarks-in-2026) (vendor blog)
- LongMemEval: commercial assistants and long-context LLMs show about a 30% accuracy drop on sustained interactions; recommended fixes: session decomposition (value granularity), fact-augmented key expansion, time-aware query expansion. — [LongMemEval (arXiv)](https://arxiv.org/abs/2410.10813)
- MemoryAgentBench: four competencies (accurate retrieval, test-time learning, long-range understanding, selective forgetting). On conflict resolution "all methods fail on the multi-hop situation (at most 28%)"; RAG agents win accurate retrieval (~60%), long-context models win test-time learning and long-range understanding. — [MemoryAgentBench (arXiv HTML)](https://arxiv.org/html/2507.05257)
- Locomo-Plus (arXiv 2602.10715): tests "cue-trigger semantic disconnect", i.e. applying a latent constraint when the later cue does not overlap the original wording; cognitive memory "remains challenging" for RAG and long context alike. — [Locomo-Plus (arXiv)](https://arxiv.org/abs/2602.10715)
- Longitudinal "tenure crossover" (arXiv 2607.21962): architecture rankings change with agent tenure (simple designs lead short-tenure, more elaborate ones long-tenure). — [arXiv 2607.21962](https://arxiv.org/pdf/2607.21962) (small-model summary, low confidence). A cost-aware study (arXiv 2609.05441) concludes memory systems do not always beat simple full-context baselines once cost is counted. — [arXiv 2609.05441](https://arxiv.org/pdf/2609.05441) (same caveat).

### Inferences
- Cost comparison per system, per turn / write path / storage / fully local? (Kataki-relevant reading of the numbers above; token counts are the papers', local viability is my judgment):

| System | Extra LLM calls per turn | Background/write cost | Storage | Fully local? |
|---|---|---|---|---|
| Generative Agents | 0 retrieval; 1 importance call per observation; reflection ~2-3/day | reflection is the big cost | flat stream + vectors | yes in principle, expensive |
| MemoryBank | 0 | daily event/personality summaries | FAISS + summaries | yes |
| MemGPT/Letta | 1-N (function-call loop, heartbeat) | recursive summary on flush; sleep-time agent every N steps | recall + archival DB | partly: needs a strong tool-calling model (DMR gap GPT-3.5 vs GPT-4) |
| Mem0 | 0 to search (~0.15s p50); 1 + n calls per message to write | per message | vectors (+Neo4j for graph) | partly: pipeline is model-agnostic but tuned on gpt-4o-mini class |
| Zep/Graphiti | 0 to search (0.5s p50) | several LLM calls per episode (extract, dedupe, invalidate); count not stated in paper | Neo4j-class graph | partly, heavy |
| A-MEM | 0 to search; 3 calls per memory | ~1,200 tok/op | notes + links | partly |
| HippoRAG 2 | 1 filter call per query | 12M tokens to index 11.7k passages | KG + PPR | no on 8 GB |
| LangMem | 0 (background mode) | background reflection | any store | partly; measured search latency was very slow in Mem0's test |
| Kataki M1 (existing) | 0 | 1.2 utility calls per 5 turns (repo spec) | SQLite + float32 blobs | yes |

- What wins for a roleplay app: not a leaderboard system. The winning pattern is hybrid retrieval over well-formed, small memory units (LongMemEval's granularity + key-expansion advice; Zep's 1.6k-token contexts; Mem0's 1.8k) with temporal handling and a small always-on profile. The evidence that a plain filesystem+grep agent matches specialised systems (Letta, vendor) and that memory does not always beat full context (2609.05441) argue against buying complexity before it is measured.
- The gap nobody measures is exactly Kataki's product: forgetting, distortion, per-knower perspective. Benchmarks reward remembering everything, so Kataki needs its own probes (Section 7) rather than borrowing LoCoMo scores. LongMemEval's abstention category is the one borrowable idea: a character who has forgotten must say so rather than fabricate.
- Zep's bi-temporal "invalidate, don't delete" and Auto-Dreamer's "read-only sources + provenance-linked replacement" are the two published patterns that match Kataki's append-only, `supersedes_id`, `run_id` design; Kataki already has both.

### Gaps
- No independent head-to-head of Mem0, Zep, Letta, A-MEM on a common protocol; all cross-system numbers are vendor-run.
- No sourced test of Mem0/Graphiti/A-MEM extraction quality with 7-12B local models (Kataki's own eval used Qwen3.5-9B Q4_K_M and found schema-constrained extraction workable; see repo spec progress log).
- Zep's exact LLM calls per episode not in the fetched text; Mem0's 600k+ tokens for Zep is Mem0's measurement and Zep disputes Mem0's methodology (phase-1 note 03 cites the dispute).
- MemoryBank paper's actual thresholds/experiments not read beyond the formula; the 2609.05441 and 2607.21962 papers were only read through lossy summaries.
- BEAM paper itself not fetched (numbers via vendor blog).

## 2. Human-like forgetting done right: decay, salience, interference, visible vs buggy forgetting, tip-of-the-tongue, false memory, reconsolidation, gist vs verbatim, sleep

### Takeaway
The psychology supports a compact rule set: power-law-ish decay boosted by spaced retrieval, emotional arousal that protects the gist and central details but not peripheral ones, retrieval that suppresses competitors, gist outliving verbatim (and gist-consistent errors growing), retrieval making a memory editable, and offline consolidation. All of it can be computed at render time with zero LLM calls; only wording distortion and consolidation need a model, and both can be done at write time or in idle jobs.

### Cited Findings
- Ebbinghaus (1880-85) measured savings with nonsense syllables; people roughly halve newly learned material within days or weeks without review; reviewing within 24 h resets the curve; a 2015 replication reproduced the original. Exponential R = e^(-t/S) fits poorly. — [Forgetting curve (Wikipedia)](https://en.wikipedia.org/wiki/Forgetting_curve); replication details also in [Phase-1 note 01](D:/Kataki/docs/research/research_notes/Human like minds for Kataki/01_what_makes_humans_human.md) (Murre & Dros, curve not smooth, probable upward jump after 24 h).
- Kataki's engine already uses ACT-R base-level learning B = ln(sum w_j * dt_j^-d), d = 0.5, with importance, relevance, graph, fidelity and noise terms; recall counts as rehearsal at weight 0.5. — [Kataki M0/M1 spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md); [activation.py](D:/Kataki/engine/src/kataki/activation.py)
- Fuzzy-trace theory (Reyna and Brainerd, 1990s): parallel verbatim and gist traces; verbatim decays faster; "true memory decays over time while false memory increases"; gist-consistent lures produce false memories because gist supports them while verbatim suppresses them ("recollection rejection"); adults prefer gist for decisions. — [Fuzzy-trace theory (Wikipedia)](https://en.wikipedia.org/wiki/Fuzzy-trace_theory)
- Emotional arousal (amygdala) improves retention but narrows to central details at the expense of peripheral ones (weapon focus; Easterbrook 1959); flashbulb memories keep high confidence even when accuracy does not; current mood biases what is recalled (mood-congruent retrieval, mood-state-dependent retrieval). — [Emotion and memory (Wikipedia)](https://en.wikipedia.org/wiki/Emotion_and_memory)
- Emotional RAG applies mood-dependent memory to role-playing agents with a combination strategy (emotion + semantic similarity together) and a sequential strategy (staged), beating baselines on three role-play datasets. — [Emotional RAG (arXiv)](https://arxiv.org/abs/2410.23041)
- Retrieval-induced forgetting (Anderson, Bjork and Bjork 1994): after practising some category members, practised items recall ~81%, related unpracticed ~55%, unrelated baseline ~68%; strongest when related items compete during practice; cue-independent. — [Retrieval-induced forgetting (Wikipedia)](https://en.wikipedia.org/wiki/Retrieval-induced_forgetting)
- Misinformation effect: post-event information degrades episodic recall (Loftus and Palmer 1974); about 30% of participants formed partial or full false childhood memories in "lost in the mall"; susceptibility rises with delay, source misattribution and low confidence, falls with stress/arousal after learning. — [Misinformation effect (Wikipedia)](https://en.wikipedia.org/wiki/Misinformation_effect)
- Reconsolidation: recalled consolidated memories become temporarily unstable and open to modification (Nader, Schafe, LeDoux 2000, rats; see [Nature](https://www.nature.com/articles/35021052)); sleep reorganises memories between hippocampus and neocortex through slow-wave reactivation. — [Memory consolidation (Wikipedia)](https://en.wikipedia.org/wiki/Memory_consolidation)
- Tip-of-the-tongue: failed retrieval with partial recall (first letter, syllable count, phonetic neighbours, semantic relations) and a feeling retrieval is imminent; partial retrieval is far better than chance (Brown and McNeill 1966); most states resolve spontaneously or with priming. — [Tip of the tongue (Wikipedia)](https://en.wikipedia.org/wiki/Tip_of_the_tongue)
- Schacter's seven sins (transience, absent-mindedness, blocking; misattribution, suggestibility, bias, persistence) and the guidance that character memory should hold gist plus a decaying strength that is refreshed on recall and rewritten slightly on recall — [Phase-1 note 01](D:/Kataki/docs/research/research_notes/Human like minds for Kataki/01_what_makes_humans_human.md).
- Kataki's current forgetting design: two activations (A_all for coming to mind, A_detail for whether detail survives), SHARP >= -2.0 injects detail, HAZY >= -4.0 injects gist with a "(hazy)" marker, detail ratchet (gist recall never resurrects detail), one reinforcement per scene, "effortful recall" roll p = sigmoid(A_detail + 2.0) on the second consecutive hazy injection, worked example table (importance 9 stays SHARP a day later, HAZY after six years; retold yearly stays SHARP). YAGNI list explicitly excludes "mutating stored memories to fake distortion" and "reflection / dream cycles". — [Kataki M0/M1 spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- Kataki logs context per turn (activation breakdown bars, what was cut) and the inspector filters memories by knower/tier/tag with edit/hide/add. — [Kataki M0/M1 spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- The archetypal "system lost it" bug in this market: SillyTavern Summarize silently defaulting to a deprecated Extras server so the summary box stays empty with no error; recursive summaries compound loss. — [Phase-1 note 02](D:/Kataki/docs/research/research_notes/Human like minds for Kataki/02_market_scan.md)
- Recursive summarisation (each new memory built from previous memory plus new turns) improves consistency but is the shape that compounds errors. — [Recursive summarization (arXiv)](https://arxiv.org/abs/2308.15022)

### Inferences
- Decay: keep the ACT-R power-law form (it beats MemoryBank's exponential and FadeMem's Weibull for this use because it is parameter-light, has one user slider, and the spec already shows a 2x story-time error costs only about 0.35 activation units). FadeMem's contribution worth borrowing is hysteresis between layers, which Kataki gets from the SHARP/HAZY thresholds plus the detail ratchet.
- Spacing effect comes free: the one-reinforcement-per-scene cap makes rehearsal spaced by construction.
- Distinguishing "forgot" from "system lost" needs an explicit reason code on every non-recall. Character-forgot reasons: not witnessed, below HAZY threshold, not cued. System-lost reasons: budget-cut while SHARP, extraction pending/failed, run stale/off-branch, embedder missing. The audit invariant: no memory with A >= SHARP_AT may be dropped for any system reason without a visible "system" badge; the existing rule "a message leaves the verbatim window only if an ok run covers it" is the right guard and should be tested as a property.
- Misremembering, reconsolidation and false memory can be implemented without violating "nothing is mutated": store per-knower recollection variants as append-only rows over intact truth (Section 7). The retelling itself is the mutation event: when a character says the memory aloud, whatever they said becomes their new version. That copies Loftus/reconsolidation findings and needs no extra call because extraction already reads the new lines.
- Human-realistic distortion targets peripheral slots (place, time of day, who else was there, who said what) and source (told vs saw), leaves the emotional core, and leaves confidence untouched (flashbulb pattern). Distortion probability should rise as detail activation falls (fuzzy-trace) and should never touch pinned or user-locked memories.
- Tip-of-the-tongue partial cues can be built by code from data already stored (initial letter of a linked entity name, the place entity, the emotion word, a coarse "years ago"), so a hazy memory under pressure can be rendered as a true partial cue rather than model invention. This upgrades the current "effortful recall" roll from all-or-nothing to graded.
- Retrieval-induced forgetting is cheap to add as a small negative term for near-duplicate competitors that lost in a scene where a sibling was recalled; it also explains why repeated routine events blur. Risky for small models, so ship behind a "dreamlike" setting.
- Emotion is stored (`memories.emotion`) but not used in scoring today; mood-congruent retrieval needs one numeric valence per memory (extracted in the same call) and the speaker's current mood from the existing flags/feelings signals.
- Sleep: a deterministic "sleep replay" at time skips that crosses a night (adds a low-weight rehearsal access to the highest-importance recent memories) reproduces the after-24h bump for zero cost.

### Gaps
- Primary papers for Anderson 1994, Loftus, McGaugh, Diekelmann and Born were read only through Wikipedia summaries; numbers such as 81/55/68% come from the Wikipedia article, not the paper.
- ACT-R base-level equation and default d = 0.5 could not be fetched from ACT-R docs (page had no formulas); the equation is cited via Kataki's own spec, not the ACT-R manual.
- No source on how much false-memory rate is "pleasant" to users in roleplay; the distortion rates in Section 7 are design defaults to tune, not evidence.
- No empirical study found comparing users' perception of "character forgot on purpose" versus "app has a bug"; recommendation for reason-code UI is design reasoning.

## 3. Memory types: episodic, semantic user facts, relationship, self-narrative, procedural; per-character memory in group scenes

### Takeaway
Published systems separate memory kinds into typed stores (LangMem: semantic collections/profiles, episodic, procedural; Auto-Dreamer: semantic and procedural), and companion apps expose a small always-on identity block plus retrievable notes. Kataki already has episodic events, facts, claims, per-knower knowledge with provenance, relationship edges and typed flags. Missing typed layers are self-narrative, per-pair relationship summary and habit (procedural) memory, all best produced by idle consolidation. Per-character witnessing is already enforced by code and is the strongest differentiator.

### Cited Findings
- LangMem defines semantic memory as either collections (documents searched at runtime) or profiles (a single schema document updated in place), episodic memory as past situations with reasoning and outcomes, and procedural memory as behavioural rules refined through feedback. — [LangMem guide](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/)
- Auto-Dreamer keeps typed entries (semantic facts, procedural how-tos) with provenance to sources. — [Auto-Dreamer (arXiv HTML)](https://arxiv.org/html/2605.20616v1)
- Nomi combines layered memory with an "Identity Core" and an editable Mind Map; Kindroid separates persistent (backstory, key memories, directives), cascaded and retrievable memory. — [Phase-1 note 02](D:/Kataki/docs/research/research_notes/Human like minds for Kataki/02_market_scan.md)
- Kataki data model: `memories` (event | fact | claim), `memory_entities` roles (actor, target, witness, place, item, subject), `knowledge(knower, memory, source in witnessed|told|overheard|rumor|inferred|innate, told_by, learned_story_time, fidelity, belief)`, `edges` (relationships with story-time validity), `flags` (typed state), `accesses`. Retrieval hard-filters through `knowledge` and story_time <= now, so an absent character cannot recall an event at any relevance. Code, not the LLM, decides witnesses. The generation unit is one speaker so a reply never holds two characters' secrets. First-order theory of mind only. — [Kataki M0/M1 spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md); [schema.sql](D:/Kataki/engine/src/kataki/schema.sql)
- The Kataki spec records that three research passes found no existing RP platform shipping per-character epistemic memory, story-time decay or contradiction challenge. — [Kataki M0/M1 spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- Real-model finding in Kataki's own evals: scene summaries written omnisciently and placed in the shared prompt leaked a secret to a character who never heard it; summaries are now stored but never sent to characters, and the past reaches a character only through their own memory. — [Kataki M0/M1 spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- Generative Agents' reflection stores higher-level insights with citations back to the memories that support them. — [Generative Agents (ar5iv)](https://ar5iv.labs.arxiv.org/html/2304.03442)

### Inferences
- Type-to-mechanism map for Kataki:
  - Episodic: `memories` kind=event, per-knower `knowledge`, decays by A (exists).
  - Semantic facts about the user: `memories` kind=fact whose subject is the persona entity, `knowledge.source` told/inferred; slower effective decay because retold often (retold access weight 1.0 exists). Add "profile" view per character = top facts about the persona above a stability threshold, rendered as a compact always-on line set (LangMem profile idea) without adding a store.
  - Relationship memory: `edges` exist; add a derived per-pair `narratives(kind='relationship')` line ("Mira trusts Tobin less since the docks") produced at consolidation, injected only for characters present (about 40 tokens each, max 3).
  - Self-narrative: `narratives(kind='self')`, 3-6 sentences in first person, refreshed at long skips and at story milestones, anchored to top-importance memories; always injected in the speaker's tail (about 100 tokens). This is the Identity Core analogue and also the place where "I am the kind of person who..." consolidates.
  - Procedural/habits: `narratives(kind='habit')`, created when the same event pattern recurs (threshold about 4 occurrences), injected by cue like a lorebook entry with sticky/cooldown behaviour (borrowing SillyTavern's timed effects so habits do not fire every turn).
- Group scenes: keep the existing hard filter; the additional human-like effect is that each knower's recollection variant is separate, so two witnesses can remember the same event differently, and a `told` memory copies the teller's variant rather than the truth (telephone effect) with fidelity -0.5. Per-turn cost stays 0 LLM calls; storage is one knowledge row per knower per memory.
- Offscreen memory: extraction "covert" flag and participants-only witnesses already handle secrets; the missing piece is source amnesia for told memories (Section 7 rule D1).

### Gaps
- No published system found that implements per-character witness-bounded memory with decay for LLM roleplay beyond Kataki's spec; the spec mentions single-source 2026 preprints on perspective-bounded memory and deterministic conflict resolution that are unverified (repo open items), and I did not locate them.
- No sourced threshold for "how many repetitions make a habit"; the value 4 is a design default.
- Higher-order theory of mind (A knows that B knows) is explicitly out of scope in the repo; not researched here.

## 4. Local retrieval stack: embeddings, vector store, hybrid search, rerankers, CPU cost, prompt budget

### Takeaway
For per-story memory counts (thousands to low tens of thousands), brute-force cosine over a float32 matrix plus FTS5 BM25 fused with RRF is sufficient; Kataki already does this with a 32M static embedding model. A neural embedder (bge-small, nomic, EmbeddingGemma) is an optional upgrade; a cross-encoder reranker is not worth it by default because the activation formula already does the re-ranking that matters. Prompt budget for memory should stay about 900 tokens at 8k, growing to about 1.5k at 16k, in line with published systems (1.6-1.8k tokens).

### Cited Findings
- Kataki built-in embedder: `minishlab/potion-retrieval-32M` via model2vec, static, 125 MB, CPU, about 1-2 ms per text; any OpenAI-compatible `/v1/embeddings` endpoint can replace it; vectors stored as float32 blobs in SQLite; brute-force cosine over one matrix per story (comment says fine to about 200K vectors); fused with FTS5 BM25 by RRF (k=10). — [embed.py](D:/Kataki/engine/src/kataki/embed.py); [Kataki spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- bge-small-en-v1.5: 33.4M parameters, 384-d, 512 tokens, MTEB average 62.17 and retrieval 51.68, no query instruction required, MIT. — [HF card](https://huggingface.co/BAAI/bge-small-en-v1.5)
- nomic-embed-text-v1.5: 0.1B parameters, 8,192-token context, 768-d with Matryoshka (MTEB 62.28 at 768, 61.04 at 256, 59.34 at 128, 56.10 at 64), task prefixes `search_document:` / `search_query:` required, Apache-2.0. — [HF card](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5)
- EmbeddingGemma-300m: 308M parameters (about 100M model + 200M embedding), sub-200 MB RAM with quantisation-aware training, under 15 ms per 256 tokens on EdgeTPU, 2,048-token context, MRL 768/512/256/128, MTEB English v2 mean 69.67 (768) to 66.66 (128), Q8_0 69.49, runs in llama.cpp, Ollama, sentence-transformers, transformers.js; governed by the Gemma licence terms with access-gated download. — [Google blog](https://developers.googleblog.com/en/introducing-embeddinggemma/); [HF card](https://huggingface.co/google/embeddinggemma-300m)
- sqlite-vec: pure C SQLite extension, float/int8/bit vectors, brute-force search (no ANN yet), pre-v1 so breaking changes expected; benchmarks: 100k vectors x 768-d float about 50 ms, 1536-d about 105 ms; 1M float vectors exceed 100 ms; binary quantisation about 11 ms at 100k x 3072 and about 124 ms at 1M; runs in Node, WASM, Windows/macOS/Linux. — [sqlite-vec repo](https://github.com/asg017/sqlite-vec); [author's benchmarks](https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/index.html)
- Hybrid FTS5 + vector search via RRF: score = w_fts/(rrf_k + fts_rank) + w_vec/(rrf_k + vec_rank), typical rrf_k = 60, k = 10 per method; FTS5 has no metadata filtering so it scans the whole table each time. — [sqlite-vec hybrid search post](https://alexgarcia.xyz/blog/2024/sqlite-vec-hybrid-search/index.html)
- bge-reranker-v2-m3: 0.6B parameters, 512-token pairs, multilingual, Apache-2.0, fp16 option; a layerwise MiniCPM variant is offered for speed. — [HF card](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- Graphiti lists a cross-encoder as its highest-cost rerank option after RRF, MMR, episode-mentions and node distance. — [Zep paper (arXiv HTML)](https://arxiv.org/html/2501.13956)
- SillyTavern defaults referenced in phase 1: Vector Storage 3 chunks with a 2-message query window; retrieved messages relocate rather than append (breaks chronology). — [Phase-1 note 02](D:/Kataki/docs/research/research_notes/Human like minds for Kataki/02_market_scan.md)
- Kataki default context split at 8k: response 600, rules 350, cards+primer 1,400, summaries 900, memory tail 900, flags+directive 250, history remainder; eviction order drops memory detail to gist, then whole memories, before history. Utility model on a CPU-only 3-4B llama-server runs about 10-20 tok/s, acceptable because extraction is idle-time. — [Kataki spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- Published memory contexts per query: Mem0 about 1,764 tokens, Mem0g about 3,616, Zep 1.6k on LongMemEval, A-MEM about 1,200 per operation. — [Mem0 paper](https://arxiv.org/html/2504.19413); [Zep paper](https://arxiv.org/html/2501.13956); [A-MEM](https://arxiv.org/html/2502.12110)

### Inferences
- Storage math (mine): 20,000 memories x 384 floats x 4 B is about 31 MB per story; at 768-d about 61 MB. Brute-force numpy over that is single-digit milliseconds, so sqlite-vec is not needed until libraries approach the repo's own 200K ceiling, and its pre-v1 status is an added reason to wait.
- Embedding choice: memories are short first-person sentences (gist plus detail), where a 33-137M model is ample. Upgrade path by cost/benefit: keep potion-32M by default (zero setup); offer bge-small (MIT, 33M, 384-d) as the one-click neural option; nomic (long context is wasted on short memories; needs prefixes) and EmbeddingGemma (best MTEB, largest, gated licence terms) as user-selected via the existing `embed` role. MTEB numbers across these cards use different suites (v1 average vs English v2) and should not be compared directly.
- CPU cost for neural embedders on short texts is not sourced here; estimate a few ms per memory for bge-small on a modern 14-core laptop and tens of ms for EmbeddingGemma, embedded once at write time and once per query. Verify by measuring; it is background either way.
- Reranker: skip by default. Retrieval already applies importance, decay, graph and fidelity after RRF, which is where a roleplay-specific "reranker" lives. If quality on paraphrase cues (Locomo-Plus style disconnect) proves weak, add bge-reranker-v2-m3 on the top 15-20 candidates as a premium option; on CPU this is a per-turn cost of an estimated 1-3 s (unsourced), which conflicts with the zero-latency retrieval goal.
- Query construction: current default is entities in last two messages + current place + FTS/vector on recent text. LongMemEval's time-aware query expansion maps to the existing story_time filter; fact-augmented key expansion maps to embedding `gist + detail + tags_text + entity names` rather than detail alone (check what is embedded today).
- Prompt budget: 900 tokens holds roughly 8 detail-tier memories or 15-18 gist-tier at about 50-100 tokens each (my arithmetic). Allocate inside the memory tail: self-narrative 100, relationships up to 3 x 40, habits 60, recalled memories the rest.

### Gaps
- No measured CPU latency for bge-small/nomic/EmbeddingGemma on this machine (i9-13900H) found; needs a local benchmark.
- Which text Kataki currently embeds (detail only vs gist+detail+entities) was not confirmed in code.
- No sourced evidence on whether a reranker helps short first-person memory retrieval.

## 5. The memory ledger UI: view, edit, pin, and see why something was recalled

### Takeaway
Competitors expose what is remembered (Nomi Mind Map, Replika dashboard, Kindroid key memories, Character.AI pinned memories, Paradot "what it's learned") but none exposes why something surfaced or how strongly it is held. Kataki already computes an activation breakdown and logs context per turn, so the ledger is mostly presentation plus three additions: reason codes for absence, a truth-versus-character's-version diff, and read-only inspection.

### Cited Findings
- Nomi Mind Map 2.0: interactive graph plus searchable, editable table; Replika shipped a memory dashboard in early 2026 to view and correct extracted facts; Kindroid key memories and journal entries; Character.AI Chat Memories and Pinned Memories; Paradot claims to show what it has learned. Nobody exposes the character's inner state or recall reasoning. — [Phase-1 note 02](D:/Kataki/docs/research/research_notes/Human like minds for Kataki/02_market_scan.md)
- Reported weaknesses: Nomi auto-memory may miss what users care about or retain unwanted details; Kindroid can accumulate "memory noise" when used badly. — [Phase-1 note 02](D:/Kataki/docs/research/research_notes/Human like minds for Kataki/02_market_scan.md)
- Kataki inspector (M1): Context tab (activation breakdown bars, what was cut), Memories tab (filter by knower, tier, tag; edit, hide, add), Entities (flags timeline, merge chips), Runs; API `GET .../memories?knower=&q=&tier=&tag=` returns the activation breakdown at "now". `context_log` stores what reached the prompt and what was cut. Backstage "Mind graph" shows what recall weighed and what reached the prompt, drawing only what the engine recorded. — [Kataki spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md); [mind.py](D:/Kataki/engine/src/kataki/mind.py)
- Letta offers optional human review before sleep-time memory updates apply. — [Letta docs](https://docs.letta.com/guides/agents/architectures/sleeptime/)

### Inferences
- Ledger layout per character ("What Mira remembers"): grouped by tier (Sharp / Hazy / Fading / Gone), then story time. Row = text at current tier, source badge (saw it, told by X, overheard, rumour), sharpness bar (from A), pin icon, action menu.
- "Why recalled" chips built from existing terms: cue match S, entity overlap G, base level B (with "last rehearsed 3 scenes ago"), importance, source fidelity, and the new mood match M. Tooltip shows the numbers.
- "Why not recalled" reason codes with a visible split: character-level (never witnessed; faded below threshold; not cued this turn) versus system-level (cut for budget; extraction pending or failed; run stale; embedder unavailable). System-level rows get an amber "app" badge and a one-click fix (re-extract, raise budget).
- Actions: Pin (immune to decay, lives in primer, already `pinned`), Correct (user-authored row supersedes, `run_id` NULL), Forget (adds a permanent suppression; hard delete only on explicit request, since the design is append-only), Remind (adds a retold access: the user rehearses it for the character), View truth (shows base memory beside the character's recollection variant when they differ), History (recollection versions).
- Inspection must be read-only: opening the ledger or previewing a cue must not write accesses (otherwise looking changes memory). Provide "Ask Mira about X" as a dry-run recall that runs retrieval with side effects disabled and shows tier and reason codes.
- Reveal policy: ledger shows the character's private view to the user (they own the story), but the same data must never enter another character's prompt; keep the existing per-speaker generation guarantee.

### Gaps
- No user research found on whether showing decay bars increases or reduces trust versus a simple "remembers / vaguely remembers / forgot" label; recommend testing both.
- Replika dashboard and Nomi Mind Map details come from aggregator snippets (phase 1), not product docs.

## 6. Consolidation jobs: when to run, what to produce, how to prevent drift and embellishment, idle-time processing

### Takeaway
Consolidation should be an idle-time, append-only, provenance-cited job triggered by time skips and volume, never a recursive summary chain. The pattern with the best published support is Auto-Dreamer/Graphiti-style: sources stay intact, the consolidator reads a bounded working region, and its output is a new, cited, versioned entry that can be discarded. Validation must be mechanical because summaries hallucinate.

### Cited Findings
- SillyTavern warns summaries lose details or hallucinate; its Summarize is recursive and loss compounds; deleting summarised messages reverts the summary. — [ST Summarize docs](https://docs.sillytavern.app/extensions/summarize/); [Phase-1 note 02](D:/Kataki/docs/research/research_notes/Human like minds for Kataki/02_market_scan.md)
- Auto-Dreamer: consolidation every k sessions (k=10 best on ScienceWorld, robust for k in 1,5,20 on ALFWorld); the working region is new entries plus older entries retrieved recently; bounded tool use to inspect provenance sources; replacement set supersedes the region; a counterfactual ablation reward keeps banks from growing; untrained pipeline already shrinks banks 6-11x. — [Auto-Dreamer (arXiv HTML)](https://arxiv.org/html/2605.20616v1)
- Graphiti keeps raw episodes as a non-lossy store beneath derived entities and communities, and invalidates rather than deletes contradicted facts. — [Zep paper (arXiv HTML)](https://arxiv.org/html/2501.13956)
- A-MEM rewrites neighbouring notes when new ones arrive ("memory evolution") at 3 LLM calls per note. — [A-MEM (arXiv HTML)](https://arxiv.org/html/2502.12110)
- Retrieval-triggered updates carry error propagation risk; mitigations are versioning, confidence gating, anchor retention and periodic re-grounding. — [arXiv 2609.16053](https://arxiv.org/pdf/2609.16053) (unverified summary)
- Sleep-time compute pays off most when future queries are predictable from the context; identifying such contexts and irregular sleep windows are open problems. — [Sleep-time Compute (arXiv HTML)](https://arxiv.org/html/2504.13171v1)
- Letta's dreaming triggers on step count or context compaction; the Hermes proposal defers to a quiet period after user activity (default 60 min). — [Letta docs](https://docs.letta.com/guides/agents/architectures/sleeptime/); [hermes-agent issue 25309](https://github.com/NousResearch/hermes-agent/issues/25309)
- Kataki: extraction triggers are every N turns (default 5), scene break, time skip, extract-before-evict and manual; one `json_schema` call with a closed-set roster (handles like M31/E12) so small models cannot invent ids; the worker starts 3 s after a reply and cancels if the user sends a turn; a turn after a skip of a day or more first reads what came before; "reflection / dream cycles" and "summary roll-ups" are currently on the not-building list. — [Kataki spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md)
- A 3-4B CPU utility model runs about 10-20 tok/s per the repo spec, so a 600-token output job takes on the order of 30-60 s in idle time. — [Kataki spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md) (throughput figure; the 30-60 s is arithmetic)

### Inferences
- Schedule (build on existing triggers):
  1. Every 5 turns / scene end / skip / evict: extraction (exists, cheap default).
  2. Skip crossing a night: deterministic sleep replay, 0 LLM calls.
  3. Skip >= about 7 story-days, or >= 40 new memories for a knower since last dream, or scene-close of a major arc: "dream" job, one call per active character, run only when the user is idle (60 s idle, cancel on input as extraction already does). Outputs: habit entries, relationship lines, self-narrative refresh, optional duplicate-cluster merge proposals.
  4. Never: recursive summary of a summary; deleting or overwriting sources.
- Working region (Auto-Dreamer-style): memories new since last dream plus older memories with recent access rows, capped at about 30 items and about 3k input tokens; uses closed-set handles so the model cites `M31` not free text.
- Mechanical anti-drift gate before any consolidated row is accepted: (a) every statement carries at least one source handle from the region; (b) proper nouns and numbers in the output must appear in the cited sources or roster; (c) no new entities; (d) hard length caps (self 6 sentences, relationship 25 words); (e) written append-only with `run_id`, `source='inferred'` (fidelity -1.0), belief about 0.8, and superseding only prior consolidated rows, never raw memories; (f) failure is discarded with a visible warning chip, never silent (avoid the SillyTavern empty-box failure). Regenerate always from raw sources, not from the previous consolidation.
- Embellishment control: prompt "compress, do not explain; no causes, motives or feelings not present in the sources"; then optional validation by embedding overlap (each output sentence must have cosine >= a threshold to some source) as a cheap non-LLM entailment proxy. A reasoning-role model can be used for a second pass only in premium mode.
- Cost: cheap default has no dream job (habit/relationship/self blocks stay empty or come from the character card). Premium: per dream, about 3k input + 600 output tokens per active character; three characters is about 9-10k input and about 1.8k output tokens per skip. Local: the 30-60 s per character on CPU is idle-time. Cloud price depends on provider and was not sourced.

### Gaps
- No evaluation found of consolidation faithfulness in roleplay specifically; the mechanical gate is my design, and its false-reject rate is unknown.
- Auto-Dreamer results are on agent task environments with a trained consolidator; transfer to narrative memory with a prompted 9B model is unproven.
- No data on how many story-days between dreams feels right to users.

## 7. Recommended architecture for Kataki (delta on the existing M1 engine): schema, write path, retrieval formula, forgetting and distortion rules, consolidation, UI, cheap default versus premium

### Takeaway
Do not adopt an external memory system. Keep Kataki's engine (per-knower knowledge, ACT-R decay, tiers, effortful recall) and add five things that map to the missing human effects: append-only per-knower recollection variants (misremembering and reconsolidation), mood-congruent and interference terms, graded tip-of-the-tongue cues, a sleep-replay rule, and idle consolidation into three narrative kinds. The cheap default adds zero LLM calls per turn and about 40-80 output tokens per extracted memory; premium adds idle dream jobs and optional recall-time recounting.

### Cited Findings
- Justification sources for the pieces below are cited in Sections 1-6: ACT-R form in [Kataki spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md); gist/verbatim divergence [Fuzzy-trace theory](https://en.wikipedia.org/wiki/Fuzzy-trace_theory); flashbulb and arousal narrowing [Emotion and memory](https://en.wikipedia.org/wiki/Emotion_and_memory); mood-congruent retrieval in roleplay [Emotional RAG](https://arxiv.org/abs/2410.23041); retrieval-induced forgetting [RIF](https://en.wikipedia.org/wiki/Retrieval-induced_forgetting); partial recall in TOT [Tip of the tongue](https://en.wikipedia.org/wiki/Tip_of_the_tongue); misinformation and false memory [Misinformation effect](https://en.wikipedia.org/wiki/Misinformation_effect); reconsolidation and sleep [Memory consolidation](https://en.wikipedia.org/wiki/Memory_consolidation); consolidation with provenance [Auto-Dreamer](https://arxiv.org/html/2605.20616v1); non-lossy sources and invalidation [Zep](https://arxiv.org/html/2501.13956).
- Constraint that shapes everything: the repo's "nothing is mutated" rule, per-speaker generation, and cache-stable prompts (noise constant within a scene) — [Kataki spec](D:/Kataki/docs/specs/2026-09-18-m0-m1-design.md).

### Inferences

#### 7.1 What already exists and stays
Truth layer `memories` (event, fact, claim) with `detail` and `gist` written once; `knowledge` per knower with source, fidelity, belief; `accesses` capped once per scene; `edges`, `flags`; FTS5 + numpy cosine + RRF; tiers SHARP/HAZY; detail ratchet; effortful recall; contradiction rule (SHARP challenges, HAZY doubts, none accepts); zero LLM calls per turn; extraction about 1.2 calls per 5 turns; pins in the primer.

#### 7.2 Schema additions (append-only, all rows carry `run_id`, NULL for user-authored)
```sql
-- extraction-time fields (same call as today; schema-constrained, closed-set slots)
ALTER TABLE memories ADD COLUMN valence REAL;      -- -1..1 (arousal is importance/10)
ALTER TABLE memories ADD COLUMN alts   TEXT;       -- JSON: up to 2 gist-consistent drifts of PERIPHERAL slots
                                                   --   [{"slot":"place|time|witness|speaker","text":"..."}]
ALTER TABLE memories ADD COLUMN core_locked INTEGER NOT NULL DEFAULT 0;  -- never distorted

-- what a knower's memory has become (misremembering + reconsolidation), truth untouched
CREATE TABLE recollections(
  id INTEGER PRIMARY KEY,
  knower_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  memory_id INTEGER NOT NULL REFERENCES memories ON DELETE CASCADE,
  parent_id INTEGER REFERENCES recollections,     -- version chain
  basis TEXT NOT NULL CHECK(basis IN('alt','retelling','intrusion','source_swap','recount')),
  text TEXT NOT NULL,                             -- replaces detail/gist rendering for this knower
  story_time INTEGER NOT NULL,
  scene_id INTEGER, run_id INTEGER REFERENCES extraction_runs(id) ON DELETE CASCADE);
CREATE INDEX ix_rec ON recollections(knower_id, memory_id, id);

-- interference (retrieval-induced forgetting), scene-capped like accesses
CREATE TABLE suppressions(
  knower_id INTEGER NOT NULL, memory_id INTEGER NOT NULL, scene_id INTEGER NOT NULL,
  winner_id INTEGER NOT NULL, story_time INTEGER NOT NULL,
  PRIMARY KEY(knower_id, memory_id, scene_id)) WITHOUT ROWID;

-- consolidated layers (self, relationship, habit), cited and versioned
CREATE TABLE narratives(
  id INTEGER PRIMARY KEY, story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  knower_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN('self','relationship','habit')),
  subject_id INTEGER REFERENCES entities,         -- the other person (relationship) or NULL
  text TEXT NOT NULL, sources TEXT NOT NULL,      -- JSON list of memory ids (required, non-empty)
  cue TEXT,                                       -- keywords for habit triggering
  story_time INTEGER NOT NULL, supersedes_id INTEGER REFERENCES narratives,
  run_id INTEGER REFERENCES extraction_runs(id) ON DELETE CASCADE);
```
Add `sleep` to `accesses.kind` for replay rows. Reason codes live in `context_log` (existing) as a per-memory `why_not` field.

#### 7.3 Write path (cheap default)
1. Existing extraction call gains three fields per memory: `valence`, `alts` (max 2, peripheral slots only, must reuse roster handles for people/places), `core_locked` suggestion for oath-like or user-emphasised facts. Cost: about 40-80 extra output tokens per memory; no extra calls.
2. Retelling detection: when a character's new line restates a memory (already produces a `retold` access), the extractor also returns `deviates: true/false` and, if true, the character's wording. Write a `recollections` row (basis `retelling`) for that speaker. This is the reconsolidation event. Cap: at most one per (knower, memory, scene) via primary key logic, chain depth limit 3 (then further drift stops until a consolidation re-anchors it).
3. Telling another character: the listener's `knowledge` row is `told`; render text = teller's latest recollection if any, else truth (telephone effect, fidelity -0.5).
4. Lies accepted by a character (belief >= 0.9) can later become `intrusion` recollections when the true memory is HAZY and the claim is old (misinformation-effect rule below). No extra call.
5. Pinned or `core_locked` memories skip every distortion rule.

#### 7.4 Retrieval scoring (per knower, zero LLM calls)
Existing:
`A = B + 3.0*(imp/10) + 1.5*S + 1.0*G + F - 2.0*superseded + noise`
Proposed:
`A' = A + 0.5*M - 0.3*min(2, log2(1+n_supp)) + P` where
- `M = valence_mem * mood_now` (both in -1..1; mood_now from the speaker's current feeling flags via the existing FEELINGS mapping; 0 if unknown), scaled by importance/10 so only affect-laden memories are mood-biased (mood-congruent retrieval, arousal-gated).
- `n_supp` = suppression rows against this memory for this knower whose winner shares a cue (near-duplicate competitors); off in "faithful" mode.
- `P = +inf` if pinned; unchanged otherwise.
Tiers unchanged: SHARP if `A_detail >= -2.0`, HAZY if `A_all >= -4.0`, else gone. `B` keeps d = 0.5 (user slider 0.3-0.8, renamed in UI "how vividly people remember"). New access kind `sleep` weight 0.25, sharp=false.

Render (per memory, per scene, deterministic via `hash01(knower, memory, scene, tag)`):
- SHARP: latest recollection text if any, else `detail`.
- HAZY: `gist` plus partial cue line when pressed (7.5), plus optional distortion (7.5).
- Gone: nothing, but eligible for a "feels familiar" hint only if `S >= 0.8` (feeling of knowing; optional, premium/dreamlike).

#### 7.5 Forgetting and distortion rules (all deterministic, all toggleable)
- D0 omission (exists): detail dropped at HAZY; ratchet prevents resurrection.
- Partial cues (graded tip-of-the-tongue): when a HAZY memory is injected on two consecutive turns and the effortful roll fails, render up to two true partial cues built by code: initial letter of the linked person/place entity, the place name or "somewhere by water" from place tags, the emotion word, coarse "years ago". Success still restores detail as today. Zero calls.
- D1 source amnesia: for `told`/`overheard` memories with `A_detail < -3.0`, render without the teller ("someone told me") with probability 0.5; belief unchanged. Never for `witnessed`.
- D2 alt drift: only in HAZY, only if not `core_locked`/pinned, once per (knower, memory, scene): `p = min(0.4, 0.10 + 0.30*(1 - imp/10))`; when it fires render `gist` with the chosen alt slot swapped and log a `recollections` row (basis `alt`) so it is stable thereafter for that knower. Confidence/belief is not lowered (flashbulb pattern: vivid and wrong). In "faithful" mode p = 0.
- D3 intrusion (misinformation): if a lie was accepted (belief >= 0.9) and the contradicted true memory is HAZY and the claim is more than 7 story-days old, roll p = 0.25 per scene at cue time; on success write an `intrusion` recollection that merges the claim into the memory. Mirrors delay + low-confidence susceptibility.
- D4 interference: as in 7.4; competitors write `suppressions` when a sibling wins the cue.
- D5 arousal narrowing: extractor marks the central slot; at HAZY, peripheral slots drop first for importance >= 7 (core stays), for importance <= 3 everything blurs equally. Implementation is prompt-side (`gist` written that way), no runtime cost.
- Reconsolidation via retelling (7.3.2) is the only path by which a character's version changes in a lasting way, plus D2/D3 when they fire once.
- Premium D6 recount: at the first HAZY injection per memory per scene where the user presses (2nd consecutive), one utility call rewrites `gist` in the character's voice given current mood and relationship line, with the constraint "you may forget or blur; you may not add facts", stored as a `recount` recollection. Cost: about 300 tokens per pressed hazy memory; expect a few per session.

Never-lose guarantee: memories with `A >= SHARP_AT` must reach the prompt unless the user-visible token budget cut them, in which case the ledger shows a "budget" system badge (7.8).

#### 7.6 Consolidation schedule
As in Section 6. Cheap default: extraction only plus sleep replay (0 calls). Premium: dream jobs per active character at large skips, cited and gated (Section 6 gate), producing `narratives` rows; self and relationship lines injected in the speaker's tail (about 100 + 3x40 tokens), habits injected on cue with SillyTavern-style sticky (2 turns) and cooldown (10 turns). Cluster merge stays a user-visible chip (existing "merge?" behaviour), never automatic.

#### 7.7 Group scenes
Unchanged hard filter through `knowledge`; per-knower `recollections` mean each witness owns a version; retelling propagates versions (telephone effect); narrator has no episodic memory; only the current speaker's memories, narratives and cues enter the prompt. Cost per turn identical to 1:1 (retrieval runs for one speaker); write cost scales with N witnesses only in `knowledge` rows.

#### 7.8 UI (ledger)
As in Section 5, plus: tier groups, source badges, why-recalled chips (S, G, B, importance, source, M), why-not codes with character vs app badge, truth-vs-version diff, Pin / Correct / Forget / Remind / History, read-only "Ask about X" dry run, a three-position "Memory style" control mapping to presets: Faithful (d = 0.3, no distortion, no interference), Human (d = 0.5, D1-D3 on, low rates), Dreamlike (d = 0.8, D4 on, higher rates). Nothing changes stored data when the control moves.

#### 7.9 Cost and latency summary
| Mode | Extra LLM calls per turn | Background | Storage per 10k memories | Latency added | Fully local |
|---|---|---|---|---|---|
| Cheap default (M1 + 7.2-7.5 D0-D5, sleep replay) | 0 | existing extraction (1.2 calls / 5 turns) with +40-80 output tokens per memory | +alts/valence text about 2 MB, recollections/suppressions rows small, vectors 15 MB at 384-d | retrieval unchanged (ms-scale numpy + SQL) | yes |
| Premium local | 0 | + dream job per active character at big skips (about 3k in + 600 out tokens each; about 30-60 s on CPU 3-4B in idle time) | + narratives (KB) | 0 per turn; dream cancels on user input | yes (quality depends on the local model) |
| Premium cloud (HF or API) | 0 (+ about 1 call per pressed hazy memory for D6, about 300 tokens) | dream job on a stronger reasoning model | same | + one round trip on pressed hazy turns only | partly (calls leave the machine); price not sourced, state call count and tokens before running per the paid-API rule |

#### 7.10 Evaluation to build (because public benchmarks do not test this)
Extend `engine/evals` with: (1) decay probes: expected tier at 1 day / 1 month / 6 years, retold vs not; (2) system-loss probe: count SHARP memories dropped for system reasons = 0 across long runs; (3) leakage probe: unwitnessed memory never appears in another knower's prompt (already tested manually; automate at N=3+ characters); (4) distortion probe: alt text only touches allowed slots, core handles and belief unchanged, pinned never distorted; (5) consolidation gate probe: reject outputs with novel proper nouns/numbers, no-source sentences; (6) abstention probe borrowed from LongMemEval: a forgotten memory must not be confabulated (gone tier yields "I don't remember"); (7) tenure probe: replay a 500-turn synthetic story and compare cheap vs premium at 50, 200, 500 turns (the tenure-crossover idea).

#### 7.11 Build order (thin slices, show-first)
1. Reason codes + read-only dry-run + budget badge (pure UI/engine reads of existing data).
2. Partial cues (zero schema change), sleep replay, mood term M.
3. Extraction fields (`valence`, `alts`, `core_locked`) + `recollections` + retelling reconsolidation + D1/D2.
4. `narratives` and the dream job with the gate (premium).
5. Interference and D3/D6 last, behind Dreamlike.

### Gaps
- All thresholds and probabilities in 7.4-7.5 (0.5 mood weight, p_distort formula, 7-day and 0.25 intrusion values, chain depth 3, habit repeat 4, sleep replay weight 0.25) are design defaults with no empirical source; they need tuning against the eval in 7.10 and user testing.
- Interaction of the new terms with the repo's existing calibration tests (worked-example table) not run; A' must be regression-checked because it changes tier boundaries for affect-laden memories.
- Whether the 8B/9B local model can reliably emit `alts` restricted to peripheral slots and honest `deviates` flags was not tested; Kataki's own eval log shows small models otherwise wrote gists as specific as details until the prompt and schema were tightened, so expect iteration.
- Did not check `context.py`/`retrieve.py` internals in depth for where `why_not` reason codes would attach; needs a code read before estimating effort.
- Model licence terms for any bundled embedder (e.g. EmbeddingGemma's gated terms) were noted only as a fetched fact and not analysed.
