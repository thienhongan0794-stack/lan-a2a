"""Round-trip test: start a real A2A server, fetch its card, delegate a task.

Runs with the standard library only:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
import unittest

import uvicorn

from lan_a2a.client import fetch_card, send_text
from lan_a2a.executor import NodeAgentExecutor, echo_handler
from lan_a2a.server import build_agent_card, build_app


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class A2AServerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.port = free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.card = build_agent_card("test-node", self.base_url)
        self.executor = NodeAgentExecutor(
            "test-node", echo_handler("test-node", "test-host"), host="test-host"
        )
        app = build_app(self.card, self.executor).build()
        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="error")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        for _ in range(200):
            if self.server.started:
                break
            time.sleep(0.05)
        self.assertTrue(self.server.started, "server did not start")

    def tearDown(self) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=5)

    def test_fetch_card(self) -> None:
        card = asyncio.run(fetch_card(self.base_url))
        self.assertEqual(card.name, "LAN Agent test-node")
        self.assertEqual(card.url, self.base_url)
        self.assertIn("echo", [s.id for s in card.skills])
        self.assertTrue(card.capabilities.streaming)

    def test_delegate_task(self) -> None:
        result = asyncio.run(send_text(self.base_url, "hello from agent-c"))
        payload = json.loads(result)
        self.assertEqual(payload["node"], "test-node")
        self.assertEqual(payload["host"], "test-host")
        self.assertEqual(payload["received"], "hello from agent-c")
        self.assertIn("hello from agent-c", payload["result"])

    def test_handler_failure_marks_task_failed(self) -> None:
        def boom(_text: str) -> str:
            raise ValueError("kaboom")

        executor = NodeAgentExecutor("test-node", boom)
        app = build_app(self.card, executor).build()
        port = free_port()
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        try:
            for _ in range(200):
                if server.started:
                    break
                time.sleep(0.05)
            with self.assertRaises(RuntimeError) as ctx:
                asyncio.run(send_text(f"http://127.0.0.1:{port}", "x"))
            self.assertIn("kaboom", str(ctx.exception))
        finally:
            server.should_exit = True
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
