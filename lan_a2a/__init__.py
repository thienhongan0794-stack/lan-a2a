"""lan-a2a: A2A (Agent-to-Agent) gateway for agents on the internal LAN.

Each LAN node runs a small A2A-compliant HTTP server that exposes an
AgentCard and executes tasks by invoking a local handler. Any A2A client
on the LAN (a CrewAI agent, a Hermes agent, or the `lan-a2a` CLI) can
discover the nodes from `registry.json` and delegate tasks to them.
"""

__version__ = "0.1.0"
