"""Sprint 277 - Desktop Monitoring: metrics (immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class PresentationMetrics:
    """Metrik desktop read-only (deklaratif, tanpa IO realtime)."""

    panels_total: int = 0
    cards_total: int = 0
    metrics: Dict[str, float] = field(default_factory=dict)

    def with_metric(self, name: str, value: float) -> "PresentationMetrics":
        m = dict(self.metrics)
        m[name] = value
        return PresentationMetrics(
            panels_total=self.panels_total,
            cards_total=self.cards_total,
            metrics=m,
        )

    def as_dict(self) -> dict:
        return {
            "panels_total": self.panels_total,
            "cards_total": self.cards_total,
            "metrics": dict(self.metrics),
        }
