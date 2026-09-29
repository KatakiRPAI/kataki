# Running image work on this laptop: rules and gotchas

## The one hardware fact

The GPU has **8 GB**. When peak VRAM goes above ~8 GB, Windows spills into shared system RAM and
everything runs **10–400× slower**, from about 1 s per step to 50–145 s per step. Every pipeline
must stay under 8 GB; the current chain peaks at 7.03 GB. Log
`torch.cuda.max_memory_allocated()` for every image (`slice1.peak()`); spills in this spike reached
8.31, 10.86 and 13.23 GB.

## Run protocol (the user's non-negotiables)

1. **Before any run, say the expected time.** Current rates: base ~30 s, hires ~33–40 s, face pass
   ~10–25 s per face, first image of a run +15–30 s warm-up, loading ~5 s.
2. **Check the step rate at a fixed ~30 s after sampling starts**, never "when step N appears".
   A spill makes step N arrive very late, so waiting for it hides the spill; that mistake cost a
   4-minute spill. Healthy is ~1.0–1.3 it/s at ~6.9 GB in `nvidia-smi`.
3. **If steps take tens of seconds, or peak VRAM is above ~8 GB: kill immediately and say why.**
   ```powershell
   Get-CimInstance Win32_Process | ? CommandLine -match '<script>' | % { Stop-Process -Id $_.ProcessId -Force }
   ```
   Then confirm `nvidia-smi` shows ~0 MiB.
4. When something does not work, say so plainly and say what it needs. No false hope.
5. Every experiment ends in a labelled grid (`grid.py`) sent to the user, with seconds per image and peak VRAM.
6. **Never start the user's llama-server.** It shares the GPU.
7. Characters must read clearly adult, in prompts, captions and every character region.

## Environment

- Venv: `.runtime/imgspike/.venv/Scripts/python.exe` (Python 3.12, torch 2.11+cu128, diffusers
  0.41 dev, transformers 5.17, spandrel, ultralytics). A throwaway spike venv, not the engine
  venv; it has no pip, so install with `uv pip install --python <that python> <pkg>`, and say so
  before adding a dependency.
- Env for every run: `HF_HOME=D:\Kataki\.runtime\hf`, `HF_HUB_DISABLE_XET=1`,
  `HF_HUB_DISABLE_SYMLINKS_WARNING=1`, `HF_HUB_DISABLE_TELEMETRY=1`.
- Run long jobs in the background with output to a log (`*> x.log` in PowerShell). The
  `NativeCommandError` line PowerShell adds to that log is stderr wrapping, not a failure.
- Model downloads for testing are pre-approved; keep them under `.runtime/`.

## Gotchas, each paid for once

**Memory**
- Call `enable_model_cpu_offload()` **after** `load_ip_adapter()` and any LoRA load.
- **Never derive a second pipeline with `from_pipe` from an offloaded pipe.** It doubled VRAM and ran
  at 145 s/step. Build siblings from shared weights before offloading
  (`Img2ImgPipeline(**pipe.components)`), then hand the hooks over: `a.remove_all_hooks()` →
  `b.enable_model_cpu_offload()`. Only one pipeline is hooked at a time.
- **Compute IP-Adapter embeddings under `torch.no_grad()`.** Otherwise the embeddings' autograd graph
  pins the 1.26 GB CLIP encoder on the GPU, and the run spilled to 50–65 s/step at 7.9 GB.
- **A full SDXL ControlNet does not fit.** diffusers keeps it on the GPU as one block beside the UNet
  (5.1 + 2.5 GB). Use the T2I-Adapter (~160 MB) instead.
- **Tile the ESRGAN upscaler** (256 px tiles, 16 px overlap). A whole-image 4× pass peaked at 8.31 GB; tiled it uses 0.7 GB.
- IP-Adapter without offload (encoder + SDXL resident) ran 35 min per image at 13.23 GB; with offload, 54 s at 6.45 GB.
- `pipe.vae.enable_slicing()` / `enable_tiling()`, not `pipe.enable_vae_slicing()`.
- Use `torch.Generator("cpu")` with offload.

**Loading**
- `from_single_file` fetches the SDXL base config from HF. If a cache blob goes missing, delete
  `.runtime/hf/hub/models--stabilityai--stable-diffusion-xl-base-1.0` and rerun with `HF_HUB_DISABLE_XET=1`.
- The `.pth` upscalers are not diffusers models; load them with `spandrel`.

**Prompts**
- **CLIP truncates at 77 tokens, silently**, and the part lost is the end of the prompt (the situation). Pony's long quality tags hit this first.
- **`dynamic pose` overrides a pose skeleton** into an action crouch. Leave it out; the skeleton sets the pose.
- **State hair length.** A back view cannot see it in a front-facing reference; "wind" plus a back view grew long hair.
- **WAI adds fake signatures** ("©HANWA") unless the negative has `signature, watermark, text, artist name`.
- Pony needs its score tags plus `source_realistic`, or the output is poor.
- **Clip skip 2 is already the default.** diffusers SDXL with `clip_skip=None` uses the penultimate
  CLIP layer, which is what A1111/Comfy call clip skip 2. Passing `clip_skip=2` would skip two more layers.

**Identity**
- Uniform IP-Adapter scale (0.5) burns the palette (orange/garish casts) and bends poses. Use the block-wise dict.
- A pale, low-contrast reference gives magenta/halftone artifacts. Auto-level and crop the reference first.
- IP-Adapter's layout block (down `block_2`) also pulls pose from the reference. With a skeleton, drop it to 0.35 and raise the pose adapter to 1.4.
- The T2I-Adapter OpenPose was trained on base SDXL. It works on WAI and breaks anatomy on Pony Realism.
