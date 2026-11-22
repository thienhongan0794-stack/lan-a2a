"""A2A client helpers: fetch AgentCards and delegate tasks over the LAN."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    JSONRPCErrorResponse,
    Message,
    MessageSendConfiguration,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageSuccessResponse,
    Task,
    TextPart,
)
from a2a.utils import get_message_text


async def fetch_card(base_url: str, *, timeout: float = 10.0) -> AgentCard:
    """Fetch the AgentCard from a node's /.well-known/agent-card.json."""
    async with httpx.AsyncClient(timeout=timeout) as hc:
        resolver = A2ACardResolver(hc, base_url)
        return await resolver.get_agent_card()


async def send_text(
    base_url: str,
    text: str,
    *,
    timeout: float = 120.0,
    blocking: bool = True,
) -> str:
    """Send a text task to an A2A agent and return its text result.

    Raises RuntimeError if the remote agent reports a failed task.
    """
    async with httpx.AsyncClient(timeout=timeout) as hc:
        resolver = A2ACardResolver(hc, base_url)
        card = await resolver.get_agent_card()
        client = A2AClient(httpx_client=hc, agent_card=card, url=base_url)
        request = SendMessageRequest(
            id=str(uuid.uuid4()),
            jsonrpc="2.0",
            method="message/send",
            params=MessageSendParams(
                message=Message(
                    role=Role.user,
                    parts=[Part(root=TextPart(text=text))],
                    message_id=str(uuid.uuid4()),
                ),
                configuration=MessageSendConfiguration(
                    blocking=blocking,
                    accepted_output_modes=["text/plain"],
                ),
            ),
        )
        response = await client.send_message(request)
        return _extract_response_text(response.root)


async def stream_text(
    base_url: str,
    text: str,
    *,
    timeout: float = 120.0,
) -> AsyncIterator[str]:
    """Stream A2A task updates, yielding each text chunk as it arrives."""
    async with httpx.AsyncClient(timeout=timeout) as hc:
        resolver = A2ACardResolver(hc, base_url)
        card = await resolver.get_agent_card()
        client = A2AClient(httpx_client=hc, agent_card=card, url=base_url)
        request = SendMessageRequest(
            id=str(uuid.uuid4()),
            jsonrpc="2.0",
            method="message/stream",
            params=MessageSendParams(
                message=Message(
                    role=Role.user,
                    parts=[Part(root=TextPart(text=text))],
                    message_id=str(uuid.uuid4()),
                ),
            ),
        )
        async for event in client.send_message_streaming(request):
            root = getattr(event, "root", event)
            if isinstance(root, Message):
                yield get_message_text(root)
            elif isinstance(root, Task):
                for artifact in root.artifacts or []:
                    yield "".join(
                        p.root.text for p in artifact.parts if hasattr(p.root, "text")
                    )


def _extract_response_text(root: object) -> str:
    if isinstance(root, SendMessageSuccessResponse):
        return _extract_text(root.result)
    if isinstance(root, JSONRPCErrorResponse):
        raise RuntimeError(f"A2A error response: {root.error}")
    return _extract_text(root)


def _extract_text(root: object) -> str:
    if isinstance(root, Message):
        return get_message_text(root)
    if isinstance(root, Task):
        if root.status and root.status.state and "failed" in str(root.status.state):
            detail = ""
            if root.status.message:
                detail = get_message_text(root.status.message)
            raise RuntimeError(f"remote task failed: {detail}".strip())
        chunks: list[str] = []
        for artifact in root.artifacts or []:
            for part in artifact.parts:
                if hasattr(part.root, "text"):
                    chunks.append(part.root.text)
        if chunks:
            return "".join(chunks)
        if root.status and root.status.message:
            return get_message_text(root.status.message)
        return ""
    raise RuntimeError(f"unexpected A2A response type: {type(root)!r}")
