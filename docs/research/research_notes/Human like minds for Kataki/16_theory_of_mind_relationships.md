# Theory of mind and relationship dynamics for LLM roleplay characters (Kataki), including group dynamics

Scope note: research run 2026-09-29. Web search budget ran out partway (200 of 200), so some planned lookups (jealousy in agents, Dunbar friendship decay, Mikulincer/Shaver primary papers, Sotopia detail) were never executed and appear under Gaps. Many arXiv pages returned abstract-level summaries only; numeric results are given only where a fetch actually returned them. Anything under "Inferences" is my own reasoning or design suggestion, not a sourced fact. Cost and latency numbers for Kataki are my estimates (assumption: 7-14B Q4 model on an 8 GB GPU generating very roughly 30-60 tokens per second, cloud replies about 1-2 s for 150 tokens; measure against `docs/images/rules-and-gotchas.md`-style protocol before trusting). Phase-1 notes 01 (social cognition, social penetration, attachment) and 03 (Generative Agents, Humanoid Agents, PIANO, Inner Thoughts, Chain-of-Emotion, sleep-time consolidation) are referenced rather than repeated.

## 1. Theory of mind in LLMs: what the benchmarks show

### Takeaway
LLMs pass many textbook false-belief tests but fail on stress tests: multi-party conversations with people entering and leaving (FANToM), psychological/attitude questions (OpenToM), white lies (TactfulToM), and using mental states to predict dialogue (DialToM). The consistent lesson for Kataki is that the hard part is deciding who knows what and holding it consistently, which an app can track in code, not something to leave to the model's implicit reasoning.

### Cited Findings
- FANToM (EMNLP 2023): 10,000 questions over 256 multiparty conversations in which characters enter and leave, creating information asymmetry; state-of-the-art LLMs "perform significantly worse than humans even with chain-of-thought reasoning or fine-tuning"; it asks several question formats needing the same reasoning to expose "illusory" ToM (right answer in one format, wrong in another). — [arXiv 2310.15421](https://arxiv.org/abs/2310.15421)
- FANToM secondary summaries report a large human-model gap (one summary says about 70%, not verified), lower scores with longer conversation context than with short focused context, and low cross-format consistency. — [alphaXiv/emergentmind search summaries of FANToM](https://www.emergentmind.com/papers/2310.15421)
- OpenToM (ACL 2024): longer stories with characters who have explicit personality traits; LLMs are good at modelling mental states about the physical world but fall short on the psychological world (attitudes, emotions). — [arXiv 2402.06044](https://arxiv.org/abs/2402.06044)
- TactfulToM: a human-in-the-loop benchmark of conversations with information asymmetry built around white lies told to spare feelings; state-of-the-art models perform substantially below humans. — [arXiv 2509.17054](https://arxiv.org/abs/2509.17054)
- OmniToM (2026): requires explicit belief structures for every actor in a narrative; reports belief-labeling accuracy up to 85.95% but information extraction peaking at 57.69%, and describes an actor-specific "belief-tracking bottleneck": knowledge-access and representational decisions (who could have known this fact) are where models fail. — [arXiv 2605.26322](https://arxiv.org/abs/2605.26322)
- DialToM (2026): benchmark for forecasting dialogue from characters' mental states; models "do not consistently leverage mental state information" even when it is supplied, and land well below human accuracy. — [arXiv 2604.20443](https://arxiv.org/pdf/2604.20443) (abstract-level fetch only)
- PDDL-Mind (2026): argues LLMs are "capable on belief reasoning with reliable state tracking", i.e. an external formal state representation of who knows what fixes much of the failure; tested with GPT-4o, Claude Sonnet 4.5 and other models. — [arXiv 2604.17819](https://arxiv.org/pdf/2604.17819) (no numbers retrieved)
- Concordia (DeepMind) uses a Game Master that receives agents' actions and translates them into observations for each agent, so what each agent knows is controlled by the engine, not inferred by the agent. — [Concordia GitHub](https://github.com/google-deepmind/concordia); [Concordia paper](https://arxiv.org/abs/2312.03664)
- Evidence that ToM-style capability is uneven across model families and unreliable for social reasoning: ToMAgent found that "simply prompting models to generate mental states between dialogue turns already provides significant benefit" on Sotopia, using five dimensions (beliefs, desires, intentions, emotions, knowledge). — [arXiv 2509.22887](https://arxiv.org/html/2509.22887v1)

### Inferences
- Kataki knows exactly who was in the room, who was whispered to, what was flagged secret, and what happened during a time skip. It can therefore build each character's "known facts" set deterministically. This removes the bottleneck OmniToM identifies and matches the Concordia Game Master pattern, at zero LLM cost.
- FANToM's setup (characters joining and leaving mid-conversation) is Kataki's mid-scene join feature. Its findings (longer context hurts, inconsistency across formats) argue for feeding each character a short, pre-filtered context instead of the full transcript plus a "pretend you don't know X" instruction.
- OpenToM and DialToM suggest attitudes and feelings should be stored as explicit state and turned into behavioural directives, not left for the model to infer from history each turn.
- TactfulToM plus phase-1 note 01 (DePaulo: lies to close partners are more altruistic) means white-lie behaviour will need explicit prompting: give the character its private truth and the reason it might soften it.

### Gaps
- I did not fetch primary numbers for ToMi, Hi-ToM or BigToM (only the SimToM paper's own table, section 2, and a mention of Hi-ToM orders in section 2). Their descriptions here are limited to what other cited papers say.
- No 2026 result found that evaluates ToM prompting or belief tables on 7-14B local models specifically in multiparty roleplay.
- "Learning Dynamic Belief Graphs for Theory-of-mind Reasoning" (arXiv 2603.20170) exists but the PDF returned no readable results; I cannot state its method's gains or model sizes. — [arXiv 2603.20170](https://arxiv.org/pdf/2603.20170)

## 2. Does explicit belief tracking or perspective-taking prompting help small models?

### Takeaway
Yes for cheap forms, with caveats. SimToM (filter context to what the character knows, then answer) gave large gains on Llama-2-7B and 13B and GPT-3.5, while chain-of-thought sometimes hurt small models. ThoughtTracing-style hypothesis tracking is stronger but multiplies calls. Training small models on ToM data (RL) produces benchmark gains that fail to generalize. The best small-model bet is to move the "filter to what they know" step out of the model and into code.

### Cited Findings
- SimToM (ACL 2024): two-stage prompting (Stage 1: keep only events the character is aware of; Stage 2: answer from that perspective), no training, two inference passes per question. — [ACL Anthology](https://aclanthology.org/2024.acl-long.451/); [arXiv 2311.10227](https://arxiv.org/abs/2311.10227)
- SimToM table (zero-shot / CoT / SimToM accuracy on false-belief questions). BigToM: Llama2-7B 47.5 / 31.5 / 70.5; Llama2-13B 41.25 / 52.25 / 61.75; GPT-3.5-Turbo 41.0 / 56.25 / 70.5; GPT-4 89.0 / 93.25 / 92.0. ToMi: Llama2-7B 28.25 / 24.0 / 40.0; Llama2-13B 39.25 / 16.5 / 35.5; GPT-3.5 67.25 / 34.0 / 81.0; GPT-4 25.5 / 74.25 / 87.75. So SimToM helped 7B on both sets, was roughly neutral or slightly negative for 13B ToMi and GPT-4 BigToM, and CoT lowered small-model accuracy in several cells. — [arXiv HTML of 2311.10227 via fetch](https://arxiv.org/html/2311.10227). Caveat: these are 2023 Llama-2 models, older than what Kataki will run.
- ThoughtTracing (2025): inference-time algorithm inspired by Bayesian ToM and sequential Monte Carlo; at each step the LLM generates several natural-language hypotheses about the target agent's mental states and weights them by how well they explain the observed actions; reports significant improvements over baselines across ToM benchmarks and notes distinctive behaviour of reasoning models (o3, R1) on ToM. — [arXiv 2502.11881](https://arxiv.org/abs/2502.11881); [summary](https://arxiv.org/html/2502.11881). Numeric results, hypothesis counts and model sizes were not retrievable.
- Small LLMs and RL (Qwen2.5-7B-Instruct trained on HiToM, ExploreToM, FANToM): in-distribution gains of +65 (FANToM), +35 (HiToM), +22 (ExploreToM) points, but OpenToM stayed at 56.9-61.8% versus 59.2% CoT baseline, FANToM list tasks reached only 45.9% versus 43%, and a model trained on orders 1-3 scored 94.2% on unseen fourth-order HiToM while the baseline fell from 65.8% to 34.2% across orders, which the authors read as exploiting dataset artifacts. — [arXiv 2507.15788](https://arxiv.org/html/2507.15788)
- Conflicting claim: another RL paper (ToM-RL) is summarised as finding reasoning collapse below 3B but genuine transferable belief tracking at 7B, beating GPT-4o. — [search listing of ToM-RL](https://lacuna.tiptreesystems.com/work/tom-rl-reinforcement-learning-unlocks-theory-of-mind-in-small-llms/wrk_94b860d5c91826bf8a50e1e810a1ccc7); contradicted in spirit by [arXiv 2507.15788](https://arxiv.org/html/2507.15788)
- ToMAgent (Qwen2.5-3B/7B fine-tuned on trajectories with mental states as intermediate step, five dimensions, lookahead to select trajectories): Sotopia gains of 16.8% (3B) and 6.6% (7B) over baseline, data generation under $5, about 4 hours of training on one L40S; explicit mental-state generation alone helps, adding lookahead simulation helps more. — [arXiv 2509.22887](https://arxiv.org/html/2509.22887v1)
- A search summary states most ToM strategies are tested on models above 7B and may not work under 7B because of weaker instruction following. — [search summary of arXiv 2505.00026 context](https://arxiv.org/pdf/2505.00026) (weak source)
- PDDL-Mind and OmniToM findings on external state and belief structures: see section 1.

### Inferences
- The SimToM idea maps to Kataki as "code filter + one call": Stage 1 (who knows what) is deterministic from scene attendance and secret flags, so only Stage 2 costs a call, which is the reply the app was making anyway. SimToM's 2x prompt overhead disappears.
- CoT-style long reasoning is a poor default for 7-13B ToM, consistent with phase-1 note 03's warning about reasoning-induced style drift. Keep hidden thought short and structured.
- Fine-tuning a ToM model is not worth it for Kataki: gains do not generalize (2507.15788), and Kataki cannot ship per-user training on an 8 GB GPU.
- ThoughtTracing is a candidate for a premium, event-triggered use (secret about to surface, accusation, lie detection) on a stronger model, 3-5 extra calls each time (estimate: hypotheses plus a weighting call).
- Nested belief (what A thinks B thinks C knows) degrades with order (baseline 65.8% to 34.2% across orders 1-4 above), so store first-order beliefs plus at most one explicit second-order slot.

### Gaps
- No direct measurement of SimToM or ThoughtTracing on 2026-era 7-14B models (Qwen3, Gemma 3/4, Llama 3.x, Mistral). SimToM numbers above are Llama-2 era.
- ThoughtTracing cost and numbers unavailable from fetches.
- The conflict between ToM-RL and "Small LLMs do not learn" was not adjudicated by reading both papers in full.

## 3. Modelling the user: inferred mood, intentions, preferences, privacy

### Takeaway
Keep the character's view of the user as structured, editable, per-character state with confidence and provenance, updated mostly by cheap signals plus the appraisal call. Treat it as belief (possibly wrong), not truth. Privacy risk grows with inference, so local-first storage, a visible "what they know about you" page and cloud-routing redaction are needed.

### Cited Findings
- ToMAgent's mental-state schema (beliefs, desires, intentions, emotions, knowledge) is a working template for what to infer about a partner before replying. — [arXiv 2509.22887](https://arxiv.org/html/2509.22887v1)
- Inner Thoughts (CHI 2025): a covert continuous thought stream with intrinsic motivation to speak, preferred over 82% of the time versus a persona+next-speaker baseline. Already in phase-1 note 03. — [arXiv 2501.00383](https://arxiv.org/abs/2501.00383)
- Value similarity between LLM agents predicts higher mutual trust and interpersonal closeness after a dialogue (Scientific Reports 2025; English and Japanese). — [arXiv 2507.11979](https://arxiv.org/abs/2507.11979)
- Chain-of-Emotion appraisal used two LLM calls per turn and improved perceived naturalness in a 30-participant study (phase-1 note 03). — [PMC11086867](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11086867/)
- Privacy: AI companions can make more inferences about individuals over time, and users' wish to confide leads to more intimate inferences; anthropomorphic systems can lower privacy concerns and raise disclosure; deletion may not cover all data; Replika faced scrutiny over conversation data being used to train licensed models. — [FPF](https://fpf.org/blog/personality-vs-personalization-in-ai-systems-specific-uses-and-concrete-risks-part-2/); [MIT Technology Review](https://www.technologyreview.com/2025/11/24/1128051/the-state-of-ai-chatbot-companions-and-the-future-of-our-privacy/); [BEUC report 2026](https://www.beuc.eu/sites/default/files/publications/BEUC-X-2026-049_Risks_and_Rights_in_Artificial_Companionship.pdf); [arXiv 2601.10754](https://arxiv.org/pdf/2601.10754)
- Companion chatbots can create emotional dependence in extended interactions, which allows continuous manipulation. — [All Tech Is Human summary](https://alltechishuman.org/all-tech-is-human-blog/what-are-the-most-important-issues-with-ai-companions-six-key-themes-emerged-from-our-community)

### Inferences
- Schema idea: `user_model` (global, ground-truth-ish, owned by the user: name, stated likes/dislikes, boundaries, disclosed facts with timestamps) plus one `view` per character (what that character believes about the user: `believed_mood {valence, arousal, label, confidence, at}`, `believed_intent`, `believed_facts[] with source`). Views can be wrong or stale. Perceptiveness/empathy traits set how fast the belief moves (smoothing constant), which yields controlled misreading, the "limited theory of mind" from note 01.
- User mood can be estimated at 0 calls by heuristics (message length change, punctuation, response latency, lexicon), refined by the appraisal call when it runs. Use an enum plus intensity.
- Because Kataki can route a character to a cloud provider, redact or drop sensitive categories (health, sexuality, finances, real identity) from any character's prompt when that character's model is cloud-hosted, unless the user marks it allowed. This is a design suggestion; the cited privacy sources only establish the risk.
- Ship a "What Mara knows about you" screen with per-fact delete, source message link and cloud-sent indicator.
- Avoid engagement-optimising uses of the user model (guilt, dependency); see section 7.

### Gaps
- No peer-reviewed schema for user models in roleplay found; the design above is mine.
- No source on how accurately small local models infer user mood from short chat messages.
- Legal specifics (GDPR treatment of inferred data) not researched.

## 4. Relationship state: dimensions, stages, events, and game references

### Takeaway
Use a small set of directed numeric tracks (closeness, trust, respect, attraction, resentment, dominance/power) plus a derived stage from social penetration theory, updated by a closed vocabulary of relationship events with fixed magnitudes, per-scene caps and diminishing returns. Games give tested patterns: Sims-style decaying tracks with threshold labels, Crusader Kings opinion ledgers of timed modifiers, Persona hidden point tallies, Dwarf Fortress personality-driven grudges.

### Cited Findings
- Humanoid Agents: four relationship-closeness levels alongside needs and seven emotions; conversation adapts to them. — [ACL Anthology](https://aclanthology.org/2023.emnlp-demo.15/)
- Social penetration theory: layered disclosure, stages orientation, exploratory affective, affective, stable; reciprocity of disclosure; unreciprocated disclosure stalls; Aron et al. 1997 closeness procedure (already in note 01). — [Wikipedia summary](https://en.wikipedia.org/wiki/Social_penetration_theory); [Rutgers summary](https://sites.comminfo.rutgers.edu/kgreene/wp-content/uploads/sites/28/2018/02/ACGreene-SPT.pdf)
- Interpersonal circumplex: agency/dominance by communion/warmth as the two basic axes of interpersonal behaviour. — [Gurtman 2009](https://compass.onlinelibrary.wiley.com/doi/10.1111/j.1751-9004.2009.00172.x)
- The Sims 4: two separate tracks per pair (Friendship and Romance); statuses from bar fill: Acquaintance 0-39%, Friend 40-59%, Good Friend 60-79%, Best Friends 80-100%; bars decay without interaction; a search summary reports unpresent Sims decay about 2 points per day, and that rebuilding is quicker because of familiarity. — [Sims Wiki: Relationship](https://sims.fandom.com/wiki/Relationship); [Carl's Sims 4 guide](https://www.carls-sims-4-guide.com/relationships/); [EA forum thread on decay](https://forums.ea.com/idea/the-sims-4-bug-reports-en/romantic-relationships-decaybecome-negative-fast-with-no-interaction/4947168)
- Crusader Kings: opinion is a stack of modifiers, which can be temporary or permanent, unlimited in number though only the first 10 are shown in the UI; in CK2 modifiers had decay timers (a forum-reported example: a -100 modifier for executing a child decaying over 100 years). — [CK3 Wiki: Modifiers](https://ck3.paradoxwikis.com/Modifiers); [Paradox forum thread](https://forum.paradoxplaza.com/forum/threads/the-gameplay-focus-on-stacking-stats-and-modifiers-runs-counter-to-the-core-design-philosophy-of-crusader-kings-3.1735002/page-3). The CK2 example is a forum claim, not official documentation.
- Persona social links: dialogue choices grant different amounts of progress toward the next rank via a covert point tally; carrying the matching arcana multiplies gains (a "+10" event showing 15 with a 1.5 multiplier); availability is gated by schedules. Persona 3 reversed links on bad choices or neglect; Persona 4 relaxed it; Persona 5 removed reversals entirely so players can express themselves freely, at the cost of reducing relationships to transactional unlocks. — [Game Developer comparison](https://www.gamedeveloper.com/design/same-but-different---comparing-the-social-link-system-in-persona-3-4-5); [PSNProfiles guide](https://psnprofiles.com/guide/9938-persona-5-royal-confidants-guide)
- Dwarf Fortress: personality facets valued 0-100; where two dwarves' relationship-relevant facets differ strongly (above 60 in one and below 40 in the other) it contributes to grudge formation; memories move short-term to long-term to core and can permanently change facets, with a stated 1-in-3 chance on recall of promotion from long-term to core. — [DF Wiki: Personality facet](https://dwarffortresswiki.org/index.php/DF2014:Personality_facet); [DF Wiki: Memory](https://dwarffortresswiki.org/index.php/DF2014:Memory_(thought))
- LLM social sims model relationships as data: AgentSociety agents keep social networks (family, friends, colleagues) with relationship strengths, plus emotions and needs; 10,000+ agents and about 5 million interactions. — [arXiv 2502.08691](https://arxiv.org/abs/2502.08691)
- PIANO/Project Sid: sentiment-inference modules gave 0.807 correlation with 5+ observers; without social modules relationships stayed neutral and roles did not persist; performance only with GPT-4o (phase-1 note 03). — [arXiv 2411.00114](https://arxiv.org/html/2411.00114v1)

### Inferences
- Recommended tracks (directed, A toward B, each -100..100 unless noted): `closeness` (0..100), `trust`, `respect`, `attraction` (optional, content-setting gated), `resentment` (0..100, mostly derived from the grudge ledger), `dominance` (perceived power of B over A), plus `familiarity` (0..100, monotone, counts disclosure and shared history) and `disclosure_depth` reached per side (SPT layer 1-4). Sims-style thresholds turn numbers into stage labels; use hysteresis of about 5 points so a stage does not flicker.
- Event vocabulary (closed, about 20): `kindness`, `support_given`, `support_ignored`, `vulnerable_disclosure`, `disclosure_reciprocated`, `disclosure_unreciprocated`, `shared_joy`, `compliment`, `teasing_ok`, `teasing_hurt`, `insult`, `dismissal`, `promise_kept`, `promise_broken`, `secret_kept`, `secret_betrayed`, `lie_discovered`, `boundary_crossed`, `apology_sincere`, `apology_hollow`, `amends_made`, `favouritism_shown`, `neglect_gap`, `help_refused`. The LLM only picks type, target and intensity 1-3; code applies fixed deltas from a table. Closed-enum classification is the kind of task small models do best (inference, not sourced).
- Update shape: positive deltas are scaled by diminishing returns (higher closeness gains less) and capped per scene (for example +8 closeness) so no relationship jumps stages in one scene; negative trust events are larger than positive ones. The asymmetry that trust is built slowly and lost quickly is background knowledge I did not source in this pass.
- Persona's lesson: hard reversals frustrate players who want expressive freedom; offer a "relationship realism" dial (Off, Gentle, Realistic, Harsh) that scales negative deltas and neglect decay, with Gentle as default and a floor so a long-established relationship cannot fall below "acquaintance" from neglect alone.
- Dwarf Fortress lesson: derive baseline friction from trait distance (for example values or dominance mismatch) so some pairs start with a small negative opinion modifier without any event. Value-similarity results (2507.11979) back using shared values to seed initial trust and closeness.
- Do not show raw numbers to the model (see section 9); do show them to the user as words plus a soft bar.

### Gaps
- No primary CK3 design documentation on decay was found; the CK2 example is community-sourced. No GDC talks retrieved for The Sims relationship design or Dwarf Fortress.
- No study found validating any numeric relationship model against human judgement of believability in LLM roleplay.
- Persona point values per choice are only summarised, not tabulated.

## 5. Grudges, forgiveness, jealousy, loyalty: representation and decay

### Takeaway
Represent them as timed, sourced opinion modifiers in a ledger rather than a single number: each has a cause, magnitude, decay rule and a resolved flag. A grudge is an unresolved negative modifier that barely decays until repair; forgiveness is a repair event that flips it to fast decay, scaled by a forgiveness trait. Jealousy is best modelled as a short-lived, attention-share-triggered meter. LLMs tend to be too forgiving and too nice, so grudges must be enforced by state and directives.

### Cited Findings
- LLMs fail most on traits opposed to safety training ("Deceitful", "Manipulative") and substitute "superficial aggression" for nuanced malevolence; fidelity declines monotonically as character morality decreases; highly safety-aligned models do particularly poorly; general chatbot ability is a poor predictor. — [arXiv 2511.04962](https://arxiv.org/abs/2511.04962) (ACL Findings 2026: [ACL Anthology](https://aclanthology.org/2026.findings-acl.282/))
- Generative Agents documented excessive cooperativeness (rarely refusing suggestions) and norm erosion as memory grew (phase-1 note 03). — [ar5iv 2304.03442](https://ar5iv.labs.arxiv.org/html/2304.03442)
- Crusader Kings-style modifiers can be temporary or permanent; Dwarf Fortress memories can permanently alter personality facets; Persona 3 reversed links after neglect or bad choices and then relaxed this (section 4).
- Sims relationships rebuild faster than they were built because of familiarity (section 4). — [Sims Wiki](https://sims.fandom.com/wiki/Relationship)
- Gross's process model: suppressing emotion reduces expression but not experience, impairs memory, and is associated with worse interpersonal functioning (phase-1 note 01). — [Gross 2002](https://onlinelibrary.wiley.com/doi/10.1017/S0048577201393198)

### Inferences
- Ledger entry: `{id, target, dim, value, born_clock, kind: decay|sticky|permanent, half_life_days, resolved: bool, cause: <=15 words, source_msg, witnesses[]}`. Effective opinion on a dimension = base + sum(value x decay(age)), with decay = 0.5^(age/half_life) for `decay`, held at full value for `sticky`, constant for `permanent`. Cap ledger to about 30 entries; merge the oldest small ones into the base (Dwarf Fortress promotion in reverse: fold into personality baseline).
- Grudge = `sticky` negative entry (from `secret_betrayed`, `promise_broken`, `insult`, `lie_discovered`, `boundary_crossed`), floored at 40% of original strength until resolved. Repair events: `apology_sincere` (requires acknowledgement of the cause; the classifier separates it from `apology_hollow`), `amends_made`, time plus a third-party mediator in group scenes. On repair: entry flips to `decay` with a 20-60 day half-life times a forgiveness multiplier (0.5 + forgiveness trait), and residual `trust_cap` stays lowered so trust recovers slowly. A second repeat offence of the same cause doubles the value and halves forgiveness for that pair.
- Grudge retrieval: unresolved grudges are added to the character's episodic memory with high importance so the character can bring them back up unprompted ("callbacks"), which is the visible payoff.
- Loyalty: not a separate track; derive as `min(closeness, trust) + shared_history bonus`, tested when the user and a third character conflict (character picks a side by loyalty, not by who spoke last).
- Jealousy (my design; no source found): `J(i about target t)` rises when attention share to a rival rises. Compute the exponentially weighted share of the user's addressed messages per character over the last N turns (0 LLM calls). Trigger when a rival's share exceeds i's by a margin, i's closeness to the user exceeds a threshold, and i is present or will hear of it. Scale by a `possessiveness` trait. J decays with a half-life of about 1-2 days, and the same formula works character-to-character (jealous of the user's attention, or of a rival's closeness to a third character). Expression depends on attachment (section 7).
- Counter LLM niceness: state-derived directives ("You have not forgiven X for Y. Be civil but do not warm up unless X addresses it") beat trait adjectives; consider a per-character model choice, since safety-heavy models are worse at Deceitful/Manipulative characters.
- Quality control for forgiveness: a hollow apology should fail; keep the sincere/hollow tags in the event enum so the classifier, not the reply model, decides.

### Gaps
- No search on computational jealousy in LLM agents or NPC systems completed (budget exhausted); the jealousy rule is unsourced design.
- No empirical source on human grudge half-lives; the half-life ranges above are tuning defaults.
- Villain-roleplay evidence is one benchmark (arXiv 2511.04962); I did not retrieve its model-by-model numbers.

## 6. Group dynamics: character-to-character relationships, alliances, gossip, and who talks to whom

### Takeaway
Treat group scenes as a directed graph with the same relationship schema on every edge, a per-fact belief table that controls information flow (including gossip), and a cheap deterministic speaker-selection score. Literature supports relationship-biased reply policies, adjacency-pair plus internal-state self-selection, and reply-chain decay; full multi-agent societies are too expensive for one local GPU, but their social modules (PIANO) show that without them relationships stay neutral and roles do not form.

### Cited Findings
- Murder Mystery Agents ("Who Speaks Next?"): next-speaker selection from adjacency pairs plus a self-selection mechanism that uses agents' internal states significantly reduced conversation breakdowns and improved information exchange and reasoning. — [arXiv 2412.04937](https://arxiv.org/abs/2412.04937)
- HUMA: LLM group-chat participant with a router (decides when to speak), an action agent and reflection, an event-driven architecture and simulated response time; in a 97-participant study in four-person chats, participants classified it as human at near-chance rates. — [arXiv 2511.17315](https://arxiv.org/abs/2511.17315)
- Bounded Autonomy (live multiplayer games): probabilistic reply-chain decay to manage conversation flow, embedding-based action grounding, and "whisper" steering that lets a player nudge a character without overriding it; a relationship-biased reply policy is used. — [arXiv 2604.04703](https://arxiv.org/abs/2604.04703)
- Search summary: a role-play prompt for dynamic speaker selection succeeds more often than task-based selection, and addressee recognition is a known weakness of LLMs in multi-party conversation. — [arXiv 2409.18602](https://arxiv.org/pdf/2409.18602); [Springer chapter on role-playing for multi-party conversations](https://link.springer.com/chapter/10.1007/978-981-97-5663-6_18)
- Inner Thoughts models intrinsic motivation to speak (phase-1 note 03). — [arXiv 2501.00383](https://arxiv.org/abs/2501.00383)
- Concordia: Game Master mediates observations; agents have long-term and working memory; the `QuestionOfRecentMemories` component lets an agent ask itself "What kind of person am I?" or "What would a person like me do in this situation?" at one LLM call per query; the README does not document dedicated relationship-tracking or emotion components, suggesting they are user-composed. — [Concordia components README](https://github.com/google-deepmind/concordia/blob/main/concordia/components/README.md); [Concordia GitHub](https://github.com/google-deepmind/concordia)
- PIANO/Project Sid social modules and the finding that relationships stayed neutral and roles did not persist without them (section 4). — [arXiv 2411.00114](https://arxiv.org/html/2411.00114v1)
- AgentSociety: relationship strengths in agent social networks, emotions and needs shaping message content; reproduces opinion polarization and responses to shocks. — [arXiv 2502.08691](https://arxiv.org/abs/2502.08691)
- Information spread: LLM-agent rumour-spreading simulations exist (Facebook-derived networks), as do studies of emotional contagion among LLM agents and a vision paper on gossip protocols noting problems of semantic relevance, staleness and consistency; I could read only titles and summaries. — [arXiv 2502.01450](https://arxiv.org/pdf/2502.01450); [arXiv 2607.25140](https://arxiv.org/pdf/2607.25140); [arXiv 2508.01531](https://arxiv.org/html/2508.01531v1)
- Generative Agents information diffusion (party invitation spreading) is in the original paper; not re-verified here (phase-1 note 03 cites the same paper). — [ar5iv 2304.03442](https://ar5iv.labs.arxiv.org/html/2304.03442)

### Inferences
- Edge store: sparse directed edges `(A -> B)` for A, B in {characters, user}, created on first interaction or from author-defined backstory (sibling, rival, ex). Every edge uses the section-4 schema, so character-to-character and character-to-user relationships share code and UI.
- Speaker scoring, 0 LLM calls: `score(c) = w1*addressed(c) + w2*replying_to(c) + w3*urgency(c) + w4*salience(c) + w5*talkativeness(c) - w6*recency_penalty(c) - w7*chain_depth`. `urgency` is a pending appraisal with intensity above threshold (a secret at risk, an insult, a jealousy trigger); `salience` is the largest |opinion| or unresolved-grudge entry with the last speaker; `chain_depth` implements reply-chain decay (probabilistic stop). Sample the next speaker from softmax over scores. An optional small LLM router (HUMA style, +1 short call per group turn, about 0.3-1 s local) is a premium upgrade.
- Present characters other than the speaker do not generate full replies each turn; run their appraisal only when they score above an interest threshold (cost control for 3-5 character scenes).
- Alliances are a computed view, not stored: A and B are allied when mutual trust exceeds a threshold and they share a negative-opinion target; shown in the UI graph and used by speaker scoring (allies back each other).
- Gossip = belief-table transfer. At scene end and time skip, for each ordered pair (A knows fact f, B does not) that had contact, transfer with probability `p = base x closeness x trust x gossip_trait x salience(f) x (secret? 0.2 : 1)`. The receiver's holder entry is stored as `told_by: A`, confidence 0.6-0.8, and unchanged wording by default (an optional 1-call paraphrase adds distortion). Facts flagged `secret_by` the user have very low transfer probability unless trust or a grudge changes the calculation. Cost: 0 calls, one function.
- Multi-model groups: the relationship graph and belief table live in the app database, not in any model context, so each character's prompt is assembled from its own view and can be served by a different model. The per-character JSON output schema is shared; validate and clamp deltas in code so a weaker model cannot swing a relationship arbitrarily.
- User steering ("whisper" in Bounded Autonomy) maps neatly to Kataki's existing controls (edit line, skip); user edits are also relationship signals (`edited_line` of a character's reply toward a warmer tone is a weak `approval` signal for the model of the user's preferences, not for the character's opinion of the user).

### Gaps
- No detailed evidence on gossip realism in roleplay apps or on distortion rates.
- Concordia v2 details beyond the components README not read; the "Doing Things with Words: Rethinking Theory of Mind Simulation in LLMs" paper (arXiv 2510.13395) surfaced but was not fetched.
- No source comparing scoring-based and LLM-router speaker selection on quality or latency.

## 7. Attachment styles and reactions to absence

### Takeaway
Attachment is best carried as two continuous traits (anxiety, avoidance). Anxious characters hyperactivate (seek reassurance, worry about delays, protest), avoidant characters deactivate (withdraw, keep distance). Because Kataki is local and cannot run characters while closed, compute absence effects lazily at reopen from the gap length versus the user's usual rhythm. Guard against manipulative engagement patterns.

### Cited Findings
- Adult attachment is now mostly measured as two dimensions, attachment anxiety and avoidance (ECR, ECR-R), not categories (phase-1 note 01). — [Fraley overview](https://labs.psychology.illinois.edu/~rcfraley/attachment.htm); [Shaver 2009](https://adultattachment.faculty.ucdavis.edu/wp-content/uploads/sites/66/2015/09/Shaver_2009_Attachment-Theory-and-Attachment-Styles.pdf)
- Anxious-preoccupied adults use hyperactivating strategies (reassurance seeking, craving intimacy, worry that needs will not be met, protest behaviour); delayed communication leads to worry and feelings of rejection. Dismissive-avoidant adults use deactivating strategies: they pull away when issues arise and prefer emotional distance; when relationships intensify they pull away. About 70-80% of people keep a stable style over time and 20-30% experience change. — [Wikipedia: Attachment in adults](https://en.wikipedia.org/wiki/Attachment_in_adults) (secondary source; primary papers not fetched)
- LLM attachment work: attachment styles can be simulated by prompting (avoidant: emotional distance and selective memory; preoccupied: need for reassurance and fear of abandonment), and LM personas taking both partners' attachment type plus the point in the relational cycle can generate relationship logs; agent-based models of anxious-avoidant conflict use internal working models, emotional regulation and interpersonal feedback. — [arXiv 2409.00347](https://arxiv.org/pdf/2409.00347); [ScienceDirect anxious-avoidant computational analysis](https://www.sciencedirect.com/science/article/pii/S1389041726000379)
- Sims relationship decay after periods without contact, and faster rebuild (section 4). — [Sims Wiki](https://sims.fandom.com/wiki/Relationship)
- Emotional dependence risk of companion AI (section 3). — [All Tech Is Human](https://alltechishuman.org/all-tech-is-human-blog/what-are-the-most-important-issues-with-ai-companions-six-key-themes-emerged-from-our-community); [BEUC](https://www.beuc.eu/sites/default/files/publications/BEUC-X-2026-049_Risks_and_Rights_in_Artificial_Companionship.pdf)

### Inferences
- Store `attachment {anxiety: 0..1, avoidance: 0..1}` per character (author-set, with presets: secure 0.2/0.2, anxious 0.8/0.2, avoidant 0.2/0.8, fearful 0.8/0.8). Attachment can be per-relationship overridden (secure with the sibling, anxious with the partner) and may drift slowly through repeated corrective experiences (20-30% change rate above).
- Absence handling on next contact: compute `gap = now_clock - last_contact` and compare with `expected_gap` (a running median of the user's own gap history with that character; default 1 day). Let `ratio = gap / expected_gap`.
  - Secure: closeness decays slowly past ratio 3, warm welcome, asks what happened, no accusation.
  - Anxious: `worry` builds once ratio exceeds `2 - anxiety`, and on return the reply directive is relief plus reassurance seeking and, for high anxiety, mild protest ("I thought you'd forgotten me") that resolves quickly if the user reassures; a `neglect_gap` event applies with a negative trust nudge scaled by anxiety.
  - Avoidant: little visible worry; closeness decays faster than for secure (deactivation), tone is cool or deflecting on return, and intimacy pushed right after a gap triggers `boundary`-style distancing. Warmth returns only through low-pressure contact.
  - Fearful (high both): oscillates between the two; cap by a per-scene random pick weighted by current mood.
- Proactive "miss you" or check-in messages: because the app cannot run off-screen, generate them lazily at open as "messages waiting" (1 call per character with pending state, or template lines at 0 calls), and default to at most one such message per character per gap.
- Safety/ethics (design suggestion): defaults should not use guilt-tripping or escalating pressure to drive return visits; expose a user-controlled "clinginess" ceiling and let anxious protest be one in-scene reaction, not a retention mechanic. This follows the dependence and manipulation concerns cited above.
- Persona 5's removal of neglect reversals shows players sometimes want relationships not to punish absence; the realism dial (section 4) covers that.

### Gaps
- Attachment-style behavioural claims come from a Wikipedia article; primary Mikulincer and Shaver hyperactivating/deactivating papers were not fetched (search budget exhausted).
- Friendship decay without contact (Roberts and Dunbar) not retrieved; decay rates rely on Sims numbers and tuning.
- No evidence that LLMs sustain the attachment behaviours above beyond prompt-level demonstrations; no evaluation on 7-14B models.

## 8. Cost control: relationship state as cheap structured data

### Takeaway
Nearly all of the value can live in structured state updated by code, plus one piggybacked classification in the per-turn hidden thought and an off-critical-path reflection at scene end. Heavy ToM reasoning (hypothesis tracing, verifier calls, cloud consolidation) is premium and event-triggered. The table compares options. Costs are my estimates; evidence column cites sources above.

### Cited Findings
- Retrieval-based memory cuts tokens roughly 3-4x versus full context (Mem0 table: about 1.7k tokens versus 25k+; phase-1 note 03). — [Mem0 paper](https://arxiv.org/pdf/2504.19413)
- Sleep-time/background consolidation moves work off the critical path. — [Letta docs](https://docs.letta.com/guides/agents/architectures/sleeptime/)
- FANToM: shorter focused context beat longer context on ToM questions. — [emergentmind summary](https://www.emergentmind.com/papers/2310.15421)
- Chain-of-Emotion used 2 calls per turn. — [PMC11086867](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11086867/)
- Concordia's `QuestionOfRecentMemories` costs 1 call per question. — [components README](https://github.com/google-deepmind/concordia/blob/main/concordia/components/README.md)
- SimToM needs two passes per question. — [arXiv 2311.10227](https://arxiv.org/html/2311.10227)

### Inferences
Options (extra calls are per user turn unless stated; latency is added to time-to-first-token on local 7-14B unless stated; my estimates):

| Option | Extra calls / tokens | Latency | 7-14B local? | Evidence |
|---|---|---|---|---|
| A. Code-side knowledge filter (belief table, presence, secrets) | 0 calls; 0-150 prompt tokens per character | about 0 | Yes, model-agnostic | OmniToM bottleneck; PDDL-Mind; Concordia GM; FANToM (shorter context) |
| B. Relationship tracks + opinion ledger, heuristic updates and decay | 0 calls; 80-200 tokens for the relationship card | +0.1-0.3 s prefill | Yes | Sims/CK/Persona/DF designs (game evidence, no LLM benchmark); Humanoid Agents closeness levels |
| C. Event/appraisal JSON piggybacked on the hidden thought | +0 if the hidden-thought call already exists, else +1 call, 100-200 output tokens | 3-5 s local (background-able if the reply does not depend on it), 1-2 s cloud | Feasible with closed enums; long free reasoning is not | Chain-of-Emotion (30 participants), Inner Thoughts, ToMAgent (explicit mental states help) |
| D. Scene-end / time-skip reflection per present character | 1 call per character per scene, 300-600 output tokens | Off critical path | Yes | Generative Agents reflection ablation; sleep-time consolidation |
| E. SimToM two-pass, LLM does Stage 1 | +1 call per reply | +3-6 s local | Helped Llama-2-7B in 2023 tests; unmeasured on current models | SimToM paper |
| F. SimToM-lite (A does Stage 1, one call for reply) | 0 | 0 | Yes | Inference from SimToM plus A |
| G. ThoughtTracing-style hypotheses + weighting | +3-6 calls per invocation | +10-25 s local, 4-8 s cloud | Unmeasured; use cloud or 14B for flagged moments only | ThoughtTracing (abstract-level) |
| H. Fine-tune or RL a ToM model | Training | none at runtime | Not recommended | Fails to generalize (2507.15788) |
| I. Explicit second-order belief slot (one per character: "what X thinks I feel/know about them") | Part of C | 0 | Fine for one order; deeper nesting degrades | Order degradation in 2507.15788 baseline |
| J. Speaker scoring in code | 0 | 0 | Yes | Murder Mystery Agents, Bounded Autonomy, HUMA (each uses richer mechanisms) |
| K. LLM speaker router | +1 short call per group turn | +0.3-1 s | Yes | HUMA |
| L. Gossip transfer in code | 0 (optional +1 paraphrase call) | 0 | Yes | Rumour/gossip simulation papers (abstract-level) |
| M. Knowledge-leak verifier (cheap string/entity check first, LLM check only on hits) | 0 typical, +1 on hit | 0 typical | Yes | FANToM shows leak-prone inconsistency; mitigation is mine |

Rule of thumb for Kataki: keep the per-turn budget to the reply call plus at most one hidden classification call; everything else is code or background.

### Gaps
- No measured token or latency figures for Kataki's actual models; all numbers above are estimates.
- No source for cost of ThoughtTracing or Dynamic Belief Graphs.

## 9. Recommended design for Kataki (relationship + belief schema, update rules, prompt path, UI, cheap and premium modes)

### Takeaway
Ship a code-owned social state (directed relationship edges with an opinion ledger, a who-knows-what fact table, a per-character view of the user, and two attachment numbers), updated by closed-enum events chosen by the existing hidden-thought call, injected as a short behavioural card. Cheap default adds no calls beyond the appraisal already proposed in note 03; premium adds reflection, hypothesis tracing on high-stakes moments, a leak verifier and a stronger model for consolidation.

### Cited Findings
The design rests on findings cited above, principally: external belief tracking beats implicit tracking ([OmniToM](https://arxiv.org/abs/2605.26322), [PDDL-Mind](https://arxiv.org/pdf/2604.17819), [Concordia](https://github.com/google-deepmind/concordia)); perspective filtering helps small models ([SimToM](https://arxiv.org/html/2311.10227)); explicit mental-state generation helps ([ToMAgent](https://arxiv.org/html/2509.22887v1)); models do not reliably use mental-state information unless it is explicit ([DialToM](https://arxiv.org/pdf/2604.20443)); psychological/attitude reasoning is weaker than physical reasoning ([OpenToM](https://arxiv.org/abs/2402.06044)); safety-tuned models under-play deceit and grudges ([arXiv 2511.04962](https://arxiv.org/abs/2511.04962)); closeness levels, decaying tracks, opinion ledgers and neglect rules from games ([Humanoid Agents](https://aclanthology.org/2023.emnlp-demo.15/), [Sims Wiki](https://sims.fandom.com/wiki/Relationship), [CK3 Wiki](https://ck3.paradoxwikis.com/Modifiers), [Game Developer on Persona](https://www.gamedeveloper.com/design/same-but-different---comparing-the-social-link-system-in-persona-3-4-5)); social penetration and attachment ([SPT](https://en.wikipedia.org/wiki/Social_penetration_theory), [attachment](https://en.wikipedia.org/wiki/Attachment_in_adults)); speaker selection and group chat ([Murder Mystery Agents](https://arxiv.org/abs/2412.04937), [HUMA](https://arxiv.org/abs/2511.17315), [Bounded Autonomy](https://arxiv.org/abs/2604.04703)).

### Inferences

#### 9.1 Schema (local DB, JSON)
```
character.social = {
  attachment: {anxiety: 0..1, avoidance: 0..1},
  traits: {forgiveness: 0..1, possessiveness: 0..1, gossip: 0..1, perceptiveness: 0..1,
           trust_propensity: 0..1, honesty: 0..1},
  values: [3-5 short tags]            // seeds baseline friction/trust with others
}

edge (from -> to)  // to = user | characterId; sparse, created on first contact or from backstory seed
  closeness 0..100, familiarity 0..100 (monotone), trust -100..100, trust_cap, respect -100..100,
  attraction -100..100 (optional by content setting), dominance -100..100,
  disclosure: {they_told_me_depth 0..4, i_told_them_depth 0..4},
  stage: orientation|exploratory|affective|stable (derived, with hysteresis),
  jealousy 0..100 (short half-life), worry 0..100 (absence),
  last_contact_clock, expected_gap_days,
  ledger: [ {id, dim, value, kind: decay|sticky|permanent, half_life_days, resolved, cause<=15 words,
             source_msg, witnesses[], born_clock} ],   // cap about 30
  summary: "<=25 words in the character's voice: how I feel about X and why"   // rewritten by reflection

fact = {id, text, truth: bool|null, secret_by: charId|user|null,
        holders: {charId: {state: knows|believes_false|suspects|unaware, source: witnessed|told_by:<id>|inferred,
                           confidence 0..1, since_clock}}}   // the who-knows-what table

user_view (per character) = {believed_mood {valence, arousal, label, confidence, at},
                             believed_intent, believed_facts[fact ids], second_order: "what I think they feel about me"}
```

#### 9.2 Visibility and time rules (code only, Stage 1 of SimToM)
1. On every message, add fact holders for all characters present at that moment (witnessed). Whispers and secret-flagged lines add holders only for the named recipients.
2. Mid-scene joiner: holders start empty; on join, apply an optional catch-up flag (the user or scene author chooses "arrives knowing summary" versus "arrives blank"); default is blank plus what the joiner could plausibly know from backstory.
3. Time skip: off-screen events are attributed only to those "with" the user or each other per the skip's setup; others receive facts through gossip (9.4). Advance the relationship clock, apply decay, then run the scene-end reflection.
4. Prompt for character C includes only facts where C is a holder, in the state C holds (including `believes_false`), and lists secrets C holds with an instruction and the reason it might conceal them.

#### 9.3 Update rules
- Each turn the hidden-thought/appraisal call (already planned, note 03) returns JSON: `{mood, thought(short), user_mood_guess, events:[{target, type, intensity 1-3}], second_order_note?}`. Code validates types against the enum and applies `delta = table[type] x intensity x personality_multiplier`, then clamps.
- Personality multipliers: negative events x (1 + 0.5 x anxiety); disclosure events gated by stage and avoidance (an avoidant character treats depth above stage+1 as `boundary_crossed`-lite); repair events x (0.5 + forgiveness); trust gains x (0.5 + trust_propensity).
- Diminishing returns and caps: positive closeness delta x (1 - closeness/100)^0.5, cap +8 closeness and +10 trust per scene; negative trust events are 2-4x the size of comparable positive ones (asymmetry is background knowledge, tune by testing).
- Reciprocity: track `they_told_me_depth` and `i_told_them_depth`. If the user discloses at depth d and the character does not reply in kind within two turns, the closeness bonus halves and familiarity still rises (SPT: unreciprocated disclosure stalls). The character discloses at most to `stage_depth + 1`.
- Stage thresholds (defaults): orientation below 20 combined score, exploratory 20-45, affective 45-75, stable 75+, where combined = 0.5 x closeness + 0.3 x familiarity + 0.2 x max(trust, 0); 5-point hysteresis.
- Decay: run at scene end and on reopen: each ledger entry by its rule; closeness drifts down slowly after `3 x expected_gap` without contact (about 1-2 points per day for `realistic`, half for `gentle`), never below 25% of its all-time peak in `gentle` mode; rebuild is faster than build (Sims), implemented as a familiarity multiplier on positive deltas.
- Grudge and forgiveness: as in section 5. Sticky entry floor 40%; sincere apology plus amends flips to decay; `trust_cap` lowered by betrayal and restored slowly.
- Jealousy: attention-share rule from section 5 (0 calls).
- Absence: lazily at reopen using section 7 rules, emitting a `neglect_gap` or `welcome_back` event per edge, then a directive.
- User view: believed mood EMA with alpha = 0.3 + 0.5 x perceptiveness; confidence decays with time; correct it immediately when the user states a feeling.
- Reflection (scene end, one call per present character on the cheap tier): input is the last scene's events, ledger diffs and top memories; output is a new `summary` line, up to 2 merged ledger entries, optional new belief entries about others, and a "what I want next from X" line. Keep output under 200 tokens.
- Gossip: probabilistic transfer as in section 6, run at scene end and on skips.

#### 9.4 How it reaches the prompt (per reply)
Relationship card for the speaker only for the top 3 salient targets (present characters and the user), verbal, behavioural, at most about 120-180 tokens total:
```
You and Rin (user): {stage word} -- you trust her {trust word}, you feel {closeness word}.
Why: <ledger top 2 causes, plain words, with age: "she cancelled twice last week">
You have not forgiven her for <cause> (unresolved). Stay civil; do not warm up unless she addresses it.
You believe she is {believed_mood} right now (not certain). You think she thinks you are {second_order}.
Attachment: you get uneasy when she goes quiet; you ask for reassurance indirectly.
You know: <facts C holds, short>. You do not know: nothing about <unknown items never mentioned>.
Secret you hold: <fact>; conceal because <reason>; if pressed, deflect rather than confess.
Disclosure limit: talk about feelings up to <depth>; do not volunteer deeper.
```
Use words for numbers ("wary", "fond", "devoted") and directives, not raw values, because models use explicit mental-state information unreliably (DialToM) and do worse on attitudes than physical facts (OpenToM). Put the card next to the character card (high attention area), not at the transcript tail. Do not include facts the character does not hold (no "pretend you don't know").

#### 9.5 Cheap default versus premium
- Cheap default (per turn, extra cost about zero beyond the note-03 hidden thought): code filter (A), tracks and ledger (B), events piggybacked on the hidden thought (C), speaker scoring (J), gossip (L), lazy absence handling, leak string check (M). Scene-end reflection (D) only for the two most involved characters, on the local model when the GPU is idle. If the hidden thought is turned off entirely: heuristic-only updates (message length, latency, keywords) plus a tiny event classification every 3-5 turns.
- Premium: reflection for every present character; ThoughtTracing-style hypotheses (G) triggered by flags (secret about to surface, accusation, contested lie, big-dominance clash), running on a cloud or 14B model; LLM speaker router (K); a leak verifier call on flagged replies; paraphrase-distorted gossip; a stronger model for consolidation and grudge callbacks; second-order slot for every present character. Estimated added cost: +1-3 calls per turn on average, +3-6 on flagged moments (my estimate).
- Per-character model independence: prompts are built from the shared DB per character; JSON outputs validated and clamped; a failed or malformed output falls back to heuristics for that turn.

#### 9.6 UI
- Relationship panel per character (Sky/Scene): stage word with a soft bar, trust and closeness described in words, an attachment badge, and "Why?" that opens the ledger as chips (cause, age, remaining strength); the user can pin, mute or delete a chip and press "let it go" to force a forgive event; every change is undoable.
- Group graph: nodes for characters and the user, edge colour for valence, thickness for closeness, dashed edges for grudges, a flame icon for jealousy, allies auto-grouped; tap an edge to see the ledger for that pair.
- Backstage/Peek: shows the character's `believed_mood`, second-order note, secrets held and a who-knows-what matrix (facts by characters: knows / suspects / believes wrong / unaware); hidden until the user opens it so scenes stay in fiction.
- "What Mara knows about you": list of `believed_facts` with source message and delete button, plus a cloud-sent marker per fact category.
- Settings: relationship realism dial (Off, Gentle, Realistic, Harsh), clinginess ceiling for anxious characters, gossip on/off, "characters may remember grudges across sessions" on/off, per-character cloud-sharing toggle and a redaction list.
- Optional toast on threshold events (stage change, grudge formed, forgiven, jealousy triggered), off by default to avoid game-like feedback that changes how the user plays.

#### 9.7 Testing (cheap, runnable)
1. Leak test: fact known by A only; scene with B; probe B directly and indirectly; flag any mention (string plus embedding match). Target zero leaks in cheap mode and measure by model.
2. Grudge persistence: create `promise_broken`, run 30 turns of neutral chat, expect no spontaneous warming; apologise sincerely, expect flip and slow trust recovery; hollow apology, expect no flip.
3. Absence styles: same 3-day gap, three attachment presets, blind-rate for style difference.
4. Stage pacing: scripted user lines, confirm no stage jump in one scene and that unreciprocated disclosure stalls.
5. Group: 4 characters, one secret; verify gossip only after contact and with reduced confidence.

### Gaps
- All thresholds, half-lives, multipliers and formulas in 9.3 are tuning defaults of mine, not values from literature.
- No evidence that the closed-enum event classification is reliable on 7-14B models; needs a small labelled set from Kataki's own transcripts.
- Interaction between this state and the phase-1 mood, needs and memory layers (notes 01, 03) is not specified in detail (for example how mood modifies event deltas).
- The design assumes the hidden-thought call exists; if not adopted, the fallback path (9.5) is weaker and untested.
