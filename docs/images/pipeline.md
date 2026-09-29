# The render chain

The current best recipe for one character image, as it runs in `char_test.py`. Every number here
was measured on the target laptop; see [findings.md](findings.md) for how each was chosen and
[rules-and-gotchas.md](rules-and-gotchas.md) before running anything.

## The flow

```
one approved picture ──► reference prep ──► IP-Adapter embedding (once per character, 1.3 MB .pt)
                                                        │
prompt (quality + character + situation) ─┐             ▼
pose skeleton (optional) ─────────────────┼──► 1. base render   832×1216, block-wise IP-Adapter, T2I pose adapter
                                          │             │
                                          │             ▼
                                          └──► 2. hires          model upscale → 1.5×, img2img, adapter at 0
                                                        │
                                                        ▼
                                               3. face pass      detect face → crop → img2img → paste face box
                                                        │
                                                        ▼
                                                  finished image  (~1–2 min, peak ≤ 7.03 GB)
```

### 0. Once per character: reference prep and embedding

1. Take the approved picture. Crop to head and shoulders (x 10–90 %, y 0–55 %) and
   `ImageOps.autocontrast(cutoff=1)`. A pale, low-contrast reference makes IP-Adapter produce
   magenta/halftone artifacts, and the crop keeps the embedding about the face.
2. Load the CLIP ViT-H encoder, compute `pipe.prepare_ip_adapter_image_embeds(ref, None, "cuda", 1, True)`
   **inside `torch.no_grad()`**, `torch.save` the result, then drop the encoder and reload the
   embeddings from disk. Assert < 0.5 GB still allocated before going on.
3. From then on, load the adapter with `image_encoder_folder=None` and pass
   `ip_adapter_image_embeds=`. The 1.26 GB encoder never sits on the GPU during rendering.

### 1. Base render

- Pipeline: `StableDiffusionXLAdapterPipeline` (T2I-Adapter), built as
  `StableDiffusionXLAdapterPipeline(**pipe.components, adapter=adapter)` from a
  `from_single_file` checkpoint, then `enable_model_cpu_offload()`, `vae.enable_tiling()`.
- IP-Adapter: `h94/IP-Adapter`, `ip-adapter-plus_sdxl_vit-h.safetensors`, scale set **block-wise**:

  | Shot | IP-Adapter scale | Pose adapter (`adapter_conditioning_scale`) |
  |---|---|---|
  | No pose preset | `{"down": {"block_2": [0.0, 0.6]}, "up": {"block_0": [0.0, 0.2, 0.0]}}` | 0.0 with a black image |
  | With a pose skeleton | same, but down `block_2` → **0.35** | **1.4** |

  Down `block_2` carries layout (it holds the character's shape, and also pulls pose); up
  `block_0` carries style/palette (kept near zero so colours follow the prompt, not the reference).
- Pose: `TencentARC/t2i-adapter-openpose-sdxl-1.0` (~160 MB), fed an OpenPose-format skeleton.
  Skeletons come from `posefx.skeleton()` (YOLO-pose keypoints drawn in OpenPose colours).
- 832×1216, Euler a, the style's steps/CFG (table below), `torch.Generator("cpu")` seeded.

### 2. Hires

1. Model-upscale 4× with the style's ESRGAN model **in 256 px tiles** (`slice1.esrgan`), then
   Lanczos-resize to 1.5× of the base (1248×1824).
2. img2img: `StableDiffusionXLImg2ImgPipeline(**pipe.components)`, Euler a, 20 steps at the style's
   strength. IP-Adapter scale **0**, but still pass `ip_adapter_image_embeds`. The diffusers UNet
   source raises without image embeds once adapter weights are loaded (read from source; never
   tried without).
3. Before this step: `t2i.remove_all_hooks()` then `i2i.enable_model_cpu_offload()`. Only one
   pipeline holds offload hooks at a time.

### 3. Face pass (hand-rolled ADetailer)

`slice2_pose.face_pass()`: for each face found by `face_yolov8n.pt` (conf 0.3):
1. Pad the box 32 px (context only), crop, resize so the long side is 1024.
2. img2img at strength 0.4, 20 steps, same prompt, IP-Adapter at 0.
3. Resize back and paste **only the face box**, feathered by an 8 px Gaussian mask.
   Pasting the whole padded crop left smudges in the background.

## Settings per style

| | WAI-Illustrious v17 (anime, **default**) | Pony Realism v2.2 (photoreal) |
|---|---|---|
| Checkpoint | `.runtime/models/waiIllustriousSDXL_v170.safetensors` | `.runtime/models/ponyRealism_V22.safetensors` |
| Quality tags | `masterpiece, best quality, amazing quality` | `score_9, score_8_up, score_7_up, source_realistic, photorealistic` |
| Negative | `bad quality, worst quality, worst detail, sketch, censor, signature, watermark, text, artist name, child` | `score_4, score_5, score_6, cartoon, anime, 3d, cgi, doll, signature, watermark, text, child` |
| Sampler | Euler a (`EulerAncestralDiscreteScheduler`) | Euler a |
| Steps / CFG | 28 / 6.0 | 30 / 6.5 |
| Clip skip | default (see gotchas) | default = "clip skip 2" |
| Upscaler | `RealESRGAN_x4plus_anime_6B.pth` | `4x-UltraSharp.pth` |
| Hires strength | 0.40 | 0.30 |

The quality/negative tags are the checkpoint creators' own, plus the watermark and `child` guards.
A third checkpoint, `novaAnimeXL_ilV190`, is installed; it came out warmer and softer than WAI,
and bled pink in colourful scenes, so it is not in use.

## Writing prompts

Prompt = `{quality}, {character}, {situation}`, all Danbooru-style tags.

- **Character tags** describe what never changes: `1boy, young man, adult, early 20s`, then
  **hair length**, hair colour, eyes, build, fixed accessories. State hair length even when the
  picture shows it: a back view cannot see it in the reference and will invent long hair.
- **Situation tags** carry what changes: pose, outfit, place, light, camera (`from above`,
  `from behind, looking back over shoulder`, `cowboy shot`, `full body`, `medium shot`).
- Keep expressions in the situation, not the character (`laughing` fights a character-level `smirk`).
- **77 CLIP tokens is a hard ceiling.** Past it, diffusers silently cuts the end of the prompt,
  which is the situation. `char_test.py` asserts every prompt fits before loading anything.
- Every character must read clearly adult: `adult, early 20s` in the character tags, `child` in the negative.

## Code map

Reference copies in [`spike/`](spike/); runnable originals in `.runtime/imgspike/` (gitignored).

| File | What it holds |
|---|---|
| `char_test.py` | **The full chain** for one character in the 4 test situations. `python char_test.py bully` (or `pony_prince`, `pony_bully`). Characters, pose settings, token guard live here |
| `slice1.py` | Style settings (`NEW`), the tiled `esrgan()` upscaler, `peak()`; the old-vs-new recipe comparison |
| `slice3.py` | The 4 test situations and seeds (`SIT`), the block-wise scale (`BLOCK`); the 4-way identity comparison |
| `slice2_pose.py` | `face_pass()`; the first pose + face fix run on the WAI prince |
| `posefx.py` | `faces()` (YOLO face boxes) and `skeleton()` (YOLO-pose → OpenPose drawing). `python posefx.py` re-runs the detector check |
| `pose_fix.py` | The pose-scale / layout-block / seed experiments on the bully's rain shot |
| `grid.py` | `grid()`, the labelled comparison sheet every experiment ends in |
| `gen_ckpt.py` | The original cast (`FLAVORS`, `SHOTS`) that slice 1 compares against |
| `pose_rain.png`, `pose_roof.png` | The two skeletons in use (running, back view looking over the shoulder) |

Models on disk (all under `.runtime/models/`): the three checkpoints; `upscale/` (two ESRGAN
`.pth`, loaded with `spandrel`); `detect/` (`face_yolov8n.pt` from `Bingsu/adetailer`,
`yolo11n-pose.pt` from ultralytics). HF downloads (`h94/IP-Adapter`, the T2I-Adapter, the SDXL
base config) cache under `.runtime/hf`.
