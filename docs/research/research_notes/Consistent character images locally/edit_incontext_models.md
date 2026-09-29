# Image edit / in-context / multi-reference models for "same character, new scene/pose" on an 8 GB GPU (2025–2026)

Research date: 2026-09-22. Target: RTX 5060 Laptop 8 GB (Blackwell sm_120), 32 GB RAM, Windows, local only. Adult RP app, adult characters only.
Note: reddit.com could not be fetched by the research tools, so r/StableDiffusion, r/comfyui and r/LocalLLaMA posts are missing. Practitioner data below comes from HF discussions, GitHub issues, note.com, Civitai and blogs instead.

## 1. Which models are current for "same character, new scene/pose", and which do practitioners rate highest?

### Takeaway
As of Sept 2026 the practical open-weight shortlist is **Qwen-Image-Edit-2511** (20B, Apache-2.0; the most consistently praised for identity and anime-style retention), **FLUX.2 [klein] 4B/9B** (Jan 2026; very fast, multi-reference, but it redraws anime styles and is heavily NSFW-filtered), **Qwen-Image-2.1** (7B unified gen+edit, released 2026-09-20; up to 10 refs; research-only licence) and **Microsoft Mage-Flow-Edit-Turbo** (4B, MIT, July 2026; rated as good as Qwen-2511 on faces in one firsthand test). Z-Image-Edit has still not been released. The 2025 FLUX.1-dev-era identity adapters (PuLID-Flux, InfiniteYou, UNO/USO, DreamO) and older editors (OmniGen2, Step1X-Edit, HiDream-E1, BAGEL, Kontext) are mostly superseded. Kontext still gets praise for character consistency.

### Cited Findings
**Qwen-Image-Edit family (Alibaba)**
- Qwen-Image-Edit-2511 (Nov 2025, Apache 2.0). Model card lists "mitigate image drift, improved character consistency, integrated LoRA capabilities… strengthened geometric reasoning" and says it "can perform imaginative edits based on an input portrait while preserving the identity and visual characteristics of the subject". Recommended settings: 40 steps, guidance 1.0, true_cfg 4.0. Takes a list of input images. — [HF: Qwen/Qwen-Image-Edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)
- 2511 bakes popular LoRAs (e.g. lighting enhancement, viewpoint generation) into the base model. — [HF: Qwen-Image-Edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)
- Qwen-Image-Edit-2509 added multi-image editing ("person + person", "person + product", "person + scene"; 1–3 input images) plus face-ID preservation and pose transformation. — [HF: Qwen/Qwen-Image-Edit-2509](https://huggingface.co/Qwen/Qwen-Image-Edit-2509); [Qwen-Image-Edit-2509.md](https://github.com/QwenLM/Qwen-Image/blob/main/Qwen-Image-Edit-2509.md)
- Official 4-step Lightning LoRA for 2511: `lightx2v/Qwen-Image-Edit-2511-Lightning` (Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16). — [HF: lightx2v/Qwen-Image-Edit-2511-Lightning](https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning/blob/main/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors)
- Qwen-Image-2.0 (Feb 2026) merged generation and editing into one 7B model with native 2K output and up to 10 input images. Qwen-Image-2.1 (released 2026-09-20) keeps the 7B size, adds native RGBA, ships BF16 weights (14.2 GB) and INT8 (7.26 GB), and moved to the **Qwen Research License (non-commercial only)**, where earlier Qwen-Image versions were Apache 2.0. — [eesel: Qwen Image 2.1 review](https://www.eesel.ai/blog/qwen-image-2-1-review); [eesel: what's new](https://www.eesel.ai/blog/qwen-image-2-1)
- ComfyUI had native day-0 support for Qwen-Image-2.1: "Up to 10 reference images", unified gen/edit checkpoint, RGBA. — [Comfy blog, 2026-09-20](https://blog.comfy.org/p/qwen-image-21-in-comfyui-open-weight)
- A "Qwen-Image 3.0" also exists. A blog title says "the lower number is newer" (2.1 is newer than 3.0). Not investigated. — [orcarouter](https://www.orcarouter.ai/blog/qwen-image-2-1-vs-qwen-image-3-0)

**FLUX (Black Forest Labs)**
- FLUX.2 [klein], released 2026-01-15, comes in 4B and 9B sizes, each as Base (50-step) and Distilled (4-step). It does T2I, single-reference editing and multi-reference composition. Formats: BF16, FP8, NVFP4. Text encoder: Qwen3-4B. RTX 5090 numbers: 4B distilled ~1.2 s / 8.4 GB; 4B base ~17 s / 9.2 GB; 9B distilled ~2 s / 19.6 GB; 9B base ~35 s / 21.7 GB. — [Comfy blog: FLUX.2 klein](https://blog.comfy.org/p/flux2-klein-4b-fast-local-image-editing); [ComfyUI docs](https://docs.comfy.org/tutorials/flux/flux-2-klein); [GitHub black-forest-labs/flux2](https://github.com/black-forest-labs/flux2)
- Licences: Klein 9B is non-commercial; Klein 4B is Apache 2.0. — [note.com (2026-01-25)](https://note.com/cute_agapan9087/n/naf0940a4bf9b?hl=en)
- Klein 9B uses a Qwen3-8B text encoder (fp8mixed file 8.1 GB) in a ComfyUI setup. — [GitHub issue local-asset-studio #357](https://github.com/Chris0Jeky/local-asset-studio/issues/357)
- FLUX.2 [dev] (32B): up to 8 reference images, "excellent prompt adherence", "extremely slow", needs quantization on smaller GPUs; a Turbo LoRA cuts 50 steps to 8. — [diffusiondoodles, 2026-02-16](https://diffusiondoodles.substack.com/p/open-source-diffusion-model-summary). A search summary of BFL material says up to 10 images. — [GitHub flux2](https://github.com/black-forest-labs/flux2)
- FLUX.1 Kontext [dev] (a 2025 model): "Excellent character consistency", "Class leading", "Good at only modifying sections of an image", but weaker with complex prompts and style transfer than newer models. — [diffusiondoodles, 2026-02-16](https://diffusiondoodles.substack.com/p/open-source-diffusion-model-summary)

**Z-Image (Tongyi-MAI)**
- Z-Image-Turbo was released 2025-11-26 and Z-Image (base) 2026-01-27, both Apache-2.0. **Z-Image-Omni-Base and Z-Image-Edit are still listed as "To be released"** with no weights. — [GitHub Tongyi-MAI/Z-Image](https://github.com/Tongyi-MAI/Z-Image)
- An HF thread asking "Is an open-source release for z-image-edit still a possibility?" (opened May 2026, still active) has no official reply. Users say the release looks unlikely and describe it as "in limbo months later". — [HF discussion #156](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/discussions/156). A July 2026 blog also says "Z-Image-Edit is not released". — [siray.ai](https://blog.siray.ai/z-image-nsfw-character-consistency/)

**Microsoft Mage-Flow (new, July 2026)**
- Mage-Flow was released 2026-07-22. — [ComfyUI Wiki news](https://comfyui-wiki.com/en/news/2026-07-22-mage-flow-microsoft). (A HackerNoon summary says "2024", which conflicts with this and is probably wrong.)
- Mage-Flow-Edit-Turbo: 4B NR-MMDiT + Mage-VAE, MIT licence, 4 steps, 1.02 s per edit at 1024² on an A100, 18–20 GB peak at full precision, 512–2048 px at any aspect ratio. Scores: ImgEdit-Bench 4.38/5, GEdit-EN 8.271. — [HackerNoon](https://hackernoon.com/mage-flow-edit-turbo-microsofts-4b-image-editing-model); [HF microsoft/Mage-Flow-Edit-Turbo](https://huggingface.co/microsoft/Mage-Flow-Edit-Turbo)
- ComfyUI supports it natively with Int8 (plus BF16/FP8) diffusion checkpoints and a "Qwen3VL-4B text encoder". The edit template accepts "one or more reference images" (LoadImage up to 3). — [ComfyUI docs: Mage-Flow](https://docs.comfy.org/tutorials/image/mage-flow/mage-flow)

**Firsthand head-to-head (July 2026, RTX 5060 Ti 16 GB, 8 models, 15 test images)** — [note.com おーら, 2026-07-28](https://note.com/ai_0049/n/n8051776106dc?hl=en)
| Model | Steps | Time | Quant |
|---|---|---|---|
| FLUX.2 [klein] 9B | 4 | ~5 s | fp8 |
| Mage-Flow-Turbo | 5 | ~2 s | BF16 |
| Qwen-Image-Edit-2511 | 4 | ~32 s | INT8 |
| Wan-Bernini-R | 3+3 | ~40 s | — |
| FireRed Image Edit 1.1 | 40 | ~475 s | Q4 |
| LongCat Image Edit | 50 | ~255 s | — |
| Boogu Image Edit | 25 | ~301 s | INT8 |
| JoyAI Image Edit | 41 | ~609 s | — |
- Verdicts from that test: Qwen-Image-Edit-2511 and Mage-Flow-Turbo were best at keeping facial features. FLUX.2 "redrew the image significantly, changing the art style" on anime input. Pose, camera-angle and head-orientation changes were "the most difficult", and 90° angle changes were "effectively unsupported by any model". Final recommendation: "FLUX.2-9B and Qwen-Image-Edit-2511". — [note.com](https://note.com/ai_0049/n/n8051776106dc?hl=en)
- Feb 2026 roundup: Qwen-Image-Edit-2511 has "reasonable character and scene consistency" but "can mis-interpret instructions, large model so fairly slow". Klein 9B "struggles with anime composition" and has lower realism than Z-Image-Turbo. — [diffusiondoodles](https://diffusiondoodles.substack.com/p/open-source-diffusion-model-summary)
- Community opinion is split on Klein vs Qwen. Some say Klein edit is "much better". Others say Klein "has no understanding of anatomy, is extremely censored" and rank it below Z-Image and Qwen 2511. (Search-snippet level; thread not fully read.) — [HF discussion Z-Image-Turbo #135](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/discussions/135); [diffusiondoodles: Klein](https://diffusiondoodles.substack.com/p/flux2-klein-shrinking-flux2-dev)

**Other 2025–2026 editors / identity methods (mostly superseded or too heavy)**
- Bernini-R (ByteDance) is a renderer fine-tuned from Wan, released as 14B and 1.3B Diffusers weights. It does t2i/i2i/video editing. The ComfyUI port "Runs in 24GB with fp8". — [GitHub bytedance/Bernini](https://github.com/bytedance/Bernini/blob/main/docs/bernini_r.md); [ComfyUI-BerniniR](https://github.com/neuregex/ComfyUI-BerniniR)
- FireRed-Image-Edit and LongCat-Image-Edit are publicly available editing checkpoints, studied alongside Qwen-Image-Edit in a May 2026 paper. — [arXiv 2605.04566](https://arxiv.org/abs/2605.04566)
- DreamOmni2 (CVPR 2026 Highlight) is built on FLUX.1-Kontext-dev and takes 1–3 reference images. It claims the best subject-driven identity/pose consistency among open models. ComfyUI node supports INT8 + CPU offload; a GGUF (7.6B) exists. — [GitHub DreamOmni2](https://github.com/JIA-Lab-research/DreamOmni2); [ComfyUI_RH_DreamOmni2](https://github.com/HM-RunningHub/ComfyUI_RH_DreamOmni2); [HF rafacost/DreamOmni2-7.6B-GGUF](https://huggingface.co/rafacost/DreamOmni2-7.6B-GGUF)
- OmniGen2 (2025-06-16, Apache-2.0): ~17 GB VRAM, model CPU offload cuts that ~50%, sequential offload <3 GB but much slower. Its README admits in-context generation "sometimes produces objects that differ from the original ones". — [GitHub VectorSpaceLab/OmniGen2](https://github.com/VectorSpaceLab/OmniGen2) (older, mid-2025)
- USO (ByteDance, Aug 2025) unifies style- and subject-driven generation and claims near-perfect retention of face/body features. — [arXiv 2508.18966](https://arxiv.org/html/2508.18966v1). InfiniteYou (Mar 2025) injects identity through InfuseNet into a FLUX DiT. — [arXiv 2503.16418](https://arxiv.org/html/2503.16418v1). UMO improves on OmniGen2 for multi-identity. — [UMO overview](https://sonusahani.com/blogs/umo). DreamO has a native ComfyUI port. — [ComfyUI-DreamO](https://github.com/ToTheBeginning/ComfyUI-DreamO). All are FLUX.1-era (2025) methods.
- Step1X-Edit v1.2 (2025-11-26) is a "reasoning" editor (GEdit overall 7.58 with think+reflect). HiDream-E1.1 dates from 2025-07-16. BAGEL is 7B-active / 14B-total MoT, Apache 2.0; high-res 1024² can need ~50 GB VRAM. — [builderai.tools](https://builderai.tools/blog/ai-image-editing-flux-kontext-qwen-image-edit-step1x); [GitHub stepfun-ai/Step1X-Edit](https://github.com/stepfun-ai/Step1X-Edit); [HiDream E1.1 low-VRAM guide](https://www.stablediffusiontutorials.com/2025/07/hidream-e11-image-editing-on-low-vrams.html)

### Inferences
- For identity fidelity on existing art, the evidence ranks Qwen-Image-Edit-2511 ≈ Mage-Flow-Edit-Turbo > FLUX.2 klein 9B > klein 4B. For photoreal faces, Kontext is still praised but is older and less capable with complex prompts.
- Mage-Flow-Edit-Turbo looks like the most promising new candidate for 8 GB: 4B DiT, Int8 ComfyUI checkpoint (~4–5 GB estimated), 4–5 steps, MIT licence. But nobody has published 8 GB numbers or NSFW/anime reports yet.
- Pose and gaze changes are a known weak point across all editors. That matches the local test where "looking away" was only partly followed. Pose-heavy requests may need a pose/ControlNet-style path rather than instruction-only editing.

### Gaps
- No Reddit data (domain blocked for the tools). No independent identity-similarity metrics (e.g. ArcFace scores) comparing these models on anime characters.
- Qwen-Image 3.0 status and weights were not checked. JoyAI, Boogu and FireRed 1.1 model cards were not examined.
- Mage-Flow-Edit's safety filtering and NSFW behaviour are undocumented in the sources found.

## 2. How do they run on 8 GB VRAM + 32 GB RAM (quants, offload, Lightning), and are there Blackwell/Windows issues?

### Takeaway
On 8 GB, the 20B Qwen-Image-Edit only runs with weight streaming/offload (even Q2_K is 7.4 GB) or with Nunchaku 4-bit plus offload. Reported times are ~2 min per 1024² image on 6 GB cards with Lightning. The small models are what fit 8 GB. FLUX.2 klein 4B distilled (8.4 GB at FP8 on a 5090, so borderline) and Qwen-Image-2.1 (1024² at 6.14 GiB VRAM when the text encoder is kept on CPU) are the realistic "fits in VRAM" options. On Windows + RTX 50, Nunchaku needs FP4 (NVFP4) checkpoints. INT4 kernels fail on sm_120, and there is an open Windows bug report.

### Cited Findings
**Qwen-Image-Edit (20B) quantized sizes and low-VRAM reports**
- GGUF sizes of the Qwen-Image-Edit (Rapid-AIO) transformer: Q2_K 7.44 GB, Q3 9.3–10 GB, Q4 12.2–13.3 GB, Q5 14.4–15.6 GB, Q6_K 17 GB, Q8_0 21.8 GB, F16 40.9 GB. — [HF Phil2Sat/Qwen-Image-Edit-Rapid-AIO-GGUF](https://huggingface.co/Phil2Sat/Qwen-Image-Edit-Rapid-AIO-GGUF). Unsloth also ships 2511 GGUFs. — [HF unsloth/Qwen-Image-Edit-2511-GGUF](https://huggingface.co/unsloth/Qwen-Image-Edit-2511-GGUF)
- RTX 3060 **laptop 6 GB + 16 GB RAM**: Qwen Image and Kontext Q4 quants "work perfectly fine if you're willing to wait". "Memory optimizations are quite mature" and the quality loss is "not visible for recreational or personal use". Another user reported 3–5 min per image with Q6_K. (Aug 2025) — [HF QuantStack/Qwen-Image-Edit-GGUF discussion #3](https://huggingface.co/QuantStack/Qwen-Image-Edit-GGUF/discussions/3)
- Rapid-AIO GGUF: ~2 minutes per 1024×1024 generate/edit on an **RTX 4050 6 GB** (secondary summary). — [HackerNoon guide](https://hackernoon.com/a-beginners-guide-to-qwen-image-edit-rapid-aio-gguf-best-use-cases-limitations-plus-more)
- Nunchaku (SVDQuant 4-bit) supports Qwen-Image-Edit, 2509 and Lightning-fused 4/8-step variants at rank r32 (faster) or r128 (better quality). "Use FP4 models for Blackwell GPUs (RTX 50-series) and INT4 models for other architectures." With CPU offload, "VRAM usage can be reduced to approximately 3GB". 2509 needs diffusers ≥0.36.0. — [Nunchaku docs: Qwen-Image-Edit](https://nunchaku.tech/docs/nunchaku/usage/qwen-image-edit.html); [HF nunchaku-ai/nunchaku-qwen-image-edit](https://huggingface.co/nunchaku-ai/nunchaku-qwen-image-edit)
- 2511 SVDQ quants from QuantFunc: INT4/FP4 at rank 32/128/256. They need the QuantFunc ComfyUI plugin (Windows `quantfunc.dll`, CUDA 12/13, native FP4 on Blackwell) and claim a "2x–11x speedup" over BF16 Python pipelines, with no per-GPU numbers. — [HF QuantFunc/Nunchaku-Qwen-Image-EDIT-2511](https://huggingface.co/QuantFunc/Nunchaku-Qwen-Image-EDIT-2511)
- An NVFP4 (Blackwell) SVDQ quant of the NSFW Rapid-AIO v19 exists: `tacodevs/svdq-fp4_r128-phr00t-qwen-image-edit-v19`. — [HF tacodevs](https://huggingface.co/tacodevs/svdq-fp4_r128-phr00t-qwen-image-edit-v19)
- Measured on an **RTX 3090**, Qwen-Image-Edit-2511 with the 4-step Lightning LoRA: Forge-Neo standard 34 s, Forge-Neo + Nunchaku 19 s, ComfyUI standard 32 s, ComfyUI + SageAttention 25 s (May 2026). — [DCAI blog](https://www.digitalcreativeai.net/en/post/how-speed-up-qwen-image-edit-2511-nunchaku-forge-neo)
- Measured on an **RTX 5060 Ti 16 GB**: Qwen-Image-Edit-2511 INT8 at 4 steps took ~32 s; Klein 9B fp8 at 4 steps took ~5 s (July 2026). — [note.com](https://note.com/ai_0049/n/n8051776106dc?hl=en)
- Regression: the ComfyUI Nunchaku Qwen-Image-Edit loader reloads the model on every generation (RTX 3090, 32 GB RAM, Windows portable, 119 s per prompt). Opened 2026-05-26 with no fix. — [ComfyUI issue #14122](https://github.com/Comfy-Org/ComfyUI/issues/14122)

**FLUX.2 klein**
- 4B distilled: ~1.2 s and 8.4 GB. 4B base: 9.2 GB. 9B distilled: 19.6 GB (RTX 5090 measurements). — [Comfy blog](https://blog.comfy.org/p/flux2-klein-4b-fast-local-image-editing)
- BFL's own model card says Klein 4B "fits in ~13GB VRAM" (RTX 3090/4070 and up). An FP8 repo exists. — [HF black-forest-labs/FLUX.2-klein-4b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8); [HF FLUX.2-klein-4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)
- A guide recommends Klein 4B for 8 GB cards. It estimates Klein 9B GGUF Q4 with text-encoder offload at ~9–11 GB peak, which is over 8 GB (estimate, not a measurement). — [willitrunai](https://willitrunai.com/blog/flux-2-klein-9b-vram-requirements); [localaimaster](https://localaimaster.com/blog/flux-2-local-setup-guide)
- NVFP4 vs GGUF Q8 on an RTX 5090: NVFP4 was 87% faster on Z-Image-Turbo, 100% on FLUX.2 Dev, 118% on FLUX.1 Dev and 93% on FLUX.1 Kontext Dev, but "showed visual degradation" compared with BF16, Q8 and FP8-scaled. The author recommends CUDA 13 builds of ComfyUI. — [dev.to Furkan Gözükara (Jan 2026)](https://dev.to/furkangozukara/bf16-vs-gguf-fp8-scaled-nvfp4-speed-quality-compared-comfyui-cuda-13-gains-flux-2-klein-9b-59k7)

**Qwen-Image-2.1 (7B) low-VRAM data (relevant to the existing local spike)**
- One community tester got 1024×1024 at **6.14 GiB VRAM with the text encoder on CPU**, and 512×512 at 3.05 GiB VRAM using ~15.2 GiB system RAM with CPU offload. — [Alexey Fateev on X](https://x.com/superalesha/status/2101940249735634998); [eesel review](https://www.eesel.ai/blog/qwen-image-2-1-review); code at [GitHub alesha-pro/tools/qwen-image-2.1](https://github.com/alesha-pro/tools/tree/main/qwen-image-2.1)
- The same repo reports an RTX 3090 with INT8 ConvRot DiT + text encoder, 2048×1152 at 50 steps: 82–96 s per end-to-end ComfyUI job. It recommends 64 GB RAM and says "32 GB may require offload tuning". For 16 GB cards: "1024 × 1024, batch 1, CPU text encoder and `--lowvram`". — [GitHub alesha-pro/tools](https://github.com/alesha-pro/tools/tree/main/qwen-image-2.1)
- ComfyUI files: diffusion `qwen_image_2.1_bf16` / `qwen_image_2.1_int8_convrot`; text encoder `qwen3vl_8b` in bf16 / int8_convrot / w4a8. An unverified community report gives "~1.32 it/s @ 1MP on 10 GB". — [GitHub issue local-asset-studio #739](https://github.com/Chris0Jeky/local-asset-studio/issues/739)
- GGUF DiT sizes for Qwen-Image-2.1: Q8_0 ~7.2 GB, Q6_K ~5.5 GB, Q5_K_M ~4.6 GB (ComfyUI-GGUF, with edit workflow). — [HF AlperKTS/Qwen-Image-2.1-GGUF](https://huggingface.co/AlperKTS/Qwen-Image-2.1-GGUF); also [HF abenzerps/Qwen-Image-2.1-GGUF](https://huggingface.co/abenzerps/Qwen-Image-2.1-GGUF)
- A setup guide claims a Qwen-Image-2.1 Lightning LoRA (4/8-step) running on 8 GB VRAM + 16 GB RAM, and says 8 GB cards are limited to Q2_K/Q3_K_S. This is a search snippet only; I found no official 2.1 Lightning release. — [MindStudio](https://www.mindstudio.ai/blog/qwen-image-2-1-local-install)

**Other**
- DreamOmni2's ComfyUI node offers INT8 + CPU offload. — [ComfyUI_RH_DreamOmni2](https://github.com/HM-RunningHub/ComfyUI_RH_DreamOmni2). OmniGen2 needs ~17 GB, or <3 GB with slow sequential offload. — [GitHub OmniGen2](https://github.com/VectorSpaceLab/OmniGen2)
- stable-diffusion.cpp runs Z-Image in "as little as 4GB of VRAM" (T2I only; no edit model exists). — [GitHub Tongyi-MAI/Z-Image](https://github.com/Tongyi-MAI/Z-Image)

**Blackwell / Windows**
- Nunchaku issue #888 (2026-01-21): Windows 11, RTX 5070 Ti (sm_120), torch 2.8 cu128 and 2.9.1 cu130, Python 3.12. INT4/AWQ fails with "no kernel image is available for execution on the device", and FP4 models show as "UNKNOWN" in the ComfyUI QwenImageDiTLoader. No maintainer reply in the thread. The reporter says "Nunchaku: 0.16.1 (latest PyPI)". — [nunchaku issue #888](https://github.com/nunchaku-ai/nunchaku/issues/888)
- Nunchaku docs: use FP4 on RTX 50 and INT4 on everything else. — [Nunchaku docs](https://nunchaku.tech/docs/nunchaku/usage/qwen-image-edit.html)

### Inferences
- The spike's ~10.9 GB peak with Qwen-Image-2.1 in diffusers is most likely the 8–9B Qwen3-VL text encoder sharing the GPU with the DiT. Two routes should bring the DiT pass to ~5–6.5 GB, inside 8 GB: keep the encoder on CPU as the 6.14 GiB report did, or run ComfyUI with a GGUF Q5_K_M/Q6_K DiT (4.6–5.5 GB). Steps: without an official 2.1 Lightning LoRA, 40–50 steps would still be slow.
- For Qwen-Image-Edit-2511 on 8 GB Blackwell, the fastest likely path is a Nunchaku/QuantFunc **FP4** r32 or r128 checkpoint with Lightning 4-step and CPU offload. Windows sm_120 support is fragile (#888). "Nunchaku 0.16.1 from PyPI" suggests the reporter may have installed the wrong PyPI package, since official Nunchaku wheels ship from GitHub/HF and are at 1.x. Verify the wheel before assuming the bug still applies.
- GGUF Qwen-Edit on 8 GB will always stream part of the weights (even Q2_K is ~7.4 GB before activations), which fits the ~2 min/image reports. That falls in the "spills" regime the spike already observed.
- FLUX.2 klein 4B distilled FP8/NVFP4 is the only editor with published figures near 8 GB that is also fast (1–2 s on a 5090). Expect several seconds on a laptop 5060, and it may need `--lowvram`.

### Gaps
- No firsthand measurements found for any edit model on an **8 GB RTX 50 laptop**, and none for Klein 4B or Mage-Flow-Edit on any 8 GB card.
- No confirmation of whether Nunchaku issue #888 was fixed in later wheels (1.x) for Windows sm_120.
- No confirmed official Lightning/distilled LoRA for Qwen-Image-2.1.

## 3. Anime/manhwa quality and NSFW: which models handle anime, which are censored, and what community uncensored finetunes/LoRAs exist?

### Takeaway
Qwen-Image-Edit-2511 has the best reputation for keeping an existing anime art style, and it is not actively censored, only undertrained on explicit anatomy. It has the most mature NSFW ecosystem: Phr00t Rapid-AIO NSFW merges, uncensor LoRAs and abliterated text encoders. FLUX.2 klein is actively filtered (IWF-filtered training data plus a safety-tuned text encoder) and tends to redraw anime into its own style. The AniEdit LoRA (Klein 4B/9B, includes drawn nudity) partly fixes both problems. Qwen-Image-2.1 reportedly has only "light content filtering", and a "Heretic" abliterated text encoder already exists.

### Cited Findings
- Qwen-Image-Edit-2511 and Mage-Flow-Turbo "had a good balance between maintaining the art style and executing instructions" on anime. FLUX.2 "redrew the image significantly, changing the art style". — [note.com (2026-07-28)](https://note.com/ai_0049/n/n8051776106dc?hl=en)
- Klein 9B "struggles with anime composition". — [diffusiondoodles](https://diffusiondoodles.substack.com/p/open-source-diffusion-model-summary)
- FLUX.2 klein NSFW: "NSFW filters included in input/output" and "Training data already filtered in partnership with the IWF". Public-figure generation is also restricted. The author's summary: "Blazing fast, but no NSFW" (Jan 2026). — [note.com cute_agapan9087](https://note.com/cute_agapan9087/n/naf0940a4bf9b?hl=en)
- Klein's Qwen3-4B text encoder has safety filtering. A community "uncensored text encoder" exists for Klein 4B. Per search summary, base Klein handles nudity and suggestive poses, but explicit anatomy needs a LoRA. — [HF Cordux/flux2-klein-4B-uncensored-text-encoder](https://huggingface.co/Cordux/flux2-klein-4B-uncensored-text-encoder)
- AniEdit (Klein 4B/9B; v2 targets 9B distilled; published 2026-01-30, updated 2026-03-12): trained on ~1,500 image pairs "that contains NSFW/Drawn nudity". Tasks: real→anime, change clothes, new pose, expression, hairstyle, compose two subjects, style transfer, upscale. Strength 1.0. BFL non-commercial licence. 1,002 likes and "Very Positive" from 98 reviews. — [Civitai AniEdit](https://civitai.com/models/2332320/aniedit-flux-2-klein)
- Qwen-Image (20B) "struggles with NSFW generation". A general NSFW LoRA needs "1,500+ handpicked, high-quality images" at rank ≥128; 100–300 images were not enough (Aug 2025). — [Civitai article 18798](https://civitai.com/articles/18798/qwen-image-nsfw-lora-notes)
- "Qwen-Image-Edit Uncensor+Nudify" LoRA: experimental, trained on ~3k censored→uncensored pairs. — [CivArchive](https://civarchive.com/models/1920220?modelVersionId=2173394)
- Phr00t Qwen-Image-Edit-Rapid-AIO (tagged "Not-For-All-Audiences", Apache-2.0): a merge of accelerators + VAE + CLIP with NSFW and SFW variants, run at CFG 1 and 4 steps. v19 adds "Lightning Edit 2511 8-step" (still recommends 4–8 steps) and the GNASS NSFW LoRA for Qwen 2512. — [HF Phr00t/Qwen-Image-Edit-Rapid-AIO](https://huggingface.co/Phr00t/Qwen-Image-Edit-Rapid-AIO); [HackerNoon summary](https://hackernoon.com/a-beginners-guide-to-qwen-image-edit-rapid-aio-gguf-best-use-cases-limitations-plus-more). There is also a discussion titled "Integrate latest Qwen edit lora to rebalance nsfw". — [HF discussion #152](https://huggingface.co/Phr00t/Qwen-Image-Edit-Rapid-AIO/discussions/152)
- The Rapid-AIO GGUF maintainer recommends the "Qwen2.5-VL-7B-Instruct-abliterated" text encoder. — [HF Phil2Sat GGUF](https://huggingface.co/Phil2Sat/Qwen-Image-Edit-Rapid-AIO-GGUF)
- Community cloud notes say Qwen-Rapid-AIO-NSFW needed 32 GB VRAM on RunPod (an RTX 4090 failed to load it at full precision). — [lilting.ch](https://lilting.ch/en/articles/runpod-qwen-nsfw-notes)
- Anime-oriented Qwen edit LoRAs: "Transform into Anime Style" for 2511 — [Civitai 2429664](https://civitai.com/models/2429664/transform-into-anime-style); chibi/comic/realistic/anime — [Civitai 1967508](https://civitai.com/models/1967508/qwen-image-edit-lora-chibi-comic-realistic-anime); ICEdit LoRA for 2511 — [Civitai 2257887](https://civitai.com/models/2257887/qwen-image-edit-2511-icedit-lora)
- Qwen-Image-2.1 has "light content filtering". Community observers note "decent anatomy understanding and can do various positions". — [eesel review](https://www.eesel.ai/blog/qwen-image-2-1-review)
- "Qwen-Image-2.1 Text Encoder — Heretic" (abliterated Qwen3-VL-8B): 5/100 refusals vs 100/100 for the original, KL 0.022 on benign prompts. ComfyUI NVFP4, W4A8 and GGUF variants are available (ComfyUI ≥0.36.0, CLIPLoader type `qwen_image`). — [HF pottokao/Qwen-Image-2.1-Text-Encoder-Heretic](https://huggingface.co/pottokao/Qwen-Image-2.1-Text-Encoder-Heretic)
- "Qwen2.1_Anime_consistency" LoRA for Qwen-Image-2.1 (experimental): trained on 4-view character model sheets and facial-expression edits. Weight 0.6–0.8. — [HF WarmBloodAban/Qwen-Image-2.1-LoRAs](https://huggingface.co/WarmBloodAban/Qwen-Image-2.1-LoRAs)
- Character LoRAs covering SFW+NSFW exist for Qwen-Image and Z-Image-Turbo (T2I route, not edit). — [Civitai Woman041](https://civitai.com/models/2144960/woman041character-lora-for-consistent-sfw-and-nsfw-content-qwen-image-or-z-image-turbo)

### Inferences
- For an adult RP app, the Qwen edit ecosystem (2511 + Rapid-AIO NSFW / uncensor LoRAs + abliterated text encoder) is the most proven NSFW-capable identity-preserving editor. Qwen-Image-2.1 plus the Heretic encoder is the newest option, but it is a 2-day-old ecosystem under a non-commercial licence.
- Klein is usable for SFW scene changes. For NSFW or anime it needs AniEdit or other LoRAs, and it still tends to restyle anime, which argues for an SDXL/Illustrious style-restoration pass after it (see Q4).
- Nothing in the sources addresses making edit models keep characters visibly adult. That has to be enforced in the app (prompting, reference images, and output checks); the models don't do it.

### Gaps
- No systematic anatomy-degradation comparison (hands, genitals, body proportions) across edit models for NSFW anime.
- No manhwa-specific evaluation found. Mage-Flow-Edit's NSFW/anime behaviour is unknown.
- The full Phr00t model card (version history, known face-drift or zoom issues) could not be read; only metadata loaded.

## 4. Hybrid pipelines: edit model for scene/pose, then SDXL (Illustrious/Pony) img2img/refine for style and detail, or edit model for character sheets only

### Takeaway
Detailed firsthand write-ups of "Qwen/Klein edit → Illustrious/Pony SDXL refine" with numbers were not found in accessible sources. What exists: generic SDXL refinement passes at denoise ~0.1–0.4, restyle img2img at 0.55–0.7, reference-latent chaining for AniEdit, and dedicated character-sheet LoRAs for Qwen-Image-2.1. The pattern is plausible and widely hinted at, but the settings for it are mostly unmeasured.

### Cited Findings
- One Civitai author's refinement workflow uses SDXL (CivitAI generator) or FLUX refinement passes at **denoise 0.1–0.4** (Aug 2025). — [Civitai article 17885](https://civitai.com/articles/17885/my-ai-image-workflow-and-tools-guide)
- An img2img anime restyle graph (Z-Image-Turbo fp8 + anime LoRAs) uses VAEEncode on the source with **denoise 0.55–0.7 at 12 steps**. The AniEdit (Klein) style-transfer workflow chains the same reference latent 2–4 times at 4–6 steps (Sept 2026). — [GitHub issue local-asset-studio #357](https://github.com/Chris0Jeky/local-asset-studio/issues/357)
- There is a published ComfyUI workflow chaining Illustrious/NoobAI-XL with an SDXL photoreal refiner, FaceDetailer, upscaling and inpainting (SDXL-only, no edit model). — [Civitai 1417633](https://civitai.com/models/1417633/ultra-photo-realistic-workflow-or-refiner-upscaling-facedetailer-index-elements-inpainting-controlnet-civitai-metadata-noobai-xlillustrioussdxl-comfyui)
- A "Qwen-Image-Edit Character-Specific Pose and Scene Editing" ComfyUI workflow (Nov 2025, 14 positive reviews) exists, but no SDXL stage or settings are documented. — [Civitai 2126628](https://civitai.com/models/2126628/qwen-image-edit-character-specific-pose-and-scene-editing)
- For character sheets: the Qwen2.1_Anime_consistency LoRA was trained on 4-view model sheets and expression edits. — [HF WarmBloodAban](https://huggingface.co/WarmBloodAban/Qwen-Image-2.1-LoRAs). AniEdit lists "prompt new pose, change expression… convert to 3d model" as supported edits. — [Civitai AniEdit](https://civitai.com/models/2332320/aniedit-flux-2-klein)
- Anime-to-real and real-to-anime conversion LoRAs exist on both sides (e.g. Anime2Reality). — [Civitai article 28911](https://civitai.com/articles/28911/turn-anime-art-into-photorealistic-images-with-anime2reality-lora)

### Inferences
- A reasonable 8 GB pipeline built from these parts:
  1. Run a small/fast editor (Klein 4B + AniEdit, Mage-Flow-Edit Int8, or Qwen-Image-2.1 GGUF with the encoder on CPU) at ~1 MP to place the character in the new scene/pose.
  2. Run the target Illustrious/Pony checkpoint as img2img at ~0.3–0.5 denoise, ideally with the character's SDXL LoRA or an IP-Adapter, to bring back the house style and detail.
  3. Run FaceDetailer/ADetailer on the face.
  Denoise below ~0.3 keeps the editor's style drift; above ~0.55 starts to lose identity and pose, based on the restyle range above. These numbers are inferred, not measured.
- Using the editor only to build a character sheet (turnaround + expressions), then training an SDXL character LoRA from it, keeps generation-time VRAM at SDXL level (well under 8 GB). This is probably the most 8 GB-friendly route when the same character appears many times.

### Gaps
- No firsthand before/after results or identity metrics for "edit model → Illustrious/Pony refine" were found. Reddit, where such posts usually live, was not reachable.
- No data on how much identity survives an SDXL pass at various denoise levels for anime faces.

## 5. Multi-reference: can these models take two character references and put both in one scene consistently?

### Takeaway
Yes, in principle. Qwen-Image-Edit-2509/2511 (1–3 images; 2511 explicitly improved multi-person consistency), Qwen-Image-2.0/2.1 (up to 10 refs), FLUX.2 dev/klein (multi-ref, up to 8–10 on dev), Mage-Flow-Edit (up to 3 in ComfyUI), DreamOmni2 (1–3) and AniEdit on Klein ("compose two subjects") all advertise it. In practice, reliability drops as the number of elements grows, and none of the sources gives quantitative two-character identity results.

### Cited Findings
- Qwen-Image-Edit-2509 supports "person + person" combinations with 1–3 input images. Its example prompt places two people together on a beach while "maintaining consistent lighting, perspective, and natural integration". — [HF Qwen-Image-Edit-2509](https://huggingface.co/Qwen/Qwen-Image-Edit-2509); [Atlabs guide](https://www.atlabs.ai/blog/qwen-image-edit-2509-guide)
- 2511: "Improved Character Consistency: Especially in multi-person scenes, the model better preserves the subject's identity" (secondary summary of the 2511 release). — [z-image.me](https://z-image.me/en/blog/Z-image-edit-is-coming-en); the card itself lists "improved character consistency" — [HF 2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)
- Qwen-Image-2.0/2.1: up to 10 reference images, which "can include character, product, background plate, and style references". — [Comfy blog](https://blog.comfy.org/p/qwen-image-21-in-comfyui-open-weight); [eesel](https://www.eesel.ai/blog/qwen-image-2-1-review)
- FLUX.2 [dev] takes up to 8 reference images. — [diffusiondoodles](https://diffusiondoodles.substack.com/p/open-source-diffusion-model-summary). Klein supports multi-reference composition. — [Comfy blog](https://blog.comfy.org/p/flux2-klein-4b-fast-local-image-editing). A community "Y7 Flux.2 Klein Edit Multi-Ref" node exists. — [comfy.icu](https://comfy.icu/node/Y7Nodes_Flux2KleinEdit_MultiRef)
- AniEdit (Klein) lists "Compose two subjects" as a supported task. — [Civitai AniEdit](https://civitai.com/models/2332320/aniedit-flux-2-klein)
- Mage-Flow-Edit ComfyUI template: "Upload one or more reference images" (up to 3). — [ComfyUI docs](https://docs.comfy.org/tutorials/image/mage-flow/mage-flow). This conflicts with a HackerNoon summary that says a single reference image. — [HackerNoon](https://hackernoon.com/mage-flow-edit-turbo-microsofts-4b-image-editing-model)
- DreamOmni2: 1–3 reference images, and it claims the best identity and pose consistency among open models for subject-driven generation. — [ComfyUI_RH_DreamOmni2](https://github.com/HM-RunningHub/ComfyUI_RH_DreamOmni2); [GitHub DreamOmni2](https://github.com/JIA-Lab-research/DreamOmni2)
- OmniGen2 supports multi-subject in-context generation but warns of object drift. UMO reports less "identity confusion" than OmniGen2 in multi-identity scenes. — [GitHub OmniGen2](https://github.com/VectorSpaceLab/OmniGen2); [UMO overview](https://sonusahani.com/blogs/umo)
- Firsthand: "Simultaneous addition/removal of multiple objects are prone to omissions or malfunctions as the number of elements increases." — [note.com (2026-07-28)](https://note.com/ai_0049/n/n8051776106dc?hl=en)

### Inferences
- Every extra reference image adds latent tokens, so VRAM and time grow with each reference. On 8 GB, two-character composites will push Qwen-Edit-20B further into offload. Klein 4B and Qwen-Image-2.1 GGUF are the more realistic two-reference options.
- For two recurring RP characters, a safer pattern: composite both references at modest resolution, then refine each face separately (inpaint/FaceDetailer with that character's LoRA or reference). This avoids identity blending, which the UMO/OmniGen2 notes flag as a failure mode.

### Gaps
- No measured two-character identity-fidelity results (for anime or photoreal) for any of these models, and no VRAM or time figures for multi-reference runs on 8 GB.
- Not verified whether Qwen-Image-2.1's 10-reference mode works in the GGUF/low-VRAM ComfyUI path.
