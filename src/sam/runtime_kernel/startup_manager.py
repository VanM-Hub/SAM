"""Startup Manager — startup runtime."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.runtime_lifecycle import LifecyclePhase


class StartupManager:
    """Manager startup — preview-only."""

    STARTUP_PHASES = ["context", "registry", "state", "coordinator", "health", "engine"]

    def build_plan(self) -> List[LifecyclePhase]:
        return [
            LifecyclePhase(f"p{i+1}", name, "pending", i + 1)
            for i, name in enumerate(self.STARTUP_PHASES)
        ]

    def count_phases(self) -> int:
        return len(self.STARTUP_PHASES)

    def get_phase_names(self) -> List[str]:
        return list(self.STARTUP_PHASES)
