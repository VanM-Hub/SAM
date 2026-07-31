"""Sprint 266 - Monitoring: monitor (agregasi monitoring seluruh runtime)."""
from __future__ import annotations

from dataclasses import dataclass

from .health import RuntimeHealth
from .metrics import RuntimeMetrics
from .snapshot import RuntimeSnapshot


@dataclass(frozen=True)
class RuntimeMonitor:
    """Monitor aplikasi: mengambil snapshot deterministik tanpa IO/thread."""

    def snapshot(self, healthy: bool = True, message: str = "ok") -> RuntimeSnapshot:
        return RuntimeSnapshot(
            health=RuntimeHealth(healthy=healthy, message=message),
            metrics=RuntimeMetrics(),
            meta={"mode": "preview"},
        )

    def snapshot_with(
        self,
        metrics: RuntimeMetrics,
        healthy: bool = True,
        message: str = "ok",
    ) -> RuntimeSnapshot:
        return RuntimeSnapshot(
            health=RuntimeHealth(healthy=healthy, message=message),
            metrics=metrics,
            meta={"mode": "preview"},
        )
