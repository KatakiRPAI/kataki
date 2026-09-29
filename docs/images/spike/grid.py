"""Labelled comparison grid. grid([(row_label, [paths...])], [col_labels], out, crop=(l,t,r,b) relative)."""
from PIL import Image, ImageDraw, ImageFont

def grid(rows, cols, out, cell=384, crop=None):
    font = ImageFont.load_default(size=18)
    first = Image.open(rows[0][1][0])
    w, h = first.size
    if crop:
        w, h = int(w * (crop[2] - crop[0])), int(h * (crop[3] - crop[1]))
    ch = int(cell * h / w)
    lw, top = 150, 30
    sheet = Image.new("RGB", (lw + cell * len(cols), top + ch * len(rows)), "white")
    d = ImageDraw.Draw(sheet)
    for c, name in enumerate(cols):
        d.text((lw + c * cell + 6, 6), name, fill="black", font=font)
    for r, (label, paths) in enumerate(rows):
        d.text((6, top + r * ch + ch // 2), label, fill="black", font=font)
        for c, p in enumerate(paths):
            im = Image.open(p).convert("RGB")
            if crop:
                im = im.crop((int(im.width * crop[0]), int(im.height * crop[1]),
                              int(im.width * crop[2]), int(im.height * crop[3])))
            sheet.paste(im.resize((cell, ch), Image.LANCZOS), (lw + c * cell, top + r * ch))
    sheet.save(out)
    return out
