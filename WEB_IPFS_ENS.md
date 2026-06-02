# Web frontend → IPFS + ENS (phi tập trung, uy tín)

Web đã bật `output: 'export'` (static). Host trên IPFS (Filebase) + trỏ ENS `.eth`.

## 1. Build + deploy lên IPFS
Chỉ chạy SAU khi đã có **contract address** + **agent URL** (env nướng vào bundle lúc build).

```bash
cd ~/Desktop/chamau/web
cp .env.local.example .env.local   # điền NEXT_PUBLIC_CONTRACT_ADDRESS, NEXT_PUBLIC_AGENT_URL, CHAIN, WC_PROJECT_ID
# Filebase keys (đã dùng cho ảnh/metadata):
export FILEBASE_KEY=...  FILEBASE_SECRET=...  FILEBASE_BUCKET=adumami
# nạp env build từ .env.local rồi chạy:
set -a; . ./.env.local; set +a
bash deploy_ipfs.sh
```
→ in ra **CID** của web. Mở thử: `https://<CID>.ipfs.dweb.link/`

⚠️ **Phải dùng subdomain gateway** (`<CID>.ipfs.dweb.link` hoặc ENS) — asset Next dùng đường dẫn tuyệt đối `/_next/...` chỉ đúng khi CID ở **gốc domain**. Gateway path-based (`.../ipfs/<CID>/`) sẽ vỡ CSS/JS. ENS `.eth.limo` phục vụ ở gốc domain nên CHẠY ĐÚNG.

## 2. Mua + trỏ ENS
1. https://app.ens.domains → connect ví → search `mythosdots` → register (~$5/năm cho tên ≥5 ký tự, trả ETH).
2. Vào tên vừa mua → tab **Records** → **Content Hash** → đặt `ipfs://<CID>`.
3. Lưu (1 tx on-chain).
4. Truy cập: **`https://mythosdots.eth.limo`** (hoặc `mythosdots.eth` trên Brave/ví hỗ trợ ENS).

## 3. Mỗi lần cập nhật web
Build + upload lại → CID mới → sửa Content Hash trong ENS (1 tx gas mỗi lần). Với mint thường set 1 lần là đủ.

## Lưu ý
- Frontend phi tập trung, nhưng **agent vẫn là server tập trung** (Render/Railway). Web gọi agent qua `NEXT_PUBLIC_AGENT_URL` (HTTPS + CORS đã bật).
- Đổi agent URL = phải build lại web + cập nhật ENS. Nên chốt domain agent trước khi build web production.
