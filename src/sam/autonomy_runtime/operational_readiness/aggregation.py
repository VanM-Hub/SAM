# Readiness Aggregation Engine - WP-42
# IP-3.2-005 (AO-3.2-001 / ED-3.2-005)
#
# Mengagregasi seluruh masukan (observasi, diagnosa, planning, recovery,
# coordination, lifecycle) menjadi satu penilaian kesiapan operasional.
# Prinsip: "Aggregation != Decision." Engine hanya menggabungkan, mengevaluasi,
# memberi skor, menjelaskan. TIDAK memilih tindakan.
# Deterministic: input identik -> output identik. Hashlib untuk stable id.

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.operational_readiness.models import (
    OperationalReadiness,
    ReadinessDimension,
    ReadinessInput,
)

# Peta dimensi -> sumber masukan yang berkontribusi.
_DIMENSION_SOURCES = {
    "observe": ("observation", "diagnostics"),
    "diagnose": ("diagnostics",),
    "plan": ("planning",),
    "recover": ("recovery",),
    "coordinate": ("coordination",),
    "lifecycle": ("lifecycle",),
    "readiness": ("readiness", "observation"),
}

# Sumber wajib agar penilaian dikategorikan lengkap.
_REQUIRED_SOURCES = (
    "observation", "diagnostics", "planning", "recovery",
    "coordination", "lifecycle", "readiness",
)


def _prepare(value: float) -> float:
    """Batas deterministik ke [0.0, 1.0]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return round(value, 4)


def _stable_id(seed: str) -> str:
    return "or-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class AggregationResult:
    """Hasil agregasi kemurnian (immutable)."""

    inputs: Tuple[ReadinessInput, ...]
    dimensions: Tuple[ReadinessDimension, ...]
    overall_score: float
    overall_level: str
    ready: bool
    blockers: Tuple[str, ...]
    missing_sources: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "inputs": [i.as_dict() for i in self.inputs],
            "dimensions": [d.as_dict() for d in self.dimensions],
            "overall_score": self.overall_score,
            "overall_level": self.overall_level,
            "ready": self.ready,
            "blockers": list(self.blockers),
            "missing_sources": list(self.missing_sources),
        }


class ReadinessAggregationEngine:
    """Mengagregasi masukan menjadi dimensi & skor kesiapan (deterministik)."""

    def aggregate(
        self,
        inputs: Tuple[ReadinessInput, ...],
        readiness_id: str = "",
        created_at: str = "",
    ) -> AggregationResult:
        inputs = tuple(inputs)
        dimensions: List[ReadinessDimension] = []
        blockers: List[str] = []

        for dim_name, sources in _DIMENSION_SOURCES.items():
            contributing = [i for i in inputs if i.source in sources]
            if not contributing:
                score = 0.0
                ready = False
                detail = "no input for {} dimension".format(dim_name)
                if dim_name in ("plan", "recover", "coordinate", "lifecycle"):
                    blockers.append("missing {} dimension".format(dim_name))
                dimensions.append(
                    ReadinessDimension(name=dim_name, score=score, ready=False,
                                       contributing_inputs=(), detail=detail)
                )
                continue
            # skor dimensi = rata-rata status masukan (deterministik)
            scores = []
            for i in contributing:
                if i.source in ("observation", "diagnostics", "readiness"):
                    scores.append(self._health_score(i.health))
                else:
                    scores.append(self._status_score(i.status))
            score = _prepare(sum(scores) / len(scores))
            ready = score >= 0.6
            if not ready:
                detail = "{} dimension below readiness".format(dim_name)
            else:
                detail = "{} dimension ready".format(dim_name)
            dimensions.append(
                ReadinessDimension(name=dim_name, score=score, ready=ready,
                                   contributing_inputs=tuple(i.artifact_id for i in contributing),
                                   detail=detail)
            )

        # blocker dari dimensi yang tidak siap
        for d in dimensions:
            if not d.ready:
                blockers.append("{} readiness below threshold".format(d.name))

        # overall score = rata-rata seluruh dimensi
        if dimensions:
            overall = _prepare(sum(d.score for d in dimensions) / len(dimensions))
        else:
            overall = 0.0

        overall_level = self._level_for(overall)
        ready = overall >= 0.6 and all(d.ready for d in dimensions)

        # sumber wajib yang hilang
        present = {i.source for i in inputs}
        missing = tuple(s for s in _REQUIRED_SOURCES if s not in present)

        return AggregationResult(
            inputs=inputs,
            dimensions=tuple(dimensions),
            overall_score=overall,
            overall_level=overall_level,
            ready=ready,
            blockers=tuple(dict.fromkeys(blockers)),
            missing_sources=missing,
        )

    def build_readiness(
        self,
        inputs: Tuple[ReadinessInput, ...],
        readiness_id: str = "",
        created_at: str = "",
        recommendations: Tuple[str, ...] = (),
        evidence_extra: Tuple[str, ...] = (),
    ) -> OperationalReadiness:
        """Bangun penilaian kesiapan lengkap dari agregasi."""
        agg = self.aggregate(inputs, readiness_id, created_at)
        readiness_id = readiness_id or _stable_id(
            "|".join(sorted(i.artifact_id for i in agg.inputs))
        )
        created_at = created_at or "t"
        all_evidence = tuple(
            dict.fromkeys(list(evidence_extra) + [e for i in agg.inputs for e in i.evidence])
        )
        trust = self._trust_score(agg)
        return OperationalReadiness(
            readiness_id=readiness_id,
            created_at=created_at,
            overall_level=agg.overall_level,
            overall_score=agg.overall_score,
            ready=agg.ready,
            inputs=agg.inputs,
            dimensions=agg.dimensions,
            blockers=agg.blockers,
            top_risks=tuple(recommendations),
            recommendation="operational readiness stated; no action selected",
            basis="integration of observe/diagnose/plan/recover/coordinate/lifecycle",
            evidence=all_evidence,
            trust_score=trust,
            is_proposal_only=True,
            metadata={
                "deterministic": True,
                "aggregation": "weighted_mean",
                "missing_sources": list(agg.missing_sources),
            },
        )

    # --- helpers ---

    @staticmethod
    def _health_score(health: str) -> float:
        return {
            "healthy": 1.0,
            "degraded": 0.5,
            "unhealthy": 0.0,
            "unknown": 0.3,
        }.get(health, 0.3)

    @staticmethod
    def _status_score(status: str) -> float:
        return {
            "ready": 1.0,
            "healthy": 1.0,
            "degraded": 0.5,
            "not_ready": 0.0,
            "risky": 0.4,
            "unknown": 0.3,
        }.get(status, 0.3)

    @staticmethod
    def _level_for(score: float) -> str:
        if score >= 0.8:
            return "ready"
        if score >= 0.6:
            return "degraded"
        if score > 0.0:
            return "not_ready"
        return "unknown"

    @staticmethod
    def _trust_score(agg: AggregationResult) -> float:
        """Tingkat kepercayaan = f(ketersediaan masukan & konsistensi dimensi).

        Deterministik: 0.5 * coverage + 0.5 * mean_score. Semakin banyak sumber
        wajib terisi & semakin siap dimensi, semakin tinggi kepercayaan.
        """
        present = {i.source for i in agg.inputs}
        coverage = sum(1 for s in _REQUIRED_SOURCES if s in present) / len(_REQUIRED_SOURCES)
        mean = agg.overall_score
        return _prepare(0.5 * coverage + 0.5 * mean)
