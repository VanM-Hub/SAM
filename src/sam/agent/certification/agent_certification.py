"""Agent Certification — sertifikasi agent (Sprint 163).

Score dimensions mengikuti blueprint:
Completeness, Consistency, Determinism, Layer Safety,
Architecture Safety, DTO Safety, Pipeline Safety.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .agent_score import AgentScorer  # noqa: F401


@dataclass(frozen=True)
class CertificationCriterion:
    """Kriteria sertifikasi (immutable)."""
    name: str
    passed: bool = False
    detail: str = ""


@dataclass(frozen=True)
class CertificationResult:
    """Hasil sertifikasi (immutable)."""
    certified: bool = False
    total_score: float = 0.0
    criteria: List[CertificationCriterion] = field(default_factory=list)


class AgentCertification:
    """Sertifikasi agent. Deterministik, read-only."""

    DIMENSIONS = [
        "Completeness",
        "Consistency",
        "Determinism",
        "Layer Safety",
        "Architecture Safety",
        "DTO Safety",
        "Pipeline Safety",
    ]

    def __init__(self) -> None:
        self._scorer = AgentScorer()

    def certify(
        self,
        modules_present: int = 0,
        modules_expected: int = 0,
        dto_frozen: bool = True,
        no_forbidden_imports: bool = True,
        deterministic: bool = True,
    ) -> CertificationResult:
        criteria = [
            CertificationCriterion(
                "Completeness",
                modules_present >= modules_expected,
                f"{modules_present}/{modules_expected} modules",
            ),
            CertificationCriterion("Consistency", modules_present <= modules_expected),
            CertificationCriterion("Determinism", deterministic),
            CertificationCriterion("Layer Safety", no_forbidden_imports),
            CertificationCriterion("Architecture Safety", no_forbidden_imports),
            CertificationCriterion("DTO Safety", dto_frozen),
            CertificationCriterion("Pipeline Safety", deterministic),
        ]
        certified = all(c.passed for c in criteria)
        score = self._scorer.compute(criteria)
        return CertificationResult(
            certified=certified,
            total_score=score,
            criteria=criteria,
        )


__all__ = ["AgentCertification", "CertificationCriterion", "CertificationResult"]
