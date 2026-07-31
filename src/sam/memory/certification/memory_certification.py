"""Memory Certification — sertifikasi memori (Sprint 178).

7 dimensi: Structure, Integrity, Consistency, Completeness,
Determinism, Immutability, PreviewOnly.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .memory_score import MemoryScorer  # noqa: F401


@dataclass(frozen=True)
class MemoryCertificationCriterion:
    """Kriteria sertifikasi (immutable)."""
    name: str
    passed: bool = False
    detail: str = ""


@dataclass(frozen=True)
class MemoryCertificationResult:
    """Hasil sertifikasi memori (immutable)."""
    certified: bool = False
    score: float = 0.0
    criteria: List[MemoryCertificationCriterion] = field(default_factory=list)


class MemoryCertification:
    """Sertifikasi memori. Deterministik, read-only."""

    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def __init__(self) -> None:
        self._scorer = MemoryScorer()

    def certify(
        self,
        modules_present: int = 0,
        modules_expected: int = 0,
        dto_frozen: bool = True,
        no_forbidden_imports: bool = True,
        no_write: bool = True,
        deterministic: bool = True,
        preview_only: bool = True,
    ) -> MemoryCertificationResult:
        criteria = [
            MemoryCertificationCriterion(
                "Structure",
                modules_present >= modules_expected,
                f"{modules_present}/{modules_expected} modules",
            ),
            MemoryCertificationCriterion("Integrity", no_forbidden_imports),
            MemoryCertificationCriterion("Consistency", modules_present <= modules_expected),
            MemoryCertificationCriterion(
                "Completeness", modules_present >= modules_expected
            ),
            MemoryCertificationCriterion("Determinism", deterministic),
            MemoryCertificationCriterion("Immutability", dto_frozen),
            MemoryCertificationCriterion("PreviewOnly", preview_only and no_write),
        ]
        certified = all(c.passed for c in criteria)
        score = self._scorer.compute(criteria)
        return MemoryCertificationResult(
            certified=certified, score=score, criteria=criteria,
        )
