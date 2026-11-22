"""LAN node registry.

`registry.json` is the single source of truth for which A2A agents exist on
the internal LAN. Each node advertises an AgentCard at
http://<host>:<port>/.well-known/agent-card.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_REGISTRY = Path(__file__).resolve().parent.parent / "registry.json"


@dataclass(frozen=True)
class Node:
    id: str
    host: str
    port: int
    user: str | None = None
    role: str = "worker"
    skills: tuple[str, ...] = ()

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def card_url(self) -> str:
        return f"{self.base_url}/.well-known/agent-card.json"


def load_registry(path: str | Path | None = None) -> list[Node]:
    reg_path = Path(path) if path else DEFAULT_REGISTRY
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    nodes: list[Node] = []
    for raw in data.get("nodes", []):
        nodes.append(
            Node(
                id=raw["id"],
                host=raw["host"],
                port=int(raw["port"]),
                user=raw.get("user"),
                role=raw.get("role", "worker"),
                skills=tuple(raw.get("skills", ())),
            )
        )
    return nodes


def get_node(node_id: str, path: str | Path | None = None) -> Node:
    for node in load_registry(path):
        if node.id == node_id:
            return node
    raise KeyError(f"node {node_id!r} not in registry")
