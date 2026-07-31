"""Cognitive Certification — sertifikasi kognitif (Sprint 194).

7 dimensi: Structure, Integrity, Consistency, Completeness,
Determinism, Immutability, PreviewOnly.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .cognitive_score import CognitiveScorer  # noqa: F401


@dataclass(frozen=True)
class CognitiveCertificationCriterion:
    """Kriteria sertifikasi (immutable)."""
    name: str
    passed: bool = False
    detail: str = ""


@dataclass(frozen=True)
class CognitiveCertificationResult:
    """Hasil sertifikasi (immutable)."""
    certified: bool = False
    score: float = 0.0
    criteria: List[CognitiveCertificationCriterion] = field(default_factory=list)


class CognitiveCertification:
    """Sertifikasi kognitif. Deterministik, read-only."""

    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def __init__(self) -> None:
        self._scorer = CognitiveScorer()

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
    ) -> CognitiveCertificationResult:
        criteria = [
            CognitiveCertificationCriterion(
                "Structure", modules_present >= modules_expected,
                f"{modules_present}/{modules_expected} modules",
            ),
            CognitiveCertificationCriterion("Integrity", no_forbidden_imports),
            CognitiveCertificationCriterion("Consistency", modules_present <= modules_expected),
            CognitiveCertificationCriterion(
                "Completeness", modules_present >= modules_expected
            ),
            CognitiveCertificationCriterion("Determinism", deterministic),
            CognitiveCertificationCriterion("Immutability", dto_frozen),
            CognitiveCertificationCriterion(
                "PreviewOnly", preview_only and no_write and no_inference
            ),
        ]
        certified = all(c.passed for c in criteria)
        score = self._scorer.compute(criteria)
        return CognitiveCertificationResult(
            certified=certified, score=score, criteria=criteria,
        )
