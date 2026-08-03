"""Discovery Resolver operational lifecycle.

Manages the operational state of the Discovery Resolver itself
(not the resolution path, which is tracked by ResolutionPathState).

Authority: R5-001 §2.3 | I0-001 §2.3
"""

from enum import Enum, auto


class ResolverLifecycleState(Enum):
    """Operational states of the Discovery Resolver.

    States:
        UNINITIALIZED: Resolver created but not started.
        INITIALIZING: Resolver initializing.
        RUNNING: Resolver operational — ready to resolve.
        STOPPING: Resolver shutting down.
        STOPPED: Resolver stopped — terminal state.
    """

    UNINITIALIZED = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()

    def is_operational(self) -> bool:
        """Check if this state allows resolution.

        Returns:
            True for RUNNING.
        """
        return self == ResolverLifecycleState.RUNNING

    def is_terminal(self) -> bool:
        """Check if this is a terminal state.

        Returns:
            True for STOPPED.
        """
        return self == ResolverLifecycleState.STOPPED


class ResolverLifecycle:
    """Manages the operational lifecycle of the Discovery Resolver.

    Allowed transitions:
        UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED
        STOPPED is terminal — no further transitions.
    """

    _ALLOWED = {
        ResolverLifecycleState.UNINITIALIZED: {
            ResolverLifecycleState.INITIALIZING,
        },
        ResolverLifecycleState.INITIALIZING: {
            ResolverLifecycleState.RUNNING,
        },
        ResolverLifecycleState.RUNNING: {
            ResolverLifecycleState.STOPPING,
        },
        ResolverLifecycleState.STOPPING: {
            ResolverLifecycleState.STOPPED,
        },
        ResolverLifecycleState.STOPPED: set(),
    }

    def __init__(self) -> None:
        self._state: ResolverLifecycleState = ResolverLifecycleState.UNINITIALIZED

    @property
    def state(self) -> ResolverLifecycleState:
        """Current lifecycle state."""
        return self._state

    def transition_to(self, target: ResolverLifecycleState) -> None:
        """Transition to a new state.

        Args:
            target: The desired target state.

        Raises:
            ValueError: If the transition is not allowed.
        """
        if target == self._state:
            return  # No-op

        allowed = self._ALLOWED.get(self._state, set())
        if target not in allowed:
            allowed_names = sorted(s.name for s in allowed)
            raise ValueError(
                f"Invalid transition: {self._state.name} → {target.name}. "
                f"Allowed: {allowed_names}"
            )

        self._state = target

    def is_operational(self) -> bool:
        """Check if resolver is in operational state."""
        return self._state.is_operational()

    def is_terminal(self) -> bool:
        """Check if resolver has terminated."""
        return self._state.is_terminal()
