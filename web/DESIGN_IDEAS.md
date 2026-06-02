# Web mint — Ý tưởng UI (để sau)

## Concept: bầy chấm gradient trôi nổi, ấn để mint
UI chính = một field nhiều **hình tròn dot gradient trôi nổi** (đúng style NFT của bộ này).
Người dùng **ấn vào 1 chấm** → khởi động flow mint.

- Các dot drift/floating nhẹ (như bong bóng), màu lấy từ thư viện gradient (`agent/gradients.py` /
  hoặc tái tạo bằng CSS conic/radial-gradient).
- Hover: dot phồng nhẹ + glow. Click: dot "nở" ra → mở panel đoán chữ.
- Sau khi giải đúng → dot biến thành preview NFT vừa khóa quota → nút Mint.
- Nền tối, vibe degen/JRPG hợp tông ảnh.

## Map vào flow hiện có
ấn dot → `POST /api/session` → quiz lật chữ 2s (overlay) → `POST /api/guess` →
pass → `mintWithPass` (trả ETH). Tức là chỉ thay lớp trình bày, logic giữ nguyên.

## Gợi ý kỹ thuật (khi dựng)
- Animation: CSS keyframes / Framer Motion / canvas (nhiều dot thì canvas/WebGL mượt hơn).
- Mỗi dot 1 gradient ngẫu nhiên (giống token) — có thể preview chính token sắp mint.
- Giữ static-export được (IPFS) → tránh thư viện cần server.

## TODO khi làm
- [ ] (đợi ảnh tham khảo nếu user gửi)
- [ ] Component DotField (floating dots)
- [ ] Click dot → mở QuizPanel (đang là form phẳng trong app/page.tsx)
- [ ] Chuyển card UI hiện tại → overlay/modal trên nền DotField
