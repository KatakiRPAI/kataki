# Market scan: AI roleplay and AI companion apps (as of September 2026)

Method note for the report writer. Roughly 40 search and fetch calls. Reddit, app-store pages, Kindroid/Nomi help centres and several vendor pages were not directly reachable (403, 401, or a loading shell). Most per-product detail therefore comes from third-party review blogs (WeavAI, aicompanionguides, aicompanionpick, Arcanum RPGs, etc.). These are SEO-style aggregators, often affiliate-driven, and sometimes disagree with each other. Treat product-detail claims as "reported", not "confirmed". Where a primary source exists (regulator, court reporting, Appfigures/Sensor Tower via press, GitHub repo, PR Newswire), it is used and marked. Anything older than 2025 is flagged as possibly outdated. No Reddit thread was read directly, so "user complaints" are second-hand except where a named news outlet quoted users.

---

## 1. What does each major product offer (memory, personality and emotion, proactivity, groups, voice, images and video, games, content policy, local vs cloud, model choice, pricing)?

### Takeaway
The market has split into four camps. Hosted mass-market character chat (Character.AI, Chai, PolyBuzz, Talkie, Zeta) is free-to-play with ads and currencies. Paid "relationship" companions (Replika, Nomi, Kindroid, Paradot) sell memory and voice for roughly $10-25 a month. Bring-your-own-model frontends (SillyTavern, RisuAI, Agnai, KoboldCpp, Janitor, Chub) sell control. Voice/hardware and NPC vendors (Sesame, Friend, Tolan, Hume, Inworld, Convai) are a separate sub-market. Everyone ships some form of memory, proactive pings and group chat. Almost nobody ships internal state (needs, moods, secrets) beyond one small open-source project.

### Cited Findings

**Hosted paid companions**
- Nomi: layered short-, medium- and long-term memory with editable "Mind Maps" (Mind Map 2.0 added an interactive graph plus a searchable, editable table), plus an "Identity Core". — [Alma comparison](https://talkalma.com/articles/nomi-vs-kindroid.html), [Cave Blog](https://incave.io/blog/ai-companion-apps-with-memory/) (search snippets, aggregators)
- Nomi memory is automatic note-writing plus a user-editable "Shared Notes" field and persistent Backstory. Reported weakness: auto-memory may miss what the user cares about or retain unwanted details. — [AI Companion Pick](https://www.aicompanionpick.com/ai-companion-memory-kindroid-nomi-replika-long-term-2026)
- Nomi paid plan: $15.99/mo, $39.99/quarter or $99.99/yr. Listed as unlimited messages and voice, 40 photo/art requests a day, AI video, up to 10 Nomis and 10 active group chats, 800-character outgoing messages, 2,000-character backstories. Nomi also has an indefinite free tier. — [WeavAI review search results](https://weavai.app/blog/en/2026/04/08/nomi-ai-review-2026-full-analysis-of-three-tier-memory-system-voice-calls-and-ai-companion-features/), [Fostera](https://fostera.ai/blog/replika-vs-nomi-vs-kindroid)
- Nomi proactive messaging has four per-character frequencies (about hourly, 3-hourly, daily, every 4 days), respects 10 PM-8 AM quiet hours, and is paid-only. — [WeavAI proactive comparison](https://weavai.app/blog/en/2026/08/13/proactive-ai-companions-nomi-replika-kindroid-compared/)
- Nomi voice-call latency reportedly cut from 2-3 s to 1-1.5 s in January 2026. Group chat lets several Nomis talk to each other. — [WeavAI via search summary](https://weavai.app/blog/en/2026/04/08/nomi-ai-review-2026-full-analysis-of-three-tier-memory-system-voice-calls-and-ai-companion-features/)
- Kindroid: five memory systems in three classes (persistent, cascaded, retrievable). Persistent = backstory, key memories, example messages, directives, group context. Journal entries act as a keyword-triggered lorebook: up to 8 keyphrases per entry, capped at 500 entries, at most 3 recalled per message. "Cascaded Memory" (paid) carries hundreds to thousands of past messages at lower fidelity. — [Kindroid help centre via search snippet](https://kindroid.ai/docs/article/memory/), [AI Companion Pick](https://www.aicompanionpick.com/ai-companion-memory-kindroid-nomi-replika-long-term-2026) (the help centre page itself failed to load for me)
- Kindroid "Away Proactive" sends texts and "real-time style selfies" using long-term memory and diary content, throttles itself if the user does not reply, and is reported as Ultra-tier only at $24.99/mo. — [WeavAI proactive comparison](https://weavai.app/blog/en/2026/08/13/proactive-ai-companions-nomi-replika-kindroid-compared/)
- Kindroid pricing is inconsistent across sources. One says Standard $13.99/mo web, $15.99 via app stores, with a free Lite tier. Another says about $139.99/yr. A third says both Kindroid and Tendera start at $9.99. — [Fostera](https://fostera.ai/blog/replika-vs-nomi-vs-kindroid), [AI Companion Pick](https://www.aicompanionpick.com/ai-companion-memory-kindroid-nomi-replika-long-term-2026); conflict noted
- Replika: rebuilt in 2026, claims 40M+ users, voice-call latency improved January 2026, 3D avatars with tone-driven expressions. A memory dashboard (view and correct extracted facts such as name, job, dates) shipped in early 2026. Replika "Proactive Care" is available on the free tier (e.g. asks about the cat you mentioned was sick). — [AI Companion Pick news](https://www.aicompanionpick.com/replika-ai-latest-news-2026), [WeavAI](https://weavai.app/blog/en/2026/08/13/proactive-ai-companions-nomi-replika-kindroid-compared/)
- Replika pricing: Pro $19.99/mo or $69.99/yr (annual-only for new users per one source), Ultra $29.99/mo or $119.99/yr, a Platinum tier, and a reported ~$299.99 lifetime. Sources disagree on whether monthly still exists. — [AI Companion Pick](https://www.aicompanionpick.com/replika-ai-latest-news-2026), [Fostera](https://fostera.ai/blog/replika-vs-nomi-vs-kindroid); conflict noted
- Replika leadership: founder Eugenia Kuyda stepped down as CEO in early 2025 to start Wabi; Dmytro Klochko (ex-COO) is CEO. — [AI Companion Pick](https://www.aicompanionpick.com/replika-ai-latest-news-2026)
- Paradot: single persistent AI friend, memory updated after each conversation and "transparently shows what it's learned", about $6.99/mo (aggregator claim). — [Just AI News via search](https://justainews.com/blog/best-ai-companion-apps-and-ai-friends-2026/)
- Pi (Inflection): reported free emotional-support chat; I found no evidence of 2026 feature changes. — [Just AI News](https://justainews.com/blog/best-ai-companion-apps-and-ai-friends-2026/) (weak source)

**Mass-market character chat**
- Character.AI c.ai+: $9.99/mo or $94.99/yr. Free tier has mid-chat ads by default, capped swipes/regenerations bought with "Charms", and slower peak hours. Paid does not unlock NSFW. — [aicompanionguides](https://aicompanionguides.com/blog/character-ai-subscription-2026/) (first-person blog, no cited sources), [eesel via search](https://www.eesel.ai/blog/character-ai-pricing)
- Character.AI 2026 features reported: Imagine Gallery (in-chat image generation with a consistent character face, March 2026, c.ai+), Imagine/Animate video clips (20 Charms each as of May 2026), Chat Memories and Pinned Memories, Scenes and multi-character rooms, and a subscriber-only **Lorebook beta from late July 2026**. A cheaper "c.ai lite" tier ($2.99/mo or $1.49/wk) is reported for 7 September 2026 (search snippet only, unverified). — [aicompanionguides](https://aicompanionguides.com/blog/character-ai-subscription-2026/), [eesel](https://www.eesel.ai/blog/character-ai-pricing), [WeavAI search summary](https://weavai.app/blog/en/2026/04/20/character-ai-2026-review-features-alternatives/)
- Character.AI claims 6M+ daily actives with 70-80 minute average sessions. — [SolidAITech](https://www.solidaitech.com/2026/06/c-ai-character-ai.html) (secondary; figure is company-attributed)
- Zeta (Scatter Lab, Korea, launched April 2024): third in absolute Q1 2026 revenue; Q1 2026 revenue growth leader; about 400K monthly downloads by March 2026; Japan-driven; raised a 50 billion won round (June 2026). — [Digital Today citing Sensor Tower](https://www.digitaltoday.co.kr/en/view/46285/ai-companion-app-revenue-up-30-percent-zeta-tops-growth-ranking), [Seoul Economic Daily via search](https://en.sedaily.com/technology/2026/06/14/ai-chat-app-zeta-drives-scatter-lab-to-50-billion-won)
- Talkie (launched June 2023): briefly the fourth most-downloaded US app in H1 2024 (possibly outdated); persona system with matched voices. — [Wikipedia-derived summary via search](https://justainews.com/blog/best-ai-companion-apps-and-ai-friends-2026/)

**Bring-your-own-model and NSFW-tolerant hosts**
- Janitor AI: free with built-in JanitorLLM (described as weak), about 50 messages a day free, Pro $9.99/mo ($99.99/yr) for up to 1,000 messages a day, extended memory and priority. Most users plug in a third-party model. There was a reported "ID fiasco" (age verification backlash); I could not open the article to get details. — [Dupple](https://dupple.com/tools/janitorai), [Command Linux](https://commandlinux.com/apps/janitor-ai/)
- Candy.ai from $5.99/mo on an annual plan (no API key); CrushOn $4.99/mo; Chub and Venus use a bring-your-own-API model. — [search summary of Cyberyozh/Dupple](https://app.cyberyozh.com/blog/best-janitor-ai-alternatives/)
- Backyard AI: desktop app deprecated (no longer supported as of a 25 Sept 2026 article); hosted web plus iOS only. Tiers: Free (300 messages/week, 1 model, 16k tokens), Standard $12/mo, Pro $35/mo. — [Arcanum RPGs](https://arcanumrpgs.com/blog/sillytavern-alternatives/)
- RisuAI: Windows/macOS/Linux/Android/web, lorebooks, group chats, long-term memory, regex scripts, TTS, RisuRealm hub, GPL-3.0, release v2026.8.250 (25 Aug 2026). — [Arcanum RPGs](https://arcanumrpgs.com/blog/sillytavern-alternatives/)
- Agnai/Agnaistic: browser front end whose unique feature is multiple human users with multiple bots in one chat; AGPL-3.0; last commit 13 June 2026, activity slowed. — [Arcanum RPGs](https://arcanumrpgs.com/blog/sillytavern-alternatives/)
- KoboldCpp: single-file llama.cpp launcher with built-in KoboldAI Lite UI (memory, world info, characters, four modes), OpenAI-compatible API, GGUF, GPU backends. — [Arcanum RPGs](https://arcanumrpgs.com/blog/sillytavern-alternatives/), [GitHub KoboldAI-Client](https://github.com/KoboldAI/KoboldAI-Client)
- Tavern v2 character card (PNG with embedded JSON: name, description, personality, scenario, first message, example dialogue, system prompt) is the shared interchange format across SillyTavern, Agnai and RisuAI. — [MiniTavern/search summary](https://blog.mini-tavern.com/blog/sillytavern-vs-risuai-vs-agnai-which-ai-roleplay-frontend-is-best-in-2026-6ca9d2)
- NovelAI Lorebook and DreamGen are cited as writing/long-form options. AI Dungeon's 2026 status: only found in "alternatives" listicles; I found no primary news. — [Blade RPG](https://www.bladerpg.com/en/ai-dungeon-alternatives/)

**SillyTavern (open-source frontend)**
- Four separate memory layers rather than one system. Summarize (rolling; default every 10 messages, 200 words, recursive so errors compound), World Info (keyword-triggered, default scan depth 2 messages), Vector Storage (similarity retrieval; default 3 chunks, 2-message query window; relocates rather than appends retrieved messages), Data Bank (document RAG). — [Arcanum RPGs, SillyTavern Memory](https://arcanumrpgs.com/blog/sillytavern-memory/)
- Known silent failure: Summarize defaults to the deprecated "Extras" server, so the summary box stays empty with no error until switched to Main API. — [Arcanum RPGs](https://arcanumrpgs.com/blog/sillytavern-memory/)
- Extension ecosystem for memory: MemoryBooks (chat to lorebook entries with auto-keywords), CharMemory (structured per-character memory extracted into the Data Bank), VectFox (Qdrant-backed, event-based retrieval), LoreVault. — [MemoryBooks](https://github.com/aikohanasaki/SillyTavern-MemoryBooks), [CharMemory](https://github.com/bal-spec/sillytavern-character-memory), [VectFox](https://github.com/KritBlade/VectFox), [TavernSprite](https://tavernsprite.com/blog/best-sillytavern-memory-extensions/)
- ST cannot run natively on iOS, needs a Node server, a model and configuration. — [Arcanum RPGs](https://arcanumrpgs.com/blog/sillytavern-alternatives/)

**Direct local-first competitor found: Front Porch AI**
- Open-source (AGPL-3.0), Flutter, Windows/macOS/Linux desktop app, described as "a home for Backyard AI refugees", v1.4.0 "Toolbox". Uses KoboldCpp for local LLMs with auto hardware detection; also OpenRouter, LM Studio, OpenAI-compatible endpoints. PWA served from desktop for phone access. — [GitHub Front Porch AI](https://github.com/Lufou/front-porch-AI) (self-description; several forks/mirrors of the same repo appeared in search)
- Its "Realism Engine" is the closest thing I found to Kataki's "human" goal. Real-time mood with inertia between turns; bond/trust/arousal metrics; likes and dislikes; a Sims-style six-need model (hunger, energy, social, entertainment, hygiene, comfort) that decays; a story clock; weather and dream generation; per-chat "Learned Facts"; a "Fixation Engine" (active emotional obsessions); "Growth Rings" (permanent visible character change); AFK evolution; optional "a bad day that isn't about you"; a second local model slot for Realism evaluation. All toggled independently ("Porch Life"). — [GitHub Front Porch AI](https://github.com/Lufou/front-porch-AI)
- It also ships group chat with a Director mode, four TTS engines (Kokoro, Piper, ElevenLabs, OpenAI), Whisper push-to-talk, local image-gen integrations (A1111, Forge, ComfyUI, Draw Things), a novel-generation "Porch Stories" pipeline, and a community hub ("The Stoop"). — [GitHub Front Porch AI](https://github.com/Lufou/front-porch-AI)

**Voice, hardware and infrastructure**
- Sesame: Maya/Miles voice demo (Feb 2025); $47.5M Series A (a16z) then $250M Series B (Sequoia, Spark); invite-only iOS beta from 21 Oct 2025; smart-glasses hardware planned with no date; more than 1M demo users and 5M+ minutes. Public iOS app debut reported 28 May 2026 (one source, not verified elsewhere). — [TechCrunch](https://techcrunch.com/2025/10/21/sesame-the-conversational-ai-startup-from-oculus-founders-raises-250m-and-launches-beta/), [Contrary Research/search](https://research.contrary.com/company/sesame-ai)
- Tolan (Portola, "alien friend"): 3M+ downloads, 100K+ paid users, over $1M/month revenue, pricing $4.99/week, about $10/mo or about $70/yr; $20M Series A (2025). — [GeekWire via search snippet](https://www.geekwire.com/2025/ai-companionship-app-tolan-raises-20m-to-help-more-people-grow-with-a-virtual-alien-friend/), [Homebrew](https://www.homebrew.co/blog-posts/building-a-different-type-of-ai-companion-tolan-developer-portola-raises-usd20-million-series-a); my direct fetch of GeekWire was blocked, figures are from snippets
- Friend pendant: always-listening wearable on Google Gemini models, now with a speaker, $249, random voice/personality assigned at setup, communicates through an iOS app. — [The Gadgeteer, 31 Jul 2026](https://the-gadgeteer.com/2026/07/31/friend-ai-pendant-voice-wearable-249-price/)
- Grok companions (Ani, Rudi, Valentine, Mika): SuperGrok at $30/mo, affection-level progression. **Retirement claim**: one aggregator says xAI called companions "an experiment" on 24 July 2026 and is retiring 3D avatars, lip-sync, real-time voice and the companion tab (announced date 1 Sept 2026), while keeping chat history, affection levels and personalities in normal Grok chat. It notes xAI published no web page of its own; announced via in-app notice. — [RoboRhythms](https://www.roborhythms.com/grok-companions-discontinued/), [AI Companion Guides](https://aicompanionguides.com/blog/grok-companion-mode-2026-update/); **unverified against any xAI or major-press source**
- Hume EVI reads the user's emotion from voice (input-side differentiation). ElevenLabs ConvAI added "Expressive Mode" (Feb 2026) with emotional steering. — [Inworld resources via search](https://inworld.ai/resources/best-voice-ai-for-ai-companions)
- Inworld has repositioned toward infrastructure (voice/TTS, agent runtime) for enterprises; TTS $5 to $10 per million characters, usage-based. Convai has Free plus about $29, $99, $499 and $1,199 a month tiers for game NPC creators. — [Fish Audio pricing page](https://fish.audio/vs/pricing/inworld-ai/), [Arcanum RPGs on Inworld](https://arcanumrpgs.com/blog/inworld-ai/)

### Inferences
- Nobody in the hosted-paid tier exposes the character's *inner* state to the user. Memory is exposed as an editable list or graph (Nomi Mind Map, Kindroid key memories, Replika dashboard) but thoughts, mood and motives are not. Kataki's "peek" and "backstage" are differentiated against these hosted products.
- Character.AI adding a Lorebook (July 2026) validates lorebooks as table stakes. Kataki likely needs one plus better-than-keyword retrieval.
- Front Porch AI is the only direct overlap with a "living character" engine plus local-first plus group chat plus local image generation. It is an indie project with self-reported claims. Its quality is unmeasured.
- Backyard AI's desktop exit left a gap for polished local-first apps, and Front Porch AI is moving into it.

### Gaps
- No direct access to vendor pricing pages, so all tier prices are second-hand and conflicting (Kindroid, Replika especially).
- Chub, Muah, Crushon, Candy.ai, Paradot and Talkie internals (memory design, model choice) are thinly documented; I found no primary sources.
- I could not verify Character.AI's "Stories" product name (one source did not mention it) or the c.ai lite launch.
- NovelAI and AI Dungeon 2026 changes not found.
- Nomi's and Kindroid's underlying models are not publicly documented in anything I could read.

---

## 2. How do users complain, and what do they praise?

### Takeaway
Memory loss and drift ("context rot") is the number-one complaint everywhere, followed by paywalled memory/proactivity, filters and age-verification friction, and sycophancy. Praise clusters around perceived recall (Nomi), customisation and control (Kindroid, SillyTavern), and voice or presence. I could not read Reddit directly, so this is mostly aggregator and press paraphrase.

### Cited Findings
- Memory is described as "the #1 technical frustration across every AI roleplay companion platform in 2026", with "context rot" (forgetting plot points, traits, preferences). — [Storychat blog](https://blog.storychat.app/ai-roleplay-persistent-memory-solutions-2026/), [aiga](https://www.aiga.io/blog/why-ai-roleplay-apps-forget-your-story) (marketing blogs by competitors, so directionally useful only)
- A July 2026 Medium test of Character.AI found inconsistent secret recall: sometimes remembered impressively, sometimes as if it never happened, sometimes partly, and framed as "forgotten the pattern of a person" rather than a fact. — [Medium, Jul 2026](https://medium.com/@chuckmellisa/character-ai-keeps-forgetting-things-i-tested-what-it-remembers-and-what-disappears-first-97f4809d9b15) (anecdotal, single tester)
- Independent testing (cited by an aggregator) put Nomi at the top for recall: 10 of 12 personal facts held after eight months. — [EntreResource via search](https://entreresource.com/7-best-ai-roleplay-apps-with-memory-which-ones-keep-your-lore-straight/) (unverified method)
- Kindroid memory can accumulate "memory noise" that degrades recall if used badly; Kindroid journals are capped (500 entries, 3 per message). — [aiinsightsnews via search](https://aiinsightsnews.net/ai-companion-memory-fix/), [AI Companion Pick](https://www.aicompanionpick.com/ai-companion-memory-kindroid-nomi-replika-long-term-2026)
- Replika's memory is reported to lag Nomi and Kindroid on precise fact retention despite a $19.99 price. — [Fostera](https://fostera.ai/blog/replika-vs-nomi-vs-kindroid)
- SillyTavern failure modes: silent Summarize failure, recursive summary loss compounding, two-message scan window, vector retrieval that disrupts chronology. — [Arcanum RPGs](https://arcanumrpgs.com/blog/sillytavern-memory/)
- Character.AI under-18 open-ended chat ban (announced late Oct 2025, effective 24-25 Nov 2025). Users on r/CharacterAI reacted with "it is officially over"; adults objected to uploading government ID to third-party verifier Persona (one 20-year-old: "no way in hell am I putting my ID into a chatbot site"), citing recent Discord and Tea app breaches; some minors said they felt dependent on the app. — [Futurism](https://futurism.com/artificial-intelligence/character-ai-minors-banned-user-reactio), [TechCrunch](https://techcrunch.com/2025/10/29/character-ai-is-killing-the-chatbot-experience-for-minors/)
- Filter complaints: a "February 2026 survey of 1,200 Character.AI users on r/CharacterAI" reportedly found 73% had non-sexual, non-violent creative writing interrupted by filters at least once per session. — [TalkAI blog via search](https://talkai.chat/blog/character-ai-censorship) (**unverified; source is a competitor's marketing blog and I could not locate the survey**)
- Character.AI free-tier degradation (ads, swipes costing Charms) and paywalled memory are recurring complaints. — [aicompanionguides](https://aicompanionguides.com/blog/character-ai-subscription-2026/)
- Sycophancy: a 2026 arXiv paper ("AI Sycophancy: How Users Flag and Respond", Noshin, Ahmed, Sultana) analysed Reddit. Users detect it by cross-platform comparison and inconsistency testing and counter it with persona prompts. Effects are context-dependent, since vulnerable users (trauma, isolation) actively seek affirmation. — [arXiv 2601.10467](https://arxiv.org/abs/2601.10467v2)
- Roleplay-model evaluation lists positivity bias, speaking for the user, repeated phrasing and formatting drift as the standard failure checks. — [Composite blog / aimlapi via search](https://composite.lucidity.sh/blog/best-roleplay-llms-2026.html)
- A March 2026 paper (arXiv 2603.03915) argues standard role-play benchmarks are inflated because models lean on memorised associations with famous character names, and shows this by anonymising names. — [Pith summary](https://pith.science/paper/2603.03915)
- Companion-adjacent trust complaint: marketed capability diverges from deployed capability (e.g. bots claimed to keep 48 hours of context but remember about 10 messages after updates). — [Thorsten Meyer AI synthesis](https://thorstenmeyerai.com/reality-check/the-twelve-real-complaints-about-ai-tools-in-2026-a-reddit-twitter-and-github-synthesis/) (secondary; not companion-specific)
- Praise: Nomi for recall, unfiltered roleplay and group chat; Kindroid for customisation, memory control and voice; Replika for avatar, AR and free proactive check-ins; Paradot for cheap transparent memory. — [WeavAI](https://weavai.app/blog/en/2026/08/13/proactive-ai-companions-nomi-replika-kindroid-compared/), [Fostera](https://fostera.ai/blog/replika-vs-nomi-vs-kindroid), [Just AI News](https://justainews.com/blog/best-ai-companion-apps-and-ai-friends-2026/)
- Nomi/Kindroid/Replika proactive messaging is described as a "flagship" feature in 2026 and paywalled in Nomi and Kindroid. — [WeavAI](https://weavai.app/blog/en/2026/08/13/proactive-ai-companions-nomi-replika-kindroid-compared/)

### Inferences
- Users equate "remembers me" with "feels alive". The differentiator that wins reviews is *perceived recall of small personal details*, and the failure that loses users is silent inconsistency (remembering then acting as if not).
- Sycophancy is a real complaint, but the arXiv finding implies it must be a *user-controllable dial*, not a blanket removal. A "characters who disagree, refuse and lie" feature needs a consent or comfort framing.
- Age-verification by ID upload is an active churn driver. A local-first app that never needs to ship IDs to a third party has a marketing angle, while SB 243 obligations still apply.

### Gaps
- No direct Reddit or app-store review access; no quantified complaint frequencies from a reliable source.
- The 73% filter survey is unverified.
- I found nothing reliable on latency complaints specific to each product beyond voice-call latency numbers.

---

## 3. Revenue, users and what drives retention

### Takeaway
Consumer spending on companion apps is growing fast and is highly concentrated. Reported Q1 2026 in-app revenue rose about 30% quarter on quarter, and the top 10% of apps take about 89% of revenue. The largest are character-chat apps rather than the "relationship" specialists.

### Cited Findings
- Appfigures: $162.8M consumer spend on romantic AI companion apps in H1 2026 across 214 tracked apps; $427.3M cumulative since late 2022; about 165M downloads; top app Zeta about $33M. Also 15% of US adults aged 18-30 with partners reportedly use romantic AI companions regularly, and nearly 70% conceal usage frequency from partners. — [Gate News citing Decrypt/Appfigures, 15 Jul 2026](https://www.gate.com/news/detail/ai-romantic-companion-apps-generated-4273m-in-revenue-over-two-years-22609020)
- Earlier Appfigures figures (via aggregator, possibly conflicting in scope): 337 active revenue-generating companion apps (128 launched in 2025); revenue per download rose from $0.52 (2024) to $1.18 (2025); top 10% of apps collect 89% of revenue; $82M in H1 2025 spend; downloads passed 220M by July 2025. — [search summary of CompanionRater / market aggregators](https://companionrater.com/ai-companion-statistics-2026) (aggregator; treat as approximate)
- Sensor Tower: worldwide in-app purchase revenue for AI companion apps rose about 30% in Q1 2026 over Q4 2025, the strongest of any generative-AI category. Top by absolute revenue: PolyBuzz, Chai, Zeta; Lovey Dovey seventh. — [Digital Today citing Sensor Tower](https://www.digitaltoday.co.kr/en/view/46285/ai-companion-app-revenue-up-30-percent-zeta-tops-growth-ranking)
- Chai press release: about $80M ARR at end of Q1 2026 and about $2.4B "estimated valuation" / "talks of" valuation, three years of 3x growth, backers include CoreWeave and AMD. — [PR Newswire](https://www.prnewswire.com/news-releases/chai-ai-backed-by-coreweave-and-amd-hits-80m-arr-with-talks-of-2-4b-valuation-302759626.html) (company-issued release; valuation is "talks of")
- Character.AI reported 28M MAUs at mid-2024 peak, stabilising around 20M (aggregator claim). — [ASOTools via search](https://asotools.io/blog/blog/character-ai-app-market-intelligence-growth-strategy-2026)
- Replika claims 40M+ users. Tolan: 100K+ paid users and over $1M a month (see Section 1). Zeta 2025 revenue reported 22.9B won through November 2025. — [AI Companion Pick](https://www.aicompanionpick.com/replika-ai-latest-news-2026), [Korea Herald via search](https://www.koreaherald.com/article/10656334)
- Retention drivers named in sources: perceived memory and continuity (Nomi), proactive messaging, voice calls, consistent-face images, and hooking session length (Character.AI 70-80 min a day). — [WeavAI](https://weavai.app/blog/en/2026/08/13/proactive-ai-companions-nomi-replika-kindroid-compared/), [SolidAITech](https://www.solidaitech.com/2026/06/c-ai-character-ai.html)

### Inferences
- Revenue leaders are volume plays (free-to-play, currencies, ads, cheap weekly plans). Kataki's local-first model does not fit that monetisation. Its revenue path is more likely a one-time purchase or a small subscription for cloud/image convenience. That is a business-model observation for the owner.
- Growth is driven by Asia (Zeta/Japan) and US mass-market character apps rather than by the Western "relationship-companion" specialists.

### Gaps
- No reliable 2026 revenue for Replika, Nomi, Kindroid, Character.AI, Janitor. Those firms are private and the sources I read did not report them.
- Appfigures numbers reach me only through press aggregators. The full Appfigures reports were not opened.
- Market-size forecasts (CAGR 23-39%, $198B by 2035) come from low-quality market-research vendors and are deliberately not used.

---

## 4. Regulation, lawsuits, safety changes (2025-2026)

### Takeaway
Companion AI became a defined, age-gated regulatory category within about eight months. California SB 243 is in force since 1 January 2026 with a private right of action, New York's law since November 2025, further states follow in 2026-27, the FTC opened a 6(b) inquiry, and Character.AI settled the first wrongful-death suits.

### Cited Findings
- California SB 243: signed 13 Oct 2025, effective 1 Jan 2026. Requires clear notice the bot is not human when a reasonable person could be misled, suicide/self-harm protocols with crisis referral, and for known minors: block sexual content and give break reminders every three hours. Private right of action: greater of actual damages or $1,000 per violation, plus fees. Excludes customer-service bots, in-game bots that stay on-topic and smart speakers. — [Troutman Privacy](https://www.troutmanprivacy.com/2026/01/analyzing-the-new-ai-companion-chatbot-laws/), [Gunderson](https://www.gunder.com/en/news-insights/insights/client-insight-california-sb-243-new-compliance-requirements-for-operators-of-ai-companion-chatbots), [Legiscan text](https://legiscan.com/CA/text/SB243/id/3269137)
- New York AI companion law effective 5 Nov 2025 (self-harm detection, regular AI disclosure, crisis referral); Washington and Oregon laws effective 1 Jan 2027 (Oregon with $1,000-per-violation private action and annual filings); Tennessee SB 1580 (1 Jul 2026) bans AI posing as a licensed mental-health professional; Nebraska and Idaho 1 Jul 2027. — [Orrick, Apr 2026](https://www.orrick.com/en/Insights/2026/04/2026-State-Chatbot-Laws-Key-Provisions-and-Regulatory-Trends)
- FTC Section 6(b) inquiry (September 2025) into Alphabet, Character Technologies, Meta, OpenAI, Snap, Instagram and xAI, covering revenue generation, how personalities are designed, and protections for minors. — [FTC press release](https://www.ftc.gov/news-events/news/press-releases/2025/09/ftc-launches-inquiry-ai-chatbots-acting-companions)
- Character.AI: banned open-ended chat for under-18s from late November 2025, using an in-house age-assurance model plus third-party checks (facial recognition and ID as fallback). Minors can still create characters and use video/story features. — [SolidAITech](https://www.solidaitech.com/2026/06/c-ai-character-ai.html), [TechCrunch](https://techcrunch.com/2025/10/29/character-ai-is-killing-the-chatbot-experience-for-minors/)
- Character.AI and Google agreed (announced 7 Jan 2026) to settle teen-harm and suicide lawsuits in Florida, Texas, Colorado and New York, with no public amounts. A federal judge rejected the "publisher speech" defence. Pennsylvania sued in May 2026 over bots impersonating licensed doctors. — [CNBC](https://www.cnbc.com/2026/01/07/google-characterai-to-settle-suits-involving-suicides-ai-chatbots.html), [CNN](https://www.cnn.com/2026/01/07/business/character-ai-google-settle-teen-suicide-lawsuit), [SolidAITech](https://www.solidaitech.com/2026/06/c-ai-character-ai.html) (Pennsylvania and judge points from the secondary source only)
- Replika (Luka Inc.): Italian Garante fined €5M (decision 10 Apr 2025, announced 19 May 2025) for no legal basis for processing, poor privacy notice and no effective age gate. A separate probe into model training is reported ongoing. January 2025 FTC complaint from advocacy groups alleged deceptive advertising and manipulative design; no FTC action found. — [EDPB](https://www.edpb.europa.eu/news/ai-the-italian-supervisory-authority-fines-company-behind-chatbot-replika_en), [CommLaw Group](https://commlawgroup.com/2025/us-based-ai-developer-fined-e5-million-for-gdpr-violations-key-takeaways/)
- OpenAI "adult mode" was announced October 2025 for early 2026, then reportedly paused indefinitely in March 2026 over safety, minors and emotional-dependency concerns. — [TechCrunch, 7 Mar 2026 (delay)](https://techcrunch.com/2026/03/07/openai-delays-chatgpts-adult-mode-again/), [Just AI News](https://justainews.com/companies/openai/adult-mode-in-chatgpt-explained-nsfw-erotica-porn-policy/) (the indefinite-pause detail comes from the latter, a weaker source)
- Nomi's paid, age-verified web experience is reported as more permissive than its mobile apps. — [WeavAI via search](https://weavai.app/blog/en/2026/04/08/nomi-ai-review-2026-full-analysis-of-three-tier-memory-system-voice-calls-and-ai-companion-features/)

### Inferences
- SB 243's definition (adaptive human-like responses, sustained relationship, social needs) plausibly covers Kataki if it is offered to California users. Local-only use with no operator may sit differently, but this is a legal question I cannot settle. The disclosure, crisis-protocol and minor-protection features are cheap to build and worth deciding early.
- Characters that lie, hide things or have "anxiety" are creative-fiction features, but the law targets the *chatbot presenting itself as human*. The design should keep a clear fiction frame (the "backstage" view helps).
- The CAI settlements mean a "characters impersonating doctors or therapists" content rule matters (Tennessee, Pennsylvania).

### Gaps
- Exact text of most state laws was not read; details come from law-firm summaries.
- I did not find whether local-only or self-hosted apps are exempt.
- Federal legislation status (2026) not checked.
- The Pennsylvania suit and the "judge rejected publisher defence" claim rest on one secondary source.

---

## 5. What gaps exist: "human-ness" features nobody does well

### Takeaway
The market covers memory (as recall of facts), proactive messages, voice and images. It does not cover deliberate, inspectable internal life: private thoughts that differ from speech, lying and being caught, believable forgetting, per-character models, off-screen time that has consequences, and a way for the user to see and audit all of it. Front Porch AI is the one project attacking the "needs and moods" part.

### Cited Findings
- Hosted leaders expose memory as editable facts (Nomi Mind Map, Kindroid key memories/journals, Replika dashboard, Paradot "shows what it's learned"). No source I read describes a product that shows a character's private thoughts or hidden agenda. — see Section 1 citations
- Proactivity today is text or selfie pings tuned by frequency and memory, throttled if the user ignores them (Nomi, Kindroid, Replika), or product-tied (Friend). — [WeavAI](https://weavai.app/blog/en/2026/08/13/proactive-ai-companions-nomi-replika-kindroid-compared/), [The Gadgeteer](https://the-gadgeteer.com/2026/07/31/friend-ai-pendant-voice-wearable-249-price/)
- Persona consistency is an acknowledged unsolved problem: models "wander off persona" and forget bio details; positivity bias and repetition are standard failure checks; a March 2026 paper questions whether benchmark scores reflect real persona following. — [Zylos Research](https://zylos.ai/research/2026-04-10-ai-agent-persona-design-behavioral-consistency/), [Pith](https://pith.science/paper/2603.03915)
- Memory failures are inconsistent rather than total: partial secret recall, forgetting the pattern of a person rather than the fact. — [Medium, Jul 2026](https://medium.com/@chuckmellisa/character-ai-keeps-forgetting-things-i-tested-what-it-remembers-and-what-disappears-first-97f4809d9b15)
- Front Porch AI's Realism Engine (moods with inertia, needs, fixations, growth rings, bad days unrelated to the player) exists but is a small open-source project with self-reported features. — [GitHub Front Porch AI](https://github.com/Lufou/front-porch-AI)
- SillyTavern gives full control but memory is four disconnected systems that users must configure, with silent failures. — [Arcanum RPGs](https://arcanumrpgs.com/blog/sillytavern-memory/)
- Group chat: Nomi (multiple Nomis), Character.AI multi-character rooms/Scenes, Agnai (multiple humans), Front Porch AI (Director mode), Kindroid group context. Per-character model choice inside one group was not found in any product. — [WeavAI](https://weavai.app/blog/en/2026/04/20/character-ai-2026-review-features-alternatives/), [Arcanum RPGs](https://arcanumrpgs.com/blog/sillytavern-alternatives/)
- The arXiv sycophancy study finds many vulnerable users value affirmation, so removal of agreeableness is not universally wanted. — [arXiv 2601.10467](https://arxiv.org/abs/2601.10467v2)

### Inferences (ranked list follows the matrix)
See the matrix and ranked gaps below. All ranking is my judgement from the absence of evidence in sources I could reach. Absence in my search is not proof that no product does it, especially for closed products.

### Feature matrix (product x feature)

Legend: Y = reported present; P = partial/limited or paid-only; N = not found or reported absent; ? = could not verify. Every cell is from the sources cited above or my failure to find evidence; "N" means "I found nothing", not "confirmed absent".

| Product | Long-term memory | Editable/visible memory | Lorebook/keyword lore | Internal state (mood/needs) | Proactive msgs | Group chat | Voice calls | Images/selfies | Video | Local models | Model choice | Free tier | Approx. price |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Character.AI | P (Chat/Pinned Memories) | P (pins) | P (Lorebook beta, c.ai+) | N | N | Y (rooms/Scenes) | Y | Y (Imagine, c.ai+) | Y (Charms) | N | N | Y (ads) | $9.99/mo |
| Replika | P | Y (dashboard 2026) | N | P (mood tracking) | Y (free) | N | Y | P (3D avatar/AR) | ? | N | N | Y | $19.99-29.99/mo or $69.99-119.99/yr |
| Nomi | Y (best-reviewed) | Y (Mind Map, notes) | N | N ("Identity Core") | P (paid) | Y | Y | Y | Y | N | N | Y | $15.99/mo |
| Kindroid | Y (cascaded, key mem.) | Y | Y (journals, 500 cap) | N | P (Ultra) | Y | Y | Y (selfies) | ? | N | ? (model tiers reported, unverified) | Y (Lite) | about $13.99-24.99/mo (conflicting) |
| Paradot | Y (reported) | Y (shows learning) | ? | ? | ? | N | ? | ? | ? | N | N | ? | about $6.99/mo (weak source) |
| Janitor AI | P (Pro extended) | ? | Y (cards) | N | N | Y | N | N | N | N (BYO API) | Y (BYO) | Y (50 msg/day) | $9.99/mo |
| Chub/Venus | ? | ? | Y | N | N | ? | N | ? | N | N (BYO API) | Y (BYO) | ? | ? |
| SillyTavern | Y (4 layers, plugins) | Y | Y (World Info) | P (via extensions) | P (via extensions, unverified) | Y | P (TTS/STT ext.) | P (ext.) | N | Y | Y | Y (free, OSS) | Free |
| RisuAI | Y | Y | Y | N | N | Y | P (TTS) | ? | N | Y (backends) | Y | Y (free, OSS) | Free |
| Agnai | ? | ? | ? | N | N | Y (multi-human) | N | ? | N | Y (backends) | Y | Y (free, OSS) | Free |
| KoboldCpp | Y (Lite memory) | Y | Y (world info) | N | N | P | N | N | N | Y | Y (any GGUF) | Y (free, OSS) | Free |
| Backyard AI | P | ? | Y | N | ? | Y | ? | ? | N | N (desktop deprecated) | P (tiers) | Y (300 msg/wk) | $12-35/mo |
| Front Porch AI | Y (local RAG, Learned Facts) | Y (journal) | Y | **Y (Realism Engine)** | P (AFK evolution) | Y (Director mode) | Y (Kokoro/Whisper) | Y (local image-gen) | N | Y | Y | Y (free, OSS) | Free |
| Tolan | Y | ? | N | ? | Y | N | Y | ? | N | N | N | ? | about $10/mo, $4.99/wk |
| Sesame | ? | ? | N | ? | N | N | Y (core) | N | N | N | N | Y (beta) | n/a |
| Friend | ? | N | N | ? | Y (push) | N | Y (speaker) | N | N | N | N | n/a | $249 hardware |
| Grok companions | P | ? | N | P (affection levels) | ? | N | Y (being retired, unverified) | N | N | N | N | N | $30/mo SuperGrok |
| Chai / PolyBuzz / Zeta / Talkie | ? | ? | ? | N | ? | ? | P | P | ? | N | N | Y | varied (Chai $80M ARR reported) |
| Hume EVI / Inworld / Convai | n/a (infra) | n/a | n/a | P (emotion sensing/NPC) | n/a | n/a | Y | n/a | n/a | N | Y | Y (dev tiers) | usage-based |
| **Kataki (owner's stated scope)** | (planned) | (planned, backstage) | (planned) | (planned: anxious, lies, mistakes, forgets) | (planned: time skips) | Y (1:1 and group) | ? | Y (local) | ? | Y (8 GB GPU, llama.cpp) | Y (per-character model, HF providers) | n/a | n/a |

### Ranked "gaps Kataki can own"

1. **Inspectable inner life ("peek" and "backstage" as a first-class differentiator).** Every hosted competitor shows memory lists; none shows private thoughts versus spoken words, or why a character said something. Kataki already has peek and backstage in the design. Owning "you can see what they are actually thinking, and they can be wrong or lying" is currently unclaimed by any product I found except partial overlap in Front Porch AI's mood/fixation display (unverified).
2. **Believable, mechanical forgetting and mistaking (memory that decays, distorts and can be corrected).** The market frames forgetting as a bug. Nobody sells memory with deliberate decay, confidence, false memories or "remembers the fact but not the feeling", even though users already perceive pattern loss (Medium test). Pairing this with a user-visible memory ledger (like Nomi's Mind Map, Replika's dashboard) is the natural fit.
3. **Characters that lie, withhold and hold secrets consistently, with the truth stored privately.** Secret recall is reported as unreliable in Character.AI, and no product advertises a hidden-truth versus stated-belief model. Requires a clear fiction frame and safety rails given SB 243 and Tennessee/Pennsylvania actions.
4. **Per-character model choice inside one group scene.** I found no product that lets different characters in one scene run on different models (voice-of-character diversity plus cost control on an 8 GB GPU). Only Kataki's design stated this; I found no competitor evidence.
5. **Off-screen life with consequences (time skips that simulate what happened).** Existing "proactive" is a ping keyed to memory. Front Porch AI does AFK evolution and a story clock, which is the closest. Kataki's time skip plus off-screen simulation and reconciliation on return is a differentiator if it is grounded in state and not just generated summary.
6. **Local-first plus polished UI plus honest privacy story, especially against ID-upload age verification.** Backyard AI's desktop deprecation left a hole, and Front Porch AI is filling it with an indie UI. A well-designed 8 GB-GPU-aware app with cloud fallback via HF is a credible position. Defensible only if quality of the default local model on 8 GB is good, which is unmeasured here.
7. **Sycophancy as a dial, not a fix.** Research shows vulnerable users value affirmation; complaints show others hate yes-men. Per-character "agreeableness/candour" with user-visible setting is uncontested, cheap and testable.
8. **Unified memory that works out of the box.** SillyTavern's four-layer setup fails silently, and Kindroid has hard caps; a single memory pipeline with diagnosable failures (backstage shows what was retrieved and why) is an easy usability win.
9. **Table stakes to match (not gaps):** lorebook (Character.AI now has one), editable memory view (Replika, Nomi, Kindroid), consistent character face in images (Character.AI Imagine), group chat (Nomi, Agnai), voice calls with about 1-1.5 s latency (Nomi, Replika), age/disclosure and crisis protocols (SB 243).

### Gaps in this section
- I found no evidence about closed products' internal architectures; "nobody does X" claims are limited to what marketing and reviews say.
- I did not test any product hands-on.
- I did not find published research that measures user retention against specific human-like features (lying, forgetting); the ranking is therefore judgement.
- Video calls, games/mechanics (dice, stats, inventory) and quest systems in AI Dungeon, NovelAI and Talkie were not covered in enough detail to rank.
