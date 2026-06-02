#!/usr/bin/env python3
"""
extract_palette.py — Rút palette màu từ folder ảnh thần (loại nền đen #000000).

  1. Nạp tất cả PNG, downsample mỗi ảnh xuống SAMPLE x SAMPLE để lấy mẫu màu nhanh.
  2. Bỏ pixel near-black (nền) theo ngưỡng BLACK_THRESH.
  3. Gom toàn bộ pixel màu → quantize median-cut xuống N_COLORS màu.
  4. Lưu palette.json ([[r,g,b],...]) + palette_preview.png để xem dải màu.

Cách dùng: python3 extract_palette.py
"""
import glob
import json
import os

import numpy as np
from PIL import Image

SRC_DIR = "/Users/loserzx/Desktop/thần"
OUT_DIR = "/Users/loserzx/Desktop/chamau"
SAMPLE = 96          # downsample mỗi ảnh xuống 96x96 để lấy mẫu
BLACK_THRESH = 30    # pixel có cả 3 kênh < ngưỡng này coi là nền đen → bỏ
N_COLORS = 256       # số màu trong palette cuối


def main():
    paths = sorted(glob.glob(os.path.join(SRC_DIR, "*.png")))
    print(f"Tìm thấy {len(paths)} ảnh nguồn")

    chunks = []
    for p in paths:
        im = Image.open(p).convert("RGB").resize((SAMPLE, SAMPLE), Image.LANCZOS)
        a = np.asarray(im).reshape(-1, 3)
        # bỏ near-black: cả 3 kênh đều dưới ngưỡng
        mask = ~np.all(a < BLACK_THRESH, axis=1)
        chunks.append(a[mask])

    pixels = np.concatenate(chunks, axis=0)
    print(f"Tổng pixel màu (sau khi bỏ nền đen): {len(pixels):,}")

    # quantize: dựng 1 ảnh dài chứa toàn bộ pixel rồi median-cut
    side = int(np.ceil(np.sqrt(len(pixels))))
    pad = side * side - len(pixels)
    if pad:
        pixels = np.concatenate([pixels, pixels[:pad]], axis=0)
    sample_img = Image.fromarray(pixels.reshape(side, side, 3).astype("uint8"), "RGB")
    pal_img = sample_img.quantize(colors=N_COLORS, method=Image.MEDIANCUT)

    pal = pal_img.getpalette()[: N_COLORS * 3]
    colors = [pal[i : i + 3] for i in range(0, len(pal), 3)]

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "palette.json"), "w") as f:
        json.dump(colors, f)
    print(f"Lưu {len(colors)} màu → palette.json")

    # preview: lưới swatch 16x16
    cols = 16
    rows = int(np.ceil(len(colors) / cols))
    sw = 40
    prev = Image.new("RGB", (cols * sw, rows * sw), (20, 20, 20))
    px = prev.load()
    for idx, c in enumerate(colors):
        cx, cy = (idx % cols) * sw, (idx // cols) * sw
        for y in range(cy, cy + sw):
            for x in range(cx, cx + sw):
                px[x, y] = tuple(c)
    prev.save(os.path.join(OUT_DIR, "palette_preview.png"))
    print("Lưu palette_preview.png")


if __name__ == "__main__":
    main()
