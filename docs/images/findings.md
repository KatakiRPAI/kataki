# Findings: every experiment and its verdict

In the order they ran. Times are per image on the RTX 5060 Laptop (8 GB), warm unless noted.
"Peak" is `torch.cuda.max_memory_allocated()`. Grids are in [`grids/`](grids/).

## Before the plan: choosing models (2026-09-21/22)

| Tried | Result | Verdict |
|---|---|---|
| **Qwen-Image-2.1**, 4-bit (bitsandbytes), 7B | Works on Blackwell. Native RGBA transparency. Editing a base image into new scenes kept the face (neon street, selfie). Pose/gaze only partly honoured. ~2 min/image, **10.86 GB peak (spilling)** | Strong identity, too slow and heavy per scene. Candidate for dataset generation (slice 4) with its text encoder on CPU (a community report says ~6.1 GB; untested here) |
| **NoobAI-XL 1.1** (SDXL anime) | Good anime look; 9.53 GB peak without offload | Superseded by Civitai checkpoints |
| **IP-Adapter-plus** on SDXL, first try | Identity held across bar/street/fight scenes, but the palette bled (a daytime scene stayed neon-purple). **35 min/image at 13.23 GB** until `enable_model_cpu_offload()`, then **54 s at 6.45 GB**, ~25 s batched warm | The mechanism works; offload is mandatory |
| Pale reference at IP-Adapter 0.55 | Magenta/halftone glitches | Auto-level the reference and use a clothed, higher-contrast base |
| Civitai checkpoints, same cast and seeds | **WAI-Illustrious v17**: crispest, least bleed. **Nova Anime XL**: warmer, softer, pink bleed. **Pony Realism v2.2**: genuinely photoreal. All ~25–30 s at 6.45 GB | **WAI = anime default (the user's pick); Pony Realism = photoreal lane** |
| Hires via `from_pipe` on an offloaded pipe | Doubled VRAM, **145 s/step** | Killed. One shared-weights img2img pipe instead |
| SDXL-Lightning few-step LoRA (28→8 steps), `gen_speed2.py` | Ran; output `speed_lightning8.png`; never judged side by side | Open speed lever for a later "fast mode" |

The user's observation that started the plan: our images looked far less pretty than Civitai
galleries. The research (`reports/Consistent character images locally.md`) found two causes. The
galleries use no reference adapter, and they apply each creator's own sampler/hires recipe plus a
face-detail pass.

## Slice 1: creator recipe + model-upscale hires (2026-09-23)

`slice1.py`: old chain (1.3× Lanczos, DPM++ 2M Karras, 0.35) vs the creators' recipes (Euler a,
creator tags, 1.5× ESRGAN, img2img 0.4 WAI / 0.30 Pony). Same seeds, both styles.
Grids: [full](grids/grid_s1.jpg), [pixel zoom](grids/grid_s1_zoom.jpg).

- Base ~31 s at 5.58 GB; new hires ~36 s at 6.16 GB. **~67 s for a finished image.**
- The first run peaked at **8.31 GB** from a whole-image 4× upscale and was killed. The tiled upscaler uses 0.7 GB, and hires got faster (50 → 36 s).
- **Sharper, modestly:** crisper hair strands, cleaner line art (WAI), finer skin texture (Pony).
  The bigger change is the look: softer, back-lit, more painterly light on WAI.
- The Pony prince came out older (mid-30s), partly because the Pony prompt ran past 77 tokens.

## Slice 3: identity from one picture, 4 situations (2026-09-23)

`slice3.py`: the WAI prince in 4 situations, each changing pose, outfit, light and camera:
café sitting and laughing; lying on a bed seen from above; running in neon rain, full body; from
behind, looking back over the shoulder, rooftop at sunset. Four identity modes at the same seed.
Grid: [grid_s3](grids/grid_s3.jpg).

| Mode | Same person? | Colours follow the scene? |
|---|---|---|
| No adapter | **No**: long hair in the café, a different face each time | Yes |
| Uniform 0.5 | Roughly | **No**: burnt orange, garish, darkened skin; poses bent |
| **Block-wise** | **Yes**: hair, bangs, eyes, face in every shot | **Yes** |
| Block-wise + stop at 65 % | Same as block-wise | Nearly identical to block-wise, so dropped |

- Base ~29 s at 6.45 GB, hires ~33 s at 7.03 GB. Embedding 1.3 MB.
- Flaws found: "running" came out as a crouch, the back view came out as a three-quarter view, and small faces were soft.

## Pose control + face pass (2026-09-23)

`posefx.py`, `slice2_pose.py`. Grids: [before/after](grids/grid_s2p.jpg), [face close-ups](grids/grid_s2p_faces.jpg).

- **Detectors:** `face_yolov8n.pt` found exactly one face in **18/18** WAI images, including a profile and a small face.
  YOLO-pose found 18/18 keypoints on the runner and 12/18 on the cropped back view.
- **Skeletons were extracted from the no-adapter renders** that already had the right poses, then
  applied through the T2I-Adapter to the block-wise renders. Peak 6.67 GB; the full ControlNet was
  rejected on memory before trying.
- Result on the WAI prince: **actually running, and a true back view with the head turned**, same person.
- Two regressions, both fixed: the back view grew long hair (added `short hair`); the face pass smudged
  the crop edge and WAI added a fake signature (paste only the face box; watermark negatives).
- The face pass gives cleaner eyes, lashes and brows. The gain is modest because these faces were already large after hires. ~17–25 s per face.

## Second WAI character: the bully (2026-09-23)

`char_test.py bully`. Grid: [grid_ct_bully](grids/grid_ct_bully.jpg).

- **Identity holds**: messy black hair and bangs, earrings, sharp eyes, fanged grin, even a small
  white streak, across all 4 situations. Colours follow each scene; reads clearly adult.
- ~29 s base + ~33 s hires + ~13 s face at 7.03 GB.
- The first run spilled (50–65 s/step, 7.9 GB): the embeddings were computed without `no_grad`
  and pinned the encoder. The rerun was normal after the fix.
- Rain shot crouched despite the skeleton. `pose_fix.py`, grid [grid_posefix2](grids/grid_posefix2.jpg):
  - Pose 1.4 and/or layout block 0.35 alone: closer (a forward dash), still low to the ground.
  - **Removing `dynamic pose` from the prompt: upright on 3/3 seeds** (303, 305, 306).
    It reads as a fast walk because the borrowed skeleton is a mild stride.
- Bed shot: lying, but more on his front than on his back.

## Photoreal: Pony Realism (2026-09-23)

`char_test.py pony_prince` (prompts trimmed to ≤ 77 tokens). Grid: [grid_ct_pony_prince](grids/grid_ct_pony_prince.jpg).

- **Identity holds moderately**: same dirty-blond tousled hair, blue eyes and face in café and bed;
  thinner and less sure in rain and on the roof. Colours follow the scenes; photoreal; adult (reads late 20s–30s, inherited from the reference).
- **Pose control fails on Pony.** Rain: twisted, broken anatomy, not running. Bed: sitting, "from above" ignored.
  Roof: back view, but the head is in profile instead of looking back. Café: a smirk, not laughing.
- Timings as WAI: base ~30 s, hires ~31 s, face ~10–19 s, peak 7.03 GB.
- `pony_bully` was interrupted after its first image; not yet judged.

## Hosted edit model: Qwen-Image-Edit-2511 via HF (2026-09-23)

`spike/hf_edit.py`, HF Inference Providers → wavespeed, one user-supplied painterly reference
(a face crop), 3 shots on a plain grey background. Grid: [grid_hf_edit](grids/grid_hf_edit.jpg).

- **Poses and bodies: excellent.** Full-body standing, and sitting while looking back over the
  shoulder, with clean anatomy and hands. No skeleton was needed. The body was invented, since the reference is a face crop.
- **Hair and eye colour kept; the face mostly not.** The reference's sharp, androgynous, heavy-lidded
  face became a generic handsome young man. The smiling coat shot reads as a different person.
- **Style lost.** Loose painterly brushwork became clean digital illustration, even with the prompt asking for it.
- Flat backgrounds came out clean, which makes them good for a transparent cutout.
- 9–16 s per image, $0.03 per image (wavespeed). The HF client sends `image`; this endpoint needs
  `images` (a list), passed through kwargs. Without it the call is a 400.

Follow-ups on the standing shot, one image each. Grids: [grid_hf_edit2](grids/grid_hf_edit2.jpg),
faces [grid_hf_edit2_faces](grids/grid_hf_edit2_faces.jpg).

- **Qwen with the face and brushwork spelled out (`hf_edit.py qwen strong`)**: the face gets much closer:
  heavy-lidded eyes, flush, androgynous, hair over the forehead. The style is still clean illustration,
  not painterly. There's a faint smudge artefact by the feet. 9.5 s, $0.03. **Prompting fixes the face, not the style.**
- **FLUX.2-dev (`hf_edit.py flux2`, same prompt as the first run)**: **keeps the painterly style**
  (soft, brushy). But the hair turns brassy yellow, the eyes go neon green, the hands are smeared,
  and he **reads younger** than the reference. 55 s, $0.024.

## Place backgrounds from text via HF (2026-09-23)

`spike/hf_bg.py`: one realistic-fantasy tavern prompt ("empty of people"), 1536×864, wavespeed,
1 image per model. Grid: [grid_bg_bakeoff](grids/grid_bg_bakeoff.jpg).

- **Qwen-Image** ($0.02, 27 s): rich and painterly-real, but the far wall opens straight onto the
  harbour water, and a small figure may have crept in by the boat.
- **Z-Image-Turbo** ($0.005, 5 s): the most believable room: rain on real windows, a hearth, a bar,
  and open floor in the middle where sprites can stand. **Best fit.**
- **FLUX.1-schnell** ($0.003, 9 s): more game-art, saturated orange/teal; the fire is built into the bar.
- Size goes through `extra_body={"size": "W*H"}` (wavespeed); `text_to_image` has no `size` argument.

## Place prompts for Z-Image-Turbo in the app (2026-09-23, task H2)

Z-Image-Turbo takes every word literally and **ignores "no"**. Mentioning something
unwanted adds it. The first place prompts through the app, all on the Gull
("A smoky dockside tavern. Lamplight, pipe smoke, rain on the windows, a harbour bell far off"):

- Name + description → **a gull smoking a pipe** on a tavern roof, outside, with a giant bell.
- Adding "no people", and "called 'The Gull', do not draw the name" → **a sign reading "The Gull"**
  and a terrace full of drinkers.
- "unoccupied empty room as a stage backdrop" → an empty interior, but a literal **theatre stage**.
- **Fix:** the name is never in the prompt, and only wanted things are described. It says "An unoccupied, empty room,
  interior view" when the name or description has a building word (tavern, inn, hall…), and otherwise
  "A deserted, unoccupied place". Result: [grid_h2_places](grids/grid_h2_places.jpg). The Gull is an empty
  lamplit room with rain on the windows; Harbour Market is deserted stalls on the harbour wall.

## A character's look in the app (2026-09-23, task H3)

Mira from the demo ("Guild courier. Loyal to friends, wary of everyone else."), drawn and packed
through the app. Grid: [grid_h3_mira_pack](grids/grid_h3_mira_pack.jpg).

- **The first draft was modern**: a baseball cap and a zip-up work shirt, because "courier" reads as today.
  The portrait prompt now says "a character from a medieval fantasy world, in period clothing".
  The redraw gave leather pauldrons, a satchel strap and a braid.
- **The pack holds her identity completely**: 5 Qwen-Image-Edit-2511 edits of the portrait, each cut out
  by RMBG-2.0 (fal). Same face, braid, outfit and pose. Only the expression changes, and all five read
  clearly. The cutouts are clean (RGBA, 888×1184). All 10 calls ran concurrently in ~30 s. It cost $0.24.

## On stage, with a face that fits the line (2026-09-23, task H4)

A real chat in the Gull with Qwen3.5-9B through HF on every text job. After each of Mira's replies,
the memory reader's model picks one of her five sprites against a closed JSON schema.
Stage: [h4_stage_doubtful](grids/h4_stage_doubtful.jpg).

- "*stares at the compass as if it were a loaded coin, her eyes narrowing*…" → **wary**.
- "Pawnshop? That's the lie you tell the street walkers, Aren…" → **doubtful**. The stage
  showed her doubtful cut-out, lit like the room.
- Each pick is one small non-streamed call, a fraction of a cent. Someone without sprites costs no extra call.

## What is settled, and what is not

**Settled** (WAI): the block-wise IP-Adapter holds a character from one picture across scene, outfit,
light and camera; the creator recipe + tiled 1.5× hires + face pass is the polish chain; pose
comes from skeletons via the T2I-Adapter; everything fits in 7.03 GB at ~1–2 min per image.

**Not settled:** pose control on Pony; a real pose preset library; the face pass on small faces;
whether a per-character LoRA (slices 4–5) beats the bridge; two characters in one image (slice 7);
LoRA training time on 8 GB (research estimate 40–90 min, unmeasured).
