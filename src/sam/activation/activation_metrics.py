"""Activation Metrics — metrik aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActivationMetrics:
    metrics_id: str = ""
    total_packages: int = 0
    total_candidates: int = 0
    avg_confidence: float = 0.0
    avg_duration: float = 0.0
    strategy_counts: Dict[str, int] = field(default_factory=dict)


class ActivationMetricsCollector:
    """Mengumpulkan metrik aktivasi — read-only, pure function."""

    def collect(self, packages: List[Any]) -> ActivationMetrics:
        if not packages:
            return ActivationMetrics(metrics_id="metrics_empty")

        total_cands = sum(p.total_candidates for p in packages)
        avg_conf = sum(p.confidence for p in packages) / len(packages)
        avg_dur = sum(p.estimated_duration for p in packages) / len(packages) if packages else 0.0

        strat_counts: Dict[str, int] = {}
        for p in packages:
            ref = p.strategy_ref
            strat_counts[ref] = strat_counts.get(ref, 0) + 1

        return ActivationMetrics(
            metrics_id=f"metrics_{len(packages)}",
            total_packages=len(packages),
            total_candidates=total_cands,
            avg_confidence=round(avg_conf, 2),
            avg_duration=round(avg_dur, 2),
            strategy_counts=strat_counts,
        )
