"""Dashboard Foundation Bridge — 5 ExecutionCards (Sprint 156).

Agent Runtime — dashboard bridge read-only.
"""
from __future__ import annotations

from .agent_registry import AgentRegistry
from ..dashboard.agent_dashboard import ExecutionCard


class DashboardFoundationBridge:
    """Bridge dashboard — 5 kartu untuk foundation."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def cards(self):
        n = self._registry.count()
        return [
            ExecutionCard("agent.foundation", "foundation", "ready",
                          f"{n} agent(s) registered", "agent registry", "ready"),
            ExecutionCard("agent.capability", "foundation", "ready",
                          "capabilities attached", "registry query", "ready"),
            ExecutionCard("agent.contract", "foundation", "ready",
                          "contracts attached", "registry query", "ready"),
            ExecutionCard("agent.metadata", "foundation", "ready",
                          "metadata attached", "registry query", "ready"),
            ExecutionCard("agent.layer", "foundation", "ready",
                          "agent runtime layer", "orchestrator", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
