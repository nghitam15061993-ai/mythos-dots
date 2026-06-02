#!/usr/bin/env python3
"""Demo gradient: mỗi token bốc 1 gradient + 1 mode tô chấm → đa dạng cả bộ."""
import os

import numpy as np
from PIL import Image, ImageDraw

from gradients import GRADIENTS, build_lut

OUT = "/Users/loserzx/Desktop/chamau/demo_grad"
CANVAS = 1024
BG = (20, 20, 24)


def draw_dots(grid, color_idx_fn, seed):
    """color_idx_fn(gx,gy,rng) -> (r,g,b). Vẽ lưới chấm tròn."""
    rng = np.random.default_rng(seed)
    im = Image.new("RGB", (CANVAS, CANVAS), BG)
    d = ImageDraw.Draw(im)
    cell = CANVAS / grid
    r = cell * 0.42
    for gy in range(grid):
        for gx in range(grid):
            cx, cy = (gx + 0.5) * cell, (gy + 0.5) * cell
            col = color_idx_fn(gx, gy, rng)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(int(v) for v in col))
    return im


def render(name, stops, mode, grid, seed):
    lut = build_lut(stops, 256)
    rng = np.random.default_rng(seed)
    g1 = grid - 1
    if mode == "sample":   # confetti trong 1 hệ màu
        fn = lambda gx, gy, r: lut[r.integers(0, 256)]
    elif mode == "linear":  # gradient chéo, hạt random nhẹ
        ang = rng.uniform(0, 2 * np.pi)
        dx, dy = np.cos(ang), np.sin(ang)
        def fn(gx, gy, r):
            t = ((gx / g1) * dx + (gy / g1) * dy + 1) / 2
            t = np.clip(t + r.uniform(-0.04, 0.04), 0, 1)
            return lut[int(t * 255)]
    else:  # radial
        cx0, cy0 = rng.uniform(0.2, 0.8), rng.uniform(0.2, 0.8)
        def fn(gx, gy, r):
            dist = np.hypot(gx / g1 - cx0, gy / g1 - cy0) / 1.2
            return lut[int(np.clip(dist, 0, 1) * 255)]
    return draw_dots(grid, fn, seed)


def main():
    os.makedirs(OUT, exist_ok=True)
    grid = 16
    picks = [
        ("Ripe Malinka", "sample"), ("Deep Blue", "sample"), ("True Sunset", "sample"),
        ("Happy Fisher", "sample"), ("Phoenix Start", "sample"), ("October Silence", "sample"),
        ("True Sunset", "linear"), ("Near Moon", "linear"), ("Smart Indigo", "radial"),
    ]
    gmap = dict(GRADIENTS)
    for i, (name, mode) in enumerate(picks):
        im = render(name, gmap[name], mode, grid, seed=100 + i)
        fn = f"grad_{name.replace(' ', '')}_{mode}.png"
        im.save(os.path.join(OUT, fn))
        print("→", fn)

    # MONTAGE: 64 token random gradient+mode → xem độ đa dạng cả bộ
    modes = ["sample", "linear", "radial"]
    cols = 8
    thumb = 220
    mont = Image.new("RGB", (cols * thumb, cols * thumb), (10, 10, 12))
    for i in range(cols * cols):
        rng = np.random.default_rng(5000 + i)
        name, stops = GRADIENTS[rng.integers(0, len(GRADIENTS))]
        mode = modes[rng.integers(0, len(modes))]
        im = render(name, stops, mode, grid, seed=5000 + i).resize((thumb, thumb), Image.NEAREST)
        mont.paste(im, ((i % cols) * thumb, (i // cols) * thumb))
    mont.save(os.path.join(OUT, "_montage_64.png"))
    print("→ _montage_64.png  (64 token random — xem độ đa dạng)")
    print("Folder:", OUT)


if __name__ == "__main__":
    main()
