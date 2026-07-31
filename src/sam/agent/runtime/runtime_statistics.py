"""Runtime Statistics — statistik runtime (Sprint 162).

Agent Runtime — statistik read-only, deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from .agent_runtime import AgentRuntime
from ..state.state_machine import COMPLETED


@dataclass(frozen=True)
class RuntimeStatistics:
    """Statistik runtime (immutable)."""
    total_missions: int = 0
    completed: int = 0
    state_counts: Dict[str, int] = field(default_factory=dict)
    external_calls: int = 0

    @property
    def completion_rate(self) -> float:
        if self.total_missions == 0:
            return 0.0
        return self.completed / self.total_missions


class RuntimeStatisticsCollector:
    """Collector statistik. Read-only."""

    def __init__(self, runtime: AgentRuntime) -> None:
        self._runtime = runtime

    def collect(self) -> RuntimeStatistics:
        machine = self._runtime.machine
        ids = getattr(machine, "_states", {})
        counts: Dict[str, int] = {}
        for st in ids.values():
            counts[st.state] = counts.get(st.state, 0) + 1
        return RuntimeStatistics(
            total_missions=len(ids),
            completed=counts.get(COMPLETED, 0),
            state_counts=counts,
            external_calls=0,
        )


__all__ = ["RuntimeStatistics", "RuntimeStatisticsCollector"]
