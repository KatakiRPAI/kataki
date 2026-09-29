"""Background bake-off: one place prompt, three HF text-to-image models (wavespeed), 1 image each.

No retries: every call costs money. Key comes from env HF_TOKEN.
"""

import os
import sys
import time
from pathlib import Path

from huggingface_hub import InferenceClient

HERE = Path(__file__).parent
PROMPT = (
    "Realistic fantasy illustration, painterly and realistic like a fantasy book cover or game key art. "
    "Interior of a cosy harbour tavern in the evening: low timber beams, a long worn wooden bar "
    "with bottles and tankards, a stone hearth with a fire, round tables and stools, fishing nets "
    "and lanterns on the walls, rain-streaked windows looking out on the harbour. Empty of people. "
    "Wide establishing shot at eye level, warm lamplight, rich detail."
)
MODELS = {
    "qwen": "Qwen/Qwen-Image",
    "zturbo": "Tongyi-MAI/Z-Image-Turbo",
    "schnell": "black-forest-labs/FLUX.1-schnell",
}

client = InferenceClient(provider="wavespeed", api_key=os.environ["HF_TOKEN"])
for name in sys.argv[1:] or MODELS:
    t = time.perf_counter()
    img = client.text_to_image(PROMPT, model=MODELS[name], extra_body={"size": "1536*864"})
    img.save(HERE / f"bg_{name}.png")
    print(name, img.size, f"{time.perf_counter() - t:.1f}s", flush=True)
