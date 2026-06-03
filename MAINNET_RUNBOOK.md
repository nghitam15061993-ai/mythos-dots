# Mythos Dots — Mainnet Launch Runbook

⚠️ Tiền thật + vĩnh viễn. Dùng **KEY MỚI** (key testnet đã lộ trong chat). Lý tưởng: key không bao giờ paste vào chat — bạn tự chạy các lệnh dưới trong terminal.

---

## 0) Mua domain (~$1-2)
Porkbun / Namecheap → mua `mythosdots.xyz` (hoặc tên bạn thích). Để đó, bước 6 trỏ DNS.

## 1) Tạo ví DEPLOY mới (terminal của bạn)
> Agent key TÁI DÙNG ví cũ `0xe61Aa0dD87807ffaD1439d086345ddd0b5d571F4` (bạn chọn vậy, rotate sau bằng setAgentSigner nếu cần). CHỈ tạo ví deploy mới — vì ví này giữ quyền rút tiền.
```bash
export PATH="$HOME/.foundry/bin:$PATH"
cast wallet new        # DEPLOY/owner → lưu ADDRESS + PRIVATE KEY riêng (KHÔNG paste vào chat)
```
- Nạp **~0.08 ETH thật** vào ví deploy.
- Ví nhận royalty: dùng 1 ví **an toàn/cold** (khác ví deploy hot).

## 2) Cấu hình deploy (sửa `contract/.env`)
```
PRIVATE_KEY=<PRIVATE KEY ví B>
MAINNET_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/<KEY>
ETHERSCAN_API_KEY=<key>
MAX_SUPPLY=7777
PRICE_FEED=0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419   # Chainlink ETH/USD mainnet
AGENT_SIGNER=0xe61Aa0dD87807ffaD1439d086345ddd0b5d571F4   # ví agent cũ (tái dùng)
BASE_URI=ipfs://bafybeicdxyjzpiuiyd4snbqp3v2defc7dep2w2ajjtqkycwl3h6reejb5a/
ROYALTY_RECEIVER=<ví an toàn>
```

## 3) Deploy + verify
```bash
cd ~/Desktop/chamau/contract
forge test                               # 15/15 phải pass
set -a; . ./.env; set +a
forge script script/Deploy.s.sol:Deploy --rpc-url mainnet --broadcast --verify -vvvv
```
→ Ghi lại **CONTRACT_ADDRESS** (dòng `MythosDots:`).

## 4) Bảo vệ quyền sở hữu (khuyên làm)
Owner = ví B (hot) có quyền `withdraw` toàn bộ doanh thu mint. Chuyển owner sang ví cold/multisig:
```bash
cast send <CONTRACT> "transferOwnership(address)" <VÍ_COLD> --rpc-url mainnet --private-key $PRIVATE_KEY
```
(Sau đó setSaleActive/withdraw ký bằng ví cold.)

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

## 7) Mở bán
```bash
cast send <CONTRACT> "setSaleActive(bool)" true --rpc-url mainnet --private-key <owner key>
```
Test mint thật bằng 1 ví khác → kiểm tra trên Etherscan + OpenSea (opensea.io, contract sẽ tự index).

---

## Nhắc
- Metadata đang trên **Filebase free** — cho collection thật nên đảm bảo bucket `adumami` không bị xoá (cân nhắc pin dự phòng / gói trả phí).
- `CHAIN_ID=1` (agent) và `NEXT_PUBLIC_CHAIN=mainnet` (web) phải khớp contract mainnet, nếu không pass sẽ sai domain EIP-712 → mint revert.
- Giá phase giữ USD, trả ETH quy đổi oracle như testnet.
