"""ComplianceFinding model per P1-001 §5."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..models.classification import FindingClassification
from ..models.severity import Severity
from ..models.evidence import ComplianceEvidence


@dataclass(frozen=True)
class ComplianceFinding:
    """Immutable compliance finding record.

    Links a check to its evidence and classification.
    Per P1-001 §5 Findings & Severity.
    """

    check_id: str
    """ID of the check that produced this finding."""

    classification: FindingClassification
    """Whether this is CONFORMITY, DEVIATION, INCONCLUSIVE, or NOT_APPLICABLE."""

    severity: Severity
    """Severity level (CRITICAL, MAJOR, MINOR, INFO)."""

    description: str = ""
    """Human-readable description of this finding."""

    evidence_ref: Optional[ComplianceEvidence] = field(default=None, compare=False, repr=False)
    """Reference to the evidence that produced this finding."""

    recommendation: str = ""
    """Recommended action if deviation."""

    baseline_ref: str = ""
    """Reference to baseline document + line."""

    @classmethod
    def conforming(cls, check_id: str, severity: Severity,
                   description: str = "", evidence: Optional[ComplianceEvidence] = None,
                   baseline_ref: str = "") -> ComplianceFinding:
        """Create a conforming (pass) finding."""
        return cls(
            check_id=check_id,
            classification=FindingClassification.CONFORMITY,
            severity=severity,
            description=description or ("Check %s: conforms to baseline" % check_id),
            evidence_ref=evidence,
            baseline_ref=baseline_ref,
        )

    @classmethod
    def deviating(cls, check_id: str, severity: Severity,
                  description: str = "", evidence: Optional[ComplianceEvidence] = None,
                  recommendation: str = "", baseline_ref: str = "") -> ComplianceFinding:
        """Create a deviating (fail) finding."""
        return cls(
            check_id=check_id,
            classification=FindingClassification.DEVIATION,
            severity=severity,
            description=description or ("Check %s: deviates from baseline" % check_id),
            evidence_ref=evidence,
            recommendation=recommendation,
            baseline_ref=baseline_ref,
        )

    @classmethod
    def inconclusive(cls, check_id: str, severity: Severity,
                     description: str = "", baseline_ref: str = "") -> ComplianceFinding:
        """Create an inconclusive finding."""
        return cls(
            check_id=check_id,
            classification=FindingClassification.INCONCLUSIVE,
            severity=severity,
            description=description or ("Check %s: evidence inconclusive" % check_id),
            baseline_ref=baseline_ref,
        )

    @classmethod
    def not_applicable(cls, check_id: str, severity: Severity = Severity.INFO,
                       description: str = "", baseline_ref: str = "") -> ComplianceFinding:
        """Create a not-applicable finding."""
        return cls(
            check_id=check_id,
            classification=FindingClassification.NOT_APPLICABLE,
            severity=severity,
            description=description or ("Check %s: not applicable" % check_id),
            baseline_ref=baseline_ref,
        )

    def is_critical(self) -> bool:
        return self.severity == Severity.CRITICAL

    def is_major(self) -> bool:
        return self.severity == Severity.MAJOR

    def is_minor(self) -> bool:
        return self.severity == Severity.MINOR

    def is_conforming(self) -> bool:
        return self.classification == FindingClassification.CONFORMITY

    def is_deviating(self) -> bool:
        return self.classification == FindingClassification.DEVIATION

    def to_dict(self):
        return {
            "check_id": self.check_id,
            "classification": self.classification.value,
            "severity": self.severity.value,
            "description": self.description,
            "recommendation": self.recommendation,
            "baseline_ref": self.baseline_ref,
        }
