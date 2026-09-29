# Cheapest local inference stack for a human-like character "mind" on consumer hardware (implementation note for Kataki, as of 2026-09-29)

Scope and method. Workload taken from notes 10, 11, 14 and 17: per turn one generation (inline thought header + stance/want + reply, optionally state deltas), a rule-based gate that rarely adds a blocking structured call, an async afterthought, batched offstage/dream jobs at time skips and scene close, CPU-side emotion classifier and embeddings, and no second resident LLM on 8 GB. WebSearch quota was exhausted, so everything below comes from direct fetches of Hugging Face model cards/APIs, the llama.cpp repo (README, PRs, issues, benchmark discussions), and `llama-server --help` of the build already in `D:/Kataki/.runtime/llama.cpp` (version 0.4.1-dev, build 11043). Where I computed something rather than read it, it is under Inferences and labelled "my arithmetic". Numbers in Inferences are estimates, not measurements; section 8 lists what Kataki must measure itself.

Local facts that shape everything: the dev GPU is an RTX 5060 Laptop, 8151 MiB (nvidia-smi); the only LLM on disk is `Qwen3.5-9B-Q4_K_M.gguf` (5.68 GB, 5,680,522,464 bytes); the image chain peaks at 7.03 GB and a spill past 8 GB costs 10-400x ([rules-and-gotchas](D:/Kataki/docs/images/rules-and-gotchas.md)), so LLM and image generation cannot be resident together.

---

## 1. Best small open models per hardware tier (general models, roleplay finetunes, licences, structured-output reliability)

### Takeaway
The 2026 small-model field is Qwen3.5 (0.8B/2B/4B/9B, hybrid Gated-DeltaNet, Apache 2.0) and Gemma 4 (E2B/E4B/12B/26B-A4B/31B, now Apache 2.0), with Qwen3.6/3.8 only at 27B and 35B-A3B and up, Ministral 3 (3B/8B/14B, Apache 2.0) as the dense non-hybrid alternative. For 8 GB the practical chat model is Qwen3.5-9B Q4 (already on disk); Gemma 4 12B QAT Q4_0 (6.98 GB) needs a 12 GB card. Roleplay finetunes exist for every family but I found no independent quality ranking of them (UGI and EQ-Bench pages did not render through fetch).

### Cited Findings
**Families, sizes, licences**
- Qwen3.5-9B: 9B params, hybrid Gated DeltaNet architecture, 262,144 native context, Apache 2.0, released Feb 2026, thinking on by default (disable with `enable_thinking: false`; no `/nothink` soft switch). Recommended sampling: general thinking T=1.0 top_p 0.95 top_k 20 presence_penalty 1.5; non-thinking T=0.7 top_p 0.8 top_k 20. — [Qwen3.5-9B card](https://huggingface.co/Qwen/Qwen3.5-9B); [Unsloth GGUF card](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF)
- Qwen3.5 sizes present on HF: 0.8B, 2B (both created 2026-02-28, plus Base), 4B, 9B, 27B, 35B-A3B, 122B-A10B, 397B-A17B. Qwen3.5-2B is non-thinking by default, Apache 2.0, 24 layers, IFEval 61.2 and MMLU-Pro 55.3 (non-thinking). — [Qwen HF API listing](https://huggingface.co/api/models?author=Qwen&sort=createdAt&direction=-1&limit=40); [Qwen3.5-2B card](https://huggingface.co/Qwen/Qwen3.5-2B)
- Newer Qwen: Qwen3.6-27B and 35B-A3B (April 2026), Qwen3.8-27B (2026-08-05), Qwen3.8-2.4T-A95B and Flash-Next; no Qwen3.6/3.8 small (<=9B) dense models appeared in the listing, and the Qwen3.8-27B card mentions none. Qwen3.6-35B-A3B: 40 layers (10 x [3 gated DeltaNet + 1 gated attention]), 256 experts, 8+1 active, Apache 2.0. — [Qwen HF API listing](https://huggingface.co/api/models?author=Qwen&sort=createdAt&direction=-1&limit=40); [Qwen3.6-35B-A3B card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B); [Qwen3.8-27B card](https://huggingface.co/Qwen/Qwen3.8-27B)
- Gemma 4 family: E2B, E4B, 12B "Unified", 26B A4B (MoE), 31B dense; released May-July 2026; Apache 2.0 (Gemma 3 used Gemma terms); native `system` role; thinking toggled by `<|think|>` in the system prompt; native function calling. E4B is 4.5B effective / 8B with per-layer embeddings, E2B 2.3B effective / 5.1B with embeddings. — [Gemma 4 E4B card](https://huggingface.co/google/gemma-4-E4B-it); [E2B card](https://huggingface.co/google/gemma-4-E2B-it); [12B card](https://huggingface.co/google/gemma-4-12B-it); [Google HF listing](https://huggingface.co/api/models?author=google&sort=createdAt&direction=-1&limit=30)
- Gemma 4 12B QAT Q4_0 GGUF from Google: 6.98 GB, 11.95B params, 256K context, sliding window 1024, Apache 2.0, MMLU-Pro 77.2. Unsloth quants of the same model: IQ3_XXS 4.64, Q3_K_M 5.69, IQ4_XS 6.38, Q4_0 6.74, UD-Q4_K_XL 7.37, Q6_K 9.79, Q8_0 12.7 GB; recommended sampling T=1.0 top_p 0.95 top_k 64, thinking off unless needed. — [Google QAT GGUF card](https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf); [Unsloth Gemma 4 12B GGUF](https://huggingface.co/unsloth/gemma-4-12b-it-GGUF)
- Gemma 4 E4B GGUF (ggml-org): Q4_0 4.59 GB, Q8_0 8.03 GB, Apache 2.0. — [ggml-org E4B GGUF](https://huggingface.co/ggml-org/gemma-4-E4B-it-GGUF)
- Qwen3.5-9B GGUF sizes (Unsloth): 3-bit 4.02-5.05 GB, 4-bit 5.17-5.97 GB, 5-bit 6.36-6.74 GB, 6-bit 7.46-8.76 GB; UD-Q4_K_XL of the MTP variant 6.14 GB. — [Unsloth Qwen3.5-9B GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF); [Unsloth Qwen3.5-9B-MTP GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-MTP-GGUF)
- Qwen3.6-35B-A3B needs about 17 GB (3-bit), 23 GB (4-bit), 30 GB (6-bit) of memory; Unsloth gives no consumer-GPU CPU-offload speeds. — [Unsloth Qwen3.6 guide](https://unsloth.ai/docs/models/qwen3.6)
- Ministral 3 8B Instruct (Dec 2, 2025): 8.4B LM + 0.4B vision, 256k context, Apache 2.0, native function calling and JSON output, strong system-prompt adherence; 3B and 14B siblings exist. — [Ministral-3-8B card](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512); [Mistral HF listing](https://huggingface.co/api/models?author=mistralai&sort=createdAt&direction=-1&limit=20)
- Mistral Small 4 is a 119B model (Jan 2026) and Mistral Medium 3.5 is 128B; nothing in the Mistral Small class at 24B was newer than Devstral-Small-2-24B in the listing. GLM-5.3-Flash is 320B total / 18B active (MIT), i.e. not a local consumer model; GLM-4.7-Flash (Jan 2026) is the smaller GLM in the listing (size not fetched). SmolLM3-3B dates from July 2025 and the newest HuggingFaceTB entries are tiny (nanowhale-100m). — [Mistral listing](https://huggingface.co/api/models?author=mistralai&sort=createdAt&direction=-1&limit=20); [GLM-5.3-Flash card](https://huggingface.co/zai-org/GLM-5.3-Flash); [zai-org listing](https://huggingface.co/api/models?author=zai-org&sort=createdAt&direction=-1&limit=15); [HuggingFaceTB listing](https://huggingface.co/api/models?author=HuggingFaceTB&sort=createdAt&direction=-1&limit=15)
- LFM2.5-1.2B-Instruct: 1.17B, 32k context, IFEval 86.23, "under 1 GB", 239 tok/s on an AMD CPU (vendor claim), recommended for data extraction, agentic tasks and RAG, not for knowledge-heavy work; licence is the custom "LFM1.0 license". — [LFM2.5 card](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct)

**Roleplay finetunes (existence and popularity only)**
- Qwen3.5 base: ArliAI Qwen3.5-{4B,9B,27B,35B,122B}-RpRMax-v1 (2026-04-28); mradermacher `Qwen3.5-text-9B-NSFW-RP-RolePlay` GGUF (34.7k downloads, Aug 24); DavidAU "Defiant-Fable-Uncensored-Heretic" 9B MTP GGUF (1.78M downloads); HauhauCS "Uncensored-Aggressive" 9B (713k); Jackrong distills onto 9B. — [ArliAI listing](https://huggingface.co/api/models?author=ArliAI&sort=createdAt&direction=-1&limit=15); [Qwen3.5-9B derivatives](https://huggingface.co/api/models?search=Qwen3.5-9B&sort=downloads&direction=-1&limit=25); [Qwen3.5 RP search](https://huggingface.co/models?search=qwen3.5+rp&sort=downloads)
- Gemma 4 base: HauhauCS Gemma4-12B-QAT-Uncensored "Balanced" (800k downloads; Q4_K_M 6.9 GB, plus a 242 MB speculative draft head; claims 0/465 refusals, ~60% faster with MTP; the card lists the "Gemma" licence while Google's card says Apache 2.0, so check the licence text per file); mradermacher `gemma-4-12b-it-roleplay-sft` (6.75k downloads); `gemma-4-26B-roleplay-v2` (4.1k). TheDrummer: Artemis-31B v1.2 (2026-09-25), Orion-26B-A4B v1.1 (2026-09-13), both Gemma 4 based. — [Gemma 4 12B derivatives](https://huggingface.co/api/models?search=gemma-4-12b&sort=downloads&direction=-1&limit=15); [HauhauCS card](https://huggingface.co/HauhauCS/Gemma4-12B-QAT-Uncensored-HauhauCS-Balanced); [TheDrummer listing](https://huggingface.co/api/models?author=TheDrummer&sort=createdAt&direction=-1&limit=25)
- Mistral/Llama base: TheDrummer Rocinante-X-12B-v1 (2026-01-19), Rocinante-XL-16B-v1 (2026-04-18), Magidonia-24B-v4.3 (2025-11-29), Skyfall-31B-v4.2 (2026-02-13), Anubis-Mini-8B-v1 (Llama 3.3 base, 2026-01-01). — [TheDrummer listing](https://huggingface.co/api/models?author=TheDrummer&sort=createdAt&direction=-1&limit=25)

**Structured-output evidence**
- Qwen3.5 instruction-following/tool scores (mode not stated on the card): 9B IFEval 91.5, IFBench 64.5, MultiChallenge 54.5, BFCL-V4 66.1; 4B IFEval 89.8, IFBench 59.2, MultiChallenge 49.0, BFCL-V4 50.3. — [Qwen3.5-9B card](https://huggingface.co/Qwen/Qwen3.5-9B)
- Ministral 3 8B advertises native JSON output and function calling; Gemma 4 advertises native function calling. — [Ministral card](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512); [Gemma 4 E4B card](https://huggingface.co/google/gemma-4-E4B-it)
- Format restrictions can lower reasoning quality, with the drop growing as the format gets stricter ("Let Me Speak Freely?"). — [arXiv 2408.02442](https://arxiv.org/abs/2408.02442)
- Kataki's own eval log (note 14): small models wrote gists as specific as details until schema and prompt were tightened. — [note 14 gaps](14_memory_forgetting.md)

### Inferences
- Tier picks (details and numbers in section 9): CPU-only Qwen3.5-4B or Gemma 4 E4B; 4 GB Qwen3.5-4B Q4; 6 GB Gemma 4 E4B Q4_0 or Qwen3.5-4B Q6; 8 GB Qwen3.5-9B Q4_K_M (default, on disk) with Gemma 4 12B at Q3_K_M/IQ4_XS as an experiment; 12-16 GB Gemma 4 12B QAT Q4_0, or a 24-31B finetune at Q3/Q4, or Qwen3.6-35B-A3B with experts on CPU; Apple 16 GB Gemma 4 12B QAT or Qwen3.5-9B.
- Grammar guarantees syntax, not semantics: a 4B model under a JSON schema will always emit parseable JSON but may still pick the wrong `stance` enum or invent state deltas. Reliability tiers I would assume until measured: 9B/12B good for the O1 inline thought header and small state deltas; 4B fine for the thought header and a flat 5-8 field JSON, weak for multi-entity relationship deltas; 0.8-2B only for single-purpose extraction or classification with a flat schema.
- Because Kataki's characters are fiction with mature themes, finetunes matter mostly for refusal behaviour and prose style; base Qwen3.5/Gemma 4 instruct models should be the default and RP finetunes an opt-in picker entry. Finetune licences follow the base model but the card must be read (see HauhauCS mismatch above).
- All the "Apache 2.0" models above allow commercial use, so licence is not a discriminator between Qwen3.5, Gemma 4 and Ministral 3. EmbeddingGemma stays on Gemma terms (section 2). LFM2.5's custom licence needs a read before bundling.

### Gaps
- No independent RP-quality ranking of any finetune or base model: `eqbench.com/creative_writing.html` loaded without data and the UGI Space returned only its shell; EQ-Bench repo README has no table. A blind A/B inside Kataki (note 10 proposes thought-on/off A/B) is the only reliable source.
- Sizes of Gemma 4 26B-A4B and 31B GGUFs and of GLM-4.7-Flash were not fetched, so the 12-16 GB tier for MoE/large dense is only sized by analogy (Qwen3.6-35B-A3B figures above).
- Licence terms of each RP finetune were not read.
- No source for Qwen3.5-4B/2B/0.8B Q4 file sizes; estimated in section 9.

---

## 2. Utility models for side jobs (extraction, classification, appraisal JSON, summaries) and CPU-side classifiers/embeddings

### Takeaway
Run side jobs either as a second slot of the same GPU model when chat is idle (best quality, no extra memory), or on a separate CPU-only llama-server with a 0.8-2B model (Qwen3.5-0.8B/2B, LFM2.5-1.2B). Emotion labelling and embeddings should stay off the LLM entirely: GoEmotions INT8 ONNX (125 MB) and the existing 32M static embedder, with bge-small/Qwen3-Embedding-0.6B as optional upgrades.

### Cited Findings
- `SamLowe/roberta-base-go_emotions-onnx`: 28 GoEmotions labels, INT8 ONNX 125 MB (499 MB full precision), about 5x faster than full-precision Transformers on an 8-core 11th-gen i7 at batch size 1, MIT; quantised metrics accuracy 0.475, precision 0.582, recall 0.398, F1 0.447 (almost identical to full precision). Absolute ms per text was not stated. — [model card](https://huggingface.co/SamLowe/roberta-base-go_emotions-onnx)
- Qwen3-Embedding-0.6B: 0.6B params, 28 layers, 32k context, embeddings 32-1024 dims, MTEB multilingual mean 64.33, instruction-aware (+1-5% with an instruction), Apache 2.0; no official GGUF on the card (259 community quantisations exist). — [card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)
- EmbeddingGemma-300m: 768-d with MRL to 512/256/128, 2048-token context, MTEB v2 English 69.67 (768-d), governed by Gemma terms (accept licence to download), not float16-safe (float32/bfloat16). — [card](https://huggingface.co/google/embeddinggemma-300m)
- Kataki's current embedder is `potion-retrieval-32M` (model2vec, 125 MB, about 1-2 ms/text on CPU) and the embedding upgrade ladder (bge-small, nomic, EmbeddingGemma) is already analysed. — [note 14 section 4](14_memory_forgetting.md)
- Qwen3.5-2B is non-thinking by default (Apache 2.0); LFM2.5-1.2B scores IFEval 86.23 (vendor) and targets extraction; Ministral 3 has a 3B tier and Gemma 4 E2B (2.3B effective) exists. — [Qwen3.5-2B card](https://huggingface.co/Qwen/Qwen3.5-2B); [LFM2.5 card](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct); [Gemma 4 E2B card](https://huggingface.co/google/gemma-4-E2B-it)
- llama-server can serve embeddings (`--embedding`, `--pooling`) and reranking (`--rerank`) as dedicated endpoints; `--prio` supports low priority (-1) for a background process. — local `llama-server --help` (build 11043)
- Kataki spec figure: a CPU-only 3-4B utility model runs about 10-20 tok/s, acceptable because extraction is idle-time; note 14 estimates a dream job (3k in, 600 out) at 30-60 s on a CPU 3-4B. — [note 14 section 4/7.9](14_memory_forgetting.md)

### Inferences
- Utility options ranked by cost: (1) code + GoEmotions ONNX for affect labels, zero LLM (note 11 option 1); (2) same-model second slot (`-np 2`) with thinking off, run only when chat is idle and cancellable; (3) CPU process with Qwen3.5-2B Q4 (about 1.4 GB, my estimate from 2B x ~5 bits) for extraction with a flat schema; (4) 4B CPU for summarisation/dream quality. Option (2) shares weights, so its memory cost is one more KV slot (about 0.26 GB per 8k of Qwen3.5-9B context, my arithmetic in section 6) but it competes for GPU decode with the chat call, hence idle-only scheduling as note 17 already specifies.
- CPU prefill dominates side-job time. My rough range for a 2-4B Q4 model on a modern 8-14 core laptop is 50-250 prompt tok/s (unsourced), so a 3k-token dream prompt costs 12-60 s before any output; keep offstage prompts to 1-1.5k tokens (note 17's 1.2k-in figure) and make them batched, one call for all present characters.
- Emotion classifier plus embeddings on CPU cost tens of ms per turn combined and must never touch the GPU; the GoEmotions F1 of 0.447 means it is a noisy signal, so feed it into the PAD update with low weight (note 11 already treats it that way) and let the LLM's own label win when they disagree.

### Gaps
- No measured ms/text for GoEmotions INT8, bge-small, Qwen3-Embedding-0.6B or EmbeddingGemma on the target CPUs (i9-13900H class); listed in section 8.
- No head-to-head extraction-quality data for 0.8B/2B/4B on Kataki's schemas; LFM2.5's IFEval is vendor-reported.
- The LFM1.0 licence terms were not read.

---

## 3. llama.cpp / llama-server features that cut cost, plus alternative runtimes

### Takeaway
llama-server already has what Kataki needs: automatic prompt (prefix) caching, host-RAM prompt cache for idle slots, context checkpoints for hybrid and sliding-window models, flash attention, unified KV, speculative decoding (draft model, MTP, n-gram), JSON-schema/GBNF constraints, a sleep-on-idle mode and a router mode. The big trap is that Qwen3.5 (hybrid recurrent) and Gemma 4 (sliding window) cannot use KV shifting or `--cache-reuse`; they rely on checkpoints, which have open bugs and a coarse default spacing. Other runtimes: KoboldCpp for the all-in-one single-exe path, Ollama only if Kataki accepts less control, EXL3/MLX/vLLM/WebLLM as niche options.

### Cited Findings
**Caching and memory (llama-server, build 11043 help and README)**
- `--cache-prompt` default on; per-request `cache_prompt` default true ("re-use KV cache from a previous request if possible"). `--cache-reuse N` (`n_cache_reuse` per request) = min chunk size to reuse via KV shifting, default 0 (off). — local `llama-server --help`; [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
- `--cache-ram` default 8192 MiB (-1 unlimited, 0 off); `--cache-idle-slots` (default on, needs cache-ram) saves idle slots to the RAM prompt cache when a new task arrives; `--kv-unified` default on when slots are auto; `--parallel` default -1 (auto); `--slot-prompt-similarity` default 0.10; request field `id_slot` pins a slot. — local `llama-server --help`; [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
- `--ctx-checkpoints` (alias `--swa-checkpoints`) default 32 per slot; `--checkpoint-min-step` default 8192 tokens minimum spacing (0 = no minimum). Checkpoints hold the sliding-window/recurrent state and are restored instead of reprocessing the prompt. — local `llama-server --help`; [PR 15293](https://github.com/ggml-org/llama.cpp/pull/15293)
- Why SWA/hybrid models cannot shift: "when the window slides, we 'forget' the old KV stuff and there is no way to recover it without recomputing it", which blocks prefix caching, context shifting and cache reuse; the SWA cache size is `PAD(n_swa*n_seq_max + n_batch)`; `--swa-full` restores a full-size SWA cache. — [PR 13194](https://github.com/ggml-org/llama.cpp/pull/13194)
- Open/closed problems with checkpoints on hybrid models: #24055 (open, Jun 2026) "context checkpoints always invalidated on hybrid/recurrent models" after the `--checkpoint-min-step` change (previously `--checkpoint-every-n-tokens` worked); #22746 (Qwen 3.6 27B, closed) full 53k-token reprocess despite 15 checkpoints; #24714 (Qwen3.5-2B-MTP, closed as not planned) same warning "forcing full prompt re-processing due to lack of cache data (likely due to SWA or hybrid/recurrent memory)"; #25913 (open, Jul 2026) `/slots` save/restore silently loses prompt reuse on hybrid models because checkpoints are not persisted; #20755 (closed, Mar 2026) images in multi-turn reprocessed each turn on Qwen3.5. — [#24055](https://github.com/ggml-org/llama.cpp/issues/24055); [#22746](https://github.com/ggml-org/llama.cpp/issues/22746); [#24714](https://github.com/ggml-org/llama.cpp/issues/24714); [issue search](https://github.com/ggml-org/llama.cpp/issues?q=is%3Aissue+qwen3.5+prompt+reprocess+checkpoint)
- `--context-shift` default disabled. `--flash-attn` default `auto`. KV type flags `-ctk/-ctv` accept f32, f16, bf16, q8_0, q4_0, q4_1, iq4_nl, q5_0, q5_1 (default f16). `--fit` (default on) adjusts unset arguments to fit device memory, with `--fit-target` margin per device and `--fit-ctx` minimum context 4096. `--sleep-idle-seconds` (default off) unloads model weights and KV after idle and wakes on the next request; `/props` reports `is_sleeping`. — local `llama-server --help`; [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
- KV quantisation quality: one measured datapoint, Qwen2.5-Coder-7B perplexity F16/F16 8.3891 vs Q8_0/Q8_0 8.3934 (+0.0043); a user reported q4_0 giving "weird results" on Qwen2-7B while q8_0 was fine. — [discussion 5932](https://github.com/ggml-org/llama.cpp/discussions/5932)

**Speculative decoding**
- Types in `--spec-type`: `draft-simple`, `draft-eagle3`, `draft-mtp`, `draft-dflash`, `draft-dspark`, `ngram-simple`, `ngram-map-k`, `ngram-map-k4v`, `ngram-mod`, `ngram-cache`; n-gram types need no extra model (ngram-mod pool about 16 MB, recommended `--spec-type ngram-mod,ngram-map-k4v --spec-ngram-mod-n-match 24 --spec-ngram-mod-n-min 48 --spec-ngram-mod-n-max 64`); if a draft model and draftless decoding are both set, draftless wins; the docs give no guidance on hybrid models, sampling temperature or JSON grammar and no throughput numbers. Draft defaults: `--spec-draft-n-max 3`. — [speculative.md](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md); local `llama-server --help`
- MTP merged 2026-05-16 (PR 22673): uses the model's own MTP heads from the same GGUF via `--spec-type draft-mtp`; about 75% acceptance with 3 draft tokens; example speed 7 to 21 tok/s; prompt processing gets slower. Unsloth Qwen3.5-9B-MTP card: `--spec-type draft-mtp --spec-draft-n-max 6 -ngl 99 -c 8192 -fa on`, "~1.5-2x faster", and `--parallel >1` and `--mmproj` are not supported with MTP; Unsloth Qwen3.6-35B-A3B guide says about 1.2x with `--spec-draft-n-max 2` and about 1 GB extra headroom. HauhauCS claims ~60% for its Gemma 4 12B draft head; Google ships a 0.4B "assistant" MTP drafter for Gemma 4 12B ("up to 3x", llama.cpp support not stated on its card). — [PR 22673](https://github.com/ggml-org/llama.cpp/pull/22673); [Unsloth MTP card](https://huggingface.co/unsloth/Qwen3.5-9B-MTP-GGUF); [Unsloth Qwen3.6 guide](https://unsloth.ai/docs/models/qwen3.6); [HauhauCS card](https://huggingface.co/HauhauCS/Gemma4-12B-QAT-Uncensored-HauhauCS-Balanced); [Gemma 4 12B assistant card](https://huggingface.co/google/gemma-4-12B-it-assistant)
- Qwen3.5-9B config has `mtp_num_hidden_layers: 1`. — [config.json](https://huggingface.co/Qwen/Qwen3.5-9B/raw/main/config.json)

**Constrained output**
- Server takes `response_format` (json_schema), `grammar` (GBNF), `chat_template_kwargs` (e.g. `{"enable_thinking": false}`), `reasoning` on/off/auto, custom `samplers` order; response `timings` include `prompt_per_second`, `predicted_per_second` and cache counts (`prompt_n + cache_n + predicted_n` = context used). — [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
- GBNF performance gotcha: repeated optionals (`x? x? x?`) are very slow, use `x{0,N}`; JSON-schema conversion: `additionalProperties` defaults false, `prefixItems` broken, numeric `minimum/maximum` integers only, nested `$ref` broken, `pattern` must be anchored, `uniqueItems/contains/not/if-then-else` unsupported. — [grammars README](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md)
- JSONSchemaBench (Guidance, Outlines, llama.cpp, XGrammar, OpenAI, Gemini on 10K schemas) exists but the abstract gives no per-engine speed overhead numbers. — [arXiv 2501.10868](https://arxiv.org/abs/2501.10868)

**Multi-model routing**
- llama-server router mode: `--models-dir`, `--models-preset` (INI), `--models-max` (default 4, 0 unlimited), `--models-autoload`; models load on first request and the least-recently-used is evicted at the limit; each model is its own process; `/models/load` and `/models/unload` exist. — [HF blog](https://huggingface.co/blog/ggml-org/model-management-in-llamacpp); [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
- llama-swap: one Go binary plus one YAML, hot-swaps llama-server (or any OpenAI/Anthropic-compatible server) per request, TTL unload, matrix/concurrent-model DSL, Windows via WinGet. — [llama-swap repo](https://github.com/mostlygeek/llama-swap)
- Control vectors: `--control-vector`, `--control-vector-scaled FNAME:SCALE`, `--control-vector-layer-range` are start-up flags; note 11 already records that they are static per server and unsupported on MoE. — local `llama-server --help`; [note 11 section 9](11_emotion_mood_anxiety.md)

**Other runtimes**
- KoboldCpp: single self-contained exe, ContextShift, fast forwarding of already-processed tokens, smart context, quantised KV (f16/q8/q4), CUDA/Vulkan/Metal, `--gpulayers -1` autofit, OpenAI-compatible API, and bundled Stable Diffusion image generation, Whisper STT and TTS (Kokoro, Qwen3TTS, OuteTTS) in one process. — [KoboldCpp wiki](https://github.com/LostRuins/koboldcpp/wiki)
- Ollama: default context 4096, KV type is a single global env var (`OLLAMA_KV_CACHE_TYPE` f16/q8_0/q4_0), `OLLAMA_KEEP_ALIVE` default 5 min, `OLLAMA_MAX_LOADED_MODELS` default 3 (CPU) or 3x GPUs, `OLLAMA_NUM_PARALLEL` default 1 with RAM scaling as parallel x context. — [Ollama FAQ](https://docs.ollama.com/faq)
- ExLlamaV3 v0.0.6: NVIDIA-only (CUDA 12.4+), Windows and Linux, EXL3 2-8 bit, KV cache 2-8 bit, speculative decoding, lists Qwen 3.5 but Gemma 4 E2B/E4B unsupported; structured output not mentioned. — [exllamav3 repo](https://github.com/turboderp-org/exllamav3)
- vLLM automatic prefix caching is block-hash based; for hybrid Mamba-type models it needs extra flags and EAGLE/MTP; Windows-native support not addressed in the doc. — [vLLM APC docs](https://docs.vllm.ai/en/latest/features/automatic_prefix_caching.html)
- MLX-LM (Apple): rotating KV cache, prompt caching, quantised models via MLX Community, OpenAI-style server; MLX 4/8-bit builds of Gemma 4 12B and Qwen3.5-9B exist from lmstudio-community. — [mlx-lm repo](https://github.com/ml-explore/mlx-lm); [Qwen3.5-9B derivatives](https://huggingface.co/api/models?search=Qwen3.5-9B&sort=downloads&direction=-1&limit=25); [Gemma 4 12B derivatives](https://huggingface.co/api/models?search=gemma-4-12b&sort=downloads&direction=-1&limit=15)
- Browser: WebLLM (WebGPU, JSON-mode structured generation, OpenAI-compatible; docs list Qwen up to 7B, Gemma-2B and do not mention Qwen3.5 or Gemma 4); wllama (llama.cpp in WebAssembly, CPU, 2 GB per file limit so split files, WebGPU since v3.1, multi-thread needs COOP/COEP headers). — [WebLLM](https://github.com/mlc-ai/web-llm); [wllama](https://github.com/ngxson/wllama)
- Latest llama.cpp release page at fetch time showed builds up to b11240 (the page header said "September 28, 2024", which is inconsistent with build numbers; the local build is 11043 from September 2026, so I treat it as 2026-09-28). — [releases](https://github.com/ggml-org/llama.cpp/releases)

### Inferences
- `--cache-reuse` is useless for the two models Kataki is actually targeting (Qwen3.5 hybrid, Gemma 4 SWA) per PR 13194 plus the issue reports; it only helps dense full-attention models (e.g. Mistral-Nemo/Llama-class finetunes) when text is inserted mid-prompt. Do not rely on it as the design.
- With `--checkpoint-min-step 8192` and an 8k chat budget, reading the flag description literally means at most about one checkpoint per prompt, so any divergence before it forces a full reprocess. This is my reading of the help text combined with #24055/#22746, not a measured result; lowering the spacing (e.g. 256-512) is the first thing to test. The first measurement in section 8 is therefore "does turn 2 log 'forcing full prompt re-processing'".
- N-gram speculative decoding should suit Kataki's JSON state deltas because the output echoes many tokens already in the prompt (character names, field names, previous values), at zero VRAM cost; it should help less on free prose replies. This is an inference; the docs give no measured numbers and no guidance on sampling temperature.
- MTP gains quoted (1.2x to 3x) mostly come from greedy or agentic settings; roleplay samples at T about 0.7-1.0, where acceptance should be lower. Expect the low end (about 1.2-1.5x) and treat it as opt-in after a local A/B, especially since MTP blocks `-np > 1`, which conflicts with a background slot on the same server.
- Runtime choice for Kataki: keep llama-server (already integrated, exposes checkpoint/cache/sleep flags, and matches the local `.runtime` build). KoboldCpp is the best "fallback runtime" for users who want one exe covering LLM+image+TTS but it moves the VRAM-sharing problem inside its own process; Ollama hides the flags that matter for cache behaviour; ExLlamaV3 and vLLM are NVIDIA/Linux-centric and not needed; MLX is worth a look only for Apple Silicon (section 7); the web build should call the same local/remote llama-server rather than run in-browser, since WebLLM/wllama do not list the 2026 models.

### Gaps
- No source for LM Studio internals (it embeds llama.cpp/MLX) or for the router-mode INI preset syntax (the README excerpt did not show it).
- No measured throughput for n-gram spec on structured JSON, or for MTP under sampling at RP temperatures.
- Whether `--cache-reuse` works on Qwen3.5 (it should not) was not tested; whether `--swa-full` on Gemma 4 gives reliable prefix reuse and at what memory cost was not tested.
- Unsure if a runtime "sleep now" endpoint exists; the README documents only idle-timeout sleep and router `/models/unload`.

---

## 4. Prompt layout for cache efficiency (where the dynamic state block goes)

### Takeaway
Put everything volatile at the very end of the prompt (after the append-only history, inside or just before the final user turn), keep the prefix byte-identical turn to turn, and evict history in large chunks, not one message per turn. With a hybrid or SWA model the cache can only resume from a checkpoint at or before the first differing token, so a state block injected at depth N forces re-prefill of everything after depth N.

### Cited Findings
- llama-server reuses the KV cache from the previous request when the prompt prefix matches (`cache_prompt`); anything after the first differing token is recomputed unless `--cache-reuse` shifting can recover a chunk (dense models only). — [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md); [PR 13194](https://github.com/ggml-org/llama.cpp/pull/13194)
- For sliding-window/hybrid models, restoring state after a divergence requires a saved checkpoint; checkpoints are stored per slot (default up to 32), spaced at least `--checkpoint-min-step` tokens apart, and idle slots are saved to a host-RAM cache (default 8 GiB). — [PR 15293](https://github.com/ggml-org/llama.cpp/pull/15293); local `llama-server --help`
- KoboldCpp calls the same idea "fast forwarding" (skip already-processed tokens) and offers "smart context" (reserve a buffer so trimming happens less often) and ContextShift for dense models. — [KoboldCpp wiki](https://github.com/LostRuins/koboldcpp/wiki)
- vLLM's prefix cache likewise only helps prefill, and only when a new query shares the prefix. — [vLLM APC docs](https://docs.vllm.ai/en/latest/features/automatic_prefix_caching.html)
- Kataki's context split at 8k (response 600, rules 350, cards+primer 1,400, summaries 900, memory tail 900, flags+directive 250, history remainder) and note 17's plan to inject one 30-60 token state line in the "volatile tail". — [note 14 section 4](14_memory_forgetting.md); [note 17 section 8](17_needs_goals_offscreen_life.md)
- Measured effect of dynamic-block placement on real RP turns: I found no published measurement.

### Inferences
Recommended layout (design proposal, untested):
1. `[SYSTEM: rules + output contract + JSON schema description]` (never changes)
2. `[CHARACTER CARDS + primer]` (changes only on edit)
3. `[SUMMARIES]` (changes only at chunked evictions)
4. `[HISTORY: alternating turns, append-only, no injected blocks]`
5. `[VOLATILE, one block, last: state line (~30-60 tok), thought-seeds, top memories (~900), agenda directive, hold_back]` then the user's latest message (or the volatile block appended to it).

Consequences (my arithmetic on token counts):
- Per turn the re-prefill is: previous assistant reply + new volatile block + new user message, about 300-1,200 tokens; at 2,000-3,500 prompt tok/s on a mid GPU (section 5) that is 0.15-0.6 s, not a 3-6k-token re-read (1-3 s on GPU, 15-60 s on CPU or a base Apple chip).
- Do not keep past volatile blocks in history (they bloat it and change every turn). The cost is that turn t+1 diverges from turn t's cached prompt at the start of turn t's volatile block, so on hybrid/SWA models the runtime must restore a checkpoint taken before that point. Ask llama-server for a checkpoint near the end of the stable history (small `--checkpoint-min-step`), or the divergence will fall behind the last checkpoint and reprocess everything. If measurement shows checkpoints do not work reliably (open issue #24055), fall back to freezing: keep each turn's volatile block in history byte-for-byte (about +100-200 tokens/turn) and drop old blocks only during chunked eviction.
- Evict in chunks with hysteresis: when the prompt hits about 90% of budget, cut history down to about 60% and refresh the summary in the same step. One full re-prefill every 15-25 turns is far cheaper than a moving front edge that invalidates the cache every turn (this is the same idea as KoboldCpp "smart context"). Never use `--context-shift` on Qwen3.5 or Gemma 4.
- Order inside the volatile block matters only mildly: put the fastest-changing items last (seeds/hold_back), memory before agenda.
- Keep the schema and output contract in the static system prefix, not the volatile block; per-request `response_format` json_schema is applied at sampling and does not change the prompt tokens (verify: some templates inject the schema text).
- Different callers (chat vs background) must not share slot 0's prefix by accident: pin chat to `id_slot: 0`, background jobs to another slot or a separate process, otherwise the utility prompt overwrites the chat prefix and the next chat turn re-prefills fully (mitigated by `--cache-idle-slots` saving the chat slot to the RAM cache, but hybrid checkpoint restoration from that cache is exactly what the open issues cast doubt on).

### Gaps
- No published measurement of prefix-cache hit rates or latency for depth-injected state in RP; only the mechanism.
- Whether `--cache-idle-slots` correctly restores hybrid-model checkpoints from the RAM cache (vs `/slots` disk save, known broken in #25913) was not verified.
- How the chat template treats an assistant `thought` field in history (stripped or kept) for Qwen3.5/Gemma 4 was not checked; if the template rewrites earlier assistant turns between requests, the prefix will diverge there. Test with the exact template.

---

## 5. Fusing cognitive steps into one generation vs separate calls, and throughput/latency numbers

### Takeaway
One grammar-constrained generation (thought, stance, reply, then state deltas) is the right default on 8 GB: it avoids a second prefill and keeps state consistent with the reply. Order the fields so the reply stream starts early and the state block comes last. I found no study comparing fused vs split cognition for RP; the only direct evidence is that stricter output formats cost reasoning quality, which argues for a short free-text thought field and a flat schema.

### Cited Findings
- Note 10 already quantifies the options: O1 inline thought +40-80 output tokens, +1-2 s local; O2 two-call +2-4 s local; O3 structured appraisal +2-4 s; O7 async afterthought 0 if the user takes over 3 s; all labelled estimates. — [note 10 section 7](10_inner_thought_subconscious.md)
- Note 11 lists the lagged appraisal (option 3) and the self-label tail (option 2, +10-20 output tokens, small models may mislabel) with the same "estimates, none measured" caveat. — [note 11 section 9](11_emotion_mood_anxiety.md)
- Format restrictions degrade reasoning, more so with stricter formats. — [arXiv 2408.02442](https://arxiv.org/abs/2408.02442)
- Llama 2 7B Q4_0 (3.56 GiB) llama.cpp CUDA scoreboard, pp512 / tg128 tok/s with flash attention: RTX 3060 12 GB 2408 / 76.9 (no FA 2138 / 75.6); RTX 4060 Ti 8 GB 3803 / 64.0; RTX 5060 5783 / 128.2 (listed as 12 GB, which looks like a labelling error since the 5060 is an 8 GB card; treat the row with caution); RTX 3080 10 GB 5570 / 140; RTX 4070 Ti SUPER 7612 / 132.9; RTX 5070 Ti 8420 / 182.4; RTX 4080 9206 / 143.5; RTX 4090 about 11,993 / 186; RTX 5090 about 14,073 / 290. No rows for RTX 4060 desktop, 4070, 3070 or any laptop card in the CUDA thread. — [discussion 15013 (two fetches)](https://github.com/ggml-org/llama.cpp/discussions/15013)
- Vulkan scoreboard (same model): RTX 4060 Mobile 2136 / 59.5; RX 7600 1167 / 58.0; RX 7800 XT 2017 / 118; Intel Arc B580 621 / 70.1; Ryzen AI Max+ 300 1289 / 53.6; Intel Core Ultra 200 iGPU 865 / 24.4; Core Ultra 300 iGPU 1380 / 24.5; Ryzen Z1 Extreme 199 / 18.8; Intel Iris Xe (i7-1185G7) 106 / 5.9. — [discussion 10879](https://github.com/ggml-org/llama.cpp/discussions/10879)
- Apple Silicon (Llama 7B Q4_0, PP512 / TG128): M1 (68 GB/s) 108 / 14.2; M2 (100 GB/s) 180 / 21.9; M3 (100 GB/s) 187 / 21.3; M4 (120 GB/s) 221 / 24.1; M5 (154 GB/s) 723 / 31.9; M5 Pro 1350 / 63.9; M5 Max 987 / 102.9. — [discussion 4167](https://github.com/ggml-org/llama.cpp/discussions/4167)

### Inferences
- Bandwidth model from the rows above (my arithmetic): 4060 Ti gets 64.0 t/s x 3.82 GB = 244 GB/s, which is about 85% of its published 288 GB/s peak (peak figure from my memory, not from a source here); the 3060 gets about 294 GB/s. So predicted decode tok/s is roughly `0.82-0.89 x bandwidth / (model file GB)`. Applied to Kataki's models on a 288 GB/s card: Qwen3.5-9B Q4_K_M (5.68 GB) about 43 t/s; Gemma 4 12B Q4_0 (6.98 GB) about 35 t/s; Qwen3.5-4B (about 2.7 GB, estimated) about 90 t/s. On a 3060 12 GB (about 360 GB/s): 9B about 54, 12B about 44. Hybrid DeltaNet layers, MTP and CPU-offloaded embeddings will shift these by an unknown amount; the RTX 5060 Laptop (dev machine) has no row, so measure it.
- Prompt processing on the same cards for a 9B is probably 2,000-3,500 tok/s (7B Q4_0 does 3,803 on a 4060 Ti; hybrid/12B slower; unmeasured), so a 600-token tail prefill is about 0.2-0.3 s and a cold 6k prompt about 2-3 s.
- Turn timeline for the fused call on the 8 GB default (about 45 t/s decode): tail prefill 0.3 s; hidden thought+stance about 60 tokens = 1.3 s; visible reply 100-200 tokens streams at 45 t/s (2-4 s); state-delta JSON about 80 tokens = 1.8 s after the reply, while the user reads. TTFT for the first visible word is about 1.6 s. Splitting thought into its own call would add a second tail prefill and a second request but no less decode work, hence O1 over O2 on 8 GB.
- Fused schema recommendation (design proposal): flat object, keys in this order, all strings/enums/short arrays, `additionalProperties: false`: `thought` (free text, <=25 words), `stance` (enum), `want` (string), `reply` (string), `state` (object of deltas). Reasons: thought and stance must precede the reply to influence it; deltas after the reply can appraise what was actually said, are off the critical path, and the reply text can be streamed by incremental JSON parsing. Avoid optional chains and nested `$ref`; cap array lengths with `{0,N}` style bounds via `maxItems`.
- Route the rare blocking "slow path" (O3) to the same model with a second, stricter schema; no need for a different model.

### Gaps
- No study found on fused vs separate multi-step cognition for character simulation; the Kataki thought-on/off A/B and a fused-vs-split A/B remain to be run (note 10 gap).
- No measured overhead of grammar-constrained sampling in llama.cpp on 9B/12B models with a 6-10 field schema; JSONSchemaBench abstract lacks speed numbers.
- The desktop RTX 4060, 4070, 3070 and all laptop GPUs are absent from the CUDA scoreboard, so the requested "typical consumer GPUs" numbers are extrapolated from the bandwidth model.

---

## 6. Memory math for context length (KV cache, recurrent state, SWA)

### Takeaway
Both target families have small KV caches: Qwen3.5 has only 8 full-attention layers (about 32 KiB/token at f16) plus a fixed recurrent state; Gemma 4 12B caps sliding layers at a 1024-token window. Context length is therefore not the VRAM problem on 8 GB, the weights are. Dense finetunes (Nemo-class) are the exception.

### Cited Findings
- Qwen3.5-9B config: 32 layers, pattern 3 linear-attention + 1 full-attention repeated 8 times, 16 attention heads, 4 KV heads, head_dim 256, hidden 4096, linear attention 32 value heads with key/value head dim 128 and conv kernel 4, vocab 248,320, untied embeddings, 262,144 context. Qwen3.5-4B: 32 layers, same 24 linear + 8 full pattern, 4 KV heads, head_dim 256, hidden 2560, tied embeddings. — [Qwen3.5-9B config](https://huggingface.co/Qwen/Qwen3.5-9B/raw/main/config.json); [Qwen3.5-4B config](https://huggingface.co/Qwen/Qwen3.5-4B/raw/main/config.json)
- Gemma 4 12B config: 48 layers, pattern 5 sliding + 1 full (8 cycles), 16 heads, 8 KV heads and head_dim 256 for sliding layers, global layers 1 KV head with global_head_dim 512 and `attention_k_eq_v: true`, sliding window 1024, hidden 3840, vocab 262,144. — [Gemma 4 12B config](https://huggingface.co/google/gemma-4-12B-it/raw/main/config.json)
- Gemma 4 E4B config: 42 layers (30 sliding with window 512, 6 full listed), 8 heads, 2 KV heads, head_dim 256, `num_kv_shared_layers` 18, per-layer input embedding table (hidden_size_per_layer_input 262,144 as reported). — [Gemma 4 E4B config](https://huggingface.co/google/gemma-4-E4B-it/raw/main/config.json)
- SWA cache size formula `PAD(n_swa*n_seq_max + n_batch)`; `--swa-full` makes it full-context. — [PR 13194](https://github.com/ggml-org/llama.cpp/pull/13194)

### Inferences (my arithmetic, verify against the server's startup log)
- Qwen3.5-9B/4B KV at f16: 8 layers x 4 KV heads x 256 dim x 2 (K,V) x 2 B = 32 KiB/token, so 8k = 256 MiB, 16k = 512 MiB, 32k = 1 GiB; q8_0 halves that, saving only 128 MiB at 8k, so KV quantisation is not worth the quality risk on Qwen3.5.
- Qwen3.5 recurrent state: 24 linear layers x (32 x 128 x 128 x 4 B, assuming fp32 state) = about 2 MiB/layer, about 48 MiB plus small conv state per sequence and per checkpoint. 16-32 checkpoints then cost roughly 1-2 GB of host RAM, inside the default `--cache-ram` 8192 MiB. The server log prints the true checkpoint size.
- Qwen3.5-9B Q4_K_M at 8k context: 5.68 GB weights + 0.26 GB KV + about 0.05 GB state + compute buffers (unknown, roughly 0.3-0.6 GB) = about 6.3-6.6 GB before the desktop's own VRAM use; that leaves 1-1.5 GB of the 8.15 GB, so 16k context is still fine but a second 6 GB-class resident model, or the 7.03 GB image chain, is not.
- Gemma 4 12B: sliding layers 40 x (8 KV heads x 256 x 2 x 2 B = 8 KiB per token) over about 1.0-3.0k cells (window 1024 plus batch, so `-b`/`-ub` size matters) = 0.3-1.0 GB; global layers 8 x (1 x 512 x 2 x 2 B = 2 KiB per token) = 16 KiB/token = 128 MiB at 8k, 512 MiB at 32k. Total at 8k with the 6.98 GB QAT file plus compute buffers is about 7.6-8.6 GB, so it does not fit an 8.15 GB card comfortably, it is a 12 GB-tier model; Q3_K_M (5.69 GB) or IQ4_XS (6.38 GB) can fit but the quality loss versus QAT Q4_0 is unmeasured.
- Gemma 4 E4B Q4_0 (4.59 GB): 24 layers own KV (42 minus 18 shared), most with a 512 window and 2 KV heads, so KV is under about 0.2 GB at 8k; its 8B-with-embeddings file size overstates the per-token bandwidth (the per-layer embedding table is a lookup), so it may decode faster than a 4.6 GB dense model. Measure.
- A dense 12B (Nemo-class: 40 layers x 8 KV heads x 128 dim by my memory of the config, not fetched) costs about 160 KiB/token f16, i.e. 1.25 GB at 8k and 2.5 GB at 16k, where `-ctk/-ctv q8_0` is worth using.

### Gaps
- Actual llama.cpp state/checkpoint byte sizes for Qwen3.5 and Gemma 4, and real compute-buffer sizes, not measured.
- Mistral-Nemo config values quoted from memory, not fetched.

---

## 7. CPU-only, Apple Silicon and iGPU numbers; sharing 8 GB between LLM, embeddings, TTS and image generation

### Takeaway
CPU-only is viable for a 2-4B chat model at roughly 10-25 tok/s but cold prefill is slow, so cache discipline is mandatory. Apple base chips decode fine but prefill slowly until M5. On 8 GB the LLM and the image chain are mutually exclusive: swap by stopping or sleeping llama-server around image jobs and accept a reload plus a cold prefill on the first turn afterwards.

### Cited Findings
- Local image chain peaks at 7.03 GB; exceeding about 8 GB spills to shared RAM and slows everything 10-400x; user rules: state expected time, check step rate at 30 s, kill spilling runs, never start the user's llama-server. — [rules-and-gotchas](D:/Kataki/docs/images/rules-and-gotchas.md)
- llama-server `--sleep-idle-seconds N` unloads weights and KV after N idle seconds and reloads on the next request; router mode evicts LRU models at `--models-max`; llama-swap adds TTL and matrix groups; Ollama unloads after `OLLAMA_KEEP_ALIVE` (default 5 min). — [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md); [llama-swap](https://github.com/mostlygeek/llama-swap); [Ollama FAQ](https://docs.ollama.com/faq)
- `--mmproj-offload` (default on) and `--no-kv-offload` exist to keep the vision projector or KV cache off the GPU; `--n-cpu-moe N` keeps MoE experts of the first N layers on CPU; `--fit` auto-fits unset args. — local `llama-server --help`
- Kataki embedder and GoEmotions classifier are CPU-only (125 MB each class). — [note 14 section 4](14_memory_forgetting.md); [GoEmotions ONNX card](https://huggingface.co/SamLowe/roberta-base-go_emotions-onnx)
- KoboldCpp bundles Stable Diffusion, Whisper and TTS in the same process as the LLM. — [KoboldCpp wiki](https://github.com/LostRuins/koboldcpp/wiki)
- Apple/iGPU throughput rows: see section 5.

### Inferences
- CPU-only decode is bandwidth bound like the GPU: with dual-channel DDR5-5600 (about 90 GB/s peak, from my memory) and 60-70% efficiency, my estimate is about 20 t/s for a 2.7 GB 4B model, about 10 t/s for the 5.7 GB 9B, and 35-40 t/s for a 1.4 GB 2B, in line with Kataki's own "10-20 tok/s for a CPU 3-4B" spec figure. Cold prefill on CPU is the real cost (tens to low hundreds of tok/s): a 3k prompt is 15-60 s, so CPU-only users get short contexts (4k), the strict cache layout of section 4, and background jobs limited to time skips.
- Apple base-chip arithmetic (scale the 7B Q4_0 row by file size): a 5.7 GB 9B decodes about 16 t/s on M4 and about 21 t/s on M5; a 7 GB 12B about 13 and 17 t/s. Prefill on M4 is only about 221 t/s at 7B, so a cold 3k prompt is about 14 s (M5 about 4 s): the cache layout matters more on Apple than anywhere else. Unified memory is shared with everything, and macOS caps GPU-usable memory below total RAM (exact default not sourced here), so treat a 16 GB Mac as roughly a 10-11 GB VRAM machine, i.e. the 12 GB tier minus the OS.
- iGPU Vulkan rows (24 t/s Intel Core Ultra, 54 t/s Ryzen AI Max+) suggest a 4B model at roughly 15-25 t/s on the best iGPUs, no better than good CPU inference on lesser ones; keep iGPU as "CPU tier plus try Vulkan".
- 8 GB sharing plan (design proposal): (a) chat LLM resident by default (about 6.5 GB); (b) embeddings, GoEmotions and TTS on CPU (TTS choice is note 18's), so they never move VRAM; (c) before any image job the Kataki process manager stops (or sleeps) llama-server, waits until `nvidia-smi` shows near 0 MiB, runs the image chain under the existing run protocol, and lets llama-server start lazily on the next chat request; (d) after a swap, the first turn pays load time (reading 5.7 GB from disk; unmeasured, estimate 2-6 s on NVMe) plus a cold prefill of the whole prompt (about 2-4 s at GPU speeds); hide it behind the image job's completion animation; (e) while images are generating, background offstage jobs must queue or run on the CPU utility process only. `--sleep-idle-seconds 600` covers the idle case for free.
- An alternative for 8 GB when image generation is frequent: a 4B chat model (about 2.7-3.5 GB with context) would leave room to keep the image chain's offloaded weights from spilling, but the image chain already peaks at 7.03 GB alone, so co-residence still fails; no LLM larger than about 1 GB co-resides with it. Swap is the answer at this tier.

### Gaps
- No measured llama-server load time or wake-from-sleep time for the 5.7 GB model on the target SSD.
- No sourced macOS GPU memory cap; no source for DDR5 bandwidth or CPU prefill rates (estimates flagged).
- NVIDIA's "CUDA sysmem fallback policy" driver setting (Prefer No Sysmem Fallback) would turn silent LLM spills into out-of-memory errors instead of 10x slowdowns; the NVIDIA KB page returned 403, so this is unverified from my own knowledge. It is also a system setting, so I only flag it for the user to consider, I have not touched it.
- TTS VRAM figures are out of scope here (note 18).

---

## 8. Hardware tier table (a)

### Takeaway
Everything below assumes thinking off, `json_schema` output, and the section 4 layout. Speeds are my bandwidth-model estimates (`0.82-0.89 x BW / file GB`) anchored on the sourced scoreboards, not measurements; "features on" follows the note 10/11/14/17 designs.

### Cited Findings
Anchors for the table (details in sections 1, 5, 6): Qwen3.5-9B Q4 5.17-5.97 GB and Q3 4.02-5.05 GB; Gemma 4 12B QAT Q4_0 6.98 GB; Gemma 4 E4B Q4_0 4.59 GB; Llama 2 7B Q4_0 scoreboard (3060 12 GB 76.9 t/s, 4060 Ti 8 GB 64.0, 4060 Mobile Vulkan 59.5, M4 24.1, M5 31.9); all Apache 2.0 except LFM2.5 (custom) and EmbeddingGemma (Gemma terms).

### Inferences
| Tier | Chat model (default / alt) | Utility (side jobs) | Expected decode tok/s (chat) | Cold prefill of a 4k prompt | Cognition features on |
|---|---|---|---|---|---|
| CPU-only, 16 GB RAM, 8+ cores | Qwen3.5-4B Q4_K_M (about 2.7 GB est.) / Gemma 4 E4B Q4_0 (4.59 GB) | Same process sequentially, or Qwen3.5-0.8B/2B CPU; GoEmotions ONNX + potion embedder | about 10-20 (4B) | about 20-60 s (est.), so context <=4k, strict cache layout | State machines in code (needs, mood, PAD), GoEmotions labels, gate, lexical leak check; O1 thought header as a short tagged field (not full JSON) or off; extraction on scene close only; offstage at time skips only (about 1 call/skip, 1-2 min); no dreams during chat |
| 4 GB VRAM | Qwen3.5-4B Q4_K_M, ctx 6-8k (about 3.1-3.5 GB with KV, est.) | Same model, idle slot or CPU 2B | about 60-90 (est.) | about 2-4 s | Above plus O1 JSON thought header, batched offstage (O8), async afterthought (O7) on chosen turns; slow-path gate at low budget |
| 6 GB VRAM | Gemma 4 E4B Q4_0 (4.59 GB) or Qwen3.5-4B Q6/Q8 (quality); test Qwen3.5-9B Q3_K_M (4.0-5.05 GB) at 4-6k ctx | Same model second slot when idle | about 50-80 (est.) | about 2-3 s | Full cheap default (O1, gate, O7, O8, O10, leak check, one-call dream on scene close) with 4B-class caveats: keep state deltas to <=6 fields |
| 8 GB VRAM (Kataki default) | Qwen3.5-9B Q4_K_M (5.68 GB, on disk), ctx 12-16k; alt Gemma 4 12B Q3_K_M/IQ4_XS (5.7-6.4 GB) only if it beats the 9B in A/B | Same model, `id_slot 1`, idle only; CPU Qwen3.5-2B/LFM2.5 optional; GoEmotions + embedder on CPU | about 40-55 (dev 5060 Laptop unmeasured; 4060 Ti-class about 43) | about 2-3 s | Full cheap default incl. slow-path O3 on gated turns (10-25% of turns), O9 ensemble for 3+ char groups (3-4 chars), O11 consolidation, dream jobs at idle (about 15 s GPU per character) ; MTP or n-gram spec optional |
| 12-16 GB VRAM | Gemma 4 12B QAT Q4_0 (6.98 GB, 32k ctx fits) / a Gemma 4 26-31B or Mistral-24B RP finetune at Q3-Q4 on 16 GB / Qwen3.6-35B-A3B with `--n-cpu-moe` and 32 GB RAM | Same model second slot; embeddings on CPU | 12B about 35-45 (3060 12 GB about 44); larger models about 15-30 (est.) | about 1.5-3 s | Everything in the 8 GB tier plus O5-style per-character passes at skips, longer memory prompts (1.5k), premium-local dream (600 out) every big skip; more tracked characters (5-6) |
| Apple Silicon 16 GB (M-series) | Gemma 4 12B QAT Q4_0 or Qwen3.5-9B Q4_K_M via llama.cpp Metal (MLX builds exist as an alternative) | Same model second slot; keep CPU work light | M4 about 13-16, M5 about 17-21 | M4 about 14 s, M5 about 4 s | 8 GB tier features, but on M1-M4 keep prompts short and evict in big chunks; offstage jobs at skips only |

### Gaps
- Every tok/s and prefill figure is an estimate; the RTX 5060 Laptop (dev machine) has no scoreboard row.
- No sourced number for 12-16 GB MoE offload (Qwen3.6-35B-A3B) or for 24-31B finetune speeds.

---

## 9. Recommended llama-server configuration for Kataki's 8 GB default (b)

### Takeaway
One chat llama-server on the GPU with the 9B at Q4_K_M, thinking off at server level, small checkpoint spacing, RAM prompt cache, sleep-on-idle, JSON-schema per request; one optional low-priority CPU utility process; image jobs stop the GPU server first. Values in brackets are starting points that section 10 must confirm.

### Cited Findings
Every flag below exists in the local build 11043 help (`D:/Kataki/.runtime/llama.cpp/llama-server.exe --help`), except where noted: `-c`, `-ngl` (accepts number, `auto` or `all`), `-fa`, `-b/-ub`, `-np`, `--cache-ram`, `--ctx-checkpoints`, `--checkpoint-min-step`, `--cache-idle-slots`, `--sleep-idle-seconds`, `--reasoning`, `--chat-template-kwargs` (documented in the README), `--spec-type`, `--metrics`, `--prio`, `-t`.

### Inferences
Chat server (GPU), design proposal:
```
llama-server.exe -m .runtime/models/Qwen3.5-9B-Q4_K_M.gguf
  --host 127.0.0.1 --port <p>
  -ngl all  -fa on
  -c 16384                       # KV about 0.5 GB f16 on Qwen3.5; Kataki budget stays 8k, eviction target 60%
  -np 1                          # chat slot; use -np 2 only if the idle-time background slot is on the same server
  -b 1024 -ub 512                # measure pp speed vs compute buffer; smaller ub = less VRAM
  --reasoning off                # thinking off for every call by default; the slow path passes chat_template_kwargs to override per request
  --cache-ram 4096               # host-RAM prompt cache (default 8192); each hybrid checkpoint about 50 MB est.
  --ctx-checkpoints 16 --checkpoint-min-step 256   # default step 8192 would give about one checkpoint per 8k chat; VERIFY (issue 24055)
  --sleep-idle-seconds 600       # frees VRAM when idle; the app also stops the process before image jobs
  --metrics -t 4                 # few CPU threads needed when fully offloaded
  (no --context-shift, no --cache-reuse, no -ctk/-ctv: hybrid model, tiny KV)
```
Per request (chat): `cache_prompt: true`, `id_slot: 0`, `response_format` json_schema (fields in the section 5 order, `additionalProperties:false`), `temperature 0.7-0.8, top_p 0.8, top_k 20, presence_penalty 1.0-1.5` (Qwen non-thinking recommendation is T 0.7, top_p 0.8, top_k 20; start there and tune for RP), `timings_per_token: false` (true in benchmarks), max_tokens about 500. Read `timings.cache_n`, `prompt_n`, `predicted_per_second` on every response and log them (free cache-hit telemetry).

Optional background slot on the same server: add `-np 2`, pin jobs to `id_slot: 1`, run only after 2 s of chat idle, abort on new user input (client disconnects the request). Note MTP and `-np > 1` are incompatible.

Utility server (CPU, optional, only if the user wants side jobs while chat streams or on <8 GB GPUs):
```
llama-server.exe -m Qwen3.5-2B-Q4_K_M.gguf -ngl 0 -c 4096 -np 1 -t 6 --prio -1 --reasoning off --port <p2>
```
Embeddings: keep potion-32M in-process; if a neural embedder is chosen, `--embedding` on the utility process or in-process ONNX.

Speed options to A/B later, not defaults: (1) `--spec-type ngram-mod` for the JSON-heavy calls (free, no VRAM); (2) MTP: switch to the `unsloth/Qwen3.5-9B-MTP-GGUF` UD-Q4_K_XL (6.14 GB) with `--spec-type draft-mtp --spec-draft-n-max 2` (expect about 1.2-1.5x under sampling; costs about 0.5+ GB and forbids `-np > 1`); (3) larger `-ub` if VRAM allows.

Failure handling: on start, parse the log for "forcing full prompt re-processing" (issue text) and expose it in the inspector as a cache-miss counter; if the measured hit rate on turn 2+ is bad, switch to the frozen-volatile-block layout from section 4; if the model does not fit (image chain, other GPU users), fall back to Qwen3.5-4B Q4_K_M or `--fit on --fit-target <MiB>`.

### Gaps
- Not run: I did not start llama-server (project rule: never start the user's llama-server; GPU is shared), so no flag combination here has been executed on this machine.
- Exact best `-b/-ub`, checkpoint spacing and threads are unknown until measured; `--reasoning off` interaction with Qwen3.5's template unverified (README shows `chat_template_kwargs` `enable_thinking:false` as the documented route, Unsloth guide uses it).

---

## 10. Measurements Kataki should run itself (c)

### Takeaway
Ten quick measurements, in this order, settle the design; the first two decide whether the hybrid-model cache strategy works at all.

### Cited Findings
Measurement hooks already exist: llama-server responses carry `timings` (prompt_per_second, predicted_per_second, cache counts), `/slots` reports per-slot state, `/props` reports `is_sleeping`, `llama-bench.exe`, `llama-batched-bench.exe` and `llama-fit-params.exe` are in `.runtime/llama.cpp`. — [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md); local directory listing

### Inferences
Follow the user's GPU run protocol (state expected time first, check at 30 s, kill on spill, note that the image chain and LLM must not both be resident):
1. **Cache hit on turn 2+ (Qwen3.5-9B and Gemma 4 12B/E4B):** send a 6k prompt, then the same prefix plus 400 new tokens, with default `--checkpoint-min-step` and with 256; record `cache_n` vs `prompt_n` and the "forcing full prompt re-processing" log line. Then repeat with the volatile block at the tail vs at depth 4 vs frozen in history. Decides layout and flags.
2. **Divergence recovery:** drop the last assistant turn and regenerate (swipe/regenerate) and edit-message cases; the same log/timings check. These are the common RP actions.
3. **Decode and prefill speed on the dev RTX 5060 Laptop (8151 MiB) and any second machine:** `llama-bench` pp512/tg128 for Qwen3.5-9B Q4_K_M, Qwen3.5-4B, Gemma 4 E4B Q4_0, Gemma 4 12B Q3_K_M/IQ4_XS/QAT Q4_0 (the last with `-ngl` sweep); record VRAM at 8k and 16k. Fills the missing scoreboard row.
4. **VRAM budget:** peak `nvidia-smi` and llama-server startup buffer sizes for each model/context; the checkpoint and state byte sizes printed in the log; confirm the section 6 arithmetic and that Gemma 4 12B does not fit.
5. **Constrained vs unconstrained cost and validity:** the fused schema with `json_schema`, 200 turns, on 9B and 4B: tokens/s with and without the grammar, parse-failure rate, enum-validity rate, and a blind quality check of `reply` under grammar vs free text (tests the "format restrictions hurt" risk). Also key-order variants (thought first vs state first).
6. **Fused vs split A/B:** O1 fused vs O2 two-call vs no-thought, blind-rated on 30 scripted scenes (note 10's A/B), with latency to first visible token and total time.
7. **Speculative options:** `ngram-mod` on the JSON state calls, and MTP (Qwen3.5-9B-MTP GGUF) under RP sampling temperatures (not greedy); acceptance rate and net tok/s, and the VRAM cost.
8. **Sleep/swap timing:** wake-from-`--sleep-idle-seconds` time, kill-and-restart time, first-turn cold prefill afterwards, and the full image-swap sequence (stop LLM, image job at 7.03 GB peak, restart) with total user-visible delay.
9. **CPU utility path:** Qwen3.5-0.8B/2B/4B and LFM2.5-1.2B on the CPU: prompt and output tok/s at 1k/3k prompts, extraction-schema validity and quality against the 9B's output as reference; GoEmotions INT8 ONNX, potion-32M, bge-small and Qwen3-Embedding-0.6B ms/text; effect of background CPU work on chat decode speed (thread contention, `--prio -1`, `-t`).
10. **Model quality for RP:** Qwen3.5-9B vs Gemma 4 12B (or E4B) vs one RP finetune (e.g. ArliAI Qwen3.5-9B-RpRMax-v1) on the same scripted scenes, scoring persona consistency, stance/leak rate, JSON validity and slop; plus a KV `q8_0` check only for dense models if any are offered.

### Gaps
- No independent public benchmark exists for character-mind workloads at these sizes; every quality question ends in Kataki's own eval harness (`engine/evals`), as notes 10 and 14 already conclude.
