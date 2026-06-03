# Mythos Dots — Mainnet Launch Runbook

⚠️ Tiền thật + vĩnh viễn. Dùng **KEY MỚI** (key testnet đã lộ trong chat). Lý tưởng: key không bao giờ paste vào chat — bạn tự chạy các lệnh dưới trong terminal.

---

## 0) Mua domain (~$1-2)
Porkbun / Namecheap → mua `mythosdots.xyz` (hoặc tên bạn thích). Để đó, bước 6 trỏ DNS.

## 1) Ví (theo lựa chọn của bạn)
- **DEPLOY**: tái dùng ví testnet `0x603015635b22E97E873f6ebE7706bb43b5Fe1DA3` → **nạp ~0.08 ETH thật** vào ví này. (Chỉ tốn gas; sẽ bị tước quyền ở bước 4.)
- **AGENT signer**: tái dùng `0xe61Aa0dD87807ffaD1439d086345ddd0b5d571F4` (rotate sau bằng setAgentSigner nếu cần).
- **OWNER + ROYALTY**: ví an toàn `0x9cfb22ca51327FD9fAffcF4851B81F127eb71369` (MetaMask, key chưa lộ).

## 2) Cấu hình deploy — `contract/.env` đã pre-fill sẵn, chỉ cần điền 2 dòng:
```
MAINNET_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/<KEY>
ETHERSCAN_API_KEY=<key>
```
(PRIVATE_KEY=ví testnet 0x6030, PRICE_FEED mainnet, AGENT_SIGNER, ROYALTY_RECEIVER=0x9cfb… đã set sẵn.)

## 3) Deploy + verify
```bash
cd ~/Desktop/chamau/contract
forge test                               # 15/15 phải pass
set -a; . ./.env; set +a
forge script script/Deploy.s.sol:Deploy --rpc-url mainnet --broadcast --verify -vvvv
```
→ Ghi lại **CONTRACT_ADDRESS** (dòng `MythosDots:`).

## 4) ⚠️ BẮT BUỘC NGAY SAU DEPLOY — chuyển owner về ví an toàn
Ví deploy testnet đã lộ trong chat; phải tước quyền nó ngay:
```bash
cast send <CONTRACT> "transferOwnership(address)" 0x9cfb22ca51327FD9fAffcF4851B81F127eb71369 \
  --rpc-url mainnet --private-key $PRIVATE_KEY
```
Sau lệnh này, ví testnet **không còn quyền gì**. Mọi thao tác owner (setSaleActive, withdraw) từ giờ ký bằng ví `0x9cfb…` — dễ nhất là dùng **Etherscan → Contract → Write** kết nối MetaMask (không cần paste private key).

## 5) Agent lên mainnet (Render)
- Render → service **mythos-agent** → **Settings → Instance Type → Starter ($7)** (always-on).
- **Environment** sửa (AGENT_PRIVATE_KEY giữ nguyên ví cũ):
  - `CONTRACT_ADDRESS` = <mainnet contract>
  - `CHAIN_ID` = `1`
  - `RPC_URL` = <mainnet RPC>
- Manual Deploy → test `https://mythos-agent.onrender.com/api/state` (maxSupply 7777, totalMinted 0).

## 6) Web lên mainnet + domain
- Render → static site **mythos-dots** → **Environment** sửa:
  - `NEXT_PUBLIC_CONTRACT_ADDRESS` = <mainnet contract>
  - `NEXT_PUBLIC_CHAIN` = `mainnet`
  - (AGENT_URL, WC_PROJECT_ID giữ nguyên)
- **Clear build cache & deploy**.
- **Settings → Custom Domains → Add** `mythosdots.xyz` và `www.mythosdots.xyz`.
- Sang registrar (Porkbun…) thêm DNS Render chỉ:
  - `www` → CNAME → `mythos-dots.onrender.com`
  - apex `@` → ALIAS/ANAME (hoặc A record) theo giá trị Render hiển thị.
  - HTTPS Render tự cấp (~vài phút).

## 7) Mở bán (ký bằng owner 0x9cfb… qua Etherscan, KHÔNG paste key)
Etherscan → contract `0x…` → **Contract → Write** → **Connect to Web3** (MetaMask ví 0x9cfb…) → `setSaleActive` = `true` → Write.
Test mint thật bằng 1 ví khác → kiểm tra Etherscan + OpenSea (opensea.io tự index).
Rút doanh thu: cũng ở Write → `withdraw(to)`.

---

## Nhắc
- Metadata đang trên **Filebase free** — cho collection thật nên đảm bảo bucket `adumami` không bị xoá (cân nhắc pin dự phòng / gói trả phí).
- `CHAIN_ID=1` (agent) và `NEXT_PUBLIC_CHAIN=mainnet` (web) phải khớp contract mainnet, nếu không pass sẽ sai domain EIP-712 → mint revert.
- Giá phase giữ USD, trả ETH quy đổi oracle như testnet.
