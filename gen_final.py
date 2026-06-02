#!/usr/bin/env python3
"""
gen_final.py — Sinh bộ 7777 "chấm màu pixel" gradient + metadata chuẩn OpenSea.

Mỗi token: random 1 gradient (Palette) × 1 kiểu tô (Pattern: Sample/Linear/Radial)
× 1 nền (Background: Dark/Light). Traits phái sinh: Hue Family, Brightness.

  python3 gen_final.py --count 7777
"""
import argparse
import colorsys
import hashlib
import json
import os

import numpy as np
from PIL import Image, ImageDraw

from gradients import GRADIENTS, build_lut

OUT = "/Users/loserzx/Desktop/chamau/out"
CANVAS, GRID = 1024, 16
BG_DARK, BG_LIGHT = (20, 20, 24), (245, 240, 232)
PATTERNS = ["Sample", "Linear", "Radial"]

COLLECTION = "Mythos Dots"
DESCRIPTION = "7777 generative pixel-dot artworks built from vivid gradient palettes."
BASE_URI = "ipfs://YOUR_CID_HERE"


def hue_family(rgb):
    r, g, b = [v / 255 for v in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s < 0.12:
        return "Neutral"
    deg = h * 360
    bands = [(15, "Red"), (45, "Orange"), (70, "Yellow"), (160, "Green"),
             (200, "Cyan"), (255, "Blue"), (290, "Purple"), (345, "Pink"), (360, "Red")]
    for hi, name in bands:
        if deg < hi:
            return name
    return "Red"


def brightness_band(lum):
    return "Dark" if lum < 85 else "Mid" if lum < 170 else "Bright"


def render(stops, pattern, bg, seed):
    """Trả về (image, color_grid[g,g,3] uint8)."""
    lut = build_lut(stops, 256)
    rng = np.random.default_rng(seed)
    g1 = GRID - 1
    if pattern == "Sample":
        t = rng.integers(0, 256, size=(GRID, GRID))
    elif pattern == "Linear":
        ang = rng.uniform(0, 2 * np.pi)
        dx, dy = np.cos(ang), np.sin(ang)
        gx, gy = np.meshgrid(np.arange(GRID), np.arange(GRID))
        base = ((gx / g1) * dx + (gy / g1) * dy + 1) / 2
        jit = rng.uniform(-0.04, 0.04, size=(GRID, GRID))
        t = (np.clip(base + jit, 0, 1) * 255).astype(int)
    else:  # Radial
        cx0, cy0 = rng.uniform(0.2, 0.8), rng.uniform(0.2, 0.8)
        gx, gy = np.meshgrid(np.arange(GRID), np.arange(GRID))
        dist = np.hypot(gx / g1 - cx0, gy / g1 - cy0) / 1.2
        t = (np.clip(dist, 0, 1) * 255).astype(int)

    grid_cols = lut[t]  # (G,G,3)
    im = Image.new("RGB", (CANVAS, CANVAS), bg)
    d = ImageDraw.Draw(im)
    cell = CANVAS / GRID
    r = cell * 0.42
    for gy_ in range(GRID):
        for gx_ in range(GRID):
            cx, cy = (gx_ + 0.5) * cell, (gy_ + 0.5) * cell
            col = tuple(int(v) for v in grid_cols[gy_, gx_])
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    return im, grid_cols


def make_metadata(tid, name, pattern, bg_name, lut_mean):
    return {
        "name": f"{COLLECTION} #{tid}",
        "description": DESCRIPTION,
        "image": f"{BASE_URI}/{tid}.png",
        "attributes": [
            {"trait_type": "Palette", "value": name},
            {"trait_type": "Pattern", "value": pattern},
            {"trait_type": "Background", "value": bg_name},
            {"trait_type": "Hue Family", "value": hue_family(lut_mean)},
            {"trait_type": "Brightness", "value": brightness_band(
                0.299 * lut_mean[0] + 0.587 * lut_mean[1] + 0.114 * lut_mean[2])},
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=7777)
    args = ap.parse_args()

    img_dir = os.path.join(OUT, "images")
    meta_dir = os.path.join(OUT, "metadata")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(meta_dir, exist_ok=True)

    seen, made, seed = set(), 0, 0
    while made < args.count:
        seed += 1
        rng = np.random.default_rng(seed)
        name, stops = GRADIENTS[rng.integers(0, len(GRADIENTS))]
        pattern = PATTERNS[rng.integers(0, len(PATTERNS))]
        is_light = bool(rng.integers(0, 4) == 0)  # ~25% nền sáng
        bg, bg_name = (BG_LIGHT, "Light") if is_light else (BG_DARK, "Dark")

        im, grid_cols = render(stops, pattern, bg, seed)
        h = hashlib.sha1(grid_cols.tobytes() + bg_name.encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        made += 1

        im.save(os.path.join(img_dir, f"{made}.png"))
        lut_mean = build_lut(stops, 256).mean(axis=0)
        with open(os.path.join(meta_dir, f"{made}.json"), "w") as f:
            json.dump(make_metadata(made, name, pattern, bg_name, lut_mean), f, indent=2)
        if made % 500 == 0:
            print(f"{made}/{args.count}")
    print(f"Xong {made} ảnh + metadata → {OUT}")


if __name__ == "__main__":
    main()
