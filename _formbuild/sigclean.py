from PIL import Image, ImageFilter
import numpy as np
import sys

def clean(src, dst, gamma=0.75, bg_drop=18, lo=0.0):
    im = Image.open(src).convert('RGB')
    rgb = np.array(im).astype(np.float32)
    g = np.array(im.convert('L')).astype(np.float32)
    bg = np.array(im.convert('L').filter(ImageFilter.GaussianBlur(40))).astype(np.float32)
    bg = np.maximum(bg, g)
    d = np.clip(bg - g - bg_drop, 0, None)
    span = np.clip(bg - 12, 25, None)
    a = np.clip(d / span, 0, 1)
    a = np.power(a, gamma)
    a[a < lo] = 0
    al = (a * 255).astype(np.uint8)
    ink = np.clip(g, 0, 70)
    out = np.dstack([np.full_like(ink, 15), np.full_like(ink, 15), np.full_like(ink, 15), al])
    res = Image.fromarray(out.astype(np.uint8), 'RGBA')
    bbox = res.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
    if bbox:
        res = res.crop(bbox)
    res.save(dst)
    return res.size

if __name__ == '__main__':
    print(clean(sys.argv[1], sys.argv[2]))
