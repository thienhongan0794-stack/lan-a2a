"""Command line interface for the LAN A2A gateway."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from lan_a2a.client import fetch_card, send_text
from lan_a2a.executor import NodeAgentExecutor, ShellHandler, echo_handler
from lan_a2a.registry import get_node, load_registry
from lan_a2a.server import build_agent_card, serve


def _cmd_serve(args: argparse.Namespace) -> int:
    node = get_node(args.node)
    port = args.port or node.port
    if args.handler == "shell":
        if not args.command:
            raise SystemExit("--handler shell requires --command")
        handler = ShellHandler(args.command.split(), timeout=args.timeout)
    else:
        handler = echo_handler(node.id, node.host)

    executor = NodeAgentExecutor(node.id, handler, host=node.host)
    url = f"http://{node.host}:{port}"
    card = build_agent_card(
        node.id, url, description=args.description, streaming=not args.no_streaming
    )
    print(f"[lan-a2a] serving {node.id} on {url} (card: {card.url})")
    serve(card, executor, host=args.bind, port=port, log_level=args.log_level)
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    for node in load_registry():
        skills = ",".join(node.skills) or "-"
        print(f"{node.id:<10} {node.base_url:<28} role={node.role:<8} skills={skills}")
    return 0


def _cmd_card(args: argparse.Namespace) -> int:
    node = get_node(args.node)
    card = asyncio.run(fetch_card(node.base_url, timeout=args.timeout))
    print(card.model_dump_json(indent=2, by_alias=True))
    return 0


def _cmd_call(args: argparse.Namespace) -> int:
    node = get_node(args.node)
    text = args.text if args.text is not None else sys.stdin.read()
    result = asyncio.run(send_text(node.base_url, text, timeout=args.timeout))
    if args.json:
        try:
            print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))
            return 0
        except json.JSONDecodeError:
            pass
    print(result)
    return 0


def _cmd_discover(args: argparse.Namespace) -> int:
    async def run() -> None:
        for node in load_registry():
            try:
                card = await fetch_card(node.base_url, timeout=args.timeout)
                skills = ",".join(s.id for s in card.skills)
                print(f"{node.id}: OK {card.name} | {card.url} | skills={skills}")
            except Exception as exc:  # noqa: BLE001 - report per-node status
                print(f"{node.id}: UNREACHABLE ({type(exc).__name__}: {exc})")

    asyncio.run(run())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lan-a2a",
        description="A2A (Agent-to-Agent) gateway for internal LAN agents.",
    )
    parser.add_argument(
        "--registry",
        default=None,
        help="path to registry.json (default: alongside the package)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_serve = sub.add_parser("serve", help="run an A2A server for a node")
    p_serve.add_argument("--node", required=True)
    p_serve.add_argument("--bind", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=None)
    p_serve.add_argument("--handler", choices=["echo", "shell"], default="echo")
    p_serve.add_argument("--command", default=None, help="shell command for --handler shell")
    p_serve.add_argument("--timeout", type=float, default=120.0)
    p_serve.add_argument("--description", default=None)
    p_serve.add_argument("--no-streaming", action="store_true")
    p_serve.add_argument("--log-level", default="info")
    p_serve.set_defaults(func=_cmd_serve)

    p_list = sub.add_parser("list", help="list nodes in the registry")
    p_list.set_defaults(func=_cmd_list)

    p_card = sub.add_parser("card", help="fetch and print a node's AgentCard")
    p_card.add_argument("--node", required=True)
    p_card.add_argument("--timeout", type=float, default=10.0)
    p_card.set_defaults(func=_cmd_card)

    p_call = sub.add_parser("call", help="send a task to a node and print the result")
    p_call.add_argument("--node", required=True)
    p_call.add_argument("--text", default=None, help="task text (default: stdin)")
    p_call.add_argument("--timeout", type=float, default=120.0)
    p_call.add_argument("--json", action="store_true", help="pretty-print JSON results")
    p_call.set_defaults(func=_cmd_call)

    p_discover = sub.add_parser("discover", help="fetch AgentCards from all nodes")
    p_discover.add_argument("--timeout", type=float, default=10.0)
    p_discover.set_defaults(func=_cmd_discover)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "registry", None):
        import lan_a2a.registry as registry_module

        registry_module.DEFAULT_REGISTRY = args.registry
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
