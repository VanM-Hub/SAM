"""RuntimeStatistics (Sprint 269).

Program D - Runtime Services & Deployment.
Statistik agregat dari metrics (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class RuntimeStatistics:
    """Statistik runtime (immutable)."""
    service_counts: Dict[str, int] = field(default_factory=dict)
    total_events: int = 0

    def as_dict(self) -> dict:
        return {
            "service_counts": dict(self.service_counts),
            "total_events": self.total_events,
        }


def compute_statistics(metrics_by_service: Dict[str, Any]) -> RuntimeStatistics:
    """Hitung statistik dari kumpulan metrics."""
    counts = {name: m.get("events", 0) for name, m in metrics_by_service.items()}
    total = sum(counts.values())
    return RuntimeStatistics(service_counts=counts, total_events=total)
