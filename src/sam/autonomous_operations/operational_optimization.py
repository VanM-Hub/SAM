"""Operational Optimization - WP-16 (MISSION-4.5 / IP-4.5-002).

Optimisasi operasional berbasis evidence (read-only, rekomendasi saja -
tidak mengeksekusi perubahan).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class OptimizationSuggestion:
    """Satu saran optimisasi."""

    suggestion_id: str
    target_id: str
    suggestion: str
    expected_benefit: str = ""
    evidence_ids: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "suggestion_id": self.suggestion_id,
            "target_id": self.target_id,
            "suggestion": self.suggestion,
            "expected_benefit": self.expected_benefit,
            "evidence_ids": list(self.evidence_ids),
        }


class OperationalOptimizer:
    """Mesin optimisasi (rekomendasi, bukan eksekusi)."""

    @staticmethod
    def suggest(
        *,
        high_cpu_targets: Tuple[str, ...] = (),
        low_availability_providers: Tuple[str, ...] = (),
        evidence_ids: Tuple[Tuple[str, str], ...] = (),
    ) -> Tuple[OptimizationSuggestion, ...]:
        suggestions: List[OptimizationSuggestion] = []
        idx = 1
        for target in high_cpu_targets:
            suggestions.append(
                OptimizationSuggestion(
                    suggestion_id=f"opt-{idx}",
                    target_id=target,
                    suggestion=f"Consider load-balancing resource allocation for {target}",
                    expected_benefit="reduce latency & stabilize health",
                    evidence_ids=tuple(
                        eid for _t, eid in evidence_ids if _t == target
                    ),
                )
            )
            idx += 1
        for target in low_availability_providers:
            suggestions.append(
                OptimizationSuggestion(
                    suggestion_id=f"opt-{idx}",
                    target_id=target,
                    suggestion=f"Review availability & failover for provider {target}",
                    expected_benefit="improve service continuity",
                    evidence_ids=tuple(
                        eid for _t, eid in evidence_ids if _t == target
                    ),
                )
            )
            idx += 1
        return tuple(suggestions)
