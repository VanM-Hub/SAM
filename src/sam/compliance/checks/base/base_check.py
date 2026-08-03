"""BaseComplianceCheck — abstract base for all compliance checks.

Every concrete check MUST inherit from this class. Checks are:
- deterministic: same context → same result
- stateless: no mutable internal state
- self-describing: carry their own metadata
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional

from ...models.check_model import ComplianceCheck
from ...models.level import ComplianceLevel
from ...models.category import ComplianceCategory
from ...models.severity import Severity
from ...models.evidence_type import EvidenceType
from .check_context import CheckContext
from .check_result import CheckResult


class BaseComplianceCheck(ABC):
    """Abstract base for all compliance checks.

    Each check declares:
    - check_id: unique identifier
    - level: L0-L4 compliance level
    - category: one of 10 categories
    - description: what this check verifies
    - evidence_type: expected evidence
    - severity: default severity on failure
    - baseline_ref: reference to baseline document
    - recommendation: action on failure

    Subclasses MUST implement execute(context) -> CheckResult.
    """

    def __init__(
        self,
        check_id: str,
        level: ComplianceLevel,
        category: ComplianceCategory,
        description: str,
        evidence_type: EvidenceType,
        severity: Severity,
        baseline_ref: str = "",
        recommendation: str = "",
    ) -> None:
        self._check_id = check_id
        self._level = level
        self._category = category
        self._description = description
        self._evidence_type = evidence_type
        self._severity = severity
        self._baseline_ref = baseline_ref
        self._recommendation = recommendation

    # -- Read-only properties ------------------------------------------------

    @property
    def check_id(self) -> str:
        return self._check_id

    @property
    def level(self) -> ComplianceLevel:
        return self._level

    @property
    def category(self) -> ComplianceCategory:
        return self._category

    @property
    def description(self) -> str:
        return self._description

    @property
    def evidence_type(self) -> EvidenceType:
        return self._evidence_type

    @property
    def severity(self) -> Severity:
        return self._severity

    @property
    def baseline_ref(self) -> str:
        return self._baseline_ref

    @property
    def recommendation(self) -> str:
        return self._recommendation

    # -- Abstract interface --------------------------------------------------

    @abstractmethod
    def execute(self, context: CheckContext) -> CheckResult:
        """Execute this check against the given context.

        MUST be deterministic: same context → same result.
        MUST be stateless: no mutation of internal state.
        """

    # -- Integration with P1-002 ---------------------------------------------

    def as_execution_fn(self, context: CheckContext) -> Callable[[], bool]:
        """Return a zero-arg callable compatible with ComplianceRunner.

        The runner calls execution_fn() and normalizes the bool
        result into a ComplianceEvidence record.
        """

        def fn() -> bool:
            result = self.execute(context)
            return result.passed

        return fn

    def to_compliance_check(self, context: CheckContext) -> ComplianceCheck:
        """Build a ComplianceCheck model suitable for registration.

        The returned ComplianceCheck has execution_fn attached,
        ready for the ComplianceRegistry and ComplianceRunner.
        """
        return ComplianceCheck(
            check_id=self.check_id,
            level=self.level,
            category=self.category,
            description=self.description,
            evidence_type=self.evidence_type,
            severity=self.severity,
            baseline_ref=self.baseline_ref,
            recommendation=self.recommendation,
            execution_fn=self.as_execution_fn(context),
        )

    # -- Configuration serialization -----------------------------------------

    def to_config(self) -> dict:
        """Serialize to a configuration dictionary for factory reconstruction.

        Subclasses should override and call super().to_config() to add
        type-specific fields.
        """
        return {
            "type": type(self).__name__,
            "check_id": self.check_id,
            "level": self.level.value,
            "category": self.category.value,
            "description": self.description,
            "evidence_type": self.evidence_type.value,
            "severity": self.severity.value,
            "baseline_ref": self.baseline_ref,
            "recommendation": self.recommendation,
        }
