"""Workflow Certification — sertifikasi workflow (Sprint 202).

7 dimensi: Structure, Integrity, Consistency, Completeness,
Determinism, Immutability, PreviewOnly.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .workflow_score import WorkflowScorer  # noqa: F401


@dataclass(frozen=True)
class WorkflowCertificationCriterion:
    """Kriteria sertifikasi (immutable)."""
    name: str
    passed: bool = False
    detail: str = ""


@dataclass(frozen=True)
class WorkflowCertificationResult:
    """Hasil sertifikasi (immutable)."""
    certified: bool = False
    score: float = 0.0
    criteria: List[WorkflowCertificationCriterion] = field(default_factory=list)


class WorkflowCertification:
    """Sertifikasi workflow. Deterministik, read-only."""

    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def __init__(self) -> None:
        self._scorer = WorkflowScorer()

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
    ) -> WorkflowCertificationResult:
        criteria = [
            WorkflowCertificationCriterion(
                "Structure", modules_present >= modules_expected,
                f"{modules_present}/{modules_expected} modules",
            ),
            WorkflowCertificationCriterion("Integrity", no_forbidden_imports),
            WorkflowCertificationCriterion("Consistency", modules_present <= modules_expected),
            WorkflowCertificationCriterion(
                "Completeness", modules_present >= modules_expected
            ),
            WorkflowCertificationCriterion("Determinism", deterministic),
            WorkflowCertificationCriterion("Immutability", dto_frozen),
            WorkflowCertificationCriterion(
                "PreviewOnly", preview_only and no_write and no_inference
            ),
        ]
        certified = all(c.passed for c in criteria)
        score = self._scorer.compute(criteria)
        return WorkflowCertificationResult(
            certified=certified, score=score, criteria=criteria,
        )
