"""Dashboard Runtime Bridge — 5 ExecutionCards (Sprint 162).

Agent Runtime — dashboard bridge read-only.
"""
from __future__ import annotations

from .agent_runtime import AgentRuntime
from ..dashboard.agent_dashboard import ExecutionCard


class DashboardRuntimeBridge:
    """Bridge dashboard — 5 kartu untuk Agent Runtime."""

    def __init__(self, runtime: AgentRuntime) -> None:
        self._runtime = runtime

    def cards(self):
        return [
            ExecutionCard("agent.runtime", "runtime", "ready",
                          "agent runtime engine", "preview-only", "ready"),
            ExecutionCard("agent.pipeline", "runtime", "ready",
                          "Mission->State->Planner->Coordinator->Monitor->Summary",
                          "pipeline", "ready"),
            ExecutionCard("agent.lifecycle", "runtime", "ready",
                          "Created..Completed lifecycle", "state machine", "ready"),
            ExecutionCard("agent.no_exec", "runtime", "ready",
                          "no runtime call, no execution", "preview", "ready"),
            ExecutionCard("agent.deterministic", "runtime", "ready",
                          "synchronous & deterministic", "engine", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
