"""Operational Diagnosis + Diagnosis Confidence - WP-15/16 (MISSION-4.2 / IP-4.2-002).

Mengubah evidence menjadi diagnosis operasional dengan confidence.
Diagnosis memiliki confidence deterministik dan menghasilkan evidence chain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple

from .evidence_collection import EvidenceModel
from .root_cause_analysis import RootCauseResult


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class DiagnosisConfidence:
    """Confidence diagnosis (deterministik, 0.0 - 1.0)."""

    value: float = 0.0
    evidence_support: float = 0.0
    coverage: float = 0.0

    @property
    def level(self) -> str:
        if self.value >= 0.8:
            return "high"
        if self.value >= 0.5:
            return "medium"
        if self.value > 0.0:
            return "low"
        return "none"

    def as_dict(self) -> dict:
        return {
            "value": self.value,
            "evidence_support": self.evidence_support,
            "coverage": self.coverage,
            "level": self.level,
        }


@dataclass(frozen=True)
class OperationalDiagnosis:
    """Diagnosis operasional berbasis evidence."""

    diagnosis_id: str
    investigation_id: str
    summary: str
    root_cause: str
    confidence: DiagnosisConfidence
    evidence_ids: Tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "diagnosis_id": self.diagnosis_id,
            "investigation_id": self.investigation_id,
            "summary": self.summary,
            "root_cause": self.root_cause,
            "confidence": self.confidence.as_dict(),
            "evidence_ids": list(self.evidence_ids),
            "created_at": self.created_at,
        }


class DiagnosisConfidenceCalculator:
    """Menghitung confidence diagnosis (deterministik)."""

    @classmethod
    def calculate(cls, rca: RootCauseResult) -> DiagnosisConfidence:
        evidence_support = rca.overall_confidence
        coverage = cls._coverage(rca)
        value = round(evidence_support * 0.7 + coverage * 0.3, 3)
        return DiagnosisConfidence(
            value=value,
            evidence_support=round(evidence_support, 3),
            coverage=coverage,
        )

    @staticmethod
    def _coverage(rca: RootCauseResult) -> float:
        if not rca.findings:
            return 0.0
        total = sum(f.confidence for f in rca.findings)
        return min(1.0, total)


class OperationalDiagnosisEngine:
    """Mesin diagnosis operasional (read-only)."""

    def __init__(self, rca_analyzer) -> None:
        self._rca = rca_analyzer

    def diagnose(
        self,
        investigation_id: str,
        observed_event: str,
        evidences: Tuple[EvidenceModel, ...],
    ) -> OperationalDiagnosis:
        rca = self._rca.analyze(
            investigation_id, observed_event, evidences
        )
        confidence = DiagnosisConfidenceCalculator.calculate(rca)
        top = rca.top_finding
        root_cause = top.hypothesis if top else "No root cause identified"
        evidence_ids = top.supporting_evidence if top else ()
        import uuid

        return OperationalDiagnosis(
            diagnosis_id=uuid.uuid4().hex,
            investigation_id=investigation_id,
            summary=(
                f"Diagnosis for {observed_event} with "
                f"{confidence.level} confidence."
            ),
            root_cause=root_cause,
            confidence=confidence,
            evidence_ids=evidence_ids,
        )
