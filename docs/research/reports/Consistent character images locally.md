# Bake each character into a LoRA

The 2025–2026 answer is to stop asking a reference image to carry identity through the final render. Every working public pipeline found (Mickmumpitz's character sheets, CharForge, the Qwen-edit dataset workflows) ends the same way. One approved base image is expanded into 20–40 varied images, a small per-character LoRA is trained on them, and scenes are rendered with that LoRA and no adapter, then finished with the checkpoint creator's own hires recipe and a face-detail pass. That route fixes both defects seen locally at the root. Palette bleed comes from IP-Adapter writing into SDXL's style block, and soft faces come from conditioning every step of every region on a soft reference. A LoRA puts identity into the weights, so the sharpening passes run clean. On this laptop the LoRA is feasible but slow. kohya's docs say SDXL LoRA training fits 8 GB with U-Net-only, cached, 8-bit settings, and a realistic estimate is 1.5–3 hours per character including dataset generation. So it belongs in an idle-time background job, with a tuned IP-Adapter as the bridge until it finishes. Two characters in one image is a composition problem first (count tags, a two-figure pose or a masked layout) and an identity problem second. The identity part is solved by per-character masked passes with one LoRA active at a time, because two globally loaded character LoRAs bleed and diffusers has no per-region LoRA. Edit models, Qwen-Image-Edit-2511 above all, hold identity best and fuse two people natively. At 20B parameters, though, they run on 8 GB only through 4-bit weights and layer streaming, at minutes per image, so they fit as optional dataset and composite tools, not as the per-scene engine. No source measures single-image LoRA quality against IP-Adapter on WAI or Pony, or LoRA training time on an 8 GB Blackwell laptop. The plan below therefore tests the two riskiest assumptions, polish quality and 8 GB training, in slices 1–5, before any app work depends on them.

*Evidence tags used below:* **[Measured]** means a cited source or the local tests measured it. **[Documented]** means a source documents the feature or setting but nobody has measured its effect on WAI or Pony. **[Inferred]** means it is my reasoning from the sources and nobody has tested it. **[Test first]** means run a quick local check before building on it.

## Every working public pipeline ends in a character LoRA

The local results are the baseline:

| Local result | Measurement |
|---|---|
| diffusers (torch 2.11+cu128) with WAI-Illustrious v17, Nova Anime XL, Pony Realism v2.2 | ~25–30 s per 832×1216 image, CPU offload, ~6.5 GB peak |
| IP-Adapter-plus | holds identity, but softens faces and pulls in the reference's palette |
| hires img2img pass | visibly helped |
| Qwen-Image-2.1, 4-bit | held identity, ~2 min/image at ~10.9 GB |
| anything past ~8 GB | spills and runs 10–400× slower |

The local LLM also needs the same GPU.

Against that baseline, the 2025–2026 practitioner record is unusually uniform. The most-copied workflow family, Mickmumpitz's, turns one input image into a multi-angle character sheet, cuts it into **10–15 crops and trains a LoRA** on them ([pIXELsHAM](https://www.pixelsham.com/2024/12/23/mickmumpitz-create-consistent-characters-from-an-input-image-with-flux-and-a-character-sheet-comfyui-tutorial-installation-guide/)). It dates from December 2024 and has since added Qwen models, expression control and turntables ([RunComfy](https://www.runcomfy.com/comfyui-workflows/consistent-character-creator-3-0)).

CharForge automates the same chain end to end: reference, sheet, auto-captions, a rank-8 LoRA, then diffusers inference. It needs **48 GB of VRAM and 60 GB of RAM** and still takes 30–40 minutes on an L40S ([CharForge](https://github.com/RishiDesai/CharForge)).

The late-2025 variant swaps the sheet generator for an instruction-edit model. One reference plus ~50 prompt variations run through Qwen-Image-Edit produces a LoRA dataset, and SDXL is listed as a valid training target ([Weird Wonderful AI Art](https://weirdwonderfulai.art/comfyui/qwen-image-edit-can-create-character-consistent-lora-dataset/)). The workflows built on it recommend **20–50 varied images, with variety mattering more than volume** ([Floyo](https://www.floyo.ai/workflows/create-character-lora-dataset-using--ac2829kggykc)).

None of these pipelines uses a reference adapter as the final identity mechanism. Roleplay front-ends have not caught up. SillyTavern's docs say it has no built-in consistency mechanism and leave users to per-character prompt prefixes and LoRA tags ([SillyTavern docs](https://docs.sillytavern.app/extensions/stable-diffusion/)). The closest open-source analogue is VNCCS, a ComfyUI suite built on Illustrious that generates visual-novel sprites in stages (base, pose, outfit, emotion). Its README does not say how it holds identity ([VNCCS](https://github.com/AHEKOT/ComfyUI_VNCCS)). The research found no open-source roleplay app that trains per-character LoRAs automatically, though that search was not exhaustive.

Adapters lose for structural reasons, not because they are badly tuned. The only 2026 measurement on anime characters scores appearance preservation (CLIP-I) at **0.791 for IP-Adapter and 0.815 for IP-Adapter Plus**, against 0.860 for a purpose-built AnimeAdapter whose weights are not yet released. The authors note that IP-Adapter often drops fine appearance details ([arXiv 2605.20237](https://arxiv.org/html/2605.20237v1)). ByteDance's HyperLoRA work makes the general point: per-person LoRA tuning gives higher fidelity, while zero-shot adapters tend to look less natural ([HyperLoRA](https://huggingface.co/bytedance-research/HyperLoRA)).

The diffusers documentation explains both local defects. IP-Adapter injects layout through down `block_2` and style (colour, texture, overall feel) through up `block_0`. Inserting it into every layer pushes the output toward the image prompt and reduces diversity ([diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)). An all-block, all-step adapter therefore copies the reference's palette by design. Because it conditions every denoising step across the whole frame, it also keeps pulling fine facial detail back toward the reference's softness **[Inferred]**. A LoRA moves identity into the weights. No reference image is present at render time, so nothing pulls the sharpening passes backwards **[Inferred]**.

Face-embedding methods do not solve the anime case. PuLID, InstantID and IP-Adapter FaceID all build on real-face embeddings. FaceID in diffusers needs InsightFace `buffalo_l` to detect a face before anything else runs ([diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)), and a detector trained on real faces often misses anime faces, leaving these methods nothing to embed **[Inferred]**.

For Pony Realism they are real candidates. PuLID-v1.1 SDXL claims better naturalness and similarity than v1, though it is a NeurIPS 2024 method, older than the target window ([PuLID](https://github.com/ToTheBeginning/PuLID)). A 2026 secondary guide describes PuLID as trained to penalise style leakage. It also says InstantID's keypoint ControlNet locks the reference's head pose and makes it the heaviest of the three ([aiofm.info](https://aiofm.info/en/guides/pulid-vs-instantid-vs-faceid)).

Two other methods are ruled out on memory:

- **InstantCharacter** (Tencent) is FLUX-only and needs 24–48 GB ([InstantCharacter #3](https://github.com/Tencent/InstantCharacter/issues/3)).
- **StoryDiffusion's** shared attention holds identity only within one batch and was tested on 24 GB ([StoryDiffusion](https://github.com/HVision-NKU/StoryDiffusion)).

The only anime-trained SDXL IP-Adapter, kataragi's NoobAI adapter, is described by its author as undertrained and needing per-image tuning ([kataragi/Noob_ipadapter](https://huggingface.co/kataragi/Noob_ipadapter)).

Edit models are the strongest identity holders available, but they need more than 8 GB. A July 2026 head-to-head of eight editors on an RTX 5060 Ti 16 GB found:

- **Qwen-Image-Edit-2511 and Microsoft's Mage-Flow-Edit-Turbo kept facial features best** and preserved anime styles.
- FLUX.2 klein largely redrew anime input in its own style.
- 2511 took ~32 s at INT8 with 4 steps.
- No model handled 90° camera turns.

([note.com](https://note.com/ai_0049/n/n8051776106dc?hl=en))

Klein is also filtered at the training-data and I/O level, which rules it out for adult content without community add-ons ([note.com](https://note.com/cute_agapan9087/n/naf0940a4bf9b?hl=en)).

Qwen's 20B transformer is ~7.4 GB even at Q2_K ([Phil2Sat GGUF](https://huggingface.co/Phil2Sat/Qwen-Image-Edit-Rapid-AIO-GGUF)). Owners of 6 GB laptops report roughly 2 minutes per 1024² image with GGUF plus Lightning ([HackerNoon](https://hackernoon.com/a-beginners-guide-to-qwen-image-edit-rapid-aio-gguf-best-use-cases-limitations-plus-more)) and 3–5 minutes at Q6_K ([QuantStack #3](https://huggingface.co/QuantStack/Qwen-Image-Edit-GGUF/discussions/3)). Nunchaku's 4-bit build, which uses FP4 weights on Blackwell, can stream layers and run in **about 3–4 GB of VRAM** ([Nunchaku docs](https://nunchaku.tech/docs/nunchaku/usage/qwen-image-edit.html)). A January 2026 report, however, shows its kernels failing on a Windows RTX 50 card ([nunchaku #888](https://github.com/nunchaku-ai/nunchaku/issues/888)).

| Method | Runs on this laptop? | Identity | Quality cost | WAI (anime) | Pony Realism |
|---|---|---|---|---|---|
| IP-Adapter-plus, default | Yes, ~6.5 GB, 25–30 s (local) | Good; CLIP-I ~0.8 on anime (preprint) | Soft faces, palette bleed (local) | Works | Works |
| IP-Adapter, block-wise + masked + early stop | Yes **[Inferred]** | Slightly below default **[Inferred]** | Reduced **[Test first]** | Bridge | Bridge |
| Character LoRA (SDXL) | Inference yes; 8 GB training documented but slow | Highest per practitioners | None added at render **[Inferred]** | Primary path | Primary path |
| FaceID Plus v2 / PuLID-SDXL | 8 GB VRAM unmeasured | Face only | PuLID targets low style leakage | Poor (face detector) **[Inferred]** | Bridge candidate **[Test first]** |
| InstantID | Needs an extra ControlNet | Face only | Locks head pose | Poor | Not recommended |
| Qwen-Image-Edit-2511 (20B) | Only 4-bit + layer streaming; minutes/image | Best-rated | Own style; needs SDXL re-render **[Inferred]** | Keeps style | Good |
| Qwen-Image-2.1 (7B, installed) | 10.9 GB / ~2 min (local); ~6.1 GB with encoder on CPU (community) | Held identity (local) | Style differs from WAI/Pony | **[Test first]** | **[Test first]** |
| FLUX.2 klein 4B | 8.4 GB on a 5090 | Weak on anime | Restyles anime; filtered | Poor fit | Poor fit |
| InstantCharacter, StoryDiffusion | No (24–48 GB, >20 GB) | n/a | n/a | Out | Out |

## Five changes turn IP-Adapter into a usable bridge

A LoRA takes hours on this machine, so a newly created character still needs a zero-training path for its first scenes. Every documented lever for that path is already in diffusers.

**1. Scale by block, not globally.** `set_ip_adapter_scale` accepts a dict. Keep down `block_2` (layout) and leave up `block_0` (style) near zero, for example `{"down": {"block_2": [0.0, 0.6]}, "up": {"block_0": [0.0, 0.2, 0.0]}}`. That should keep the character while dropping the reference's palette. The API and the block roles are documented ([diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)), but nobody has published a before/after on Illustrious or Pony **[Test first]**.

**2. Separate face from body.** The docs load the plus and plus-face adapters together at `[0.7, 0.3]`. They also restrict any reference to a region with `IPAdapterMaskProcessor`, passed via `cross_attention_kwargs={"ip_adapter_masks": masks}` ([diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)). A tight face crop can then drive the face while the prompt controls the rest of the frame.

**3. Stop the adapter before the detail steps.** diffusers has no start/end parameter for IP-Adapter. A `callback_on_step_end` that sets the scale to zero after ~60–70% of the steps imitates cubiq's `end_at` **[Inferred, Test first]**.

**4. Keep the adapter out of every hires and face pass.** Then the passes that add sharpness are not pulled back toward the soft reference **[Inferred]**.

**5. Precompute the reference embedding once per character.** Run `prepare_ip_adapter_image_embeds`, save the result with `torch.save`, and reload the adapter with `image_encoder_folder=None`. That keeps the CLIP-ViT-H encoder, a large part of the earlier local VRAM spill, off the generation path. `enable_model_cpu_offload()` must come after `load_ip_adapter()`, or the call errors ([diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)).

The magenta/halftone artifacts from a pale reference point to the same global colour statistics. Auto-levelling and tightly cropping the reference before encoding is a cheap fix **[Inferred]**.

The ComfyUI IP-Adapter node that most tutorials assume has been maintenance-only since 14 April 2025 ([cubiq](https://github.com/cubiq/ComfyUI_IPAdapter_plus)). That does not affect the diffusers path.

For Pony Realism, FaceID Plus v2 is a documented alternative bridge: InsightFace embeddings passed as `ip_adapter_image_embeds`, with DDIM or Euler recommended for face models ([diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)). Whether InsightFace's ONNX runtime works on sm_120 was not researched **[Test first]**.

## An 8 GB laptop can train the LoRA, but only while nothing else runs

The dataset sets the ceiling. Sources disagree on size: 20–50 varied images ([Floyo](https://www.floyo.ai/workflows/create-character-lora-dataset-using--ac2829kggykc)), 55+ for Illustrious characters ([ArtificialGuyBR](https://artificialguy.com/blog/illustrious-noobai-anime-guide/)), or 100 images at 5 repeats in DCAI's original-character runs ([DCAI Illustrious](https://www.digitalcreativeai.net/en/post/original-character-lora-illustrious-character-training)). They agree that variety matters more than count: angle, expression, pose, outfit, background, framing and lighting. Blurry frames, bad crops and near-duplicates must go ([Offline Creator](https://offlinecreator.com/guide/pony-lora-training-guide)).

Captions:

- Use a unique trigger token plus the class tag.
- Tag clothing and background explicitly, so the trigger binds only to face, hair and body.
- Add per-image negative style captions such as `3d, cgi, render` to curb style bleed ([ArtificialGuyBR](https://artificialguy.com/blog/illustrious-noobai-anime-guide/)).
- For Pony, start with the score and source tags the checkpoint expects ([Offline Creator](https://offlinecreator.com/guide/pony-lora-training-guide)).

A LoRA's faces can only be as sharp as its training images **[Inferred]**. Put every dataset image through the full polish chain (hires plus face pass, adapter off) before keeping it.

There are three ways to produce that dataset on this laptop.

**Cheapest: render it on WAI or Pony itself**, using the tuned adapter with varied prompts or a pose ControlNet. This stays inside the measured ~6.5 GB envelope and in the target style, but it inherits whatever softness the adapter leaves **[Inferred]**.

**Strongest: Qwen-Image-Edit-2511.** Its model card claims better character consistency than 2509 and new viewpoints from one portrait ([Qwen-Image-Edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)). Dataset workflows loop it over ~60 prompts from a single front-facing image ([Floyo 2511](https://www.floyo.ai/workflows/qwen-2511-edit-single-image-to-chara-65qytngb2sux)). On 8 GB that means either Nunchaku FP4 with layer streaming, or a Q2–Q3 GGUF that practitioners call noticeably softer ([Thunder Compute](https://www.thundercompute.com/blog/qwen-image-edit-comfyui)). Its output must go back through the target checkpoint at low denoise before training, or the LoRA learns Qwen's rendering style along with the face **[Inferred]**.

**Middle: the Qwen-Image-2.1 already installed.** One tester ran it at 1024² in **6.14 GiB with the text encoder kept on CPU** ([Alexey Fateev](https://x.com/superalesha/status/2101940249735634998), [code](https://github.com/alesha-pro/tools/tree/main/qwen-image-2.1)). That suggests the local 10.9 GB peak was mostly the 8B Qwen3-VL encoder sitting on the GPU **[Inferred, Test first]**. An experimental Qwen-Image-2.1 anime-consistency LoRA, trained on four-view model sheets, also exists ([WarmBloodAban](https://huggingface.co/WarmBloodAban/Qwen-Image-2.1-LoRAs)).

Whatever the generator, no editor tested in 2026 handled 90° turns ([note.com](https://note.com/ai_0049/n/n8051776106dc?hl=en)). Full profiles and back views will need pose-guided SDXL renders.

For training, kohya's sd-scripts is the best-documented 8 GB route. Its SDXL guide says LoRA training works on 8 GB (10 GB recommended) with ([sd-scripts SDXL docs](https://github.com/kohya-ss/sd-scripts/blob/main/docs/train_SDXL-en.md)):

- U-Net-only training
- gradient checkpointing
- cached text-encoder outputs and cached latents
- an 8-bit optimizer or Adafactor
- dim 4–8

The current release is v0.11.1 (June 2026, after a major v0.11.0 refactor). It asks for PyTorch 2.8 with CUDA 12.8/12.9 on RTX 50 cards ([sd-scripts](https://github.com/kohya-ss/sd-scripts)), so the local torch 2.11+cu128 should qualify **[Inferred, Test first]**.

Blackwell failures in 2025 came from cu121 builds and xformers, which throw "no kernel image" errors ([kohya_ss #3276](https://github.com/bmaltais/kohya_ss/issues/3276)). A May 2025 Windows 11 guide swaps xformers for SDPA. Two replies confirm that install runs on an RTX 5060 Ti, but nobody reported a training run ([kohya_ss #3218](https://github.com/bmaltais/kohya_ss/discussions/3218)).

OneTrainer offers offloading layers to system RAM, but a 2025 regression shows what spilling costs. The same 6 GB SDXL job went from **4.9 GB at 3.54 s/it to 12.2 GB at ~80 s/it** between builds ([OneTrainer #934](https://github.com/Nerogar/OneTrainer/issues/934)). An Illustrious practitioner advises against ai-toolkit ([ArtificialGuyBR](https://artificialguy.com/blog/illustrious-noobai-anime-guide/)).

Training settings conflict:

- **DCAI, default Illustrious run** (AdamW8bit, 1e-4, dim 8/alpha 1, 1,600 steps): barely changed the face. A cosine-plus-Prodigy run reproduced the character well, and the LoRA transferred across Illustrious-lineage checkpoints ([DCAI Illustrious](https://www.digitalcreativeai.net/en/post/original-character-lora-illustrious-character-training)).
- **ArtificialGuyBR:** AdamW8bit at a 3e-4 U-Net rate, dim 64/alpha 32, Min SNR γ 4 and noise offset 0.02, and warns against Prodigy on Illustrious and Pony ([ArtificialGuyBR](https://artificialguy.com/blog/illustrious-noobai-anime-guide/)).

A defensible first 8 GB run splits the difference **[Inferred]**:

- AdamW8bit, U-Net rate 1e-4 to 2e-4
- rank 16–32, alpha at half the rank
- 1024 buckets, batch 1
- ~1,200–1,600 steps, saving a checkpoint every 200–300

Train directly on the checkpoint you will render with, as the Pony guide recommends ([Offline Creator](https://offlinecreator.com/guide/pony-lora-training-guide)).

No source gives a measured SDXL LoRA training time on an 8 GB Blackwell laptop. A 2026 hardware guide calls 8 GB possible but slow, and puts ~1,500 steps at 30–60 minutes on a 24 GB RTX 3090 ([LocalAIMaster](https://localaimaster.com/blog/image-lora-training-local-guide)). Extrapolating from the 3.54 s/it low-VRAM figure gives **~40–90 minutes of training**. Adding dataset generation gives **~1.5–3 hours per character**, and the GPU can do nothing else meanwhile **[Inferred]**.

Research methods promise shortcuts, but neither documents custom checkpoints, anime, or 8 GB use:

- **T-LoRA** (AAAI 2026) targets single-image overfitting and trains in about 30 minutes on an H100 ([T-LoRA](https://github.com/ControlGenAI/T-LoRA)).
- **HyperLoRA** predicts SDXL LoRA weights zero-shot ([HyperLoRA](https://huggingface.co/bytedance-research/HyperLoRA)).

This route also makes the adult-only rule easier to enforce **[Inferred]**. The LoRA fixes the character's apparent age along with the face. One careful review of the dataset sets the look for every later scene: reject any image that reads as young, and write an explicit adult descriptor into every caption. No source addresses age drift in edit models or LoRAs, so the app has to enforce it through prompts, captions and output review.

## The "Civitai look" is the creator's recipe plus a face pass

The local hires test used settings both checkpoint creators steer away from.

| | WAI v17 (published 23 April 2026) | Pony Realism v2.2 (October 2024, older than the window) |
|---|---|---|
| Sampler | **Euler a** | **Euler a or DPM2 a**; explicitly not DPM++ 2M Karras |
| Steps | **15–30** | **30+** |
| CFG | **5–7** | **6–7** |
| Clip skip | not specified | **2** |
| Resolution | at least 1024 px | above 1024 |
| Positive tags | `masterpiece,best quality,amazing quality` | `score_9, score_8_up, score_7_up` |
| Negative tags | `bad quality,worst quality,worst detail,sketch,censor` | `score_4, score_5, score_6` |
| Hires | **R-ESRGAN 4x+ Anime6B, 1.5×, denoise 0.35–0.5, 20 hires steps** | 4x-UltraSharp, ≥1.5×, denoise 0.30 (from a mirrored card, not the creator page) |
| Source | [WAI on Civitai](https://civitai.com/api/v1/models/827184) | [Pony Realism](https://civitai.com/models/372465/pony-realism); [HF mirror](https://huggingface.co/TheImposterImposters/PonyRealism-v2.2MainVAE) |

A third-party guide lists DPM++ 2M Karras for Pony Realism ([Offline Creator](https://offlinecreator.com/guide/pony-lora-training-guide)); the creator's page should win.

The local pass (1.3×, denoise 0.35, DPM++ 2M Karras) sits at or below the low end of both ranges. The first change is therefore a 1.5× model upscale with Euler a **[Documented; the improvement is Test first]**. Implementation notes:

- In diffusers, Euler a is `EulerAncestralDiscreteScheduler`.
- The .pth upscalers are not diffusers models. They need a loader such as spandrel or Real-ESRGAN before the img2img pass **[Inferred]**.
- `clip_skip=2` needs checking on the SDXL pipeline **[Test first]**.

No source evaluates manhwa style specifically; WAI's anime look is the closest proxy.

The other half of the look is a face-detail pass. ADetailer and Impact FaceDetailer provide it in A1111 and ComfyUI; diffusers lacks it. DCAI found its Pony character LoRA needed ADetailer to fix faces in long shots ([DCAI Pony](https://www.digitalcreativeai.net/en/post/original-character-lora-pony-character-training)). It is easy to hand-roll with the existing img2img components:

1. Detect the face box.
2. Crop with padding and upscale the crop to ~1024 px.
3. Run img2img at moderate denoise.
4. Paste it back with a feathered edge.

Denoise 0.35–0.5 and a 5–10 px feather come from general community practice, not a cited source **[Test first]**. The detector must find anime faces, which rules out InsightFace **[Inferred]**. Once a LoRA exists, run the face pass with the LoRA active, so it reinforces identity where it matters most **[Inferred]**.

For gaze, Danbooru tags cost nothing: `looking at viewer`, with `looking away, looking to the side` in the negative **[Inferred]**. OpenPose with face keypoints is the stronger fix. ControlNet options:

- **Illustrious-specific pose ControlNets** appeared in January 2025: windsingai pose, and openpose-v2_1 at 2.32 GB fp16 ([Civitai CNXL collection](https://civitai.com/api/v1/models/136070)).
- **xinsir's union ProMax** covers openpose, depth and tile in one ~1B-parameter file. It does not mention Pony or Illustrious, and its training is paused ([xinsir](https://huggingface.co/xinsir/controlnet-union-sdxl-1.0)).

Each ControlNet is ~2.3–2.5 GB on top of a ~5 GB UNet. On 8 GB, pose control needs offload and should apply only to the base pass **[Inferred]**.

One plumbing fix matters. The earlier over-8 GB blow-up from deriving a second pipeline with `from_pipe` on an offloaded pipe most likely came from the derived pipe lacking offload hooks. Either call `enable_model_cpu_offload()` on it too, or keep one img2img pipeline for both hires and face passes **[Inferred, Test first]**. Base render, 1.5× hires and face pass together should take about twice the current 30 s **[Inferred]**.

## Two characters need composition first and identity second

Plain prompting is the baseline to beat. Illustrious and Pony understand count tags. A June 2026 Illustrious guide sets the conventions: total count (`2boys` or `1boy, 1girl`) in a shared line, one tag block per character, and BREAK only between entities ([note.com Forge Couple guide](https://note.com/nonb0716/n/n02ce7117ac22?hl=en)). Guides admit this is unreliable. It depends on the model and on luck ([SeaArt](https://www.seaart.ai/articleDetail/d28i2gle878c73dnois0)), and at three or more characters SDXL regional prompting breaks down ([PixAI](https://blog.pixai.art/en/multi-character-lora-generation-guide/)). In local tests WAI showed the least colour bleed of the three checkpoints. Strong visual contrast between the two characters helps every method, for example blond vs black hair or a white vs dark outfit **[Inferred]**.

Attention Couple is the standard fix for features mixing between characters on SDXL-family models:

- **Forge Couple** implements it for Forge Classic/Neo, SD1 and SDXL only ([Forge Couple](https://github.com/Haoming02/sd-forge-couple/blob/main/README.md)). The June 2026 guide calls Illustrious a good match. It warns that an empty prompt line creates a phantom region, which produces a single character or mirrored twins ([note.com](https://note.com/nonb0716/n/n02ce7117ac22?hl=en)).
- **ComfyUI-ppm** provides the same node with bounding-box masks ([ComfyUI-ppm](https://github.com/pamparamm/ComfyUI-ppm)).

diffusers has no maintained SDXL regional-prompting pipeline. A request for SDXL support in the community pipeline was still unanswered in May 2025 ([regional-prompter #317](https://github.com/hako-mikan/sd-webui-regional-prompter/discussions/317)). What diffusers does have is **masked IP-Adapter with one reference per region**. The docs' example loads plus-face at `[[0.7, 0.7]]`, passes two face images and two masks, and prompts for two people ([diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)). It uses the same adapter and encoder as the current path, so its cost should be close to today's ~25–30 s **[Inferred, Test first]**.

Loading two character LoRAs globally bleeds, and every regional-LoRA mechanism found has a cost:

- **ComfyUI hooks** (a December 2024 feature, older than the window) give each character a masked conditioning branch. Every conditioning must be masked, or the unmasked areas come out as beige artifacts ([Comfy blog](https://blog.comfy.org/p/masking-and-scheduling-lora-and-model-weights)). Flux users saw runs grow from ~30 s to 14+ minutes, and in one case both characters took the second LoRA ([ComfyUI #5992](https://github.com/comfyanonymous/ComfyUI/discussions/5992)).
- **Impact-Pack RegionalSampler**, in a July 2026 recipe: generate the pair, mask each figure, then resample each region with its own LoRA. Settings were LoRA weight 0.8–1.0, Euler, 32–33 steps, CFG 5, 6–16 base-only steps, and overlap factor 10–24. It worked, but one character's eye shape still overwrote the other's, and it was unsuitable for batch use ([Civitai RegionalSampler article](https://civitai.com/articles/32568/anima-crossover-couple-generation-using-regional-sampler)).
- **FreeFuse** (October 2025) routes each LoRA to automatically derived masks using only activation words, and ships an SDXL workflow. There are no Illustrious reports or overhead numbers ([FreeFuse](https://github.com/yaoliliu/FreeFuse)).

In diffusers, LoRA adapters apply to the whole UNet, so the native answer is sequential **[Inferred]**:

1. Compose the pair with neither LoRA, or both at low weight.
2. Re-render each character's face or region with only that character's LoRA active.

ADetailer exposes this pattern with `[SEP]`, running a different prompt and LoRA on each detected face in order ([adetailer #533](https://github.com/Bing-su/adetailer/discussions/533), thread date unknown). An older multi-LoRA guide describes the same compose-then-inpaint route ([Scribd](https://www.scribd.com/document/694090409/Beginner-guide-to-work-with-multiple-Loras-for-complex-composition)).

Edit models offer the other route. Qwen-Image-Edit-2511 is explicitly built to fuse two separate person images into one group shot ([Qwen blog](https://qwen.ai/blog?id=qwen-image-edit-2511)). Its model card passes two input images with a left/right positional prompt at 40 steps and true CFG 4.0 ([Qwen-Image-Edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)). The limits:

- Reliability drops as the number of elements grows ([note.com](https://note.com/ai_0049/n/n8051776106dc?hl=en)).
- Each extra reference adds tokens, and therefore time, on a model that is already offloading **[Inferred]**.
- No source reports two-character identity accuracy for any editor.

The practical hybrid is to let the editor lay out the pair, then run the SDXL checkpoint over the result, then the per-face LoRA pass **[Inferred]**. Practitioners refine at denoise 0.1–0.4 ([Civitai 17885](https://civitai.com/articles/17885/my-ai-image-workflow-and-tools-guide)), while a full restyle needs 0.55–0.7 ([local-asset-studio #357](https://github.com/Chris0Jeky/local-asset-studio/issues/357)).

Adult descriptors belong in each character's own block or region, not only in the shared line, so each figure is conditioned as adult **[Inferred]**.

## diffusers stays the engine; ComfyUI is the fallback for regional tricks

ComfyUI has solved much of what makes 8 GB painful:

- **Async offload and pinned memory** have been on by default for NVIDIA since December 2025. They speed sampling by 10–50% when weights don't fit, and were tested down to an RTX 3070 8 GB ([ComfyUI blog](https://blog.comfy.org/p/new-comfyui-optimizations-for-nvidia)).
- **Dynamic VRAM**, stable on Windows since March 2026, loads weights just in time; its benchmark ran on an RTX 5060 ([Dynamic VRAM](https://blog.comfy.org/p/dynamic-vram-in-comfyui-saving-local)).
- It runs **headless** with a queue, `/interrupt`, `/free` to release models, and cached node outputs reported over WebSocket ([ComfyUI server routes](https://docs.comfy.org/development/comfyui-server/comms_routes)).

The costs are breakage. The Dynamic VRAM update broke some custom nodes ([Dynamic VRAM](https://blog.comfy.org/p/dynamic-vram-in-comfyui-saving-local)). cu128 builds broke others early on ([ComfyUI #6643](https://github.com/comfyanonymous/ComfyUI/discussions/6643)). A Nunchaku Qwen-edit loader regression reloads the model on every generation ([ComfyUI #14122](https://github.com/Comfy-Org/ComfyUI/issues/14122)).

Two headline speedups don't carry over to this setup:

- **NVFP4** needs a cu130 PyTorch. On other builds it can run up to 2× slower than fp8 ([ComfyUI blog](https://blog.comfy.org/p/new-comfyui-optimizations-for-nvidia)).
- **SageAttention's** 30–35% gain was measured on Qwen-Image-Edit on a 5090 ([ComfyUI #11583](https://github.com/Comfy-Org/ComfyUI/discussions/11583)). SDXL benchmark rows on a 5060 Ti are nearly identical with and without it ([ComfyUI #2970](https://github.com/Comfy-Org/ComfyUI/discussions/2970)).

Everything slices 1–7 need is in diffusers: adapter block scales, masks, precomputed embeds, ControlNet, img2img, inpaint and LoRA loading. Nunchaku exposes its layer-streaming mode through a diffusers API for the edit-model path ([Nunchaku docs](https://nunchaku.tech/docs/nunchaku/usage/qwen-image-edit.html)). Only Attention Couple, FreeFuse and the Impact detailers are ComfyUI-only. Adding ComfyUI as a headless second process is worth it only if the diffusers two-character slice fails **[Inferred]**.

Taking turns on the GPU matters more than raw seconds per image **[Inferred]**:

- Unload the image pipeline (delete its modules, then `torch.cuda.empty_cache()`) before handing the GPU back to llama.cpp.
- Batch a character's pending scenes while the model is loaded.
- Cache prompt and adapter embeddings per character.
- Pinned host memory competes with the LLM for the 32 GB of RAM.
- Laptop 5060s often run PCIe x8, which weakens offload.

## Nine slices, each ending in images you can judge

The order front-loads the two assumptions everything rests on:

- The polish chain makes WAI and Pony look Civitai-good on this laptop.
- An 8 GB LoRA training run finishes without spilling.

Every slice ends in a side-by-side grid at fixed seeds, so the judgement is visual. Use one clearly adult test character per checkpoint and the same six scene prompts throughout: close-up, medium shot, full body, dim lighting, a colourful setting, and a different outfit. Log `torch.cuda.max_memory_allocated()` and watch Task Manager's "Shared GPU memory" on every run. A rise there means the run is spilling.

| # | Build | What you judge | Evidence | Gate before moving on |
|---|---|---|---|---|
| 1 | Creator recipes + 1.5× model-upscale hires, no identity | Old vs new pass, same seed | Settings Documented; gain Test first | Visibly sharper; peak <8 GB; ≤~1 min/image |
| 2 | Hand-rolled face-detail pass | Faces in medium and full-body shots | Mechanism Documented; values Test first | Detector finds anime faces; no seams |
| 3 | Tuned IP-Adapter bridge | Default IPA vs block-wise vs block-wise + early stop | API Documented; effect Test first | Identity holds, palette follows the prompt, faces as sharp as slice 2 |
| 4 | ~30-image dataset for one WAI character | Contact sheet | Size/variety Documented; generator Inferred | ≥25 on-model, sharp, clearly adult images |
| 5 | First kohya LoRA on WAI | Grid comparing saved checkpoints on held-out prompts | Settings Documented but conflicting; 8 GB time Test first | No spill; one checkpoint holds identity while outfit, pose and scene change |
| 6 | LoRA scenes vs bridge scenes; repeat 4–5 for Pony Realism | Side-by-side | Inferred | Decide: LoRA becomes the final path |
| 7 | Two characters in diffusers | Identity swaps and bleed over 10 seeds | Masked IPA Documented; sequential LoRA passes Inferred | Both identities correct in most seeds |
| 8 | Escalations, only if 7 fails | Same grid | Test first | Beats slice 7 at acceptable time |
| 9 | App wiring: bridge now, LoRA overnight | Flow from character creation to first scenes | Inferred | Character locks without blocking chat |

### Slices 1–2 fix image quality before adding identity

**WAI settings:**

- `EulerAncestralDiscreteScheduler`, ~28 steps, CFG 6, the creator's positive and negative tag strings.
- Render at 832×1216, then try the creator's 1024×1344 if VRAM allows.
- Upscale with R-ESRGAN 4x+ Anime6B, resize to 1.5× of the base, then img2img at denoise 0.4 with 20 steps.

**Pony Realism settings:**

- Euler a (then try DPM2 a), 30 steps, CFG 6.5, clip skip 2.
- Score tags plus `source_realistic`, which the local tests found necessary.
- 4x-UltraSharp upscale, then img2img at denoise 0.30.

If the 1.5× VAE decode pushes the peak up, try VAE tiling **[Test first]**.

**Slice 2 face pass:** start from a YOLO-style face detector of the kind ADetailer uses, 32 px padding, crop resized to 1024, img2img at 0.4, 8 px feather. Check it detects faces on 20 WAI images before trusting it **[Test first]**. Judge both slices against the current 1.3×/DPM++ 2M Karras output at the same seeds. If the new chain isn't visibly better, nothing downstream will fix it.

### Slice 3 gives new characters a usable mode on day one

For one character:

- Precompute and save the IP-Adapter embedding, and load the adapter with `image_encoder_folder=None`.
- Enable offload after the adapter load.
- Render the six scenes under three configurations:
  1. today's uniform 0.5
  2. the block-wise dict from the bridge section
  3. the block-wise dict plus a `callback_on_step_end` that zeroes the scale at ~65% of steps
- Run hires and the face pass with the adapter unloaded or set to zero.
- Auto-level the reference before encoding.

For Pony Realism, add a FaceID Plus v2 variant if InsightFace installs cleanly on sm_120 **[Test first]**. The winning configuration becomes the in-app mode for characters whose LoRA doesn't exist yet.

### Slices 4–6 turn one approved image into a LoRA and prove it works

**Slice 4: dataset.** Generate ~40 candidates with the slice 3 pipeline, varying:

- angles: front, both three-quarters, and both profiles (profiles via pose ControlNet)
- about five expressions
- four lighting setups
- three outfits
- varied backgrounds and framings

Polish every candidate through slices 1–2 with the adapter off. Curate down to 25–35, deleting anything off-model, blurry, duplicated, or youthful-looking.

Caption each image:

1. Run an automatic tagger, then review every caption by hand.
2. Prepend a unique trigger (e.g. `kt_<name>`), the class tag (`1girl`/`1boy`) and an explicit adult descriptor.
3. Tag outfit and background, so they stay promptable.
4. For Pony, lead with the score and source tags.

If identity across the set is too loose, regenerate the weak angles with Qwen-Image-2.1 with its text encoder on CPU. Check that peak VRAM drops to ~6 GB and measure the time per image first. Push those images through WAI img2img at ~0.3 so the dataset stays in style **[Inferred, Test first]**.

**Slice 5: training.** Unload the LLM, then run sd-scripts. The flag names below come from the SDXL guide; check them against v0.11's refactor. Resolution 1024 and `bucket_reso_steps` 32 go in the dataset TOML:

```powershell
accelerate launch sdxl_train_network.py `
  --pretrained_model_name_or_path "WAI-illustrious-SDXL-v17.safetensors" `
  --dataset_config char.toml --output_dir out --output_name kt_name `
  --network_module networks.lora --network_dim 32 --network_alpha 16 `
  --network_train_unet_only --learning_rate 1e-4 `
  --optimizer_type AdamW8bit --lr_scheduler cosine `
  --max_train_steps 1500 --save_every_n_steps 250 --train_batch_size 1 `
  --mixed_precision bf16 --sdpa --gradient_checkpointing `
  --cache_latents --cache_latents_to_disk --cache_text_encoder_outputs `
  --min_snr_gamma 4 --noise_offset 0.02
```

Read the speed over the first 20 steps. A few seconds per step is healthy. Tens of seconds means the run is spilling. In that case, add `--fp8_base`, drop to rank 16, or train at 768 **[Test first]**.

Judge the saved checkpoints on held-out prompts that change outfit, pose, scene and lighting, at LoRA weight 0.8–1.0. The right checkpoint is the last one before the outfit or pose starts sticking.

**Slice 6: decision.** Render the six scenes with the LoRA (face pass with the LoRA on, no adapter) next to the slice 3 bridge images. If the LoRA wins on both sharpness and identity, it becomes the final path. Then repeat slices 4–5 for Pony Realism, trained on Pony Realism v2.2 itself with score tags leading the captions.

### Slice 7 handles two characters without leaving diffusers

Run three variants at 10 seeds each and count identity swaps.

**7a: plain-prompt baseline.** Use the count tag, one BREAK-separated block per character, and adult descriptors in each block.

**7b: masked IP-Adapter.** Use the two precomputed character embeddings with left/right masks, following the docs' two-face pattern.

**7c: compose, then sequential identity passes.**

1. Compose the pair with both LoRAs off or at ~0.3. Add a two-figure OpenPose ControlNet when the bodies overlap.
2. Detect both faces, ordered left to right.
3. Run each face through img2img at ~0.45 with only that character's LoRA loaded.
4. If hair or outfits still swap, widen to a body-region mask at 0.5–0.6 **[Inferred, Test first]**.

### Slices 8–9 are the fallback and the product

**Slice 8: escalation.** Try only what slice 7 failed on:

- **ComfyUI running headless as a separate process**, with either ComfyUI-ppm's Attention Couple or FreeFuse's SDXL workflow for per-character LoRA routing without masks.
- **Qwen-Image-Edit-2511 two-image fusion** through Nunchaku FP4 layer streaming and the lightx2v 4-step Lightning LoRA ([lightx2v](https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning/blob/main/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors)), followed by SDXL refinement and the per-face LoRA pass. First confirm a Nunchaku wheel loads on Windows sm_120 **[Test first]**.
- **Mage-Flow-Edit-Turbo** (4B, 4 steps, Int8 in ComfyUI) is the one to watch. There are no 8 GB or adult-content reports yet ([Mage-Flow-Edit-Turbo](https://huggingface.co/microsoft/Mage-Flow-Edit-Turbo)).

**Slice 9: app wiring.**

1. **At creation:** render the base image. The user approves it and it passes an adult check. Cache its prompt and adapter embeddings, and serve scenes immediately through the bridge.
2. **"Lock this character" job:** dataset, then captions, then training. Queue it for idle time or overnight with the LLM unloaded, and show progress. When it finishes, swap the character to its LoRA.
3. **Per character, store:** base image, seed, prompt, embeddings, dataset and LoRA file.
4. **Scene queue:** batch per character while the model is loaded, and unload before every LLM turn.

## Conclusion

Quality and consistency looked like a trade-off locally only because one mechanism carried both. Once identity lives in LoRA weights, every quality lever (creator samplers, model-upscaled hires, face passes) runs without a reference image fighting it. The fix for "beautiful" and the fix for "consistent" turn out to be the same move. The real constraint on this laptop is therefore not rendering, which the tested SDXL setup already handles in ~30 s, but the one-time work of making a character's identity: generating the dataset and training the LoRA. That turns an image-quality problem into a product-design problem: an instant but softer bridge mode, plus an overnight "lock" that upgrades the character. No open roleplay front-end found does this automatically. The same design turns the adult-only rule into a single review at dataset approval rather than a check repeated on every scene.

Four open items could shorten the plan. AnimeAdapter's weights, a Windows-stable Nunchaku FP4 build, FreeFuse results on Illustrious, and 8 GB numbers for Mage-Flow-Edit-Turbo would each make the training step or the two-character step cheaper. None has evidence yet, so slices 1–7 are built entirely on parts known to run today.
