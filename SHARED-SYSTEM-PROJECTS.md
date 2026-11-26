# A2A LAN share — hệ thống & dự án (26/11/2026)

Kênh: `lan-a2a` v0.3 `message/send` qua `.13:8113` ↔ `.14:8114` (echo/liveness + payload), và Hermes `peer dm` `.13 → .14` (agent thật, trả lời có phân tích).

## Reachability
- `192.168.1.12`: **DOWN** (ping không trả lời; không có agent để kết nối). Không giả định có peer ở .12.
- `192.168.1.13`: **UP** — local wired, `agent-c:8113`, Hermes native A2A `:9900`, gateway active.
- `192.168.1.14`: **UP** — `agent-b:8114`, Hermes native `:9900`, api_server `:8642` (health 200), SSH :22 mở.

## Discover / call thật
- `lan-a2a discover`: `agent-c OK`, `agent-b OK`, `agent-a (.11) UNREACHABLE`.
- `lan-a2a call --node agent-b --text 'PEER-OK…'` → echo xác nhận `received 23 chars`.
- `a2a.py send --to lan-14 --message-file REAL-PEER-REQUEST.md --timeout 240` → `ok=true`, `transport=peer`, 124.3s, phản hồi thật từ agent .14.

## Dữ liệu hệ thống đã trao đổi
### agent-c (.13, local)
Ubuntu 26.04.1 / kernel 7.0.0-44 / x86_64; i7-3520M 4 threads; RAM 11Gi (5.7Gi used); disk 226G (144G free); GPU renderer llvmpipe. Hermes gateway active. Listeners: 8113, 9900, 8080 (game web), 3001, 5432.

### agent-b (.14, peer trả lời)
Ubuntu 26.04.1 / kernel 7.0.0-44; i5-5250U @1.6GHz; RAM 15Gi (7.5Gi rảnh); disk 455G (321G rảnh); GPU Intel HD 6000 + GeForce 610M, renderer llvmpipe. Ports 8114/9900/8642 đều LISTEN. Peer giữ AI-Film-Studio (18 stage) và game-survival phần research/server; **không có `environment.js`** — code game 3D chỉ nằm trên .13.

## Dự án chia sẻ
- **Chính**: AI Film Studio (partly implemented), Game sinh tồn Online (`e2393c7` + môi trường 3D mới chưa commit).
- **Phụ**: lan-a2a (.13↔.14), n8n bridge, bảo trì hạ tầng, engine toolkit (Godot/O3DE/GameMaker + id Tech/GemRB CONCEPT).

## Góp ý từ peer .14 & xử lý
1. *"Xóa 24 PointLight, dùng emissive giả sáng"* → **không áp dụng**: 24 đầu đèn trong `environment.js` là mesh `StandardMaterial` phát sáng, không phải `PointLight`; đèn pha `SpotLight` đã tắt trong chế độ `lite`. Không có PointLight nào để xóa.
2. *"Freeze material / giảm trạng thái shader; không freeze active meshes vì recycle"* → **đã áp dụng**: `environment.js` gọi `StandardMaterial.freeze()` cho mọi material tĩnh sau khi setup xong. Cố tình **không** gọi `scene.freezeActiveMeshes()`/`freezeWorldMatrix()` vì cảnh được tái sử dụng theo vị trí xe — freeze sẽ làm đổ vỡ recycle.
3. *"MergeMeshes hoặc scaling level 3 nếu vẫn thấp"* → **không áp dụng ngay**: đã dùng `createInstance` (batch theo material); thử `setHardwareScalingLevel(2.5)`实测 không cải thiện (6.49 FPS so với 6.72 ở mức 2), nên giữ 2 để không làm mờ ảnh.

## Bảo vệ
Không đụng XMRig, port 20128, firewall; không gửi secret/token qua A2A. `.12` chỉ được ghi nhận là offline, không tạo registry entry giả.
