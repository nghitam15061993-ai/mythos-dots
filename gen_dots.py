#!/usr/bin/env python3
"""
gen_dots.py — Sinh ảnh "chấm màu pixel" random từ palette (palette.json).

Style:
  mosaic — lưới N×N ô vuông đặc, mỗi ô 1 màu random từ palette.
  dots   — chấm tròn rải trên nền tối, màu random từ palette.

DEMO:  python3 gen_dots.py --demo
FULL:  python3 gen_dots.py --count 7777 --style mosaic --grid 24
"""
import argparse
import hashlib
import json
import os
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw

OUT_DIR = "/Users/loserzx/Desktop/chamau"
CANVAS = 1024
BG = (17, 17, 20)   # nền tối cho style dots

COLLECTION = "Mythos Dots"
DESCRIPTION = "7777 generative pixel-dot artworks. Colors sampled from the Mythos Pantheon gods palette."
BASE_URI = "ipfs://YOUR_CID_HERE"


def _hex(c):
    return "#%02X%02X%02X" % (int(c[0]), int(c[1]), int(c[2]))


def make_metadata(token_id, idx, palette, style, grid):
    flat = idx.flatten()
    counts = Counter(flat.tolist())
    dom_idx, _ = counts.most_common(1)[0]
    dom = palette[dom_idx]
    lum = float(np.mean([0.299 * palette[i][0] + 0.587 * palette[i][1] + 0.114 * palette[i][2]
                         for i in flat]))
    brightness = "Bright" if lum > 140 else "Mid" if lum > 70 else "Dark"
    return {
        "name": f"{COLLECTION} #{token_id}",
        "description": DESCRIPTION,
        "image": f"{BASE_URI}/{token_id}.png",
        "attributes": [
            {"trait_type": "Style", "value": style.capitalize()},
            {"trait_type": "Grid", "value": f"{grid}x{grid}"},
            {"trait_type": "Palette Source", "value": "Mythos Gods"},
            {"trait_type": "Dominant Color", "value": _hex(dom)},
            {"trait_type": "Distinct Colors", "value": len(counts)},
            {"trait_type": "Brightness", "value": brightness},
        ],
    }


def load_palette():
    with open(os.path.join(OUT_DIR, "palette.json")) as f:
        return np.array(json.load(f), dtype=np.uint8)


def render_mosaic(palette, grid, seed):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(palette), size=(grid, grid))
    small = palette[idx]  # (grid, grid, 3)
    im = Image.fromarray(small, "RGB").resize((CANVAS, CANVAS), Image.NEAREST)
    return im, idx


def render_dots(palette, grid, seed):
    rng = np.random.default_rng(seed)
    im = Image.new("RGB", (CANVAS, CANVAS), BG)
    d = ImageDraw.Draw(im)
    cell = CANVAS / grid
    r = cell * 0.42
    idx = rng.integers(0, len(palette), size=(grid, grid))
    for gy in range(grid):
        for gx in range(grid):
            cx, cy = (gx + 0.5) * cell, (gy + 0.5) * cell
            col = tuple(int(v) for v in palette[idx[gy, gx]])
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    return im, idx


def render(style, palette, grid, seed):
    return render_dots(palette, grid, seed) if style == "dots" else render_mosaic(palette, grid, seed)


def demo(palette):
    demo_dir = os.path.join(OUT_DIR, "demo")
    os.makedirs(demo_dir, exist_ok=True)
    combos = [
        ("mosaic", 16), ("mosaic", 24), ("mosaic", 32),
        ("dots", 16), ("dots", 24), ("dots", 32),
    ]
    for style, grid in combos:
        im, _ = render(style, palette, grid, seed=42)
        name = f"demo_{style}_{grid}x{grid}.png"
        im.save(os.path.join(demo_dir, name))
        print("→", name)
    print(f"\nXong. Mở folder: {demo_dir}")


def full(palette, count, style, grid):
    img_dir = os.path.join(OUT_DIR, "out", "images")
    meta_dir = os.path.join(OUT_DIR, "out", "metadata")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(meta_dir, exist_ok=True)
    seen, made, seed = set(), 0, 0
    while made < count:
        seed += 1
        im, idx = render(style, palette, grid, seed)
        h = hashlib.sha1(idx.tobytes()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        made += 1
        im.save(os.path.join(img_dir, f"{made}.png"))
        with open(os.path.join(meta_dir, f"{made}.json"), "w") as f:
            json.dump(make_metadata(made, idx, palette, style, grid), f, indent=2)
        if made % 500 == 0:
            print(f"{made}/{count}")
    print(f"Xong {made} ảnh + metadata → {OUT_DIR}/out")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--count", type=int, default=7777)
    ap.add_argument("--style", choices=["mosaic", "dots"], default="mosaic")
    ap.add_argument("--grid", type=int, default=24)
    args = ap.parse_args()

    palette = load_palette()
    if args.demo:
        demo(palette)
    else:
        full(palette, args.count, args.style, args.grid)


if __name__ == "__main__":
    main()
