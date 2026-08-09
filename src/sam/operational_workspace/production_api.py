"""Production API - WP-27 (MISSION-4.6 / IP-4.6-003).

Antarmuka produksi terpadu. Read-only untuk dashboard/trust/history/metrics;
tidak memiliki authority eksekusi.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .production_platform import (
    DashboardRenderer,
    ExperienceBrowser,
    OperationalHistory,
    PlatformCertifier,
    PlatformMetricsCollector,
    TrustScore,
    TrustVisualizer,
)


class ProductionAPI:
    """Facade produksi (read-only)."""

    def __init__(
        self,
        *,
        history: OperationalHistory,
        experience_browser: Optional[ExperienceBrowser] = None,
    ) -> None:
        self._history = history
        self._experience_browser = experience_browser or ExperienceBrowser(history)

    # --- Dashboard ---
    def dashboard(self, **kwargs: Any) -> Dict[str, Any]:
        return DashboardRenderer.render(**kwargs).as_dict()

    # --- Trust ---
    def trust(self, component: str, evidence_count: int, validation_rate: float) -> Dict[str, Any]:
        return TrustVisualizer.compute(
            component, evidence_count=evidence_count, validation_rate=validation_rate
        ).as_dict()

    # --- History / Experience ---
    def history(self, kind: str = "") -> Tuple[Dict[str, Any], ...]:
        return self._experience_browser.browse(kind)

    def trace(self, record_id: str) -> Optional[Dict[str, Any]]:
        return self._experience_browser.trace(record_id)

    # --- Metrics ---
    def metrics(
        self,
        *,
        total_experiences: int = 0,
        knowledge_count: int = 0,
        trust_scores: Tuple[TrustScore, ...] = (),
    ) -> Dict[str, Any]:
        return PlatformMetricsCollector.collect(
            total_history=self._history.count(),
            total_experiences=total_experiences,
            knowledge_count=knowledge_count,
            trust_scores=trust_scores,
        ).as_dict()

    # --- Certification ---
    def certify(self, **kwargs: Any) -> Dict[str, Any]:
        return PlatformCertifier.certify(**kwargs).as_dict()
