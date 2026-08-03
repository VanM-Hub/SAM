"""Approval Decision per APPROVAL_SPEC.

The Approval process produces a decision:
- Approved: the operation may proceed
- Rejected: the operation may not proceed
- Expired: the Approval was valid but is no longer valid
- Cancelled: the Approval was withdrawn before a decision took effect
- Superseded: a newer Approval replaced this Approval

ADR-001: deterministic output shape, explainable, auditable.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Type, Any


class ApprovalDecisionState(str, Enum):
    """Decision states per APPROVAL_SPEC 'Approval Decision'.

    Fixed set of 6 states — this is the deterministic output shape
    mandated by ADR-001.
    """
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class ApprovalDecision:
    """An Approval Decision — the outcome of the Approval process.

    Per ADR-001:
    - State is one of 6 fixed values (deterministic output shape)
    - decision_reason explains the decision (explainable)
    - decided_at + decided_by provide audit trail (auditable)
    - Binding — cannot be changed after creation (frozen)
    """
    state: ApprovalDecisionState
    decision_reason: str
    approval_id: str
    decided_at: float
    decided_by: str
    metadata: Any = None

    # ── Factory methods ──────────────────────────

    @classmethod
    def approved(
        cls,
        approval_id: str,
        reason: str,
        decided_by: str = "system",
        metadata: Any = None,
    ) -> "ApprovalDecision":
        """Create an APPROVED decision."""
        return cls(
            state=ApprovalDecisionState.APPROVED,
            decision_reason=reason,
            approval_id=approval_id,
            decided_at=time.time(),
            decided_by=decided_by,
            metadata=metadata,
        )

    @classmethod
    def rejected(
        cls,
        approval_id: str,
        reason: str,
        decided_by: str = "system",
        metadata: Any = None,
    ) -> "ApprovalDecision":
        """Create a REJECTED decision."""
        return cls(
            state=ApprovalDecisionState.REJECTED,
            decision_reason=reason,
            approval_id=approval_id,
            decided_at=time.time(),
            decided_by=decided_by,
            metadata=metadata,
        )

    @classmethod
    def expired(
        cls,
        approval_id: str,
        reason: str = "Approval request expired",
        decided_by: str = "system",
    ) -> "ApprovalDecision":
        """Create an EXPIRED decision."""
        return cls(
            state=ApprovalDecisionState.EXPIRED,
            decision_reason=reason,
            approval_id=approval_id,
            decided_at=time.time(),
            decided_by=decided_by,
            metadata=None,
        )

    @classmethod
    def cancelled(
        cls,
        approval_id: str,
        reason: str = "Approval request was withdrawn",
        decided_by: str = "system",
    ) -> "ApprovalDecision":
        """Create a CANCELLED decision."""
        return cls(
            state=ApprovalDecisionState.CANCELLED,
            decision_reason=reason,
            approval_id=approval_id,
            decided_at=time.time(),
            decided_by=decided_by,
            metadata=None,
        )

    @classmethod
    def superseded(
        cls,
        approval_id: str,
        reason: str = "Superseded by newer Approval",
        decided_by: str = "system",
    ) -> "ApprovalDecision":
        """Create a SUPERSEDED decision."""
        return cls(
            state=ApprovalDecisionState.SUPERSEDED,
            decision_reason=reason,
            approval_id=approval_id,
            decided_at=time.time(),
            decided_by=decided_by,
            metadata=None,
        )

    # ── Query methods ────────────────────────────

    def is_approved(self) -> bool:
        """Check whether the operation may proceed."""
        return self.state == ApprovalDecisionState.APPROVED

    def is_rejected(self) -> bool:
        return self.state == ApprovalDecisionState.REJECTED

    def is_expired(self) -> bool:
        return self.state == ApprovalDecisionState.EXPIRED

    def is_cancelled(self) -> bool:
        return self.state == ApprovalDecisionState.CANCELLED

    def is_superseded(self) -> bool:
        return self.state == ApprovalDecisionState.SUPERSEDED

    def permits_execution(self) -> bool:
        """Only APPROVED permits execution."""
        return self.is_approved()

    def validate(self) -> bool:
        """Validate decision integrity.

        A valid decision has a non-empty reason (explainable — ADR-001)
        and a recognized state.
        """
        return bool(
            self.decision_reason.strip()
            and self.approval_id.strip()
            and self.decided_by.strip()
        )

    def __repr__(self) -> str:
        return (
            f"ApprovalDecision("
            f"state={self.state.value}, "
            f"reason='{self.decision_reason[:30]}', "
            f"id='{self.approval_id}')"
        )
