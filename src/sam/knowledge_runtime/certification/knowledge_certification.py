"""Knowledge Certification — sertifikasi knowledge (Sprint 186).

7 dimensi: Structure, Integrity, Consistency, Completeness,
Determinism, Immutability, PreviewOnly.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .knowledge_score import KnowledgeScorer  # noqa: F401


@dataclass(frozen=True)
class KnowledgeCertificationCriterion:
    """Kriteria sertifikasi (immutable)."""
    name: str
    passed: bool = False
    detail: str = ""


@dataclass(frozen=True)
class KnowledgeCertificationResult:
    """Hasil sertifikasi knowledge (immutable)."""
    certified: bool = False
    score: float = 0.0
    criteria: List[KnowledgeCertificationCriterion] = field(default_factory=list)


class KnowledgeCertification:
    """Sertifikasi knowledge. Deterministik, read-only."""

    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def __init__(self) -> None:
        self._scorer = KnowledgeScorer()

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
    ) -> KnowledgeCertificationResult:
        criteria = [
            KnowledgeCertificationCriterion(
                "Structure",
                modules_present >= modules_expected,
                f"{modules_present}/{modules_expected} modules",
            ),
            KnowledgeCertificationCriterion("Integrity", no_forbidden_imports),
            KnowledgeCertificationCriterion("Consistency", modules_present <= modules_expected),
            KnowledgeCertificationCriterion(
                "Completeness", modules_present >= modules_expected
            ),
            KnowledgeCertificationCriterion("Determinism", deterministic),
            KnowledgeCertificationCriterion("Immutability", dto_frozen),
            KnowledgeCertificationCriterion(
                "PreviewOnly", preview_only and no_write and no_inference
            ),
        ]
        certified = all(c.passed for c in criteria)
        score = self._scorer.compute(criteria)
        return KnowledgeCertificationResult(
            certified=certified, score=score, criteria=criteria,
        )
