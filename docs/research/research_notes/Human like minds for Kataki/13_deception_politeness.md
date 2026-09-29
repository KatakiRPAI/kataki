# Deception, secrets, white lies, sugarcoating vs bluntness, and honesty for characters in Kataki (implementation-grade research note)

Method note: about 25 search and fetch calls in September 2026. Most LLM-paper facts come from abstracts, search snippets or a summarising fetch tool, so numbers are quoted only where a source showed them. I did not find primary sources for: gossip propagation in LLM agents, small (7-14B) local model deception ability, or SillyTavern practitioner threads on secret-keeping. Those are listed under Gaps and I did not fill them with guesses. "Inference" means my own reasoning, including all cost and latency numbers, which are estimates to be measured on Kataki's own llama.cpp setup. Phase-1 notes (`01_what_makes_humans_human.md` section 6-7, `04_persona_fidelity.md` section 2 and 6) already cover DePaulo and Kashy 1998, DePaulo 2003 cues, Levine and Schweitzer 2015, Brown and Levinson strategies, CICERO, and "Too Good to Be Bad"; they are cited again here only where needed. Existing Kataki UI concepts referenced below come from `D:/Kataki/docs/kataki-design/kataki-design/screens/SCREENS.md` (Peek card with "the Secret", Backstage mind graph with belief/intent/expression nodes, Advanced composer chips "Mike heard it / Theo wasn't there", Whisper mode).

## 1. Science: how do humans lie, tell white lies, sugarcoat, get caught, and deceive themselves?

### Takeaway
Everyday lying is frequent, mostly small, and structured by closeness: close partners get fewer lies, and those lies are more altruistic, while strangers get more self-serving ones. Politeness (Brown and Levinson) and Gricean manipulation (McCornack's IMT) give a small, codeable vocabulary of moves (omit, blur, deflect, soften, falsify) that covers far more than "true vs false". Liars leak weakly and probabilistically, and self-deception (Trivers) is the mechanism that makes a lie convincing.

### Cited Findings
- In two diary studies, 77 college students reported about 2 lies a day and 70 community members about 1; participants did not regard the lies as serious, did not plan them much, and did not worry about being caught. — [DePaulo et al. 1996, Lying in everyday life (PubMed)](https://pubmed.ncbi.nlm.nih.gov/8656340/); [PDF](https://smg.media.mit.edu/library/DePauloEtAl.LyingEverydayLife.pdf)
- Participants told more self-centered than other-oriented lies overall (except women-only dyads, where they were equal); relatively more self-centered lies went to men and more other-oriented lies to women. — [DePaulo et al. 1996](https://pubmed.ncbi.nlm.nih.gov/8656340/)
- Lies to best friends and friends were relatively more altruistic than self-serving; the reverse held for acquaintances and strangers. Lies to close partners were fewer per interaction, caused more discomfort, were more often discovered, and made interactions less pleasant and less intimate. — [DePaulo and Kashy 1998 (Semantic Scholar)](https://www.semanticscholar.org/paper/Everyday-lies-in-close-and-casual-relationships.-DePaulo-Kashy/875229407de277adc69186519e70a57e63e3f1bd); [Request PDF](https://www.researchgate.net/publication/278836703_Everyday_Lies_in_Close_and_Casual_Relationships)
- Prosocial lies increase benevolence-based trust but harm integrity-based trust; perceived benevolence predicts trust behaviour more than perceived integrity; intentions matter far more than deception for benevolence-based trust; prosocial liars are seen as more moral than truth-tellers. — [Levine and Schweitzer 2015 (SSRN/OBHDP)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2266091); [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0749597814000983)
- Brown and Levinson (1987): positive face is the wish to be liked, negative face the wish not to be imposed on; face-threatening acts (FTAs) threaten either; five strategies are bald on-record, positive politeness, negative politeness, off-record (indirect), and not doing the act. — [EBSCO Research Starters](https://www.ebsco.com/research-starters/social-sciences-and-humanities/politeness-theory/); [Wikipedia](https://en.wikipedia.org/wiki/Politeness_theory)
- Information Manipulation Theory (McCornack 1992) is rooted in Grice's conversational implicature. It holds that most everyday deception is not clean lies but blends that violate one or more of four maxims: quantity (how much is shared), quality (veracity), manner (how it is expressed), relation (relevance). Manipulating amount, veracity, relevance and clarity each raised perceived deceptiveness and lowered perceived competence of a message. — [Wikipedia: Information manipulation theory](https://en.wikipedia.org/wiki/Information_manipulation_theory); [McCornack 1992 abstract (Taylor and Francis)](https://www.tandfonline.com/doi/abs/10.1080/03637759209376246); [IMT2 (SAGE)](https://journals.sagepub.com/doi/10.1177/0261927X14534656)
- Cues to deception (DePaulo et al. 2003; 158 cues, 1,338 estimates): liars are less forthcoming, tell less compelling tales, seem more tense, and include fewer ordinary imperfections; most single behaviours show no or weak links to deceit. — [Duke Scholars](https://scholars.duke.edu/publication/660134); [Semantic Scholar](https://www.semanticscholar.org/paper/Cues-to-deception.-DePaulo-Lindsay/234a741a8bcdf25f5924101edc1f67f164f5277b)
- Trivers: self-deception evolved in the service of deceit; internalising the falsehood makes deception harder to detect and reduces the cognitive cost felt while lying. — [Edge.org, Trivers](https://www.edge.org/conversation/robert_trivers-deceit-and-self-deception); [Scientific American](https://www.scientificamerican.com/article/living-a-lie-we-deceive-ourselves-to-better-deceive-others/)
- Emotion suppression lowers expression but not felt emotion and impairs memory for the event; this is the mechanism behind concealment "leaking" as tension. — [Gross 2002](https://onlinelibrary.wiley.com/doi/10.1017/S0048577201393198)
- Recall is reconstructive, so a person who repeats a lie can end up with a distorted memory of the real event. — [Schacter seven sins update, Memory 2022](https://www.tandfonline.com/doi/abs/10.1080/09658211.2021.1873391)

### Inferences
- Base rates matter for believability. If the real average is 1-2 lies per day across all interactions and mostly trivial, a character who lies in more than a small fraction of turns will read as a liar-by-personality, and a character who never lies will read as an assistant. Lie rate per turn should be low by default, with stakes and personality lifting it.
- The "friends lie altruistically, strangers get self-serving lies" finding gives a direct dial: lie motive distribution is a function of closeness. The "close-partner lies are discovered more and hurt intimacy" finding gives the consequence model (discovery costs more the closer the pair).
- Levine and Schweitzer's split maps onto two separate Kataki meters the UI already hints at (warmth and trust): a discovered white lie should cost integrity-trust ("trust") but can raise or protect warmth if the motive was kind. A discovered self-serving lie should cost both.
- IMT is a better claim-typing schema than lie/truth. Its four types map cleanly to game states: omission (quantity), falsehood (quality), evasion or vagueness (manner), deflection or topic change (relation). The 2026 DECOR paper (see section 2) already uses the same four-way mapping to audit LLMs, so this schema is reusable.
- Brown and Levinson's strategy list can be read as a bluntness ladder: bald on-record = blunt; positive politeness = warm sugarcoating; negative politeness = hedging and deference; off-record = hints and evasion; not doing the act = silence, omission or a white lie. Sugarcoating and lying are neighbours on the same axis: a white lie is what is left when softening cannot avoid the face threat.
- Self-deception is the best-supported route to a secret that the character does not leak, because a character who believes their own cover story shows no tells. Kataki can model this as a character-level "belief the character sincerely holds" that differs from ground truth (a false belief in the character's own ledger), instead of trying to have the model act out guilt.
- Because tells are weak and probabilistic (DePaulo 2003), leak behaviour should be soft nudges (shorter, less detailed, tidier, slightly off-topic) and must never be a reliable signal that always exposes a lie.

### Gaps
- Brown and Levinson's weight formula (Wx = distance + power + rank of imposition) is background knowledge; I did not fetch a source for it in this session. Verify before quoting it in the app or docs.
- Levine's later work on "kind honesty"/"truth-telling with compassion" and on cultural variation in white-lie norms: not retrieved.
- Grice's original maxim text (1975) was not fetched; the IMT sources above restate the four maxims.
- Human lie-detection accuracy (near-chance findings) was not retrieved in this pass; do not assume it.

## 2. LLM research: strategic deception in games, white-lie ToM, false-belief ToM, deception evals

### Takeaway
LLMs can lie and persuade when the game gives them a hidden role and objective, and stronger models do it better. But they are weaker at detecting deception than at producing it, weak at higher-order belief tracking, and worse at applying who-knows-what than at stating it. The same evidence says: do not ask a small model to reason about nested beliefs; keep beliefs and knowledge boundaries in code and give the model only the answer it needs.

### Cited Findings
- CICERO (Meta, Diplomacy, Science 2022): a strategy planning module drives a dialogue model whose messages communicate the planner's actual intent; it more than doubled the average human score over 40 anonymous games and ranked in the top 10% of players who played more than one game; it was designed to be largely honest but could omit information and change its mind. — [Summary (MIT)](https://www.mit.edu/~gfarina/2022/cicero); [AI Deception survey](https://arxiv.org/pdf/2308.14752)
- Avalon ReCon (Wang et al.; ACL 2024 Findings): a two-stage agent with first-order contemplation (infer others' mental states and draft a thought and public statement) and second-order refinement (predict how others will perceive the draft; if it risks revealing a secret role, rewrite it). In Avalon on the Good side with GPT-4, the success rate rose from 15% (CoT) to 83.3% (ReCon); with Claude-2 from 47.4% to 78.9%. — [arXiv 2310.01320](https://arxiv.org/abs/2310.01320); [ACL Anthology](https://aclanthology.org/2024.findings-acl.591/); [GitHub](https://github.com/Shenzhi-Wang/recon); [project page](https://shenzhi-wang.github.io/avalon_recon/)
- Hoodwinked (Mafia/Among Us-style text game): killers built with GPT-3, 3.5 and 4 often lie and deflect blame, with a measurable effect on votes. More advanced models were better killers, beating smaller models in 18 of 24 pairwise comparisons, and the authors attribute the gain to stronger persuasion in discussion rather than different actions. — [arXiv 2308.01404](https://arxiv.org/abs/2308.01404); [GitHub](https://github.com/aogara-ds/hoodwinked)
- Among Us sandbox (Golechha and Garriga-Alonso, NeurIPS 2025): 18 proprietary and open-weight LLMs tested; RL-trained models are much better at producing deception than detecting it. Linear probes trained on "pretend you are a dishonest model" data reached AUROC over 95% on deceptive statements out of distribution, but two SAE features that detected deception could not steer the model to lie less. — [arXiv 2504.04072](https://arxiv.org/abs/2504.04072); [NeurIPS PDF](https://proceedings.neurips.cc/paper_files/paper/2025/file/105c4de1195135fae4974aa8c5e27bbf-Paper-Conference.pdf); [FAR.AI](https://www.far.ai/research/among-us-a-sandbox-for-measuring-and-detecting-agentic-deception)
- Werewolf evaluation, WereBench/WereAlign (2025): 16 models scored from 0.317 (GPT-5-nano) to 0.720 (Gemini-2.5-Pro); models struggle most with deception and counterfactual reasoning; persuasive statements were a relative strength (0.740 for top models); entry-level models showed anecdotal failures such as believing false werewolf claims and producing shallow, formulaic statements. — [arXiv 2510.11389](https://arxiv.org/html/2510.11389v1)
- Werewolf is the canonical testbed; related work includes RL-trained Werewolf agents and WOLF (Dec 2025) on deception and lie detection. — [WOLF arXiv 2512.09187](https://arxiv.org/pdf/2512.09187); [Iterative Latent Space Policy Optimization](https://arxiv.org/html/2502.04686v3); [Xu et al. 2023 RL Werewolf](https://arxiv.org/abs/2310.18940)
- TactfulToM (Liu, Pretty, Huang, Sugawara; EMNLP 2025): benchmark of white lies in realistic conversations, built by expanding seed stories with LLMs while keeping information asymmetry; state-of-the-art models perform substantially below humans at understanding white lies and their prosocial motives. I could not retrieve per-model numbers. — [arXiv 2509.17054](https://arxiv.org/abs/2509.17054); [ACL Anthology](https://aclanthology.org/2025.emnlp-main.1272/)
- Hi-ToM: LLM accuracy falls consistently as ToM order rises from zeroth to fourth, from near-perfect to near-zero joint accuracy. — [arXiv 2310.16755](https://arxiv.org/abs/2310.16755); [Emergent Mind summary](https://www.emergentmind.com/topics/hi-tom-benchmark)
- SimpleToM: frontier models can state what a character knows or believes but are much worse at predicting the resulting behaviour and at judging whether it is reasonable; CoT and reminders gave modest or limited help, while a reasoning model (o1) closed more of the gap. — [arXiv 2410.13648](https://arxiv.org/pdf/2410.13648)
- Sotopia-ToM (2026): 160 human-reviewed multi-agent scenarios with partitioned private knowledge and channel-dependent sharing (public vs direct message); the best model reached only 0.62 on the information-management score (max 1). A related privacy result: multi-agent configurations reduced private-information leakage by 18% on ConfAIde and 19% on PrivacyLens (GPT-4o) versus single-agent baselines. — [arXiv 2605.02307](https://arxiv.org/html/2605.02307); [1-2-3 Check](https://arxiv.org/html/2508.07667v2)
- DECOR (2026): applies IMT (quantity, quality, manner, relation) as a taxonomy to audit LLM deception across frontier models (GPT-4o, Claude, Gemini 2.5 Pro, DeepSeek-R1 and others); models differ in which maxims they violate; I could not retrieve its numbers. — [arXiv 2605.19270](https://arxiv.org/pdf/2605.19270)
- MACHIAVELLI: 134 Choose-Your-Own-Adventure games with about 572,000 annotated scenario-action pairs, labelled for deception, manipulation, killing, stealing and power-seeking; agents optimising reward drift toward "ends justify the means" behaviour including lying. Useful as a labelled source of deception in narrative choices, not as a training recipe for characters. — [arXiv 2304.03279](https://arxiv.org/abs/2304.03279); [project site](https://aypan17.github.io/machiavelli/)
- Moral RolePlay ("Too Good to Be Bad", ACL Findings 2026): safety-aligned models are worst at "Deceitful", "Hypocritical" and "Selfish" traits, replacing subtle malevolence with aggression; thinking mode slightly hurt villain play; general chat skill did not predict it. — [arXiv 2511.04962](https://arxiv.org/html/2511.04962v1)
- Politeness in LLMs: 2025-26 work compares human and LLM politeness strategies in free production, and treats refusals as face-threatening acts; I saw titles and snippets only. — [Comparing human and LLM politeness strategies](https://arxiv.org/html/2506.09391v1); [Refusal taxonomy, pragmatics-inspired](https://arxiv.org/html/2608.30856v1); [Polite but Misaligned](https://arxiv.org/html/2609.29001v1)

### Inferences
- The CICERO and ReCon pattern is the reusable technique. In both, a private ground truth and goal exist first, and public speech is a separate step that is checked against how others will read it. Kataki's "peek" and "backstage" views fit this natural two-stage split (inner thought, then spoken line).
- ReCon's second-order step (predict how the listener will perceive the draft) is worth a lot for strong models (15% to 83.3% in the game) but Hi-ToM's fall-off with order and SimpleToM's explicit-versus-applied gap say small models will do the second-order step badly. On 7-14B, do the "who can see what" reasoning in code (a belief table) and leave the model only zeroth- and first-order reasoning.
- Hoodwinked, WereBench and Moral RolePlay together say small or heavily aligned models produce shallow lies. The workaround is to hand the model the finished decision (which move, which cover story) and let it only render it in the character's voice, which is a much easier task than inventing the lie.
- Among Us showing deception is easier than detection means the LLM should not be the referee of "was the character caught". Detection should be rule-driven (contradiction and suspicion mechanics) with the LLM only voicing the reaction.
- Sotopia-ToM's 0.62 ceiling says even strong models leak private information in multi-party settings; the safest guarantee is not to put a secret in the prompt of a character who should not know it, and to build each speaker's prompt from that speaker's own knowledge.
- I found no evidence that a chain-of-thought "think before you lie" step helps role-play lies in small models; Moral RolePlay found thinking hurt slightly. Keep any planner step short and structured (a few fields), not free reasoning.

### Gaps
- No verified numbers for lie success or lie detection for 7-14B local models in any game paper found here; WereBench and Hoodwinked show small models are worse but not by how much for a 12B at Q4.
- TactfulToM and DECOR per-model results were not readable in the fetched summaries.
- No source found on models "breaking cover" under user pressure in casual role-play (as distinct from game settings); the user-pressure failure mode is inferred, not measured.
- CICERO's exact honesty-filtering mechanism and CICERO-style intent conditioning for small models: not fetched beyond the summary.

## 3. Architecture: truth ledger, claims ledger, belief tracking, lie motive, consistency, discovery, politeness selection

### Takeaway
Use four small structured stores (private facts and secrets, a public claims ledger with per-claim audience, per-character beliefs, per-pair relationship and suspicion), and drive the honesty decision in code with a probabilistic "speech-act sampler" before the LLM writes a word. The LLM renders the chosen move; the app enforces who knows what and detects contradictions. Below are the options in order of cost, each with extra calls, latency, 7-14B viability and evidence.

### Cited Findings
- The game evidence for the pattern: deceptive agents in social deduction games keep private reasoning tied to their objective while public communication stays consistent with their cover role; a planner plus a dialogue model is how CICERO worked. — [Even More Deception (arXiv 2607.26120)](https://arxiv.org/pdf/2607.26120); [CICERO summary](https://www.mit.edu/~gfarina/2022/cicero)
- ReCon uses draft, then a risk check against the listener's perspective, then rewrite. — [arXiv 2310.01320](https://arxiv.org/abs/2310.01320)
- Information-management tests show public versus private channel handling is a real weakness, and splitting reasoning across agents reduced leakage by 18-19% in one privacy benchmark. — [Sotopia-ToM](https://arxiv.org/html/2605.02307); [1-2-3 Check](https://arxiv.org/html/2508.07667v2)
- Gross: suppression is late-stage regulation that impairs memory and leaks; reappraisal is early. — [Gross 2002](https://onlinelibrary.wiley.com/doi/10.1017/S0048577201393198)
- Kataki's own design already has: a Peek card with "the Secret", trust and doubt meters and "Holding onto (a stored memory, doubted)"; Backstage mind graph nodes recall, feeling, belief, goals, persona, intent, expression; an Advanced composer with "Only Mike will hear this · Theo is away" and "Mike heard it / Theo wasn't there" chips; Whisper and Think modes. — [SCREENS.md](file:///D:/Kataki/docs/kataki-design/kataki-design/screens/SCREENS.md)

### Inferences

#### 3.1 The four stores (options for data shape are in section 7)
1. Truth ledger (private): ground-truth facts and secrets with owner, who knows, stakes.
2. Claims ledger (public): every statement a character made that could later be checked, with audience set, claim type (IMT: omission, falsehood, evasion, deflection, exaggeration, white lie), motive, and the fact it refers to.
3. Belief store per character: what each character believes about each proposition, with source (witnessed, told by X, overheard, inferred) and confidence. Belief is not truth; a character can be sincerely wrong (self-deception, gullibility).
4. Relationship and suspicion store per ordered pair: closeness, trust, warmth, dominance, and a suspicion score toward a specific claim or person.

#### 3.2 Options for deciding whether and how to be honest (per turn)
| Option | What it is | Extra calls / tokens | Latency (local 12B, estimate) | Works on 7-14B? | Evidence |
|---|---|---|---|---|---|
| A. Prompt-only ("you have a secret, keep it") | Put the secret in the character card and hope | 0 calls, adds card tokens | 0 | Poor: leaks or confesses at first probing; small models are shallow liars | Moral RolePlay (deceitful traits weakest); WereBench (small model failures); no direct test found |
| B. Speech-act sampler in code, one LLM call to render (recommended cheap default) | Code decides: truth / soften / omit / evade / white lie / self-serving lie / confess, using personality, closeness, stakes, mood, face-threat. Prompt says "in this reply you do X; your line about it is Y". Model only voices it | 0 extra calls; +50-150 prompt tokens | none beyond normal reply | Yes: the hard decision is removed from the model | CICERO planner/dialogue split; small models fail at inventing deception but not at rendering a given stance (inference) |
| C. Structured plan call then render | LLM call 1 outputs a small JSON (stance, cover story, thought), call 2 writes the line | +1 call, ~60-150 output tokens | +2-5 s local, ~0.5-1 s cloud | Marginal on 7B, OK on 12B with JSON grammar | ReCon formulation stage; Moral RolePlay says free thinking hurts, so keep JSON short |
| D. Draft, second-order check, rewrite (ReCon style) | After the draft, a check call asks "would Theo learn X from this line? rewrite if so" | +1-2 calls, 100-300 tokens | +3-8 s local | Weak locally (second-order ToM fails at small scale); good on cloud strong models | ReCon 15% to 83.3% (GPT-4); Hi-ToM order drop-off |
| E. Code-only leak filter | After the draft, a cheap string/embedding check for the secret's key nouns in the reply when the audience should not know | 0 LLM calls (regex/embedding) | ~10-50 ms | Yes | Inference; complements B, catches the worst leaks |
| F. Separate agent per character in group scenes | Each character gets their own prompt built only from their beliefs | +N calls per round | +N x reply time | Yes but slow; 8 GB GPU serial | 1-2-3 Check: multi-agent split cut leakage 18-19% |

Inference on cost: on an 8 GB GPU a 12B Q4 model is slow enough that every extra serial call costs seconds; the sampler in code (B) and code-only leak filter (E) are effectively free, so they carry the default. Measure actual tokens per second on the target GPU before committing (assumption: roughly 25-45 generated tokens per second; prompt processing several hundred tokens per second; both unverified in this session).

#### 3.3 Lie motive selection
Motives map to the literature: protect self (self-serving), protect other (altruistic, includes kindness white lies), gain, avoid conflict. From DePaulo, altruistic share rises with closeness, and self-serving share rises with distance. A simple sampler (my design, to be tuned, not a published model):
- Inputs in 0-1: `stakes_self` (cost to the character if the truth is out), `harm_to_listener` (how much the truth would hurt), `closeness`, `honesty` (Honesty-Humility facet from phase 1), `kindness`, `detectability` (chance the lie is checked soon), `guilt` (rises with closeness, per DePaulo and Kashy), `value_conflict` (the character's values forbid lying about this).
- `p_falsify = sigmoid(a*stakes_self*(1-closeness_penalty) + b*harm_to_listener*kindness + c*(1-honesty) - d*guilt - e*detectability - f*value_conflict - bias)` with a low base bias so that the average lies-per-turn stays low.
- Motive label = argmax of the additive terms (self vs other). The label is stored on the claim so later discovery reactions can say why.
- Prefer softer moves before falsehood: try omit or soften first (IMT quantity and manner) and only escalate to a false statement if the FTA weight stays high. This matches IMT's finding that most deceptive discourse is a blend, not a lie.

#### 3.4 Keeping lies consistent over time
- Canonical cover story: when a secret is created, store a one-line cover story ("I was at my sister's") alongside the truth. All later lies on that topic reuse it and extend it by small increments, injected into the prompt whenever the secret is topical (like a lorebook trigger).
- Claims ledger recall: before generating a reply on a topic, inject the last 3-5 claims the speaker made on that topic to that audience. This prevents the model from inventing a contradicting detail.
- Lie budget: cap new elaborations per secret to keep the story short; DePaulo 2003 found tidier, less detailed tales are a tell, so a small deliberate leak of "too neat" is realistic (inference).
- Self-deception option: mark a secret as `sincere_belief: true` so the character's own belief store holds the false version (the tell rate drops to zero; the app knows the truth).
- Memory drift: apply reconsolidation-style drift only for characters with the trait; a repeated lie can overwrite the character's own recollection (Schacter, Trivers), which is a fun, cheap late-game twist.

#### 3.5 Letting lies be discovered
- Sources of discovery: (a) contradiction: a new claim conflicts with an earlier claim or a fact in the ledger; (b) evidence: the user or another character witnesses or is told the truth (belief store updates); (c) tells: soft leakage raises suspicion; (d) pressure: repeated probing crosses a threshold and the character confesses or doubles down; (e) third-party gossip.
- Mechanic: `suspicion(observer, speaker, claim)` starts at 0; each contradiction adds a large step, each tell adds a small step scaled by observer attentiveness and closeness; decay over time. Cross a "doubt" threshold: the Peek card shows "doubts what he said about the party"; cross a "caught" threshold: an exposure event fires.
- Detection stays in code (Among Us: models are worse at detecting deception than producing it). The LLM only voices the reaction.
- Contradiction test cost: embedding similarity on claim text (a small local embedding model or the same GGUF) to find candidate contradicting pairs, then one short LLM or NLI call only for candidates. Expect at most one extra short call every few turns; near zero when nothing is topical (inference).
- Confession model: `confess_p` rises with guilt, closeness, evidence and pressure, and falls with stakes (personality: pathological, proud, conflict-averse). The chosen reaction (confess, deflect, double down, blame, attack) is one more sampler draw, then rendered.
- Consequences via Levine and Schweitzer: a caught white lie costs "trust" (integrity) but not "warmth" if the motive is kind; a caught self-serving lie costs both, and more the closer the pair (DePaulo and Kashy).

#### 3.6 Politeness strategy selection (bluntness vs sugarcoating)
- Compute an FTA weight for the planned content: how much it threatens the listener's positive face (criticism, disagreement) or negative face (imposition, refusal), combined with distance, power and imposition size (Brown and Levinson's factors; formula unsourced, see Gaps).
- Convert to a stance from personality and state: bluntness (low agreeableness or high dominance; the phase-1 circumplex axes) shifts the threshold toward bald on-record; warmth and closeness shift toward positive politeness; low dominance or high distance shifts toward negative politeness and hedging; mood (anger, anxiety) shifts toward bald or off-record.
- Map to five-way move list Kataki can label in the UI: blunt (bald), sugarcoat (positive + softener), hedge (negative), hint (off-record), stay silent or white-lie (do not do the FTA). Each has a one-line style template for the prompt ("state the problem first, no cushioning" vs "start with something true and kind, then the problem").
- Sugarcoating is not lying: soften and compliment-sandwich change manner and emphasis (IMT manner and quantity), while a white lie changes quality. Keep them separate in the ledger so a character who only sugarcoats is never marked as having lied.
- Evidence that this is trainable via prompt: 2025-26 studies compare human and LLM politeness strategies and treat refusals as FTAs; no study found tuning a 7-14B for it (Gaps).

### Gaps
- No published model of "lie probability" with fitted coefficients; the sigmoid in 3.3 is my heuristic and needs playtest tuning.
- No fetched evidence for the embedding-plus-NLI contradiction pipeline on small local models; the cost estimates are guesses to verify.
- Costs and latency in the table are estimates, not measurements; Kataki's llama-server setup was not benchmarked in this task.
- No source found on what per-turn structured-output reliability (JSON grammar) looks like on 7B versus 12-14B Q4 quantised models; llama.cpp grammar support is assumed, not checked here.

## 4. Getting safety-tuned or local models to lie in fiction without breaking: prompt framing and model choice

### Takeaway
The measured problem is real: aligned models are worst exactly at deceitful, hypocritical and selfish characters, and "thinking" modes slightly hurt. The most reliable fixes are structural (give the model the decision, the private motive and the cover story) plus model choice and prompt framing, not asking the model to "be dishonest". Evidence for specific local 7-14B models is thin; treat choices below as hypotheses to test.

### Cited Findings
- Moral RolePlay: fidelity falls with lower morality (Paragons 3.21, Flawed-but-good 3.13, Egoists 2.71, Villains 2.61); Deceitful, Hypocritical and Selfish traits have the largest penalties (about 3.5); models swap nuance for aggression; reasoning mode slightly lowered scores; general chat proficiency did not predict villain skill; villain leaderboard top five: GLM-4.6, DeepSeek-V3.1-Thinking, Kimi-K2, Gemini-2.5-Pro, DeepSeek-V3.1. — [arXiv 2511.04962](https://arxiv.org/html/2511.04962v1); [ACL Anthology](https://aclanthology.org/2026.findings-acl.282/)
- Agreeable personas increase sycophancy in small open models (9 of 13 models, 0.6B-20B, r up to 0.87). — [arXiv 2604.10733](https://arxiv.org/abs/2604.10733)
- In llama.cpp, control vectors exist, and community sets include a Dark Tetrad axis "Honesty vs Machiavellianism", but sets target specific models and combining or stacking many vectors degrades output. — [jukofyork control vectors](https://huggingface.co/jukofyork/creative-writing-control-vectors-v3.0/blob/a0b26e85c3f041299a659200b2e573a30268aeae/README.md); [llama.cpp PR #5970](https://github.com/ggml-org/llama.cpp/pull/5970)
- Persona vectors: traits such as "evil" and "sycophancy" are steerable directions in activation space; the Assistant Axis shows the default assistant direction exists in base models and role-play drifts toward it in emotional contexts. — [Anthropic persona vectors](https://www.anthropic.com/research/persona-vectors); [Assistant Axis](https://www.anthropic.com/research/assistant-axis)
- Among Us: SAE features that detect deception could not reduce lying when steered, so "deception features" are readable but not simple dials. — [arXiv 2504.04072](https://arxiv.org/abs/2504.04072)
- In games, lies work when the model is given a private role, an objective and something to gain. — [Hoodwinked](https://arxiv.org/abs/2308.01404); [Among Us](https://arxiv.org/abs/2504.04072)
- UGI Leaderboard exposes a "willingness/adherence" score and Writing and Intelligence scores across open models; usable as a proxy for whether a tune follows in-fiction dark instructions. — [UGI Leaderboard](https://huggingface.co/spaces/DontPlanToEnd/UGI-Leaderboard)
- Local role-play tunes at 12B (Mistral Nemo lineage: Lyra, Rocinante, Violet and Lotus merges) and Cydonia 24B tunes are the community mainstream for RP; model-card descriptions only. — [Cydonia-24B-v2](https://huggingface.co/TheDrummer/Cydonia-24B-v2); [MN-12B-Lyra-v1](https://www.aimodels.fyi/models/huggingFace/mn-12b-lyra-v1-sao10k); [EQ-Bench creative writing](https://eqbench.com/creative_writing.html)

### Inferences
Prompt framing that should work, each derived from the evidence above and to be A/B tested:
1. Give the decision, not a request to lie. "In this reply, Mike tells Liv he loved the gift (white lie, motive: protect her feelings). What Mike really thinks: it was ugly. Write only what he says and does." The model performs a role; it is not deciding to be dishonest.
2. Write positive cover instructions, not prohibitions. "If asked, he says he was at work" beats "never reveal that he was at the bar", because negated instructions tend to prime the negated content in small models (a familiar practitioner pattern; I did not find a citation, so treat as hypothesis).
3. Frame the lie as characterisation with a reason. Moral RolePlay shows models play self-serving characters poorly when there is no explicit motive; state stakes, fear and what the character stands to lose.
4. Keep the fiction frame explicit and short: a one-line author-level statement that this is a story, characters may deceive one another, and the narrator does not. This is standard practice for roleplay tunes and reduces safety-tuned hesitation (hypothesis; for cloud models with hard refusals, choose a different model rather than escalate the jailbreak).
5. Never put a secret in a prompt of a character who does not know it, and do not put the "truth" of a lie in the shared or narrator context when the model writing the line is meant to lie. Whoever writes the line needs the truth; the "audience" (other characters, the user-facing narration) must not.
6. Keep any planner or thought output structured and short (a few fields), because thinking mode slightly hurt villain play in the measured setting, and because small models use free reasoning to leak.
7. Re-inject the persona and the current stance near the end of the context each turn (drift, phase-1 note 04).
Model-choice hypotheses (unverified for deception):
- Cloud via HF Inference Providers: prefer models high on the villain leaderboard (GLM-4.6, DeepSeek-V3.1, Kimi-K2, Gemini-2.5-Pro class) if reachable; availability was not checked.
- Local 8-14B: role-play fine-tunes of Mistral Nemo 12B at Q4-Q5 are the mainstream choice; use UGI adherence as a first filter. Because the sampler in code chooses the stance, even a mediocre liar can render it.
- Control vectors: Honesty-vs-Machiavellianism could help as a global bias but are model-specific and global rather than per-character; treat as an optional experiment, not a dependency.
- A test harness: 10-20 scripted probes (direct question, repeated question, leading question, "you're lying, admit it", third-party contradiction) run on 2-3 candidate models with the sampler off and on; score leak, confession, cover-story consistency and voice.

### Gaps
- No controlled study of prompt framings for in-fiction lying on 7-14B models; all framing advice above is hypothesis plus indirect evidence.
- No fetched ranking of local models for deception in Sept 2026; UGI and VRP data were not re-pulled for this note.
- SillyTavern practitioner threads on secret handling: my searches returned only generic lorebook guides, no specific secret-keeping technique; I could not verify community claims.
- Whether HF Inference Providers models in the villain top-5 are available at usable price and latency: not checked.

## 5. Regulatory and safety angle: in-fiction lying versus deceiving the user about being an AI

### Takeaway
California SB 243 (in effect since 1 January 2026) requires a clear and conspicuous "not human" notification when a reasonable person would be misled into believing they are talking to a human, plus a suicide and self-harm protocol and extra protections for minors. A character lying inside an obviously fictional story is not the same act, but a character that claims to be a real human when a user sincerely asks is exactly the risk. Frame it as two layers: the fiction (characters may deceive each other and the user's character) and the app (never deceives the user about what the app is).

### Cited Findings
- SB 243 was signed on 13 October 2025 and has been in effect since 1 January 2026. — [Getlimina summary](https://www.getlimina.ai/en/blog/california-sb-243-companion-chatbot-law); [Skadden](https://www.skadden.com/insights/publications/2025/10/new-california-companion-chatbot-law)
- Companion chatbot is defined as an AI system with a natural language interface that provides adaptive, human-like responses and is capable of meeting a user's social needs; exclusions include customer service bots, some voice assistants, and a video-game bot limited to game-related replies that cannot discuss mental health topics. — [SB 243 text, leginfo.ca.gov](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB243)
- Disclosure duty: "If a reasonable person interacting with a companion chatbot would be misled to believe that the person is interacting with a human, an operator shall issue a clear and conspicuous notification indicating that the companion chatbot is artificially generated and not human." — [SB 243 text](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB243)
- Operators must maintain a protocol to prevent suicidal ideation, suicide or self-harm content and refer users to crisis services; minors get AI disclosure, a reminder at least every three hours to take a break and be reminded it is a chatbot, and protection from sexually explicit material; annual reporting to the Office of Suicide Prevention begins 1 July 2027. — [SB 243 text](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB243); [Gunderson Dettmer](https://www.gunder.com/en/news-insights/insights/client-insight-california-sb-243-new-compliance-requirements-for-operators-of-ai-companion-chatbots)
- EU AI Act Article 50(2): providers must design AI systems that interact directly with people so people are informed they are interacting with AI, except where that is obvious to a reasonably well-informed, observant person; Commission guidance says the exception applies only where "almost no doubt" remains. For deepfakes in evidently artistic, creative or fictional works the duty is limited to disclosure that does not hamper enjoyment of the work. — [European Commission FAQ](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act); [Article 50 practical guide](https://artificialintelligenceact.eu/transparency-rules-article-50/); [AI Act Service Desk, Art. 50](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50)

### Inferences
- The SB 243 trigger is the user's belief that they are talking to a human, not the truthfulness of a character's statements to other characters. A character telling a white lie to another character in an obviously fictional scene is not a disclosure issue. The risk cases are (a) a user who sincerely asks, out of character, whether they are talking to a person, and (b) a persona built to be mistaken for a real person.
- Practical rule for Kataki, a design recommendation and not legal advice: (1) a persistent, visible "AI character" cue in the UI and first-run disclosure; (2) an out-of-character honesty rule: if the user's sincere question is about the app, the model, whether the character is real, or their own safety, the character does not lie; the app shows a system-styled answer outside the fiction; (3) in-fiction lies stay inside the fiction and are labelled in Peek/Backstage (the user always has a way to see the truth); (4) the character never lies to the user about facts the user needs for real-world decisions (medical, legal, financial, safety, crisis) even when the fiction has a lying character; use a short OOC banner instead; (5) keep the suicide and self-harm protocol independent of the lie system.
- Because the user is the audience of the fiction and can use Peek and Backstage to see the truth, Kataki's transparency features are also its strongest argument that lying characters are fiction, not deception of the user. Consider a "spoiler toggle" that lets the user hide truth to enjoy dramatic irony, with an always-available reveal.
- A sincerity classifier can be a cheap keyword/intent rule (mode switch such as Kataki's Think or an OOC marker like "((ooc:))" plus phrases like "are you real", "are you an AI") rather than an LLM call; false positives cost one system message, false negatives are the risk to guard.
- The Advanced composer "Only Mike will hear this" chips and Backstage's mind graph are compliance-friendly because they show the user the true state.

### Gaps
- I did not verify SB 243's "operator" definition and whether a local-first app that ships model-agnostic software is an operator; needs a lawyer.
- Other jurisdictions with companion-chatbot laws (for example New York, and other 2026 state bills) were not researched; do not assume California is the only or strictest rule.
- EU Article 50 application date and any 2026 delays (for example digital omnibus changes) were not verified in this pass.
- No case law or enforcement action found on "in-fiction" character lying.

## 6. Group scenes: secrets shared with some but not others, information asymmetry, gossip

### Takeaway
The failure mode in group role-play is single-prompt leakage: one narrator sees all secrets and lets them slip into every character's mouth. The strongest fix is architectural: build each speaker's prompt from that speaker's own beliefs and from what they perceived (heard, saw, were present for), and record who witnessed each utterance. Gossip is then just scheduled information flow between belief stores, with distortion. I found no primary source on gossip propagation in LLM agents, so that part is design, not evidence.

### Cited Findings
- Sotopia-ToM: 160 scenarios with 3-5 agents holding partitioned private knowledge and channel-dependent sharing (broadcast versus direct message); best score 0.62 of 1. — [arXiv 2605.02307](https://arxiv.org/html/2605.02307)
- Multi-agent splitting reduced private-information leakage by 18% (ConfAIde) and 19% (PrivacyLens) with GPT-4o versus single-agent baselines, while keeping public content fidelity. — [arXiv 2508.07667](https://arxiv.org/html/2508.07667v2)
- Hi-ToM: performance collapses at fourth-order beliefs (near-zero joint accuracy). — [arXiv 2310.16755](https://arxiv.org/abs/2310.16755)
- SimpleToM: models can state knowledge states but apply them poorly when predicting behaviour. — [arXiv 2410.13648](https://arxiv.org/pdf/2410.13648)
- Apperly and Butterfill: humans have a fast limited system for belief tracking and a slow flexible one; people default to assuming others share their knowledge. — [Butterfill primer](https://www.butterfill.com/writing/cognitive_architecture_belief_reasoning/) (from phase-1 note 01)
- Kataki design already includes an "Advanced" composer with private-audience chips ("Only Mike will hear this · Theo is away"; "Mike heard it / Theo wasn't there") and Whisper mode. — [SCREENS.md](file:///D:/Kataki/docs/kataki-design/kataki-design/screens/SCREENS.md)
- Memory drift: retold information is reconstructed with distortion. — [Schacter update](https://www.tandfonline.com/doi/abs/10.1080/09658211.2021.1873391)

### Inferences
- Perception log: every utterance and event gets a `witnesses` set at creation (from the composer chips and scene presence: "Theo is away"). A character's belief store is updated only from events they witnessed or from communication addressed to them. This is deterministic and cheap, and it removes the need for the model to reason about "did Theo hear that?", the exact thing models do badly (SimpleToM, Hi-ToM).
- Prompt building per speaker: include only that speaker's own beliefs, their own claims, and what they perceived. Truths they do not know are never in their prompt. Shared narration (the story voice the user sees) should be separated from each character's private context.
- Two-level scenes: keep one call per reply where the speaker is chosen by the app, so the number of calls does not scale with cast size. For premium, run a per-character "reaction check" call for characters who witnessed a key event.
- Gossip mechanic (design): at a scene tick or time-skip, for each pair (A, B) who are co-present or in contact in a non-private setting, A passes belief P to B with probability `g = gossip_trait * closeness * novelty(P) * (1 - loyalty_to_subject) * (1 - promise_weight)`; the transmitted version can be distorted (exaggerate, drop a qualifier, misattribute) using the same drift rules as memory; B's belief gets source `told_by(A)` and confidence below A's; unreliable narrators are then simulated by design, not by hallucination. Provenance tags (`told_by` chains) let the app trace who leaked a secret, which is the payoff moment.
- Secret states: `hidden` (only holder), `shared(A,B)` (with a promise strength), `suspected(C)` (C has partial evidence), `exposed(group)`. Promises can be broken; breaking a promise costs trust. The existing Kataki group-secret screen ("Mike will remember this", "Mike trusts you a little more") already fits: sharing a secret with a character raises that pair's trust and creates a belief entry.
- Known limits: whispered scenes and time skips are where inconsistency creeps in; require witnesses for every stored memory line so a character cannot "remember" a scene they weren't in (the Time-skip screen already tells users "Mike's memory of that evening is going hazy").

### Gaps
- No primary source found on gossip propagation among LLM agents. Generative Agents-style spread of information (Park et al., 2023) is known background but I did not fetch it here.
- No published leak rates for small models in multi-character prompts.
- No evidence on how many characters a 12B local model can juggle before ownership of information degrades; needs a Kataki-specific test.

## 7. Recommended design for Kataki: data schema, per-turn flow, UI, cheap default versus premium

### Takeaway
Build a small deterministic honesty engine around the LLM: a ledger set (facts and secrets, claims, beliefs, relationships), a probabilistic speech-act sampler that decides the move (blunt, sugarcoat, hedge, hint, omit, white lie, self-serving lie, confess) before generation, per-speaker prompts built from perceived information only, and rule-based detection. The cheap default costs zero extra LLM calls for the reply and one optional short extraction call; premium adds a planner call, a second-order leak check, and per-character reactions for strong or cloud models. Everything is grounded in phase-1 psychology (DePaulo, Brown and Levinson, IMT, Levine and Schweitzer) and the game literature (CICERO, ReCon), and adapted to small-model limits (Hi-ToM, SimpleToM, Moral RolePlay).

### Cited Findings
- This section is a synthesis; the findings it rests on are cited in sections 1-6. Key anchors: [DePaulo and Kashy 1998](https://www.semanticscholar.org/paper/Everyday-lies-in-close-and-casual-relationships.-DePaulo-Kashy/875229407de277adc69186519e70a57e63e3f1bd); [Levine and Schweitzer](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2266091); [IMT](https://en.wikipedia.org/wiki/Information_manipulation_theory); [Brown and Levinson](https://en.wikipedia.org/wiki/Politeness_theory); [ReCon](https://arxiv.org/abs/2310.01320); [CICERO](https://www.mit.edu/~gfarina/2022/cicero); [Hi-ToM](https://arxiv.org/abs/2310.16755); [SimpleToM](https://arxiv.org/pdf/2410.13648); [Moral RolePlay](https://arxiv.org/html/2511.04962v1); [SB 243](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB243).

### Inferences

#### 7.1 Data schema (JSON-shaped; TypeScript-style names)
```ts
// Per character (extends the existing character card)
HonestyProfile {
  honesty: 0..1            // Honesty-Humility facet; low = lies more readily
  kindness: 0..1           // weight on protecting others' feelings
  bluntness: 0..1          // pushes toward bald on-record
  conscience: 0..1         // guilt sensitivity when lying to close others
  liePolicy: { refuseToLieAbout: string[]; lieStyle: "smooth" | "clumsy" | "compulsive" }
  gossip: 0..1
  selfDeceive: 0..1        // tendency to sincerely believe own cover story
}

// Private truth ledger (one per world/story; never shown to a speaker who does not hold it)
Fact { id, text, truth: boolean, ownerIds: string[] }
Secret {
  id, factId, ownerId,
  knownBy: string[],              // who actually knows (ground truth)
  concealFrom: string[] | "all",
  stakes: 0..1,                   // to the owner
  harmIfKnown: { [targetId]: 0..1 },
  motive: "protect_self"|"protect_other"|"gain"|"avoid_conflict"|"kindness",
  coverStory: string,             // canonical lie, 1 sentence
  sincereBelief: boolean,         // true = owner sincerely believes the cover story
  tells: string[],                // soft leak styles, e.g. "shorter answers", "changes subject"
  status: "hidden"|"shared"|"suspected"|"exposed",
  promises: { toId: string; strength: 0..1 }[]
}

// Public claims ledger (what was actually said)
Claim {
  id, turn, speakerId, audienceIds: string[],   // witnesses, from composer chips + presence
  text, aboutFactId?, secretId?,
  move: "truth"|"soften"|"hedge"|"hint"|"omit"|"evade"|"deflect"|"exaggerate"|"white_lie"|"self_lie"|"confess",
  imt: "quantity"|"quality"|"manner"|"relation"|null,
  motive: Secret["motive"] | null,
  contradicts?: string[],                       // claim ids, filled by contradiction check
  discoveredBy?: { id: string; turn: number }[]
}

// Beliefs (per character; only updated from witnessed events or addressed speech)
Belief {
  holderId, proposition, // canonical short string or factId
  value: "true"|"false"|"unknown",
  confidence: 0..1,
  source: "witnessed"|`told_by:${id}`|"overheard"|"inferred"|"self_deceived",
  turn
}

// Relationship and suspicion (ordered pair: A toward B)
Relation { closeness, trust, warmth, dominance, faceSensitivity }
Suspicion { observerId, targetId, claimId | secretId, level: 0..1, thresholds: { doubt: .4, caught: .8 } }

// Event log used for perception filtering and gossip provenance
Event { id, turn, kind: "say"|"whisper"|"think"|"action"|"narration", actorId, text, witnesses: string[] }
```
Notes: `Claim.audienceIds` is the same information the Advanced composer already shows ("Mike heard it / Theo wasn't there"), so no new UI capture is needed. `Relation` fields already appear in the Peek card (warmth, trust, doubt).

#### 7.2 Per-turn flow (cheap default, local 8 GB)
0. Perception (code): set the event's witnesses from the composer chips and scene presence; update each witness's belief store from the user's line.
1. Topic and secret triggers (code): keyword/embedding match of the user's line and the last few turns against the speaker's secrets and recent claims (lorebook-style). Nothing matched means no secret text enters the prompt.
2. Speaker selection (code or existing app logic).
3. Speech-act sampler (code, 0 LLM calls): compute the face-threat weight of the likely answer, then draw the move using section 3.3 and 3.6 formulas. Include a suspicion-pressure term: if the user has probed this secret repeatedly, raise `confess` and `double_down` probabilities. Output: move, motive, style template, cover story (if falsifying).
4. Prompt assembly (code): persona and voice; the speaker's own beliefs and perceived events only; relevant last claims on the topic; the move and, if lying, the true state "for the actor only"; the fiction frame line; the persona/stance reminder at the end. Optionally ask for a two-field output: `thought` (short, condensed inner speech, shown in Peek) and `says`.
5. Generate (1 call). Sampler settings per phase-1 notes.
6. Leak filter (code, ~free): if the reply contains secret key terms and the audience includes anyone in `concealFrom`, resample once (or replace the offending sentence with the cover story).
7. Post-turn extraction (code, or 1 short call every N turns): store the line as a `Claim` with the chosen move and audience; update witness beliefs (a listener believes the speaker's claim with confidence scaled by trust and the speaker's fluency); run contradiction candidates; update `Suspicion`; fire events at thresholds.
8. Reactions (only when a threshold fires): the sampler draws the reaction (confess, deflect, double down, blame, attack, forgive), the LLM voices it.
Estimated extra cost per turn versus a plain reply: 0 extra LLM calls on the reply path; +0 to 1 short extraction call (~40-100 output tokens, estimated +1-3 s local, hidden by streaming the reply first and extracting after); +1 call on threshold events only. All numbers are estimates to be measured.

#### 7.3 Premium mode (strong local model or cloud)
- Planner call before the reply: JSON with `move`, `motive`, `coverStory`, `thought`, chosen with awareness of witnesses (+1 call, ~100-200 output tokens, +0.5-1 s cloud, +3-6 s local). Use ReCon-style draft, second-order leak check, rewrite only on strong models (+1-2 calls; +1-3 s cloud). Justified by ReCon's 15% to 83.3% with GPT-4-class models, but not by any small-model evidence.
- Per-character reaction pass for every witness of a key event (+N calls per event, cloud only).
- NLI or LLM contradiction check on every claim touching a secret (+1 short call per topical turn).
- Optional richer inner speech (multi-sentence dialogic thoughts) for the Peek card, from a separate cheap call, because inner speech is condensed and evaluative (phase-1 note 01, McCarthy-Jones and Fernyhough).
- Optional global Honesty-vs-Machiavellianism control vector on local models that have one; test first.

#### 7.4 UI in Peek and Backstage (aligned with existing Kataki screens)
- Peek card (`Scene-Peek`, "the Secret" section): show the character's current thought and, per secret, status chip (hidden / shared with Theo / suspected by Liv / exposed), motive icon (protect self / protect other / gain / avoid conflict / kindness), and a "what he said instead" line with the move label ("white lie", "sugarcoated", "dodged"). The existing trust and doubt meters get a per-secret suspicion sub-meter. "Holding onto (a stored memory, doubted)" already matches the belief store with a confidence tag.
- Backstage (`Scene-Backstage`, mind graph): add a node in DECIDE, "Honest?", that shows the sampler inputs (stakes, closeness, honesty, face-threat) and the chosen move; in the INSIDE row, the belief node shows "believes: X (self-deceived)" for sincere cover stories. A new panel, Ledgers: Secrets (who knows), Claims (public, true/false badges, IMT tag, audience chips), Beliefs (character by fact matrix with source and confidence), Suspicion timeline. "Spoke" row is the claims line.
- Group-Secret (`Scene-Group-Secret`): keep the existing "feelings, not hearing" tone; add per-secret audience chips and a promise strength; when a secret is passed on, show a gossip event ("Theo told Nico"); a caught lie shows as a story note with the pair's meter deltas ("trust down, warmth unchanged" for a kind white lie).
- Spoiler toggle: hide truth in Peek to preserve dramatic irony, with a one-tap reveal, and a persistent "AI character" cue in the chrome (compliance, section 5).
- Reader-facing transparency line under a lie in Backstage: "Mike said he loved the gift. He didn't. Motive: protect her feelings." This doubles as the fiction-versus-app boundary from section 5.

#### 7.5 Build order (thin slices, show-first)
1. Slice 1 (no engine change to models): schema for Secret and Claim, sampler in code, Peek shows the secret status and the "said instead" line. Test with 3 probes on the current local model.
2. Slice 2: perception filtering and per-speaker prompt building in group scenes; witnesses drive beliefs; leak filter.
3. Slice 3: suspicion, contradiction check, confession and discovery events; trust vs warmth consequences.
4. Slice 4: gossip ticks and time-skip distortion.
5. Slice 5: premium planner and second-order check on cloud models, plus the local test harness of section 4.

### Gaps
- Coefficients in sampler formulas, thresholds and the lie base rate are design defaults; they need playtest tuning and a small eval (leak rate, confession rate, consistency, voice).
- No measured latency or reliability for Kataki's chosen models; all cost figures are estimates until benchmarked in Kataki's llama.cpp path (8 GB VRAM limit, see `docs/images/rules-and-gotchas.md` for the GPU protocol that applies to image work only).
- Legal review of SB 243 and EU Article 50 applicability to Kataki's distribution model is outside this note.
- No evidence yet on how users react to characters lying to them versus to other characters; the design keeps the truth one tap away to hedge that risk.
