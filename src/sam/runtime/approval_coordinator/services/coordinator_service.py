"""Approval Coordinator — orchestrator and gate of authorization.

Implements the 5-method public API:
- create_approval()
- evaluate()
- transition()
- get()
- get_health()

Per ADR-001 Accountable Decision Framework:
- Deterministic output shape (6 fixed states)
- Explainable (decision_reason always present)
- Auditable (decided_at, decided_by, metadata)
- Mechanism-open (DecisionPolicy pluggable callable)
- Binding (decision cannot be changed)
- Gate: no execution bypass
"""

import uuid
import time
from typing import Dict, Any, Optional

from src.sam.runtime.approval_coordinator.models.approval_identity import (
    ApprovalIdentity,
)
from src.sam.runtime.approval_coordinator.models.approval_request import (
    ApprovalRequest,
)
from src.sam.runtime.approval_coordinator.models.approval_decision import (
    ApprovalDecision,
    ApprovalDecisionState,
)
from src.sam.runtime.approval_coordinator.state.approval_state import (
    ApprovalState,
    ApprovalLifecycleState,
)
from src.sam.runtime.approval_coordinator.lifecycle.coordinator_lifecycle import (
    ApprovalCoordinatorLifecycle,
    CoordinatorLifecycleState,
)
from src.sam.runtime.approval_coordinator.validation.request_validator import (
    RequestValidator,
)
from src.sam.runtime.approval_coordinator.validation.decision_validator import (
    DecisionValidator,
)
from src.sam.runtime.approval_coordinator.services.health_service import (
    HealthService,
)
from src.sam.runtime.approval_coordinator.interfaces.coordinator_interface import (
    DecisionPolicy,
)
from src.sam.runtime.approval_coordinator.exceptions.approval_errors import (
    ApprovalError,
    InvalidRequestError,
    ExpiredRequestError,
    ApprovalNotFoundError,
    InvalidTransitionError,
    CoordinatorNotOperationalError,
)


class ApprovalCoordinator:
    """Authorization gate — produces binding Approval decisions.

    Public API (5 methods):
        create_approval(request) → ApprovalIdentity
        evaluate(approval_id, policy) → ApprovalDecision
        transition(approval_id, new_state) → None
        get(approval_id) → ApprovalState
        get_health() → Dict[str, Any]

    Internal:
        _approvals: Dict[str, ApprovalState]
    """

    def __init__(self) -> None:
        self._lifecycle = ApprovalCoordinatorLifecycle()
        self._approvals: Dict[str, ApprovalState] = {}

    # ── Lifecycle management ─────────────────────

    def initialize(self) -> None:
        """Initialize the coordinator."""
        self._lifecycle.transition(
            CoordinatorLifecycleState.INITIALIZING
        )
        self._lifecycle.transition(
            CoordinatorLifecycleState.RUNNING
        )

    def shutdown(self) -> None:
        """Graceful shutdown."""
        self._lifecycle.transition(
            CoordinatorLifecycleState.STOPPING
        )
        self._lifecycle.transition(
            CoordinatorLifecycleState.STOPPED
        )

    def _require_operational(self) -> None:
        """Ensure coordinator is in operational state."""
        if not self._lifecycle.is_operational():
            raise CoordinatorNotOperationalError(
                f"Approval Coordinator is not operational "
                f"(state={self._lifecycle.state.value})"
            )

    # ── Public API ───────────────────────────────

    def create_approval(self, request: ApprovalRequest) -> ApprovalIdentity:
        """Create a new Approval from a request.

        Validates the request, creates an ApprovalIdentity and ApprovalState.
        The approval starts in CREATED state.

        Args:
            request: The ApprovalRequest to process.

        Returns:
            ApprovalIdentity for the created approval.

        Raises:
            CoordinatorNotOperationalError: if not in operational state.
            InvalidRequestError: if request is malformed.
            ExpiredRequestError: if request has expired.
        """
        self._require_operational()

        # Validate the request
        RequestValidator.validate(request)

        # Generate a unique approval ID
        approval_id = str(uuid.uuid4())

        # Create identity
        identity = ApprovalIdentity(
            approval_id=approval_id,
            decision_context=request.decision_context,
            contract_reference=request.contract_reference,
            capability_reference=request.capability_reference,
            citizen_reference=request.citizen_reference,
        )

        # Create and store state
        approval_state = ApprovalState(identity=identity, request=request)
        self._approvals[approval_id] = approval_state

        return identity

    def evaluate(
        self,
        approval_id: str,
        policy: DecisionPolicy,
    ) -> ApprovalDecision:
        """Evaluate an approval using the given DecisionPolicy.

        This is the mechanism-open design per ADR-001:
        the DecisionPolicy callable determines the decision,
        while the framework enforces determinism, explainability,
        and auditability.

        The evaluation transitions the approval state:
        - CREATED → PENDING (before evaluation)
        - PENDING → APPROVED/REJECTED/EXPIRED/CANCELLED (decision)
        - APPROVED → SUPERSEDED (if superseded by newer approval)

        Args:
            approval_id: The approval to evaluate.
            policy: Callable that takes ApprovalRequest → ApprovalDecisionState.

        Returns:
            A binding ApprovalDecision.

        Raises:
            CoordinatorNotOperationalError, ApprovalNotFoundError.
        """
        self._require_operational()

        approval = self._ensure_approval(approval_id)

        # Transition to PENDING if not yet decided
        if approval.state == ApprovalLifecycleState.CREATED:
            approval.transition(ApprovalLifecycleState.PENDING)

        # If already decided (APPROVED/REJECTED), re-evaluation may supersede
        if approval.has_decision():
            if approval.state == ApprovalLifecycleState.APPROVED:
                # A new evaluation supersedes a previous APPROVED
                old_decision = approval.decision
                decision = ApprovalDecision.superseded(
                    approval_id=approval_id,
                    reason=f"Superseded by re-evaluation",
                )
                DecisionValidator.validate(decision)
                approval.set_decision(decision)
                approval.transition(ApprovalLifecycleState.ARCHIVED)

                # Return the old decision it was superseded
                if old_decision is not None:
                    return old_decision

            # For REJECTED/EXPIRED/CANCELLED — return existing decision
            # (binding — cannot undo a rejection)
            if approval.decision is not None:
                return approval.decision

        # Apply the DecisionPolicy
        decision_state = policy(approval.request)
        reason = f"Decision by policy: {decision_state.value}"
        decided_by = "system"

        # Create the binding decision
        decision = ApprovalDecision(
            state=decision_state,
            decision_reason=reason,
            approval_id=approval_id,
            decided_at=time.time(),
            decided_by=decided_by,
        )

        DecisionValidator.validate(decision)
        approval.set_decision(decision)

        # Map decision state to lifecycle state
        lifecycle_map = {
            ApprovalDecisionState.APPROVED: ApprovalLifecycleState.APPROVED,
            ApprovalDecisionState.REJECTED: ApprovalLifecycleState.REJECTED,
            ApprovalDecisionState.EXPIRED: ApprovalLifecycleState.EXPIRED,
            ApprovalDecisionState.CANCELLED: ApprovalLifecycleState.CANCELLED,
        }

        target_lifecycle = lifecycle_map.get(decision_state)
        if target_lifecycle:
            approval.transition(target_lifecycle)

        return decision

    def transition(
        self,
        approval_id: str,
        new_state: str,
    ) -> None:
        """Transition an approval to a new lifecycle state.

        Args:
            approval_id: The approval to transition.
            new_state: Target lifecycle state (string value).

        Raises:
            CoordinatorNotOperationalError, ApprovalNotFoundError,
            InvalidTransitionError.
        """
        self._require_operational()

        approval = self._ensure_approval(approval_id)

        try:
            target = ApprovalLifecycleState(new_state)
        except ValueError:
            raise InvalidTransitionError(
                f"Unknown lifecycle state: '{new_state}'"
            )

        try:
            approval.transition(target)
        except ValueError as e:
            raise InvalidTransitionError(str(e))

    def get(self, approval_id: str) -> ApprovalState:
        """Retrieve an approval by its ID.

        Raises ApprovalNotFoundError if not found.
        """
        return self._ensure_approval(approval_id)

    def get_health(self) -> Dict[str, Any]:
        """Return health status."""
        return HealthService.get_health(self._lifecycle)

    # ── Internal helpers ─────────────────────────

    def _ensure_approval(self, approval_id: str) -> ApprovalState:
        """Get approval state or raise ApprovalNotFoundError."""
        if approval_id not in self._approvals:
            raise ApprovalNotFoundError(
                f"Approval not found: '{approval_id}'"
            )
        return self._approvals[approval_id]

    # ── Internal accessors (for tests) ────────────

    @property
    def lifecycle(self) -> ApprovalCoordinatorLifecycle:
        """Internal: lifecycle state machine."""
        return self._lifecycle

    @property
    def approval_count(self) -> int:
        """Internal: number of tracked approvals."""
        return len(self._approvals)

    def list_approval_ids(self):
        """Internal: list all approval IDs."""
        return list(self._approvals.keys())
