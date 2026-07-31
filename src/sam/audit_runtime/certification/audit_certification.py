"""Audit Certification — sertifikasi audit 7 dimensi (Sprint 218)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AuditCertificationCriterion:
    """Kriteria sertifikasi immutable."""
    name: str
    passed: bool = False


@dataclass(frozen=True)
class AuditCertificationResult:
    """Hasil sertifikasi immutable."""
    certified: bool = False
    score: float = 0.0
    criteria: List[AuditCertificationCriterion] = field(default_factory=list)


class AuditCertification:
    """Sertifikasi audit — 7 dimensi."""

    DIMENSIONS = ("Structure", "Integrity", "Consistency", "Completeness",
                  "Determinism", "Immutability", "PreviewOnly")
    EXPECTED_MODULES = 9

    def certify(self, modules_present: int = 9,
                modules_expected: int = None,
                dto_frozen: bool = True,
                no_forbidden_imports: bool = True,
                no_inference: bool = True,
                no_write: bool = True,
                deterministic: bool = True,
                preview_only: bool = True) -> AuditCertificationResult:
        modules_expected = modules_expected or self.EXPECTED_MODULES
        criteria = [
            AuditCertificationCriterion("Structure",
                                        modules_present >= modules_expected),
            AuditCertificationCriterion("Integrity", dto_frozen),
            AuditCertificationCriterion("Consistency", no_forbidden_imports),
            AuditCertificationCriterion("Completeness",
                                        modules_present == modules_expected),
            AuditCertificationCriterion("Determinism", deterministic and no_inference),
            AuditCertificationCriterion("Immutability", dto_frozen),
            AuditCertificationCriterion("PreviewOnly", preview_only and no_write),
        ]
        passed = sum(1 for c in criteria if c.passed)
        score = passed / len(criteria) * 100.0
        certified = score >= 100.0
        return AuditCertificationResult(
            certified=certified, score=score, criteria=list(criteria))
