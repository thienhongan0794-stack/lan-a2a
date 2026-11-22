"""A2A v1.0 dialect test: a Hermes-style SendMessage must reach a v0.3 executor."""

from __future__ import annotations

import json
import socket
import threading
import time
import unittest
import urllib.request

import uvicorn

from lan_a2a.executor import NodeAgentExecutor, echo_handler
from lan_a2a.server import build_agent_card, build_asgi


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class DialectTestCase(unittest.TestCase):
    def test_v1_send_message_reaches_v03_executor(self) -> None:
        port = free_port()
        base = f"http://127.0.0.1:{port}"
        card = build_agent_card("agent-x", base)
        executor = NodeAgentExecutor("agent-x", echo_handler("agent-x", "host-x"))
        app = build_asgi(card, executor)
        server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
        )
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        try:
            for _ in range(200):
                if server.started:
                    break
                time.sleep(0.05)
            body = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "SendMessage",
                "params": {
                    "message": {
                        "role": "ROLE_USER",
                        "parts": [{"text": "hello from hermes v1"}],
                        "messageId": "m1",
                    }
                },
            }
            request = urllib.request.Request(
                base + "/",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertNotIn("error", payload, payload)
            self.assertIn("hello from hermes v1", json.dumps(payload["result"]))
        finally:
            server.should_exit = True
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
