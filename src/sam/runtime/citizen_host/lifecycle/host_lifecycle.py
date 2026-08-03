"""Citizen Host lifecycle state machine.

Manages the lifecycle of the Citizen Host unit:
UNINITIALIZED → INITIALIZING → RUNNING ↔ DEGRADED → STOPPING → STOPPED

Authority: R4-001 §3.1 | R5-001 §2.1 | R5-001 C2
"""

from enum import Enum, auto
from typing import Dict, Set


class HostLifecycleState(Enum):
    """Lifecycle states of the Citizen Host.

    Transitions:
        UNINITIALIZED → INITIALIZING (startup)
        INITIALIZING  → RUNNING      (ready)
        RUNNING       → DEGRADED     (partial failure)
        DEGRADED      → RUNNING      (recovery)
        RUNNING       → STOPPING     (shutdown request)
        DEGRADED      → STOPPING     (shutdown request)
        STOPPING      → STOPPED      (terminal)

    Authority: R5-001 C2
    """

    UNINITIALIZED = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    DEGRADED = auto()
    STOPPING = auto()
    STOPPED = auto()


class HostLifecycle:
    """Manages lifecycle state transitions for Citizen Host.

    Only transitions through allowed paths. Any disallowed transition
    raises ValueError.

    Invariants:
        - State cannot jump from UNINITIALIZED to RUNNING directly.
        - STOPPED is terminal — no further transitions.
        - DEGRADED is reversible (can return to RUNNING).
    """

    # ── Allowed transitions ───────────────────────────────────────

    _ALLOWED_TRANSITIONS: Dict[HostLifecycleState, Set[HostLifecycleState]] = {
        HostLifecycleState.UNINITIALIZED: {HostLifecycleState.INITIALIZING},
        HostLifecycleState.INITIALIZING: {HostLifecycleState.RUNNING},
        HostLifecycleState.RUNNING: {
            HostLifecycleState.DEGRADED,
            HostLifecycleState.STOPPING,
        },
        HostLifecycleState.DEGRADED: {
            HostLifecycleState.RUNNING,
            HostLifecycleState.STOPPING,
        },
        HostLifecycleState.STOPPING: {HostLifecycleState.STOPPED},
        HostLifecycleState.STOPPED: set(),  # terminal
    }

    def __init__(self) -> None:
        self._state: HostLifecycleState = HostLifecycleState.UNINITIALIZED

    @property
    def state(self) -> HostLifecycleState:
        """Current lifecycle state."""
        return self._state

    def transition_to(self, target: HostLifecycleState) -> None:
        """Attempt a state transition.

        Args:
            target: The desired target state.

        Raises:
            ValueError: If the transition is not in the allowed set.
        """
        allowed = self._ALLOWED_TRANSITIONS.get(self._state, set())
        if target not in allowed:
            raise ValueError(
                f"Disallowed transition: {self._state.name} → "
                f"{target.name}. Allowed: "
                f"{[s.name for s in sorted(allowed, key=lambda s: s.name)]}"
            )
        self._state = target

    def is_operational(self) -> bool:
        """Check if the host can serve requests.

        Returns:
            True if RUNNING or DEGRADED.
        """
        return self._state in (
            HostLifecycleState.RUNNING,
            HostLifecycleState.DEGRADED,
        )

    def is_terminal(self) -> bool:
        """Check if the host has reached a terminal state.

        Returns:
            True if STOPPED.
        """
        return self._state is HostLifecycleState.STOPPED
