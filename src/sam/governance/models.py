"""
Governance Models – Sprint 21

Defines the formal governance model for evaluating execution graphs
before they run: risk, approval, cluster conditions, resource capacity,
maintenance windows, and policy guardrails.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class GovernanceDecision(str, Enum):
    """Possible governance decisions when evaluating an execution graph."""

    ALLOW = "ALLOW"
    """Graph may proceed without restrictions."""

    ALLOW_WITH_WARNING = "ALLOW_WITH_WARNING"
    """Graph may proceed but warnings are attached (non-blocking concerns)."""

    WAIT = "WAIT"
    """Graph must wait — typically for a maintenance window to end or cluster to stabilise."""

    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    """Graph requires human or programmatic approval before execution."""

    REJECT = "REJECT"
    """Graph is rejected — risk too high, capacity insufficient, or policy violation."""

    ESCALATE = "ESCALATE"
    """Graph cannot be auto-decided — manual escalation required."""


class GovernanceResult(BaseModel):
    """Result of a governance evaluation (single evaluator or aggregate)."""

    model_config = ConfigDict(extra="forbid")

    decision: GovernanceDecision = Field(
        description="Final decision for this evaluation"
    )
    reason: str = Field(
        default="",
        description="Human-readable explanation of the decision",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warning messages",
    )
    required_approvals: List[str] = Field(
        default_factory=list,
        description="Approval identifiers required before execution (e.g. ['ops-lead', 'security-team'])",
    )
    suggested_delay: Optional[int] = Field(
        default=None,
        description="Suggested delay in seconds before retrying (for WAIT decisions)",
    )
    evaluator_results: Dict[str, "GovernanceResult"] = Field(
        default_factory=dict,
        description="Per-evaluator results keyed by evaluator name (set by engine, not evaluators)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (e.g. risk score, maintenance window info)",
    )

    def is_blocked(self) -> bool:
        """Return True if the decision blocks execution."""
        return self.decision in (
            GovernanceDecision.REQUIRE_APPROVAL,
            GovernanceDecision.REJECT,
            GovernanceDecision.ESCALATE,
        )

    def needs_approval(self) -> bool:
        """Return True if human/system approval is required."""
        return self.decision == GovernanceDecision.REQUIRE_APPROVAL and len(self.required_approvals) > 0

    def is_allowed(self) -> bool:
        """Return True if execution is allowed (possibly with warnings)."""
        return self.decision in (
            GovernanceDecision.ALLOW,
            GovernanceDecision.ALLOW_WITH_WARNING,
        )

    @classmethod
    def allowed(cls, reason: str = "", **kwargs) -> "GovernanceResult":
        """Shorthand for ALLOW decision."""
        return cls(decision=GovernanceDecision.ALLOW, reason=reason, **kwargs)

    @classmethod
    def allowed_with_warning(cls, reason: str = "", warnings: Optional[List[str]] = None, **kwargs) -> "GovernanceResult":
        """Shorthand for ALLOW_WITH_WARNING decision."""
        return cls(
            decision=GovernanceDecision.ALLOW_WITH_WARNING,
            reason=reason,
            warnings=warnings or [],
            **kwargs,
        )

    @classmethod
    def wait(
        cls,
        reason: str = "",
        suggested_delay: Optional[int] = None,
        **kwargs,
    ) -> "GovernanceResult":
        """Shorthand for WAIT decision."""
        return cls(
            decision=GovernanceDecision.WAIT,
            reason=reason,
            suggested_delay=suggested_delay,
            **kwargs,
        )

    @classmethod
    def require_approval(
        cls,
        reason: str = "",
        approvals: Optional[List[str]] = None,
        **kwargs,
    ) -> "GovernanceResult":
        """Shorthand for REQUIRE_APPROVAL decision."""
        return cls(
            decision=GovernanceDecision.REQUIRE_APPROVAL,
            reason=reason,
            required_approvals=approvals or [],
            **kwargs,
        )

    @classmethod
    def rejected(cls, reason: str = "", **kwargs) -> "GovernanceResult":
        """Shorthand for REJECT decision."""
        return cls(decision=GovernanceDecision.REJECT, reason=reason, **kwargs)

    @classmethod
    def escalated(cls, reason: str = "", **kwargs) -> "GovernanceResult":
        """Shorthand for ESCALATE decision."""
        return cls(decision=GovernanceDecision.ESCALATE, reason=reason, **kwargs)


class GovernanceRule(BaseModel):
    """A single governance rule stored in the database or loaded from config."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Unique rule ID")
    name: str = Field(description="Human-readable rule name")
    evaluator_type: str = Field(
        description="Evaluator type: RISK, APPROVAL, MAINTENANCE, CLUSTER, RESOURCE, CAPABILITY, POLICY"
    )
    condition: str = Field(
        default="",
        description="Expression or predicate that triggers this rule (evaluator-specific syntax)",
    )
    decision_override: Optional[GovernanceDecision] = Field(
        default=None,
        description="If set, overrides the evaluator's natural decision with this value",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this rule is active",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary evaluator-specific metadata",
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Rule creation timestamp",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp",
    )
