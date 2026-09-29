"""Detectors for the pose + face passes: YOLO face boxes, and YOLO-pose keypoints drawn as an OpenPose skeleton."""
import numpy as np
from PIL import Image, ImageDraw
from ultralytics import YOLO

D = "D:/Kataki/.runtime/models/detect"
_face, _pose = None, None

# OpenPose-18 order, as indices into COCO-17 (None = neck, the shoulder midpoint)
OP_FROM_COCO = [0, None, 6, 8, 10, 5, 7, 9, 12, 14, 16, 11, 13, 15, 2, 1, 4, 3]
LIMBS = [(1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7), (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),
         (1, 0), (0, 14), (14, 16), (0, 15), (15, 17)]
COLORS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0),
          (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255),
          (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)]


def faces(img, conf=0.3):
    """Face boxes (x0, y0, x1, y1), left to right."""
    global _face
    _face = _face or YOLO(f"{D}/face_yolov8n.pt")
    r = _face(img, conf=conf, verbose=False, device="cpu")[0]
    return sorted([tuple(map(int, b)) for b in r.boxes.xyxy.tolist()])


def skeleton(img, conf=0.3):
    """OpenPose-style skeleton image (black bg) of the most confident person, or None."""
    global _pose
    _pose = _pose or YOLO(f"{D}/yolo11n-pose.pt")
    r = _pose(img, verbose=False, device="cpu")[0]
    if r.keypoints is None or len(r.keypoints) == 0:
        return None
    i = int(r.boxes.conf.argmax())
    xy, c = r.keypoints.xy[i].numpy(), r.keypoints.conf[i].numpy()
    pts = []
    for k in OP_FROM_COCO:
        if k is None:  # neck
            ok = c[5] > conf and c[6] > conf
            pts.append(tuple((xy[5] + xy[6]) / 2) if ok else None)
        else:
            pts.append(tuple(xy[k]) if c[k] > conf else None)
    out = Image.new("RGB", img.size, "black")
    d = ImageDraw.Draw(out)
    w = max(4, img.width // 100)
    for n, (a, b) in enumerate(LIMBS):
        if pts[a] and pts[b]:
            d.line([pts[a], pts[b]], fill=tuple(int(v * 0.6) for v in COLORS[n]), width=w)
    for n, p in enumerate(pts):
        if p:
            d.ellipse([p[0] - w, p[1] - w, p[0] + w, p[1] + w], fill=COLORS[n])
    return out, sum(p is not None for p in pts)


if __name__ == "__main__":
    import glob
    OUT = "D:/Kataki/.runtime/imgspike"
    files = sorted(glob.glob(f"{OUT}/s3_*_?.png")) + sorted(glob.glob(f"{OUT}/s1_wai_*_newhires.png"))
    hit = 0
    for f in files:
        b = faces(Image.open(f).convert("RGB"))
        hit += bool(b)
        print(f"{f.split('/')[-1]:28s} faces={len(b)} {b}")
    print(f"face detector: {hit}/{len(files)} images with a face")
    for tag in ("rain", "roof"):
        sk, n = skeleton(Image.open(f"{OUT}/s3_{tag}_0_base.png").convert("RGB"))
        sk.save(f"{OUT}/pose_{tag}.png")
        print(f"pose_{tag}: {n}/18 keypoints")
