"""A2A server construction for a LAN node."""

from __future__ import annotations

import uvicorn
from a2a.server.agent_execution import AgentExecutor
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
)

from lan_a2a.dialect import DialectNormalization
from lan_a2a.executor import local_hostname


def build_agent_card(
    node_id: str,
    url: str,
    *,
    description: str | None = None,
    skills: list[dict] | None = None,
    version: str = "1.0.0",
    streaming: bool = True,
) -> AgentCard:
    """Build the A2A AgentCard advertised at /.well-known/agent-card.json."""
    skills = skills or [
        {
            "id": "echo",
            "name": "echo",
            "description": "Echo the task text and report this node's identity.",
            "tags": ["echo", "identity"],
        },
        {
            "id": "shell",
            "name": "shell",
            "description": "Run a local shell command with the task text on stdin.",
            "tags": ["shell", "local"],
        },
    ]
    return AgentCard(
        name=f"LAN Agent {node_id}",
        description=description
        or f"A2A gateway for LAN node {node_id} ({local_hostname()})",
        url=url,
        version=version,
        capabilities=AgentCapabilities(
            streaming=streaming, push_notifications=False
        ),
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["text/plain", "application/json"],
        skills=[
            AgentSkill(
                id=s["id"],
                name=s["name"],
                description=s["description"],
                tags=s.get("tags", []),
                examples=s.get("examples", []),
            )
            for s in skills
        ],
        provider=AgentProvider(organization="LAN", url="https://lan.local"),
    )


def build_app(card: AgentCard, executor: AgentExecutor) -> A2AFastAPIApplication:
    """Wire an executor into an A2A FastAPI application."""
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    return A2AFastAPIApplication(agent_card=card, http_handler=request_handler)


def build_asgi(card: AgentCard, executor: AgentExecutor):
    """Return the A2A ASGI app with v1.0<->v0.3 dialect normalization."""
    return DialectNormalization(build_app(card, executor).build())


def serve(
    card: AgentCard,
    executor: AgentExecutor,
    *,
    host: str = "0.0.0.0",
    port: int = 8113,
    log_level: str = "info",
) -> None:
    """Run the A2A server with uvicorn (blocking)."""
    uvicorn.run(build_asgi(card, executor), host=host, port=port, log_level=log_level)
