"""Slice 1 — creator recipe + model-upscale hires, no identity.
Old chain (existing base, 1.3x Lanczos, DPM++ 2M Karras, 0.35) vs new chain (Euler a base, 1.5x ESRGAN, Euler a img2img).
Same seeds as gen_ckpt.py. One txt2img + one img2img pipe sharing weights; offload re-hooked on the swap.
"""
import gc, time, numpy as np, torch
from diffusers import (StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline,
                       EulerAncestralDiscreteScheduler, DPMSolverMultistepScheduler)
from spandrel import ModelLoader
from PIL import Image
from gen_ckpt import FLAVORS, SHOTS
from grid import grid

OUT = "D:/Kataki/.runtime/imgspike"
M = "D:/Kataki/.runtime/models"
NEW = {
    "wai": dict(ckpt=f"{M}/waiIllustriousSDXL_v170.safetensors", old="illustrious",
                qual="masterpiece, best quality, amazing quality",
                neg="bad quality, worst quality, worst detail, sketch, censor, signature, watermark, text, artist name, child",
                steps=28, cfg=6.0, up=f"{M}/upscale/RealESRGAN_x4plus_anime_6B.pth", strength=0.4),
    "pony": dict(ckpt=f"{M}/ponyRealism_V22.safetensors", old="pony",
                 qual="score_9, score_8_up, score_7_up, source_realistic, photorealistic",
                 neg="score_4, score_5, score_6, cartoon, anime, 3d, cgi, doll, signature, watermark, text, child",
                 steps=30, cfg=6.5, up=f"{M}/upscale/4x-UltraSharp.pth", strength=0.30),
}
# clip skip 2 == diffusers SDXL default (penultimate layer), so clip_skip stays None.
BASES = [(t.split("_")[0], s, seed) for t, s, seed, who, sc in SHOTS if t.endswith("_base")]


def peak():
    return torch.cuda.max_memory_allocated() / 1e9


def esrgan(path, img, scale, tile=256, pad=16):
    # tiled: a whole-image 4x pass peaked at 8.31 GB (3328x4864 feature maps); tiles stay tiny
    m = ModelLoader().load_from_file(path).cuda().eval().half()
    s = m.scale
    x = torch.from_numpy(np.array(img)).permute(2, 0, 1)[None].half() / 255
    H, W = x.shape[2:]
    out = torch.zeros(1, 3, H * s, W * s, dtype=torch.float16)
    for y0 in range(0, H, tile):
        for x0 in range(0, W, tile):
            y1, x1 = min(y0 + tile, H), min(x0 + tile, W)
            py, px = max(y0 - pad, 0), max(x0 - pad, 0)
            with torch.no_grad():
                o = m(x[..., py:min(y1 + pad, H), px:min(x1 + pad, W)].cuda()).cpu()
            out[..., y0 * s:y1 * s, x0 * s:x1 * s] = o[..., (y0 - py) * s:(y1 - py) * s, (x0 - px) * s:(x1 - px) * s]
    y = out.clamp(0, 1)[0].permute(1, 2, 0).float().numpy()
    del m
    torch.cuda.empty_cache()
    big = Image.fromarray((y * 255).round().astype(np.uint8))
    return big.resize(((int(img.width * scale) // 8) * 8, (int(img.height * scale) // 8) * 8), Image.LANCZOS)


def run(name, N):
    O = FLAVORS[N["old"]]
    t = time.time()
    pipe = StableDiffusionXLPipeline.from_single_file(N["ckpt"], torch_dtype=torch.float16)
    i2i = StableDiffusionXLImg2ImgPipeline(**pipe.components)
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()
    print(f"[{name}] loaded in {time.time()-t:.1f}s", flush=True)

    for who, scene, seed in BASES:
        torch.cuda.reset_peak_memory_stats(); t = time.time()
        img = pipe(prompt=f"{N['qual']}, {O[who]}, {scene}", negative_prompt=N["neg"], width=832, height=1216,
                   num_inference_steps=N["steps"], guidance_scale=N["cfg"],
                   generator=torch.Generator("cpu").manual_seed(seed)).images[0]
        img.save(f"{OUT}/s1_{name}_{who}_newbase.png")
        print(f"[{name}] {who} new base {time.time()-t:.1f}s peak {peak():.2f}GB", flush=True)

    # swap offload hooks onto the img2img pipe (shared modules); never keep both hooked
    pipe.remove_all_hooks()
    i2i.enable_model_cpu_offload()
    euler_a = EulerAncestralDiscreteScheduler.from_config(i2i.scheduler.config)
    dpm = DPMSolverMultistepScheduler.from_config(i2i.scheduler.config, use_karras_sigmas=True)

    for who, scene, seed in BASES:
        # old chain: existing gen_ckpt base, 1.3x Lanczos, DPM++ 2M Karras, 0.35, 18 steps
        src = Image.open(f"{OUT}/{name}_{who}_base.png").convert("RGB")
        big = src.resize(((int(src.width * 1.3) // 8) * 8, (int(src.height * 1.3) // 8) * 8), Image.LANCZOS)
        i2i.scheduler = dpm
        torch.cuda.reset_peak_memory_stats(); t = time.time()
        i2i(prompt=f"{O['qual']}, {O[who]}, {scene}", negative_prompt=O["neg"], image=big, strength=0.35,
            num_inference_steps=18, guidance_scale=O["cfg"],
            generator=torch.Generator("cpu").manual_seed(7)).images[0].save(f"{OUT}/s1_{name}_{who}_oldhires.png")
        print(f"[{name}] {who} old hires {big.size} {time.time()-t:.1f}s peak {peak():.2f}GB", flush=True)

        # new chain: ESRGAN 4x -> 1.5x, Euler a img2img, 20 steps
        src = Image.open(f"{OUT}/s1_{name}_{who}_newbase.png").convert("RGB")
        torch.cuda.reset_peak_memory_stats(); t = time.time()
        big = esrgan(N["up"], src, 1.5)
        tu = time.time() - t
        i2i.scheduler = euler_a
        i2i(prompt=f"{N['qual']}, {O[who]}, {scene}", negative_prompt=N["neg"], image=big, strength=N["strength"],
            num_inference_steps=20, guidance_scale=N["cfg"],
            generator=torch.Generator("cpu").manual_seed(7)).images[0].save(f"{OUT}/s1_{name}_{who}_newhires.png")
        print(f"[{name}] {who} new hires {big.size} {time.time()-t:.1f}s (upscale {tu:.1f}s) peak {peak():.2f}GB", flush=True)

    i2i.remove_all_hooks()
    del pipe, i2i
    gc.collect(); torch.cuda.empty_cache()


def main():
    for name, N in NEW.items():
        run(name, N)
    cols = ["old base", "old hires 1.3x DPM++", "new base Euler a", "new hires 1.5x ESRGAN"]
    rows = [(f"{n} {w}", [f"{OUT}/{n}_{w}_base.png", f"{OUT}/s1_{n}_{w}_oldhires.png",
                          f"{OUT}/s1_{n}_{w}_newbase.png", f"{OUT}/s1_{n}_{w}_newhires.png"])
            for n in NEW for w, _, _ in BASES]
    grid(rows, cols, f"{OUT}/grid_s1.png")
    grid(rows, cols, f"{OUT}/grid_s1_faces.png", cell=420, crop=(0.2, 0.04, 0.8, 0.44))
    print("DONE")


if __name__ == "__main__":
    main()
