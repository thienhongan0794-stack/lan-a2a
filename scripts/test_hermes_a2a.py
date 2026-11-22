"""Verify the Hermes-native A2A client against the LAN gateway.

Chain: Hermes A2A v1.0 (a2a_call) -> gateway :9902 (v1.0<->v0.3) -> crewAI :9901.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.expanduser("~/.hermes/hermes-agent"))

from plugins.platforms.a2a.tools import a2a_call, a2a_discover, a2a_list  # noqa: E402


def main() -> None:
    print("=== a2a_list ===")
    print(a2a_list({}))
    print()
    print("=== discover lan-14 gateway ===")
    print(a2a_discover({"url": "http://192.168.1.14:9902"}))
    print()
    print("=== call lan-14 (crewAI backend) ===")
    print(a2a_call(
        {
            "agent": "lan-14",
            "message": "Phân tích ngắn: host 192.168.1.14 mở port 22, 8642, 9900, 9902. "
            "Có bất thường không? Trả lời tiếng Việt, 3 dòng.",
        }
    ))


if __name__ == "__main__":
    main()
