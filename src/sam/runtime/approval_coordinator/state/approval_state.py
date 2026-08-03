"""Approval State Machine — per-approval lifecycle.

APPROVAL_SPEC lifecycle states:
    CREATED, PENDING, APPROVED, REJECTED, EXPIRED, CANCELLED, ARCHIVED

Legal transitions:
    Created → Pending
    Created → Rejected
    Pending → Approved
    Pending → Rejected
    Pending → Expired
    Pending → Cancelled
    Approved → Expired
    Approved → Archived
    Rejected → Archived
    Expired → Archived
    Cancelled → Archived

ARCHIVED is terminal.
"""

from enum import Enum
from typing import Optional, Dict, Any

from src.sam.runtime.approval_coordinator.models.approval_identity import (
    ApprovalIdentity,
)
from src.sam.runtime.approval_coordinator.models.approval_request import (
    ApprovalRequest,
)
from src.sam.runtime.approval_coordinator.models.approval_decision import (
    ApprovalDecision,
)


class ApprovalLifecycleState(str, Enum):
    """Per-approval lifecycle states per APPROVAL_SPEC.

    Seven states:
    - CREATED: approval identity established
    - PENDING: awaiting decision
    - APPROVED: authorized to proceed
    - REJECTED: authorization denied
    - EXPIRED: no longer valid
    - CANCELLED: withdrawn before decision
    - ARCHIVED: terminal, recorded
    """
    CREATED = "CREATED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


# Legal transitions per APPROVAL_SPEC
_LEGAL_TRANSITIONS: Dict[ApprovalLifecycleState, set] = {
    ApprovalLifecycleState.CREATED: {
        ApprovalLifecycleState.PENDING,
        ApprovalLifecycleState.REJECTED,
    },
    ApprovalLifecycleState.PENDING: {
        ApprovalLifecycleState.APPROVED,
        ApprovalLifecycleState.REJECTED,
        ApprovalLifecycleState.EXPIRED,
        ApprovalLifecycleState.CANCELLED,
    },
    ApprovalLifecycleState.APPROVED: {
        ApprovalLifecycleState.EXPIRED,
        ApprovalLifecycleState.ARCHIVED,
    },
    ApprovalLifecycleState.REJECTED: {
        ApprovalLifecycleState.ARCHIVED,
    },
    ApprovalLifecycleState.EXPIRED: {
        ApprovalLifecycleState.ARCHIVED,
    },
    ApprovalLifecycleState.CANCELLED: {
        ApprovalLifecycleState.ARCHIVED,
    },
}
# ARCHIVED has no outgoing transitions (terminal)


class ApprovalState:
    """Per-approval state container.

    Tracks the lifecycle state, identity, request, and decision
    for a single Approval.
    """

    def __init__(
        self,
        identity: ApprovalIdentity,
        request: ApprovalRequest,
    ) -> None:
        self._identity: ApprovalIdentity = identity
        self._request: ApprovalRequest = request
        self._state: ApprovalLifecycleState = ApprovalLifecycleState.CREATED
        self._decision: Optional[ApprovalDecision] = None

    # ── Properties ───────────────────────────────

    @property
    def state(self) -> ApprovalLifecycleState:
        """Current lifecycle state."""
        return self._state

    @property
    def identity(self) -> ApprovalIdentity:
        """Approval identity."""
        return self._identity

    @property
    def request(self) -> ApprovalRequest:
        """Original Approval Request."""
        return self._request

    @property
    def decision(self) -> Optional[ApprovalDecision]:
        """The decision, if one has been made."""
        return self._decision

    # ── Transition validation & execution ─────────

    def is_valid_transition(self, new_state: ApprovalLifecycleState) -> bool:
        """Check whether transitioning to new_state is legal."""
        allowed = _LEGAL_TRANSITIONS.get(self._state, set())
        return new_state in allowed

    def is_terminal(self) -> bool:
        """True if current state is terminal (ARCHIVED)."""
        return self._state == ApprovalLifecycleState.ARCHIVED

    def transition(self, new_state: ApprovalLifecycleState) -> None:
        """Transition to a new lifecycle state.

        Raises ValueError on illegal transitions.
        Same-state is a no-op.
        """
        if new_state == self._state:
            return  # No-op

        if not self.is_valid_transition(new_state):
            raise ValueError(
                f"Invalid approval transition: "
                f"{self._state.value} → {new_state.value}"
            )

        if self.is_terminal():
            raise ValueError(
                f"Cannot transition from terminal state "
                f"{self._state.value}"
            )

        self._state = new_state

    def set_decision(self, decision: ApprovalDecision) -> None:
        """Record the approval decision.

        The decision is binding — once set, it cannot be changed.
        """
        self._decision = decision

    def has_decision(self) -> bool:
        """Check whether a decision has been recorded."""
        return self._decision is not None

    def to_dict(self) -> Dict[str, Any]:
        """Expose approval state for auditability."""
        result: Dict[str, Any] = {
            "approval_id": self._identity.approval_id,
            "state": self._state.value,
            "decision_context": self._identity.decision_context,
            "capability_reference": self._identity.capability_reference,
            "contract_id": self._identity.contract_reference.contract_id,
            "contract_version": self._identity.contract_reference.version,
            "has_decision": self.has_decision(),
        }
        if self._decision:
            result["decision_state"] = self._decision.state.value
            result["decision_reason"] = self._decision.decision_reason
            result["decided_by"] = self._decision.decided_by
        return result

    def __repr__(self) -> str:
        return (
            f"ApprovalState("
            f"id='{self._identity.approval_id}', "
            f"state={self._state.value})"
        )
