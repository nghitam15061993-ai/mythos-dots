#!/usr/bin/env python3
"""
pin_to_pinata.py — Upload 1 folder lên Pinata IPFS dưới dạng thư mục, in CID.

Stream từng file (không nuốt cả 374MB vào RAM) + nâng giới hạn open-files vì
folder có 7777 file.

CHUẨN BỊ:
  - Tạo Pinata JWT: pinata.cloud → API Keys → New Key (bật pinFileToIPFS) → copy JWT
  - export PINATA_JWT="eyJ..."

DÙNG:
  python3 pin_to_pinata.py out/images   "Mythos Dots images"
  # ... chạy set_image_uri.py với CID ảnh ...
  python3 pin_to_pinata.py out/metadata "Mythos Dots metadata"

File nằm ở ROOT của CID → truy cập ipfs://CID/<id>.png  và  ipfs://CID/<id>.json
→ baseURI contract = ipfs://CID_METADATA/
"""
import glob
import json
import os
import resource
import sys

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

ENDPOINT = "https://api.pinata.cloud/pinning/pinFileToIPFS"


def raise_fd(n):
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    target = n if (hard < 0 or n <= hard) else hard
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
    except ValueError:
        pass


def main():
    if len(sys.argv) < 2:
        sys.exit("Dùng: python3 pin_to_pinata.py <folder> [tên-pin]")
    folder = sys.argv[1].rstrip("/")
    name = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(folder)
    jwt = os.environ.get("PINATA_JWT")
    if not jwt:
        sys.exit("Thiếu env PINATA_JWT — export PINATA_JWT=\"eyJ...\"")

    files = sorted(glob.glob(os.path.join(folder, "*")))
    if not files:
        sys.exit(f"Folder rỗng: {folder}")
    raise_fd(len(files) + 256)

    handles, fields = [], []
    for p in files:
        fh = open(p, "rb")
        handles.append(fh)
        # filename KHÔNG có dấu / → file nằm ở root của thư mục CID
        fields.append(("file", (os.path.basename(p), fh, "application/octet-stream")))
    fields.append(("pinataOptions", json.dumps({"cidVersion": 1})))
    fields.append(("pinataMetadata", json.dumps({"name": name})))

    enc = MultipartEncoder(fields=fields)
    total = enc.len
    last = [0]

    def cb(monitor):
        pct = monitor.bytes_read * 100 // total
        if pct >= last[0] + 5:
            last[0] = pct
            print(f"  upload {pct}%", end="\r", flush=True)

    monitor = MultipartEncoderMonitor(enc, cb)
    print(f"Upload {len(files)} file ({total/1e6:.0f} MB) → Pinata...")
    r = requests.post(
        ENDPOINT,
        data=monitor,
        headers={"Authorization": f"Bearer {jwt}", "Content-Type": monitor.content_type},
        timeout=3600,
    )
    for fh in handles:
        fh.close()

    if not r.ok:
        sys.exit(f"\nLỗi {r.status_code}: {r.text[:300]}")
    cid = r.json()["IpfsHash"]
    sample = os.path.basename(files[0])
    print(f"\n✅ CID: {cid}")
    print(f"   Test: https://gateway.pinata.cloud/ipfs/{cid}/{sample}")
    print(f"   ipfs://{cid}/{sample}")


if __name__ == "__main__":
    main()
