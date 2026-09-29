# Two consistent original characters in one image (Illustrious / Pony / edit models, 8 GB local)

Scope note: research date 2026-09-22. Items older than 2025 are flagged **[OLDER]**. Where a claim comes only from a search-result snippet (page not fetched or fetch blocked), it is flagged **[snippet]**. Civitai articles were often behind a login or moved to civitai.red (403), so several practitioner write-ups could not be read in full.

Local context (from the project's own M3 spike notes, `C:\Users\user\.claude\projects\D--Kataki\memory\m3-image-spike.md`): on this RTX 5060 Laptop 8 GB box, WAI-Illustrious / Pony Realism via diffusers run ~25-30 s/image at 6.45 GB peak with `enable_model_cpu_offload()`. IP-Adapter-plus (ViT-H) consistency works but spilled to 13.23 GB and ~35 min/image until offload was enabled. Qwen-Image-2.1 (7B, 4-bit) peaked at 10.86 GB, ~2 min/image. So any method that adds a second full model copy or a large encoder resident on the GPU is the main risk.

## 1. Regional prompting / attention masking: which methods work with Illustrious/Pony in 2025-2026?

### Takeaway
Attention Couple is the standard way to keep two characters' features apart on SDXL-family checkpoints (Illustrious and Pony are SDXL). It is available as Forge Couple (Forge Classic/Neo) and as ComfyUI nodes (ComfyUI-ppm, cgem156, ComfyCouple), and 2026 practitioner guides report it pairs well with Illustrious. The Impact-Pack RegionalSampler is the heavier alternative when each region also needs its own LoRA. Diffusers has no maintained SDXL regional-prompting pipeline, so a diffusers-only app would have to port it or use masked IP-Adapter instead (see Q2/Q3).

### Cited Findings
- **Forge Couple** (Haoming02/sd-forge-couple) implements Attention Couple for Forge WebUI and is meant to stop colour bleed and feature mixing between subjects. Modes: Basic (tile per prompt line), Advanced (normalized coordinates plus weights), Mask (hand-drawn masks), and Tile (regional upscaling). "Only SD1 and SDXL are supported", plus newer Anima support. It works with Forge Classic and Forge Neo. A Compatibility Toggle disables it during Hires.Fix. sd-dynamic-prompts may conflict. The README does not document per-region LoRA. — [Forge Couple README](https://github.com/Haoming02/sd-forge-couple/blob/main/README.md)
- A **June 2, 2026** Illustrious/SDXL guide to Forge Couple says Illustrious-based models are "relatively strong with multiple characters and are a good match" for it. Recommended structure:
  - a first "background" line with style, quality, scene and the total count (e.g. `masterpiece, best quality, cafe interior, 2girls`)
  - a `{common}` block for shared outfit or pose
  - one line per character with that character's features and `1girl`/`1boy`
  - BREAK only between entities, never inside one character's tags

  Its main failure mode: "Empty lines are strictly prohibited". An empty line creates a phantom region, which gives single-character or mirrored-twin outputs. Mask mode was reported as less stable than Advanced mode. — [note.com Forge Couple + Illustrious guide](https://note.com/nonb0716/n/n02ce7117ac22?hl=en)
- A Forge Couple issue thread shows a user running it with the WAI-NSFW-illustrious-SDXL checkpoint **[snippet]**. — [sd-forge-couple issue #98](https://github.com/Haoming02/sd-forge-couple/issues/98)
- **ComfyUI-ppm (pamparamm)**: an Attention Couple node for SD1/SDXL/Anima, with Flux marked "Unmaintained". Regions come from cond+mask pairs (`LatentToMaskBB` gives bounding-box masks, e.g. `x=0.5,y=0,w=0.5,h=1` for the right half). Mask values and `ConditioningSetAreaStrength` adjust region strength. It should be connected after other model patches. It works with asagi4's prompt-control (which also offers a prompt-syntax Attention Couple) and BlenderNeko Advanced CLIP. It does not work with smZ Nodes. The pack also includes CLIPNegPip (negative prompt weights). — [ComfyUI-ppm README](https://github.com/pamparamm/ComfyUI-ppm)
- The original laksjdjf/attention-couple-ComfyUI moved to laksjdjf/cgem156-ComfyUI. ComfyCouple and ComfyEnhancedMultiRegion are forks that make setup easier **[snippet]**. — [laksjdjf/attention-couple-ComfyUI](https://github.com/laksjdjf/attention-couple-ComfyUI); [ComfyCouple](https://github.com/Danand/ComfyUI-ComfyCouple); [ComfyEnhancedMultiRegion](https://github.com/neeltheninja/ComfyUI-ComfyEnhancedMultiRegion)
- An Attention Couple workflow write-up warns that masks guide where things go, "but the attention mechanisms may still blend concepts". Tuning tips: lower the base prompt to about 0.75 if masked features are ignored, and balance dominant and weak regions (0.5-0.75 vs about 1.5). The masks must match the latent resolution or you get tensor mismatch errors. No date and no benchmark vs native Conditioning (Set Mask). — [roblaughter attention_couple.md](https://github.com/roblaughter/comfyui-workflows/blob/main/docs/attention_couple.md)
- **Impact-Pack RegionalSampler/RegionalPrompt**: each region can have its own ControlNet, prompt, model, LoRA, sampler, denoise and CFG. The base sampler runs every step and each region's sampler runs inside its mask. It is described as compatible with SDXL and DiT models such as Anima **[snippet]**. — [Impact-Pack regional_sampler tutorial](https://github.com/ltdrdata/ComfyUI-extension-tutorials/blob/Main/ComfyUI-Impact-Pack/tutorial/regional_sampler.md); [Civitai ANIMA couple article](https://civitai.com/articles/32568/anima-crossover-couple-generation-using-regional-sampler)
- Ready-made Illustrious ComfyUI workflows on Civitai:
  - "Eazy Regional Prompter": txt2img + hires fix + face detailer. The second region holds the second character and should start with that character's gender. A regional LoRA is typed as `<lora:NAME:STR> [TRIGGER]` inside that region.
  - "Dynamic Multi-Character Workflow"
  - "Regional Prompt for couple focus V3"

  All **[snippet]**, results not verified. — [Eazy Regional Prompter](https://civitai.com/models/2339837/eazy-regional-prompter-illustrious-workflow-for-comfyui); [Dynamic Multi-Character](https://civitai.com/models/1669611/dynamic-multi-character-workflow-all-in-one-regional-prompts-and-wildcards-comfyui); [Couple focus V3](https://civitai.com/models/1874205/comfyui-workflow-with-regional-prompt-for-couple-focus-v3)
- ComfyUI-EasyIllustrious (regiellis) includes mask-scoped regional prompting with per-region weights and a schedule, built for Illustrious **[snippet]**. — [ComfyUI-EasyIllustrious](https://github.com/regiellis/ComfyUI-EasyIllustrious)
- **Diffusers:** the community Regional Prompting pipeline (hako-mikan) is documented for SD1.x. A Jan 2024 request for SDXL support was still unanswered in May 2025 ("been a year and half"). **[OLDER thread, 2025 follow-up]** — [regional-prompter discussion #317](https://github.com/hako-mikan/sd-webui-regional-prompter/discussions/317); [diffusers community README](https://github.com/huggingface/diffusers/blob/main/examples/community/README.md)

### Inferences
- For a ComfyUI backend, Attention Couple (ComfyUI-ppm) is the lowest-cost method. It patches attention and does not load a second model, so it should fit in the same ~6.5 GB envelope as plain SDXL on this box. That is inferred from how it works, not measured.
- For the current diffusers backend, there is no maintained SDXL regional-prompt pipeline. The options are: port Attention Couple's attention-processor logic (it is small), switch the image backend to ComfyUI or Forge Neo, or use masked IP-Adapter (Q3), which diffusers does support.
- Attention Couple controls where things go and stops colour bleed. It does not by itself make an original character recognizable across scenes. Identity still needs a LoRA or IP-Adapter per character.

### Gaps
- No 2025-2026 benchmark comparing Attention Couple, native `Conditioning (Set Mask)`, and Dense Diffusion on Illustrious, and no success-rate numbers. DenseDiffusion / cutoff-style nodes: no 2025-2026 practitioner reports found.
- No Pony-specific (Pony Realism / photoreal) regional-prompting reports found. Pony is SDXL, so the same nodes should load, but quality is unverified.
- Could not read Civitai article 15657 ("How I generate pictures with several characters (updated)"). It moved to civitai.red and returned 403.

## 2. Two character LoRAs at once: regional LoRA application, bleeding and fixes

### Takeaway
Loading two character LoRAs globally bleeds. Per-region LoRAs are possible three ways: ComfyUI hooks (masked LoRA), the Impact-Pack RegionalSampler, and FreeFuse (automatic token routing, Oct 2025+). Practitioner reports say hooks are slow and buggy. The RegionalSampler works in 2026 but cannot fully remove style bleeding and is slow and manual. FreeFuse is the newest option: it supports SDXL and needs no masks, but there are no Illustrious-specific reports yet.

### Cited Findings
- **ComfyUI hooks** **[OLDER, Dec 6 2024]**:
  - Nodes: Create Hook LoRA, Set CLIP Hooks, Cond Set Props, Cond Pair Set Props Combine, Set Hook Keyframes.
  - The masked-LoRA method gives each character a separate conditioning branch with its own hook and mask, then combines them.
  - "All conditioning must have a mask applied", or unmasked areas come out as beige artifacts.
  - Keyframes cause weight recalculation "hiccups" in sampling speed.
  - No VRAM figures given.

  — [Comfy blog: Masking and Scheduling LoRA and Model Weights](https://blog.comfy.org/p/masking-and-scheduling-lora-and-model-weights)
- User reports on hooks (Flux, Dec 2024 to Apr 2025):
  - One user saw generation time jump from ~30 s to 14+ min (RTX 4070 Ti Super) with blurry results.
  - Another found "both characters used the second hooked lora", with the first ignored and >10 min runs.
  - Workarounds: both regional prompts describe the whole scene plus trigger words, CFG 3.5, denoise 0.85.
  - By April 2025 ComfyUI internals cut one user's run from 8:30 to 2:30.

  All tests were on Flux, not SDXL. — [ComfyUI discussion #5992](https://github.com/comfyanonymous/ComfyUI/discussions/5992)
- **Impact-Pack RegionalSampler with per-region LoRAs**, practitioner article of **Jul 15 2026** (ANIMA base, method said to carry over to SDXL):
  1. Generate a base image with both characters, using the model's own knowledge.
  2. Mask each character in LoadImage.
  3. Give each mask a RegionalPrompt with that character's LoRA.

  Settings:
  - deterministic Euler sampler (not euler_a), 32-33 steps, CFG 5
  - `base_only_steps` 6-16
  - LoRA weight 0.8 for large masks, 1.0 for small ones
  - `overlap_factor` 10, raised to 16-24 if seams appear

  Reported benefits: fewer artifacts and softer seams than inpainting. Limits: it cannot fully remove "style bleeding" (one character's eye shape overwrote the other's), it is "Not suitable for batch generation", it needs manual curation, and it is slower than a plain KSampler. The author mentions FreeFuse as an untested alternative. — [Civitai: ANIMA Crossover Couple Generation using Regional Sampler](https://civitai.com/articles/32568/anima-crossover-couple-generation-using-regional-sampler)
- **FreeFuse** (arXiv 2510.23515, Oct 2025, v2 later): training-free multi-subject LoRA fusion. "FreeFuseAttn" routes each subject's tokens to automatically derived spatial masks at early timesteps, and each LoRA's output is kept inside its region. The user supplies only activation words, with no masks. Supported: Flux.dev, SDXL, Z-Image-turbo, FLUX.2-klein 4B/9B, LTX2. It ships `freefuse_comfyui` nodes and an `sdxl_freefuse_complete.json` workflow. Quantization is optional to save VRAM. No overhead numbers and no Illustrious examples. — [FreeFuse GitHub](https://github.com/yaoliliu/FreeFuse); [arXiv 2510.23515](https://arxiv.org/html/2510.23515v2); [SDXL workflow json](https://github.com/yaoliliu/FreeFuse/blob/master/freefuse_comfyui/workflows/sdxl_freefuse_complete.json)
- The Eazy Regional Prompter (Illustrious ComfyUI workflow) supports regional LoRAs through `<lora:...>` syntax inside a region's prompt **[snippet]**. — [Civitai Eazy Regional Prompter](https://civitai.com/models/2339837/eazy-regional-prompter-illustrious-workflow-for-comfyui)

### Inferences
- In ComfyUI, each masked LoRA or RegionalSampler branch applies a different LoRA patch to the model per region. On an 8 GB card that likely means repeated patching and/or extra model memory. The 14-minute Flux reports suggest the cost can be large, but SDXL is ~5x smaller than Flux. Treat it as unmeasured here and benchmark before adopting.
- A lower-cost pattern for this app: generate the composition with no character LoRAs (or at low weight), then apply each character's LoRA only in its own inpaint/detailer pass (Q3). Only one LoRA is active per pass, so nothing bleeds between LoRAs.
- FreeFuse is the method most worth testing, because it removes the manual mask step, which matters for an automated roleplay app. Its SDXL workflow should load Illustrious/Pony checkpoints, since they are SDXL-architecture. That is unverified.

### Gaps
- No quantitative bleed/success rates for any regional-LoRA method on Illustrious or Pony.
- No VRAM or speed data for hooks, RegionalSampler or FreeFuse on SDXL at 8 GB.
- Diffusers has no built-in per-region LoRA. PEFT adapters are global, and no maintained diffusers regional-LoRA implementation was found.

## 3. Two-pass approaches: composition first, then per-character inpaint/detail or composite and harmonize

### Takeaway
The most reliable path practitioners use is two passes: (1) lay out two figures (OpenPose/depth ControlNet or regional prompt), then (2) re-render each character inside its own mask with only that character's LoRA or reference. The 2026 RegionalSampler article is a latent-space version of this. In diffusers, masked IP-Adapter is documented and can put two different face references into two regions in one pass, which fits this project's existing IP-Adapter lane directly.

### Cited Findings
- **Diffusers IP-Adapter masking** (official docs): "Binary masking enables assigning an IP-Adapter image to a specific area of the output image". Each reference image gets its own binary mask, preprocessed with `IPAdapterMaskProcessor` (pass the output height/width). The docs example:
  - loads `ip-adapter-plus-face_sdxl_vit-h`
  - calls `set_ip_adapter_scale([[0.7, 0.7]])`
  - passes `ip_adapter_image=[[face1, face2]]` and `cross_attention_kwargs={"ip_adapter_masks": masks}` with prompt "2 girls"

  The docs show an image with masks next to one without. `enable_model_cpu_offload()` must be called **after** `load_ip_adapter()`, or the image encoder gets offloaded and errors. Precomputed image embeddings (`prepare_ip_adapter_image_embeds`) can be saved and reused, which removes the need for the image encoder at generation time (`image_encoder_folder=None`). — [Diffusers IP-Adapter guide](https://huggingface.co/docs/diffusers/main/en/using-diffusers/ip_adapter)
- The same docs show IP-Adapter combined with ControlNet for structure (depth/pose) and with InstantStyle layer scaling. The layer scaling can limit IP-Adapter to layout blocks (`down block_2`) or style blocks (`up block_0`), which reduces style/palette carry-over from the reference. — [Diffusers IP-Adapter guide](https://huggingface.co/docs/diffusers/main/en/using-diffusers/ip_adapter)
- RegionalSampler two-pass (Jul 2026): generate the pair first, mask each, re-sample each region with its own LoRA. It gives fewer artifacts than traditional inpainting, but style bleed remains and it is slow. — [Civitai ANIMA RegionalSampler article](https://civitai.com/articles/32568/anima-crossover-couple-generation-using-regional-sampler)
- **aDetailer (A1111/Forge)** can run a different prompt and LoRA on each detected face in order using `[SEP]`, e.g. `Bobby <lora:bobby:1> [SEP] Tracy <lora:tracy:1>`, with "keep k largest" limiting it to the main faces **[snippet; thread date unknown]**. Impact-Pack FaceDetailer has no native `[SEP]`. Users asked for per-face-order prompts in an early Impact-Pack issue **[OLDER, snippet]**. — [adetailer discussion #533](https://github.com/Bing-su/adetailer/discussions/533); [Impact-Pack issue #148](https://github.com/ltdrdata/ComfyUI-Impact-Pack/issues/148)
- A guide on working with multiple LoRAs describes two routes: generate at low LoRA weights, pick a composition, then inpaint each character one at a time with its LoRA; or use ControlNet (depth) to lock a complex overlapping composition first **[OLDER, pre-2025 Scribd doc, snippet]**. — [Scribd: Beginner guide to work with multiple LoRAs](https://www.scribd.com/document/694090409/Beginner-guide-to-work-with-multiple-Loras-for-complex-composition)
- The Eazy Regional Prompter workflow bundles regional txt2img, hires fix and face detailer, i.e. the regional-then-detail two-pass pattern **[snippet]**. — [Civitai Eazy Regional Prompter](https://civitai.com/models/2339837/eazy-regional-prompter-illustrious-workflow-for-comfyui)

### Inferences
- Masked IP-Adapter is the most promising first slice for this project. The project already runs IP-Adapter-plus with WAI/Pony at 6.45 GB with offload, and adding a second reference image to the same adapter adds no second encoder or model. Expected cost is close to the measured ~25-54 s/image. This is inferred from the local spike numbers, not measured for two references.
- For a school-hallway interaction ("prince pushes bully against lockers"), overlapping bodies are where masked methods break down. Lock the pose first (OpenPose ControlNet for two figures), then use masked IP-Adapter or one per-character detail pass. Each extra ControlNet on SDXL adds roughly 2.5 GB fp16 of weights, so it must go through offload to stay under 8 GB. The weight figure is from general knowledge of SDXL ControlNet sizes and is unsourced here.
- Composite-then-harmonize (cut out each character, place on a background, low-denoise img2img) fits the project's existing transparent-sprite lane (Qwen-Image-2.1 native RGBA plus background plate). No 2025-2026 practitioner write-up with results was found for it.

### Gaps
- No 2025-2026 source measuring two-face masked IP-Adapter reliability on Illustrious/Pony (identity swap rate, bleed).
- No firsthand 2025-2026 Reddit threads could be retrieved. Search returned none on-topic for OpenPose + per-character inpaint with Illustrious.
- No source on an Illustrious-specific OpenPose ControlNet's quality or VRAM. One search result mentioned an anime/Illustrious-optimized OpenPose ControlNet but without a checkable link.

## 4. Edit / multi-reference models: can they place two referenced characters together, and at what cost on 8 GB?

### Takeaway
Qwen-Image-Edit-2509/2511 is explicitly built for "person + person" multi-image fusion, and 2511 specifically improved multi-person group shots. It is a 20B model, though: even 4-bit Nunchaku or GGUF Q4 (~13 GB file) will not fit 8 GB without CPU offload, so expect minutes per image on this box. FLUX.2 Klein 4B is the only multi-reference edit model near the 8 GB line (ComfyUI docs: 8.4 GB for the 4-step distilled model), so it would still spill slightly. OmniGen2 needs ~17 GB natively. No usable data was found for DreamO.

### Cited Findings
- **Qwen-Image-Edit-2509**: multi-image editing trained through image concatenation. It supports "person + person", "person + product" and "person + scene", with best results at 1-3 input images, and improved facial-identity preservation. — [Qwen-Image-Edit-2509 README](https://huggingface.co/Qwen/Qwen-Image-Edit-2509/blob/main/README.md)
- **Qwen-Image-Edit-2511** (version tag = late 2025): improved multi-person consistency, "high-fidelity fusion of two separate person images into a coherent group shot", improved character consistency, and built-in popular-LoRA effects. — [Qwen blog: Qwen-Image-Edit-2511](https://qwen.ai/blog?id=qwen-image-edit-2511)
- Model card details: 20B parameters, the example passes two images (`"image": [image1, image2]`) with a positional prompt ("...on the left, ...on the right, facing each other..."), and recommended settings are 40 steps, true CFG 4.0, guidance 1.0. — [HF Qwen-Image-Edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)
- ComfyUI native 2511 workflow: bf16 diffusion model, `qwen_2.5_vl_7b_fp8_scaled` text encoder, optional 4-step Lightning LoRA, and multi-image input through separate LoadImage nodes. No VRAM figure given. — [ComfyUI docs: Qwen-Image-Edit-2511](https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit-2511)
- Prompting guidance for multi-image: name which element comes from which image, e.g. "place the person from the first image on the left and the person from the second image on the right" **[snippet]**. — [Scenario KB: Advanced Editing with Qwen Models](https://help.scenario.com/articles/5117943220-advanced-editing-with-qwen-models)
- Speed (May 30 2026, **RTX 3090 24 GB**, 4-step Lightning): bf16 34 s vs Nunchaku `qwen_image_edit_2511` int4 r128 19 s in Forge Neo. An fp4 Nunchaku variant exists for RTX 50-series. Nunchaku claims operation "as little as 4GB VRAM" with CPU offload, but no VRAM was measured. — [DCAI: Qwen-Image-Edit 2511 + Nunchaku in Forge Neo](https://www.digitalcreativeai.net/en/post/how-speed-up-qwen-image-edit-2511-nunchaku-forge-neo)
- VRAM table (Jan 2026): FP8 model ~15 GB file ("6GB+" VRAM claimed, presumably with offload), GGUF Q4_K_M 13.1 GB, NF4 ~10 GB, and a stated minimum of RTX 3060 12 GB + 32 GB RAM. There is no 8 GB spec. — [lilting.ch: Qwen-Image-Edit-2511 local VRAM](https://lilting.ch/en/articles/qwen-image-edit-2511-local-specs). *Internal inconsistency:* a 15 GB FP8 file cannot sit in 6 GB of VRAM without offload.
- **FLUX.2 Klein** (ComfyUI docs):

  | Variant | Steps | Time | VRAM |
  |---|---|---|---|
  | 4B distilled | 4 | ~1.2 s | 8.4 GB |
  | 4B base | standard | ~17 s | 9.2 GB |

  GPU unstated. Text encoder: Qwen3-4B (4B) / Qwen3-8B fp8 (9B). Capabilities include "multi-reference composition". — [ComfyUI docs: FLUX.2 Klein](https://docs.comfy.org/tutorials/flux/flux-2-klein)
- FLUX.2 supports up to 10 reference images. On 8 GB, limit to 2-3 references, use FP8, lower the resolution, and expect slower runs **[secondary blog, snippet]**. — [Promptus: FLUX2 multi-image reference](https://www.promptus.ai/blog/flux-context-guide-multi-image-ai-generation); [HackerNoon: FLUX.2 Klein 4B on 8GB](https://hackernoon.com/the-8gb-vram-image-model-that-feels-instant-meet-flux2-klein-4b)
- FreeFuse (multi-character LoRA routing) supports FLUX.2-klein 4B/9B, so Klein can take per-character LoRAs as well as reference images. — [FreeFuse GitHub](https://github.com/yaoliliu/FreeFuse)
- **OmniGen2** (June 2025): in-context generation that combines "humans, reference objects, and scenes". It needs ~17 GB natively (RTX 3090 class). Model CPU offload cuts VRAM by nearly 50% with small speed impact. Sequential offload goes below 3 GB but is much slower. DFloat11 brings it from 18 to 14 GB. — [OmniGen2 GitHub](https://github.com/VectorSpaceLab/OmniGen2); [ComfyUI Wiki OmniGen2 news](https://comfyui-wiki.com/en/news/2025-06-24-omnigen2-unified-image-generation); [OmniGen2 issue #36 DFloat11](https://github.com/VectorSpaceLab/OmniGen2/issues/36)
- Local measurement on this machine: Qwen-Image-2.1 (7B, 4-bit, diffusers, 1024 px, 24 steps) took ~2 min/image at 10.86 GB peak (spilling). Feeding a base image back kept the same face across new scenes. — project spike notes (`memory/m3-image-spike.md`)

### Inferences
- On 8 GB, Qwen-Image-Edit-2511 two-person fusion is feasible only with offload (Nunchaku fp4 on Blackwell, or GGUF Q4 + offload) plus Lightning 4-step. Given the 7B Qwen-Image-2.1 already spilled at 4-bit, the 20B edit model will certainly offload, and a realistic guess is minutes per image, not seconds. That is an estimate and needs benchmarking.
- FLUX.2 Klein 4B distilled is the best candidate for a fast multi-reference pass on this box (8.4 GB reported, so it slightly spills without offload). Two references are within the suggested 2-3 limit for 8 GB.
- A plausible hybrid: make each character's canonical sheet with WAI/Pony (+LoRA or IP-Adapter), then use an edit model only to stage both sheets together in a scene, or use the edit model's output as a pose/composition base for an SDXL regional/inpaint refine pass.
- Adult framing: prompts should keep describing both characters as adults ("young man, adult, early 20s"), as the local spike notes already do.

### Gaps
- **NSFW capability** of Qwen-Image-Edit-2511, FLUX.2 Klein and OmniGen2 for romance/explicit scenes: no sources found. It is typically limited without community LoRAs, but that is unverified.
- **DreamO**: no 2025-2026 data found on two-subject reliability or VRAM.
- No measured 8 GB (or RTX 50-series laptop) numbers for Qwen-Image-Edit-2511 multi-image or for Klein multi-reference. No practitioner success rates for keeping two *original* (non-celebrity, anime-styled) characters distinct in edit models.
- Whether Qwen-Image-2.1 (already installed locally) accepts multiple reference images, as the 2509/2511 edit models do, was not researched here.

## 5. Illustrious/Danbooru prompt conventions for multiple characters and native handling

### Takeaway
Illustrious (and NoobAI/Pony, which share Danbooru tagging) understands count tags like `2boys` / `1boy, 1girl` and can often render two figures natively. With plain prompting, though, attribute bleed (hair colour, eye colour, outfits swapping) is common, and at 3+ characters it gets much worse. Community practice is: count tag in a shared/global line, one character block per region, BREAK only between characters, and strong negatives. Plain prompting is "not 100%" and depends on the checkpoint.

### Cited Findings
- 2026 Forge Couple + Illustrious guide conventions:
  - put the total count (`2girls`) in the background/common line and `1girl`/`1boy` in each character line
  - use comma-separated tags, no periods
  - parentheses only for weighting
  - BREAK only between separate entities
  - keep related tags next to each other
  - Illustrious is "relatively strong with multiple characters"

  — [note.com guide (Jun 2 2026)](https://note.com/nonb0716/n/n02ce7117ac22?hl=en)
- Multiple-character syntax for Pony/Illustrious/NoobAI "is not 100% working trick and highly depends on model's capabilities and your luck" **[snippet]**. — [SeaArt: Multiple Character Syntax for Illustrious/Pony/NoobAI](https://www.seaart.ai/articleDetail/d28i2gle878c73dnois0)
- Advice to reinforce the count and gender (`2boys`, `male focus`) with negatives such as `1girl`, `feminine`. Also: at three or more characters even advanced models bleed noticeably and "SDXL regional prompting breaks down quickly" **[snippet]**. — [PixAI: Multi-Character LoRA Generation guide](https://blog.pixai.art/en/multi-character-lora-generation-guide/)
- Illustrious XL 2.0 guidance: include count tags (`1girl`, `2boys`) plus character names where applicable **[snippet]**. — [SeaArt: Ultimate Guide Illustrious XL 2.0](https://www.seaart.ai/articleDetail/cvdosb5e878c73c7ipig)
- Local finding on this project: of the three checkpoints tested, WAI-Illustrious v17 showed the "least bleed". Nova Anime let the pale prince pick up pink in colourful scenes. Pony Realism needs `score_9, score_8_up...` + `source_realistic`. — project spike notes (`memory/m3-image-spike.md`)
- A 2026 Illustrious/NoobAI guide was checked and had **no** multi-character content. — [ArtificialGuyBR Illustrious & NoobAI guide (updated Jul 27 2026)](https://artificialguy.com/blog/illustrious-noobai-anime-guide/)

### Inferences
- For the "blonde prince + dark-haired bully" example, plain prompting (`2boys, school hallway, ... BREAK blonde hair, blue eyes, white uniform ... BREAK black hair, red eyes, delinquent, open jacket ...`) will sometimes work on WAI, but hair and eye colour swaps are the expected failure. Strong contrasts (blonde vs black hair, white vs black outfit) help regional methods separate the two. Treat plain prompting as the baseline to beat, not the product path.
- For adult romance scenes, keep adult descriptors (`adult`, `mature male`, age in the 20s) in each character's own block, not only in the global line, so that an adult descriptor applies to each character's region, not just the image as a whole.

### Gaps
- No quantitative data (e.g. % of images with correct attribute binding) for native Illustrious two-character prompting. No first-party Illustrious (OnomaAI) documentation on multi-character capability was found.
- Most prompt-convention sources are SeaArt/PixAI blogs retrieved only as snippets, not firsthand posts with shown results.
