# Cross-Runtime Readiness Report - WP-48
# IP-3.2-005 (AO-3.2-001 / ED-3.2-005)
#
# Menyatukan penilaian kesiapan operasional dari BEBERAPA runtime menjadi satu
# laporan keseluruhan sistem. Konsolidasi lintas-runtime agar satu pandangan
# operasional terpadu terhadap seluruh runtime kolektif.
# Prinsip: read-only, aggregative, evidence-backed, proposal-only.
# TIDAK memilih tindakan lintas-runtime, TIDAK orchestration, TIDAK mutate.
# Deterministic.

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.operational_readiness.models import OperationalReadiness


@dataclass(frozen=True)
class CrossRuntimeEntry:
    """Entri kesiapan satu runtime dalam laporan lintas-runtime (immutable)."""

    runtime_id: str
    readiness_id: str
    overall_level: str
    overall_score: float
    ready: bool
    top_risks: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "readiness_id": self.readiness_id,
            "overall_level": self.overall_level,
            "overall_score": self.overall_score,
            "ready": self.ready,
            "top_risks": list(self.top_risks),
        }


@dataclass(frozen=True)
class CrossRuntimeReadinessReport:
    """Laporan kesiapan operasional seluruh runtime (immutable, read-only)."""

    report_id: str
    created_at: str
    entries: Tuple[CrossRuntimeEntry, ...] = ()
    system_level: str = "unknown"  # ready | degraded | not_ready | unknown
    system_score: float = 0.0
    system_ready: bool = False
    ready_count: int = 0
    total_count: int = 0
    cross_runtime_risks: Tuple[str, ...] = ()
    is_proposal_only: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "created_at": self.created_at,
            "entries": [e.as_dict() for e in self.entries],
            "system_level": self.system_level,
            "system_score": self.system_score,
            "system_ready": self.system_ready,
            "ready_count": self.ready_count,
            "total_count": self.total_count,
            "cross_runtime_risks": list(self.cross_runtime_risks),
            "is_proposal_only": self.is_proposal_only,
            "metadata": dict(self.metadata),
        }

    def entry_count(self) -> int:
        return len(self.entries)

    def system_ready_ratio(self) -> float:
        if self.total_count == 0:
            return 0.0
        return round(self.ready_count / self.total_count, 4)


class CrossRuntimeReadinessAssembler:
    """Mengonsolidasikan penilaian kesiapan lintas-runtime (deterministik)."""

    def assemble(
        self,
        runtime_assessments: Tuple[Tuple[str, OperationalReadiness], ...],
        report_id: str = "",
        created_at: str = "",
    ) -> CrossRuntimeReadinessReport:
        runtime_assessments = tuple(runtime_assessments)
        entries: List[CrossRuntimeEntry] = []
        all_risks: List[str] = []

        for runtime_id, readiness in runtime_assessments:
            entries.append(CrossRuntimeEntry(
                runtime_id=runtime_id,
                readiness_id=readiness.readiness_id,
                overall_level=readiness.overall_level,
                overall_score=readiness.overall_score,
                ready=readiness.ready,
                top_risks=readiness.top_risks,
            ))
            all_risks.extend(readiness.top_risks)

        # urutkan deterministik by runtime_id
        entries.sort(key=lambda e: e.runtime_id)

        total = len(entries)
        ready_count = sum(1 for e in entries if e.ready)
        if total:
            system_score = round(sum(e.overall_score for e in entries) / total, 4)
            system_ready = all(e.ready for e in entries)
            system_level = self._level_for(system_score, ready_count, total)
        else:
            system_score = 0.0
            system_ready = False
            system_level = "unknown"

        # risiko lintas-runtime = risiko paling umum muncul
        cross_risks = self._top_cross_risks(all_risks)

        return CrossRuntimeReadinessReport(
            report_id=report_id or self._stable_id(
                "|".join(sorted(r[0] for r in runtime_assessments))),
            created_at=created_at or "t",
            entries=tuple(entries),
            system_level=system_level,
            system_score=system_score,
            system_ready=system_ready,
            ready_count=ready_count,
            total_count=total,
            cross_runtime_risks=cross_risks,
            is_proposal_only=True,
            metadata={
                "deterministic": True,
                "assembly": "cross_runtime_mean",
            },
        )

    @staticmethod
    def _level_for(score: float, ready_count: int, total: int) -> str:
        if ready_count == total and score >= 0.6:
            return "ready"
        if ready_count == 0:
            return "not_ready"
        if score >= 0.6:
            return "degraded"
        return "not_ready"

    @staticmethod
    def _top_cross_risks(risks: List[str]) -> Tuple[str, ...]:
        if not risks:
            return ()
        freq: Dict[str, int] = {}
        for r in risks:
            freq[r] = freq.get(r, 0) + 1
        ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
        return tuple(r for r, _ in ranked[:3])

    @staticmethod
    def _stable_id(seed: str) -> str:
        return "xr-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
