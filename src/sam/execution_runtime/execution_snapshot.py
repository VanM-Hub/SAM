"""Execution Snapshot (Sprint 256).

Program C - Real Execution Runtime.
Snapshot immutable status runtime pada satu titik waktu.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from .execution_health import ExecutionHealth
from .execution_history import ExecutionHistory


@dataclass(frozen=True)
class ExecutionSnapshot:
    """Snapshot status runtime (immutable)."""
    snapshot_id: str
    health: ExecutionHealth
    total_recorded: int = 0
    external_calls_total: int = 0

    def as_dict(self) -> dict:
        return {"snapshot_id": self.snapshot_id,
                "health": self.health.as_dict(),
                "total_recorded": self.total_recorded,
                "external_calls_total": self.external_calls_total}
