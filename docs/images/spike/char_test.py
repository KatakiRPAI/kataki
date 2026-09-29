"""Full chain for one character in the 4 test situations: block-wise IP-Adapter from one reference picture,
T2I-Adapter pose skeletons where set (scale 0 elsewhere), 1.5x hires, face pass.
Usage: python char_test.py bully | pony_prince | pony_bully
"""
import sys, time, torch
from diffusers import (StableDiffusionXLAdapterPipeline, StableDiffusionXLImg2ImgPipeline, StableDiffusionXLPipeline,
                       EulerAncestralDiscreteScheduler, T2IAdapter)
from transformers import CLIPVisionModelWithProjection, CLIPImageProcessor, CLIPTokenizer
from PIL import Image, ImageOps
from slice1 import NEW, esrgan, peak, OUT
from slice3 import SIT, BLOCK
from slice2_pose import face_pass
from grid import grid

CHARS = {
    "bully": dict(flavor="wai", ref=f"{OUT}/s1_wai_bully_newbase.png",
                  char="1boy, solo, young man, adult, early 20s, tall, muscular, short hair, messy black hair, "
                       "dark eyes, sharp eyes, earrings, delinquent, manhwa style"),
    "pony_prince": dict(flavor="pony", ref=f"{OUT}/s1_pony_prince_newbase.png",
                        char="1boy, young man, adult, early 20s, short hair, blonde hair, blue eyes, soft handsome face"),
    "pony_bully": dict(flavor="pony", ref=f"{OUT}/s1_pony_bully_newbase.png",
                       char="1boy, young man, adult, early 20s, muscular, short hair, messy black hair, dark eyes, earrings"),
}
POSE_SCALE, POSE_LAYOUT = 1.4, 0.35  # posed shots: stronger skeleton, weaker IP layout block (bully rain fix)
POSES = {"rain": f"{OUT}/pose_rain.png", "roof": f"{OUT}/pose_roof.png"}  # stand-ins for preset skeletons


def main(name):
    C = CHARS[name]
    N = NEW[C["flavor"]]
    tok = CLIPTokenizer.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", subfolder="tokenizer")
    for tag, sit, _ in SIT:  # CLIP silently truncates at 77 and the situation is at the end
        n = len(tok(f"{N['qual']}, {C['char']}, {sit}").input_ids)
        assert n <= 77, f"{tag} prompt is {n} tokens"
    ref = Image.open(C["ref"]).convert("RGB")
    ref = ImageOps.autocontrast(ref.crop((int(ref.width * .1), 0, int(ref.width * .9), int(ref.height * .55))), cutoff=1)

    pipe = StableDiffusionXLPipeline.from_single_file(N["ckpt"], torch_dtype=torch.float16)
    enc = CLIPVisionModelWithProjection.from_pretrained("h94/IP-Adapter", subfolder="models/image_encoder",
                                                        torch_dtype=torch.float16).cuda()
    pipe.image_encoder, pipe.feature_extractor = enc, CLIPImageProcessor()
    pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models",
                         weight_name="ip-adapter-plus_sdxl_vit-h.safetensors", image_encoder_folder=None)
    # no_grad: otherwise the embeds' autograd graph pins the 1.26 GB encoder on the GPU (it spilled at 50 s/step)
    with torch.no_grad():
        embeds = pipe.prepare_ip_adapter_image_embeds(ref, None, "cuda", 1, True)
    torch.save([e.cpu() for e in embeds], f"{OUT}/ct_{name}_embeds.pt")
    pipe.image_encoder = None
    del enc, embeds
    torch.cuda.empty_cache()
    left = torch.cuda.memory_allocated() / 1e9
    print(f"[{name}] after encoder drop: {left:.2f}GB still allocated", flush=True)
    assert left < 0.5, "image encoder still on the GPU"
    embeds = [e.to("cuda") for e in torch.load(f"{OUT}/ct_{name}_embeds.pt")]

    adapter = T2IAdapter.from_pretrained("TencentARC/t2i-adapter-openpose-sdxl-1.0", torch_dtype=torch.float16)
    t2i = StableDiffusionXLAdapterPipeline(**pipe.components, adapter=adapter)
    i2i = StableDiffusionXLImg2ImgPipeline(**pipe.components)
    del pipe
    t2i.scheduler = EulerAncestralDiscreteScheduler.from_config(t2i.scheduler.config)
    t2i.enable_model_cpu_offload()
    t2i.vae.enable_tiling()
    print(f"[{name}] loaded, embeds saved", flush=True)

    blank = Image.new("RGB", (832, 1216), "black")
    for tag, sit, seed in SIT:
        pose = POSES.get(tag)
        t2i.set_ip_adapter_scale({"down": {"block_2": [0.0, POSE_LAYOUT]}, "up": {"block_0": [0.0, 0.2, 0.0]}}
                                 if pose else BLOCK)
        torch.cuda.reset_peak_memory_stats(); t = time.time()
        t2i(prompt=f"{N['qual']}, {C['char']}, {sit}", negative_prompt=N["neg"],
            image=Image.open(pose) if pose else blank, adapter_conditioning_scale=POSE_SCALE if pose else 0.0,
            width=832, height=1216, ip_adapter_image_embeds=embeds, num_inference_steps=N["steps"],
            guidance_scale=N["cfg"], generator=torch.Generator("cpu").manual_seed(seed)
            ).images[0].save(f"{OUT}/ct_{name}_{tag}_base.png")
        print(f"[{name}] {tag} base{' (posed)' if pose else ''} {time.time()-t:.1f}s peak {peak():.2f}GB", flush=True)

    t2i.remove_all_hooks()
    i2i.enable_model_cpu_offload()
    i2i.scheduler = EulerAncestralDiscreteScheduler.from_config(i2i.scheduler.config)
    i2i.set_ip_adapter_scale(0.0)
    for tag, sit, seed in SIT:
        prompt = f"{N['qual']}, {C['char']}, {sit}"
        torch.cuda.reset_peak_memory_stats(); t = time.time()
        big = esrgan(N["up"], Image.open(f"{OUT}/ct_{name}_{tag}_base.png").convert("RGB"), 1.5)
        img = i2i(prompt=prompt, negative_prompt=N["neg"], image=big, strength=N["strength"],
                  ip_adapter_image_embeds=embeds, num_inference_steps=20, guidance_scale=N["cfg"],
                  generator=torch.Generator("cpu").manual_seed(7)).images[0]
        th = time.time() - t
        face_pass(i2i, img, prompt, embeds, N["neg"], N["cfg"]).save(f"{OUT}/ct_{name}_{tag}.png")
        print(f"[{name}] {tag} hires {th:.1f}s + face {time.time()-t-th:.1f}s peak {peak():.2f}GB", flush=True)

    grid([(name, [C["ref"]] + [f"{OUT}/ct_{name}_{s[0]}.png" for s in SIT])],
         ["reference"] + [s[0] for s in SIT], f"{OUT}/grid_ct_{name}.png", cell=460)
    print("DONE")


if __name__ == "__main__":
    main(sys.argv[1])
