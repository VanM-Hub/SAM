"""ComplianceEvidence model per P1-001 §4."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..models.evidence_type import EvidenceType


@dataclass(frozen=True)
class ComplianceEvidence:
    """Immutable compliance evidence record.

    Represents one piece of objective evidence from a compliance check.
    Per P1-001 §4 Evidence Model.
    """

    check_id: str
    """ID of the check this evidence belongs to."""

    evidence_type: EvidenceType
    """Type of evidence collected."""

    status: str
    """Evidence status: 'COLLECTED', 'PASSED', 'FAILED'."""

    value: Any = None
    """Raw evidence value (file path, boolean, source text, etc.)."""

    source_path: str = ""
    """Path to the source that produced this evidence."""

    timestamp: str = ""
    """ISO-format timestamp of evidence collection."""

    baseline_ref: str = ""
    """Reference to baseline document."""

    details: str = ""
    """Additional details or notes about this evidence."""

    @classmethod
    def conforming(cls, check_id: str, evidence_type: EvidenceType,
                   value: Any = None, source_path: str = "",
                   timestamp: str = "", baseline_ref: str = "",
                   details: str = "") -> ComplianceEvidence:
        """Create a conforming (PASSED) evidence record."""
        return cls(
            check_id=check_id,
            evidence_type=evidence_type,
            status="PASSED",
            value=value,
            source_path=source_path,
            timestamp=timestamp,
            baseline_ref=baseline_ref,
            details=details,
        )

    @classmethod
    def deviating(cls, check_id: str, evidence_type: EvidenceType,
                  value: Any = None, source_path: str = "",
                  timestamp: str = "", baseline_ref: str = "",
                  details: str = "") -> ComplianceEvidence:
        """Create a deviating (FAILED) evidence record."""
        return cls(
            check_id=check_id,
            evidence_type=evidence_type,
            status="FAILED",
            value=value,
            source_path=source_path,
            timestamp=timestamp,
            baseline_ref=baseline_ref,
            details=details,
        )

    @classmethod
    def collected(cls, check_id: str, evidence_type: EvidenceType,
                  value: Any = None, source_path: str = "",
                  timestamp: str = "", baseline_ref: str = "",
                  details: str = "") -> ComplianceEvidence:
        """Create a collected (not yet analyzed) evidence record."""
        return cls(
            check_id=check_id,
            evidence_type=evidence_type,
            status="COLLECTED",
            value=value,
            source_path=source_path,
            timestamp=timestamp,
            baseline_ref=baseline_ref,
            details=details,
        )

    def is_passed(self) -> bool:
        return self.status == "PASSED"

    def is_failed(self) -> bool:
        return self.status == "FAILED"

    def to_dict(self):
        return {
            "check_id": self.check_id,
            "evidence_type": self.evidence_type.value,
            "status": self.status,
            "value": str(self.value) if self.value is not None else "",
            "source_path": self.source_path,
            "timestamp": self.timestamp,
            "baseline_ref": self.baseline_ref,
            "details": self.details,
        }
