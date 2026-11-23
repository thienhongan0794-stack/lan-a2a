# lan-a2a

A2A (Agent-to-Agent) gateway cho các agent trong nội bộ LAN, dựng trên
**crewAI** (`crewai[a2a]`) và `a2a-sdk`. Mỗi node LAN chạy một server A2A nhỏ,
công bố `AgentCard` tại `/.well-known/agent-card.json` và thực thi task bằng
một handler local. Bất kỳ A2A client nào trong LAN (Hermes, crewAI, CLI này)
cũng có thể phát hiện và giao task sang node khác.

## Ba giải pháp A2A hiện có trên LAN

| # | Giải pháp | Protocol | Vị trí | Trạng thái |
|---|-----------|----------|--------|------------|
| 1 | **Hermes A2A platform** (native) | A2A **v1.0** (`SendMessage`) | `~/.hermes/hermes-agent/plugins/platforms/a2a/` | sẵn có; inbound `:9900` (đã bật + token + `A2A_TRUSTED_PEERS`), outbound tools `a2a_call/discover/list/history/orchestrate` |
| 2 | **lan-a2a** (repo này) | A2A **v0.3** (`message/send`) + **chuẩn hóa v1.0↔v0.3** | `~/lan-a2a` | đã chạy `:8113` (agent-c), `:8114` (agent-b); chưa có auth |
| 3 | **Hermes `bot_peers`** | HTTP JSON qua `api_server` | `config.yaml: bot_peers` | đã cấu hình `agent-b`, `lan-14` |

Ngoài ra `.14` có `~/crewai-lab/lan-agents/a2a_gateway.py` (`:9902`) — bridge
v1.0↔v0.3 fronting một crewAI crew (`:9901`) phân tích nmap/arp.

## Kiến trúc

```
Hermes agent (v1.0)  ──►  lan-a2a node ──┐
                                          ├─► NodeAgentExecutor ─► handler local
crewAI / a2a-sdk (v0.3) ─► lan-a2a node ──┘
```

`lan_a2a/dialect.py` là pure-ASGI middleware: rewrite `SendMessage` →
`message/send` và `ROLE_USER`/`ROLE_AGENT` → `user`/`agent`, nên cùng một
endpoint chấp nhận cả hai dialect.

## Cài đặt

```bash
cd ~/lan-a2a
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python \
  -e "$HOME/crewAI/lib/crewai[a2a]" fastapi uvicorn httpx
```

## Chạy

```bash
# server cho một node
.venv/bin/python -m lan_a2a.cli serve --node agent-c --port 8113

# phát hiện + gọi
.venv/bin/python -m lan_a2a.cli discover
.venv/bin/python -m lan_a2a.cli call --node agent-b --text "ping" --json
```

## Test

```bash
.venv/bin/python -m unittest discover -s tests -v   # 4/4 pass
```

## Bằng chứng xuyên LAN (đã chạy thật)

- `agent-c (192.168.1.13:8113) → agent-b (192.168.1.14:8114)`: ✅
- `agent-b → agent-c`: ✅
- Hermes A2A **v1.0** `a2a_call` → `agent-b` và `agent-c`: ✅ (qua normalizer)
- Hermes A2A **v1.0** `a2a_call` → gateway `:9902` → crewAI crew `:9901`: ✅
  (trả báo cáo tiếng Việt)
- Hermes native `:9900` hai chiều `.13 ↔ .14` (v1.0 `SendMessage`, có bearer token): ✅
  - `.13 → .14:9900`: `TASK_STATE_COMPLETED`
  - `.14 → .13:9900`: `TASK_STATE_COMPLETED`
  - không token → `401`; token sai/peer lạ → `403` (fail-closed)
- `.13 → .14:9902` (crewAI crew): ✅ báo cáo tiếng Việt
- `agent-a (192.168.1.11:8115)`: offline (máy tắt)

## Registry

`registry.json` là nguồn dữ liệu duy nhất: mỗi node có `id`, `host`, `port`,
`user`, `role`, `skills`. `lan_a2a/cli.py --registry` đổi đường dẫn.

## Bảo mật

- Chưa cấu hình token thì chỉ nên bind loopback.
- Với Hermes dùng `a2a_agents.*.auth` (bearer) + `A2A_BEARER_TOKEN` /
  `A2A_PEER_TOKENS`; không token => Hermes bind `127.0.0.1`.
- Token `lan-14` được đặt trong `~/.hermes/.env`, không commit.
