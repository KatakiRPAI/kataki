# Cloud economics of a human-like character "mind", and pricing/licensing for Kataki (as of 2026-09-29)

> Method note for the report writer. WebSearch was exhausted (200/200), so everything below comes from direct fetches. The strongest sources are two machine-readable primaries pulled on 2026-09-29: the OpenRouter model catalogue (`https://openrouter.ai/api/v1/models`, 460 models) and the Hugging Face router catalogue (`https://router.huggingface.co/v1/models`, 134 models, per-provider prices). Vendor pricing pages were fetched through a small summarising model, so a few numbers carry that risk; where a page would not render I say so under Gaps. Competitor pricing pages (Character.AI, Nomi, Kindroid, Replika, Janitor, Chub) returned 403/404/JS shells; those prices come from the earlier note 02 (third-party reviews) and are marked "secondary". All cost-per-user figures are my arithmetic on the cited prices and stated assumptions, not measurements. Roleplay *quality* of the cheap models was not tested here; price-based picks need a Kataki eval before shipping.
> Workload assumptions (from the brief): reply about 3k input / 300 output tokens (midpoint of 2-4k / 150-400); side call 1k/150; extraction about 1 per 5 turns; offstage/dream job 3k/600 per character at a time skip. Note 02 (`02_market_scan.md`), note 17 (cost/law lines) and note 18 (voice cost) in this folder were read first and are reused, not repeated.

---

## 1. Current per-million-token prices (roleplay and utility models, providers, caching and batch discounts)

### Takeaway
By September 2026 a usable roleplay reply model costs roughly $0.15 in / $0.50 out per million tokens (GLM-5.3-Flash, DeepSeek V4.1 Flash off-peak $0.15/$0.60), and a utility/JSON model costs $0.03-0.10 in / $0.13-0.50 out. Cached input is 2-20% of the miss price on nearly every provider, so an append-only roleplay prompt is mostly a cache-hit bill. Frontier-ish options (Kimi K3 $3/$15, Claude Haiku 4.5 $1/$5, GLM-5.3 $1.40/$4.40) are 7-30x more expensive and only viable as an opt-in premium tier. The catalogue also shows Google's Gemini 3.6-3.8 Flash prices are promotional and double on 1 Jan 2027, and DeepSeek has peak/off-peak pricing.

### Cited Findings

**Price table ($ per 1M tokens; in / cached-in / out). "OR" = OpenRouter catalogue listing (default endpoint), "HF" = HF router per-provider price.**

Reply-class (roleplay writing) candidates

| Model | In | Cached in | Out | Source / notes |
|---|---|---|---|---|
| GLM-5.3-Flash (Z.ai) | 0.15 | 0.03 | 0.50 | Z.ai docs; identical 0.15/0.50 on Novita, Together, Baseten, DeepInfra (HF); batch listing on OR 0.06/0.20 |
| GLM-5.3-FlashX | 0.37 | 0.075 | 1.25 | Z.ai docs |
| GLM-5.3 | 1.40 | 0.26 | 4.40 | Z.ai docs; DeepInfra 0.90/4.00 (HF) |
| GLM-4.7-Flash, GLM-4.5-Flash | free | free | free | Z.ai docs lists both "Free"; rate limits/data use not retrieved |
| DeepSeek V4.1 Flash (direct), peak | 0.30 | 0.006 | 1.20 | DeepSeek docs |
| DeepSeek V4.1 Flash (direct), off-peak | 0.15 | 0.003 | 0.60 | DeepSeek docs; off-peak = half; 1M context; thinking is the default mode |
| DeepSeek V4.1 Flash, other hosts | 0.20-0.30 | 0.006 (Together) | 0.60-1.20 | HF: DeepInfra 0.20/0.60, Novita/Baseten 0.30/1.20; OR batch 0.112/0.336 |
| DeepSeek V4-Pro-0813 (direct) | 1.32 peak / 0.66 off | 0.044 / 0.022 | 3.96 / 1.98 | DeepSeek docs |
| Gemini 3.8 / 3.7 / 3.6 Flash | 0.75 | 0.075 | 3.75 | Google pricing; "through Dec 31, 2026; double after"; batch 0.375/1.875 |
| Gemini 3.5 Flash | 1.50 | 0.15 | 9.00 | Google pricing |
| Gemini 3.5 Flash-Lite | 0.30 | 0.03 | 2.50 | Google pricing; batch 0.15/1.25 |
| Gemini 3.1 Flash-Lite | 0.25 | 0.025 | 1.50 | Google pricing (varies by modality); batch 0.125/0.75 |
| Gemini 2.5 Flash | 0.30 | 0.03 | 2.50 | Google pricing |
| Claude Haiku 4.5 | 1.00 | 0.10 (5-min write 1.25x, 1-hour write 2x) | 5.00 | Anthropic docs; batch -50%; newest Haiku listed on the page is 4.5 |
| Claude Sonnet 5.5 / Opus 5.5 / Fable 5.1 | 2 / 4 / 10 | 0.20-0.25 | 10 / 20 / 50 | Anthropic docs (reference only) |
| Kimi K3 | 3.00 | 0.30 | 15.00 | Kimi platform docs; Together/Fireworks/Baseten also 3/15, DeepInfra 2.85/14.25 (HF); K3 has 5-min and 1-hour cache tiers with separate write costs |
| Kimi K2.6 | 0.95 | 0.16 | 4.00 | Kimi platform docs; OR lists 0.65/3.41 |
| Qwen3.8-Flash (OR) | 0.15 | 0.016 | 0.47 | OR; Together lists 0.09/0.28 |
| Qwen3.8-27B | 0.42 (DeepInfra 0.20) | 0.085 (OR) | 3.00 (DeepInfra 2.50) | OR, HF |
| Qwen3.7-Plus / Max (Alibaba intl) | 0.40 / 2.00 | about 10% of input | 1.20 / 6.00 | Alibaba Model Studio (Plus tier 0-256K; tiered above) |
| Mistral Small 2603 | 0.15 | 0.015 | 0.60 | OR; batch -50% |
| Mistral Large 2512 | 0.50 | 0.05 | 1.50 | OR and Mistral pricing page; batch -50% |
| Mistral Medium 3.1 | 0.40 | 0.04 | 2.00 | OR |
| MiniMax M3 | 0.30 | 0.06 (OR) | 1.20 | OR; same 0.30/1.20 on Novita, Together, Fireworks (HF) |
| gpt-oss-120b | 0.037-0.35 | 0.075 (OR) | 0.17-0.75 | HF: DeepInfra 0.037/0.17, Novita 0.05/0.25, Baseten 0.10/0.50, Together and Fireworks 0.15/0.60, Groq 0.15/0.75, Cerebras 0.35/0.75 |
| Llama 3.3 70B | 0.135 (Novita) to 1.04 (Together) | none | 0.40-1.04 | HF (huge spread across providers) |

Roleplay-tuned finetunes (OR unless noted): TheDrummer Cydonia-24B v4.1 0.30/0.50 (cache 0.15); TheDrummer UnslopNemo-12B 0.40/0.40; TheDrummer Skyfall-36B v2 0.55/0.80; Sao10K L3.3-Euryale-70B 0.65/0.75; Anthracite Magnum-v4-72B 2.50/5.00; Aion-RP-Llama-3.1-8B 0.80/1.60; Sao10K L3-8B-Stheno-v3.2 and Lunaris-8B 0.05/0.05 on Novita via HF; MiniMax M2-her 0.30/1.20 (name only, not verified as roleplay-specific). — [OR catalogue](https://openrouter.ai/api/v1/models), [HF router catalogue](https://router.huggingface.co/v1/models)

Utility / structured-output candidates

| Model | In | Cached in | Out | Notes |
|---|---|---|---|---|
| Qwen3.7-Flash | 0.03 (0-32K tier) | 0.006 | 0.13 | Alibaba tiers: 0-32K 0.03/0.13, 32-256K 0.10/0.40, 256K-1M 0.20/0.80; OR shows 0.03/0.13 |
| gpt-oss-20b | 0.03 (DeepInfra) | none | 0.14 | HF: Novita 0.04/0.15, Nscale 0.05/0.20, Groq 0.10/0.50 (737 tokens/s); OR 0.018/0.09; structured output flagged true on all these hosts |
| GPT-6 Luna | 0.10 | 0.01 | 0.50 | OpenAI pricing; OR batch 0.05/0.25 |
| GPT-5-nano | 0.05 | 0.005 | 0.40 | OpenAI pricing; OR batch 0.025/0.20 |
| GPT-5.4-nano / GPT-5-mini | 0.20 / 0.25 | 0.02 / 0.025 | 1.25 / 2.00 | OR |
| Gemini 2.5 Flash-Lite | 0.10 | 0.01 | 0.40 | Google pricing; batch 0.05/0.20 |
| Amazon Nova Micro / Lite | 0.035 / 0.06 | none | 0.14 / 0.24 | OR |
| Mistral Nemo / Ministral 8B | 0.019 / 0.15 | none / 0.015 | 0.03 / 0.15 | OR |
| Llama-3.1-8B-Instruct | 0.02 | none | 0.05 | HF: Novita and DeepInfra |

- Source for all rows: [OR catalogue](https://openrouter.ai/api/v1/models), [HF router catalogue](https://router.huggingface.co/v1/models), [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing), [Google Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing), [Z.ai pricing](https://docs.z.ai/guides/overview/pricing), [Kimi pricing](https://platform.kimi.ai/docs/pricing/chat), [Alibaba Model Studio](https://www.alibabacloud.com/help/en/model-studio/model-pricing), [OpenAI pricing](https://developers.openai.com/api/docs/pricing), [Together pricing](https://www.together.ai/pricing), [Mistral pricing](https://mistral.ai/pricing).

**Discounts and pricing mechanics**
- DeepSeek direct: cache hit is 2% of the miss price ($0.006 vs $0.30 peak); off-peak is half of peak; peak is 01:00-04:00 and 06:00-10:00 UTC Monday-Friday excluding Chinese public holidays (about 21% of weekly hours); the API also says deepseek-flash "supports both non-thinking and thinking (default) modes". Legacy names deepseek-v4-flash are served by V4.1-Flash at the Flash price. — [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing)
- Together lists cached-input discounts of 98% (DeepSeek V4.1 Flash), 90% (Kimi K3, V4-Pro), 87% (Qwen3.8-2.4T), 81% (GLM-5.3), 80% (GLM-5.3-Flash). — [Together pricing](https://www.together.ai/pricing)
- Anthropic: a cache hit costs 10% of base input; 5-minute cache writes 1.25x, 1-hour writes 2x; Batch API is 50% off input and output and stacks with caching multipliers. — [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- Batch discounts of 50%: Google (batch column is half of standard), Mistral ("reduces the price by 50%"), Alibaba Model Studio ("50% batch inference discount"), Novita ("introductory 50% discount"), OpenAI and Anthropic batch variants on OR. — [Google](https://ai.google.dev/gemini-api/docs/pricing), [Mistral](https://mistral.ai/pricing), [Alibaba](https://www.alibabacloud.com/help/en/model-studio/model-pricing), [Novita](https://novita.ai/pricing), [OR catalogue](https://openrouter.ai/api/v1/models)
- Google flags Gemini 3.6-3.8 Flash and 3.8 Flash TTS prices as "through Dec 31, 2026; double after that date". — [Google Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Qwen Flash is tiered by prompt length (0.03 up to 32K, 0.10 to 256K, 0.20 to 1M input), so a 3k-token roleplay prompt sits in the cheapest tier. — [Alibaba Model Studio](https://www.alibabacloud.com/help/en/model-studio/model-pricing)

**Routing platforms and fees**
- Hugging Face Inference Providers: "no markup from Hugging Face" (provider price passed through); free users get $0.10/month of credits, PRO $2.00/month (PRO costs $9/month), Team/Enterprise $2 per seat; credits apply only to HF-routed requests, not to a custom provider key. — [HF billing docs](https://huggingface.co/docs/inference-providers/pricing), [HF pricing](https://huggingface.co/pricing)
- Provider capability matters: on HF, GLM-5.3-Flash's structured-output flag is false on Novita, Together and Z.ai but true on Baseten, DeepInfra and Fireworks; DeepSeek V4.1 Flash is false on Novita and true on Baseten, DeepInfra and Fireworks; gpt-oss-20b/120b is true on every listed host. Measured first-token latency in the catalogue ranges 0.2-4 s and throughput 19-1,070 tokens/s for the same model across hosts. — [HF router catalogue](https://router.huggingface.co/v1/models)
- OpenRouter: 5.5% fee on pay-as-you-go credit purchases, 8% Business; BYOK is free for the first $25,000/month of list-price inference and 5% after. — [OpenRouter pricing](https://openrouter.ai/pricing)
- Featherless: flat plans, not per token. Chat is $25/month, "unlimited tokens, 32K context, 4 concurrent units, any model", described as "for roleplay, stories and long conversations typed by you"; Developer is $50/month billed per token for agents and production API traffic; Business is dedicated GPUs. — [Featherless pricing](https://featherless.ai/pricing)
- Groq and Cerebras direct pricing pages did not render usable price tables; their prices above come from the HF router catalogue (gpt-oss-120b: Groq 0.15/0.75, Cerebras 0.35/0.75; gpt-oss-20b Groq 0.10/0.50). Fireworks' pricing page only showed embeddings and a link to docs; Fireworks prices above are from HF. — [HF router catalogue](https://router.huggingface.co/v1/models)

### Inferences
- The cheap-good reply tier is now GLM-5.3-Flash and DeepSeek V4.1 Flash; both have 1M-class context and 80-98% cache discounts, which fits Kataki's append-only history plus static character card.
- The one big variance is provider choice for the same model (Llama 3.3 70B is $0.135 on Novita and $1.04 on Together; gpt-oss-120b is $0.037 to $0.35 input). A Kataki cloud router should pick per model on price plus structured-output flag plus latency, not hard-code one host.
- Thinking-by-default models (DeepSeek V4.1 Flash) and reasoning models (gpt-oss) bill hidden reasoning tokens as output; the cost tables below assume thinking is off or capped. If it is left on, output cost can multiply several times. (Mechanism is standard; magnitude not measured.)
- Gemini 3.x Flash's promo price should not be the basis for a subscription margin; at the doubled 2027 price its Arch-A cost per turn is about $0.0039 (cached), 11x GLM-5.3-Flash.
- Featherless "typed by you" wording plausibly forbids automated background calls (side call, extraction, offstage jobs) on the flat plan. Not verified against its terms of service.

### Gaps
- Groq, Cerebras, Fireworks, Novita direct pricing pages: no usable tables; used HF router prices. Batch and cache discounts for those hosts unknown.
- Whether HF-routed providers honour prompt caching (and pass the cached price through) is not documented in what I retrieved; only OR and native pages list cache prices.
- DeepSeek cache TTL and cache-key behaviour not retrieved. Kimi K3 cache-write prices ($3.00 for 5 minutes, $6.00 for 1 hour per the summary) not double-checked.
- No roleplay-quality benchmark or refusal-behaviour comparison for the cheap models; NSFW acceptance by each provider not checked.
- Rate limits and free-tier data-use terms for Z.ai's free Flash models not retrieved.

---

## 2. Cost per active user per month, three profiles by three architectures (math, cache and utility-model effects)

### Takeaway
On a cheap-good stack (GLM-5.3-Flash reply, Qwen3.7-Flash utility, cached) the recommended Arch B costs about $0.58 (light, 50 msgs/day), $3.49 (heavy, 300) and $11.63 (whale, 1000) per month; caching cuts about 40% and the utility side calls add only about 10%. The same workload on a quality reply model (GLM-5.3 or Haiku 4.5) is 8-9x more, and on Kimi K3 about 20x more. The reply model's output price and input price decide the bill; the "human-like mind" extras are cheap as long as they run on a nano-class model. The full table (a) is in the final section.

### Cited Findings
Inputs are the prices in section 1. The model itself is arithmetic; the only cited items here are the prices and mechanics below.
- Cache-hit multipliers used: GLM-5.3-Flash 0.03/0.15 (20%), DeepSeek V4.1 Flash 0.006/0.30 (2%), Gemini 3.8 Flash 0.075/0.75 (10%), GLM-5.3 0.26/1.40 (19%), Haiku 4.5 0.10/1.00 (10%), Kimi K3 0.30/3.00 (10%). — [Z.ai](https://docs.z.ai/guides/overview/pricing), [DeepSeek](https://api-docs.deepseek.com/quick_start/pricing), [Google](https://ai.google.dev/gemini-api/docs/pricing), [Anthropic](https://platform.claude.com/docs/en/about-claude/pricing), [Kimi](https://platform.kimi.ai/docs/pricing/chat)
- Prior-art cost check: A-Mem reports about 1,200 tokens and about $0.0003 per memory operation on commercial APIs (consistent with the order of magnitude here for a small structured call). — [A-MEM](https://arxiv.org/html/2502.12110) (via note 14)
- Hugging Face free accounts get $0.10/month of routed credits and PRO accounts $2.00/month, which bound what a no-card user can spend. — [HF billing docs](https://huggingface.co/docs/inference-providers/pricing)

### Inferences (the model)
Definitions (per user message = one "turn"; month = 30 days; light 1,500 turns, heavy 9,000, whale 30,000):
- **Reply call:** 3,000 in / 300 out on the reply model. **Cache on:** 70% of input tokens are prefix hits (static system prompt + character card + append-only history; volatile memory/state block placed last). **Cache off:** 0%.
- **Arch A (single call):** reply only.
- **Arch B (recommended default):** A + 0.4 gated side call (1,000 in / 150 out, utility model) + 0.2 extraction per turn (2,000 in / 300 out, utility model; the extraction call size is my assumption). No caching on utility calls (conservative).
- **Arch C (premium):** A + a structured-thinking call every turn (2,000 in / 400 out, on the reply-class model, 50% cache) + 0.2 extraction + background offstage jobs: 2 characters x (3,000 in / 600 out) every 20 turns on the reply-class model, no cache, no batch. **C-lite** runs thinking and background jobs on the utility model instead.
- Cost of a call = (uncached_in x P_in + cached_in x P_cache + out x P_out) / 1e6.

Per-turn worked example, GLM-5.3-Flash + Qwen3.7-Flash, cache on:
- Reply: 2,100 cached x 0.03 + 900 x 0.15 + 300 x 0.50 = 63 + 135 + 150 = 348 (in units of $1e-6), so $0.000348.
- Side (x0.4): (1,000 x 0.03 + 150 x 0.13) / 1e6 = $0.0000495, times 0.4 = $0.0000198. Extraction (x0.2): (2,000 x 0.03 + 300 x 0.13) = $0.000099, times 0.2 = $0.0000198.
- Arch B per turn = 0.000348 + 0.0000198 + 0.0000198 = $0.000388. Monthly: light 1,500 x = $0.58; heavy 9,000 x = $3.49; whale 30,000 x = $11.63. Cache off: $0.00064 per turn ($0.96 / $5.76 / $19.19).
- Whale token volume for reference: 30,000 turns = 90M input and 9M output tokens per month on the reply model alone.

Effects worth stating:
- **Prompt caching:** saves 40-45% on cheap models (GLM Flash $0.90 to $0.52 light Arch A), 49% on DeepSeek, 42% on Gemini, and 42% on Haiku (before Anthropic's 1.25x write premium on new tokens, which adds roughly 8-9% back for Haiku). Cache only works if the prompt is prefix-stable: static blocks first, history append-only, retrieved memories and the state line last, no rewriting of the rolling summary each turn.
- **Cheap utility model:** moving side and extraction calls from a Luna-class ($0.10/$0.50) to a Qwen-Flash-class ($0.03/$0.13) model cuts utility cost about 3.5x ($0.000140 to $0.000040 per turn in Arch B), but utility is only about 10% of Arch B on a cheap reply model, so it matters far more in Arch C.
- **Arch C is roughly 2x Arch B** when thinking and background jobs run on the reply model (1.23 vs 0.58 light; 24.68 vs 11.63 whale on the cheap stack); **C-lite** brings it to 1.28x of B ($0.74 / $4.47 / $14.90).
- **Off-peak:** DeepSeek off-peak halves the price; background/offstage jobs can be queued to 10:00-01:00 UTC or weekends. Arch A whale on DeepSeek off-peak cached is about $9.64/month vs $19.28 at peak.
- **Local reply + cloud mind:** if the reply runs locally (zero marginal cost) and only thinking, extraction and background jobs go to a cloud utility model, the cloud bill is $0.22 (light), $1.34 (heavy), $4.46 (whale) per month on Qwen3.7-Flash and $0.80 / $4.77 / $15.90 on GPT-6 Luna. Economically, "speak locally, think in the cloud" is the cheapest way to sell "premium cognition".
- **Sensitivities not in the table:** regenerations/swipes (assume +20-30% turns), longer contexts (an 8k-token prompt makes a cheap-model reply about 2.2x dearer uncached), retries on malformed JSON, and voice (section 3), which dwarfs text cost when hosted.
- **Break-even against a flat rate:** Featherless's $25 flat plan equals pay-per-token Arch B cached on GLM-5.3-Flash at about 64,000 turns/month (2,150/day), or about 255 turns/day on GLM-5.3 and 303/day on Haiku 4.5. Below those volumes, per-token is cheaper; flat rates are a bet on big models plus heavy users.
- **Free-credit coverage:** an HF PRO user's $2 credit covers about 5,150 turns (cached) or 3,100 (uncached) of Arch B on GLM-5.3-Flash, roughly 100-170 turns/day; the $0.10 free credit covers about 160-260 turns. (Assumes HF providers pass through cache pricing; see Gaps.)

### Gaps
- Real Kataki token counts per call (extraction size, side-call gating rate, background-job frequency) are not measured; the 0.4 / 0.2 / one-in-20 rates are my assumptions and should be replaced by telemetry from the engine.
- Actual cache-hit ratios depend on Kataki's prompt assembly and provider TTL; 70% is an estimate.
- Regeneration/swipe rates and real msgs/day distribution of paying roleplay users were not found (no source).

---

## 3. Voice and image add-on costs

### Takeaway
Hosted TTS costs 10-100x more than the text of the same reply ($0.0036-0.058 per spoken minute vs about $0.0004 per turn of text), so voice must be local-by-default (Kokoro, Apache 2.0, CPU-capable per note 18) or metered. Images cost $0.003-0.06 each depending on model; 20-100 images a month adds $0.3-5, comparable to the whole text bill, so images should be a capped quota or credits.

### Cited Findings
**TTS**
- ElevenLabs API: Flash/Turbo $0.04 per 1,000 characters; Multilingual v2 and v3 $0.08 per 1,000 characters. Plans: Free $0 (10,000 characters), Starter $6, Creator $22 (1,000,000 characters), Pro $99 (4,500,000). — [ElevenLabs API pricing](https://elevenlabs.io/pricing/api)
- Together TTS per 1M characters: Kokoro-82M $4, Orpheus $15, Cartesia Sonic-3 $65. Novita: Fish Audio and standard TTS $15 per 1M characters. — [Together](https://www.together.ai/pricing), [Novita](https://novita.ai/pricing)
- OpenAI: tts-1 $15 per 1M characters; gpt-4o-mini-tts about $0.60/M text plus $12/M audio-output tokens. Note 18 puts gpt-4o-mini-tts at about $0.015/min. — [OpenAI pricing](https://developers.openai.com/api/docs/pricing), note 18 (`18_voice_embodiment.md`)
- Google: Gemini 3.8 Flash TTS $0.50 in (text) / $9.00 out (audio) per 1M tokens, 3.8 Flash-Lite TTS $0.50 / $6.00, both promotional through 31 Dec 2026; 3.1 Flash TTS Preview $1 / $20. — [Google Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Note 18 conversion: about 150 wpm is about 900 characters per spoken minute; Cartesia direct is reported at about $0.03/min (conflicts with Together's $65/M-character Sonic-3 listing, which is about $0.058/min); realtime speech-to-speech agents cost $0.02-0.46/min. — note 18 (`18_voice_embodiment.md`), [CloudTalk via note 18](https://www.cloudtalk.io/blog/cartesia-pricing/)

Cost per spoken minute at 900 characters/minute (my arithmetic): Kokoro-82M hosted $0.0036; $15/M-character engines (Orpheus, Novita, tts-1) $0.0135; ElevenLabs Flash $0.036; ElevenLabs v2/v3 $0.072; Cartesia Sonic-3 (Together list) $0.0585. A 300-token reply is about 1,100 characters, about 1.2 spoken minutes, so a voiced reply costs $0.0044 (hosted Kokoro), $0.0165 ($15/M), $0.044 (ElevenLabs Flash). A light user voicing every reply (1,500 x 1.2 min): about $6.5 hosted Kokoro, $24 at $15/M, $65 on ElevenLabs Flash.

**Images**
- Together per image: FLUX.2 [dev] $0.0154, FLUX.2 [pro] $0.03, Qwen Image 2.0 $0.04, GPT Image 1.5 $0.034, Imagen 4.0 Ultra $0.06. — [Together pricing](https://www.together.ai/pricing)
- fal: Seedream V4 $0.03/image, Flux Kontext Pro $0.04, Nanobanana $0.0398, Qwen $0.02 per megapixel (priced on 1MP output). — [fal pricing](https://fal.ai/pricing)
- Replicate: Flux Schnell $3.00 per thousand images ($0.003 each), Flux Dev $0.025, Flux 1.1 Pro $0.04; GPU per second: T4 $0.000225, L40S $0.000975, A100 80GB $0.0014, H100 $0.001525. — [Replicate pricing](https://replicate.com/pricing)
- Novita: Qwen-Image text-to-image and edit $0.02/image. — [Novita pricing](https://novita.ai/pricing)
- Google: Gemini 3.1 Flash Image $0.045-0.151 per image by resolution; 3.1 Flash-Lite Image $0.0336 at 1K; 3 Pro Image $0.134-0.24. — [Google Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
- HF hf-inference bills compute time x hardware price (example: a 10 s FLUX.1-dev request on a $0.00012/s machine = $0.0012), but as of July 2025 hf-inference is mostly CPU models; image gen goes through third-party providers. — [HF billing docs](https://huggingface.co/docs/inference-providers/pricing)

Monthly image bill (my arithmetic): 20 images: $0.06 (Replicate Schnell), $0.31 (FLUX.2 dev), $0.40 (Qwen Image), $0.60 (Seedream / FLUX.2 pro), $0.90 (Gemini Flash Image 1K). 100 images: $0.30 / $1.54 / $2.00 / $3.00 / $4.50.

### Inferences
- A voice-every-reply light user on a hosted $0.015/min engine (about $24/month) costs 40x the light-user text bill ($0.58), so hosted voice cannot sit inside a $5-8 plan. Options: local Kokoro/Piper by default, hosted voice via credits or a minutes quota, or BYOK for ElevenLabs/Cartesia.
- ElevenLabs Creator ($22 for 1M characters, about 1,100 spoken minutes) is effectively $0.02/min; reselling minutes at cost-plus is not attractive versus letting users bring their own key.
- Images: a cheap consistent-character pipeline at $0.015-0.03/image supports about 100 images per $2-3, so a monthly quota of 30-60 images fits a $8 plan, with more via credits. Hosted providers' rules on NSFW images were not checked (Gaps); many hosted APIs restrict it, so NSFW images are best left to local or BYOK.
- Nothing here prices latency; TTS time-to-first-audio and image queue time matter more than the last 30% of price.

### Gaps
- Google Cloud TTS (Standard/WaveNet/Neural2/Chirp) price page did not render; not reported. Gemini TTS per-minute cost needs the audio-tokens-per-second rate, not retrieved.
- ElevenLabs Starter's 273,000-character figure came from the summariser and looks odd; verify before quoting.
- Provider content policies (NSFW images/voices) not retrieved.
- Local costs (electricity, user GPU) are zero to Kataki but not zero to the user; not quantified.

---

## 4. What competitors charge, and the margins that implies

### Takeaway
Hosted companion apps cluster at $10-25/month (Character.AI+ $9.99, Janitor Pro $9.99, Backyard AI Standard $12, Nomi $15.99, Replika Pro $19.99, NovelAI Opus $25, Featherless Chat $25), with cheaper $5-6 entries and $30-35 top tiers. With 2026 token prices, a cheap-model stack costs $0.6-12/month per active user, so those prices imply 70-95% gross margins on typical users, if the competitor runs a cheap or self-hosted model. SillyTavern and its peers monetise nothing and push inference cost to the user (BYOK/local).

### Cited Findings
| Product | Price | Notes | Source (reliability) |
|---|---|---|---|
| NovelAI | Paper free (50 text gens, 30 images, 100 TTS); Tablet $10; Scroll $15; Opus $25/month | Opus: 10,000 Anlas/month, 28,672-token context, unlimited text and TTS and free images up to 1024x1024, exclusive Xialong/Krake/Llama 3 Erato models | [NovelAI docs](https://docs.novelai.net/en/subscription) (primary, may be dated) |
| Featherless | Chat $25; Developer $50 (per token); Business custom | See section 1 | [Featherless](https://featherless.ai/pricing) (primary) |
| Character.AI c.ai+ | $9.99/month or $94.99/year; free tier with ads and slower peak; reported new "lite" $2.99/month or $1.49/week (search snippet, unverified) | Paid tier does not unlock NSFW; claims 6M+ daily actives, 70-80 minute average sessions | note 02, [aicompanionguides](https://aicompanionguides.com/blog/character-ai-subscription-2026/), [SolidAITech](https://www.solidaitech.com/2026/06/c-ai-character-ai.html) (secondary) |
| Nomi | $15.99/month, $39.99/quarter, $99.99/year; indefinite free tier | Listed unlimited messages and voice, 40 image requests/day, 10 Nomis | note 02, [WeavAI](https://weavai.app/blog/en/2026/04/08/nomi-ai-review-2026-full-analysis-of-three-tier-memory-system-voice-calls-and-ai-companion-features/), [Fostera](https://fostera.ai/blog/replika-vs-nomi-vs-kindroid) (secondary) |
| Kindroid | Sources conflict: Standard $13.99 web / $15.99 app store, about $139.99/year, Ultra $24.99; a free Lite tier; one source says $9.99 entry | Proactive "Away" messages reported Ultra-only | note 02 (secondary, conflicting) |
| Replika | Pro $19.99/month or $69.99/year; Ultra $29.99/month or $119.99/year; lifetime about $299.99 | Sources disagree on whether monthly still exists | note 02 (secondary, conflicting) |
| Janitor AI | Free about 50 messages/day on JanitorLLM; Pro $9.99/month ($99.99/year) for up to 1,000 messages/day | Most users plug in third-party models | note 02, [Dupple](https://dupple.com/tools/janitorai) (secondary) |
| Backyard AI | Free (300 messages/week, 1 model, 16k tokens); Standard $12; Pro $35/month | Desktop app deprecated; hosted web and iOS remain | note 02, [Arcanum RPGs](https://arcanumrpgs.com/blog/sillytavern-alternatives/) (secondary) |
| Candy.ai / CrushOn | from $5.99/month (annual) / $4.99/month | | note 02 (secondary) |
| Chub (Mercury/Venus) | not found | Chub uses a bring-your-own-API model per note 02; pricing page returned 403 | (Gap) |
| SillyTavern | free, AGPL-3.0, 33.9k GitHub stars, "will always be free and open sourced"; user brings keys or local models | | [GitHub](https://github.com/SillyTavern/SillyTavern) (primary) |
| Mistral Le Chat (reference for "credits in a sub") | Free ($10/month API credits); Pro $14.99 ($15 credits); Team $24.99/user | | [Mistral pricing](https://mistral.ai/pricing) |

### Inferences
- Token budget a competitor price buys at 60% target gross margin (price x 0.4 / cost per turn, Arch B, cached): $10 buys about 10,300 turns/month (340/day) on GLM-5.3-Flash-class; about 1,200 turns/month (40/day) on GLM-5.3 class ($0.00327/turn). So "unlimited" $10-16 plans on quality-tier models are only viable if the median user sends far fewer than 100 messages a day, or the operator runs cheap in-house models. Character.AI's 70-80 minute sessions suggest tens to low hundreds of messages a day, so their economics rely on cheap or in-house inference and ads on the free tier (inference, not sourced).
- Janitor's "1,000 messages/day" Pro cap and Nomi's "unlimited" are whale exposures: at Kataki's cheap stack a whale costs $11-20/month, so a $10-16 plan is roughly break-even on whales and highly profitable on the median user.
- NovelAI's Opus at $25 with an exclusive 28k-context model and free images shows there is a market for $25 tiers when the differentiator is a proprietary model; Kataki's differentiator is cognition, not a model, so the ceiling is more like $10-15.
- Featherless's $25 vs per-token math (section 2) shows flat rates only beat token pricing above roughly 255 turns/day on quality models.

### Gaps
- Primary pricing pages for Character.AI, Nomi, Kindroid, Replika, Janitor, Chub, Backyard, Candy and CrushOn were unreachable (403/404/JS shells); all these prices are second-hand and several conflict (Kindroid, Replika).
- No competitor gross margins are published; margin figures above are implications of token prices, not disclosures.
- c.ai lite tier (Sept 2026) unverified.

---

## 5. Business models and licence choices

### Takeaway
The precedent set in this niche is: free open-source app + user pays for inference (SillyTavern, RisuAI, Agnai, Front Porch), or a free core app with paid convenience services (Obsidian's Sync $4-5/month, Publish, a $25 supporter licence; Hugging Face PRO $9 with bundled credits). Backyard AI's desktop shutdown shows the risk of a cloud-funded local-first product with no open code. For Kataki, an open-core hybrid (free local app, optional paid cloud sync and hosted models on fair-use plus credits) has the best margin/consumer-friendliness balance; AGPL-3.0 is the licence most similar tools chose.

### Cited Findings
**Precedents**
- SillyTavern: AGPL-3.0, 33.9k stars, free forever, no pricing. — [GitHub](https://github.com/SillyTavern/SillyTavern)
- Front Porch AI (closest local-first competitor, note 02): AGPL-3.0 from v0.9.0 (GPLv3 in v0.8.x), described in its README as a "modified hosted copy has to publish its changes"; no funding or pricing model disclosed; explicitly "a home for Backyard AI refugees" with a built-in importer for Backyard's `.byaf` character archives, crediting Backyard's team for open-sourcing the `.byaf` format when the desktop app shut down. — [Front Porch AI](https://github.com/Lufou/front-porch-AI)
- RisuAI GPL-3.0; Agnai AGPL-3.0 (activity slowed, last commit June 2026); Backyard AI: desktop app deprecated, hosted web and iOS only. — note 02, [Arcanum RPGs](https://arcanumrpgs.com/blog/sillytavern-alternatives/)
- Jan (local AI app): Apache-2.0, 44.7k stars; the README shows no monetisation plan. — [GitHub](https://github.com/janhq/jan)
- Open WebUI: BSD-3-Clause up to v0.6.6 (April 2025), then BSD-3 plus a branding-protection clause (branding may be removed only for 50 or fewer users in 30 days, substantive contributors, or enterprise licence holders); rationale: entities "strip out branding, repackage work as their own, and monetize it". — [Open WebUI licence docs](https://docs.openwebui.com/license/)
- Obsidian: free for personal use "without limits"; Sync $4/month annual or $5 monthly; Publish $8/$10 per site; Catalyst $25 one-time supporter licence; optional commercial licence $50 per user per year; "100% user-supported". — [Obsidian pricing](https://obsidian.md/pricing)
- Hugging Face PRO $9/month includes $2 of compute credits; Mistral Pro $14.99 includes $15 of API credits (the "subscription includes at-cost credits" pattern). — [HF pricing](https://huggingface.co/pricing), [Mistral pricing](https://mistral.ai/pricing)
- Payment platform costs (merchant-of-record): Paddle 5% + 50 cents per transaction; Lemon Squeezy 5% + 50 cents (base). — [Paddle pricing](https://www.paddle.com/pricing), [Lemon Squeezy pricing](https://www.lemonsqueezy.com/pricing)

**Model menu**

| Model | Pros | Cons / risks |
|---|---|---|
| Fully open source + BYOK | Zero inference cost and liability; matches SillyTavern culture; HF PRO $2 credits give users a cheap start | No revenue; support cost falls on you; donations only |
| Open-core (free local app; paid cloud sync, hosted models, premium cognition) | Obsidian/HF pattern; sync is nearly free to run; hosted inference priced at 55-80% margin | Needs hosted-tier compliance (section 6); free-to-paid conversion unknown |
| One-time purchase | Consumer-friendly; Backyard history and Front Porch's audience show demand for owning the app | A lifetime price cannot fund unbounded hosted inference; only sell local/BYOK features one-time |
| Credits / pay-as-you-go | Aligns cost with usage; no whale risk; fixed fee bites small packs (Paddle 5% + $0.50 is 15% of a $5 pack, 10% of $10) | Users dislike meters; refund/expiry rules |
| Flat sub with fair-use cap | Predictable for users; cap protects margin | Needs a visible counter and a cheap default model |
| Hybrid routing | Local reply + cloud mind costs cents (section 2) | Complexity; quality drop on 8 GB local models |

### Inferences
- Licence: AGPL-3.0 on the app and engine fits the niche (SillyTavern, Front Porch, Agnai) and blocks someone from running a modified hosted clone without publishing changes, which is the main commercial threat to a hosted-tier business. If Kataki wants to keep the option of a proprietary hosted service or app-store distribution, the author holds copyright and can dual-license, but that requires a contributor licence agreement from day one. (Reasoning from Front Porch's stated rationale; I did not verify AGPL/App Store compatibility. Widely reported to be problematic for GPL-family licences; unverified here.)
- Alternatives: Apache-2.0/MIT (Jan) maximises adoption but lets anyone resell a hosted version; a source-available/BSL/FSL licence protects the hosted business but excludes Kataki from the "free software" community that SillyTavern users expect and reduces contributions. Open WebUI's branding clause is a middle path but adds friction. (Sentry's FSL and BSL terms were not fetched; mention as options only.)
- Open formats matter: Backyard's `.byaf` being open-sourced let Front Porch build an importer after the shutdown. Kataki should publish its character/story export format and keep it importable, as a credibility signal for "your data survives us".
- Consumer-friendly rule of thumb: never sell something with unbounded marginal cost for a one-time price; do sell the local app free, a supporter licence (about $25, Catalyst precedent), sync at $3-4, and hosted inference by cap or credit.
- Hybrid routing default: run side/extraction/offstage jobs on a cheap cloud utility model (or local 3-8B if a GPU exists) and let the user pick where the reply runs; "speak locally, think in the cloud" bill is $0.2-4.5/month (section 2).

### Gaps
- Sentry FSL/BSL details and other source-available precedents (fetch of the FSL template 404'd).
- No data on free-to-paid conversion rates for Obsidian Sync, Backyard, or any roleplay app.
- AGPL vs Apple/Google store terms, and CLA practice in this niche, not verified.
- Backyard's reasons for deprecating desktop not retrieved (only the fact of it, via note 02).

---

## 6. Payment-processor, app-store, age-verification and companion-law constraints (brief)

### Takeaway
A free local/BYOK app carries little of this. A paid hosted tier with companion-style chat brings: Stripe will not process explicit adult content (including AI-generated), Apple requires IAP (15% under $1M/year, 30% above) plus content filters, reporting and age restriction, Google Play bans sexual content, and California SB 243 (in force since 1 Jan 2026) plus several other state laws impose disclosure, crisis-protocol and reporting duties with a $1,000-per-violation private right of action. Design the paid tier as SFW-by-default with adult content only on local/BYOK.

### Cited Findings
- Stripe restricted list: prohibits "adult services", "pornography and other mature audience content ... designed for the purpose of sexual gratification", and "any artificial-intelligence generated content that meets the above criteria". No separate AI-companion category was found in the fetched text. — [Stripe restricted businesses](https://stripe.com/legal/restricted-businesses)
- Paddle: 5% + 50 cents per transaction as merchant of record; its acceptable-use page returned 404 so its adult/AI stance is unchecked. Lemon Squeezy 5% + 50 cents. — [Paddle pricing](https://www.paddle.com/pricing), [Lemon Squeezy pricing](https://www.lemonsqueezy.com/pricing)
- Apple: 1.1.4 prohibits overtly sexual or pornographic material; 1.2 UGC needs filtering, reporting, blocking and contact info; 1.2.1 creator content needs age restriction; 3.1.1 requires in-app purchase for subscriptions, features and premium content; 4.7 covers chatbots and mini apps with the same privacy, moderation, IAP and age-restriction rules. — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- Apple Small Business Program: 15% commission up to $1M annual proceeds, 30% above; eligibility re-tested yearly. — [Apple](https://developer.apple.com/app-store/small-business-program/)
- Google Play: "We don't allow apps that contain or promote sexual content or profanity, including pornography"; fetched excerpt did not include the AI-generated-content policy or the service-fee rates. — [Google Play policy](https://support.google.com/googleplay/android-developer/answer/9878810)
- California SB 243: companion chatbot = AI system with natural-language interface giving human-like responses that sustains relationships across interactions; excludes customer-service, productivity, game and voice-assistant bots; operators must disclose AI status when a reasonable person could be misled; for known minors, disclose AI, remind every 3 hours, and prevent sexually explicit content; must maintain and publish suicide/self-harm protocols with crisis referral; annual reporting to the Office of Suicide Prevention from 1 July 2027; private right of action for injunctive relief, damages up to $1,000 per violation and attorney fees. — [SB 243 text via leginfo](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB243)
- Other states (from note 17, citing Orrick and FPF): New York requires disclosure at start and every 3 hours; Oregon and Washington (effective 2027-01-01) add minor-safety protocols and $1,000-per-violation private actions; Nebraska and Idaho from 2027-07-01. — note 17 (`17_needs_goals_offscreen_life.md`), [Orrick 2026 state chatbot laws](https://www.orrick.com/en/Insights/2026/04/2026-State-Chatbot-Laws-Key-Provisions-and-Regulatory-Trends), [FPF](https://fpf.org/blog/understanding-the-new-wave-of-chatbot-legislation-california-sb-243-and-beyond/)
- Age assurance vendors: k-ID advertises a free "AgeKit" age-classification product across 200+ jurisdictions and mentions the proposed US GUARD Act (would ban under-18 use of AI companions) and 42 state AGs urging child safeguards; Yoti cites the UK Online Safety Act (fines up to 10% of global turnover) and the ICO Children's Code; neither publishes per-check prices. — [k-ID](https://k-id.com), [Yoti](https://www.yoti.com/business/age-verification/)

### Inferences
- Whether a local or BYOK desktop app makes Kataki an "operator" under SB 243 is a legal question I did not answer; a hosted paid service clearly does. Budget compliance work (3-hour reminder toggle for minors or age-gate, crisis protocol page, disclosure banner, reporting from July 2027) into the hosted tier, not the free app. Not legal advice.
- Card processing for a SFW hosted tier via Paddle/Lemon Squeezy (about 5% + $0.50) or Stripe (standard rates not fetched) is viable; NSFW hosted content is a processor-termination risk (Stripe explicitly names AI-generated adult content), so adult content should be local/BYOK only and not sold.
- App-store distribution adds a 15-30% cut plus IAP; on a $7.99 plan that removes $1.20-2.40 versus $0.90 on Paddle. Start on web and desktop (already Kataki's targets) and treat mobile stores as later.
- Age verification cost per user is unknown; at low volume a declared-age gate plus SFW default is the cheapest, and the free k-ID tier is a candidate for classification only.

### Gaps
- Stripe's standard card fee (2.9% + 30c in the US) is common knowledge but its pricing page did not yield text; not cited.
- Paddle acceptable-use page 404; Paddle's actual stance on AI companions/NSFW unknown.
- Google Play service fee and AI-content policy text not retrieved.
- Per-check age verification prices (Yoti, Persona, k-ID paid) not public/retrieved; Persona pricing page returned 403.
- Provider (HF providers, OpenRouter models, DeepSeek) acceptable-use terms for roleplay/NSFW via a reseller not checked.

---

## 7. Deliverables: (a) cost-per-user table, (b) pricing/licensing packages, (c) cheapest-good model picks

### Takeaway
On cheap-good models, a $7.99 hosted plan with a 5,000-reply fair-use cap keeps 47-78% of list price as margin after payment fees and inference (63% at the cap with caching); "premium cognition" adds about 2x cost on the same model or about 1.3x if run on a nano utility model. Quality-tier reply models (GLM-5.3, Haiku 4.5, Kimi K3) must be credits-only.

### Cited Findings
All price inputs are cited in sections 1-3 and 6; the tables below are arithmetic on them (assumptions in section 2).

### Inferences

#### (a) Cost per active user per month ($, cache on / cache off), by profile x architecture x model choice
Light = 1,500 turns, heavy = 9,000, whale = 30,000. Reply/utility pair per row.

| Reply model + utility model | Arch | Light 50/day | Heavy 300/day | Whale 1000/day |
|---|---|---|---|---|
| **GLM-5.3-Flash + Qwen3.7-Flash** ($0.15/$0.50; $0.03/$0.13) | A | 0.52 / 0.90 | 3.13 / 5.40 | 10.44 / 18.00 |
| | B | **0.58 / 0.96** | **3.49 / 5.76** | **11.63 / 19.19** |
| | C | 1.23 / 1.79 | 7.41 / 10.75 | 24.68 / 35.84 |
| | C-lite | 0.74 | 4.47 | 14.90 |
| **DeepSeek V4.1 Flash direct, peak + gpt-oss-20b** ($0.30/$1.20; $0.03/$0.14) | A | 0.96 / 1.89 | 5.78 / 11.34 | 19.28 / 37.80 |
| | B | 1.03 / 1.95 | 6.15 / 11.71 | 20.50 / 39.02 |
| | C | 2.42 / 3.78 | 14.50 / 22.70 | 48.33 / 75.67 |
| | C-lite | 1.19 | 7.17 | 23.89 |
| (same, off-peak: halve rows; Arch A whale cached = 9.64) | | | | |
| **Gemini 3.8 Flash promo + Gemini 2.5 Flash-Lite** ($0.75/$3.75; $0.10/$0.40) | A | 2.94 / 5.06 | 17.62 / 30.38 | 58.73 / 101.25 |
| | B | 3.13 / 5.25 | 18.77 / 31.53 | 62.57 / 105.09 |
| | C | 7.19 / 10.33 | 43.17 / 62.00 | 143.90 / 206.67 |
| | C-lite | 3.65 | 21.92 | 73.06 |
| (after 1 Jan 2027 Gemini 3.8 rate doubles: roughly 2x these rows' reply share) | | | | |
| **GLM-5.3 + GPT-6 Luna** ($1.40/$4.40; $0.10/$0.50) | A | 4.69 / 8.28 | 28.13 / 49.68 | 93.78 / 165.60 |
| | B | 4.90 / 8.49 | 29.39 / 50.94 | 97.98 / 169.80 |
| | C | 10.95 / 16.25 | 65.70 / 97.51 | 219.00 / 325.02 |
| | C-lite | 5.48 | 32.90 | 109.68 |
| **Claude Haiku 4.5 + GPT-6 Luna** ($1/$5; $0.10/$0.50) | A | 3.92 / 6.75 | 23.49 / 40.50 | 78.30 / 135.00 |
| | B | 4.12 / 6.96 | 24.75 / 41.76 | 82.50 / 139.20 |
| | C | 9.57 / 13.75 | 57.42 / 82.53 | 191.40 / 275.10 |
| **Kimi K3 + GPT-6 Luna** ($3/$15; $0.10/$0.50) | A | 11.75 / 20.25 | 70.47 / 121.50 | 234.90 / 405.00 |
| | B | 11.95 / 20.46 | 71.73 / 122.76 | 239.10 / 409.20 |
| | C | 28.50 / 41.05 | 171.00 / 246.33 | 570.00 / 821.10 |
| **Local reply + cloud "mind" only** (thinking + extraction + offstage on utility) | Qwen3.7-Flash | 0.22 | 1.34 | 4.46 |
| | GPT-6 Luna | 0.80 | 4.77 | 15.90 |

Per-turn cost, Arch B cached: GLM-5.3-Flash stack $0.000388; DeepSeek peak $0.00068; Gemini 3.8 promo $0.00209; GLM-5.3 $0.00327; Haiku 4.5 $0.00275; Kimi K3 $0.00797. Excludes: regenerations (+20-30%), Anthropic cache-write premium (+8-9% on Haiku), retries, voice, images, sync/storage, support, chargebacks, free-tier subsidy.

#### (b) Three pricing/licensing packages (margin = share of list price left after payment fees and inference; my arithmetic; Paddle 5% + $0.50 unless stated)

**Package 1: "Open and Yours" (community, no hosted inference)**
- Free, AGPL-3.0 app and engine (local llama.cpp + BYOK to HF/OpenRouter/DeepSeek/others), published export format; optional Supporter licence about $25 one-time (Obsidian Catalyst precedent); optional Sync $4/month or $3.33 annual (Obsidian precedent $4-5).
- Margin: Supporter $25 leaves $23.25 after fees = 93%; Sync at $4 leaves $3.30 after fees, about 78% of list after an assumed $0.20/user/month storage cost (not researched). No inference cost, no SB 243 operator exposure for the free app (legal question open).
- Consumer-friendly: no meter, the app never stops working; users can use HF PRO's $2 credits (about 3,100-5,150 Arch-B turns on GLM-5.3-Flash) or free local models.

**Package 2: "Kataki Plus" (open-core hosted, fair-use)**
- $7.99/month or about $69/year. Includes sync, the hosted cheap-good default (GLM-5.3-Flash class, Arch B with local or nano-utility "mind") up to about 5,000 replies/month (about 165/day) with a visible counter; past the cap the app offers credits or BYOK, never a hard lock-out of local mode. Voice is local by default; premium cognition (Arch C-lite) counts as 1.3x replies.
- Margin (cost includes $0.10 sync): typical user at 40% of cap: $0.88 cost, 78% of list (74% via Apple 15%, 59% via Apple 30%); a full-cap user with caching: $2.04 cost, 63% (59% / 44%); full cap without caching: $3.30 cost, 47%. Whale users are capped by design.
- Stretch tier "Max" $19.99 for 20,000 replies is only viable on the cheap stack: 53% of list with caching, 28% without; not recommended unless cache hit rate is proven.
- Compliance: SFW-by-default hosted content, AI disclosure, crisis protocol, age gate (SB 243 and state analogues); adult content only local/BYOK.

**Package 3: "Credits" (pay-as-you-go, quality and extras)**
- $10 minimum pack (a $5 pack loses 15% to the fixed fee); credits priced at provider cost x 1.5 and never expire (expiry rules not researched); usable for quality reply models, hosted voice, images, and overflow past the Plus cap; shown as replies or a dollar balance, not tokens.
- Margin: 23% of list at 1.5x markup (19% at 1.4x, 10% at 1.25x) after Paddle fees; add 5.5% more cost if traffic is relayed through OpenRouter (direct provider accounts avoid it).
- What $10 buys (provider cost $6.67): about 17,000 Arch-B replies on GLM-5.3-Flash, about 2,000 on GLM-5.3, about 2,400 on Haiku 4.5, about 840 on Kimi K3; about 400 spoken minutes at $0.0165/min; or about 220-430 images at $0.015-0.03 (all cost-basis arithmetic).

Recommended combination: ship Package 1 immediately (it is the default product), add Package 2 when hosted routing exists, and use Package 3 as the overflow valve. This keeps a real free tier, no "kidney-priced" tier, and never makes the whale a loss.

#### (c) Cheapest-good cloud model picks (price-based; roleplay quality needs a Kataki eval)
- **Reply (default):** GLM-5.3-Flash at $0.15/$0.50, cache $0.03, on the cheapest host that returns structured output when needed (Baseten, DeepInfra or Fireworks per the HF flags; Novita/Together/Z.ai flag it false). Alternative: DeepSeek V4.1 Flash direct with thinking off ($0.30/$1.20 peak, $0.15/$0.60 off-peak, cache $0.006/$0.003), best for cache-heavy long histories and for queueing background jobs off-peak.
- **Reply (quality tier, credits only):** GLM-5.3 ($1.40/$4.40; DeepInfra $0.90/$4.00) or Claude Haiku 4.5 ($1/$5, cache $0.10) for predictable behaviour; Kimi K3 ($3/$15) only for showcase. Avoid building margin on Gemini 3.x Flash until its Jan 2027 doubled price is known.
- **Reply (roleplay-tuned, cheap):** Cydonia 24B v4.1 ($0.30/$0.50), Euryale 70B ($0.65/$0.75) or Novita's Stheno/Lunaris 8B ($0.05/$0.05) exist on OR/HF at low prices; unevaluated here.
- **Utility (side call, extraction, JSON):** Qwen3.7-Flash ($0.03/$0.13 up to 32K prompt, cache $0.006), gpt-oss-20b (DeepInfra $0.03/$0.14; Groq $0.10/$0.50 at 737 tokens/s; structured output true on every listed host; reasoning tokens bill as output), GPT-6 Luna ($0.10/$0.50, cache $0.01) as the reliable-JSON fallback, Gemini 2.5 Flash-Lite ($0.10/$0.40). Do not build on the free GLM-4.7-Flash/4.5-Flash tier.
- **Background offstage/dream jobs:** DeepSeek off-peak, or any host's batch variant (50% off: GLM-5.3-Flash batch $0.06/$0.20 on OR, Gemini and Mistral batch 50%), since they are not latency-bound.
- **Voice:** local Kokoro/Piper by default; hosted only via credits ($0.0036/min hosted Kokoro to $0.036/min ElevenLabs Flash). **Images:** FLUX.2 dev ($0.0154) or Qwen-Image ($0.02) hosted; Replicate Flux Schnell ($0.003) for cheap drafts.

### Gaps
- All margins exclude free-tier subsidy, refunds/chargebacks, VAT/sales-tax handling (a merchant of record absorbs it, included in Paddle's fee), support, engineering, and marketing. They are unit economics, not a P&L.
- Actual Kataki telemetry (turns/day, cache-hit rate, gating rate) is needed to replace the assumed workload.
- Legal questions (operator status of a BYOK app, AGPL and app stores, credits expiry) need counsel, not desk research.
