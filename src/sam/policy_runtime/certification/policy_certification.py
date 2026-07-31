"""Policy Certification — sertifikasi policy (Sprint 210).

7 dimensi: Structure, Integrity, Consistency, Completeness,
Determinism, Immutability, PreviewOnly.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .policy_score import PolicyScorer  # noqa: F401


@dataclass(frozen=True)
class PolicyCertificationCriterion:
    """Kriteria sertifikasi (immutable)."""
    name: str
    passed: bool = False
    detail: str = ""


@dataclass(frozen=True)
class PolicyCertificationResult:
    """Hasil sertifikasi (immutable)."""
    certified: bool = False
    score: float = 0.0
    criteria: List[PolicyCertificationCriterion] = field(default_factory=list)


class PolicyCertification:
    """Sertifikasi policy. Deterministik, read-only."""

    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def __init__(self) -> None:
        self._scorer = PolicyScorer()

    def certify(
        self,
        modules_present: int = 0,
        modules_expected: int = 0,
        dto_frozen: bool = True,
        no_forbidden_imports: bool = True,
        no_inference: bool = True,
        no_write: bool = True,
        deterministic: bool = True,
        preview_only: bool = True,
    ) -> PolicyCertificationResult:
        criteria = [
            PolicyCertificationCriterion(
                "Structure", modules_present >= modules_expected,
                f"{modules_present}/{modules_expected} modules",
            ),
            PolicyCertificationCriterion("Integrity", no_forbidden_imports),
            PolicyCertificationCriterion("Consistency", modules_present <= modules_expected),
            PolicyCertificationCriterion(
                "Completeness", modules_present >= modules_expected
            ),
            PolicyCertificationCriterion("Determinism", deterministic),
            PolicyCertificationCriterion("Immutability", dto_frozen),
            PolicyCertificationCriterion(
                "PreviewOnly", preview_only and no_write and no_inference
            ),
        ]
        certified = all(c.passed for c in criteria)
        score = self._scorer.compute(criteria)
        return PolicyCertificationResult(
            certified=certified, score=score, criteria=criteria,
        )
