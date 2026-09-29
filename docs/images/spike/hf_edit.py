"""Slice-8 probe: one reference picture -> new shots via Qwen-Image-Edit-2511 on HF (wavespeed).

One call per shot, no retries: every call costs money. Key comes from env HF_TOKEN.
"""

import base64
import io
import os
import sys
import time
from pathlib import Path

from huggingface_hub import InferenceClient
from PIL import Image

HERE = Path(__file__).parent
KEEP = (
    "Keep the exact same young man from the reference: same face, same green eyes, same "
    "messy wavy blond hair, same pale skin. Keep the same loose painterly digital-painting "
    "style with visible brush strokes. Plain flat light grey background, nothing else in it."
)
SHOTS = {
    "standing": "Full body, standing, three-quarter view, plain white shirt and dark trousers, "
    "neutral expression, whole figure visible from head to shoes.",
    "coat": "Waist-up portrait, a small warm smile, wearing a dark wool coat.",
    "sitting": "Full body, sitting on the floor, looking back over his shoulder at the viewer.",
}
# follow-up 1: spell out the face and the brushwork, and don't ask for a new expression
STRONG = (
    "Same person as the reference with an identical face: narrow sharp face, high cheekbones, "
    "straight narrow nose, thin lips, heavy-lidded half-closed pale green eyes under low brows, "
    "cool unsmiling expression, androgynous features, pale skin with a pink flush, messy wavy "
    "blond hair falling over the forehead and eyes. Keep the reference's art style exactly: loose "
    "rough painterly brushwork with broad visible strokes, soft blended edges, muted warm palette, "
    "like a digital oil sketch; not clean line art, not vector, not cel shading. "
    "Plain flat light grey background, nothing else in it."
)
MODELS = {"qwen": "Qwen/Qwen-Image-Edit-2511", "flux2": "black-forest-labs/FLUX.2-dev"}

client = InferenceClient(provider="wavespeed", api_key=os.environ["HF_TOKEN"])
buf = io.BytesIO()
Image.open(HERE / "ref.webp").convert("RGB").save(buf, "PNG")
ref = buf.getvalue()
# the hub client sends `image`; wavespeed's edit-2511 wants `images` (a list), so send it too
images = ["data:image/png;base64," + base64.b64encode(ref).decode()]
# usage: hf_edit.py [qwen|flux2] [strong] [shot ...]
args = sys.argv[1:]
model = args.pop(0) if args and args[0] in MODELS else "qwen"
keep = STRONG if args and args[0] == "strong" and args.pop(0) else KEEP
tag = ("" if model == "qwen" else f"{model}_") + ("strong_" if keep is STRONG else "")
for name in args or SHOTS:
    t = time.perf_counter()
    img = client.image_to_image(ref, prompt=f"{keep} {SHOTS[name]}", model=MODELS[model], images=images)
    img.save(HERE / f"edit_{tag}{name}.png")
    print(name, img.size, f"{time.perf_counter() - t:.1f}s", flush=True)
