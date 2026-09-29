# Mistakes, Self-Correction and Conversational Realism for Kataki Characters (Phase 2, as of September 2026)

Method note: about 45 tool calls. The web-search budget ran out mid-session, so the second half used direct page fetches and the arXiv API. Several publisher pages returned 403 (ACM, Taylor and Francis, PNAS, OpenAI, Replika, Kindroid). Where a claim comes from a search-result summary and not from the page itself, it says so. The corrected-typo paper and the Beyond Words paper were read in full text. Inner Thoughts was read from the arXiv HTML. Most others are abstract level. Numbers in tables under "Inferences" are design defaults to tune, not sourced findings. Phase-1 notes (`01_what_makes_humans_human.md`, `04_persona_fidelity.md`) are cited again where they carry the evidence. Kataki repo facts (memory model, speaker selection, pacing) were read from `D:/Kataki/engine/src/kataki/` and `D:/Kataki/app/src/pace.ts` on 2026-09-29.

## 1. Which mistakes are worth simulating, how often, and how do you keep them natural and not broken? (including cognitive biases and controlled injection)

### Takeaway
The best-evidenced human-like error is small: a typo that the character then corrects. Made-and-corrected typos raised perceived humanness across 3,399 participants, while uncorrected typos did nothing. Substantive errors (memory slips, misreadings, biased judgement) have thinner evidence: LLMs show some human biases (anchoring, framing) and lack others, and the only found precedent for deliberately injected persona errors (MathVC) is abstract-level. The engineering lesson is to plant errors from code with a known ground truth, not to ask the model to "make mistakes".

### Cited Findings
- Across five experiments, two supplemental experiments and pilot data (N = 3,399), agents who made and then corrected a typo were perceived as more human and more helpful than agents with no typo or an uncorrected typo. — [Imperfectly Human, full text](https://www.escholarship.org/content/qt7863m2pf/qt7863m2pf_noSplash_77769d18410cf32e93ad9cacc46fc0dc.pdf); [J. Assoc. Consumer Research 9(3)](https://www.journals.uchicago.edu/doi/abs/10.1086/728412)
- Live-chat Study 2 (N = 518): corrected typo M = 4.07 humanness versus no typo 3.45 (d = 0.36) and uncorrected typo 3.50 (d = 0.31). No-typo and uncorrected-typo were indistinguishable (d = 0.02). The authors conclude that correcting, not merely making, an error conveys a mindful agent. — [Imperfectly Human, full text](https://www.escholarship.org/content/qt7863m2pf/qt7863m2pf_noSplash_77769d18410cf32e93ad9cacc46fc0dc.pdf)
- The typo paradigm was minimal: two typos, each corrected in the next message with an asterisk ("helo" then "*help"; "talking" then "*taking"). In a comparison of humanising cues (N = 815), a corrected typo beat agent name, gender and a human photo. — [Imperfectly Human, full text](https://www.escholarship.org/content/qt7863m2pf/qt7863m2pf_noSplash_77769d18410cf32e93ad9cacc46fc0dc.pdf)
- When users knew the agent was a chatbot the effect shrank but persisted: corrected typo 3.25 versus no typo 2.53 (d = 0.60), against d = 1.34 when identity was ambiguous and d = 1.10 for a known human. Perceived humanness mediated expected helpfulness. — [Imperfectly Human, full text](https://www.escholarship.org/content/qt7863m2pf/qt7863m2pf_noSplash_77769d18410cf32e93ad9cacc46fc0dc.pdf)
- Counter-evidence: earlier chatbot work reports that typing errors mostly lowered perceived humanness and social presence, and that mistakes did not improve long-term perceptions of conversational agents. — [Beyond Words related-work section](https://arxiv.org/pdf/2510.08912)
- In the GPT-4.5 three-party Turing test, "linguistic style" was 27% of interrogator reasons (for example "they had a typo") and "interaction dynamics" 23% (for example "avoided questions"). The paper stresses that success needed more than surface tricks. — [Jones and Bergen 2025](https://arxiv.org/html/2503.23674v1)
- Related preprint: a highly agreeable prompted GPT agent exceeded a 60% confusion rate in a Turing-style test, and all three personality variants exceeded 50%. This conflicts in spirit with the introverted, evasive persona of Jones and Bergen, so persona style is test-dependent. — [arXiv 2411.13749](https://arxiv.org/abs/2411.13749)
- Users "prefer less human-like outputs from LLMs in many contexts," per HumT DumT, which links anthropomorphic language to warmth and to deception and overreliance risks. That was measured on assistant use, not companion roleplay. — [arXiv 2502.13259](https://arxiv.org/abs/2502.13259)
- Human memory failure has named types: transience, absent-mindedness, blocking, misattribution, suggestibility, bias, persistence. Tip-of-the-tongue gives accurate partial knowledge. — [Schacter update, Memory 2022](https://www.tandfonline.com/doi/abs/10.1080/09658211.2021.1873391); [Schwartz and Metcalfe](https://link.springer.com/article/10.3758/s13421-010-0066-8)
- LLM anchoring: simple mitigations (Chain-of-Thought, Reflection, "ignore the anchor" hints) were not enough for GPT-4 and Gemini. A 2026 benchmark of 14 models found even frontier API models with above 95% control accuracy remain susceptible to plausible anchors, and a synthetic-data study reports anchoring "exists commonly with shallow-layer acting." — [arXiv 2412.06593](https://arxiv.org/abs/2412.06593); [AnchorBench, arXiv 2608.14320](https://arxiv.org/abs/2608.14320); [arXiv 2505.15392](https://arxiv.org/abs/2505.15392)
- In a price-negotiation study, reasoning models were less anchored (long chain of thought mitigates the effect) and persona personality traits showed no correlation with anchoring. — [arXiv 2508.21137](https://arxiv.org/abs/2508.21137)
- In clinical-note interpretation, 23% of GPT-4 interpretations contained reasoning errors, with confirmation and anchoring bias most prevalent. Framing effects appear in LLMs in a human-like manner. Anxiety-inducing prompts reproduced human-like consumer biases. — [arXiv 2511.20680](https://arxiv.org/abs/2511.20680); [arXiv 2502.17091](https://arxiv.org/abs/2502.17091); [arXiv 2510.06222](https://arxiv.org/abs/2510.06222)
- Opposite finding: a benchmark of 20+ LLMs on causal reasoning found most use more rule-like strategies than humans and lack characteristic human biases. — [arXiv 2602.02983](https://arxiv.org/abs/2602.02983)
- MathVC uses "error-injected persona schemas seeded from teacher-specified misconceptions" for simulated students. A pilot with 14 middle-schoolers reported value from "realistic AI mistakes." Only the abstract was read, so schema structure and error rates are unknown. — [arXiv 2404.06711](https://arxiv.org/abs/2404.06711)
- Small open models get more sycophantic as the persona gets more agreeable (r up to 0.87 across 0.6B to 20B models), so a character who never holds a wrong belief against the user is the default failure. — [arXiv 2604.10733](https://arxiv.org/abs/2604.10733)
- Kataki already models forgetting: an ACT-R style activation with importance, relevance, graph, fidelity ("witnessed", "told", "overheard") and noise terms, plus a "detail ratchet" where gist survives without detail. The engine records beliefs and doubts per reply. — `D:/Kataki/engine/src/kataki/activation.py`, `D:/Kataki/engine/src/kataki/mind.py` (repo files read this session)

### Inferences
- **Error taxonomy ranked by payoff and control.**

| Error class | Where to produce it | Extra LLM calls | Latency | Works on 7-14B | Evidence it raises perceived humanness |
|---|---|---|---|---|---|
| Typo, dropped or swapped letter, wrong homophone | Display layer in code, after generation | 0 | none | yes (no model involvement) | Strong for corrected typos (N = 3,399); none for uncorrected |
| Memory slip on hazy memory (wrong detail, misattribution) | Engine picks a distractor detail and plants it in the prompt as "what you remember" | 0 | none | yes | Indirect only (Schacter taxonomy, Turing "knowledge gaps"); no direct human-rating study found |
| Missing part of the user's message (skim, answers only the first of two questions) | Engine flags which clause the character "did not register" | 0 | none | yes | None found; inference from human misreading |
| Wrong assumption about what the user knows | Knowledge-boundary rule in the prompt | 0 | none | yes | None found; limited theory of mind from phase 1 |
| Wrong word or malapropism | Code with a small per-persona confusion list | 0 | none | yes | None found |
| Biased judgement (anchoring, confirmation, first-impression stickiness) | Engine supplies the anchor and the held belief; character resists revision | 0 | none | yes | LLM anchoring is real and hard to remove, so it is cheap to induce; effect on perceived humanness untested |
| Real-world fact error | Only when a fact is outside the story's canon | 0 | none | yes | None found |

- **Plant errors, do not request them.** Kamoi and Huang (question 2) show models cannot reliably notice their own mistakes, and a model told to "make a mistake" will pick an easy or absurd one. If the engine chooses the wrong detail (for example the wrong weekday or a swapped name from the same category), then the engine holds ground truth and can drive a later repair. This is the same private-truth pattern phase 1 recommended for lying (CICERO-style split).
- **Never err on canon.** Slips are allowed only on memory the engine already scores as hazy, and on trivia outside the story. A character who forgets the murder weapon breaks the fiction; one who misremembers which cafe you met at is charming. Kataki's `activation.py` already produces this split: use the "hazy" band as the eligibility rule.
- **Frequency: start very low.** The one strong study used two typos, each corrected, per whole conversation. A reasonable default is a visible slip on roughly 1 in 10 to 15 character messages in casual texting, doubled for tired, anxious, drunk or careless characters and halved for precise ones. Persona and mood scale the rate. These are unsourced tuning defaults; instrument slip rate and let users turn it off.
- **Natural not broken:** (a) errors are local, not structural, so the sentence still parses; (b) errors follow persona and state (a hurried texter, not a scholar); (c) the same character repeats their own error pattern (one habitual confusion word), which reads as personality; (d) the character must remember having erred, and must not cave when the user "corrects" something that was actually right (sycophancy result).
- **Biases:** do not prompt "be biased." Inject the stimulus (a number the character heard first, a first impression stored as a belief) and let the model's own anchoring do the work. Give each belief a stickiness value and require accumulated evidence plus face cost (phase-1 Brown and Levinson framing) before the character updates it. Untested for perceived humanness; ship behind a persona flag.
- The corrected-typo effect is smaller when users know it is a bot (d 0.60 versus 1.34), and Kataki users know. It is still a medium effect, so it should still work, but expect a weaker signal than the headline numbers.

### Gaps
- No study found on the perceived humanness of substantive character errors (memory slips, wrong assumptions, misreading) in companion or roleplay contexts, as opposed to typos in customer-service chat.
- No human-rating data on how often is too often for slips; every rate above is a guess to be tuned.
- MathVC's error-injection method beyond the abstract was not retrievable.
- Mishearing and misreading the user as a designed feature: no LLM-side study found.
- I did not fetch the two Taylor and Francis chatbot-error papers (403); their findings appear above only through a search-result summary (social error responses judged more human-like than neutral ones), so I left them out of the findings list.

## 2. Self-correction and repair: how do humans do it, is LLM self-correction reliable, and how should a delayed correction be generated?

### Takeaway
Human repair is systematic and mostly self-initiated (Schegloff, Jefferson and Sacks). LLMs cannot reliably detect their own errors without external feedback, so Kataki must not depend on the model spotting its slips. The reliable route is engine-planted errors with engine-triggered repairs (mid-message restart, immediate "*fix", or a delayed correction turns later), written by a tiny call or a template.

### Cited Findings
- Repair organisation: self-repair by the speaker of the trouble source predominates over other-repair, with a preference for self-correction. Initiation and completion can each be self or other. — [Schegloff, Jefferson, Sacks 1977](https://www.cambridge.org/core/journals/language/article/abs/preference-for-selfcorrection-in-the-organization-of-repair-in-conversation/5549B861FDE7180B75FA5C382821875E)
- "Uh" signals a minor expected delay and "um" a major one; speakers use them for word search and floor-holding. — [Clark and Fox Tree 2002](http://www.columbia.edu/~rmk7/HC/HC_Readings/Clark_Fox.pdf)
- Type 1 gives a default answer that Type 2 may override, which maps to "first answer, then revision." — [Evans and Stanovich 2013](https://journals.sagepub.com/doi/10.1177/1745691612460685)
- ICLR 2024: LLMs "struggle to self-correct their responses without external feedback, and at times, their performance even degrades after self-correction." — [Huang et al., arXiv 2310.01798](https://arxiv.org/abs/2310.01798)
- TACL 2024: no prior work shows successful self-correction with feedback from prompted LLMs except on tasks exceptionally suited to it. Reliable external feedback works, and large-scale fine-tuning enables self-correction that prompting does not. — [Kamoi et al., arXiv 2406.01297](https://arxiv.org/abs/2406.01297)
- Correction is the humanising part of an error, not the error itself (uncorrected typo = no-typo). The authors' reading: correcting shows an engaged mind that cares how it is perceived. — [Imperfectly Human, full text](https://www.escholarship.org/content/qt7863m2pf/qt7863m2pf_noSplash_77769d18410cf32e93ad9cacc46fc0dc.pdf); [TechXplore summary](https://techxplore.com/news/2024-08-err-human-age-ai-humanizing.html)
- Beyond Words (CUI 2024, an open-source typing simulator, GitHub `jigglypuff96/human-like-typing-bot`): three GPT-based agents (baseline, hesitation only, hesitation plus self-editing). Self-editing randomly deletes, inserts or modifies characters, words or sentences, once per element, with the start of a sentence protected. Among 11 analysed participants (of 20 recruited) the hesitation-plus-editing agent was the most preferred, and users typed more with it (mean 62.27 words versus 49.10 for hesitation-only). Hesitation alone was the worst: human-likeness 1.727 versus 2.455 baseline and 2.909 for editing, and participants called it "dumb" and "robotic." The baseline was called "unreal" for its speed. None of the differences were statistically significant. — [Beyond Words](https://arxiv.org/pdf/2510.08912)
- Sesame's voice companions are reported (third-party summary) to produce disfluencies including filler words and self-corrections. Sesame itself states CSM "can only model the text and speech content in a conversation, not the structure of the conversation itself" (turn-taking, pauses, pacing). — [Learn Prompting summary](https://learnprompting.org/blog/sesame-conversational-speech-model); [Sesame research post](https://www.sesame.com/research/crossing_the_uncanny_valley_of_voice)
- Inner Thoughts implements a System 1 (quick, intuitive) and System 2 (deliberate, memory-based) thought path. — [Liu et al., CHI 2025](https://arxiv.org/html/2501.00383)

### Inferences
- **Repair types and how to produce them:**

| Repair | Trigger and script | Extra calls and tokens | Latency | Works 7-14B | Evidence |
|---|---|---|---|---|---|
| A. Instant asterisk fix (typo) | Courier sends message, then a second burst "\*word" after a short delay | 0 | 1-3 s extra | yes | Strong (corrected-typo studies) |
| B. Mid-message restart ("tuesday- no wednesday") | Engine rewrites a planted wrong slot into "wrong- no, right" in the reply text | 0 (string edit) | none | yes | Schegloff self-repair; no perception study |
| C. Follow-up correction message, seconds to minutes later | Engine holds `{slot, wrong, right}`; sends a corrective burst | 0 with template, or 1 tiny call (~40 output tokens) | ~1-3 s on local 8B for the tiny call | yes for template; tiny call fine | Indirect (corrected typo) |
| D. Delayed correction turns later ("wait, I told you the wrong day") | Engine schedules a repair after N turns or when the topic recurs | 1 tiny call | ~1-3 s | yes | Indirect |
| E. Changed mind after reflection | Premium: a reflection pass reads the last N turns plus the belief store and may revise a stance | 1 call, ~200-400 tokens | 3-8 s | borderline on 7B; better at 12-14B or cloud | Inner Thoughts uses System 1/2 thoughts; no direct test of mind-change |
| F. Other-initiated repair (user challenges) | Character checks the challenged claim against engine truth: owns a real slip, holds the line on a true statement | 0 extra (prompt carries truth) | none | yes | None found; sycophancy risk |

- **Do not use "reflect and revise" prompting as the correction mechanism** on 7-14B models: the literature says it does not work without external feedback, and Moral RolePlay found thinking mode slightly hurt in-character fidelity (phase-1 finding). The engine knows the answer, so the character never needs to discover it.
- **Delayed correction as its own message:** because the slip is planted with `{slot, wrong, right}`, the correction can be a template per persona ("wait \*{right}", "sorry {right}, not {wrong}") or one short call given the character card, the wrong line and the right value. Keep the corrected utterance in the transcript as its own row so the user can see and react to it.
- **Hesitation must have a reason.** Beyond Words suggests pauses without visible edits look "dumb"; combine a typing-indicator stall with a visible edit (a deleted or rewritten clause) or drop the stall. Sample size is tiny (n = 11, not significant), so treat it as a caution, not a law.
- **Cap the rate of repairs.** Mid-message restarts and "no wait" phrases are easy to overuse; a character that self-corrects every message reads as scripted (phase-1 medium-high risk). Suggested cap: at most one visible repair per five character messages.
- Changing one's mind should cost face: gate mind-change by openness and dominance, and let the character be stubborn first, then concede later after a gap (an incubation-style delay from phase 1).

### Gaps
- No perception study of delayed corrections (a correction several turns later) or of "changing one's mind" for chatbots.
- No quantitative human repair rate per turn (Schegloff gives structure, not rates).
- Beyond Words is a small exploratory study; I could not find a replication.
- I did not find how Sesame's disfluency behaviour was evaluated with users; only Sesame's naturalness-versus-context finding (raters showed no clear preference without conversational context, and favoured the originals when context was given).

## 3. Texting realism: bursts, typing indicators, variable latency, read-without-reply, double-texting, register

### Takeaway
Response timing is a social cue: delays scaled to message length and complexity raise perceived humanness and satisfaction, and a typing indicator mitigates the cost of a longer wait. The one directly usable, tested timing model is the delay formula from the GPT-4.5 Turing test. Bursts, read-without-reply and double-texting have no academic evidence found; they are product practice. In a story app with a story clock, most "long silence" behaviour belongs on the story clock, not the real one.

### Cited Findings
- The Turing-test system delayed each message with 1 s plus N(0.3, 0.03) x characters typed, plus N(0.03, 0.003) x characters of the previous message (reading time), plus a right-skewed Gamma(2.5, 0.25) s "thinking" term. — [Jones and Bergen 2025](https://arxiv.org/html/2503.23674v1)
- Dynamic response delays (length set by the complexity of the reply and of the previous message) increased perceived humanness and social presence and increased satisfaction versus near-instant replies, in a customer-service experiment. — [Gnewuch et al., ECIS 2018](https://aisel.aisnet.org/ecis2018_rp/113/)
- Typing indicators raised social presence only for novice chatbot users, and the effect depended on indicator design and prior experience. — [Gnewuch et al., SIGHCI 2018](https://aisel.aisnet.org/sighci2018/14/) (via search-result summary)
- With instant, 5 s or 20 s latency, longer latency lowered satisfaction, and a typing indicator mitigated that through higher social presence (search-result summary). — [From Seconds to Sentiments, IJHCI 2025](https://www.tandfonline.com/doi/full/10.1080/10447318.2025.2508915)
- In VR with LLM-driven agents, latency above 4 s degraded quality of experience and conversational fillers (gestures and verbal cues) bridged the gap, especially at high delay. — [Mitigating Response Delays, CUI 2025](https://arxiv.org/abs/2507.22352)
- Typing behaviour carries information about stress, cognitive load and topic familiarity. — [Beyond Words related work citing Vizer et al. and Ong et al.](https://arxiv.org/pdf/2510.08912)
- Beyond Words' timing parameters: per-character typing pace, per-word "space lag" pause, deletion pace and cursor speed, each drawn from a normal distribution. — [Beyond Words](https://arxiv.org/pdf/2510.08912)
- In Beyond Words' small sample, the user's word count tracked the agent's: user words = 0.67 x agent words + 6.81, R2 = 0.79 (n = 11). — [Beyond Words](https://arxiv.org/pdf/2510.08912)
- Phase-1 sources: turn gaps average about 200 ms in speech across ten languages and the listener predicts turn end, which does not transfer to text. — [Stivers et al. 2009](https://www.pnas.org/doi/10.1073/pnas.0903616106); [Levinson and Torreira 2015](https://www.frontiersin.org/articles/10.3389/fpsyg.2015.00731/full)
- Kataki already paces streaming replies to a reading speed (slow 25, normal 45, fast 90 characters per second, or instant) with a 40 ms tick. — `D:/Kataki/app/src/pace.ts` (repo file read this session)

### Inferences
- **Message delivery engine ("courier")** sits between the model's reply and the UI, in code:

| Feature | How | Extra calls | Latency effect | Works 7-14B | Evidence |
|---|---|---|---|---|---|
| Burst splitting | Prompt asks for short lines in phone/text mode; courier splits on newline into 1-4 bubbles and releases each after its own delay | 0 | first bubble can release on the first completed line, so time-to-first-bubble drops | yes (small models follow "one short line per message" from a first message and examples; not verified) | None found for bursts; timing evidence supports per-message delays |
| Length-scaled delay | Jones and Bergen formula, scaled per persona typing speed and mood | 0 | hidden inside LLM time (below) | yes | Moderate (Gnewuch, Turing test) |
| Typing indicator | Show while the computed typing time runs | 0 | none | yes | Moderate for novice users; mitigates waits |
| Delay hidden in generation | Start generating at once; release = max(0, computed delay minus elapsed) | 0 | zero added when the local model is slow | yes | Design inference |
| Read-without-reply | State flag "seen"; reply after k minutes | 0 | user-visible wait | yes | None found |
| Double-text / follow-up | Timer plus initiative score (section 4) | 0 or 1 | none | yes | None found |
| Reply-length variance | Sample a length class per turn, injected as one line at depth | 0 (~30 prompt tokens) | none | yes | Weak (length mirroring in n = 11) |
| Emoji, slang, lowercase, dropped periods | Deterministic per-persona post-process | 0 | none | yes | Turing test attributes 27% of reasons to style |

- **Latency budget:** the Turing formula gives long waits for long messages (0.3 s per character means about 3 characters a second, slow for a fast texter), which was fine for a 5-minute test but will annoy in a long roleplay. Scale typing time by a persona typing-speed factor and clamp total simulated delay to about 1.5-8 s in default mode (from the 4 s VR threshold and Gnewuch's finding, weakly transferred). Always offer "instant" and a tap to skip.
- **Delay is a mood channel, not decoration.** Reply latency multiplier from arousal (excited: fast; sulky or avoidant: slow), effort (long or hard message: slow) and availability (character's story-clock schedule). A face-threatening reply gets a longer pre-typing pause (phase-1 inference).
- **Story clock versus wall clock.** In scene mode, "left on read for two hours" should be a story-clock jump (Kataki's `clock.py` already owns story minutes), shown as a timestamp or a narrated beat. Wall-clock delays beyond ~10 s only in an explicit "phone mode" with notifications, off by default.
- **Register by persona:** lowercase, "u", trailing-off, emoji density, and ellipsis habits are per-character profile fields applied after generation, so they hold across long chats (drift, from phase 1) and never depend on the model.
- **Don't stall for its own sake.** Beyond Words rated hesitation-only worst; the courier should pair an indicator stall with a visible outcome (a message, or a message plus an edit).

### Gaps
- No academic source found for message bursts, double-texting, or read-receipt behaviour in chatbots; no human texting statistics (typical burst count, reply latency distribution, double-text rate).
- Templeton et al. (PNAS 2022) on response speed and perceived connection was not retrievable (403; PubMed search blocked by cookie wall); I have not cited numbers from it.
- Kalman and Rafaeli on online silence and chronemic expectancy violations: not retrieved.
- "Explaining the Wait" (how justifying delays affects trust, CUI 2024) — only the title was seen; findings not read. [ACM](https://dl.acm.org/doi/fullHtml/10.1145/3640794.3665550)
- The delay evidence is all from customer-service or VR settings, not companion roleplay, and the chatbot studies were short.
- No source on whether users of AI companions prefer simulated delays; expect some to want instant replies.

## 4. Initiative and proactivity: starting topics, asking back, boredom, interrupting, and group turn-taking

### Takeaway
Inner Thoughts (CHI 2025) is the strongest directly usable design: generate covert thoughts, rate them for motivation, speak only above a threshold, and let silence raise the score. It beat baselines with raters, and its "active contributor" setting beat both a chatty and a passive one. SillyTavern's talkativeness roll is the cheap baseline; conversation-analysis turn-taking (current speaker selects, else self-selection) is the principled structure. LLM next-speaker prediction is weak in self-selection turns.

### Cited Findings
- Inner Thoughts has five stages: trigger (on new message, or after 10 s of silence), retrieval (memory saliency with decay lambda = 0.95), thought formation (System 1 and System 2), thought evaluation (a 1-5 intrinsic-motivation score), participation. — [Liu et al., CHI 2025, arXiv HTML](https://arxiv.org/html/2501.00383)
- Motivation heuristics from a 24-participant formative study: relevance (77 mentions), information gap (33), balance (33), coherence (30), dynamics (30), expected impact (23), originality (16), urgency (14). — [Liu et al.](https://arxiv.org/html/2501.00383)
- The score aggregates five LLM ratings, with a silence-duration factor (lambda = 1.02 per unit of silence) so longer silence raises motivation. A threshold (`imThreshold`) sets the minimum motivation to speak, `system1Prob` sets a baseline chance of quick intuitive talk, and a separate `interruptThreshold` gates interrupting someone else's turn. — [Liu et al.](https://arxiv.org/html/2501.00383)
- Results: 50 simulated conversations per condition, 10 human raters, Inner Thoughts significantly higher on turn appropriateness, coherence, anthropomorphism, intelligence, engagement, initiative and adaptability, with an overall 82% preference. A fine-tuned GPT-3.5 next-speaker baseline reached 0.853 accuracy when a turn was allocated but only 0.156 in self-selection turns. — [Liu et al.](https://arxiv.org/html/2501.00383)
- User study (6 pairs, 12 participants, a Slack bot): "Active Contributor" (`system1Prob` 0.2, `imThreshold` 3.59) was most preferred by 6 of 12; "Selective Participant" (threshold 4.09) was least preferred by 7 of 12 as too passive; "Non-stop Chatter" (`system1Prob` 0.7) was identified as an AI 69.23% of the time and criticised as overwhelming. — [Liu et al.](https://arxiv.org/html/2501.00383)
- Murder Mystery Agents applies Sacks, Schegloff and Jefferson turn-taking (current speaker selects the next; otherwise self-selection from internal state) and reports fewer dialogue breakdowns and better information sharing. — [arXiv 2412.04937](https://arxiv.org/abs/2412.04937)
- A 2026 study reports LLMs zero-shot exceed supervised models at predicting addressee, turn change and next speaker in meetings. A longitudinal multi-party dataset paper notes that structural gains in speaker modelling "don't necessarily enhance dialogue naturalness." — [arXiv 2606.17542](https://arxiv.org/abs/2606.17542); [TIDES, arXiv 2608.01724](https://arxiv.org/abs/2608.01724)
- SillyTavern group chat: Natural Order (whole-word name mentions activate; the rest roll against Talkativeness, default 50%; if nobody activates, one is picked at random), List Order, Pooled Order (random among those who have not spoken since the last user message) and Manual. Auto-mode waits 5 s between turns. "Swap" loads only the speaker's card; "Join" merges all cards. — [SillyTavern docs](https://docs.sillytavern.app/usage/core-concepts/groupchats/)
- A community request to let the LLM choose the next speaker found name extraction from free text unreliable and was routed to STscript (`/gen`, `/trigger`, `/fuzzy`). — [SillyTavern discussion 4130](https://github.com/SillyTavern/SillyTavern/discussions/4130)
- Unguided proactivity can misdirect attention or cause harm; proactive systems need behavioural constraints on when to intervene. — [Kaur, Lyu, Shah, ICML 2026, arXiv 2602.15259](https://arxiv.org/abs/2602.15259)
- Nomi documents "Proactive Messaging" as messages sent when you have not responded in a while, framed as agency while you are away. Tolan (via a search summary of OpenAI's case study) rebuilds context every turn from a recent-message summary, persona card, vector-retrieved memories, tone guidance and app signals, and positions itself as a proactive friend that offers topics. — [Nomi Knowledge](https://nomi.ai/nomi-knowledge/); [OpenAI on Tolan](https://openai.com/index/tolan/) (page not fetched; secondary summary)
- Kataki's `turns.py` already explains speaker choice as picked, named, last-to-speak, quietest, retake, narrator or alone, and has a mind graph of what each speaker heard, recalled, believed and felt. — `D:/Kataki/engine/src/kataki/mind.py`, `D:/Kataki/engine/src/kataki/turns.py` (repo files read this session)
- Phase-1 basis for initiative: minds wander about 47% of waking time, and needs (SDT) and boredom should drive topic starts. — [Killingsworth and Gilbert 2010](https://www.science.org/doi/10.1126/science.1192439); [APA on SDT](https://www.apa.org/research-practice/conduct-research/self-determination-theory)

### Inferences
- **Initiative options:**

| Option | Mechanism | Extra calls and tokens | Latency | Works 7-14B | Evidence |
|---|---|---|---|---|---|
| Rules-only initiative (cheap default) | Per character: boredom counter, curiosity, unfinished-business queue; after each user message roll ask-back, topic-shift, or own-thread; suppress if the character just asked | 0 | none | yes | Indirect (Inner Thoughts heuristics; SDT); untested as rules |
| Silence timer with follow-up | After t of silence, courier sends a nudge if motivation exceeds threshold | 0 or 1 | none | yes | Product practice (Nomi); silence-raises-motivation term from Inner Thoughts |
| Inner-Thoughts-lite | One call: "what does {name} think right now, and how much do they want to say it, 1-5?" Read the rating (or expected value from logprobs) instead of five samples | 1 call, ~150-250 tokens out plus prompt | ~2-5 s local | plausible on 12-14B; 7B ratings will be noisy (not verified) | Strong for the full method (82% preference; user-study preference for the middle setting); the lite version is untested |
| Full Inner Thoughts | Five rating samples per thought, retrieval scoring, System 1 and 2 | 5+ calls per character per trigger | 10+ s local | poor locally; fine in cloud | As above |

- **1:1 initiative rules (default):** a character answers what was asked, then with a small probability adds one of: a question back (higher for high curiosity and warmth, zero if it asked last turn), a change of subject (probability grows with boredom, needs a transition marker), or something from its own off-screen thread (queue fed by Kataki's time-skip and mind data). Cap unprompted topic starts to about one per five to eight character turns to avoid the "non-stop chatter" failure (69% identified as AI in the Inner Thoughts study).
- **Group turn-taking default:** extend Natural Order in three moves, all in code. (1) Addressee resolution: names, the previous speaker's question, or "you" directed at someone select the next speaker with high probability (Sacks et al.: current speaker selects). (2) Otherwise self-selection: each character scores relevance (embedding similarity of the last message to the character's interests, using Kataki's `embed.py`), relationship to the last speaker, a silence term that rises with time since they last spoke, and a balance penalty for recent airtime, then speaks if above its own threshold (a talkativeness-derived per-character threshold). (3) Fallback to the quietest present character, as Kataki already does. This costs zero extra calls and improves on a bare coin flip.
- **Premium group option:** one short constrained call ("who speaks next, or nobody") with grammar-constrained decoding to an enum of present names, which removes the name-extraction failure the SillyTavern thread hit (llama.cpp grammar support is background knowledge to verify in Kataki's server integration). The fine-tuned 0.156 self-selection result suggests using the LLM as one input to the score, not the sole decision.
- **Interruptions in groups:** gate by an urgency threshold (Inner Thoughts `interruptThreshold`) and render as a short line landing between another character's bursts. Complex and rarely essential: leave for later.
- **Cost of group scenes locally:** each speaker is a separate serial generation. Use "swap" mode (only the speaker's card in context) to protect the 8 GB context budget, and allow at most 0-2 extra speakers after the addressed one.
- Behavioural constraint from Kaur et al.: proactive behaviour must respect user control; provide "quiet" and "chatty" settings per character and per scene.

### Gaps
- Inner Thoughts was tested with GPT models in Slack-style meetings and small samples (12 user-study participants); no test with 7-14B local models, and no test in one-to-one roleplay.
- No study found of what proactivity rate users of companion apps prefer.
- I could not fetch Replika, Kindroid or Character.AI documentation (403, or a loading screen), so their timing and group behaviour is unsourced.
- The claim that a "lite" motivation score works on small local models is untested.

## 5. Anti-slop: repeated phrases, over-structured replies, and style variation

### Takeaway
Slop is measurable (some patterns are over 1,000 times more frequent than in human text) and the cheap local answer is a sampler stack: Min-P, DRY and optionally XTC, plus a short banned list. Samplers fix vocabulary and looping but not over-structured replies or uniform rhythm, which need prompt structure and a per-turn style directive. Direct evidence that anti-slop raises perceived humanness is missing.

### Cited Findings
- Antislop (ICLR 2026): some patterns appear over 1,000 times more often than in human text. Its backtracking sampler suppresses 8,000+ patterns but cuts throughput 69-96% at 1k-8k banned entries; FTPO training cuts slop about 90% while keeping benchmark scores, and DPO degrades writing quality. — [arXiv 2510.15061](https://arxiv.org/abs/2510.15061)
- Min-p (ICLR 2025 oral): dynamic threshold scaled by the top token's probability, improving quality and diversity at higher temperature, with human evaluations preferring it, now in Hugging Face Transformers and vLLM. — [arXiv 2407.01082](https://arxiv.org/abs/2407.01082)
- DRY: penalty = multiplier x base^(n minus allowed_length); defaults multiplier 0 (off), base 1.75, allowed length 2, sequence breakers newline, colon, quote and asterisk so chat formatting does not trigger false penalties; adopted in llama.cpp and KoboldCPP. — [text-generation-webui PR 5677](https://github.com/oobabooga/text-generation-webui/pull/5677)
- XTC (Exclude Top Choices): with probability `xtc_probability` (default 0.5), removes all tokens above `xtc_threshold` (default 0.1) except the least likely one, and only acts when at least two tokens pass the threshold; the author suggests Min-P 0.02 and DRY multiplier 0.8 with other samplers off. — [text-generation-webui PR 6335](https://github.com/oobabooga/text-generation-webui/pull/6335)
- llama.cpp applies penalties, DRY, top_n_sigma, top_k, typ_p, top_p, min_p, XTC, then temperature; a community baseline is `--sampling-seq mx --min-p 0.02 --xtc-probability 0.5`. — [llama.cpp completion README](https://github.com/ggml-org/llama.cpp/blob/master/tools/completion/README.md) (as recorded in phase 1)
- ChatGPT models do not produce human-like lexical diversity, and classifiers easily separated GPT-3.5 news comments from human ones. — [arXiv 2508.00086](https://arxiv.org/abs/2508.00086); [arXiv 2312.13961](https://arxiv.org/abs/2312.13961)
- The first message and example dialogue set voice and length more than the description does (practitioner docs, phase 1). — [SillyTavern character design](https://docs.sillytavern.app/usage/core-concepts/characterdesign/)

### Inferences
- **Anti-slop options:**

| Option | Extra calls and tokens | Latency | Works 7-14B | Evidence for perceived humanness |
|---|---|---|---|---|
| Min-P 0.02-0.05 plus DRY 0.8/1.75/2 (breakers include newline and speaker separators) | 0 | none | yes | Sampler quality evidence (min-p human eval); not measured on humanness |
| Add XTC (p 0.5, thr 0.1) for chat register only | 0 | none | yes; can hurt factual slots, so off for planted-error or lore-recall turns | Anecdotal; none formal |
| Short banned-string list (tens, not thousands) | 0 | small | yes | Antislop shows suppression works; large lists cost throughput |
| Opener ledger: track first three words and closing phrases of the last ~10 messages; on repeat, regenerate with a logit bias against the repeated opener | 0 extra unless triggered, then 1 regeneration | rare +1 generation | yes | None; addresses a visible tell |
| Per-turn style directive (length class, answer-first or reaction-first or question-first, emoji yes/no, punctuation habit), about 30 tokens at depth | 0 | none | yes | Weak; consistent with lexical-diversity gap |
| Strip markdown, bullets and bold in chat register; never allow list replies in phone mode | 0 | none | yes | None found; obvious tell |
| Antislop FTPO-tuned or role-play-tuned model | 0 (model choice) | none | yes for 8-14B tunes | Strong on slop reduction; humanness not measured |

- Because thinking mode slightly hurt fidelity in Moral RolePlay and "reason then answer" pipelines double latency locally, avoid a "draft, then rewrite in human style" second pass as default; reserve it for premium/cloud.
- Reply-length variance and burst counts are better sampled by code than left to the model, since models settle into one length (drift, phase 1).

### Gaps
- No study found linking DRY/XTC/min-p to human ratings of conversational humanness.
- No verified 2026 recommendation for 8 GB-class models; sampler defaults are community guidance.
- Whether logit-bias on repeated openers works reliably through Kataki's llama-server and HF Inference Providers endpoints is untested.

## 6. What do existing products do (Replika, Nomi, Kindroid, Tolan, Friend, Sesame, others)?

### Takeaway
Documentation for the big companion apps is thin and mostly gated. What I could confirm is that Nomi ships proactive messages, Tolan is built around a proactive friend with memory and per-turn context rebuild, and Sesame does disfluency in voice but says it cannot model conversation structure. Message bursts, typing indicators and simulated latency in Replika, Nomi and Kindroid were not verifiable from sources.

### Cited Findings
- Nomi: "Proactive Messaging" sends messages if you have not responded in a while; the docs frame it as agency while you are away. — [Nomi Knowledge](https://nomi.ai/nomi-knowledge/)
- Tolan (Portola): voice-first companion; memory and character design were the two levers; context is rebuilt from scratch each turn from a recent summary, persona card, vector-retrieved memories, tone guidance and real-time app signals; it offers topics and reacts to uploaded photos (secondary summaries of OpenAI's case study). — [OpenAI](https://openai.com/index/tolan/); [Digital Watch summary](https://dig.watch/updates/meet-the-voice-first-ai-companion-with-personality)
- Sesame CSM: a 1B open-weights speech model released March 2025 under Apache 2.0, trained on about one million hours of audio; reported to produce disfluencies and self-corrections; Sesame notes it models text and speech content, not conversation structure, and points to future full-duplex models. Subjective tests: no clear preference between generated and real speech without context, original favoured with context. — [Learn Prompting](https://learnprompting.org/blog/sesame-conversational-speech-model); [Sesame](https://www.sesame.com/research/crossing_the_uncanny_valley_of_voice)
- SillyTavern is the open baseline for group chat (see question 4). — [SillyTavern docs](https://docs.sillytavern.app/usage/core-concepts/groupchats/)
- Open-source typing simulator with hesitation and self-editing: `jigglypuff96/human-like-typing-bot`. — [Beyond Words](https://arxiv.org/pdf/2510.08912)

### Inferences
- The best-supported transferable pattern across Tolan and Nomi is proactivity plus memory, which Kataki's memory and mind layers already provide; the missing piece is the courier and the initiative scorer.
- Sesame shows disfluency is a generation-layer feature in voice, but its own caveat (no conversation structure) argues for a separate timing and turn-taking layer, which is what the courier is.
- Since burst and latency behaviour of Replika, Nomi and Kindroid could not be verified, hand-test them before copying any pattern from memory.

### Gaps
- Replika, Kindroid, Friend and Character.AI: no documentation retrieved (403, loading screens, or not searched). Multi-message bursts, typing indicators, "left on read" and group behaviour in these products remain unverified here.
- No data on retention or satisfaction effects of these behaviours in any companion product.
- Tolan details come from secondary summaries because the OpenAI page returned 403.

## 7. Recommended design for Kataki: error and repair policy, message delivery engine, initiative rules, cheap default and premium mode

### Takeaway
Build three small code layers around the model instead of asking the model to be human: a slip planner (engine picks and remembers errors), a courier (splits, times and roughens the text and owns delays, seen states and follow-ups), and an initiative scorer (rules for 1:1, an extended Natural Order for groups). The cheap default adds no LLM calls. Premium adds one to three short calls for correction wording, motivation scoring and reflection.

### Cited Findings
- Corrected typos are the best-evidenced humanising error; uncorrected ones do nothing; the effect persists but shrinks when users know it is a bot. — [Imperfectly Human](https://www.escholarship.org/content/qt7863m2pf/qt7863m2pf_noSplash_77769d18410cf32e93ad9cacc46fc0dc.pdf)
- LLMs cannot reliably self-correct without external feedback. — [Huang et al.](https://arxiv.org/abs/2310.01798); [Kamoi et al.](https://arxiv.org/abs/2406.01297)
- Delays scaled to message complexity raise perceived humanness and satisfaction; a typing indicator softens waits; latency above about 4 s hurts in VR agents. — [Gnewuch et al.](https://aisel.aisnet.org/ecis2018_rp/113/); [IJHCI 2025](https://www.tandfonline.com/doi/full/10.1080/10447318.2025.2508915); [CUI 2025](https://arxiv.org/abs/2507.22352)
- The GPT-4.5 study's delay formula and persona are documented. — [Jones and Bergen](https://arxiv.org/html/2503.23674v1)
- Inner Thoughts (82% rater preference; middle proactivity setting preferred) and Natural Order (talkativeness default 50%) are the two group/initiative baselines. — [Liu et al.](https://arxiv.org/html/2501.00383); [SillyTavern docs](https://docs.sillytavern.app/usage/core-concepts/groupchats/)
- Antislop, Min-P, DRY and XTC are the local sampler stack; a large backtracking banlist costs 69-96% throughput. — [arXiv 2510.15061](https://arxiv.org/abs/2510.15061); [arXiv 2407.01082](https://arxiv.org/abs/2407.01082); [DRY](https://github.com/oobabooga/text-generation-webui/pull/5677); [XTC](https://github.com/oobabooga/text-generation-webui/pull/6335)

### Inferences
Everything below is design recommendation; rates and thresholds are tuning defaults, not sourced values.

**Realism setting (user-facing):** Off / Light / Natural / Messy, per app and overridable per character. Off skips everything below and keeps today's behaviour (streaming at reading speed via `pace.ts`). Every delay has a tap to skip. Story-scene prose is untouched; the courier applies only in "phone/text" scenes and to spoken lines inside scenes (as disfluency and narrated pauses, not typing indicators).

**A. Error and repair policy ("slip planner")**
1. Before each character turn, code rolls whether a slip is due. Base chance by Realism level (Light about 1 in 20, Natural 1 in 10-12, Messy 1 in 6), times persona factors (careless, tired, anxious, drunk up; precise, formal down), then capped: no slip in the first 2 messages of a chat, no more than one visible slip per five character messages, none while the topic is high-stakes or emotionally raw.
2. Choose the slip type by what is available: typo (display layer), hazy-memory detail (only from memories `activation.py` scores hazy), clause missed in the user's message, or wrong assumption. Never touch canon or hard-scored memories.
3. For content slips the engine writes `{slot, wrong, right, turn, kind}` to a `slips` row, injects the wrong value into the prompt as what the character remembers, and stores the truth. The prompt never says "make a mistake."
4. Repair schedule decided at the same time, weighted: 45% no repair yet (lets a later turn or the user catch it), 25% mid-message restart, 20% follow-up burst within seconds, 10% delayed correction 2-8 turns later or at the next mention of the topic. Typos: correct about 80% of the time, with a leave-uncorrected persona flag for sloppy characters (uncorrected typos give no humanness gain, so use them only for characterisation).
5. Correction text: templates per persona for typos and restarts (zero calls); one tiny call (~40 output tokens, given the card, the wrong line and the right value) for follow-up or delayed corrections in premium mode.
6. If the user challenges a claim, the character checks it against the `slips` and memory truth: owns real slips, holds the line on correct statements (sycophancy guard), and records having been corrected.
7. Store both the displayed text and the clean canonical text; the model's context uses the canonical clean text (so typos do not snowball), while UI shows the displayed version and the correction row.
8. Biases and mind-change: beliefs carry a stickiness value; the engine injects the anchor or first impression and requires accumulated evidence plus a face cost to update. Reflective mind-change (premium only) runs during time skips or every N turns: one call, reads the belief store and the recent lines, may emit a "been thinking" burst.

**B. Message delivery engine ("courier")**, code between model output and UI:
1. Start generation immediately and stream. Split on newline into 1-4 bubbles in phone mode (prompt example lines show the target rhythm; a first message in that rhythm anchors it).
2. Per bubble delay = read time (previous message characters x ~0.03 s) + typing time (characters x persona seconds-per-char, default well below the Turing test's 0.3 s so long messages do not drag) + a right-skewed think term, then multiplied by mood (arousal, avoidance) and effort. Release at max(0, delay minus elapsed generation time), which hides model latency when the local model is slow.
3. Show a typing indicator during typing time. If a burst sequence includes a repair, show a type-delete-retype stall only when a visible edit follows.
4. Apply persona register after generation: lowercase, dropped final period, "u", emoji density, elongation ("sooo"), typos from a keyboard-adjacent, swap or drop model at the slip planner's chosen spots.
5. Availability and states: a per-character schedule and mood set the reply latency multiplier and a "seen" state (read-without-reply). Long silences are story-clock jumps in scene mode; real-time waits beyond ~10 s only in optional phone mode with a notification.
6. Double-text: the initiative scorer (below) can queue a follow-up burst after a silence; the courier owns the timer and cancels it if the user types.
7. Length control: sample a length class per turn (one word, short, medium, long) conditioned on mood and the user's message length (mirroring, weak evidence), and inject one line at depth.
8. Sampler stack for chat register: Min-P 0.02-0.05, DRY 0.8/1.75/2 with breakers, optional XTC 0.5/0.1 (off for lore and slip turns), a short banned-string list, and the opener ledger with one regeneration on repeats. Markdown and bullets stripped in phone mode.

**C. Initiative rules**
- *1:1 (default, rules only):* boredom counter (+1 per low-novelty turn), curiosity and warmth from the character card, an unfinished-business queue fed by the mind graph and time skips. After each user message: answer first, then roll ask-back, topic shift, or own-thread within the cap (about one unprompted topic per 5-8 character turns). Silence longer than a persona threshold can queue a follow-up (double-text) if motivation exceeds a threshold that varies by attachment style.
- *Group (default, zero calls):* (1) addressee resolution selects the next speaker (names, replied-to speaker, questions); (2) else self-selection by relevance (embedding), relationship to the last speaker, silence term, balance penalty, against a per-character threshold set from talkativeness; (3) fallback to the quietest character. Up to two extra speakers per user turn with falling probability; swap mode keeps context small.
- *Premium:* Inner-Thoughts-lite (one rating call per candidate speaker per trigger, run only for the top 1-2 candidates from the rule scorer), a constrained "who next" call for groups, and interruption gating with an urgency threshold.

**Cost and latency summary (assume ~30-50 generation tokens per second for a 12B Q4 model on 8 GB; measure in Kataki's llama-server):**

| Mode | Extra LLM calls per character turn | Extra latency (local) | Contents |
|---|---|---|---|
| Cheap default | 0 | none (delay hidden inside generation time) | Slip planner, courier, rule-based initiative, sampler stack, opener ledger |
| Premium | 1-3 short calls (~40-250 tokens each) | roughly 1-8 s | Adds correction-wording call, Inner-Thoughts-lite rating, "who next" call, reflective mind-change on time skips; prefer 12-14B or cloud for the rating and reflection calls |
| Avoid | 5-sample scoring, reasoning-mode voice, large backtracking banlists | 10+ s or 69-96% throughput loss | Not worth it on 8 GB |

**Evaluation plan:** add a slip-rate and repair-rate counter, a "realism" toggle for A/B by users, and extend the phase-1 probe set with three scenes (forgetful character, texting burst, group tangent). Compare the same model with and without the courier and slip planner; judge blind for humanness and for enjoyment, and log the fraction of slips users noticed.

### Gaps
- None of the recommended rates, thresholds and mixes come from a study; they are starting points to tune.
- The 7-14B behaviour of one-line-per-bubble prompting, Inner-Thoughts-lite ratings and the tiny correction call is untested; run the probe set before shipping the premium tier.
- The evidence base for humanness is dominated by customer-service, Turing-test and VR studies with short interactions; whether companion-roleplay users, who know it is an AI, enjoy these behaviours more is unmeasured.
- Interaction with other Kataki layers (memory receipts, mind graph, time skips) needs an engine-level design pass: where `slips` rows live and how they appear in Backstage.
