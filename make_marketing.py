#!/usr/bin/env python3
"""Tạo ảnh marketing từ chính NFT của bộ (banner, teaser, X header, showcase)."""
import glob, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = "/Users/loserzx/Desktop/chamau/marketing"
IMGS = sorted(glob.glob("/Users/loserzx/Desktop/chamau/out/images/*.png"))
os.makedirs(OUT, exist_ok=True)
random.seed(7)

PINK = (201, 91, 154); INK = (58, 51, 80); WHITE = (255, 255, 255)

def font(size):
    for p in ["/System/Library/Fonts/SFNSRounded.ttf",
              "/System/Library/Fonts/Supplemental/Futura.ttc",
              "/System/Library/Fonts/Avenir Next.ttc",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]:
        try: return ImageFont.truetype(p, size)
        except Exception: pass
    return ImageFont.load_default()

def pastel_bg(w, h):
    y, x = np.mgrid[0:h, 0:w].astype(float)
    t = ((x / w) + (y / h)) / 2
    c1, c2, c3 = np.array([255, 235, 245.]), np.array([229, 239, 255.]), np.array([232, 255, 243.])
    a = c1 + (c2 - c1) * np.clip(t * 2, 0, 1)[..., None]
    b = c2 + (c3 - c2) * np.clip((t - .5) * 2, 0, 1)[..., None]
    img = np.where(t[..., None] < .5, a, b)
    return Image.fromarray(img.astype("uint8"))

def thumb(path, size, radius=None, border=0):
    im = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    if border:
        bg = Image.new("RGB", (size + 2 * border, size + 2 * border), WHITE)
        bg.paste(im, (border, border)); im = bg; size = im.size[0]
    if radius:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size], radius, fill=255)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); out.paste(im, (0, 0), mask)
        return out
    return im.convert("RGBA")

def ctext(d, cx, y, text, fnt, fill, anchor="mm"):
    d.text((cx, y), text, font=fnt, fill=fill, anchor=anchor)

# ── 1. BANNER GRID 1600x900: tường NFT + card title ──
def banner():
    W, H = 1600, 900
    bg = pastel_bg(W, H)
    cell = 116; cols = W // cell + 1; rows = H // cell + 1
    pics = random.sample(IMGS, min(len(IMGS), cols * rows))
    k = 0
    for r in range(rows):
        for c in range(cols):
            t = thumb(pics[k % len(pics)], cell - 14, radius=18)
            bg.paste(t, (c * cell + 7, r * cell + 7), t); k += 1
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rounded_rectangle([W//2-470, H//2-150, W//2+470, H//2+150], 40, fill=(255, 255, 255, 232))
    bg.paste(ov, (0, 0), ov)
    d = ImageDraw.Draw(bg)
    ctext(d, W//2, H//2-50, "MYTHOS DOTS", font(96), INK)
    ctext(d, W//2, H//2+38, "7777 generative pixel-dot NFTs", font(38), PINK)
    ctext(d, W//2, H//2+95, "guess the word  ·  mint the dots  ·  mythosdots.xyz", font(28), INK)
    bg.save(f"{OUT}/banner.png"); print("banner.png")

# ── 2. TEASER 1200x675: masked word ──
def teaser():
    W, H = 1200, 675
    bg = pastel_bg(W, H); d = ImageDraw.Draw(bg)
    # vài NFT rải góc
    for (x, y, s) in [(60, 60, 120), (W-200, 90, 140), (90, H-210, 150), (W-230, H-220, 130)]:
        t = thumb(random.choice(IMGS), s, radius=26); bg.paste(t, (x, y), t)
    ctext(d, W//2, 210, "_  _  _  _  _  _", font(110), PINK)
    ctext(d, W//2, 340, "Guess the word. Mint the dots.", font(52), INK)
    ctext(d, W//2, 410, "The faster you solve, the more you mint.", font(32), (120, 110, 150))
    ctext(d, W//2, 600, "mythosdots.xyz", font(34), INK)
    bg.save(f"{OUT}/teaser.png"); print("teaser.png")

# ── 3. X HEADER 1500x500 ──
def header():
    W, H = 1500, 500
    bg = pastel_bg(W, H)
    s = 150
    pics = random.sample(IMGS, 9)
    for i, p in enumerate(pics):
        t = thumb(p, s, radius=24); bg.paste(t, (40 + i * (s + 14), H - s - 40), t)
    d = ImageDraw.Draw(bg)
    ctext(d, W//2, 110, "MYTHOS  DOTS", font(92), INK)
    ctext(d, W//2, 185, "7777  ·  solve to mint  ·  mythosdots.xyz", font(34), PINK)
    bg.save(f"{OUT}/x_header.png"); print("x_header.png")

# ── 4. SHOWCASE 1080x1080: 3x3 ──
def showcase():
    W = 1080
    bg = pastel_bg(W, W); d = ImageDraw.Draw(bg)
    pics = random.sample(IMGS, 9)
    g = 300; gap = 30; x0 = (W - (3 * g + 2 * gap)) // 2; y0 = 150
    for i, p in enumerate(pics):
        t = thumb(p, g, radius=34, border=6)
        bg.paste(t, (x0 + (i % 3) * (g + gap), y0 + (i // 3) * (g + gap)), t)
    ctext(d, W//2, 80, "MYTHOS DOTS", font(72), INK)
    ctext(d, W//2, W-60, "9 of 7777  ·  mythosdots.xyz", font(34), PINK)
    bg.save(f"{OUT}/showcase.png"); print("showcase.png")

banner(); teaser(); header(); showcase()
print("Done →", OUT)
