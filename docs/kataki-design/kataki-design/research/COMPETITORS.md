# Competitor research

**Date:** 26 September 2026
**Method:** Desk research using official documentation, official app/help-center pages, GitHub repositories and issues, app store listings, Trustpilot reviews, and independent review/blog coverage. Unverifiable claims are marked "not verified" rather than asserted. Quotes are reproduced as found in source; aggregator sites sometimes paraphrase rather than quote verbatim, noted where relevant. The five apps span a spectrum: local/open-source power-user tool (SillyTavern), venture-backed consumer app (Character.AI), community-driven NSFW-tolerant proxy front-ends (Janitor AI, Chub/Venus), mobile companion app (Talkie), and a closed-source local-first desktop app (Backyard AI) — the closest structural analogue to Kataki RPAI.

---

## SillyTavern

### What it is
SillyTavern is a free, open-source, self-hosted "LLM frontend for power users" — a chat client that connects to many different backends (KoboldAI/CPP, Horde, NovelAI, Oobabooga, TabbyAPI, OpenAI, OpenRouter, Claude, Mistral, and more) rather than hosting a model itself. It began in February 2023 as a fork of TavernAI 1.2.8 and has since grown to over 300 contributors ([GitHub README](https://github.com/SillyTavern/SillyTavern)).

### First run
Per the official Quick Start doc: install via the separate Installation Guide, then (1) open API Connections in the top bar and either enter the placeholder key `0000000000` for the free AI Horde backend and pick a model, or create an OpenAI account, generate a key at platform.openai.com, choose "Chat Completion (OpenAI)" in API Connections and paste the key; (2) name a persona; (3) open Character Management and pick an existing sample character (the built-in character is named **Seraphina**); (4) type in the chat box at the bottom and press Enter ([Quick Start](https://docs.sillytavern.app/usage/quick-start/)). Separately, the newer Welcome Screen lets a user skip character selection entirely by typing straight into the input bar, which auto-creates a blank "Assistant" character card to customize later ([What is SillyTavern?](https://docs.sillytavern.app/)). The README is candid about the cost of this flexibility: **"The steep learning curve is part of the fun!"** ([GitHub README](https://github.com/SillyTavern/SillyTavern)).

### Information architecture
Top bar: API Connections, Character Management, Persona Management, World Info, User Settings, and an Advanced Formatting panel for prompt/template tuning ([docs.sillytavern.app](https://docs.sillytavern.app/)). Settings alone are organized into General Settings, UI Theme, Character Handling, Chat/Message Handling (itself split into Message Display, Input & Response Controls, Auto-Management with auto-swipe/auto-continue, Message Formatting, and Prompt Inspection/Debugging), STscript settings, a Clean-Up menu and a Debug menu explicitly flagged for advanced users only. The docs note the developers added a **Settings Search** feature specifically because the settings surface had grown large enough to need one — an implicit admission of settings overwhelm ([User Settings](https://docs.sillytavern.app/usage/user-settings/)).

### The chat screen
Messages sit in a scrolling log with a persistent chat bar fixed at the bottom of the screen. Per-message controls include: **Swipe** (generate an alternate reply, also bound to the Right arrow key), **Edit** (modify text, with sub-actions to confirm, copy, delete or reposition the message), **Regenerate** and **Continue** (in a Chat Options panel), **Branch** ("start alternate story path"), and per-message exclusion from the AI's context ([Chatting docs](https://docs.sillytavern.app/usage/chatting/)). A live, filed GitHub feature request (opened years ago, still open) asks for swipe/regenerate on *any* historical message, not just the last one — current behavior restricts regeneration to the most recent AI turn even though editing any past message is already allowed, which the requester calls unnecessarily restrictive given "other platforms" already support it ([Issue #4075](https://github.com/SillyTavern/SillyTavern/issues/4075)). Visual Novel Mode is offered as an alternate presentation with a full-screen character sprite; the standard chat mode's exact portrait size/position is not documented in detail in the sources checked — **not verified**.

### Memory & persona
World Info (aka Lorebook/Memory Book) is a keyword-triggered prompt-injection system: entries fire when their keyword appears in recent chat, are inserted at configurable positions (before/after the character definition, inside Author's Note, at a specific prompt depth), and can have activation probability and grouping logic. It can be bound globally, or to a specific character, persona, or chat via buttons inside Character Management / Persona Management. Documentation is explicit that World Info "does not guarantee its appearance in the generated output" — it nudges, not forces ([World Info docs](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)). Persona Management is a dedicated panel: create/select personas, set a display name/avatar/description, and lock a persona to the current chat, to a specific character, or as the global default (shown with a yellow border); connected characters render as small clickable avatars inside the panel ([Personas docs](https://docs.sillytavern.app/usage/core-concepts/personas/)).

### What users complain about
- Setup and settings are self-acknowledged as a steep learning curve; the existence of a dedicated settings-search feature is itself evidence users get lost.
- Swipe/regenerate only works on the latest message — an explicit, long-standing feature request rather than a shipped capability ([Issue #4075](https://github.com/SillyTavern/SillyTavern/issues/4075)).

### What users praise
- Model-agnosticism ("a single unified interface for many LLM APIs") and depth of customization: themes, custom CSS, extensions, worldbuilding tools, TTS, image-gen integration ([GitHub README](https://github.com/SillyTavern/SillyTavern)).
- Open-source trust and a genuinely large, active contributor/extension ecosystem.

### What we should steal
- Persona-as-first-class-object with three explicit binding scopes (chat / character / global default) — a clean mental model worth reusing for Kataki's persona system.
- A dedicated in-settings search bar as an escape hatch once a settings surface grows past a screenful.
- Making "start with no character at all" a valid, zero-friction first path (auto-generated blank Assistant card).

### What we should avoid
- Splitting core actions (regenerate, continue, branch, delete) across a top-bar "Chat Options" menu *and* per-message hover controls *and* keyboard shortcuts, with no single discoverable source of truth.
- Restricting an editing-adjacent action (regenerate) to only the newest message when editing itself is unrestricted — an arbitrary inconsistency that trained users to file a bug report instead of trusting the UI.

---

## Character.AI

### What it is
Founded November 2021 by ex-Google LaMDA engineers Noam Shazeer and Daniel de Freitas; public beta launched September 16, 2022; reached 3.5 million daily visitors by January 2024, skewing 16–30 years old ([Wikipedia](https://en.wikipedia.org/wiki/Character.ai)). It is the largest consumer-facing character-chat product in this set, with premium tier "c.ai+" at $9.99/month.

### First run
Independent UI teardown documents **3 onboarding steps** before reaching the main app, followed immediately by a soft paywall screen introducing the premium subscription ($2.49/wk, $94.99/yr) ([screensdesign.com](https://screensdesign.com/showcase/character-ai-chat-talk-text); [appllama.io](https://appllama.io/apps/1671705818/character-ai-chat-talk-text)). Character creation itself (the "Quickstart") is an 8-step wizard per the official Help Center: (1) name the character, (2) create an avatar (upload a ≥512×512 square image, or generate one), (3) choose a voice (suggested, library, or a custom 3–15 second clone), (4) write a greeting (the guide's own example: **"You are finally here"**, with up to five greetings and an auto-generate option), (5) add genre/texture tags, (6) set visibility (Public / Unlisted / Private), (7) add optional tagline/description/character definition, (8) publish ([Help Center Quickstart](https://support.character.ai/hc/en-us/articles/50608869548699-2-Creating-a-Character-Quickstart-Guide-%CF%89)).

### Information architecture
Discovery is feed-first: a "For You" feed surfaces conversations as visual "moments" a user can jump straight into, rather than a flat character directory ([screensdesign.com](https://screensdesign.com/showcase/character-ai-chat-talk-text)). The teardown counts roughly eight top-level flows (discovery, chat, character creation, profile, settings, etc.), each 1–6 screens deep.

### The chat screen
Per-chat settings expose memory management, wallpaper/background changes, and a chat-history summary view. The composer supports multiple input modes beyond text: image upload, stickers, and voice calls ([screensdesign.com](https://screensdesign.com/showcase/character-ai-chat-talk-text)). Contextual paywalls interrupt specifically at premium touchpoints (advanced memory, custom app icon) rather than blocking the whole app — a "just-in-time" upsell pattern. Exact portrait size/position on the chat screen: **not verified** in sources fetched (locked behind the teardown site's paid tier).

### Memory & persona
"Advanced memory" is explicitly a premium-gated feature (see paywall note above). Beyond that, granular memory UI details were not accessible in the sources reviewed — **not verified**.

### What users complain about (Trustpilot, verbatim quotes)
- Ads: **"ads are tolerable but it got worse with the limits of chats and age verification"**; **"ruined by ads, slow-mode, and maximum 100go per day (goes fast)"**; **"The ads between messages. They will literally pop up between messages."**
- Filtering/censorship: **"Lots of unnecessary, sometimes ridiculous filters and endless technical glitches"**; **"it keeps censoring me when I state 'shooting' for anything like a action sequence."**
- Memory/consistency: **"Chatbots have poor memory and you have to repeat the commands several times"**; **"Characters can change their features and behavior out of the blue."**
- Age verification (rolled out ahead of a policy banning under-18 users from creating/chatting with bots, effective November 25, 2025): **"This new age verification is just asking for kids to steal parents' IDs"**; **"They ask to scan your face and scan your identification card."**
- Bot overreach: **"when the rp bot takes controle of my characters actions. It pisses me off."**
(All quotes: [Trustpilot](https://www.trustpilot.com/review/character.ai); background on the under-18 policy and December 2024 safety features: [Wikipedia](https://en.wikipedia.org/wiki/Character.ai).)

Separately, Character.AI has faced serious, well-documented safety controversies — wrongful-death lawsuits (Sewell Setzer III, Florida, February 2024; Juliana Peralta, Colorado, November 2023), impersonation of real deceased people, and a Pennsylvania state lawsuit over a bot impersonating a licensed psychiatrist (May 2026) ([Wikipedia](https://en.wikipedia.org/wiki/Character.ai)). These are moderation/trust-and-safety issues rather than UX issues per se, but they are the direct cause of the filter tightening that then generates the UX complaints above — worth noting for Kataki's own approach to safety-by-design.

### What users praise
Praise is thin in the sources reviewed and mostly nostalgic: **"This site used to be amazing. I remember using it often to roleplay"**; a 4-star review calling it **"my chill out app"** despite citing ads as its one flaw ([Trustpilot](https://www.trustpilot.com/review/character.ai)).

### What we should steal
- Just-in-time, feature-scoped paywalls (interrupt at the exact premium action, not a global gate) — good discoverability without constant friction.
- A short, opinionated character-creation wizard with a strong example (the "You are finally here" greeting tip) that teaches craft, not just fields.

### What we should avoid
- Letting trust-and-safety fixes visibly degrade the core experience (users can taste the filter tightening as "personality loss") without any user-facing explanation — this is a discoverability/communication failure as much as a moderation one.
- Repeat-yourself memory failures that users notice and complain about specifically ("poor memory... have to repeat the commands several times").

---

## Janitor AI / Chub AI (Venus)

Treating these together since Janitor AI is a hosted chat front-end (bring-your-own API key or reverse proxy) and Chub AI (formerly "Venus") is a character/lorebook repository plus its own chat client — both serve the same NSFW-tolerant, power-user-adjacent niche and are frequently used together.

### What it is
Janitor AI's own landing copy: **"Be anyone. Build anything,"** claiming **"15M+ users crafting living stories"** and hosting **over 640,000 characters** ([janitorai.com](https://janitorai.com/)). Chub AI positions itself as a platform where users chat via multiple LLM APIs (OpenAI, Anthropic) with "no meaningful content restrictions," plus chat trees and chat import/export ([docs.chub.ai](https://docs.chub.ai/)).

### First run
Janitor AI: register or log in from the header; browse a "Popular" character feed; each card shows name, creator handle, a truncated description, metadata tags (gender, OC vs. fictional, genre, "Limitless" for unfiltered content), token count and a star rating ([janitorai.com](https://janitorai.com/)). Getting an AI backend working, however, is a separate and non-trivial step: because Janitor AI does not include its own model, new users must configure either a paid API key (e.g., OpenRouter, DeepSeek) or a community reverse proxy — an entire genre of third-party guide exists just to explain this ("Janitor AI Proxy and API Settings: Complete Setup Guide," [proxywing.com](https://proxywing.com/blog/janitor-ai-guide-characters-api-setup-reverse-proxy-and-alternatives); "Janitor AI API Setup: OpenRouter, DeepSeek and Reverse Proxies," [chatjanitor.com](https://chatjanitor.com/blog/janitor-ai-api-setup-reverse-proxy)). Chub AI signup: visit chub.ai, register with email + username + password, accept ToS, then "create your first character and start interacting right away" ([docs.chub.ai](https://docs.chub.ai/)).

### Information architecture
Janitor AI nav includes a `Ctrl+K` search shortcut, and top sections Home / Following (login-gated) / Favorites (login-gated) / Popular, with a footer to careers, status, guidelines, safety and support ([janitorai.com](https://janitorai.com/)).

### The chat screen
Not independently verified in detail from primary sources during this pass (janitorai.com's own chat screen was not directly fetchable) — **not verified** for exact portrait placement; secondary guides describe standard swipe/regenerate controls consistent with the genre, but specific measurements were not found in citable primary sources.

### Memory & persona
Chub AI's lorebooks are keyword-triggered content-injection entries very similar in mechanism to SillyTavern's World Info: case-insensitive whole-word keyword matching by default (so "apple" matches "Apple" but not "Applebottom"), optional secondary keywords requiring co-occurrence, and probabilistic triggering. UI controls live in two places: **Chat Settings** (Scan Depth = how many recent messages are scanned for keywords; Token Budget = cap on lorebook token spend) and a **Lorebook/Character Creator** (keyword/content fields, case sensitivity, priority, insertion order). Attaching one requires copying its path from the repository and pasting it into Chat Settings; character-embedded lorebooks require the "V2 Spec" flag ([Chub AI lorebook docs](https://docs.chub.ai/docs/advanced-setups/lorebooks)).

### What users complain about
Janitor AI, Trustpilot quotes: **"the base AI is rather shoddy, going into clichés such as 'dangerous game'"**; **"the quality of the LLM peaked back in November to December"**; **"the AI is impossible to roleplay it always turns into a boring chatgpt"**; **"the replies became nonsensical no matter what I adjusted."** UI/feature removal: **"they removed The search short Cut on mobile"**; **"I've lost the search bar to my chats on the app"**; **"all the good features are gone."** Character behavior: **"bots are completely stupid EVEN if YOU yourself make them"**; **"generating text on behalf of the user."** Support: **"staff refused to provide any details, explain their policies"**; **"complaining about bugs will lead to them ignoring you."** Moderation: **"They banned my account for reason that weren't even true"** ([uk.trustpilot.com/review/janitorai.com](https://uk.trustpilot.com/review/janitorai.com)).

A major, well-documented 2026 flashpoint: Janitor AI rolled out mandatory face-photo/ID age verification for users in Australia, Brazil and the UK (announced officially, using the k-ID identity provider, in response to new age-verification laws carrying fines up to $35M in Australia and $9.5M in Brazil) ([official announcement](https://janitorai.com/news/announcements/24/)). The rollout (April 24, 2026) triggered strong backlash: **"Guys it here age verification is here guess who cant use the app anymore i aint giving a ai company a picture of my face or anything"**, and **"I for one will be leaving Janitor.Ai for this as I just don't trust a company with that kind of data"** — compounded by technical failures where the verification flow looped users back to the start screen after apparent success, and by an unrelated simultaneous interface update that broke other features ([roborhythms.com](https://www.roborhythms.com/janitor-ai-age-verification-rollout/)).

### What users praise
Janitor AI Trustpilot: **"allows you to do pretty much anything"**; **"easy interface for proxies, allowing you to potentially link to Deepseek"**; **"lorebooks allow for advanced set up"**; **"don't pressure you to buy premium"**; **"everyone here is really sweet"** ([uk.trustpilot.com/review/janitorai.com](https://uk.trustpilot.com/review/janitorai.com)).

### What we should steal
- Visible, glanceable character metadata on discovery cards (gender/type/genre tags, token count, rating) — lets users triage without opening each character.
- `Ctrl+K` search as a first-class navigation affordance, not buried in a menu.

### What we should avoid
- Silently removing previously-shipped features (mobile search) without communication — the single most repeated complaint pattern here.
- Bundling a sensitive, trust-critical change (biometric age verification) with an unrelated UI update in the same release — it multiplies backlash and makes the two issues impossible for users to disentangle, and for support to triage.
- Making backend/model configuration (proxy, API key) a prerequisite the product itself doesn't explain — an entire cottage industry of third-party guides existing to explain "how to actually make this app work" is a discoverability failure, not a content gap.

---

## Talkie

### What it is
Talkie ("Talkie: Creative AI Community" / "Talkie Soulful AI") is a mobile companion/roleplay app (Android package `com.weaver.app.prod`) built around chat, voice, and a virtual-currency ("gems") economy for premium features.

### First run
Onboarding reportedly asks for gender, preference, and age before entering the app; one review documents a **specific onboarding bug where the flow won't progress past the "gender, preference, and age part"** ([Trustpilot via WebFetch summary](https://www.trustpilot.com/review/www.talkie-ai.com)).

### Information architecture / paywalled features
Named premium features include **"Their Phone"** and **"Secret Space"**, gated behind gem purchases; cloud sync is capped at **60 days of chat history** on the free tier, and syncing is per-chat rather than bulk ([Trustpilot](https://www.trustpilot.com/review/www.talkie-ai.com)).

### The chat screen
Specific layout/portrait details not verified from primary sources in this pass — **not verified**.

### Memory & persona
Free-tier memory is characterized by users as having **"memory of a goldfish"** ([Trustpilot](https://www.trustpilot.com/review/www.talkie-ai.com)).

### What users complain about
Content filtering: users report the app repeats **"change your topic"** "on a loop when everything I'm saying is appropriate," with filters triggering on innocuous words like "cat" while missing genuinely harmful community content; one review calls the 18+ gating **"absolutely ridiculous...can't even say sex or naked."** Monetization: ads appear "every few seconds" before entering a chat and "every 5 mins" inside one; premium features are gem-gated. Technical: chats get **"stuck and you get no reply"** requiring an app restart; messages sometimes render **"in the wrong language"**; ad close buttons are sometimes missing or ads fail to load. Character quality, compared explicitly to Character.AI: **"bots need more emotion, memory"**; characters **"easily get frightened over shit, they're too soft and just boring."** Account/data loss: losing account access can mean losing all prior conversations ([Trustpilot](https://www.trustpilot.com/review/www.talkie-ai.com)). A separate review aggregator classifies the same themes by severity: "Excessive and repetitive ads" and "Overly strict and nonsensical content filters that block harmless words" both rated **High priority**; "Technical bugs and crashes" and "chat resets" rated Medium; overall UX described as having **"addictive design patterns that frustrate users"** ([unstar.app](https://unstar.app/app/com.weaver.app.prod?platform=android&country=en-US)).

### What users praise
Talkie is credited with providing an **"enjoyable pastime"** that relieves **"feelings of loneliness,"** offering **"great emotional interaction"** and being **"engaging for daily entertainment"** ([Trustpilot](https://www.trustpilot.com/review/www.talkie-ai.com)).

### What we should steal
- Explicit companionship framing and named "moments" features (e.g. "Their Phone") that dramatize the relationship rather than just chat text — a reminder that character presence can be more than a portrait + text log.

### What we should avoid
- A content filter so blunt it blocks the word "cat" while missing actually harmful content — filters that fail on both precision and recall simultaneously destroy user trust fastest.
- Gem/currency abstraction layered over already-metered features (chat limits, sync limits) — multiplies monetization friction points instead of consolidating them.
- Onboarding gates (mandatory gender/age/preference screen) that can outright block first use if buggy — onboarding must be the most bulletproof path in the whole app, because a broken first run has no recovery.

---

## Backyard AI (formerly Faraday)

### What it is
Backyard AI is the closest structural sibling to Kataki: a desktop (and now also mobile) app for local, offline character chat, positioned as "Fictional Text & Voice Chats With No Filters," with thousands of community characters plus the ability to run models entirely locally with no account required ([backyard.ai](https://backyard.ai/)). Note: the standalone "desktop.backyard.ai" legacy app has been deprecated in favor of the unified backyard.ai web/desktop product; the deprecation notice itself confirms the product has consolidated onto one client rather than maintaining a separate desktop build ([desktop.backyard.ai](https://desktop.backyard.ai/)).

### First run
Landing page offers a no-credit-card "Get Started," with sign-in leading straight into the app; mobile apps exist for Android and iOS ([backyard.ai](https://backyard.ai/)). An independent review frames the onboarding advantage explicitly relative to SillyTavern: **"One installer, no separate backend/frontend pairing to configure, unlike SillyTavern"** — download, pick a model, start chatting ([promptquorum.com](https://www.promptquorum.com/power-local-llm/backyard-ai-review-local-roleplay)).

### Information architecture
A Community Hub for discovering pre-built characters sits alongside character-creation tools. The iOS App Store listing (Ahoy Labs, Inc.; 40.7 MB; 16+ age rating; free with in-app purchases QAR 39.99–999.99) lists core features as: character creation with lore books, author's note, and background images; a community hub; and selection across "12+ AI models" for personality/memory customization ([App Store listing](https://apps.apple.com/qa/app/backyard-ai/id6498968886)).

### The chat screen
Exact portrait size/position not documented in the sources reviewed — **not verified**. Feature set per the marketing site: **Dynamic Voices** for spoken dialogue delivery, **Lorebooks** for embedding "relevant context, history, and memories," **Author's Note** to "set the scene, add atmosphere, or guide your story," **Grammars** to enforce structured/constrained output formatting, and exposed **Model Parameters** (samplers, context length, prompt templates) for advanced users ([backyard.ai](https://backyard.ai/)).

### Memory & persona
Lorebooks function as the memory/worldbuilding layer (see above); a review notes local mode is capped at roughly **8B–13B parameter models**, with access to 70B-class models gated behind a paid "Backyard Cloud" subscription, and that Fimbulvetr-10.7B is called out as running "comfortably on a 16 GB VRAM gaming GPU" ([promptquorum.com](https://www.promptquorum.com/power-local-llm/backyard-ai-review-local-roleplay)).

### What users complain about
Per the same independent review: no group chats and no visual node-based workflow editor (unlike SillyTavern's extension ecosystem); local-mode model selection is restricted to Backyard's own curated list, with **no ability to import arbitrary GGUF files** the way a koboldcpp+SillyTavern combination allows; as a closed-source app, its offline/privacy claims **"cannot be independently verified the way an open-source frontend can"**; and community-submitted character quality **"varies; curation is uneven"** ([promptquorum.com](https://www.promptquorum.com/power-local-llm/backyard-ai-review-local-roleplay)). The App Store listing itself notes there were not yet enough ratings to display an aggregate score, so broader consumer sentiment at scale is **not verified**.

### What users praise
Ease of setup relative to SillyTavern (single installer, no backend pairing); a large built-in character library removing the need to author cards from scratch; genuine offline operation with no account requirement in local mode ([promptquorum.com](https://www.promptquorum.com/power-local-llm/backyard-ai-review-local-roleplay); [backyard.ai](https://backyard.ai/)).

### What we should steal
- "One installer, no backend/frontend pairing" as the explicit onboarding promise — this is precisely the bar Kataki should clear, stated as plainly in marketing as in the product.
- Bundling a curated, ready-to-chat character library so day-one use doesn't require authoring anything.
- Surfacing hardware reality up front (which models run "comfortably" on what VRAM) rather than letting users discover it by trial and error.

### What we should avoid
- A closed-source trust gap on privacy claims for a product whose entire pitch is local-first/private — if Kataki claims local-first, it should make that claim independently verifiable (open components, clear data-flow diagrams, or at minimum a transparent, specific description of what stays on-device).
- A hard split between "curated local models only" and "unlocked capability requires our paid cloud" — this reads as a bait-and-switch on the local-first promise once a user's hardware or ambitions outgrow the curated list.

---

## Cross-cutting patterns

| Pattern | Who does it | Verdict for Kataki |
|---|---|---|
| Keyword-triggered lorebook/world-info with scan depth + token budget controls | SillyTavern, Chub AI | Adopt the mechanism, but default the budget/depth to sane values and hide the numeric controls behind an "Advanced" disclosure — both source products expose these as raw numbers on day one. |
| Persona as a bindable object (chat / character / global-default scope) | SillyTavern | Adopt — it is the cleanest mental model found across all five apps for "who am I in this conversation." |
| Swipe/regenerate restricted to only the latest message | SillyTavern | Avoid the restriction; if latest-only is a technical constraint early on, at minimum keep edit and regenerate permission-symmetric so users don't file bugs over the asymmetry. |
| Single installer, no backend/frontend pairing | Backyard AI (vs. SillyTavern) | This is Kataki's core differentiation opportunity — make it the loudest first-run promise. |
| Curated built-in character library so day one needs no authoring | Backyard AI, Janitor AI, Chub AI | Adopt — ship with a small, well-crafted default roster (echoing SillyTavern's single "Seraphina" default, but more than one). |
| Feature-scoped, in-context paywalls instead of a global gate | Character.AI | Only relevant if Kataki monetizes; if so, gate at the exact premium action, never as a blanket wall. |
| Command palette (`Ctrl+K` / `Cmd+K`) as first-class, not buried | Janitor AI, Linear, Raycast, Notion (slash-in-canvas variant) | Adopt for character/chat/settings search — cheap to build, high perceived power. |
| Progressive disclosure via tiered menus ("More actions") rather than one giant settings page | Linear, GitLab (per UX literature), contrasted with SillyTavern's flat, deep settings tree | Adopt tiering explicitly: essential controls always visible, common controls one click away, advanced/debug behind an explicit "Advanced" or "Developer" toggle — this is the single biggest lesson from SillyTavern's self-acknowledged learning curve. |
| Gentle, contextual shortcut teaching (hover-triggered hint banners) | Linear | Adopt for teaching Kataki's own shortcuts/command palette without a modal tutorial wall. |
| Silent feature removal / undocumented UI changes | Janitor AI (mobile search removed) | Avoid — always changelog visible UI/feature changes, however small; this was the single most repeated non-performance complaint found. |
| Bundling sensitive policy changes with unrelated UI updates in one release | Janitor AI (age verification + interface update same day) | Avoid — ship trust-sensitive changes (privacy, moderation, data handling) in isolated releases with dedicated, calm communication. |
| Bluntly over-broad content filters (false positives on innocuous words, false negatives on real harm) | Character.AI, Talkie | Avoid — if Kataki filters at all, precision matters more than aggressiveness; a filter users can mock ("can't even say cat") destroys trust in the whole safety system, not just that filter. |
| Monetization via layered micro-limits (message caps, sync-history caps, currency gates) stacked simultaneously | Talkie, Character.AI | Avoid stacking; pick one legible constraint if any, not several compounding ones. |

---

## Sources

**SillyTavern**
- [What is SillyTavern? (docs.ST.app)](https://docs.sillytavern.app/)
- [Quick Start (docs.ST.app)](https://docs.sillytavern.app/usage/quick-start/)
- [User Settings (docs.ST.app)](https://docs.sillytavern.app/usage/user-settings/)
- [Chatting (docs.ST.app)](https://docs.sillytavern.app/usage/chatting/)
- [World Info (docs.ST.app)](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- [Personas (docs.ST.app)](https://docs.sillytavern.app/usage/core-concepts/personas/)
- [GitHub: SillyTavern/SillyTavern README](https://github.com/SillyTavern/SillyTavern)
- [GitHub Issue #4075: swipe/regenerate on every message](https://github.com/SillyTavern/SillyTavern/issues/4075)

**Character.AI**
- [Character.ai — Wikipedia](https://en.wikipedia.org/wiki/Character.ai)
- [Creating a Character: Quickstart Guide (Help Center)](https://support.character.ai/hc/en-us/articles/50608869548699-2-Creating-a-Character-Quickstart-Guide-%CF%89)
- [Character AI: Chat, Talk, Text UI Breakdown (screensdesign.com)](https://screensdesign.com/showcase/character-ai-chat-talk-text)
- [Character AI: Chat, Talk, Text screens, onboarding and paywall (appllama.io)](https://appllama.io/apps/1671705818/character-ai-chat-talk-text)
- [Trustpilot: character.ai reviews](https://www.trustpilot.com/review/character.ai)

**Janitor AI / Chub AI (Venus)**
- [Janitor AI (janitorai.com)](https://janitorai.com/)
- [Janitor AI official announcement: age verification for Australia, Brazil, UK](https://janitorai.com/news/announcements/24/)
- [Janitor AI Just Forced Face Photo Age Verification on Everyone (roborhythms.com)](https://www.roborhythms.com/janitor-ai-age-verification-rollout/)
- [Trustpilot: janitorai.com reviews (UK)](https://uk.trustpilot.com/review/janitorai.com)
- [Unstar.app: Janitor AI negative review summary](https://unstar.app/app/com.janitor.ai?country=us&platform=android)
- [Chub AI Guide (docs.chub.ai)](https://docs.chub.ai/)
- [Lorebooks (docs.chub.ai)](https://docs.chub.ai/docs/advanced-setups/lorebooks)
- [Janitor AI Proxy and API Settings guide (proxywing.com)](https://proxywing.com/blog/janitor-ai-guide-characters-api-setup-reverse-proxy-and-alternatives)
- [Janitor AI API Setup: OpenRouter, DeepSeek and Reverse Proxies (chatjanitor.com)](https://chatjanitor.com/blog/janitor-ai-api-setup-reverse-proxy)

**Talkie**
- [Trustpilot: www.talkie-ai.com reviews](https://www.trustpilot.com/review/www.talkie-ai.com)
- [Unstar.app: Talkie negative review summary (Google Play)](https://unstar.app/app/com.weaver.app.prod?platform=android&country=en-US)

**Backyard AI (formerly Faraday)**
- [Backyard AI (backyard.ai)](https://backyard.ai/)
- [Backyard AI legacy desktop app deprecation notice (desktop.backyard.ai)](https://desktop.backyard.ai/)
- [Backyard AI — App Store listing](https://apps.apple.com/qa/app/backyard-ai/id6498968886)
- [Backyard AI Review 2026: Local Roleplay & Character Chat (promptquorum.com)](https://www.promptquorum.com/power-local-llm/backyard-ai-review-local-roleplay)

**Craft references (desktop chat UI patterns)**
- [The Elegant Design of Linear.app (telablog.com)](https://telablog.com/the-elegant-design-of-linear-app/)
- [The Art of Progressive Disclosure in UX/UI Design (timgraf.com)](https://timgraf.com/ux-design/the-art-of-progressive-disclosure-in-ux-ui-design-balancing-complexity-and-clarity/)
- [Using slash commands — Notion Help Center](https://www.notion.com/help/guides/using-slash-commands)
- [Progressive disclosure — Wikipedia](https://en.wikipedia.org/wiki/Progressive_disclosure)

Note: several searches surfaced only SEO/review-farm content (near-identical "20XX guide" sites for SillyTavern, Talkie and Janitor AI); these were excluded in favor of official docs, GitHub, app stores and Trustpilot. No single authoritative first-party design write-up was found for Raycast, Discord or Obsidian beyond their own help docs and the general progressive-disclosure literature cited above; specific claims about those three beyond what's cited are **not verified** and were omitted rather than guessed.
