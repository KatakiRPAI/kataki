"""Consistency test (plan slice 3, pulled forward): one WAI character in 4 situations (pose/outfit/light/angle),
4 identity configs at the same seed: none, uniform 0.5, block-wise, block-wise + stop at 65%.
Reference embedding precomputed once; encoder dropped before generation. Hires (slice 1 chain) with adapter at 0.
"""
import os, time, torch
from diffusers import (StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline, EulerAncestralDiscreteScheduler)
from transformers import CLIPVisionModelWithProjection, CLIPImageProcessor
from PIL import Image, ImageOps
from slice1 import NEW, esrgan, peak, OUT
from grid import grid

N = NEW["wai"]
CHAR = "1boy, solo, young man, adult, early 20s, short hair, blonde hair, blue eyes, soft handsome features, bishounen, manhwa style"
REF = f"{OUT}/s1_wai_prince_newbase.png"
EMB = f"{OUT}/s3_prince_embeds.pt"
SIT = [  # tag, situation, seed
    ("cafe",  "sitting at a cafe table, laughing, holding a coffee cup, knit sweater, daytime, window light, medium shot", 301),
    ("bed",   "lying on back on bed, holding a phone above face, from above, t-shirt, night, dim lamp light", 302),
    ("rain",  "running in the rain, full body, wet hair, hoodie, jeans, city street at night, neon lights, reflections", 303),
    ("roof",  "from behind, looking back over shoulder, standing on a rooftop, sunset, black suit, wind, cowboy shot", 304),
]
BLOCK = {"down": {"block_2": [0.0, 0.6]}, "up": {"block_0": [0.0, 0.2, 0.0]}}
CONFIGS = [("none", 0.0, False), ("uniform 0.5", 0.5, False), ("block-wise", BLOCK, False), ("block + stop 65%", BLOCK, True)]


def main():
    ref = Image.open(REF).convert("RGB")
    ref = ImageOps.autocontrast(ref.crop((int(ref.width * .1), 0, int(ref.width * .9), int(ref.height * .55))), cutoff=1)
    ref.save(f"{OUT}/s3_ref.png")

    pipe = StableDiffusionXLPipeline.from_single_file(N["ckpt"], torch_dtype=torch.float16)
    enc = CLIPVisionModelWithProjection.from_pretrained("h94/IP-Adapter", subfolder="models/image_encoder",
                                                        torch_dtype=torch.float16).cuda()
    pipe.image_encoder, pipe.feature_extractor = enc, CLIPImageProcessor()
    pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models",
                         weight_name="ip-adapter-plus_sdxl_vit-h.safetensors", image_encoder_folder=None)
    embeds = pipe.prepare_ip_adapter_image_embeds(ref, None, "cuda", 1, True)
    torch.save([e.cpu() for e in embeds], EMB)
    pipe.image_encoder = None
    del enc
    torch.cuda.empty_cache()
    embeds = [e.to("cuda") for e in torch.load(EMB)]
    print(f"[s3] embeds saved {os.path.getsize(EMB)/1e6:.1f}MB, encoder dropped", flush=True)

    i2i = StableDiffusionXLImg2ImgPipeline(**pipe.components)
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()

    steps = N["steps"]
    for tag, sit, seed in SIT:
        for ci, (cname, scale, stop) in enumerate(CONFIGS):
            pipe.set_ip_adapter_scale(scale)

            def cb(p, i, t, kw):
                if stop and i == int(steps * 0.65):
                    p.set_ip_adapter_scale(0.0)
                return kw
            torch.cuda.reset_peak_memory_stats(); t = time.time()
            pipe(prompt=f"{N['qual']}, {CHAR}, {sit}", negative_prompt=N["neg"], width=832, height=1216,
                 ip_adapter_image_embeds=embeds, num_inference_steps=steps, guidance_scale=N["cfg"],
                 callback_on_step_end=cb, generator=torch.Generator("cpu").manual_seed(seed)
                 ).images[0].save(f"{OUT}/s3_{tag}_{ci}_base.png")
            print(f"[s3] {tag} / {cname} base {time.time()-t:.1f}s peak {peak():.2f}GB", flush=True)

    pipe.remove_all_hooks()
    i2i.enable_model_cpu_offload()
    i2i.scheduler = EulerAncestralDiscreteScheduler.from_config(i2i.scheduler.config)
    i2i.set_ip_adapter_scale(0.0)
    for tag, sit, seed in SIT:
        for ci, (cname, _, _) in enumerate(CONFIGS):
            torch.cuda.reset_peak_memory_stats(); t = time.time()
            big = esrgan(N["up"], Image.open(f"{OUT}/s3_{tag}_{ci}_base.png").convert("RGB"), 1.5)
            i2i(prompt=f"{N['qual']}, {CHAR}, {sit}", negative_prompt=N["neg"], image=big, strength=N["strength"],
                ip_adapter_image_embeds=embeds, num_inference_steps=20, guidance_scale=N["cfg"],
                generator=torch.Generator("cpu").manual_seed(7)).images[0].save(f"{OUT}/s3_{tag}_{ci}.png")
            print(f"[s3] {tag} / {cname} hires {time.time()-t:.1f}s peak {peak():.2f}GB", flush=True)

    rows = [(c[0], [REF] + [f"{OUT}/s3_{s[0]}_{ci}.png" for s in SIT]) for ci, c in enumerate(CONFIGS)]
    grid(rows, ["reference"] + [s[0] for s in SIT], f"{OUT}/grid_s3.png", cell=360)
    print("DONE")


if __name__ == "__main__":
    main()
