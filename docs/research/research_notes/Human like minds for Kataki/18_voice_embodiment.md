# Voice, Expression and Embodiment for Kataki characters (research as of 2026-09-29)

Scope: emotional TTS, voice calls, STT, facial expression/sprites/avatars, mood-aware images, human vocal cues, and GPU sharing on an 8 GB card. Source quality note: most "2026 comparison" pages are SEO aggregators. I anchored on model cards (Hugging Face/GitHub), vendor pages, arXiv, and the Artificial Analysis-derived Elo numbers, and flag where only aggregators exist. The web-search budget ran out mid-session, so a few items are marked as gaps or as background knowledge (unverified this session).

## 1. Local TTS options in 2026: quality, latency, VRAM/CPU, licence, emotion and non-verbals

### Takeaway
For Kataki's constraints (8 GB shared GPU, commercial-friendly), the practical shortlist is Kokoro-82M (CPU-runnable, Apache 2.0, no non-verbals, no cloning), Chatterbox Turbo (350M, MIT, native [laugh]/[sigh]-style tags, cloning), and Orpheus 3B (Apache 2.0, emotive tags, about 4 GB at Q8). The highest-Elo open models (Fish S2 Pro, Step Audio EditX, Voxtral, Breeze TTS 2) are either too big for 8 GB or non-commercial, and every top-10 arena model is still closed cloud.

### Cited Findings
- Arena position: on the Artificial Analysis speech arena (May 2026 snapshot; live board updated 2026-07-28), the best open-weight rows are Fish Audio S2 Pro 1128.7 Elo (rank 11), Step Audio EditX 1104.9 (16), NVIDIA Magpie-Multilingual 357M 1064.2 (26), Kokoro 82M v1.0 1056.2 (32), Voxtral TTS 1055.9 (33), Maya1 1050.6 (35). The source warns Elo does not measure latency, licensing, cost or reliability. — [OfflineTTS leaderboard summary](https://www.offlinetts.com/blog/tts-arena-leaderboard-2026/)
- Another summary says "every single model in the top 10 is closed-source", 16 open-weight models out of 92 on the board. — [OfflineTTS via search summary](https://www.offlinetts.com/blog/tts-arena-leaderboard-2026/)
- Breeze TTS 2 (3B, research/non-commercial licence, released 2026-08-25) is reported as top open-weights at about 1206-1215 Elo. Single aggregator source only, not verified against the Artificial Analysis board. — [OrcaRouter](https://www.orcarouter.ai/blog/breeze-tts-2-tops-open-weights-speech-arena)
- Chatterbox Turbo: 350M-parameter architecture, distilled decoder (10 steps down to 1), MIT licence, built "for low-latency voice agents", 23+ languages, native tags including [cough], [laugh], [chuckle]; every output carries an imperceptible Perth watermark; cloning needs a reference clip (about 10 s by example code). — [ResembleAI/chatterbox-turbo model card](https://huggingface.co/ResembleAI/chatterbox-turbo)
- Chatterbox Turbo tag list per a summary page: [clear throat], [sigh], [shush], [cough], [groan], [sniff], [gasp], [chuckle], [laugh]; also [whisper] mentioned; "up to 6x faster than real time on a GPU". — [Resemble AI](https://www.resemble.ai/learn/models/chatterbox-turbo), [The Rundown](https://www.therundown.ai/tools/chatterbox-turbo)
- Original Chatterbox (0.5B, English) reported at a 63.75% preference rate over ElevenLabs in blind tests (another page headlines 65.3%; both are vendor-adjacent aggregator claims, not independent). — [BentoML](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models); [FindSkill](https://findskill.ai/blog/best-open-source-tts-2026/)
- Orpheus TTS (Canopy Labs): Apache 2.0, Llama-3B backbone, released March 2025; trained tags <laugh>, <chuckle>, <sigh>, <cough>, <sniffle>, <groan>, <yawn>, <gasp>; Q8_0 GGUF about 4 GB, fits in roughly 8 GB VRAM, about 200 ms streaming latency; Orpheus-FastAPI gives an OpenAI-compatible /v1/audio/speech with 8 English voices. — [LocalAIMaster Orpheus guide](https://localaimaster.com/blog/orpheus-tts-setup-guide), [lex-au GGUF card](https://huggingface.co/lex-au/Orpheus-3b-FT-Q8_0.gguf), [canopyai/Orpheus-TTS](https://github.com/canopyai/Orpheus-TTS)
- Orpheus also ships 1B, 400M, 150M variants; trained on over 100k hours of English; zero-shot cloning and guided emotion claimed. — [BentoML](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models)
- Sesame CSM-1B: Apache 2.0, listed as 2B parameters, English-focused ("some capacity for non-English... likely won't do well"), "sounds best when provided with context" (prior audio+text turns), a base model not tied to a specific voice, explicit prohibition on impersonation. VRAM/latency not stated on the card. — [sesame/csm-1b](https://huggingface.co/sesame/csm-1b)
- Kyutai TTS 1.6B (actually 1.8B params): CC-BY-4.0 weights, English and French, 12.5 Hz frame rate, streaming from partial text, "75x generated audio per compute unit of time" (a batched-server throughput figure, not single-user latency), no direct cloning (only pre-computed voice embeddings from a separate repo), no watermark by design. Latency reported about 200-220 ms. — [kyutai/tts-1.6b-en_fr](https://huggingface.co/kyutai/tts-1.6b-en_fr), [Kyutai TTS](https://kyutai.org/tts/)
- Voxtral TTS (Mistral, March 2026): 4B, 9 languages, open weights under CC BY-NC 4.0, needs a 16 GB+ GPU (BF16), reported about 70 ms latency. — [Mistral](https://mistral.ai/news/voxtral-tts/), [HF card](https://huggingface.co/mistralai/Voxtral-4B-TTS-2603), [InsiderLLM](https://insiderllm.com/guides/mistral-voxtral-tts-local-voice-ai/)
- Fish Audio S2 Pro: 5B, Fish Audio Research License (commercial use needs a paid licence), open-domain emotion tags, 80+ languages, Elo about 1123. — [MarkTechPost benchmark roundup](https://www.marktechpost.com/2026/05/30/best-text-to-speech-tts-models-in-2026-a-benchmark-based-comparison/)
- Kokoro-82M: Apache 2.0, MOS 4.5 in one third-party test, CPU-capable, only experimental emotion markup, about 54 preset voices, no cloning, Elo about 1056-1060. — [MarkTechPost](https://www.marktechpost.com/2026/05/30/best-text-to-speech-tts-models-in-2026-a-benchmark-based-comparison/), [BentoML](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models)
- Kokoro CPU speed varies a lot. On 2 ARM Neoverse-N1 cores it runs at ×0.87-0.93 (slower than real time; RTF here means audio seconds per compute second), with a fixed cost of about 0.51 s per call. Piper on the same box ran at ×8.1-8.5. Quality was not measured in that benchmark. — [obole-ia/tts-cpu-benchmark](https://github.com/obole-ia/tts-cpu-benchmark)
- Kokoro on an Apple M3 Pro CPU rendered 22 s of audio in about 3.5 s (about 6x real time) via kokoro-onnx. Note: a search summary mis-stated the ARM number as "faster than real time"; the repo data shows the opposite. — [search summary of Kokoro benchmarks](https://heyneo.com/blog/kokoro-tts-vs-supertonic-3-tts), [obole-ia repo](https://github.com/obole-ia/tts-cpu-benchmark)
- Other open models (secondary sources): Zonos v0.1 Apache 2.0 about 6 GB VRAM; Higgs Audio V2 Apache 2.0 (Llama 3.2 3B base, 10M+ hours); XTTS-v2 under the Coqui Public Model License (non-commercial), 4-6 GB VRAM; F5-TTS CC-BY-NC-4.0; Dia 1.6B for scripted dialogue with non-verbal cues; VibeVoice 1.5B (EN/ZH, up to about 90 min, described as permissive). — [CodeSOTA](https://www.codesota.com/text-to-speech), [Pinggy](https://pinggy.io/blog/best_open_source_self_hosted_text_to_speech_models/), [MarkTechPost](https://www.marktechpost.com/2026/05/30/best-text-to-speech-tts-models-in-2026-a-benchmark-based-comparison/)
- Other 2026 open entrants named in the roundup: IndexTTS-2 (separates timbre from emotion), CosyVoice 2 (0.5B), Qwen3-TTS (1.7B, custom voices), Maya1. Their licences and VRAM are not stated in the source. — [MarkTechPost](https://www.marktechpost.com/2026/05/30/best-text-to-speech-tts-models-in-2026-a-benchmark-based-comparison/)

### Inferences
- Non-verbal support splits into three kinds: trained tag vocabularies (Chatterbox Turbo, Orpheus, Dia), free-form style/emotion control (Fish, ElevenLabs v3, Gemini), and context-conditioned prosody (CSM). For a roleplay app the tag route is the most controllable, because the LLM can emit tags.
- Kokoro is the only option with a plausible "always works, zero GPU" story, but on weak CPUs it is not comfortably real-time without sentence-level streaming, and it cannot laugh or sigh. Piper (about 8x real time on 2 ARM cores) is the safety net for very weak hardware but its quality was unmeasured here and its licence changed over time (background knowledge, verify before shipping).
- Chatterbox Turbo (MIT, 350M) is the best fit for the "local premium" tier. I found no measured VRAM figure for it (see Gaps); given 350M parameters plus a vocoder, it likely fits well under 4 GB, but that must be measured.
- Kyutai TTS is architecturally the best for streaming LLM text in, but English/French only, 1.8B, and no user voice cloning, so it is a poor match for arbitrary custom characters.
- Anything CC-BY-NC, CPML or research-licence (Voxtral, XTTS-v2, F5-TTS, Fish S2 Pro, Breeze 2) cannot be bundled in a commercial app. They can be used only as user-supplied optional backends, and even that needs a legal read.

### Gaps
- No measured VRAM/latency figures for Chatterbox Turbo, Zonos, Higgs Audio, Dia, CSM-1B on an 8 GB card were found; run a local benchmark.
- Confirmed licences for Dia, VibeVoice, Qwen3-TTS, IndexTTS-2 were not found in primary sources this session.
- No independent MOS/arena numbers for Chatterbox Turbo or Orpheus; the Chatterbox "beats ElevenLabs" claim traces to vendor-adjacent blind tests.
- Search budget was exhausted before checking Piper's current licence and the Sesame CSM 8 GB feasibility.

## 2. Local STT: whisper.cpp, faster-whisper, Parakeet, Moonshine and CPU latency

### Takeaway
For a voice-call feature, use a streaming-friendly CPU STT: Parakeet TDT v3 or Moonshine are far faster on CPU than Whisper Large; Whisper large-v3-turbo (via whisper.cpp or faster-whisper) is the multilingual fallback.

### Cited Findings
- On the same MacBook Pro, Moonshine reported 107 ms latency versus 11,286 ms for Whisper Large V3. — [ModelsLab Moonshine vs Whisper](https://modelslab.com/blog/audio-generation/moonshine-vs-whisper-asr-real-time-speech-2026)
- Parakeet TDT v3 has a real-time factor under 0.1x on CPU (as measured by aggregator write-ups) because its transducer decoder is cheap; Whisper Large V3 Turbo cuts decoder layers from 32 to 4 (about 6x faster than Large V3) but is still slower than Parakeet or Moonshine on CPU. — [Northflank STT roundup](https://northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2026-benchmarks), [SnailText Whisper vs Parakeet](https://snailtext.app/blog/whisper-vs-parakeet-tdt/)
- A 2026 arXiv paper describes a compact high-accuracy English streaming ASR for on-device low-latency use. — [arXiv 2604.14493](https://arxiv.org/html/2604.14493v2)
- Kyutai also ships a streaming STT alongside its TTS, used by Unmute. — [kyutai-labs/delayed-streams-modeling](https://github.com/kyutai-labs/delayed-streams-modeling/)

### Inferences
- Push-to-talk and simple VAD endpointing can use Parakeet (English/European) or Moonshine (English, lowest latency, tiny). Whisper stays the default for languages those do not cover.
- Because STT is CPU-cheap, it should never compete with the LLM/TTS for VRAM. Background knowledge (unverified this session): Whisper models are MIT, Parakeet TDT v3 is CC-BY-4.0, Moonshine has permissive/MIT-family licences; check each before bundling.

### Gaps
- No apples-to-apples CPU latency table (same CPU class as an average user laptop) was found; the numbers above come from different machines and aggregators.
- Word-error-rate on noisy/accented microphone input and on roleplay vocabulary (invented names) was not researched.

## 3. Full-duplex / speech-to-speech models versus cascaded pipelines; turn-taking, backchannels, latency budgets

### Takeaway
True full-duplex (Moshi/PersonaPlex) gives the most human turn-taking and backchannels but replaces the LLM, is English-only, loses context after about 4 minutes, and is only barely viable on 8 GB. A cascaded pipeline (STT, your LLM, streaming TTS) is the right default because Kataki's characters, memory and model choice live in the LLM.

### Cited Findings
- PersonaPlex (NVIDIA, January 2026): 7B full-duplex speech-to-speech, based on Moshi architecture/weights; code MIT, weights under the NVIDIA Open Model License; text role prompts plus audio voice conditioning; 8 natural + 10 varied prebuilt voice embeddings; supports interruptions, backchannels and pauses (evaluated with FullDuplexBench); English documented. — [NVIDIA/personaplex](https://github.com/NVIDIA/personaplex)
- Official BF16 path needs about 19 GB (RTX 3090). Community 8-bit/4-bit builds and moshi.cpp claim 8-16 GB support, including "great performance" on an 8 GB RTX 2070 laptop; results depend on quantization and CPU spill. Context is a rolling 3,000 frames (about 4 min) after which it forgets and degrades into repetition. — [MakeUseOf](https://www.makeuseof.com/nvidia-personaplex-local-speech-model-8gb-vram/)
- Unmute (Kyutai) is the reference open cascaded stack: STT, any text LLM, TTS, in a Rust server. — [kyutai-labs/unmute](https://github.com/kyutai-labs/unmute)
- Hugging Face publishes a modular open-source cascaded voice-agent repo. — [huggingface/speech-to-speech](https://github.com/huggingface/speech-to-speech)
- Recent full-duplex research: "Full-Duplex Speech Models Take the Floor When Asked, Not When Needed" (arXiv 2609.19596), streaming user transcription in full-duplex S2S models (arXiv 2609.15759), DuplexDrama expressive/full-duplex dialogue dataset (arXiv 2609.12872), JoyAI-Talker empathetic full-duplex agent (arXiv 2608.01119). Only titles/abstract listings were read, not full papers. — [arXiv 2609.19596](https://arxiv.org/pdf/2609.19596), [arXiv 2609.15759](https://arxiv.org/pdf/2609.15759), [arXiv 2609.12872](https://arxiv.org/pdf/2609.12872), [arXiv 2608.01119](https://arxiv.org/pdf/2608.01119)
- Cloud realtime speech models: OpenAI gpt-realtime bills audio tokens (1 token per 100 ms user, 1 per 50 ms assistant); a typical agent costs about $0.06-0.11/min on the flagship and $0.02-0.05/min on mini with prompt caching, up to $0.18-0.46/min without caching; audio rates $32/$64 per 1M in/out (flagship) versus $10/$20 (mini), July 2026. — [Layer3Labs](https://www.layer3labs.io/guides/openai-realtime-api-pricing), [HackerNoon measured sessions](https://hackernoon.com/openai-realtime-api-pricing-in-2026-real-world-data-from-4000-measured-sessions)

### Inferences
- Latency budget for a cascaded call (engineering estimate, not measured in Kataki): end-of-speech detection 200-400 ms, STT 100-300 ms (CPU Parakeet/Moonshine), LLM first sentence 400-1000 ms on an 8 GB local model, TTS first chunk 100-300 ms, so roughly 1-2 s. Hiding it needs filler/backchannel audio ("mm", "hm") played immediately and sentence-level TTS streaming.
- Backchannels in a cascade can be faked: pre-rendered "mm-hm/oh/right" clips in the character's voice, triggered by VAD pauses in the user's speech, are cheap and cover most of the perceived responsiveness. This is an engineering suggestion, not something validated by a source here.
- PersonaPlex is a "lab" mode candidate, not a default: it would sit outside the character memory/LLM pipeline and hog the whole GPU. Sesame's CSM-1B (context-conditioned generation) is better used as a TTS component than as a speech-to-speech engine.

### Gaps
- Sesame's and Hume EVI 3's internal turn-taking design and measured latencies were not found in primary sources.
- No measured end-to-end latency of an Unmute-like cascade on 8 GB hardware with a local llama.cpp model.
- Barge-in/interrupt handling best practice (cancel TTS, truncate the assistant turn in context) was not sourced.

## 4. Cloud voice options and cost per minute

### Takeaway
Plain streaming TTS costs about $0.01-0.05 per spoken minute; full managed voice-agent platforms are $0.04-0.10 per minute plus LLM fees. Emotional/tag control is best at ElevenLabs v3, Gemini 3.1 Flash TTS and Cartesia; Hume is the emotion-specialist.

### Cited Findings
- ElevenAgents: $0.08 per minute for all plans (burst $0.16/min over concurrency), TTS included, LLM fees billed on top; included minutes range from 15 (Free) to 12,375 (Business). — [ElevenLabs agents pricing](https://elevenlabs.io/pricing/agents)
- ElevenLabs v3 supports inline tags such as [whispers], [laughs], [sighs] and scene cues, but is "not optimized for real-time". — [MarkTechPost roundup](https://www.marktechpost.com/2026/05/30/best-text-to-speech-tts-models-in-2026-a-benchmark-based-comparison/)
- Cartesia Sonic 3.5: Elo about 1204, about 82 ms TTFA, laughter support; Sonic-3.6 (August 2026) is reported as leading both Artificial Analysis speech arenas. TTS about $0.03/min pay-as-you-go (about 900 credits per spoken minute); Line voice agents flat $0.06/min. — [MarkTechPost roundup](https://www.marktechpost.com/2026/05/30/best-text-to-speech-tts-models-in-2026-a-benchmark-based-comparison/), [MarkTechPost Sonic-3.6](https://www.marktechpost.com/2026/08/18/cartesia-ships-sonic-3-6-a-streaming-tts-model-that-now-leads-both-artificial-analysis-speech-arenas/), [CloudTalk Cartesia pricing](https://www.cloudtalk.io/blog/cartesia-pricing/)
- Google Gemini 3.1 Flash TTS: Elo 1216, 200+ audio tags for style/pacing/accent, 30 prebuilt voices only, no streaming, 32k-token session limit. — [MarkTechPost roundup](https://www.marktechpost.com/2026/05/30/best-text-to-speech-tts-models-in-2026-a-benchmark-based-comparison/)
- OpenAI gpt-4o-mini-tts: steerable via instructions, custom voices from a sample, about $0.015/min ($0.60/1M text tokens, $12/1M audio tokens). — [MarkTechPost roundup](https://www.marktechpost.com/2026/05/30/best-text-to-speech-tts-models-in-2026-a-benchmark-based-comparison/)
- Inworld TTS-1.5 / Realtime TTS-2: Elo 1200-1208, P90 first-audio under 130 ms (Mini) / under 250 ms (Max), $25-35 per 1M characters on demand. Hume Octave 2: $10-100+/1M characters, "reads for meaning", cloning via sales. — [MarkTechPost roundup](https://www.marktechpost.com/2026/05/30/best-text-to-speech-tts-models-in-2026-a-benchmark-based-comparison/)
- Hume EVI (speech-to-speech empathic voice): about $0.072/min pay-as-you-go; EVI 3 overage $0.06 (Pro), $0.05 (Scale), $0.04 (Business) per minute. — [eesel Hume pricing](https://www.eesel.ai/blog/hume-ai-pricing), [AutoGPT Hume pricing](https://autogpt.net/hume-ai-pricing-every-plan-explained/)
- Hugging Face Inference Providers is a router to providers including fal, Replicate and Together; TTS models exist on the Hub, and the `huggingface_hub` inference client exposes a text-to-speech task. Which specific high-quality TTS models are actually served (and billed) through the router is not confirmed here. — [HF Inference Providers docs](https://huggingface.co/docs/inference-providers/index), [InferenceClient reference](https://huggingface.co/docs/huggingface_hub/en/package_reference/inference_client)
- Character-per-minute conversion: about 150 wpm is about 900 characters per spoken minute, so $15/1M chars (Fish-hosted) is about $0.014/min and $35/1M chars is about $0.03/min. — [CloudTalk Cartesia pricing](https://www.cloudtalk.io/blog/cartesia-pricing/) (900 chars/min figure), arithmetic mine.

### Inferences
- For a "premium cloud voice" mode that runs at roughly 30-60 minutes per user per day, TTS-only at $0.015-0.03/min is about $0.5-1.8/day; agent platforms at $0.08-0.10/min plus LLM would be $2.4-6/day. TTS-only plus Kataki's own LLM and turn logic is markedly cheaper and keeps character control in-app.
- Cloud emotion control that matters for Kataki: ElevenLabs v3 and Gemini 3.1 Flash TTS accept LLM-authored tags (best fit for the "LLM writes the cues" design); Hume Octave 2 infers emotion from meaning (less control, less tag plumbing); Cartesia wins on latency.

### Gaps
- Live pricing pages for Cartesia, Hume, OpenAI TTS and Inworld were not opened directly (aggregators only); verify before quoting to users.
- No confirmed list of TTS models served by HF Inference Providers with per-minute costs.
- Sesame's hosted product and Kindroid/Nomi/Replika/Character.AI voice architectures were not researched (proprietary, little public detail).

## 5. Expression: mood to sprite selection, Live2D/VRM avatars, mood-conditioned images

### Takeaway
The cheapest proven pattern is SillyTavern's: a small CPU text-emotion classifier picks one label per message and the UI swaps a pre-made sprite. For Kataki, pre-generate a small expression set per character from the character sheet/LoRA once, cache it, and only consider Live2D/VRM as a later premium avatar.

### Cited Findings
- SillyTavern's Expressions extension: a local classifier (Cohee/distilbert-base-uncased-go-emotions-onnx, about 100 MB, downloaded once) reads the new message and returns the single most likely of 28 labels; the front end shows the matching sprite. — [SillyTavern docs: Expression Images](https://docs.sillytavern.app/extensions/expression-images/), [SillyTavern-Docs source](https://github.com/SillyTavern/SillyTavern-Docs/blob/main/extensions/Expression-Images.md)
- expressions-plus adds rules for 22 combination emotions (anxious, awe, bewildered, contempt, etc.), profiles and live classification insight on top of the 28 base labels. — [Tyranomaster/expressions-plus](https://github.com/Tyranomaster/expressions-plus)
- Community services generate a 28-sprite set from a single image, showing the "one picture to expression set" workflow is already expected by SillyTavern users. — [TavernSprite](https://tavernsprite.com/)
- @pixiv/three-vrm and three.js are MIT; VRoid Studio exports rigged VRM avatars for free; VRM `expressionManager` can drive lip sync in the browser; Live2D Cubism has a free tier for simple models (paid for professional use). — [npm/aggregator overview](https://www.npmjs.com/package/pixi-live2d-display-lipsyncpatch), [Streamer Magazine avatar tools guide](https://alive-project.com/en/streamer-magazine/article/7382/)
- Kataki repo context: local image generation and a character-sheet concept already exist under `docs/images/` (pipeline, rules-and-gotchas, README), with an 8 GB rule and a run protocol; no expression-specific generation was found there beyond that.

### Inferences
- Use 8-12 Kataki expression states (neutral, happy, amused/laughing, sad, angry, anxious/embarrassed, surprised, flirty/soft, tired, thinking) and collapse the 28 go-emotions labels onto them by a fixed table. 28 art assets per character is not affordable.
- Better than a text-classifier alone: have the LLM emit a structured per-line cue (mood, intensity, optional non-verbal tag). Use the CPU classifier only as fallback, and let the same cue drive sprite, TTS tag, and chat-bubble styling.
- Sprite generation belongs at character-creation time as a batch job under the existing GPU run protocol: face inpaint or img2img on the base sheet with an expression prompt and the character LoRA, human-approved once, then cached as static images. No diffusion at chat time.
- Mood-conditioned scene images (scene art reflecting mood) can reuse the same cue as an extra prompt fragment, costing nothing beyond the normal image path.
- Live2D/VRM adds real-time lip sync and idle motion but needs rigged assets, which conflicts with Kataki's "one picture to character" flow. A later option is audio-amplitude-driven mouth-flap on 2D sprites (open/closed mouth variants), which is much cheaper than a rig.

### Gaps
- No published benchmark for identity-consistent expression variants from a single character image/LoRA was found; needs a Kataki spike on the local SDXL-class chain.
- Live2D Cubism runtime licensing for a distributed open app was not verified in a primary source; check before committing.
- No evidence on how well the go-emotions classifier maps to roleplay/erotic/dark-fantasy prose; likely needs an LLM-tag path.

## 6. Making voices carry human cues: hesitation, sighs, laughter, tone matching mood

### Takeaway
Human cues need three layers: the script (spoken-style text with sparse disfluency), the cue plan (mood/intensity/non-verbal tags per line), and the delivery (pauses, timing, backchannel). Research shows disfluency raises perceived spontaneity at a small intelligibility cost, so use it sparingly and only in voice mode.

### Cited Findings
- Hassan, Lison and Halvorsen fine-tune an LLM with LoRA to insert disfluencies, then synthesize with a disfluency-capable TTS; a user study found perceived spontaneity rose significantly with a slight loss of intelligibility. (Dec 2024, revised Oct 2025.) — [arXiv 2412.12710](https://arxiv.org/abs/2412.12710)
- In that work Bark emerged as the most capable of the tested TTS models at handling disfluencies (per a summary of the paper; the abstract page does not name the models). — [alphaXiv summary](https://www.alphaxiv.org/abs/2412.12710)
- Related work covers filler words and backchannels as distinct behaviours in dialogue: NAACL 2025 "Behaviorally Aware Spoken Dialogue Generation" and "Talking to...uh...um...Machines" (perceived partner model effects of disfluent agents). Only titles/abstracts were read. — [ACL Anthology](https://aclanthology.org/2025.naacl-long.484.pdf), [arXiv 2507.18315](https://arxiv.org/pdf/2507.18315)
- Tag vocabularies for non-verbals exist natively in Chatterbox Turbo, Orpheus, ElevenLabs v3 and Gemini 3.1 Flash TTS (see section 1 and 4). Kokoro's emotion markup is only experimental. — [Chatterbox Turbo card](https://huggingface.co/ResembleAI/chatterbox-turbo), [LocalAIMaster Orpheus](https://localaimaster.com/blog/orpheus-tts-setup-guide), [MarkTechPost](https://www.marktechpost.com/2026/05/30/best-text-to-speech-tts-models-in-2026-a-benchmark-based-comparison/)
- CSM-1B improves with prior conversation audio as context, a route to tone continuity across turns. — [sesame/csm-1b](https://huggingface.co/sesame/csm-1b)
- Full-duplex models expose backchannels and interruptions natively (PersonaPlex), which cascades must simulate. — [NVIDIA/personaplex](https://github.com/NVIDIA/personaplex)

### Inferences
- Add a "voice render" pass: a second short LLM call (or a prompt section) rewrites the display text into speakable text with a cue list, for example: `{text:"Ha... okay, fine.", mood:"amused", intensity:0.6, tags:["chuckle"], pause_before_ms:400}`. Keep the display transcript clean (tags stripped) so the user never reads `[laugh]` and the TTS never speaks bracket text.
- Engine adapter table: one canonical cue vocabulary mapped to engine syntax (`[laugh]` for Chatterbox/ElevenLabs, `<laugh>` for Orpheus, plain text or punctuation like "Ha..." for Kokoro, and a `stability/style` knob on cloud engines). Unsupported cues degrade to punctuation ("..." for hesitation, em-dash for cut-offs).
- Frequency guardrails: at most one non-verbal and one filler per 2-3 sentences, scaled by character trait (shy = more hesitation; confident = fewer), and none on the first word of a line. This follows the spontaneity/intelligibility trade-off above.
- Tone-matches-mood: mood state from the existing emotion model drives (a) which tags the LLM may use, (b) TTS speed/pitch/energy or engine-specific style prompt, (c) pre-render pause length. Same mood state also selects the sprite so face and voice agree.
- Realism through timing, not only audio: variable response latency (longer when the character is upset or thinking), a short "breath/hm" lead-in before long replies, and pre-rendered backchannel clips while the user talks.
- Consent/safety: voice cloning should accept only user-provided or synthetic reference voices; Sesame's card bans impersonation, Kyutai restricts cloning, and Chatterbox watermarks outputs, so keep the watermark on and avoid a "clone any celebrity" UX.

### Gaps
- No controlled study of laughter/sigh insertion in roleplay or companion contexts (only general dialogue naturalness) was found.
- Optimal disfluency rates per persona type are unquantified; must be tuned by listening tests.
- No source evaluated whether users find synthetic non-verbals uncanny versus charming over long sessions.

## 7. Sharing an 8 GB GPU between LLM, TTS and image generation

### Takeaway
Keep the LLM resident, run STT and the default TTS on CPU, and treat image generation as an exclusive job that pauses voice. GPU TTS (Chatterbox Turbo, Orpheus Q4) is a mode that requires either a cloud LLM (GPU free) or a smaller LLM/context. Model swapping is the enemy of voice latency.

### Cited Findings
- Orpheus 3B Q8_0 is about 4 GB and reportedly fits in roughly 8 GB total; Q4 variants exist. — [lex-au GGUF card](https://huggingface.co/lex-au/Orpheus-3b-FT-Q8_0.gguf), [isaiahbjork Q4_K_M GGUF](https://huggingface.co/isaiahbjork/orpheus-3b-0.1-ft-Q4_K_M-GGUF)
- Zonos v0.1 about 6 GB; XTTS-v2 about 4-6 GB; Voxtral 4B needs 16 GB+. — [Pinggy](https://pinggy.io/blog/best_open_source_self_hosted_text_to_speech_models/), [Voxtral HF card](https://huggingface.co/mistralai/Voxtral-4B-TTS-2603)
- PersonaPlex supports `--cpu-offload` (via accelerate) and pure-CPU runs but spills performance to CPU; community 4-bit builds claim 8-16 GB. — [NVIDIA/personaplex](https://github.com/NVIDIA/personaplex), [MakeUseOf](https://www.makeuseof.com/nvidia-personaplex-local-speech-model-8gb-vram/)
- Kokoro and Piper are CPU-capable; Kokoro has about 0.5 s fixed per-call overhead on a weak CPU, so sentence chunking must not be too fine. — [obole-ia/tts-cpu-benchmark](https://github.com/obole-ia/tts-cpu-benchmark)
- Project rule: the repo's image docs impose the 8 GB limit and a run protocol (state expected time, check step rate at about 30 s, kill a spilling run at once). — `D:/Kataki/CLAUDE.md`, `D:/Kataki/docs/images/rules-and-gotchas.md`

### Inferences
- Residency plan (estimates, must be benchmarked): LLM (llama.cpp, about 5-6 GB for a 7-8B Q4 with modest context) resident; STT and Kokoro/Piper on CPU (0 GB VRAM); Chatterbox Turbo optional on GPU only if the LLM is small enough or cloud-hosted; image gen exclusive.
- Scheduler rules: (1) a single GPU job queue with priorities: voice-turn > text generation > expression batch > scene image; (2) when a call is active, image jobs are refused or deferred and the UI says so; (3) when an image job starts, the call ends or falls back to text; (4) never load TTS and diffusion together; (5) keep the CPU TTS as the always-available fallback if VRAM is contested.
- Swap cost: loading a 2-4 GB model from NVMe is seconds, which is fine between activities but unacceptable per turn, so do not swap TTS in and out of VRAM during a conversation. (Estimate; no measurement found.)
- With the cloud path (HF Inference Providers LLM), the GPU is free and local GPU TTS becomes the natural "quality local voice" choice.

### Gaps
- No measured co-residency figures for llama.cpp plus Chatterbox/Orpheus plus SDXL on an 8 GB card; needs a spike.
- No source on Windows/CUDA model-unload behaviour (VRAM fragmentation after swapping) in llama.cpp, ComfyUI-style stacks.

## 8. Recommended voice and expression stack for Kataki (cheap/local default plus premium cloud)

### Takeaway
Ship a cascaded design with a canonical per-line "cue" object produced by the LLM, engine adapters for TTS, sprite selection from the same cue, and tiered engines: CPU Kokoro/Piper by default, Chatterbox Turbo (or Orpheus Q4) as local premium, and a cloud tag-capable TTS (ElevenLabs v3, Cartesia, or Gemini) as premium cloud. Full-duplex PersonaPlex stays an experiment.

### Cited Findings
- Facts underpinning the stack are cited in sections 1-7 above: Kokoro Apache 2.0 CPU-capable; Chatterbox Turbo MIT with tags and cloning; Orpheus Apache 2.0 with tags at about 4 GB Q8; Parakeet/Moonshine CPU STT; Unmute/HF speech-to-speech as open cascaded references; ElevenAgents $0.08/min plus LLM, Cartesia about $0.03/min TTS, gpt-4o-mini-tts about $0.015/min; SillyTavern-style classifier plus sprites; PersonaPlex 8 GB caveats and 4-minute context. — [Chatterbox Turbo card](https://huggingface.co/ResembleAI/chatterbox-turbo), [kyutai-labs/unmute](https://github.com/kyutai-labs/unmute), [ElevenLabs agents pricing](https://elevenlabs.io/pricing/agents), [SillyTavern docs](https://docs.sillytavern.app/extensions/expression-images/), [NVIDIA/personaplex](https://github.com/NVIDIA/personaplex)

### Inferences
Design, in build order (thin see-it-first slices):

1. Cue contract (no audio yet). The LLM output (or a follow-up small call) adds a per-line cue: `mood`, `intensity`, `tags[]`, `pause_ms`. Strip tags for display. Drive chat-bubble styling and a sprite swap from `mood` immediately. This is the entire expression feature at zero GPU cost, and it feeds every later step.
2. Expression set. At character creation, batch-generate 8-12 expression images from the character sheet/LoRA under the GPU run protocol, cache them, and allow user approval. Fallback classifier (go-emotions DistilBERT ONNX on CPU) only when the LLM gave no mood.
3. Default voice (local, CPU): Kokoro-82M (Apache 2.0) with sentence streaming; Piper as an ultra-low-spec fallback. No real non-verbals, so simulate with text ("Ha.", "Hmm...", ellipses) and pre-rendered generic laugh/sigh/breath samples that are mixed in as short clips.
4. STT (CPU): Parakeet TDT v3 or Moonshine for English, Whisper large-v3-turbo via whisper.cpp for other languages; push-to-talk first, then VAD auto-endpointing.
5. Voice call (cascaded): VAD, STT, LLM (streaming), sentence chunker, TTS, playback queue, with barge-in (stop playback, truncate the assistant turn in context to what was actually spoken). Add pre-rendered backchannel and lead-in clips per character voice. Target under 1.5-2 s from end of user speech to first audio (estimate).
6. Local premium voice (GPU or cloud-LLM users): Chatterbox Turbo (MIT, tags, cloning, watermark kept on), Orpheus 3B Q4/Q8 as an alternative with fixed voices/fine-tuning; runs behind the same TTS interface (OpenAI-compatible `/v1/audio/speech` shape, as Orpheus-FastAPI already offers). Scheduler rules from section 7 apply.
7. Premium cloud voice: pluggable TTS-only adapters (ElevenLabs v3, Cartesia Sonic 3.x, Gemini 3.1 Flash TTS; Hume Octave 2 for emotion-from-meaning), user brings their own key or Kataki proxies; TTS-only (about $0.015-0.03/min) rather than agent platforms ($0.08+/min plus LLM). Cost meter shown in UI.
8. Optional later: avatar layer (amplitude mouth-flap on sprites first; VRM via three-vrm MIT; Live2D only after a licence check); PersonaPlex/moshi.cpp as an opt-in experimental "phone mode" for English with the caveat of no Kataki memory/LLM in the loop and about 4 minutes of context.

Decisions to avoid: bundling CC-BY-NC/CPML/research-licensed models (Voxtral, XTTS-v2, F5-TTS, Fish S2 Pro, Breeze TTS 2); loading TTS and diffusion at the same time on 8 GB; putting non-verbal tags in the visible transcript; aiming for full-duplex as the default.

### Gaps
- All latency and VRAM numbers for the combined stack are estimates; a benchmark spike on the target 8 GB machine (LLM plus Kokoro CPU plus Chatterbox Turbo GPU) should precede commitment.
- Consent/legal treatment of user voice cloning (and of watermark policy for exported audio) needs a separate policy note.
- Turn-taking quality in cascades (false endpointing, echo/self-hearing without headphones) was not researched; acoustic echo cancellation will matter in Electron/web (browser AEC is available via getUserMedia constraints, background knowledge, unverified here).
