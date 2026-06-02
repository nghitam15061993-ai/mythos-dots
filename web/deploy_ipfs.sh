#!/usr/bin/env bash
# Build web static → pack CAR → upload Filebase IPFS → in CID.
# CHẠY SAU KHI đã có contract address + agent URL (env build bị nướng vào bundle).
#
# Cần env:
#   build : NEXT_PUBLIC_CONTRACT_ADDRESS, NEXT_PUBLIC_AGENT_URL, NEXT_PUBLIC_CHAIN, NEXT_PUBLIC_WC_PROJECT_ID
#   upload: FILEBASE_KEY, FILEBASE_SECRET, FILEBASE_BUCKET
set -euo pipefail
cd "$(dirname "$0")"

echo "== next build (static export) =="
node_modules/.bin/next build

echo "== pack CAR (root = nội dung out/, index.html ở gốc) =="
npx --yes ipfs-car@latest pack out --no-wrap --output /tmp/web.car

echo "== upload Filebase =="
python3 ../filebase_upload_car.py /tmp/web.car web.car

echo ""
echo "⚠️ Mở thử bằng SUBDOMAIN gateway (đường dẫn tuyệt đối /_next/ chỉ đúng ở subdomain/ENS):"
echo "   https://<CID>.ipfs.dweb.link/"
echo "   KHÔNG dùng gateway path-based (gateway/ipfs/<CID>/) — sẽ vỡ asset."
