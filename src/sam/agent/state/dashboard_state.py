"""Dashboard State Bridge — 5 ExecutionCards (Sprint 158).

Agent Runtime — dashboard bridge read-only.
"""
from __future__ import annotations

from .state_machine import StateMachine
from ..dashboard.agent_dashboard import ExecutionCard


class DashboardStateBridge:
    """Bridge dashboard — 5 kartu untuk state machine."""

    def __init__(self, machine: StateMachine) -> None:
        self._machine = machine

    def cards(self):
        states = ["Created", "Preparing", "Running", "Waiting", "Completed",
                  "Cancelled", "Failed"]
        return [
            ExecutionCard("state.machine", "state", "ready",
                          "lifecycle state machine", "7 states", "ready"),
            ExecutionCard("state.no_retry", "state", "ready",
                          "no auto retry", "deterministic", "ready"),
            ExecutionCard("state.terminal", "state", "ready",
                          "Completed/Cancelled/Failed", "terminal states", "ready"),
            ExecutionCard("state.valid", "state", "ready",
                          f"{len(states)} valid states", "state validator", "ready"),
            ExecutionCard("state.deterministic", "state", "ready",
                          "synchronous & deterministic", "state machine", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
