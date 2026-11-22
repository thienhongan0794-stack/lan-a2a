#!/usr/bin/env bash
# End-to-end LAN A2A verification.
#   - starts agent-c locally, agent-b is expected on 192.168.1.14:8114
#   - calls agent-b from agent-c, and agent-c from agent-b
#   - exercises the Hermes-native v1.0 client against both nodes
set -u

PY="$HOME/lan-a2a/.venv/bin/python"
HERMES_PY="$HOME/.hermes/hermes-agent/venv/bin/python"

echo "== listeners =="
ss -ltnp 2>/dev/null | grep -E ':8113|:8114' || true

echo
echo "== discover =="
"$PY" -m lan_a2a.cli discover

echo
echo "== agent-c -> agent-b =="
"$PY" -m lan_a2a.cli call --node agent-b --text "e2e ping from agent-c" --json

echo
echo "== agent-b -> agent-c =="
ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=6 \
  thienhongan0908@192.168.1.14 \
  'cd ~/lan-a2a && ~/crewai-lab/.venv/bin/python -m lan_a2a.cli call --node agent-c --text "e2e ping from agent-b" --json'

echo
echo "== Hermes v1.0 -> agent-b / agent-c =="
"$HERMES_PY" "$HOME/lan-a2a/scripts/test_hermes_direct.py"
