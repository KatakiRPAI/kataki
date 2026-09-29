"""Bully rain shot ignored the running skeleton. Base-only test: stronger pose adapter vs weaker IP layout block."""
import time, torch
from diffusers import (StableDiffusionXLPipeline, StableDiffusionXLAdapterPipeline, EulerAncestralDiscreteScheduler,
                       T2IAdapter)
from PIL import Image
from slice1 import NEW, peak, OUT
from slice3 import SIT
from char_test import CHARS
from grid import grid

N, C = NEW["wai"], CHARS["bully"]
tag, sit, seed = [s for s in SIT if s[0] == "rain"][0]
sit = sit.replace("dynamic pose, ", "")
VARIANTS = [(f"no dynamic pose, seed {s}", 1.4, 0.35, s) for s in (303, 305, 306)]


def main():
    embeds = [e.to("cuda") for e in torch.load(f"{OUT}/ct_bully_embeds.pt")]
    pipe = StableDiffusionXLPipeline.from_single_file(N["ckpt"], torch_dtype=torch.float16)
    pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models",
                         weight_name="ip-adapter-plus_sdxl_vit-h.safetensors", image_encoder_folder=None)
    adapter = T2IAdapter.from_pretrained("TencentARC/t2i-adapter-openpose-sdxl-1.0", torch_dtype=torch.float16)
    t2i = StableDiffusionXLAdapterPipeline(**pipe.components, adapter=adapter)
    del pipe
    t2i.scheduler = EulerAncestralDiscreteScheduler.from_config(t2i.scheduler.config)
    t2i.enable_model_cpu_offload()
    t2i.vae.enable_tiling()
    for i, (name, pose_s, layout, seed) in enumerate(VARIANTS):
        t2i.set_ip_adapter_scale({"down": {"block_2": [0.0, layout]}, "up": {"block_0": [0.0, 0.2, 0.0]}})
        torch.cuda.reset_peak_memory_stats(); t = time.time()
        t2i(prompt=f"{N['qual']}, {C['char']}, {sit}", negative_prompt=N["neg"], image=Image.open(f"{OUT}/pose_rain.png"),
            adapter_conditioning_scale=pose_s, width=832, height=1216, ip_adapter_image_embeds=embeds,
            num_inference_steps=N["steps"], guidance_scale=N["cfg"],
            generator=torch.Generator("cpu").manual_seed(seed)).images[0].save(f"{OUT}/pf2_{i}.png")
        print(f"[pf] {name} {time.time()-t:.1f}s peak {peak():.2f}GB", flush=True)
    grid([("rain", [f"{OUT}/pose_rain.png", C["ref"], f"{OUT}/ct_bully_rain_base.png"] +
                   [f"{OUT}/pf2_{i}.png" for i in range(len(VARIANTS))])],
         ["skeleton", "reference", "before"] + [v[0] for v in VARIANTS], f"{OUT}/grid_posefix2.png", cell=340)
    print("DONE")


if __name__ == "__main__":
    main()
