#!/usr/bin/env python3
"""
set_image_uri.py — Cập nhật field "image" trong metadata sau khi có CID ảnh trên IPFS.
KHÔNG re-gen ảnh, chỉ sửa JSON (vài giây).

  python3 set_image_uri.py ipfs://CID_IMAGES
(không cần dấu / cuối — script tự thêm)
"""
import glob
import json
import os
import sys

META = "/Users/loserzx/Desktop/chamau/out/metadata"


def main():
    if len(sys.argv) != 2:
        sys.exit("Dùng: python3 set_image_uri.py ipfs://CID_IMAGES")
    base = sys.argv[1].rstrip("/")
    files = glob.glob(os.path.join(META, "*.json"))
    for p in files:
        tid = os.path.splitext(os.path.basename(p))[0]
        with open(p) as f:
            m = json.load(f)
        m["image"] = f"{base}/{tid}.png"
        with open(p, "w") as f:
            json.dump(m, f, indent=2)
    print(f"Đã cập nhật image cho {len(files)} metadata → {base}/<id>.png")


if __name__ == "__main__":
    main()
