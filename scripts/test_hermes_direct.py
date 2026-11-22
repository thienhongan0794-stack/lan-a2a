"""Hermes-native A2A v1.0 -> lan-a2a nodes (agent-b, agent-c) directly."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.expanduser("~/.hermes/hermes-agent"))

from plugins.platforms.a2a.tools import a2a_call  # noqa: E402


def main() -> None:
    for agent in ("agent-b", "agent-c"):
        print(f"=== a2a_call {agent} ===")
        print(a2a_call(
            {"agent": agent, "message": f"ping from hermes v1.0 to {agent}"}
        ))
        print()


if __name__ == "__main__":
    main()
