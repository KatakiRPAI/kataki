"""M3 spike — run the prince x bully cast on a Civitai single-file checkpoint.
Usage: python gen_ckpt.py --ckpt <path.safetensors> --name wai --flavor illustrious|pony
Same characters / scenes / seeds across models for a clean head-to-head.
"""
import argparse, time, torch
from diffusers import StableDiffusionXLPipeline
from transformers import CLIPVisionModelWithProjection, CLIPImageProcessor
from PIL import Image

OUT = "D:/Kataki/.runtime/imgspike"
BLANK = Image.new("RGB", (832, 1216), (128, 128, 128))

FLAVORS = {
    "illustrious": {
        "qual": "masterpiece, best quality, amazing quality, very aesthetic, absurdres",
        "neg": ("worst quality, low quality, bad anatomy, bad hands, extra digits, jpeg artifacts, "
                "signature, watermark, text, blurry, deformed, mutated, ugly, child"),
        "prince": "1boy, solo, young man, adult, blonde hair, soft handsome features, blue eyes, gentle expression, faint smile, bishounen, casual collared shirt, manhwa style",
        "bully":  "1boy, solo, young man, adult, tall, muscular, messy black hair, sharp eyes, delinquent, tough, confident smirk, earrings, manhwa style",
        "steps": 28, "cfg": 5.5,
    },
    "pony": {
        "qual": "score_9, score_8_up, score_7_up, score_6_up, source_realistic, photorealistic, realistic, highly detailed",
        "neg": ("score_6, score_5, score_4, worst quality, low quality, bad anatomy, bad hands, extra digits, "
                "blurry, deformed, mutated, cartoon, anime, 3d, cgi, doll, child"),
        "prince": "1boy, solo, young man, adult early 20s, blonde hair, soft handsome face, blue eyes, gentle expression, slight smile, casual collared shirt",
        "bully":  "1boy, solo, young man, adult, tall, muscular, messy black hair, sharp eyes, tough, confident smirk, earrings, leather jacket",
        "steps": 30, "cfg": 6.5,
    },
}
# tag, scene suffix, seed, character, ip-adapter scale (0 = fresh base, becomes that character's ref)
SHOTS = [
    ("prince_base",   "plain soft studio background, upper body, looking at viewer",                                111, "prince", 0.0),
    ("prince_school", "wearing a school uniform, boarding school classroom, sunlight, upper body",                  112, "prince", 0.4),
    ("prince_room",   "cozy small bedroom, fairy lights, plushies on bed, casual hoodie, warm soft light, sitting", 113, "prince", 0.4),
    ("prince_street", "walking on a local town street, casual jacket, daytime, buildings",                          114, "prince", 0.4),
    ("bully_base",    "school hallway background, upper body, looking at viewer",                                    200, "bully",  0.0),
    ("bully_school",  "leaning against a locker cornering someone, school hallway, looming, smirk, daytime",        201, "bully",  0.55),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--flavor", choices=list(FLAVORS), required=True)
    a = ap.parse_args()
    F = FLAVORS[a.flavor]

    t = time.time()
    enc = CLIPVisionModelWithProjection.from_pretrained(
        "h94/IP-Adapter", subfolder="models/image_encoder", torch_dtype=torch.float16)
    pipe = StableDiffusionXLPipeline.from_single_file(a.ckpt, torch_dtype=torch.float16)
    pipe.image_encoder = enc
    if getattr(pipe, "feature_extractor", None) is None:
        pipe.feature_extractor = CLIPImageProcessor()
    pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models",
                         weight_name="ip-adapter-plus_sdxl_vit-h.safetensors")
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_slicing()
    print(f"[{a.name}] loaded '{a.ckpt}' in {time.time()-t:.1f}s")

    refs = {}
    for tag, scene, seed, who, scale in SHOTS:
        ref = BLANK if scale == 0.0 else refs[who]
        pipe.set_ip_adapter_scale(scale)
        t = time.time()
        img = pipe(prompt=f"{F['qual']}, {F[who]}, {scene}", negative_prompt=F["neg"],
                   ip_adapter_image=ref, width=832, height=1216,
                   num_inference_steps=F["steps"], guidance_scale=F["cfg"],
                   generator=torch.Generator("cpu").manual_seed(seed)).images[0]
        img.save(f"{OUT}/{a.name}_{tag}.png")
        if scale == 0.0:
            refs[who] = img
        print(f"[{a.name}] {tag} in {time.time()-t:.1f}s  peak {torch.cuda.max_memory_allocated()/1e9:.2f}GB")
    print(f"[{a.name}] DONE")

if __name__ == "__main__":
    main()
