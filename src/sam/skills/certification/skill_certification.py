"""Skill Certification — sertifikasi skill (Sprint 170).

Dimensi (blueprint): Structure, Integrity, Consistency, Completeness,
Determinism, Immutability, PreviewOnly.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .skill_score import SkillScorer  # noqa: F401


@dataclass(frozen=True)
class CertificationCriterion:
    """Kriteria sertifikasi (immutable)."""
    name: str
    passed: bool = False
    detail: str = ""


@dataclass(frozen=True)
class SkillCertificationResult:
    """Hasil sertifikasi skill (immutable)."""
    certified: bool = False
    score: float = 0.0
    criteria: List[CertificationCriterion] = field(default_factory=list)


class SkillCertification:
    """Sertifikasi skill. Deterministik, read-only."""

    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def __init__(self) -> None:
        self._scorer = SkillScorer()

    def certify(
        self,
        modules_present: int = 0,
        modules_expected: int = 0,
        dto_frozen: bool = True,
        no_forbidden_imports: bool = True,
        deterministic: bool = True,
        preview_only: bool = True,
    ) -> SkillCertificationResult:
        criteria = [
            CertificationCriterion(
                "Structure",
                modules_present >= modules_expected,
                f"{modules_present}/{modules_expected} modules",
            ),
            CertificationCriterion("Integrity", no_forbidden_imports),
            CertificationCriterion("Consistency", modules_present <= modules_expected),
            CertificationCriterion(
                "Completeness", modules_present >= modules_expected
            ),
            CertificationCriterion("Determinism", deterministic),
            CertificationCriterion("Immutability", dto_frozen),
            CertificationCriterion("PreviewOnly", preview_only),
        ]
        certified = all(c.passed for c in criteria)
        score = self._scorer.compute(criteria)
        return SkillCertificationResult(
            certified=certified, score=score, criteria=criteria,
        )
