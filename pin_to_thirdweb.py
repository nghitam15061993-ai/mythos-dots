#!/usr/bin/env python3
"""
pin_to_thirdweb.py — Upload 1 folder lên IPFS qua thirdweb storage, in CID.

Stream từng file + nâng giới hạn open-files (folder 7777 file).

CHUẨN BỊ:
  - thirdweb.com → Dashboard → Settings → API Keys → Create key
    → copy SECRET KEY (chỉ hiện 1 lần)
  - export THIRDWEB_SECRET_KEY="..."

DÙNG:
  python3 pin_to_thirdweb.py out/images
  # ... set_image_uri.py với CID ảnh ...
  python3 pin_to_thirdweb.py out/metadata

File nằm ở ROOT của CID → ipfs://CID/<id>.png , ipfs://CID/<id>.json
→ baseURI contract = ipfs://CID_METADATA/
"""
import glob
import os
import resource
import sys

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

ENDPOINT = "https://storage.thirdweb.com/ipfs/upload"


def raise_fd(n):
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    target = n if (hard < 0 or n <= hard) else hard
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
    except ValueError:
        pass


def main():
    if len(sys.argv) < 2:
        sys.exit("Dùng: python3 pin_to_thirdweb.py <folder>")
    folder = sys.argv[1].rstrip("/")
    key = os.environ.get("THIRDWEB_SECRET_KEY")
    if not key:
        sys.exit("Thiếu env THIRDWEB_SECRET_KEY — export THIRDWEB_SECRET_KEY=\"...\"")

    files = sorted(glob.glob(os.path.join(folder, "*")))
    if not files:
        sys.exit(f"Folder rỗng: {folder}")
    raise_fd(len(files) + 256)

    handles, fields = [], []
    for p in files:
        fh = open(p, "rb")
        handles.append(fh)
        # filename = tên file (không có /) → file nằm ở root thư mục CID
        fields.append(("file", (os.path.basename(p), fh, "application/octet-stream")))

    enc = MultipartEncoder(fields=fields)
    total = enc.len
    last = [0]

    def cb(monitor):
        pct = monitor.bytes_read * 100 // total
        if pct >= last[0] + 5:
            last[0] = pct
            print(f"  upload {pct}%", end="\r", flush=True)

    monitor = MultipartEncoderMonitor(enc, cb)
    print(f"Upload {len(files)} file ({total/1e6:.0f} MB) → thirdweb...")
    r = requests.post(
        ENDPOINT,
        data=monitor,
        headers={"Authorization": f"Bearer {key}", "Content-Type": monitor.content_type},
        timeout=3600,
    )
    for fh in handles:
        fh.close()

    if not r.ok:
        sys.exit(f"\nLỗi {r.status_code}: {r.text[:400]}")

    data = r.json()
    cid = data.get("IpfsHash") or data.get("cid") or data.get("ipfsHash")
    if not cid:
        sys.exit(f"\nKhông tìm thấy CID trong response: {data}")
    sample = os.path.basename(files[0])
    print(f"\n✅ CID: {cid}")
    print(f"   Test: https://ipfs.io/ipfs/{cid}/{sample}")
    print(f"   ipfs://{cid}/{sample}")


if __name__ == "__main__":
    main()
