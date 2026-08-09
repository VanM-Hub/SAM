"""Trust Assessment - WP-24 (MISSION-4.2 / IP-4.2-003).

Menilai trust atas diagnosis & rekomendasi secara deterministik.
Read-only, evidence-based.
"""
from __future__ import annotations

from dataclasses import dataclass

from .operational_diagnosis import DiagnosisConfidence


@dataclass(frozen=True)
class TrustAssessment:
    """Hasil penilaian trust (deterministik)."""

    assessment_id: str
    confidence: DiagnosisConfidence
    evidence_count: int = 0
    traceability: bool = False
    explainability: bool = False
    trust_score: float = 0.0

    @property
    def level(self) -> str:
        if self.trust_score >= 0.8:
            return "high"
        if self.trust_score >= 0.5:
            return "medium"
        if self.trust_score > 0.0:
            return "low"
        return "none"

    def as_dict(self) -> dict:
        return {
            "assessment_id": self.assessment_id,
            "confidence": self.confidence.as_dict(),
            "evidence_count": self.evidence_count,
            "traceability": self.traceability,
            "explainability": self.explainability,
            "trust_score": self.trust_score,
            "level": self.level,
        }


class TrustAssessor:
    """Menghitung trust score (deterministik)."""

    WEIGHT_CONFIDENCE = 0.5
    WEIGHT_EVIDENCE = 0.3
    WEIGHT_TRACE = 0.2

    def assess(
        self,
        assessment_id: str,
        confidence: DiagnosisConfidence,
        *,
        evidence_count: int = 0,
        traceability: bool = True,
        explainability: bool = True,
    ) -> TrustAssessment:
        conf_component = confidence.value * self.WEIGHT_CONFIDENCE
        ev_component = min(1.0, evidence_count / 5.0) * self.WEIGHT_EVIDENCE
        trace_component = float(traceability and explainability) * self.WEIGHT_TRACE
        score = round(min(1.0, conf_component + ev_component + trace_component), 3)
        return TrustAssessment(
            assessment_id=assessment_id,
            confidence=confidence,
            evidence_count=evidence_count,
            traceability=traceability,
            explainability=explainability,
            trust_score=score,
        )
