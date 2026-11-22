"""A2A agent executor backed by a local handler.

The executor is the only node-specific piece: it takes the text of an
incoming A2A message and produces a text result. Everything else
(card, JSON-RPC transport, registry) is shared across all LAN nodes.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import socket
import uuid
from collections.abc import Awaitable, Callable

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)
from a2a.utils import build_text_artifact, new_task

Handler = Callable[[str], Awaitable[str] | str]


def local_hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:  # pragma: no cover - defensive
        return "unknown"


def result_payload(node_id: str, host: str, received: str, result: str) -> str:
    """Wrap a handler result in a JSON envelope so the caller can verify origin."""
    return json.dumps(
        {
            "node": node_id,
            "host": host,
            "received": received,
            "result": result,
        },
        ensure_ascii=False,
    )


class NodeAgentExecutor(AgentExecutor):
    """Runs incoming A2A tasks through a local handler on the hosting node."""

    def __init__(
        self,
        node_id: str,
        handler: Handler,
        *,
        host: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.node_id = node_id
        self.host = host or local_hostname()
        self.handler = handler
        self.timeout = timeout

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = context.get_user_input() or ""
        task: Task = new_task(context.message)  # type: ignore[arg-type]
        task.status = TaskStatus(state=TaskState.working)
        await event_queue.enqueue_event(task)

        try:
            raw = self.handler(text)
            if inspect.isawaitable(raw):
                raw = await asyncio.wait_for(raw, timeout=self.timeout)
            payload = result_payload(self.node_id, self.host, text, str(raw))
            task.artifacts = [
                build_text_artifact(payload, artifact_id=str(uuid.uuid4()))
            ]
            task.status = TaskStatus(state=TaskState.completed)
        except Exception as exc:  # noqa: BLE001 - surface any handler failure as A2A failure
            task.status = TaskStatus(
                state=TaskState.failed,
                message=Message(
                    role=Role.agent,
                    parts=[
                        Part(
                            root=TextPart(
                                text=f"{type(exc).__name__}: {exc}"
                            )
                        )
                    ],
                    message_id=str(uuid.uuid4()),
                ),
            )

        await event_queue.enqueue_event(task)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task
        if task is None:
            return
        task.status = TaskStatus(state=TaskState.canceled)
        await event_queue.enqueue_event(task)


class ShellHandler:
    """Handler that pipes the task text to a local command's stdin."""

    def __init__(
        self,
        command: list[str],
        *,
        timeout: float = 120.0,
        cwd: str | None = None,
    ) -> None:
        self.command = command
        self.timeout = timeout
        self.cwd = cwd

    async def __call__(self, text: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.cwd,
        )
        out, err = await asyncio.wait_for(
            proc.communicate(text.encode("utf-8")), timeout=self.timeout
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"handler exited {proc.returncode}: "
                f"{err.decode('utf-8', 'replace')[:500]}"
            )
        return out.decode("utf-8", "replace").strip()


def echo_handler(node_id: str, host: str | None = None) -> Handler:
    """Deterministic default handler: reports node identity and echoes the task.

    Used for verification so a caller can prove the task ran on the
    intended LAN node (the response carries that node's id and hostname).
    """

    node_host = host or local_hostname()

    def _handler(text: str) -> str:
        return (
            f"[{node_id}@{node_host}] received {len(text)} chars; "
            f"echo: {text[:200]}"
        )

    return _handler
