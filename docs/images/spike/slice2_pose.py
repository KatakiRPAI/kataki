"""Fix the slice-3 flaws: pose (T2I-Adapter OpenPose from the skeletons posefx.py extracted) for rain + roof,
then hires, then a hand-rolled ADetailer face pass on all 4 situations. Block-wise IP-Adapter throughout; 0 in passes.
"""
import time, torch
from diffusers import (StableDiffusionXLPipeline, StableDiffusionXLAdapterPipeline, StableDiffusionXLImg2ImgPipeline,
                       EulerAncestralDiscreteScheduler, T2IAdapter)
from PIL import Image, ImageDraw, ImageFilter
from slice1 import NEW, esrgan, peak, OUT
from slice3 import CHAR, SIT, BLOCK, EMB
from posefx import faces
from grid import grid

N = NEW["wai"]
POSED = {"rain", "roof"}


def face_pass(i2i, img, prompt, embeds, neg, cfg, pad=32, feather=8, strength=0.4):
    for x0, y0, x1, y1 in faces(img):
        box = (max(x0 - pad, 0), max(y0 - pad, 0), min(x1 + pad, img.width), min(y1 + pad, img.height))
        crop = img.crop(box)
        s = 1024 / max(crop.size)
        big = crop.resize((int(crop.width * s) // 8 * 8, int(crop.height * s) // 8 * 8), Image.LANCZOS)
        fixed = i2i(prompt=prompt, negative_prompt=neg, image=big, strength=strength,
                    ip_adapter_image_embeds=embeds, num_inference_steps=20, guidance_scale=cfg,
                    generator=torch.Generator("cpu").manual_seed(7)).images[0].resize(crop.size, Image.LANCZOS)
        # padding is context only: paste back just the face box, feathered, so the background never changes
        mask = Image.new("L", crop.size, 0)
        ImageDraw.Draw(mask).rectangle([x0 - box[0], y0 - box[1], x1 - box[0], y1 - box[1]], fill=255)
        img.paste(fixed, box[:2], mask.filter(ImageFilter.GaussianBlur(feather / 2)))
    return img


def main():
    embeds = [e.to("cuda") for e in torch.load(EMB)]
    pipe = StableDiffusionXLPipeline.from_single_file(N["ckpt"], torch_dtype=torch.float16)
    pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models",
                         weight_name="ip-adapter-plus_sdxl_vit-h.safetensors", image_encoder_folder=None)
    adapter = T2IAdapter.from_pretrained("TencentARC/t2i-adapter-openpose-sdxl-1.0", torch_dtype=torch.float16)
    t2i = StableDiffusionXLAdapterPipeline(**pipe.components, adapter=adapter)
    i2i = StableDiffusionXLImg2ImgPipeline(**pipe.components)
    del pipe
    t2i.scheduler = EulerAncestralDiscreteScheduler.from_config(t2i.scheduler.config)
    t2i.enable_model_cpu_offload()
    t2i.vae.enable_tiling()
    print("[s2p] loaded", flush=True)

    t2i.set_ip_adapter_scale(BLOCK)
    for tag, sit, seed in SIT:
        if tag not in POSED:
            continue
        torch.cuda.reset_peak_memory_stats(); t = time.time()
        t2i(prompt=f"{N['qual']}, {CHAR}, {sit}", negative_prompt=N["neg"], image=Image.open(f"{OUT}/pose_{tag}.png"),
            width=832, height=1216, ip_adapter_image_embeds=embeds, adapter_conditioning_scale=1.0,
            num_inference_steps=N["steps"], guidance_scale=N["cfg"],
            generator=torch.Generator("cpu").manual_seed(seed)).images[0].save(f"{OUT}/s2p_{tag}_base.png")
        print(f"[s2p] {tag} posed base {time.time()-t:.1f}s peak {peak():.2f}GB", flush=True)

    t2i.remove_all_hooks()
    i2i.enable_model_cpu_offload()
    i2i.scheduler = EulerAncestralDiscreteScheduler.from_config(i2i.scheduler.config)
    i2i.set_ip_adapter_scale(0.0)
    for tag, sit, seed in SIT:
        prompt = f"{N['qual']}, {CHAR}, {sit}"
        torch.cuda.reset_peak_memory_stats(); t = time.time()
        if tag in POSED:
            big = esrgan(N["up"], Image.open(f"{OUT}/s2p_{tag}_base.png").convert("RGB"), 1.5)
            img = i2i(prompt=prompt, negative_prompt=N["neg"], image=big, strength=N["strength"],
                      ip_adapter_image_embeds=embeds, num_inference_steps=20, guidance_scale=N["cfg"],
                      generator=torch.Generator("cpu").manual_seed(7)).images[0]
        else:
            img = Image.open(f"{OUT}/s3_{tag}_2.png").convert("RGB")  # block-wise hires from the last run
        img.save(f"{OUT}/s2p_{tag}_hires.png")
        th = time.time() - t
        face_pass(i2i, img, prompt, embeds, N["neg"], N["cfg"]).save(f"{OUT}/s2p_{tag}.png")
        print(f"[s2p] {tag} hires {th:.1f}s + face pass {time.time()-t-th:.1f}s peak {peak():.2f}GB", flush=True)

    S = [s[0] for s in SIT]
    grid([("before (last run)", [f"{OUT}/s3_{s}_2.png" for s in S]),
          ("after: pose + face", [f"{OUT}/s2p_{s}.png" for s in S])], S, f"{OUT}/grid_s2p.png", cell=420)
    # face close-ups: same box, hires only vs hires + face pass
    rows = [("hires only", []), ("+ face pass", [])]
    for s in S:
        a, b = Image.open(f"{OUT}/s2p_{s}_hires.png"), Image.open(f"{OUT}/s2p_{s}.png")
        x0, y0, x1, y1 = faces(a)[0]
        m = (x1 - x0) // 3
        box = (max(x0 - m, 0), max(y0 - m, 0), min(x1 + m, a.width), min(y1 + m, a.height))
        for (_, paths), im in zip(rows, (a, b)):
            p = f"{OUT}/_fz_{s}_{len(paths)}_{id(im)}.png"
            im.crop(box).resize((512, 512), Image.LANCZOS).save(p)
            paths.append(p)
    grid(rows, S, f"{OUT}/grid_s2p_faces.png", cell=420)
    print("DONE")


if __name__ == "__main__":
    main()
