# VM fleet — vai trò & chống ghi đè

Ba VM do user cấp toàn quyền (SSH InstaBox, port 2222). Chi tiết kết nối do user cung cấp, **không lưu trong git**. Điều phối qua A2A; peer chỉ tư vấn, không sửa repo.

## Phân công (theo gợi ý A2A peer)
| VM | Host | Vai trò | Workspace riêng | Chỉ ghi |
|---|---|---|---|---|
| VM1 | `instabox-thienhongan0908` | CI/test runner game | `~/game-survival`, `~/ci-runs` | `ci-latest.json`, `web.summary`, `web.log` |
| VM2 | `instabox-thienhongan0794` | Render frame AI Film Studio | `~/renders` | `frame.png`, `render-latest.json` |
| VM3 | `instabox-bancaitien` | Encode MP4 + backup/monitor | `~/encode`, `~/health`, `~/lan-a2a` | `sample.mp4`, `status.json` |

**Luật chống chồng chéo:** mỗi VM một workspace/profile riêng; không 2 process dùng chung profile; VM1 không đụng `renders/`, VM2 không đụng `ci-runs/`, VM3 read-only backup. Artifact kéo về `.13` phải đặt tên prefix theo VM (`ci-latest.json`, `render-latest.json`, `status.json`) — không dùng chung tên `latest.json`.

## Kết quả chạy thật (26/11/2026)
- VM1 CI: snapshot commit `04fb181`, `node --test web/tests` → **44/44 pass, 0 fail**; `ci-latest.json` `web_rc=0`.
- VM2 Render: Chromium headless → `frame.png` **1280×720, 352 KB**; `render-latest.json` có host/time.
- VM3 Encode: ffmpeg `testsrc` → `sample.mp4` **31 KB, 2.000000 s** (ffprobe verify cả trên VM và local); `status.json` free 3.8G.
- Artifact đối chiếu tại `VM-ARTIFACTS/` (local `.13`).

## Script khởi động lại
- `vm1_ci.sh`, `vm2_render.sh`, `vm3_encode.sh` — chạy bằng `ssh -p 2222 … 'bash -s' < script`.
- VM1 nhận snapshot repo qua `tar` từ `.13` (repo private, clone trực tiếp trên VM không có credential).
- Không cài/gỡ service nào trên máy local; XMRig, port 20128, firewall giữ nguyên.
