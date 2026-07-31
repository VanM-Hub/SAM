"""Mission Route — rute mission (Sprint 159).

Agent Runtime — rute adalah urutan runtime pipeline yang dilalui mission.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

# Urutan runtime pipeline SAM (standar blueprint Phase XV)
PIPELINE_ROUTE = [
    "mission",
    "agent",
    "guardian",
    "decision",
    "approval",
    "operational_brain",
    "activation",
    "execution",
    "runtime_kernel",
    "connector",
    "provider",
]


@dataclass(frozen=True)
class MissionRoute:
    """Rute mission (immutable)."""
    mission_id: str
    runtimes: List[str] = field(default_factory=lambda: list(PIPELINE_ROUTE))

    @property
    def runtime_count(self) -> int:
        return len(self.runtimes)

    def contains(self, runtime_name: str) -> bool:
        return runtime_name in self.runtimes
