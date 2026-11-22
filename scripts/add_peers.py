"""Append the LAN a2a_agents block to ~/.hermes/config.yaml (idempotent).

The bearer token is read from ~/.lan_token and never printed.
"""

from __future__ import annotations

import pathlib

CONFIG = pathlib.Path.home() / ".hermes" / "config.yaml"
TOKEN_FILE = pathlib.Path.home() / ".lan_token"

BLOCK = """a2a_agents:
  lan-14:
    url: http://192.168.1.14:9902
    auth:
      type: bearer
      token: {token}
    timeout: 300
    capabilities:
      - lan-analysis
      - vietnamese-report
  agent-b:
    url: http://192.168.1.14:8114
    timeout: 30
    capabilities:
      - echo
      - shell
  agent-c:
    url: http://192.168.1.13:8113
    timeout: 30
    capabilities:
      - echo
      - shell
"""


def main() -> None:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        raise SystemExit("missing token")
    text = CONFIG.read_text(encoding="utf-8")
    if "a2a_agents:" in text:
        raise SystemExit("a2a_agents already present; edit manually")
    if not text.endswith("\n"):
        text += "\n"
    text += "\n" + BLOCK.format(token=token)
    CONFIG.write_text(text, encoding="utf-8")
    print("appended a2a_agents block")


if __name__ == "__main__":
    main()
