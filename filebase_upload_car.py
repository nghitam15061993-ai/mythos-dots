#!/usr/bin/env python3
"""
filebase_upload_car.py — Upload 1 file CAR lên Filebase (IPFS) → in root CID thư mục.

Filebase nhận CAR qua S3 với metadata import=car, rồi pin nguyên thư mục.
Ép upload 1-part (không multipart) để CAR import hoạt động đúng.

CHUẨN BỊ (1 lần):
  - filebase.com → tạo bucket loại IPFS
  - Access Keys → copy Access Key + Secret Key
  export FILEBASE_KEY="..."  FILEBASE_SECRET="..."  FILEBASE_BUCKET="ten-bucket"

DÙNG:
  python3 filebase_upload_car.py /tmp/images.car images.car
  python3 filebase_upload_car.py /tmp/metadata.car metadata.car
"""
import os
import sys
import time

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config

ENDPOINT = "https://s3.filebase.com"


def main():
    if len(sys.argv) < 3:
        sys.exit("Dùng: python3 filebase_upload_car.py <file.car> <object-key>")
    car_path, key = sys.argv[1], sys.argv[2]
    ak = os.environ.get("FILEBASE_KEY")
    sk = os.environ.get("FILEBASE_SECRET")
    bucket = os.environ.get("FILEBASE_BUCKET")
    if not (ak and sk and bucket):
        sys.exit("Thiếu env FILEBASE_KEY / FILEBASE_SECRET / FILEBASE_BUCKET")

    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=ak,
        aws_secret_access_key=sk,
        region_name="us-east-1",
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )

    size = os.path.getsize(car_path)
    # ép single-part: threshold/chunk > size
    cfg = TransferConfig(multipart_threshold=size + 1, multipart_chunksize=size + 1)
    print(f"Upload CAR {size/1e6:.0f} MB → filebase bucket '{bucket}' key '{key}'...")
    s3.upload_file(
        car_path, bucket, key,
        ExtraArgs={"Metadata": {"import": "car"}},
        Config=cfg,
    )

    # Filebase tính CID sau khi pin → poll head_object lấy x-amz-meta-cid
    cid = None
    for _ in range(30):
        h = s3.head_object(Bucket=bucket, Key=key)
        md = {k.lower(): v for k, v in h.get("Metadata", {}).items()}
        cid = md.get("cid")
        if cid:
            break
        time.sleep(2)
    if not cid:
        sys.exit("Không lấy được CID (Metadata.cid trống) — kiểm tra bucket có phải loại IPFS?")
    print(f"\n✅ ROOT CID: {cid}")
    print(f"   Test: https://{cid}.ipfs.dweb.link/  (mở thử /1.png hoặc /1.json bên trong)")
    print(f"   ipfs://{cid}/")


if __name__ == "__main__":
    main()
