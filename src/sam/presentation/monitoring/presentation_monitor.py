"""Sprint 277 - Desktop Monitoring: monitor (service, tanpa IO)."""
from __future__ import annotations

from typing import Tuple

from ..composition.presentation_pipeline import PresentationPipeline
from .presentation_health import PresentationHealth
from .presentation_report import PresentationReport
from .presentation_snapshot import PresentationSnapshot


class PresentationMonitor:
    """Monitor desktop: agregasi health + snapshot deklaratif (tanpa IO)."""

    @staticmethod
    def check(pipeline: PresentationPipeline) -> PresentationHealth:
        # pipe snake sequence deterministik; sehat jika semua stage ada
        stages_ok = all(s for s in pipeline.stages) and len(pipeline.stages) >= 8
        return PresentationHealth(
            status="healthy" if stages_ok else "degraded",
            checks=pipeline.stages,
        )

    @staticmethod
    def snapshot(panels: Tuple[str, ...]) -> PresentationSnapshot:
        return PresentationSnapshot(
            panels=panels,
            status="ready",
        )

    @staticmethod
    def report(health: PresentationHealth) -> PresentationReport:
        return PresentationReport(
            observations=health.checks,
            counters={"healthy": 1 if health.is_healthy() else 0},
            status=health.status,
        )
