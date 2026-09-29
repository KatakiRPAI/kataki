# Practitioner pipelines, open-source tools, and 8 GB runtime practicalities for consistent original-character images (2025–2026)

Scope note: Reddit (r/StableDiffusion, r/comfyui, r/SillyTavernAI, r/LocalLLaMA) could not be read. The search/fetch tooling returns "domains are not accessible" for reddit.com, so the community-sentiment evidence below comes from GitHub repos, issues and discussions, the ComfyUI blog and docs, Hugging Face model cards, Civitai-linked write-ups, and practitioner tutorial sites. SEO listicles such as thinkpeak.ai and sozee.ai turned up in searches and were left out on purpose, including their unsourced "80–95% consistency" figures. Items older than 2025 are marked **[older]**.

## 1. Full shared workflows for "consistent original character" and what the community currently considers best

### Takeaway
Across 2025–2026 the dominant shared recipe is a pipeline, not a single trick: (1) make one good base image, (2) expand it into a multi-view/multi-expression **character sheet or dataset** with a reference or edit model, (3) **train a small character LoRA** on crops of that sheet, (4) generate scenes with the LoRA, optionally plus a reference adapter and a face detailer. In late 2025 the expansion step moved from PuLID/IP-Adapter on Flux/SDXL to **instruction-edit models (Qwen-Image-Edit 2509/2511)**. Those edit models are also used directly as a no-training consistency route. IP-Adapter now looks like the legacy zero-training option: its main ComfyUI node went maintenance-only in April 2025.

### Cited Findings
**Character sheet → LoRA (the "Mickmumpitz" lineage, the most-copied workflow family)**
- Mickmumpitz's workflow starts from a single input image and generates a **character sheet** (the same person from several angles and expressions on a controlled background). The sheet is cut into **10–15 clean crops** to train a **FLUX LoRA**. **[older: v1 Dec 2024]** — [pIXELsHAM summary of Mickmumpitz tutorial (2024-12-23)](https://www.pixelsham.com/2024/12/23/mickmumpitz-create-consistent-characters-from-an-input-image-with-flux-and-a-character-sheet-comfyui-tutorial-installation-guide/); [Runflow guide (2026)](https://www.runflow.io/blog/comfyui-consistent-characters-flux)
- "Consistent Character Creator 3.0", the third iteration of that series, adds **Qwen model integration**, expression control and turntable rendering. It produces front/side/angled profile sheets and expression libraries for comics and animation — [RunComfy: Consistent Character Creator 3.0](https://www.runcomfy.com/comfyui-workflows/consistent-character-creator-3-0)
- Mickmumpitz publishes free workflows covering FLUX, ComfyUI and **SDXL** for character sheets plus custom LoRA training — [Mickmumpitz Patreon (free workflows)](https://mickmumpitz.ai/posts/free-workflows-113743435?synced=1)

**Edit-model dataset synthesis (late-2025 shift)**
- Oct 2025 write-up: **Qwen-Image-Edit (original or 2509)** "can generate consistently the provided subject in varying styles, environments and orientations". The workflow feeds **one reference image plus 50+ prompt variations** (via a prompt file and custom nodes) to build a LoRA dataset. Training goes through **AI Toolkit** (Flux/Wan/Qwen/SDXL targets). The author reports a "consistent face however in different poses, clothes and backgrounds". Model sizes: **FP8 20.4 GB, BF16 40.9 GB**. The author suggests renting a cloud GPU at about $1/h. No captioning step and no caveats are described — [Weird Wonderful AI Art (2025-10-10)](https://weirdwonderfulai.art/comfyui/qwen-image-edit-can-create-character-consistent-lora-dataset/)
- ComfyUI ships a default Qwen edit workflow under its Templates menu ("search Qwen") — [same source](https://weirdwonderfulai.art/comfyui/qwen-image-edit-can-create-character-consistent-lora-dataset/)
- **Qwen-Image-Edit-2511** (Apache-2.0, 20B; the name encodes 2025-11, and install guides are dated 2025-12-23) lists "mitigated image drift, improved character consistency", better multi-person consistency, and **community LoRAs merged into the base** (for example lighting and viewpoint changes). The model card says it "can perform imaginative edits based on an input portrait while preserving the identity". Diffusers class `QwenImageEditPlusPipeline`; example uses 40 steps, `true_cfg_scale` 4.0 — [HF model card Qwen/Qwen-Image-Edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511); [kombitz GGUF guide (2025-12-23)](https://www.kombitz.com/2025/12/23/how-to-use-qwen-image-edit-2511-gguf-in-comfyui/)

**Fully automated single-image → LoRA pipeline (datacenter-class)**
- **CharForge** (MIT) does single reference → character sheet (multiple poses, expressions and lighting, plus optional **PuLID-Flux** and **MV-Adapter** views, run in an *ephemeral ComfyUI server*) → auto-captioning (LoRACaptioner, via Together AI) → **ai-toolkit Flux.1-dev LoRA, rank 8, 512 px** → inference in **diffusers** with an optional FaceEnhance pass. It credits Mickmumpitz as its inspiration. Requirements: **"GPU with at least 48GB VRAM", "At least 60GB RAM"**; "entire training pipeline takes 30–40 minutes on 1 L40S"; batch of 4 at 1024² takes 60–120 s on L40S — [GitHub RishiDesai/CharForge](https://github.com/RishiDesai/CharForge)

**Zero-training reference adapters (IP-Adapter / PuLID)**
- The SillyTavern-oriented ComfyUI guidance says a character looking different in every expression comes from missing visual conditioning. It recommends **IP-Adapter Plus fed by the character avatar (`%char_image%`) at weight ~0.7**. *(This is a secondary how-to site, not a firsthand post.)* — [Oreate AI guide](https://discover.oreateai.com/discover/how-to-set-up-the-sillytavern-comfyui-workflow-for-character-avatars-and-expressions)
- **ComfyUI_IPAdapter_plus** (cubiq), the standard IP-Adapter node pack, was set to **"maintenance only" on 2025-04-14**. The author said they no longer use ComfyUI as their main tool and plan no consistent work on it — [GitHub cubiq/ComfyUI_IPAdapter_plus README](https://github.com/cubiq/ComfyUI_IPAdapter_plus/blob/main/README.md)

**Local ground truth already measured on this machine (from the brief, not a web source)**
- On SDXL checkpoints (WAI-Illustrious, Nova Anime XL, Pony Realism) with IP-Adapter-plus, identity carries across scenes but **quality drops** compared with the no-adapter base image, and style/palette bleeds in from the reference. Speed is ~25–30 s/image at 832×1216 with model CPU offload, ~6.5 GB peak. This matches the practitioner move toward LoRA or edit models for the final quality path.

### Inferences
- The community "best" in 2025–2026 is **LoRA for durable identity plus an edit model or reference adapter to bootstrap the dataset**. Every serious public pipeline I found (Mickmumpitz 1–3, CharForge, the Qwen-edit dataset write-up) ends in LoRA training. None of them treats IP-Adapter alone as the final answer.
- For an app on Illustrious/SDXL, the likely shape is: base image, then **sheet generation** (SDXL + IP-Adapter/ControlNet-pose on 8 GB, or Qwen-Image-Edit if it can be made to fit), then a **background LoRA train**, then scene generation with the LoRA at normal quality without IP-Adapter. Until the LoRA exists, IP-Adapter (the current local path) can serve as the "first few scenes" fallback.
- IP-Adapter's node pack being maintenance-only is a medium-term maintenance risk for a ComfyUI-based app. The diffusers `load_ip_adapter` path is separate and was not assessed here.
- The SDXL LoRA route stays within the app's constraints. Flux-based pipelines (CharForge, Mickmumpitz v1/v2) assume 24–48 GB.

### Gaps
- No firsthand Reddit or Civitai-comment sentiment on "LoRA vs IP-Adapter vs edit models" could be read (reddit.com is blocked for this tool). The claim that commenters prefer LoRA rests on what published pipelines do, not on comment threads.
- No 2025–2026 source gave measured identity-similarity numbers (for example face-embedding cosine) comparing IP-Adapter, LoRA and Qwen-edit on anime/Illustrious characters.
- Whether Qwen-Image-Edit keeps **anime/Illustrious** styles as well as photoreal faces is not established by any source I read. The model card speaks to portraits.

## 2. Open-source projects that automate consistent characters for stories, comics, VNs and roleplay

### Takeaway
Most open-source story/comic tools use a **"reference sheet as visual anchor"** pattern: generate a sheet or avatar once, then feed it into every later generation. Local tools do this with IP-Adapter or img2img. Hosted-API tools pass it to multimodal models (Gemini, OpenAI). SillyTavern has **no built-in consistency**; it gives placeholders (`%char_avatar%`) and per-character prompt prefixes and LoRA tags. The most complete local, anime-oriented automation is **VNCCS**, a ComfyUI node suite on Illustrious. The academic StoryDiffusion approach (consistent self-attention) is older and needs more than 20 GB.

### Cited Findings
**SillyTavern (the reference roleplay front-end)**
- The Image Generation extension supports ComfyUI (noted as GPL-3) among many backends. Users export a ComfyUI workflow **"in API format"** and paste it into ST's Workflow Editor, and ST substitutes placeholders: `%prompt%`, `%negative_prompt%`, `%model%`, `%vae%`, `%sampler%`, `%scheduler%`, `%steps%`, `%scale%`, `%clip_skip%`, `%seed%`, `%width%`, `%height%`, `%denoise%`, `%user_avatar%`, `%char_avatar%`, plus custom find/replace pairs — [SillyTavern docs: Image Generation](https://docs.sillytavern.app/extensions/stable-diffusion/)
- Modes: character ("Yourself"), face ("Your Face"), user persona ("Me"), whole-story recap, last message, background — [same](https://docs.sillytavern.app/extensions/stable-diffusion/)
- **"No built-in character consistency mechanism exists."** Users rely on **character-specific prompt prefixes** (descriptors plus optional **LoRA tags**), which apply only in 1:1 chats and not to backgrounds or free mode — [same](https://docs.sillytavern.app/extensions/stable-diffusion/)
- ST ships two ComfyUI workflows: `Default_Comfy_Workflow.json` (txt2img) and `Char_Avatar_Comfy_Workflow.json` (img2img from the character avatar plus prompt) — [Oreate AI guide](https://discover.oreateai.com/discover/how-to-set-up-the-sillytavern-comfyui-workflow-for-character-avatars-and-expressions)

**VNCCS – Visual Novel Character Creation Suite (ComfyUI, MIT, v3.0)**
- A staged pipeline: Step 1 Character Creator (base model **Illustrious or "Anima"**, tag-based or a "CHARACTER WIZARD"), then Pose Studio (pose, proportions, age/height/body type), then Character Generator (optional upscale and **chroma-key background removal**, with SAM3 "details recovery"), then Step 2 Clothes (outfit sets across all poses), then Step 3 Emotions (**Face Detailer denoise** controls how far each expression departs from the base). It offers "Q4/Q5/Q8" model options, which suggests GGUF-quantized components. The README warns that emotion quality "depends very strongly on the exact character, style, and model". The fetched README did not explain the identity mechanism (IP-Adapter/LoRA/edit model) — [GitHub AHEKOT/ComfyUI_VNCCS](https://github.com/AHEKOT/ComfyUI_VNCCS)
- The project advertises consistent characters "as simple as pressing a button just 4 times" and lists animations, 3D scenes, voice and music as planned — [VNCCS search summary / repo](https://github.com/AHEKOT/ComfyUI_VNCCS)

**Comic generators**
- **ComicMind** (2025–26 graduation project, OpenAI-based) generates a **character reference sheet first**, then passes it back into every panel request "as a visual anchor" — [GitHub joessef97/comicmind](https://github.com/joessef97/comicmind)
- **AI-Comic-Generator** (Gemini models) does automatic storyboards plus **"character consistency checks"** and a visual editor — [GitHub Dapeng960208/AI-Comic-Generator](https://github.com/Dapeng960208/AI-Comic-Generator)
- **comic_book_project** is a local notebook: Qwen2.5-7B-Instruct for story, **SDXL/RealVisXL** for images. Consistency comes from locked character descriptions, reference images for main characters, and **"StoryDiffusion-style consistency logic via custom spatial attention"**. Evaluated with CLIP similarity (no numbers published). Only 4 commits — [GitHub AbdelrahmanMostafa12/comic_book_project](https://github.com/AbdelrahmanMostafa12/comic_book_project)

**StoryDiffusion (academic reference) [older: NeurIPS 2024]**
- Uses **consistent self-attention** across a batch of 3+ prompts (5–6 recommended), on SD1.5/SDXL-based models. The low-memory version was "tested on … 24GB GPU-memory (Tesla A10) and 30GB RAM, expected to work well with >20 G GPU-memory". Apache-2.0. No ComfyUI integration mentioned in the README — [GitHub HVision-NKU/StoryDiffusion](https://github.com/HVision-NKU/StoryDiffusion)

**Single-photo consistency repos**
- **oftenliu/consistent-character** advertises highly consistent images from a single photo with prompt-controlled clothing/expression/background. It is not assessed in depth (I only saw the search snippet) — [GitHub oftenliu/consistent-character](https://github.com/oftenliu/consistent-character)
- **CharForge** (see §1): the most complete automated OC pipeline, but it needs 48 GB — [GitHub RishiDesai/CharForge](https://github.com/RishiDesai/CharForge)

### Inferences
- The shared pattern for the app is **"reference-sheet anchor"**: a canonical base image stored per character, reused for every scene. This is what SillyTavern (`%char_avatar%`), ComicMind and VNCCS all do in different forms. The app's existing base→scene loop fits this pattern.
- VNCCS is the closest open-source analogue to the app's needs (Illustrious, sprites with transparent backgrounds, outfits, emotions, staged pipeline). Its workflow JSONs could be read to find the exact identity mechanism before designing ours.
- StoryDiffusion-style attention sharing only holds identity **within one batch** and needs more than 20 GB, so it is a poor fit for roleplay, where scenes arrive one at a time over days.

### Gaps
- Could not confirm how VNCCS keeps identity (IP-Adapter vs Qwen-edit vs face-detailer-only). Its README does not say. Reading its workflow JSONs would settle it.
- No 2025–2026 open-source roleplay front-end (SillyTavern, RisuAI, Agnai, Voxta, etc.) was found that **automatically trains per-character LoRAs**. That appears to be unoccupied ground, but a proper search of those projects was not done.
- No quantitative quality comparisons were found for any of these tools.

## 3. Running locally on 8 GB RTX 50-series laptop, Windows, driven by an app

### Takeaway
ComfyUI on Windows with Blackwell (sm_120) is mainstream as of 2025–2026. The portable build and desktop installer ship cu128 PyTorch. Since Dec 2025 **async offload and pinned memory are on by default** for NVIDIA, and since ~March 2026 **Dynamic VRAM** (just-in-time weight loading, Windows and Linux, NVIDIA only) is in stable. These are exactly the features that make an 8 GB card usable, and in diffusers they have to be hand-tuned. SageAttention 2.2 has Windows/Blackwell wheels (~30–35 % faster on a heavy Qwen-edit job on a 5090), but its Triton path can produce black images. **NVFP4** (2× speed on RTX 50) needs **cu130** PyTorch, while this machine is on cu128. For edit models on 8 GB, **Nunchaku 4-bit (FP4 on RTX 50) with per-layer offload (3–4 GB VRAM)** is the credible path. GGUF Q2/Q3 fits but looks soft. ComfyUI is GPL-3 and is driven over HTTP/WebSocket as a separate process. Diffusers is Apache-2.0 and in-process.

### Cited Findings
**Blackwell / Windows support**
- The ComfyUI Blackwell support thread (opened 2025-01-29) says 50-series needs "pytorch that has been built against cuda 12.8". On Windows, use the latest **standalone portable package or desktop installer** (pre-configured cu128). Early issues: missing torchaudio wheels on Windows, **custom-node import failures (Manager, InstantID, ReActor)**, and "sm_120 is not a recognized processor" when compiling Triton/SageAttention — [ComfyUI Discussion #6643](https://github.com/comfyanonymous/ComfyUI/discussions/6643)
- SageAttention on Blackwell/Windows (2025-12-31): PyTorch **2.11** (nightly at the time), **CUDA 12.8**, **Python 3.11**, **SageAttention 2.2.0** via prebuilt wheel (no CUDA Toolkit or Visual Studio needed). Measured **"30–35% faster on RTX 5090"**: Qwen-Image-Edit, 40 steps, **14 min 30 s → 9 min 30 s**. **Do not use `--use-sage-attention`** because "it uses the Triton backend which causes black output with some models (Qwen, Wan)". Instead use the KJNodes **"Patch Sage Attention"** node with the `sageattn_qk_int8_pv_fp16_cuda` backend — [ComfyUI Discussion #11583](https://github.com/Comfy-Org/ComfyUI/discussions/11583)
- Triton + SageAttention install guide for RTX 50 on Windows (2025-08-15) — [kombitz](https://www.kombitz.com/2025/08/15/install-triton-and-sageattention-on-windows-rtx-50-series/)

**Memory management features (the 8 GB-relevant part)**
- **Async offload + pinned memory**: "Enabled by default for all NVIDIA GPUs (as of December [2025])". "Your sampling speed may have improved 10–50%". This only helps when weights don't fit in VRAM, and it scales with PCIe generation and lane count (tested on PCIe 4.0 x16; x8 less impressive). Tested GPUs include an **RTX 3070 8 GB**. Flags: `--async-offload [streams]`, `--disable-async-offload`, `--disable-pinned-memory` — [ComfyUI blog (2026-01-09)](https://blog.comfy.org/p/new-comfyui-optimizations-for-nvidia); flag names also in [search summary of ComfyUI docs](https://docs.comfy.org/troubleshooting/overview)
- **NVFP4**: RTX 50 and Blackwell Pro, "~2x performance boost compared to fp8 or bf16". It **requires PyTorch built with CUDA 13.0 (cu130)**; otherwise sampling may be "up to 2x slower than fp8" — [ComfyUI blog (2026-01-09)](https://blog.comfy.org/p/new-comfyui-optimizations-for-nvidia)
- **Dynamic VRAM** (2026-03-25): a custom PyTorch VRAM allocator doing on-demand weight offload ("VBAR", a `fault()` API for just-in-time loading), "available in ComfyUI stable since 3 weeks ago for Nvidia hardware on Windows and Linux (WSL not supported)". It removes the need to predict memory usage. The benchmark chart uses an **RTX 5060** (WAN 2.2 video). Model loader nodes "execute almost instantly". Users report some broken custom nodes (SUPIR, KJ Nodes) after the update — [ComfyUI blog: Dynamic VRAM](https://blog.comfy.org/p/dynamic-vram-in-comfyui-saving-local)
- Related open issues exist: "Models always unloaded when using dynamic VRAM" (#13139), "Memory Management Regression (Update 13)" (#12541), and a positive "Pinned_memory feature is amazing" (#10555). Only titles were seen; contents not read — [#13139](https://github.com/Comfy-Org/ComfyUI/issues/13139), [#12541](https://github.com/Comfy-Org/ComfyUI/issues/12541), [#10555](https://github.com/Comfy-Org/ComfyUI/issues/10555)
- With GGUF models, the recommendation is to start ComfyUI with `--disable-pinned-memory` to avoid pinned-memory errors (secondary source) — [Neura Market](https://www.neura.market/errors/fix-pinned-memory-errors-gguf-models-comfyui)

**Measured speeds**
- ComfyUI community GPU benchmark (SDXL base 1.0, **1024², 20 steps**): **RTX 5060 Ti 16 GB 3.71 it/s** (2025-07-22) and **3.56–3.73 it/s** with `--fast` + xformers + sage attention (2025-07-27); **2.81–3.67 it/s** (2025-05-13). No RTX 5060 *Laptop 8 GB* entries — [ComfyUI Discussion #2970](https://github.com/Comfy-Org/ComfyUI/discussions/2970)
- A hosting vendor cites ~7 s per 1024² SDXL image on a 5060 Ti 16 GB in ComfyUI (vendor source, unverified) — [GigaGPU](https://gigagpu.com/rtx-5060-ti-16gb-comfyui-setup/)
- Local (brief): diffusers + model CPU offload on this RTX 5060 Laptop 8 GB gives **~25–30 s/image at 832×1216**, ~6.5 GB peak.

**Edit models on 8 GB**
- **Nunchaku** (SVDQuant 4-bit) supports Qwen-Image-Edit, Edit-Lightning (4/8-step), 2509 and 2509-Lightning. It auto-selects **FP4 weights on Blackwell** and INT4 elsewhere, with rank 32 or 128. Low-VRAM mode is per-layer offload: `set_offload(True, use_pin_memory=False, num_blocks_on_gpu=1)`, which "only requires 3-4GB of VRAM". Diffusers ≥0.36 is needed for 2509. No speed numbers given — [Nunchaku docs: Qwen-Image-Edit](https://nunchaku.tech/docs/nunchaku/usage/qwen-image-edit.html)
- For RTX 50, use `nunchaku_qwen_image_edit_2511_balance_fp4.safetensors`. Nunchaku runs 2511 in Forge-Neo — [DCAI blog](https://www.digitalcreativeai.net/en/post/how-speed-up-qwen-image-edit-2511-nunchaku-forge-neo)
- An HF discussion asks whether an 8 GB RTX 2060 Super works with nunchaku-qwen-image-edit (content not read) — [HF discussion #6](https://huggingface.co/nunchaku-ai/nunchaku-qwen-image-edit/discussions/6)
- GGUF route: on 8 GB "you are limited to **Q2_K or Q3_K_S** with the Lightning LoRA", and results are "usable but noticeably softer". Lightning = **4 steps, CFG 1.0** (secondary source) — [Thunder Compute blog](https://www.thundercompute.com/blog/qwen-image-edit-comfyui); models at [unsloth/Qwen-Image-Edit-2511-GGUF](https://huggingface.co/unsloth/Qwen-Image-Edit-2511-GGUF)

**ComfyUI as a headless API**
- The server runs headless (the UI is just one client) on port 8188. Main routes: `POST /prompt` (queue an API-format workflow, returns `prompt_id`), `GET /history/{prompt_id}`, `GET /view` (fetch an image), `POST /upload/image`, `GET/POST /queue`, **`POST /interrupt`**, **`POST /free`** (unload models / free memory), `GET /system_stats`, `GET /object_info`, `GET /models/{folder}`. The WebSocket `/ws` streams `status`, `execution_start`, **`execution_cached`**, `executing`, `progress`, `executed` — [ComfyUI docs: Server Routes](https://docs.comfy.org/development/comfyui-server/comms_routes); [official websockets_api_example.py](https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/websockets_api_example.py); [websockets_api_example_ws_images.py](https://github.com/Comfy-Org/ComfyUI/blob/master/script_examples/websockets_api_example_ws_images.py)
- CharForge runs ComfyUI as an **ephemeral server** for sheet generation and switches to **diffusers** for inference. That mixed architecture shows up in a real project — [CharForge](https://github.com/RishiDesai/CharForge)
- SillyTavern itself drives ComfyUI through this API with placeholder-substituted JSON — [SillyTavern docs](https://docs.sillytavern.app/extensions/stable-diffusion/)

**Licensing / maintenance**
- ComfyUI is **GPL-3** — [SillyTavern docs (backend list)](https://docs.sillytavern.app/extensions/stable-diffusion/)
- Diffusers is Apache-2.0 — [GitHub huggingface/diffusers](https://github.com/huggingface/diffusers)
- Qwen-Image-Edit-2511 is Apache-2.0 — [HF model card](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)
- Maintenance signals: the IP-Adapter node pack is maintenance-only (2025-04-14) — [cubiq README](https://github.com/cubiq/ComfyUI_IPAdapter_plus/blob/main/README.md). Memory-management updates broke custom nodes (SUPIR, KJ Nodes) — [ComfyUI Dynamic VRAM blog](https://blog.comfy.org/p/dynamic-vram-in-comfyui-saving-local). cu128 builds broke some custom nodes early on — [#6643](https://github.com/comfyanonymous/ComfyUI/discussions/6643)

### Inferences
- **ComfyUI vs diffusers tradeoff for this app:**
  - *ComfyUI (separate process over HTTP/WS):* you get Dynamic VRAM, async offload, pinned memory, node-output caching, a queue, `/interrupt` and `/free` without writing them. It also has the richest consistency ecosystem (VNCCS, Mickmumpitz sheets, Nunchaku nodes, KJ Sage patch). Costs: a second large Python install to ship and update; GPL-3; custom-node churn and breakage on updates (documented above); the app must version-pin ComfyUI plus its nodes. Running it as a separate process and talking HTTP is the usual way to keep the GPL boundary at "aggregation", but this is not legal advice. The user said to ignore licence matters, so treat this as a note only.
  - *Diffusers (in-process in the Python engine):* Apache-2.0, one environment, direct control, already working. But every memory trick has to be hand-rolled, and the local log shows a single wrong move (stacking `from_pipe` on an offloaded pipe) can go from seconds to 145 s/step. Nunchaku's diffusers API (`set_offload`) covers the edit-model case in-process.
- Since the engine already works on diffusers at 25–30 s/image, a reasonable path is **diffusers for the SDXL/Illustrious lane** (plus Nunchaku-in-diffusers for Qwen-edit). ComfyUI would then be an optional or "power-user" backend, as SillyTavern treats it, rather than a hard dependency.
- **NVFP4 on this machine:** the user's torch is cu128. The ComfyUI blog says NVFP4 without cu130 can be *2× slower than fp8*. Nunchaku FP4 uses its own kernels, so it may not share that constraint, but the wheel must match the exact torch/CUDA/Python combination (unverified for torch 2.11+cu128 on Windows).
- **SageAttention's win is mostly on heavy DiT/edit models.** The 30–35 % figure is Qwen-Image-Edit on a 5090. For SDXL at ~1 MP the attention share is smaller, and the 5060 Ti benchmark rows with and without sage are close (3.56–3.73 vs 3.71 it/s). Expect little gain for the SDXL lane.
- **Laptop PCIe matters.** Async offload gains scale with PCIe lanes, and many laptop 5060s run PCIe x8, so offload-heavy paths (Qwen-edit with 1 block on GPU) will be slower than desktop reports.
- **GPU turn-taking with llama.cpp:** ComfyUI's `POST /free` (unload_models) gives the app an explicit "hand the GPU back" call. In diffusers the equivalent is deleting or offloading pipeline modules plus `torch.cuda.empty_cache()`. Pinned-memory buffers use host RAM that llama.cpp may also want on a 32 GB machine, so disabling pinned memory (or bounding it) may be needed while both are loaded.

### Gaps
- No measured SDXL numbers for an **RTX 5060 Laptop 8 GB** in ComfyUI were found. The closest are 5060 Ti 16 GB (~3.6–3.7 it/s at 1024²/20 steps, which is roughly 6 s/image). The local diffusers figure (25–30 s at 832×1216 with CPU offload) suggests offload overhead dominates. A fair ComfyUI-vs-diffusers A/B on this machine has not been done.
- No measured s/image for **Qwen-Image-Edit 2509/2511 via Nunchaku FP4 on 8 GB** was found.
- Did not verify whether Nunchaku publishes a Windows wheel for torch 2.11 + cu128 + Python 3.12.
- Could not read the contents of ComfyUI issues #13139 / #12541, so their effect on keeping a model warm between app requests is unknown.
- The kohya/SDXL 8 GB LoRA training discussion (next section) is mostly **[older: 2024]** with one Dec 2025 comment. No clean 2025–2026 measurement of Illustrious LoRA training time on 8 GB was found.

## 4. Caching and speed patterns for an app (pre-generated sheets, reused embeddings/LoRAs, batching, background queues)

### Takeaway
The patterns practitioners use: **generate the canonical reference or sheet once at character creation** and store it as the anchor. **Turn it into a LoRA as a background job** where feasible. **Keep the model warm and batch a character's scenes** so offload/reload costs are paid once. Use a **queue with interrupt and unload** so the image model and the LLM can take turns. ComfyUI provides node-output caching and queueing for free. In diffusers you implement them yourself: cache the prompt embeddings and the IP-Adapter image embeddings per character.

### Cited Findings
- **Reference-sheet anchor, generated once and reused every time:** ComicMind generates the sheet first and passes it into every panel request — [ComicMind](https://github.com/joessef97/comicmind). SillyTavern's img2img workflow reuses `%char_avatar%` for every generation — [SillyTavern docs](https://docs.sillytavern.app/extensions/stable-diffusion/). VNCCS builds base, poses, clothes and emotions as separate stored stages — [VNCCS](https://github.com/AHEKOT/ComfyUI_VNCCS)
- **LoRA as the cached identity:** Mickmumpitz sheets go to 10–15 crops, then a LoRA — [pIXELsHAM](https://www.pixelsham.com/2024/12/23/mickmumpitz-create-consistent-characters-from-an-input-image-with-flux-and-a-character-sheet-comfyui-tutorial-installation-guide/). CharForge's end-to-end sheet, caption and train run takes 30–40 min on an L40S (48 GB) — [CharForge](https://github.com/RishiDesai/CharForge)
- **SDXL LoRA training on 8 GB is feasible with memory savers.** kohya sd-scripts recommends U-Net-only training, gradient checkpointing, `cache_text_encoder_outputs` + cached latents, an 8-bit optimizer or Adafactor, and **network dim 4–8 for 8 GB** ("8GB GPU memory (10GB recommended)") — [kohya-ss/sd-scripts train_SDXL-en.md](https://github.com/kohya-ss/sd-scripts/blob/main/docs/train_SDXL-en.md)
- Practitioner reports on 8 GB SDXL LoRA training: "Lowest I have seen people do is 6gb", using fp8 training **[older: 2024-06-16]**. A Dec 2025 comment warns "get ready to halve the speed if the spill is above a few Mbs" and says 16 GB is "not enough" without gradient checkpointing — [kohya_ss Discussion #2594](https://github.com/bmaltais/kohya_ss/discussions/2594)
- **ComfyUI caches node outputs between queued prompts.** The WebSocket reports `execution_cached` for nodes whose inputs didn't change (for example the checkpoint loader or an unchanged character-prompt encode), and the server exposes `/queue`, `/interrupt` and `/free` for background-queue control — [ComfyUI Server Routes](https://docs.comfy.org/development/comfyui-server/comms_routes)
- **Dynamic VRAM** makes model loader nodes "execute almost instantly" and balances VRAM continuously, which suits an app that switches models between requests — [ComfyUI blog](https://blog.comfy.org/p/dynamic-vram-in-comfyui-saving-local)
- **Few-step distilled variants** (Qwen-Image-Edit-Lightning 4/8-step) exist for a fast in-story lane — [Nunchaku docs](https://nunchaku.tech/docs/nunchaku/usage/qwen-image-edit.html); Lightning 4-step at CFG 1.0 — [Thunder Compute](https://www.thundercompute.com/blog/qwen-image-edit-comfyui)
- Local (brief/prior spike): batching a character's scenes in one warm process gave ~25 s/image, while the offload tax mostly hits on reload. Keeping every pipeline under ~8 GB peak was the single biggest speed factor, since spilling into shared RAM made generation 10–400× slower.

### Inferences
- A workable app shape:
  1. **At character creation (quality mode):** generate the base image (no IP-Adapter, full steps, optional hires pass), then a small **sheet** (a few angles and expressions) from it. Store the base, the sheet, the seed, the prompt and the cached text-encoder/IP-Adapter embeddings with the character record.
  2. **Background job (optional, opt-in):** train an SDXL character LoRA (dim 4–8, U-Net-only, cached latents/TE) from the sheet while the user is idle and the LLM is unloaded. Time on 8 GB is unmeasured (see gaps).
  3. **In-story scenes (fast mode):** a queue that **batches scenes per character** while the model is warm. Use a few-step LoRA (Lightning/DMD2, already planned locally) or an edit-model Lightning variant. Explicitly unload (ComfyUI `/free` or diffusers offload + `empty_cache`) before handing the GPU back to llama.cpp.
- Caching the IP-Adapter **image embedding** per character (diffusers accepts precomputed `ip_adapter_image_embeds`) would skip the CLIP ViT-H encoder on every scene. The earlier local spike found that encoder was a big part of the VRAM problem. This is an inference from the local spike, not from a source read here.
- Scheduling the queue around the LLM (for example "generate after the reply is streamed and the LLM is idle") matters more than raw s/image, since both models cannot share 8 GB.

### Gaps
- No 2025–2026 firsthand measurement of **Illustrious/SDXL character-LoRA training wall time on an 8 GB 50-series laptop** was found. The kohya docs give settings, not times, and the Civitai article "Training SDXL LoRA in Kohya_SS with 8GB, 12GB…" (articles/10872) returned HTTP 404.
- No source quantified how much ComfyUI's node caching saves in a roleplay-style request stream.
- No source described an open-source roleplay app that **auto-trains** per-character LoRAs in a background queue, so there is no measured precedent for that UX.
