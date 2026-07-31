"""Dashboard Runtime — bridge dashboard <-> model runtime (Sprint 246).

Program B — Model Runtime Integration.
Read-only bridge; pipeline preview, no-network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .model_monitor import ModelMonitor, ModelHealth
from .model_statistics import ModelStatisticsCollector, ModelStatistics


@dataclass(frozen=True)
class DashboardRuntimeRow:
    """Satu baris runtime pada dashboard (immutable)."""
    row_id: str
    name: str
    value: str = ""
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "row_id": self.row_id,
            "name": self.name,
            "value": self.value,
            "external_calls": self.external_calls,
        }


class DashboardRuntime:
    """Bridge dashboard <-> model runtime. Read-only, no-network."""

    def __init__(
        self,
        monitor: ModelMonitor | None = None,
        collector: ModelStatisticsCollector | None = None,
    ) -> None:
        self._monitor = monitor or ModelMonitor()
        self._collector = collector or ModelStatisticsCollector()

    def health(self) -> ModelHealth:
        return self._monitor.health()

    def statistics(self) -> ModelStatistics:
        return self._collector.collect(self._monitor)

    def rows(self) -> List[DashboardRuntimeRow]:
        stats = self.statistics()
        return [
            DashboardRuntimeRow("drun-total", "Total Reports", str(stats.total_reports)),
            DashboardRuntimeRow("drun-ok", "OK", str(stats.ok)),
            DashboardRuntimeRow("drun-failed", "Failed", str(stats.failed)),
        ]

    def summary(self) -> Dict[str, object]:
        stats = self.statistics()
        return {
            "health": self._monitor.health().as_dict(),
            "total": stats.total_reports,
            "ok": stats.ok,
            "failed": stats.failed,
            "external_calls": stats.external_calls,
        }
