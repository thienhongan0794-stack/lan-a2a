"""A2A dialect normalization middleware.

Hermes speaks A2A **v1.0** JSON-RPC (``SendMessage``, roles ``ROLE_USER`` /
``ROLE_AGENT``); the crewAI / a2a-sdk server speaks **v0.3** (``message/send``,
roles ``user`` / ``agent``). This pure-ASGI middleware rewrites an incoming
v1.0 request into the v0.3 dialect before it reaches the a2a-sdk handler, so a
Hermes agent can call a `lan-a2a` node directly (no separate bridge process).
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

Receive = Callable[[], Awaitable[dict]]
Send = Callable[[dict], Awaitable[None]]

_METHOD_MAP = {
    "SendMessage": "message/send",
    "sendMessage": "message/send",
    "MessageStream": "message/stream",
    "message/stream": "message/stream",
    "message/send": "message/send",
}


def _normalize_role(role: object) -> object:
    if isinstance(role, str) and role.startswith("ROLE_"):
        return role.split("_", 1)[1].lower()
    return role


def _rewrite_body(data: dict) -> dict:
    method = data.get("method")
    if isinstance(method, str) and method in _METHOD_MAP:
        data["method"] = _METHOD_MAP[method]
    params = data.get("params")
    if isinstance(params, dict):
        message = params.get("message")
        if isinstance(message, dict):
            message["role"] = _normalize_role(message.get("role"))
    return data


async def _read_body(receive: Receive) -> bytes:
    chunks: list[bytes] = []
    more = True
    while more:
        message = await receive()
        if message.get("type") == "http.disconnect":
            break
        chunks.append(message.get("body", b""))
        more = bool(message.get("more_body", False))
    return b"".join(chunks)


class DialectNormalization:
    """Pure ASGI middleware: rewrite v1.0 JSON-RPC to v0.3 for the a2a-sdk app."""

    def __init__(self, app: Callable) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Receive, send: Send) -> None:
        if (
            scope.get("type") != "http"
            or (scope.get("method") or "").upper() != "POST"
            or (scope.get("path") or "/") not in ("", "/")
        ):
            await self.app(scope, receive, send)
            return

        body = await _read_body(receive)
        try:
            data = json.loads(body)
        except (ValueError, TypeError):
            await self._forward(scope, body, send)
            return

        if not (isinstance(data, dict) and data.get("method") in _METHOD_MAP):
            await self._forward(scope, body, send)
            return

        await self._forward(
            scope, json.dumps(_rewrite_body(data)).encode("utf-8"), send
        )

    async def _forward(self, scope: dict, payload: bytes, send: Send) -> None:
        headers = [
            (b"content-length", str(len(payload)).encode("ascii"))
            if name.lower() == b"content-length"
            else (name, value)
            for name, value in scope.get("headers", [])
        ]
        new_scope = dict(scope)
        new_scope["headers"] = headers
        sent = False

        async def new_receive() -> dict:
            nonlocal sent
            if sent:
                return {"type": "http.disconnect"}
            sent = True
            return {"type": "http.request", "body": payload, "more_body": False}

        await self.app(new_scope, new_receive, send)
