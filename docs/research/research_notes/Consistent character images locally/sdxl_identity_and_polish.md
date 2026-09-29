# SDXL / Illustrious / Pony: keeping identity without losing quality, plus the polish pipeline

Scope: WAI-Illustrious-SDXL v17 (anime) and Pony Realism v2.2 (photoreal), ComfyUI and diffusers, RTX 5060 Laptop 8 GB. Already tested locally, not re-derived here: ip-adapter-plus_sdxl_vit-h at 0.4–0.6, applied to the whole image for all steps, keeps identity but softens faces and bleeds the reference palette; a pale reference gave magenta/halftone artifacts; a 1.3× hires img2img pass at denoise 0.35 (DPM++ 2M Karras) sharpens (~30 s, 6 GB); a second diffusers pipeline made with from_pipe on an offloaded pipe went over 8 GB.

Date note: Several key artifacts are **older than 2025** and are flagged: Pony Realism v2.2 (Oct 2024), the h94 IP-Adapter / FaceID weights (2023–24), and PuLID (NeurIPS 2024). Everything else is dated 2025–2026 or has no stated date.

---

## 1. IP-Adapter done right: settings that avoid soft faces and palette bleed, and anime-specific adapters

### Takeaway
Full-strength, all-block, all-step IP-Adapter is exactly the setup that produces soft faces and palette bleed. The documented fixes are: (a) lower weight, and in diffusers apply it block by block (InstantStyle), keeping the reference out of the "style" block (up block_0), which carries colour and texture; (b) mask it to the face or character region; (c) split the work into a face-crop adapter at low scale plus a general adapter. The only anime-trained SDXL IP-Adapter found (kataragi Noob IPA) is openly experimental. cubiq's ComfyUI node has been in maintenance-only mode since April 2025, and no successor has been named.

### Cited Findings
- cubiq/ComfyUI_IPAdapter_plus has been **"maintenance only" since 14 Apr 2025**. The author says he no longer uses ComfyUI as his main tool. Crucial PRs may still be merged, but no consistent development is planned, and no successor repo is named. — [cubiq/ComfyUI_IPAdapter_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus)
- The cubiq README advises lowering `weight` (to about 0.8 or below) and raising step count for better results. It says that changing the **weight type** in IPAdapter Advanced can "increase adherence to the prompt". — [cubiq README](https://github.com/cubiq/ComfyUI_IPAdapter_plus)
- According to cubiq's README, the plus-face models are for portraits but "not necessarily better" than full-face. FaceID Plus **v2** is the current FaceID variant; v1 is deprecated. — [cubiq README](https://github.com/cubiq/ComfyUI_IPAdapter_plus)
- The "Style Transfer (SDXL)" weight type copies look and feel (colours, texture, lighting). Practitioners typically drop weight from the 1.0 default to about 0.8, and to 0.3–0.5 to keep the text prompt in charge. — [Runflow IPAdapter guide 2026](https://www.runflow.io/blog/comfyui-ipadapter-guide) (tutorial site; treat as secondary)
- **diffusers: block-wise scale (InstantStyle).** Per the diffusers docs, down `block_2` is where IP-Adapter injects **layout**, and up `block_0` is where **style** (colour, texture, overall feel) is injected. Layers left out of the dict are set to 0. Exact API:
  `pipeline.set_ip_adapter_scale({"down": {"block_2": [0.0, 1.0]}, "up": {"block_0": [0.0, 1.0, 0.0]}})`. The docs also say that inserting IP-Adapter in *all* layers "tends to generate images that focus more on the image prompt and may reduce the diversity". — [diffusers IP-Adapter docs (v0.40)](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)
- **diffusers: masking.** `IPAdapterMaskProcessor().preprocess([mask], height=H, width=W)` is passed via `cross_attention_kwargs={"ip_adapter_masks": masks}`, and it limits a reference image to a region. The docs' example uses `ip-adapter-plus-face_sdxl_vit-h` at 0.7 per masked face. — [diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)
- **diffusers: combining face and general adapters.** The documented pattern loads `["ip-adapter-plus_sdxl_vit-h.safetensors", "ip-adapter-plus-face_sdxl_vit-h.safetensors"]` with `set_ip_adapter_scale([0.7, 0.3])`, with a style-image list feeding the first and a face image feeding the second. — [diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)
- **diffusers: FaceID / FaceID Plus v2** need InsightFace (`buffalo_l`) face embeddings passed as `ip_adapter_image_embeds`. Plus/Plus v2 also need CLIP embeds set on `image_projection_layers[0].clip_embeds`, with `.shortcut = True` for Plus v2. The docs recommend DDIM or Euler schedulers for face models. — [diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)
- **diffusers: precomputed embeds.** `prepare_ip_adapter_image_embeds(...)` can be saved with `torch.save` and reloaded with `image_encoder_folder=None`, so the CLIP image encoder never has to be in VRAM at generation time. The docs note these embeds can also come from ComfyUI. — [diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)
- **diffusers offload ordering.** `enable_model_cpu_offload()` must be called **after** `load_ip_adapter()`. Otherwise the image encoder is offloaded and the call errors. — [diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)
- **Anime-specific IP-Adapter: kataragi/Noob_ipadapter.** Files: `ip_adapter_Noobtest_800000.bin` (trained on NoobAI 1.1) and `ip_adapter_test_400000.bin` (AnimagineXL 3.1). Encoder: CLIP-ViT-H. Training was 3 stages × 400k steps, 50k–100k images, 1024 px, ~408 h on one A6000. The author's own caveat: "Training feels insufficient; usability may be poor". Weight and end step must be tuned per image, and high weights cause artifacts. It is documented for the A1111/Forge ControlNet IP-Adapter slot; ComfyUI/diffusers compatibility is not stated. Licence CreativeML OpenRAIL-M. — [kataragi/Noob_ipadapter](https://huggingface.co/kataragi/Noob_ipadapter)
- The Civitai ControlNetXL collection has listed "kataragi noob-ipa" and "ipa" since **13 Jan 2025**. — [Civitai CNXL collection API](https://civitai.com/api/v1/models/136070)
- **Measured comparison on anime (preprint, 17 May 2026, "AnimeAdapter").** On anime characters, CLIP-I (appearance preservation, higher is better): IP-Adapter 0.791, IP-Adapter Plus 0.815, AnimeAdapter 0.860. LPIPS (lower is better): 0.503 / 0.434 / 0.431. The authors say IP-Adapter "often fail[s] to preserve fine-grained appearance details". Code and weights are promised only "upon acceptance", and the base model is described only as SD anime variants (SDXL/Illustrious not confirmed). — [arXiv 2605.20237](https://arxiv.org/html/2605.20237v1)

### Inferences
- **Palette bleed = the style block.** In diffusers, the closest equivalent to cubiq's weight types is the per-block scale dict. To keep character or composition without copying the reference's palette, set up `block_0` low or zero and keep down `block_2` (layout), e.g. `{"down": {"block_2": [0.0, 0.6]}, "up": {"block_0": [0.0, 0.2, 0.0]}}`. This follows from the documented block roles but I found no before/after test of it on Illustrious or Pony; it needs a local A/B.
- **Soft faces.** Likely causes are (i) IP-Adapter active in late steps, where fine detail forms, and (ii) the whole image being conditioned. diffusers has no built-in start/end-step parameter for IP-Adapter. The usual workaround is a `callback_on_step_end` that calls `set_ip_adapter_scale(0)` after about 60–70% of the steps, which mimics cubiq's `end_at`. The other fix is to run the hires/detail pass **without** IP-Adapter, so the sharpening pass is not pulled back toward the soft reference. Both are unverified here and need a local test.
- **Pale reference → magenta/halftone.** CLIP-ViT-H embeds global colour statistics, and low-contrast references push the style tokens toward odd colours. Cheap mitigations: auto-levels/contrast-normalise the reference before encoding; crop tightly to the face or character; lower up `block_0`. cubiq's node also has a "negative image" / noise input for this, but that is **unverified in this session** (from prior knowledge of the node, not the fetched README text).
- From prior knowledge, **not re-verified in this session**: cubiq's weight-type list includes linear, ease in/out/in-out, reverse in-out, weak/strong input/output/middle, style transfer, composition, strong style transfer, style and composition, style transfer precise, composition precise; plus combine-embeds modes concat/add/subtract/average/norm average. Check the node before citing.
- For anime OCs specifically, an identity-by-image adapter will probably never beat a character LoRA trained on 15–30 generated images of the OC. The IP-Adapter numbers above (CLIP-I about 0.8) support treating IP-Adapter as the bootstrap for generating a LoRA dataset, not the final identity mechanism.

### Gaps
- No 2025–2026 firsthand Reddit or Civitai comparisons of cubiq weight types on Illustrious or Pony were retrieved (search budget).
- `r3gm/ip-adapter-anime` on HF surfaced in search but was not examined.
- No Illustrious-specific (as opposed to NoobAI) IP-Adapter was found. NoobAI is Illustrious-derived, so the Noob IPA *may* transfer to WAI-Illustrious, but that is untested.

---

## 2. Other identity methods for SDXL (InstantID, PuLID-SDXL, PhotoMaker V2, reference-only, InstantCharacter) — anime vs photoreal, and quality cost

### Takeaway
The face-ID methods (InstantID, PuLID, FaceID) are built on real-face embeddings (ArcFace/InsightFace, EVA-CLIP). They suit **Pony Realism** and are weak or untested on anime. InstantCharacter is **FLUX-only and needs 24–48 GB**, so it is out for 8 GB. For WAI-Illustrious there is no mature zero-shot identity method; the practical answer is IP-Adapter (tuned as in §1) to bootstrap, then a character LoRA.

### Cited Findings
- **PuLID** (NeurIPS 2024, older): **PuLID-v1.1 SDXL** is the latest SDXL model, claiming "better compatibility, editability, facial naturalness, and similarity" than v1. The README gives no SDXL VRAM figure; PuLID-FLUX runs on 16 GB (12 GB in local demos). It uses EVA-CLIP. Implementations exist for ComfyUI (native and diffusers-based), SD.Next and the WebUI ControlNet. The README shows only photoreal examples. — [ToTheBeginning/PuLID](https://github.com/ToTheBeginning/PuLID)
- A 2026 comparison guide describes PuLID as ArcFace plus CLIP-Vision, trained to penalise style leakage so it "transfers face only". It says PuLID handles diverse outputs "including anime stylisations" better, is "the leanest computationally", and fits 12 GB without swapping. The same guide says **InstantID** renders 5 face keypoints into a KPS image for a dedicated ControlNet, which **locks pose** and makes it the heaviest option (IP-Adapter path plus ControlNet). — [aiofm.info PuLID vs InstantID vs FaceID (2026)](https://aiofm.info/en/guides/pulid-vs-instantid-vs-faceid) (secondary guide site, not firsthand; the anime claim is unsubstantiated)
- **InstantCharacter (Tencent, 2025)**: supports **FLUX.1 only**. It recommends 48 GB VRAM, optimised for 24 GB, and users on 12 GB cards report CUDA OOM. — [Tencent/InstantCharacter issue #3](https://github.com/Tencent/InstantCharacter/issues/3); [AI Sharing Circle summary](https://aisharenet.com/en/instantcharacter/)
- FaceID variants in diffusers need `insightface` `FaceAnalysis(name="buffalo_l")` to detect a face and produce `normed_embedding`. — [diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)

### Inferences
- **Anime:** InsightFace detectors are trained on real faces, so anime faces are often not detected, and then FaceID, InstantID and PuLID have nothing to embed. This is the core reason these methods are "photoreal tools". The claim that PuLID handles anime stylisation refers to *stylised output from a real reference face*, not to an anime reference. Inference, not tested.
- **Pony Realism (photoreal):** PuLID-v1.1-SDXL or FaceID Plus v2 is the better-grounded choice. InstantID's KPS ControlNet forces the reference's head pose, which works against the "specific pose / looking at viewer" goal and costs an extra ControlNet in VRAM.
- The adult-content constraint is unaffected by the method choice. Reference faces should be generated adult OCs; photoreal ID methods on real people's photos raise consent issues and are out of scope.

### Gaps
- PhotoMaker V2 and "reference-only" / ControlNet-reference: no 2025–2026 sources retrieved.
- No VRAM measurement for PuLID-SDXL or InstantID-SDXL on 8 GB was found.
- No firsthand anime test of PuLID-v1.1 was found.

---

## 3. The polish pipeline: sampler, CFG, steps, hires fix, detailers, upscalers, tags

### Takeaway
Follow each creator's own recipe. WAI v17 (Apr 2026): Euler a, 15–30 steps, CFG 5–7, ≥1024 px, 1.5× hires with R-ESRGAN 4x+ Anime6B at denoise 0.35–0.5. Pony Realism v2.2 (Oct 2024, older): Euler a or DPM2 a, 30+ steps, CFG 6–7, clip skip 2, score tags. The creator **explicitly discourages DPM++ 2M Karras**, which is the sampler used in the local hires test. The Civitai look usually comes from hires fix plus a face detailer pass; I found no documented Illustrious-specific detailer settings.

### Cited Findings
- **WAI-illustrious-SDXL v17.0, published 23 Apr 2026** (v16.0 on 18 Dec 2025, v15.0 on 31 Aug 2025). Creator settings: sampler **Euler a**; **15–30 steps**; **CFG 5–7**; resolution at least 1024×1024 (example 1024×1344). Positive: `masterpiece,best quality,amazing quality,`. Negative: `bad quality,worst quality,worst detail,sketch,censor,`. Hires: **R-ESRGAN 4x+ Anime6B, 1.5×, denoise 0.35–0.5, 20 hires steps**. VAE is baked in. Scheduler and clip skip are not specified. The creator recommends **forge-neo**. — [Civitai API, model 827184](https://civitai.com/api/v1/models/827184)
- The WAI Civitai page now redirects mature content to civitai.red. — [civitai.com/models/827184](https://civitai.com/models/827184/wai-illustrious-sdxl)
- **Pony Realism v2.2, published 2 Oct 2024 (older than 2025).** Sampler: **Euler A** or **DPM2 a** ("Best for detail"). Explicitly **avoid "DPM++ 2M Karras"**. Steps 30+; CFG 6–7; **clip skip 2**; resolution above 1024. Positive `score_9, score_8_up, score_7_up, BREAK`; negative `score_4, score_5, score_6`. Danbooru-style tags; keep prompt weights ≤1.5; use "female/male" rather than "woman/man". — [Civitai, Pony Realism](https://civitai.com/models/372465/pony-realism)
- Hires fix for Pony Realism reported as: at least 5 hires steps, at least 1.5×, **4x-UltraSharp**, **denoise 0.30**. — search-result summary drawn from [HF mirror PonyRealism-v2.2MainVAE](https://huggingface.co/TheImposterImposters/PonyRealism-v2.2MainVAE) / [ponyrealism.com](https://ponyrealism.com/) (not verified by direct fetch; mirror of the model card)
- A **v2.3 "ULTRA"** of Pony Realism exists on Tensor.Art. — [Tensor.Art Pony Realism v2.3](https://www.tensor.art/models/894416222643344525/Pony-Realism-v2.3-2.3-ULTRA) (not examined)
- diffusers docs recommend DDIM or Euler schedulers when using IP-Adapter face models. — [diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)

### Inferences
- The local hires test (1.3×, denoise 0.35) sits at the low end of both creators' ranges. Moving to **1.5×** with a model upscaler (Anime6B for WAI, UltraSharp for Pony) before the img2img pass should add detail. Also change the hires sampler to **Euler a** for both models (or DPM2 a for Pony), since the Pony creator explicitly flags DPM++ 2M Karras.
- In diffusers: Euler a = `EulerAncestralDiscreteScheduler`. Clip skip 2 for Pony = `clip_skip=2` in the SDXL pipeline call (a diffusers pipeline argument; not verified in this session). Upscaler .pth models (Anime6B, UltraSharp) are not diffusers models. They run via `spandrel` (what ComfyUI uses) or Real-ESRGAN, then feed the img2img pipeline; a 4× model on a 1024 image makes 4096 px, which is resized down to 1.5×.
- **Face detailer (ADetailer / Impact FaceDetailer)** is the other half of the Civitai look. Mechanism: detect face bbox (YOLO face model) → crop with padding → upscale the crop to about 1024 px → img2img/inpaint at moderate denoise → paste back with feathering. Starting values from general community practice, **not sourced in this session**: denoise about 0.35–0.5, crop padding/dilation of a few tens of px, feather about 5–10 px. In diffusers this is a hand-rolled loop reusing the same img2img/inpaint components (no Impact Pack equivalent).
- **CFG rescale** matters mainly for v-pred models (NoobAI v-pred). WAI and Pony Realism are eps models, so it is likely unnecessary. Unverified.

### Gaps
- No creator-documented FaceDetailer/ADetailer settings for WAI or Pony Realism were found; the Impact Pack README was not fetched.
- No 2025–2026 upscaler comparisons (4x-AnimeSharp vs Anime6B vs UltraSharp) were retrieved.
- No sources were found on Ultimate SD Upscale / tiled settings or on negative embeddings for these two models.
- WAI's scheduler and clip skip are unspecified by the creator.

---

## 4. ControlNet for pose and gaze on Illustrious/Pony, and VRAM cost

### Takeaway
There are Illustrious- and NoobAI-specific ControlNets (Jan 2025): windsingai pose, the anytest-v4 and openpose-v2_1 pair, and Eugeoter's NoobAI set. xinsir union-promax covers pose, depth and tile in one file but is general SDXL, and its training is paused. Each SDXL ControlNet is about **2.3–2.5 GB fp16**, which on 8 GB means CPU offload is required alongside the ~5 GB UNet.

### Cited Findings
- **Illustrious-specific:** windsingai **pose**, **tile**, **tile-10w**, published 12 Jan 2025. — [Civitai CNXL collection API](https://civitai.com/api/v1/models/136070)
- **NoobAI-specific (Eugeoter):** canny, depth, lineart-anime, lineart-real, mangaline, normal, scribble-pidi/hed, softedge-hed, tile, published 13 Jan 2025. — [Civitai CNXL collection API](https://civitai.com/api/v1/models/136070)
- **2vXpSwA7 anytest-v4** and **openpose-v2_1**, published 18 Jan 2025, **2.32 GB fp16 each**. — [Civitai CNXL collection API](https://civitai.com/api/v1/models/136070)
- **xinsir controlnet-union-sdxl-1.0 / ProMax:** one model covering openpose, depth, canny, lineart and **anime lineart**, MLSD, scribble, HED, softedge, TEED, segmentation, normal, **tile** (deblur, variation, super-resolution), inpaint and outpaint. About 1B params F16. It is stated compatible with other SDXL models (BluePencilXL, CounterfeitXL); Pony and Illustrious are not mentioned. The creator says **training is paused** for lack of GPU. — [xinsir/controlnet-union-sdxl-1.0](https://huggingface.co/xinsir/controlnet-union-sdxl-1.0)
- diffusers supports combining ControlNet (depth, pose, etc.) with IP-Adapter in one pipeline. — [diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)

### Inferences
- **"Looking away" fix, cheapest first:** (1) prompt tags `looking at viewer, facing viewer` plus negative `looking away, looking to the side` (Danbooru tags both models understand); (2) an openpose ControlNet with face keypoints enabled, since OpenPose face and eye points steer gaze; (3) depth from a reference pose. Use the Illustrious-native windsingai pose or openpose-v2_1 for WAI. Use xinsir union-promax (openpose mode) for Pony Realism, since the Illustrious ones are tuned for anime.
- **Union tile mode as a quality tool:** the same union file does tile or super-resolution, so one 2.5 GB download can serve both pose control and a tile-guided hires pass. That avoids a second ControlNet.
- **VRAM:** SDXL UNet fp16 is about 5 GB, plus a ControlNet of about 2.3–2.5 GB, plus the VAE decode. That exceeds 8 GB unless model CPU offload is on. Expect a slower first step while modules move. Apply ControlNet only for the base pass and drop it for hires.

### Gaps
- No measured VRAM or it/s numbers for ControlNet on 8 GB Blackwell cards were found.
- No quality comparison of windsingai pose vs openpose-v2_1 vs xinsir promax on WAI was found.
- Whether diffusers' `ControlNetUnionModel` / `StableDiffusionXLControlNetUnionPipeline` handles the promax file was not verified in this session (the HF card only shows `DiffusionPipeline.from_pretrained`).

---

## 5. VRAM and speed on 8 GB, and diffusers vs ComfyUI availability

### Takeaway
All IP-Adapter features you need (plus, plus-face, FaceID Plus v2, masks, block-wise scales, precomputed embeds) are in **diffusers**. The finishing tools (FaceDetailer, Ultimate SD Upscale, cubiq weight-type presets with start/end) are **ComfyUI- or A1111-only** and have to be rebuilt by hand in diffusers. On 8 GB the main VRAM rule is: one pipeline, shared components, and offload enabled after all adapters are loaded.

### Cited Findings
- diffusers (docs v0.40) ships: IP-Adapter loading, per-block scale dicts, `IPAdapterMaskProcessor`, multiple adapters, FaceID/FaceID Plus v2 (insightface), and precomputed `ip_adapter_image_embeds`. — [diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)
- `enable_model_cpu_offload()` must come **after** `load_ip_adapter()`. — [diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)
- Precomputed embeds with `image_encoder_folder=None` remove the CLIP-ViT-H encoder from the generation path. — [diffusers IP-Adapter docs](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)
- PuLID has ComfyUI and diffusers-based third-party implementations. PuLID-FLUX needs 12–16 GB. — [ToTheBeginning/PuLID](https://github.com/ToTheBeginning/PuLID)
- InstantCharacter needs 24–48 GB and is FLUX-only. — [InstantCharacter issue #3](https://github.com/Tencent/InstantCharacter/issues/3)
- cubiq IPAdapter_plus (ComfyUI) is in maintenance-only mode as of Apr 2025. — [cubiq repo](https://github.com/cubiq/ComfyUI_IPAdapter_plus)
- The WAI creator recommends forge-neo (an A1111/Forge fork) rather than ComfyUI. — [Civitai API 827184](https://civitai.com/api/v1/models/827184)

### Inferences
- **The from_pipe blow-up:** `from_pipe` shares module objects, but the derived pipeline does not get the offload hooks. Calling it on an offloaded pipe then running it probably pulls the modules onto the GPU. Two fixes: call `enable_model_cpu_offload()` on the derived pipe as well, or keep a single `StableDiffusionXLImg2ImgPipeline` / inpaint pipeline for hires and face-detail passes and do the base pass with the text2img pipe that shares the same UNet. Unverified; needs a local check.
- **Suggested budget per image on 8 GB, no ControlNet:** base 1024² with IP-Adapter at block-scaled low weight, then 1.5× model upscale on CPU/GPU via spandrel, then img2img at denoise about 0.35 **without IP-Adapter**, then a face crop at 1024 through img2img at about 0.4, pasted back. Each pass reuses the same UNet. This roughly doubles the measured 30 s hires cost. Estimate only.
- **Availability matrix (inference plus prior knowledge, verify):**
  - diffusers native: IP-Adapter variants, masks, block scales, ControlNet (plus union), img2img and inpaint, schedulers.
  - ComfyUI or A1111 only: cubiq weight-type presets and start/end, Impact FaceDetailer, ADetailer, Ultimate SD Upscale, Noob IPA (documented for the A1111 ControlNet ext).
  - Third-party diffusers ports: PuLID-SDXL, InstantID (community pipeline).

### Gaps
- No measured 8 GB VRAM or timing numbers were found for IP-Adapter plus ControlNet plus hires on SDXL in 2025–2026 sources.
- Blackwell (sm_120) compatibility of insightface/onnxruntime-gpu (needed by FaceID, InstantID and possibly PuLID) was not researched.
- Whether kataragi's Noob IPA .bin loads through diffusers `load_ip_adapter` (key-format compatibility) is unknown.
