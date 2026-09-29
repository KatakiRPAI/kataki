# One generated image to a character LoRA on an 8 GB laptop GPU (SDXL / Illustrious / Pony), 2025–2026

Scope: WAI-Illustrious-SDXL v17 (anime) and Pony Realism v2.2 (photoreal). Hardware: RTX 5060 Laptop 8 GB (Blackwell sm_120), 32 GB RAM, Windows, local only.
Source caveats: Civitai articles are behind a login wall and could not be read. Reddit could not be fetched. Most practitioner numbers below therefore come from GitHub issues/READMEs, Hugging Face cards and a few independent blogs. Anything dated before 2025 is flagged "(older)".

## Q1. How do people build a training dataset from one image in 2025–2026?

### Takeaway
The dominant 2025–2026 pattern is "one image → edit model (Qwen-Image-Edit 2509/2511, optionally with a multi-angle LoRA) loops over a fixed prompt list → 20–60 varied images → auto-caption + trigger word → SDXL LoRA". Practitioners stress variety (angle, expression, lighting, outfit, background) over volume. The edit models are 20B-parameter and do not fit in 8 GB VRAM, so on this laptop they run slowly with offload or quantization.

### Cited Findings
- **Qwen-Image-Edit-2509 dataset workflow (Oct 10, 2025):** it comes with 50 prompt variations (gender-neutral and female sets) covering angles, clothes, expressions and backgrounds. The author says the output keeps a "consistent face" and can be used "to train a Wan/Flux/Qwen LoRA or SDXL LoRA". Model sizes: FP8 20.4 GB, BF16 40.9 GB. The author recommends an RTX 5090 (32 GB) or RunPod at about $1/h. No per-image time is given, and no LoRA was actually trained or shown. — [Weird Wonderful AI Art](https://weirdwonderfulai.art/comfyui/qwen-image-edit-can-create-character-consistent-lora-dataset/)
- **Qwen-Image-Edit-2509 workflow:** the model edits from the reference instead of generating from scratch, "so faces don't drift between shots". It loops through built-in portrait prompts: left/right profiles, three-quarter views, high/low angles, Dutch tilts, Rembrandt lighting. The page recommends 20–50 varied images for a character LoRA, with "variety mattering more than volume". — [Floyo: Create Character LoRA Dataset using Qwen Image Edit 2509](https://www.floyo.ai/workflows/create-character-lora-dataset-using--ac2829kggykc)
- **Qwen-Image-Edit-2511 workflow:** produces 60 images from a single input covering poses, lighting, expressions and environments. It works best from a character sheet with front and back views, but a single front-facing image "will also work well". — [Floyo: Qwen 2511 Edit – Single Image to Character Dataset](https://www.floyo.ai/workflows/qwen-2511-edit-single-image-to-chara-65qytngb2sux)
- **Qwen-Image-Edit-2511 model card:** claims "notably better consistency" and "improved character consistency" compared with 2509, while "preserving the identity and visual characteristics of the subject". It accepts multiple input images and has "selected popular LoRAs" merged into the base, including lighting control and new-viewpoint generation. — [HF: Qwen/Qwen-Image-Edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)
- **Multi-angle LoRA for Qwen-Edit-2509 (dx8152):** adds camera control (rotate left/right, tilt up/down, wide-angle vs close-up, top-down). Community tools drive it with four sliders: rotate_degrees, move_forward, vertical_tilt, use_wide_angle. It is used to make character turnarounds from one image. — [HF: dx8152/Qwen-Edit-2509-Multiple-angles](https://huggingface.co/dx8152/Qwen-Edit-2509-Multiple-angles); [Floyo workflow](https://www.floyo.ai/workflows/dynamic-camera-control-for-your-imag-2fn800hyn93q)
- **Qwen-Image-Edit-2511 local requirements (Jan 14, 2026):**

  | Precision | Model size | VRAM |
  |---|---|---|
  | BF16 | ~30 GB | 24 GB+ |
  | FP8 | ~15 GB | "6GB+", described as "Slow, but it runs" |
  | NF4 | ~10 GB | 16–20 GB |
  | GGUF Q4_K_M | 13.1 GB | CPU-runnable |

  A Lightning LoRA cuts steps from 40 to 4. The article has no per-GPU seconds-per-image numbers and does not mention 8 GB cards. — [lilting channel](https://lilting.ch/en/articles/qwen-image-edit-2511-local-specs)
- **Dataset hygiene (Pony guide):** vary angle, expression, pose, outfit, background, framing and lighting while keeping identity features visible. Delete blurry images, watermarks, stray text, bad crops and near-duplicates. Check hands, limbs, ears and so on. — [Offline Creator: Pony LoRA Training Guide](https://offlinecreator.com/guide/pony-lora-training-guide)
- **Captioning on Pony:** booru tags plus natural language are both understood. Example caption order: `score_9, source_anime, myponychar, solo, blue hair, green eyes, black jacket, standing, city street, night`. — [Offline Creator](https://offlinecreator.com/guide/pony-lora-training-guide)
- **Captioning on Illustrious/NoobAI (updated 2026-07-27):**
  - Tag with Civitai's on-site tagger or JoyTag, then review every caption by hand.
  - Invent a unique trigger token.
  - Add per-image negative captions such as `3d, cgi, render, plastic skin` to stop style bleed.
  - "Dataset congruence is the biggest factor."
  - Recommends 55+ images for character LoRAs.

  — [ArtificialGuyBR: Illustrious & NoobAI guide](https://artificialguy.com/blog/illustrious-noobai-anime-guide/)
- **DCAI original-character guides (Illustrious Jul/Sep 2025; Pony Jun 2025):** 100 images at 1024×1024 with 5 repeats. Trigger `dcai-girl`, class `1girl`, captions generated automatically. — [DCAI Illustrious](https://www.digitalcreativeai.net/en/post/original-character-lora-illustrious-character-training); [DCAI Pony](https://www.digitalcreativeai.net/en/post/original-character-lora-pony-character-training)

### Inferences
- For this laptop, Qwen-Image-Edit is the heaviest step, not the LoRA training. At FP8 (~15–20 GB weights) it always spills past 8 GB. Per the tested context, anything over ~8 GB VRAM becomes 10–400× slower, so each of 20–60 edits could take minutes. The project's own M3 spike (4-bit Qwen-Image on Blackwell) is the closest local evidence of what speed is achievable.
- Qwen-Edit output has its own rendering style. When the target is WAI-Illustrious anime or Pony Realism, training straight on Qwen-Edit images risks teaching the LoRA Qwen's style along with the identity. A common mitigation is to caption style terms or to re-render or img2img each edit through the target checkpoint at low denoise before training. That is an inference; no 2025–2026 source measured it.
- A lighter dataset path that stays within SDXL (no 20B model) is to render the character on WAI or Pony itself with the tested IP-Adapter (0.4–0.6) plus OpenPose/Depth ControlNet over a list of poses, then keep only the on-model outputs. It fits the measured ~6.5 GB SDXL peak. It inherits IP-Adapter's softened faces and palette bleed, which the trained LoRA would then learn.

### Gaps
- No 2025–2026 source gave measured seconds per image for Qwen-Image-Edit 2509/2511 on an 8 GB card, or any Nunchaku/SVDQuant 4-bit edit-model timings on Blackwell laptops. Not verified in this session.
- No first-hand, dated Reddit or Civitai post with a side-by-side "Qwen-Edit dataset → SDXL/Illustrious LoRA" result could be read: Civitai needs login and Reddit was unreachable.
- No verified 2025–2026 source on Flux Kontext or Flux.2 for building SDXL-anime datasets, or on WD14 vs JoyCaption vs Florence-2 accuracy for Illustrious captions.

## Q2. Which trainers run SDXL/Illustrious LoRA on 8 GB, with what settings, how fast, and do they work on Windows + RTX 50?

### Takeaway
kohya sd-scripts (CLI or bmaltais GUI) is the best-documented 8 GB SDXL LoRA path. It works on RTX 50-series once PyTorch is a cu128+ build and SDPA replaces xformers. OneTrainer can offload layers to system RAM, but a 2025 FP8 SDXL VRAM regression was reported. ai-toolkit supports SDXL on Windows, but an Illustrious practitioner advises against it. Expect roughly 1–1.5 h per LoRA at 1024 px on an 8 GB card. That is an estimate: no 2025–2026 source gives a measured 8 GB SDXL time.

### Cited Findings
- **sd-scripts SDXL docs** (doc text dates from the 2023 SDXL release, so older; still the repo's current guidance). LoRA "can be done with 8GB GPU memory (10GB recommended)". For 8 GB it recommends:
  - train U-Net only (`--network_train_unet_only`, "highly recommended for SDXL LoRA")
  - gradient checkpointing
  - `--cache_text_encoder_outputs` plus cached latents
  - an 8-bit optimizer or Adafactor
  - "lower dim (4 to 8 for 8GB GPU)"
  - `--bucket_reso_steps` can be 32 (not lower)

  — [kohya-ss/sd-scripts docs/train_SDXL-en.md](https://github.com/kohya-ss/sd-scripts/blob/main/docs/train_SDXL-en.md)
- **sd-scripts versions:** latest release v0.11.1 (2026-06-16), after v0.11.0 (2026-06-12, a major refactor). Requires PyTorch ≥ 2.6.0. "For RTX 50 series GPUs, PyTorch 2.8.0 with CUDA 12.8/12.9 should be used." — [kohya-ss/sd-scripts README](https://github.com/kohya-ss/sd-scripts)
- **kohya_ss GUI on Windows 11 + RTX 50 (guide, May 4, 2025):**
  - Python 3.10.11, CUDA Toolkit 12.8, PyTorch nightly cu128, accelerate 0.30.0 with bf16.
  - SDPA attention; xformers not installed.
  - Comment out `-e ./sd-scripts` in requirements.txt, then install `requirements_windows.txt`.
  - Two replies confirm it runs on an RTX 5060 Ti. The guide author had not yet tested training.

  — [bmaltais/kohya_ss Discussion #3218](https://github.com/bmaltais/kohya_ss/discussions/3218)
- **Blackwell failure mode (Jun 6, 2025):** an RTX 5090 with a cu121 build or xformers gave "CUDA error: no kernel image is available for execution on the device" and xformers DLL entry-point errors. No maintainer fix was posted. — [bmaltais/kohya_ss Issue #3276](https://github.com/bmaltais/kohya_ss/issues/3276)
- **Slow-training report:** one RTX 5090 user saw 4.78 s/it, against 1–2 s/it before a Windows reinstall, and could not configure the accelerate step. — [bmaltais/kohya_ss Issue #3332](https://github.com/bmaltais/kohya_ss/issues/3332) (via search summary)
- **PyTorch 2.7.0** was the first stable release with native sm_120 (CUDA 12.8 wheels). — [SaladCloud docs](https://docs.salad.com/container-engine/tutorials/machine-learning/pytorch-rtx5090)
- **OneTrainer FP8 SDXL LoRA VRAM regression (reported 2025):** on an RTX 2060 6 GB at 1024 px, batch 1, FP8 weights:
  - Oct 2024 build (475dc51): **4.9 GB VRAM, ~3.54 s/it**
  - master build (~May 2025): **12.2 GB, ~80 s/it**

  It spilled into shared memory and was 20× slower. The regression persisted across adam8bit, lion8bit and Prodigy. Root cause unresolved in the thread; PR #989 is closed. — [Nerogar/OneTrainer Issue #934](https://github.com/Nerogar/OneTrainer/issues/934)
- **OneTrainer RAM offload (announced Nov 2024, older):** set Gradient checkpointing = `CPU_OFFLOADED` and "Layer offload fraction" 0–1. Higher values use more system RAM, with "low impact on training times" per the announcement. — [r/StableDiffusion repost, daslikes](https://daslikes.wordpress.com/2024/11/02/onetrainer-now-supports-efficient-ram-offloading-for-training-on-low-end-gpus-via-r-stablediffusion/); [Offline Creator OneTrainer guide](https://offlinecreator.com/guide/onetrainer-lora-training-guide)
- **ai-toolkit:**
  - Supports SDXL/SD1.5 LoRA and has a Windows one-click path (`run_windows.bat`, UI on :8675). — [Hysen Labs](https://hysenlabs.com/en/projects/ostris-ai-toolkit); [DeepWiki](https://deepwiki.com/ostris/ai-toolkit)
  - Its 8 GB recipe for Z-Image (not SDXL): batch 1, gradient checkpointing, quantization, "Low VRAM", 512-only resolution, offload if needed. — [RunComfy](https://www.runcomfy.com/trainer/ai-toolkit/z-image-8gb-vram-lora-training)
  - An Illustrious practitioner uses kohya_ss and "explicitly advises against AI-Toolkit". — [ArtificialGuyBR](https://artificialguy.com/blog/illustrious-noobai-anime-guide/)
- **Hardware tiers (Jun 20, 2026):** 8 GB SDXL LoRA is "Possible… Slow; gradient checkpointing + 8-bit Adam + block swap mandatory". 12 GB is comfortable. On an RTX 3090, SDXL LoRA takes 30–60 min for ~1,500 steps. Typical SDXL settings: dim 32 (up to 64), alpha 16, LR ~1e-4, AdamW8bit, 1024², 1,000–2,000 steps. — [LocalAIMaster](https://localaimaster.com/blog/image-lora-training-local-guide)
- **Older low-VRAM anecdotes (2024):** the lowest seen was 6 GB, some managed 4 GB, and overflowing to RAM had "minimal speed impact" per one user. Another took 11 h for one epoch of 300 mixed-size high-res images on 16 GB. — [bmaltais/kohya_ss Discussion #2594](https://github.com/bmaltais/kohya_ss/discussions/2594)
- **Illustrious on an 8 GB RTX 3070 (Jan 2025):** a Civitai guide covers LoRA Easy Training Scripts (derrian-distro). The content is login-walled and could not be read. — [Civitai article 10307](https://civitai.com/articles/10307/lora-easy-training-dev-derrian-distro-for-illustrious-xl-with-3070rtx-8gb-of-vram-january-2025)

### Inferences
- **Recommended 8 GB kohya recipe** (synthesised from the sd-scripts docs plus the tested peak/spill context):
  - SDXL LoRA, U-Net only, cached latents and cached text-encoder outputs (these two are incompatible with training the TE)
  - gradient checkpointing, `--sdpa`, mixed precision bf16, `--fp8_base` if memory is tight
  - AdamW8bit or Adafactor, batch 1, 1024 buckets (or 768 for speed)
  - rank 8–32 (the docs' "4–8 for 8 GB" is older, conservative advice)
  - no sample generation during training; watch Task Manager "shared GPU memory" so nothing spills
- **Time estimate for the RTX 5060 Laptop:** the only measured low-VRAM figure is ~3.5 s/it at 1024 on a 6 GB RTX 2060. A 5060 Laptop is newer and faster, so ~1.5–3 s/it is a plausible guess, giving ~40–90 min for 1,500 steps. If anything spills over 8 GB, the OneTrainer #934 case shows how bad it gets (~80 s/it).
- **OneTrainer:** pin a known-good version and verify VRAM before relying on it for SDXL FP8. The 2025 regression may or may not be fixed.

### Gaps
- No 2025–2026 measured s/it or total time for SDXL LoRA on any 8 GB Blackwell card (5060/5060 Laptop/5050), or on an 8 GB 40-series laptop.
- OneTrainer's official RTX 50 / cu128 status was not confirmed from its repo in this session.
- No first-hand Illustrious/Pony run on ai-toolkit with VRAM numbers.
- musubi-tuner is aimed at video/newer models; I found no evidence it targets SDXL.

## Q3. How good are single-image-derived LoRAs vs IP-Adapter, and what are the failure modes and fixes?

### Takeaway
No 2025–2026 source gives a controlled "one image → synthetic dataset → SDXL LoRA vs IP-Adapter" comparison. The evidence is indirect: trained LoRAs keep identity better than adapters and transfer across checkpoints in the same family. Single-image training overfits (pose, outfit, background, low diversity) unless the dataset is varied, captions untie non-identity attributes, and training settings are tuned.

### Cited Findings
- **Transfer and default-settings results:** DCAI's Illustrious-XL v2.0 original-character LoRA worked on Illustrious v0.1 and other checkpoints in the Illustrious lineage. With default settings (AdamW8bit, 1e-4, dim 8/α 1, 1,600 steps) it produced "only slight costume effects" and little facial change. Their Cosine + Prodigy run "well reproduced" the character. — [DCAI Illustrious](https://www.digitalcreativeai.net/en/post/original-character-lora-illustrious-character-training)
- **Pony results:** DCAI's Pony V6 character LoRA gave "reasonably high-quality" results, and long shots needed ADetailer to fix faces. — [DCAI Pony](https://www.digitalcreativeai.net/en/post/original-character-lora-pony-character-training)
- **T-LoRA (AAAI 2026):** fine-tuning from limited samples "frequently suffers from overfitting… compromising both generalization capability and output diversity". Higher diffusion timesteps overfit more than lower ones. T-LoRA's fix is timestep-dependent rank masking plus orthogonal init. — [arXiv 2507.05964](https://arxiv.org/abs/2507.05964)
- **HyperLoRA (Mar 2025):** per-person LoRA/DreamBooth gives higher fidelity, while adapter (zero-shot) methods "often exhibit a lack of naturalness". — [HF: bytedance-research/HyperLoRA](https://huggingface.co/bytedance-research/HyperLoRA) (via abstract/search summary)
- **Style bleed fix:** add negative captions (`3d, cgi, render, plastic skin`) and keep the dataset congruent. — [ArtificialGuyBR](https://artificialguy.com/blog/illustrious-noobai-anime-guide/)
- **Overfitting fix:** vary pose, outfit, background, framing and lighting, and drop near-duplicates. — [Offline Creator Pony guide](https://offlinecreator.com/guide/pony-lora-training-guide)
- **Hidden-attribute fix:** the Illustrious guide uses Min SNR gamma 4 and noise offset 0.02. It caps steps at ~1,000–3,000 and checks intermediate epochs. — [ArtificialGuyBR](https://artificialguy.com/blog/illustrious-noobai-anime-guide/)

### Inferences
- **Expected failure modes** of a LoRA trained on 20–60 edit-model images of one source:
  1. **Pose, outfit or background lock-in.** Fix by varying these in the edit prompts and by captioning the clothing and background, so the trigger holds only face, hair and body.
  2. **Style bleed from the edit model.** Fix with style tags or negative captions, or by re-rendering through the target checkpoint.
  3. **"Same face as the source".** This is usually the desired identity. The risk is the LoRA copying the source's expression and lighting, so include expression and lighting variation.
  4. **Weak effect at dim 8 with default LR.** This matches DCAI's default-settings result. Raise rank to 16–32 or the LR.
- **Versus the tested IP-Adapter baseline (softened faces, palette bleed):** a LoRA should avoid the per-image palette bleed because there is no reference image at inference. Its faces are only as sharp as the training images, so a soft or inconsistent dataset produces a soft LoRA.

### Gaps
- No measured identity-similarity scores (e.g., face-embedding cosine or CLIP-I) comparing a single-image LoRA to IP-Adapter on WAI or Pony.
- No readable 2025–2026 Reddit or Civitai post with first-hand before/after results. Both were blocked.

## Q4. Anything faster than full LoRA training, and is per-character training practical inside an app?

### Takeaway
Tuning-free options exist (HyperLoRA for SDXL, IP-Adapter, which is already tested), plus research single-image LoRA methods (T-LoRA). None is a proven drop-in for Illustrious anime on 8 GB. Per-character LoRA training is practical only as a background job of roughly 1–3 hours per character (dataset generation plus training) on this laptop, not as an "instant" step at character creation.

### Cited Findings
- **HyperLoRA (ByteDance, Mar 2025):** an SDXL plug-in network generates LoRA weights for "zero-shot personalized portrait generation (supporting both single and multiple image inputs)" without per-person fine-tuning. The card does not state anime support, ComfyUI support or VRAM. — [HF: bytedance-research/HyperLoRA](https://huggingface.co/bytedance-research/HyperLoRA)
- **T-LoRA (AAAI 2026):**
  - Official SDXL and FLUX.1-dev scripts adapted from the diffusers DreamBooth examples, with a single-image mode (`one_image=`).
  - Example settings: rank 64, min_rank 32, 1024 px, 800 epochs, mixed precision "no".
  - "approximately 30 minutes" per model on one H100.
  - Multi-adapter inference and LoRAShop integration.
  - Custom SDXL checkpoints and ComfyUI are not documented.

  — [ControlGenAI/T-LoRA](https://github.com/ControlGenAI/T-LoRA)
- **Known characters without a LoRA:** Illustrious and NoobAI can reproduce thousands of known characters by name. That does not help original characters. — [ArtificialGuyBR](https://artificialguy.com/blog/illustrious-noobai-anime-guide/)
- **NoobAI/Illustrious IP-Adapter:** a workflow is described as mimicking the overall style of the reference image, not identity specifically. — [Civitai NoobAI/Illustrious IPAdapter workflow](https://civitai.com/models/1466666/noobai-illustrious-ipadapter-workflow)
- **Rough time budget:**
  - SDXL LoRA ~1,500 steps: 30–60 min on a 24 GB RTX 3090, "significantly" longer with RAM offload on small cards. — [LocalAIMaster](https://localaimaster.com/blog/image-lora-training-local-guide)
  - Qwen-Image-Edit FP8 on a ~6 GB-class card is "Slow, but it runs". — [lilting channel](https://lilting.ch/en/articles/qwen-image-edit-2511-local-specs)

### Inferences
- **Per-character app pipeline on this laptop:**
  1. Qwen-Image-Edit, 20–40 images: tens of minutes to 1+ hour with offload, Lightning 4-step.
  2. Auto-tagging: minutes.
  3. kohya SDXL LoRA, ~1,000–1,500 steps: ~40–90 min.

  Total ~1.5–3 h per character, and the GPU is unusable for chat/image generation meanwhile. That is viable as an optional "lock this character" overnight job with a progress UI. It is not viable at creation time.
- **Automation:** every step is scriptable. sd-scripts is a CLI (`sdxl_train_network.py` with a TOML dataset config), and Qwen-Edit runs through diffusers or ComfyUI API. There is no GUI dependency, so the app can queue jobs.
- **Bridge strategy:** use the IP-Adapter reference (already working) at creation time, and swap to the trained LoRA once the background job finishes.
- **Anime caveat:** face-embedding methods (InstantID/FaceID/PuLID-style, and possibly HyperLoRA) rely on real-face detectors and are likely weak on anime faces. This is unverified and needs a test on WAI before relying on it. They may suit Pony Realism better.

### Gaps
- No measured end-to-end "minutes per character" figure from anyone running a single-image → LoRA pipeline on 8 GB in 2025–2026.
- HyperLoRA's ComfyUI support, VRAM needs and behaviour on Illustrious/Pony fine-tunes are unknown.
- T-LoRA's memory needs with mixed precision "no" at 1024 px on SDXL were not given; it probably exceeds 8 GB without changes (inference).
- Textual inversion on SDXL for OC identity: no 2025–2026 source found.

## Q5. Illustrious / Pony-specific settings posted by practitioners

### Takeaway
Practitioners broadly agree on AdamW8bit, UNet LR around 1e-4 to 3e-4 with TE ~10× lower (or U-Net only), 1024 px, batch 1–4, 1,000–3,000 steps, rank 8–64, cosine or constant schedulers. They disagree on Prodigy, and on whether to train on the base model (Illustrious v2.0 / Pony V6) or directly on the checkpoint you will use (WAI / Pony Realism).

### Cited Findings
**Illustrious — DCAI** (kohya_ss GUI, base Illustrious-XL-v2.0; Jul 2025, updated Sep 2025). [Source](https://www.digitalcreativeai.net/en/post/original-character-lora-illustrious-character-training)
- Default run: AdamW8bit, UNet 1e-4 / TE 5e-5, cosine, dim 8 / alpha 1, 1,600 steps, batch 1, 1024², clip_skip 2, 100 images × 5 repeats.
- Result: weak identity (see Q3).
- Recommended instead: Cosine Annealing + Prodigy. The detailed values are paywalled.

**Illustrious — ArtificialGuyBR** (character LoRA, updated 2026-07-27). [Source](https://artificialguy.com/blog/illustrious-noobai-anime-guide/)
- Base Illustrious XL v2.0 "STABLE", trained with kohya_ss.
- AdamW8bit, UNet 3e-4 / TE 3e-5 (10:1).
- Dim 64 / alpha 32 (~70 MB file); 48/24 for complex characters.
- ~1,000–3,000 steps, batch 1–4, constant or cosine-with-restarts, Min SNR γ 4, noise offset 0.02.
- "Avoid Prodigy optimizer: Multiple reports of poor results on Illustrious and Pony".

**Pony — DCAI** (base "Pony Diffusion V6 XL – v6 Start with this one"; Jun 2025). [Source](https://www.digitalcreativeai.net/en/post/original-character-lora-pony-character-training)
- AdamW8bit, 1e-4 / TE 5e-5, cosine, rank 8 / alpha 1, 1024², batch 1, 1,600 steps, 5 repeats.
- Score tags ranged from none to score_9.
- The LoRA transferred to other Pony-lineage models.

**Pony — Offline Creator.** [Source](https://offlinecreator.com/guide/pony-lora-training-guide)
- "Train on the checkpoint you expect to use most often". The original V6 XL is the cleanest compatibility reference.
- Pony Realism inference: DPM++ 2M Karras, 20–30 steps, CFG 5–7, 1024².

**Conflict on rank for 8 GB.** The sd-scripts docs say dim 4–8 ([older doc](https://github.com/kohya-ss/sd-scripts/blob/main/docs/train_SDXL-en.md)). Practitioners use 8/1 (DCAI) or 64/32 (ArtificialGuyBR). LocalAIMaster suggests 32/16 ([source](https://localaimaster.com/blog/image-lora-training-local-guide)).

**Conflict on Prodigy.** DCAI recommends Prodigy for characters. ArtificialGuyBR says avoid it on Illustrious and Pony.

### Inferences
- **Starting point for WAI-Illustrious v17:**
  - kohya, trained on WAI v17 itself for maximum fidelity, or on Illustrious v1.0/v2.0 for portability. DCAI shows cross-lineage transfer works, but WAI is the only target.
  - U-Net only, AdamW8bit, UNet LR 1e-4 to 2e-4, rank 16–32 / alpha half the rank.
  - 1024 buckets, batch 1, ~1,200–1,600 steps over 20–40 images.
  - Save every ~200–300 steps and pick the epoch by test prompts that change outfit, pose and scene.
  - Booru-style tags with a unique trigger (e.g., `ohwx_<name>`) and `1girl`/`1boy` class tag. Tag clothing and background so they stay promptable.
- **Starting point for Pony Realism v2.2:** same recipe, trained on Pony Realism v2.2 directly (photoreal textures differ a lot from Pony V6 anime). Put the score/source tags the checkpoint expects at the start of the captions.
- **Adults only:** captions and edit prompts should state adult age descriptors, and the dataset should be checked, because edit models can drift toward younger-looking faces on anime styles. Not sourced; a product-safety precaution.

### Gaps
- No readable 2025–2026 source gave settings specific to WAI-Illustrious v17 or Pony Realism v2.2. Civitai model pages and articles are login-walled.
- No sourced comparison of training on base models vs training directly on WAI or Pony Realism for original-character LoRAs.
