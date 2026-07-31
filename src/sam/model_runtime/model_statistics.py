"""Model Statistics — statistik model (Sprint 246).

Program B — Model Runtime Integration.
Statistik deterministik, read-only, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .model_monitor import ModelMonitor


@dataclass(frozen=True)
class ModelStatistics:
    """Statistik model (immutable)."""
    total_reports: int = 0
    ok: int = 0
    failed: int = 0
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "total_reports": self.total_reports,
            "ok": self.ok,
            "failed": self.failed,
            "external_calls": self.external_calls,
        }


class ModelStatisticsCollector:
    """Mengumpulkan statistik dari monitor. Read-only."""

    def collect(self, monitor: ModelMonitor) -> ModelStatistics:
        metrics = {m.name: m.value for m in monitor.metrics()}
        return ModelStatistics(
            total_reports=int(metrics.get("reports", 0)),
            ok=int(metrics.get("ok", 0)),
            failed=int(metrics.get("failed", 0)),
            external_calls=0,
        )
