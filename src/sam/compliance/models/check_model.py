"""ComplianceCheck model per P1-001 §2 (Check Model)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Callable

from ..models.level import ComplianceLevel
from ..models.category import ComplianceCategory
from ..models.evidence_type import EvidenceType
from ..models.severity import Severity


@dataclass(frozen=True)
class ComplianceCheck:
    """Immutable compliance check definition.

    Each check has: identifier, level, category, description,
    evidence type, severity, baseline reference, and an optional
    execution callable.

    Per P1-001 Check Model specification.
    """

    check_id: str
    """Unique check identifier, e.g. 'L1-C01'."""

    level: ComplianceLevel
    """Compliance level (L0-L4)."""

    category: ComplianceCategory
    """Compliance category (1 of 10)."""

    description: str
    """Human-readable description of what this check verifies."""

    evidence_type: EvidenceType
    """Expected evidence type for this check."""

    severity: Severity
    """Default severity if check fails (per P1-001 §5.3)."""

    baseline_ref: str = ""
    """Reference to baseline document + line, e.g. 'CITIZEN_SPEC L10-12'."""

    recommendation: str = ""
    """Recommended action if check fails."""

    execution_fn: Optional[Callable] = field(default=None, compare=False, repr=False)
    """Optional callable that executes this check. Takes no args, returns ComplianceEvidence or None."""

    def execute(self):
        """Execute this check's execution function if available."""
        if self.execution_fn is not None:
            return self.execution_fn()
        return None

    def is_executable(self) -> bool:
        """Whether this check has an execution function."""
        return self.execution_fn is not None

    def to_dict(self):
        return {
            "check_id": self.check_id,
            "level": self.level.value,
            "category": self.category.value,
            "description": self.description,
            "evidence_type": self.evidence_type.value,
            "severity": self.severity.value,
            "baseline_ref": self.baseline_ref,
            "recommendation": self.recommendation,
        }
