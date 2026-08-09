"""Failure Correlation - WP-12 (MISSION-4.2 / IP-4.2-002).

Mengkorelasikan failure yang saling terkait dari evidence operasional.
Read-only, deterministik.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .evidence_collection import EvidenceModel


@dataclass(frozen=True)
class CorrelatedFailure:
    """Satu kelompok failure yang terkorelasi."""

    correlation_id: str
    failure_ids: Tuple[str, ...] = field(default_factory=tuple)
    common_source: str = ""
    evidence_count: int = 0

    def as_dict(self) -> dict:
        return {
            "correlation_id": self.correlation_id,
            "failure_ids": list(self.failure_ids),
            "common_source": self.common_source,
            "evidence_count": self.evidence_count,
        }


@dataclass(frozen=True)
class FailureCorrelationResult:
    """Hasil korelasi failure."""

    investigation_id: str
    correlations: Tuple[CorrelatedFailure, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "correlations": [c.as_dict() for c in self.correlations],
            "correlation_count": len(self.correlations),
        }


class FailureCorrelator:
    """Mengkorelasikan failure berdasarkan sumber & kategori umum."""

    def correlate(
        self,
        investigation_id: str,
        failures: Tuple[EvidenceModel, ...],
    ) -> FailureCorrelationResult:
        # Kelompokkan failure berdasarkan (source_id, category) umum
        groups: Dict[str, List[EvidenceModel]] = {}
        for ev in failures:
            key = f"{ev.source.source_id}::{ev.category}"
            groups.setdefault(key, []).append(ev)

        correlations = []
        for idx, (key, evs) in enumerate(
            sorted(groups.items(), key=lambda kv: -len(kv[1])), start=1
        ):
            if len(evs) < 2:
                continue  # korelasi butuh minimal 2 evidence
            source = evs[0].source.source_id
            correlations.append(
                CorrelatedFailure(
                    correlation_id=f"corr-{idx}",
                    failure_ids=tuple(e.evidence_id for e in evs),
                    common_source=source,
                    evidence_count=len(evs),
                )
            )
        return FailureCorrelationResult(
            investigation_id=investigation_id,
            correlations=tuple(correlations),
        )
