"""Verification Result model — ADR-007, AUDIT_SPEC §Verification.

Verification occurs after Execution completes, before Audit finalization.
Per ADR-007: Verification is a state transition Recorded → Verified
within the Audit Recorder, not a separate unit.

Verification:
- does not change the outcome
- does not repeat execution
- only verifies compliance
- produces verification status
- produces verification evidence
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class VerificationStatus(str, Enum):
    """Outcome of verification per ADR-007."""
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"


@dataclass(frozen=True)
class VerificationResult:
    """Immutable result of traceability verification.

    Per ADR-007: verification checks compliance by tracing
    references through Contract + Registry, without affecting
    the execution outcome.

    Authority: ADR-007, AUDIT_SPEC §Verification
    """
    status: VerificationStatus
    evidence: str = ""
    broken_references: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def verified(cls, evidence: str = "") -> "VerificationResult":
        """Factory for VERIFIED result."""
        return cls(
            status=VerificationStatus.VERIFIED,
            evidence=evidence,
            broken_references={},
        )

    @classmethod
    def not_verified(
        cls,
        evidence: str = "",
        broken_references: Optional[Dict[str, str]] = None,
    ) -> "VerificationResult":
        """Factory for NOT_VERIFIED result."""
        return cls(
            status=VerificationStatus.NOT_VERIFIED,
            evidence=evidence,
            broken_references=broken_references or {},
        )

    def is_verified(self) -> bool:
        """Return True if verification passed."""
        return self.status == VerificationStatus.VERIFIED

    def has_broken_references(self) -> bool:
        """Return True if any references are broken."""
        return len(self.broken_references) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Return verification result as a dictionary."""
        return {
            "status": self.status.value,
            "evidence": self.evidence,
            "broken_references": self.broken_references,
        }

    def __repr__(self) -> str:
        broken = (
            f", broken={self.broken_references}"
            if self.has_broken_references() else ""
        )
        return (
            f"VerificationResult("
            f"status={self.status.value}, "
            f"evidence='{self.evidence}'{broken})"
        )
