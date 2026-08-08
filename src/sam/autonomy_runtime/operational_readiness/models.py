# Operational Readiness Model - WP-41
# IP-3.2-005 (AO-3.2-001 / ED-3.2-005)
#
# Model penilaian kesiapan operasional - integrasi seluruh proposal
# (IP-3.2-001..004) menjadi satu pandangan operasional terpadu.
# Prinsip IP-3.2-005: "Runtime tidak menjadi lebih berkuasa, hanya lebih mampu
# memahami kesiapan operasional." Seluruh output = penilaian (read-only).
# Integration layer, BUKAN execution layer. Per ADR-023: frozen dataclasses.

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class ReadinessInput:
    """Satu masukan penilaian - referensi ke proposal/penilaian hulu.

    Mencakup sumber (observation/diagnostics/planning/recovery/coordination/
    lifecycle), nilai readiness/kesehatan, kepercayaan, bukti, dan ID artefak
    asal. Immutable - aggregator membaca, tidak memodifikasi artefak asal.
    """

    source: str  # observation | diagnostics | planning | recovery | coordination | lifecycle
    artifact_id: str  # ID artefak asal yang diagregasi
    status: str = "unknown"  # ready | degraded | not_ready | unknown | healthy | risky
    health: str = "unknown"  # healthy | degraded | unhealthy | unknown
    confidence: float = 0.0
    evidence: Tuple[str, ...] = ()
    proposal_label: str = ""  # label proposal/penilaian (bukan aksi)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "artifact_id": self.artifact_id,
            "status": self.status,
            "health": self.health,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "proposal_label": self.proposal_label,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ReadinessDimension:
    """Skor satu dimensi kesiapan operasional (0.0 - 1.0).

    Dimensi: observe, diagnose, plan, recover, coordinate, lifecycle,
    readiness. Semua deterministik; nilai turunan dari masukan, bukan keputusan.
    """

    name: str  # observe | diagnose | plan | recover | coordinate | lifecycle | readiness
    score: float
    ready: bool
    contributing_inputs: Tuple[str, ...] = ()  # artifact_id masukan
    detail: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "ready": self.ready,
            "contributing_inputs": list(self.contributing_inputs),
            "detail": self.detail,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class OperationalReadiness:
    """Penilaian kesiapan operasional terpadu (immutable, read-only).

    Integrasi seluruh proposal dari langkah observe -> diagnosis -> plan ->
    recover -> coordinate -> lifecycle menjadi satu penilaian utuh. HANYA
    penilaian: tidak memilih tindakan, tidak menjalankan, tidak mengubah
    governance. Semuanya deterministic & evidence-backed.
    """

    readiness_id: str
    created_at: str
    overall_level: str = "unknown"  # ready | degraded | not_ready | unknown
    overall_score: float = 0.0
    ready: bool = False
    inputs: Tuple[ReadinessInput, ...] = ()
    dimensions: Tuple[ReadinessDimension, ...] = ()
    blockers: Tuple[str, ...] = ()
    top_risks: Tuple[str, ...] = ()
    recommendation: str = ""
    basis: str = "operational readiness integration"
    evidence: Tuple[str, ...] = ()
    trust_score: float = 0.0
    is_proposal_only: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "readiness_id": self.readiness_id,
            "created_at": self.created_at,
            "overall_level": self.overall_level,
            "overall_score": self.overall_score,
            "ready": self.ready,
            "inputs": [i.as_dict() for i in self.inputs],
            "dimensions": [d.as_dict() for d in self.dimensions],
            "blockers": list(self.blockers),
            "top_risks": list(self.top_risks),
            "recommendation": self.recommendation,
            "basis": self.basis,
            "evidence": list(self.evidence),
            "trust_score": self.trust_score,
            "is_proposal_only": self.is_proposal_only,
            "metadata": dict(self.metadata),
        }

    def input_count(self) -> int:
        return len(self.inputs)

    def dimension_count(self) -> int:
        return len(self.dimensions)

    def get_dimension(self, name: str) -> Optional[ReadinessDimension]:
        for d in self.dimensions:
            if d.name == name:
                return d
        return None


@dataclass(frozen=True)
class ReadinessMetadata:
    """Metadata penilaian kesiapan - asal usul, basis bukti, determinisme."""

    readiness_id: str
    created_at: str
    basis: str
    engine: str = "operational_readiness"
    deterministic: bool = True
    evidence_refs: Tuple[str, ...] = ()
    generated_by: str = "operational_readiness_integration"
    phase: str = "integrative"  # integrative (assessment only) - bukan execution
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "readiness_id": self.readiness_id,
            "created_at": self.created_at,
            "basis": self.basis,
            "engine": self.engine,
            "deterministic": self.deterministic,
            "evidence_refs": list(self.evidence_refs),
            "generated_by": self.generated_by,
            "phase": self.phase,
            "metadata": dict(self.metadata),
        }
