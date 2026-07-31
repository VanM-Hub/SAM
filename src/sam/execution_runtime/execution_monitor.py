"""Execution Monitor (Sprint 256).

Program C - Real Execution Runtime.
Monitor yang mengagregasi health + history + metrics. Read-only, no network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .execution_health import ExecutionHealth
from .execution_history import ExecutionHistory, ExecutionHistoryEntry
from .execution_snapshot import ExecutionSnapshot
from .execution_metrics import ExecutionMetrics


class ExecutionMonitor:
    """Monitor eksekusi. Aggregasi health/history/metrics."""

    def __init__(self, health: ExecutionHealth | None = None,
                 history: ExecutionHistory | None = None) -> None:
        self._health = health or ExecutionHealth(health_id="h-main", provider_available=True)
        self._history = history or ExecutionHistory()
        self._metrics: List[ExecutionMetrics] = []

    @property
    def history(self) -> ExecutionHistory:
        return self._history

    def record_report(self, report) -> ExecutionHistoryEntry:
        return self._history.record(report)

    def add_metrics(self, metrics: ExecutionMetrics) -> None:
        self._metrics.append(metrics)

    def snapshot(self, snapshot_id: str) -> ExecutionSnapshot:
        return ExecutionSnapshot(
            snapshot_id=snapshot_id,
            health=self._health,
            total_recorded=self._history.count(),
            external_calls_total=sum(m.external_calls for m in self._metrics),
        )

    def health(self) -> ExecutionHealth:
        return self._health
