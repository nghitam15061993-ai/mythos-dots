# Mythos Dots — Deploy Guide (degen pass-gated mint)

Kiến trúc 3 phần: **IPFS** (xong) → **Contract** (ERC721A pass-gated) → **Agent** (chấm quiz + ký pass) → **Web** (chơi + mint).

Mô hình: giải đoán chữ → agent ký EIP-712 pass {wallet,quota,nonce,deadline} → **pay-at-lock**: mint full quota + trả **ETH** ngay (1 flow). Cap 10/ví on-chain. Giá 4 phase theo thứ tự mint, niêm yết USD nhưng **trả bằng ETH — contract tự quy đổi qua Chainlink ETH/USD, hoàn dust**.

| Phase | Token | Giá |
|---|---|---|
| 1 | 1–777 | $0.03 |
| 2 | 778–3111 | $0.15 |
| 3 | 3112–5444 | $0.25 |
| 4 | 5445–7777 | $0.35 |
(1 tx vắt qua mép phase được tính giá per-NFT chính xác bằng `costFor`.)

---

## BƯỚC 1 — IPFS ✅ XONG
Xem `IPFS_RESULT.md`. `BASE_URI = ipfs://bafybeicdxy…ejb5a/` (đã điền sẵn `contract/.env.example`).

---

## BƯỚC 2 — Deploy contract (Foundry)

Foundry + lib đã cài sẵn, **test 12/12 PASS**. Verify lại:
```bash
export PATH="$HOME/.foundry/bin:$PATH"
cd ~/Desktop/chamau/contract && forge test -vv
```

Tạo ví agent signer (KHÁC ví deploy) — đây là ví ký pass off-chain:
```bash
cast wallet new          # lưu address → AGENT_SIGNER ; private key → agent/.env (AGENT_PRIVATE_KEY)
```

Cấu hình + deploy:
```bash
cp .env.example .env     # điền PRIVATE_KEY, RPC, ETHERSCAN_API_KEY, PRICE_FEED(Chainlink ETH/USD), AGENT_SIGNER
source .env
# Sepolia trước:
forge script script/Deploy.s.sol:Deploy --rpc-url sepolia --broadcast --verify -vvvv
# Mainnet khi chắc:
forge script script/Deploy.s.sol:Deploy --rpc-url mainnet --broadcast --verify -vvvv
```
Ghi lại địa chỉ contract. Mở sale:
```bash
cast send <CONTRACT> "setSaleActive(bool)" true --rpc-url sepolia --private-key $PRIVATE_KEY
```

---

## BƯỚC 3 — Agent service (quiz + ký pass)

```bash
cd ~/Desktop/chamau/agent
npm install                      # đã cài
npm run fetch-words              # words.txt (đã có 6.5k từ)
cp .env.example .env             # AGENT_PRIVATE_KEY, CONTRACT_ADDRESS, CHAIN_ID, RPC_URL
npm run start                    # :8787
```
Endpoints: `POST /api/session {wallet}` · `GET /api/peek/:id` · `POST /api/guess {sessionId,guess}` · `GET /api/state`.

⚠️ `AGENT_PRIVATE_KEY` phải khớp `AGENT_SIGNER` đã set trong contract. Production: KMS, không plaintext. Đặt sau reverse-proxy + giữ rate-limit.

**Availability (chống over-issue):** agent phát pass chỉ khi `maxSupply − totalMinted(on-chain) − Σ pending(TTL ngắn) ≥ quota`. Restart = pending rỗng (under-issue an toàn). Single instance.

---

## BƯỚC 4 — Web mint

```bash
cd ~/Desktop/chamau/web
npm install                      # đã cài
cp .env.local.example .env.local # CONTRACT_ADDRESS, CHAIN, AGENT_URL, WC_PROJECT_ID
npm run dev                      # localhost:3000
```
Flow UI: connect ví → "Bắt đầu đoán chữ" (chữ lật mỗi 2s) → đoán đúng → hiện quota + giá ETH → "Mint" (gửi ETH = costForEth + đệm 5%, contract hoàn dust).

Deploy: push GitHub → Vercel → khai env.

---

## Artifacts
| | |
|---|---|
| `out/images`, `out/metadata` | 7777 ảnh + metadata (trên IPFS) |
| `contract/` | ERC721A pass-gated, 12 test |
| `agent/` | Node+viem service |
| `web/` | Next.js mint + quiz |
| `rarity.py`, `out/rarity_ranking.csv` | rarity local (OpenSea tự tính OpenRarity) |

## Lưu ý đã review (xem lại nếu cần)
- Bot gần như luôn thắng quiz → FCFS = đua bot + nhiều ví (cap chỉ 10/ví, KHÔNG chống Sybil). Degen có chủ đích.
- Agent là SPOF (down = ngừng mint). Cân nhắc HA nếu cần.
- Trả ETH 1 tx (không cần approve). Oracle Chainlink: contract chặn answer≤0 và quá cũ (`maxOracleAge` mặc định 1h, chỉnh bằng `setMaxOracleAge`).
