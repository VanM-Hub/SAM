"""Approval Coordinator Interface — Public API Protocol.

Defines the 5 public methods:
- create_approval()
- evaluate()
- transition()
- get()
- get_health()
"""

from typing import Protocol, Dict, Callable, Any

from src.sam.runtime.approval_coordinator.models.approval_request import ApprovalRequest
from src.sam.runtime.approval_coordinator.models.approval_identity import ApprovalIdentity
from src.sam.runtime.approval_coordinator.models.approval_decision import (
    ApprovalDecision,
    ApprovalDecisionState,
)

# DecisionPolicy is a callable that takes an ApprovalRequest and returns a
# decision. This is the mechanism-open design mandated by ADR-001:
# the framework does not prescribe HOW to decide, only WHAT must be produced.
DecisionPolicy = Callable[[ApprovalRequest], ApprovalDecisionState]


class ApprovalCoordinatorInterface(Protocol):
    """Public API for the Approval Coordinator.

    Per ADR-001 Accountable Decision Framework:
    - Deterministic output shape (6 fixed states)
    - Explainable (decision_reason)
    - Auditable (metadata + traceability)
    - Mechanism-open (DecisionPolicy pluggable)
    """

    def create_approval(self, request: ApprovalRequest) -> ApprovalIdentity:
        """Create a new Approval from a request.

        Returns an ApprovalIdentity representing the created approval.
        The approval starts in a non-decided state.
        """
        ...

    def evaluate(
        self,
        approval_id: str,
        policy: DecisionPolicy,
    ) -> ApprovalDecision:
        """Evaluate an approval using the given DecisionPolicy.

        The policy is the pluggable decision mechanism per ADR-001.
        Returns a binding ApprovalDecision.
        """
        ...

    def transition(self, approval_id: str, new_state: str) -> None:
        """Transition an approval to a new lifecycle state.

        Raises InvalidTransitionError if the transition is not legal.
        """
        ...

    def get(self, approval_id: str) -> Any:
        """Retrieve an approval by its ID.

        Raises ApprovalNotFoundError if the approval does not exist.
        """
        ...

    def get_health(self) -> Dict[str, Any]:
        """Return the current health status of the coordinator."""
        ...
