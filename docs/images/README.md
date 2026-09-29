# Character images: where we are

**In the app now (2026-09-23): pictures through HuggingFace.** The M3 spec's §7 amendment (the
HuggingFace slice, tasks H1–H5) is built. Z-Image-Turbo draws place backgrounds and first
character pictures. Qwen-Image-Edit-2511 makes a character's five expressions from their one
picture, and RMBG-2.0 cuts each out. The stage shows the expression the memory model picks for
each line. All of it is plain HTTPS in `engine/src/kataki/images.py`, with no GPU. The
findings are in [findings.md](findings.md) (the "via HF" and "task H" sections). The local
pipeline below is still a spike and not an app backend.

Local image generation for Kataki (milestone M3), worked out as a see-it-first spike on the
target laptop (RTX 5060 Laptop, **8 GB VRAM**, 32 GB RAM, Windows). Last updated 2026-09-23.

**The short answer so far:** one approved picture of a character is enough to keep that character
recognisable across very different scenes, poses, outfits and lighting. It takes about **1–2
minutes per finished image** and stays under 8 GB, all local, in the anime style (WAI-Illustrious).
Identity comes from a **block-wise IP-Adapter** built from that one picture; poses come from
**OpenPose skeletons**; polish comes from the checkpoint creator's own sampler, a **1.5× model
upscale** and a **face-detail pass**. Photoreal (Pony Realism) holds identity less well, and its
pose control does not work yet.

## Read by task

| You are about to… | Read |
|---|---|
| Render anything, or change a setting | [pipeline.md](pipeline.md): the render chain, exact settings per style, code map |
| Run anything on the GPU | [rules-and-gotchas.md](rules-and-gotchas.md): the run protocol and every trap already paid for |
| Decide what to try next, or answer "did we test X?" | [findings.md](findings.md): every experiment, its numbers, its grid, its verdict |
| Plan the app feature | [Where this is going](#where-this-is-going) below, then the M3 spec |

Background research, with sources: [`docs/research/reports/Consistent character images locally.md`](../research/reports/Consistent%20character%20images%20locally.md)
(and its raw notes in `research_notes/`). The 9-slice plan that the spike follows came from that
report; its slice numbers are used throughout these docs.

## Status by slice

| # | Slice | State |
|---|---|---|
| 1 | Creator recipe + 1.5× model-upscale hires | **Done** (WAI + Pony) |
| 2 | Face-detail pass (hand-rolled ADetailer) | **Done** (WAI; ran on Pony too) |
| 3 | Identity bridge: tuned IP-Adapter from one picture | **Done**. Block-wise wins. Two WAI characters pass; Pony passes moderately |
| — | Pose control (added; not in the original plan) | **Works on WAI** (T2I-Adapter OpenPose). **Fails on Pony** |
| 4 | ~40-image dataset per character (the "character sheet") | Not started |
| 5 | Train a per-character LoRA on the laptop | Not started |
| 6 | LoRA vs bridge decision | Not started |
| 7 | Two characters in one image | Not started |
| 8 | Escalations (ComfyUI, Qwen-Image-Edit) if 7 fails | Only if needed |
| 9 | App wiring + M3 spec amendment | **Done for HuggingFace** (spec §7, H1–H5). The local pipeline is not wired |

Open items, in the order they bite:
- **Pony pose control.** The skeleton broke the rain shot's anatomy and was ignored in bed/roof.
  Needs a Pony-compatible pose ControlNet or a lower pose scale.
- **Pony bully run** was cut off after one image. Re-run `char_test.py pony_bully`.
- **Pose preset library.** The two skeletons in use were extracted from earlier renders and are mild.
  The app needs strong, deliberate skeletons (sprint, back view, lying on back, sitting…).
- **Face pass on truly small faces** (wide full-body shots) is untested. Every test face was already large.

## Where this is going

The product flow the user wants. **This is a concept: build it only when the user says so.**

1. A creator makes a character and provides **one picture**.
2. Once they confirm it, the app generates a **full character sheet** from it (the slice-4 dataset)
   and whatever it needs for consistency (the slice-3 embedding now; a slice-5 LoRA later).
3. Story scenes are rendered from the sheet, never from the previous scene, so the face does not drift.
4. When the user gives a generated image a **thumbs-up**, it is added to the sheet as a future
   reference. The sheet grows, and a grown sheet is the natural trigger to retrain the LoRA.

Until a LoRA exists, the block-wise IP-Adapter serves scenes from the one picture (the "bridge").
Training is expected to take 40–90 min per character on this laptop (an estimate; not yet
measured), so it belongs in an idle or overnight "lock this character" job.

**Resolved for the HuggingFace path by the §7 amendment (approved 2026-09-23). Still true for the local pipeline:** the M3 spec is out of date on two points. [`docs/specs/2026-09-21-m3-images.md`](../specs/2026-09-21-m3-images.md)
forbids diffusers/torch as engine dependencies and assumes ComfyUI or OpenAI-compatible backends.
Everything here runs on diffusers. Write a short spec amendment and get the user's approval before
any image work touches `engine/`.

## What is in this folder

- `spike/`: reference copies of the working scripts and the two pose skeletons. The runnable
  originals, the venv, the models and every output image live in `.runtime/imgspike/`, which is
  gitignored and exists only on the dev laptop.
- `grids/`: the comparison grids the decisions were made from (JPG copies). [findings.md](findings.md) links each one.
