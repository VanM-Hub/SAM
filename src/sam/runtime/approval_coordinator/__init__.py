"""Approval Coordinator — Unit 5 Reference Implementation.

Authorization gate producing binding Approval decisions before execution.
Implements Accountable Decision Framework per ADR-001.

Public API:
    create_approval() — Create a new Approval from a request
    evaluate()        — Evaluate using pluggable DecisionPolicy
    transition()      — Transition approval lifecycle state
    get()             — Retrieve approval by ID
    get_health()      — Health status of the coordinator

Depends on: shared, contracts.
Must NOT depend on: citizen_host, capability_manager, discovery_resolver,
                     contract_enforcer, execution_scheduler, audit_recorder,
                     registry, internal.
"""

from src.sam.runtime.approval_coordinator.services.coordinator_service import (
    ApprovalCoordinator,
)
from src.sam.runtime.approval_coordinator.models.approval_request import (
    ApprovalRequest,
)
from src.sam.runtime.approval_coordinator.models.approval_identity import (
    ApprovalIdentity,
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
from src.sam.runtime.approval_coordinator.interfaces.coordinator_interface import (
    DecisionPolicy,
)

__all__ = [
    "ApprovalCoordinator",
    "ApprovalRequest",
    "ApprovalIdentity",
    "ApprovalDecision",
    "ApprovalDecisionState",
    "ApprovalState",
    "ApprovalLifecycleState",
    "ApprovalCoordinatorLifecycle",
    "CoordinatorLifecycleState",
    "DecisionPolicy",
]
