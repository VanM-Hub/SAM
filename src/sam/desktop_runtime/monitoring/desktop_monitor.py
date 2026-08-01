"""Sprint 277 - Desktop Monitoring: monitor (service, tanpa IO)."""
from __future__ import annotations

from typing import Tuple

from ..runtime.desktop_pipeline import DesktopPipeline
from .desktop_health import DesktopHealth
from .desktop_report import DesktopReport
from .desktop_snapshot import DesktopSnapshot


class DesktopMonitor:
    """Monitor desktop: agregasi health + snapshot deklaratif (tanpa IO)."""

    @staticmethod
    def check(pipeline: DesktopPipeline) -> DesktopHealth:
        # pipe snake sequence deterministik; sehat jika semua stage ada
        stages_ok = all(s for s in pipeline.stages) and len(pipeline.stages) >= 8
        return DesktopHealth(
            status="healthy" if stages_ok else "degraded",
            checks=pipeline.stages,
        )

    @staticmethod
    def snapshot(panels: Tuple[str, ...]) -> DesktopSnapshot:
        return DesktopSnapshot(
            panels=panels,
            status="ready",
        )

    @staticmethod
    def report(health: DesktopHealth) -> DesktopReport:
        return DesktopReport(
            observations=health.checks,
            counters={"healthy": 1 if health.is_healthy() else 0},
            status=health.status,
        )
