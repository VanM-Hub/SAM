"""Approval Coordinator Lifecycle.

5 states:
    UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED

Per I0-001 §2.5:
- RUNNING = operational, authorized with restrictions on mechanism
- STOPPED = terminal
- Same-state transition = no-op
"""

from enum import Enum


class CoordinatorLifecycleState(str, Enum):
    """Lifecycle states for the Approval Coordinator unit.

    Follows the standard 5-state lifecycle pattern:
    UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED
    """
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class ApprovalCoordinatorLifecycle:
    """Manages the lifecycle state of the Approval Coordinator."""

    def __init__(self) -> None:
        self._state: CoordinatorLifecycleState = (
            CoordinatorLifecycleState.UNINITIALIZED
        )

    @property
    def state(self) -> CoordinatorLifecycleState:
        """Current lifecycle state."""
        return self._state

    def is_operational(self) -> bool:
        """True if the coordinator is in a state where it can process approvals.

        Per I0-001: RUNNING = operational.
        """
        return self._state == CoordinatorLifecycleState.RUNNING

    def is_terminal(self) -> bool:
        """True if state is terminal (STOPPED)."""
        return self._state == CoordinatorLifecycleState.STOPPED

    def transition(self, new_state: CoordinatorLifecycleState) -> None:
        """Attempt a lifecycle state transition.

        Valid transitions:
            UNINITIALIZED → INITIALIZING
            INITIALIZING   → RUNNING
            RUNNING        → STOPPING
            STOPPING       → STOPPED

        Same-state is a no-op.
        Invalid transitions raise ValueError.
        """
        if new_state == self._state:
            return  # No-op

        # Allowed transitions
        allowed = {
            CoordinatorLifecycleState.UNINITIALIZED: {
                CoordinatorLifecycleState.INITIALIZING,
            },
            CoordinatorLifecycleState.INITIALIZING: {
                CoordinatorLifecycleState.RUNNING,
            },
            CoordinatorLifecycleState.RUNNING: {
                CoordinatorLifecycleState.STOPPING,
            },
            CoordinatorLifecycleState.STOPPING: {
                CoordinatorLifecycleState.STOPPED,
            },
        }

        valid_targets = allowed.get(self._state, set())
        if new_state not in valid_targets:
            raise ValueError(
                f"Invalid lifecycle transition: "
                f"{self._state.value} → {new_state.value}"
            )

        self._state = new_state

    def __repr__(self) -> str:
        return f"ApprovalCoordinatorLifecycle(state={self._state.value})"
