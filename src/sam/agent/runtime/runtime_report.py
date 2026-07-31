"""Runtime Report — laporan runtime (Sprint 162).

Agent Runtime — laporan read-only tentang state Agent Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .agent_runtime import AgentRuntime


@dataclass(frozen=True)
class RuntimeReport:
    """Laporan runtime (immutable)."""
    version: str = "1.0.0"
    total_missions: int = 0
    states: Dict[str, int] = field(default_factory=dict)
    ready: bool = False
    external_calls: int = 0


class RuntimeReporter:
    """Reporter runtime. Read-only."""

    def __init__(self, runtime: AgentRuntime) -> None:
        self._runtime = runtime

    def report(self) -> RuntimeReport:
        machine = self._runtime.machine
        ids = getattr(machine, "_states", {})
        counts: Dict[str, int] = {}
        for st in ids.values():
            counts[st.state] = counts.get(st.state, 0) + 1
        return RuntimeReport(
            version=AgentRuntime.RUNTIME_VERSION,
            total_missions=len(ids),
            states=counts,
            ready=True,
            external_calls=0,
        )


__all__ = ["RuntimeReporter", "RuntimeReport"]
