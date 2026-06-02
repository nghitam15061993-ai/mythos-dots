# IPFS — Kết quả upload (Filebase, 2026-06-02)

Bucket Filebase: `adumami` (IPFS) — đã pin.

## CID
- **Images**:   `bafybeifg7qyfe7jcfccgn3i7skbh7u5emqbb3atr4axwuojt66ol4xmi6e`
  → `ipfs://CID_IMAGES/<id>.png`
- **Metadata**: `bafybeicdxyjzpiuiyd4snbqp3v2defc7dep2w2ajjtqkycwl3h6reejb5a`
  → `ipfs://CID_METADATA/<id>.json`

## BASE_URI cho contract
```
ipfs://bafybeicdxyjzpiuiyd4snbqp3v2defc7dep2w2ajjtqkycwl3h6reejb5a/
```
(đã điền sẵn vào `contract/.env.example`)

## Verify
- https://ipfs.filebase.io/ipfs/bafybeifg7qyfe7jcfccgn3i7skbh7u5emqbb3atr4axwuojt66ol4xmi6e/1.png → 200
- https://ipfs.filebase.io/ipfs/bafybeicdxyjzpiuiyd4snbqp3v2defc7dep2w2ajjtqkycwl3h6reejb5a/1.json → 200
- 1.json.image trỏ đúng CID_IMAGES/1.png ✅

## Lưu ý vận hành
- Giữ 2 object CAR trong bucket `adumami` để Filebase tiếp tục pin (đừng xóa).
- File CAR gốc: `/tmp/images.car`, `/tmp/metadata.car` (có thể build lại bằng ipfs-car nếu cần).
