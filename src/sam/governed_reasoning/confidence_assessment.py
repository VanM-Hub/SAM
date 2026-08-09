"""Confidence Assessment - WP-14 (MISSION-4.4 / IP-4.4-002).

Menilai confidence hasil reasoning (deterministik, berbasis evidence &
dukungan langkah).
"""
from __future__ import annotations

from dataclasses import dataclass

from .structured_reasoning import StructuredReasoning


@dataclass(frozen=True)
class ConfidenceAssessment:
    """Hasil penilaian confidence."""

    reasoning_id: str
    value: float = 0.0
    evidence_coverage: float = 0.0
    step_support: float = 0.0

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
            "reasoning_id": self.reasoning_id,
            "value": self.value,
            "evidence_coverage": self.evidence_coverage,
            "step_support": self.step_support,
            "level": self.level,
        }


class ConfidenceAssessor:
    """Menghitung confidence reasoning (deterministik)."""

    @staticmethod
    def assess(reasoning: StructuredReasoning) -> ConfidenceAssessment:
        if not reasoning.steps:
            return ConfidenceAssessment(reasoning_id=reasoning.reasoning_id)
        evidence_coverage = reasoning.total_evidence / max(
            len(reasoning.steps), 1
        )
        step_support = sum(
            1 for s in reasoning.steps if s.evidence_refs
        ) / len(reasoning.steps)
        value = round(evidence_coverage * 0.6 + step_support * 0.4, 3)
        return ConfidenceAssessment(
            reasoning_id=reasoning.reasoning_id,
            value=value,
            evidence_coverage=round(evidence_coverage, 3),
            step_support=round(step_support, 3),
        )
