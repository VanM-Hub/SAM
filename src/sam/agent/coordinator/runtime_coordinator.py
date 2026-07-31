"""Runtime Coordinator — menentukan runtime berikutnya (Sprint 160).

Agent Runtime — coordinator hanya menentukan runtime berikutnya dari antrian.
Tidak memanggil runtime, tidak mengeksekusi, tidak approval.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from .runtime_queue import RuntimeQueue
from .runtime_registry import RuntimeRegistry


@dataclass(frozen=True)
class CoordinatorDecision:
    """Keputusan coordinator (immutable)."""
    mission_id: str
    next_runtime: Optional[str] = None
    matched: bool = False
    reason: str = ""


class RuntimeCoordinator:
    """Coordinator runtime. Deterministik, preview-only."""

    def __init__(self, registry: RuntimeRegistry, queue: RuntimeQueue = None) -> None:
        self._registry = registry
        self._queue = queue if queue is not None else RuntimeQueue()

    def determine_next(self, mission_id: str) -> CoordinatorDecision:
        """Tentukan runtime berikutnya berdasarkan antrian & registry."""
        next_entry = self._queue.next_pending()
        if next_entry is None:
            return CoordinatorDecision(
                mission_id=mission_id, matched=False, reason="queue empty"
            )
        if not self._registry.has(next_entry.runtime_name):
            return CoordinatorDecision(
                mission_id=mission_id,
                next_runtime=next_entry.runtime_name,
                matched=False,
                reason="runtime not registered",
            )
        return CoordinatorDecision(
            mission_id=mission_id,
            next_runtime=next_entry.runtime_name,
            matched=True,
            reason="next pending runtime",
        )
