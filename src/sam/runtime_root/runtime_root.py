"""RuntimeRoot — public API for the composed Reference Runtime (E1-001).

RuntimeRoot is the sole public handle produced by RuntimeBuilder. It wraps the
immutable RuntimeContainer and drives the deterministic lifecycle. Units never
import the root; the root only orchestrates them through the container.

Public API (E1-001):
    RuntimeRoot.build()        -- create/rebuild a fresh runtime (delegates to
                                   RuntimeBuilder; returns a new RuntimeRoot).
    RuntimeRoot.start()        -- deterministic startup.
    RuntimeRoot.stop()         -- deterministic shutdown.
    RuntimeRoot.restart()      -- stop then start again (fresh composition).
    RuntimeRoot.health()       -- aggregate health (Healthy/Degraded/Failed).
    RuntimeRoot.container()    -- immutable seven-unit container.
    RuntimeRoot.is_running()   -- True iff the runtime is STARTED.

Lifecycle (deterministic):
    CREATED -> BUILT -> STARTED -> STOPPED -> DISPOSED

Wiring follows the canonical pipeline with no shortcut:
    CitizenHost -> CapabilityManager -> DiscoveryResolver -> ContractEnforcer
        -> ApprovalCoordinator -> ExecutionScheduler -> AuditRecorder

Dependency rule (E1-001):
    import only `shared`, `contracts`, `runtime.*`. No lateral unit
    instantiation, no global singleton, no service locator — the builder
    creates everything.

Authority: E1-001 COMPOSITION ROOT | R5-001 S2 | I1-001 §3 | I0-001 M1/M2/M32
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .exceptions import RuntimeCompositionError
from .health import HealthStatus, RuntimeHealth
from .lifecycle import RuntimeLifecycle, RuntimeState
from .runtime_container import RuntimeContainer


class RuntimeRoot:
    """Public API over the composed Reference Runtime.

    Attributes:
        container: immutable RuntimeContainer (the seven units).
        lifecycle: RuntimeLifecycle (deterministic state machine).
        health:    RuntimeHealth (aggregate over the seven units).
    """

    def __init__(
        self,
        container: RuntimeContainer,
        lifecycle: RuntimeLifecycle,
        health: RuntimeHealth,
    ) -> None:
        self._container = container
        self._lifecycle = lifecycle
        self._health = health

    # -- construction ----------------------------------------------------

    @classmethod
    def build(cls) -> "RuntimeRoot":
        """Build a fresh, fully wired runtime.

        Aliases RuntimeBuilder().build(); exists so callers can use
        RuntimeRoot.build() directly as the composition entry point.
        """
        from .runtime_builder import RuntimeBuilder

        return RuntimeBuilder().build()

    # -- public API ------------------------------------------------------

    def start(self) -> "RuntimeRoot":
        """Start the runtime deterministically (BUILT -> STARTED).

        Returns:
            self, for chaining.
        """
        self._lifecycle.transition_to(RuntimeState.STARTED)
        self._drive_initialize()
        return self

    def stop(self) -> "RuntimeRoot":
        """Stop the runtime deterministically (STARTED -> STOPPED).

        Returns:
            self, for chaining.
        """
        if self._lifecycle.state == RuntimeState.STARTED:
            self._lifecycle.transition_to(RuntimeState.STOPPED)
        elif self._lifecycle.state == RuntimeState.BUILT:
            self._lifecycle.transition_to(RuntimeState.STOPPED)
        elif self._lifecycle.state in (
            RuntimeState.CREATED,
            RuntimeState.DISPOSED,
        ):
            raise RuntimeCompositionError(
                "Cannot stop runtime in state: %s"
                % self._lifecycle.state.value
            )
        return self

    def restart(self) -> "RuntimeRoot":
        """Stop (if needed) then build and start a fresh runtime.

        Returns a NEW RuntimeRoot in STARTED state via a fresh
        RuntimeBuilder (no mutation of the old one).
        """
        if self._lifecycle.state in (RuntimeState.STARTED, RuntimeState.BUILT):
            self._lifecycle.transition_to(RuntimeState.STOPPED)
        from .runtime_builder import RuntimeBuilder

        fresh = RuntimeBuilder().build()  # CREATED -> BUILT
        fresh._lifecycle.transition_to(RuntimeState.STARTED)  # noqa: SLF001
        fresh._drive_initialize()
        return fresh

    def health(self) -> HealthStatus:
        """Aggregate health of the seven units (Healthy/Degraded/Failed)."""
        return self._health.aggregate()

    def health_summary(self):
        """Return (aggregate, {unit_id: status}) for inspection/audit."""
        return self._health.summary()

    def container(self) -> RuntimeContainer:
        """Return the immutable seven-unit container."""
        return self._container

    def is_running(self) -> bool:
        """True iff the runtime is in the STARTED state."""
        return self._lifecycle.state == RuntimeState.STARTED

    def dispose(self) -> None:
        """Dispose the runtime (STOPPED -> DISPOSED). Terminal state."""
        if self._lifecycle.state not in (
            RuntimeState.STOPPED,
            RuntimeState.BUILT,
        ):
            raise RuntimeCompositionError(
                "Cannot dispose runtime in state: %s"
                % self._lifecycle.state.value
            )
        self._lifecycle.transition_to(RuntimeState.DISPOSED)

    # -- inspection ------------------------------------------------------

    @property
    def lifecycle(self) -> RuntimeLifecycle:
        """The deterministic lifecycle state machine."""
        return self._lifecycle

    def units(self) -> Dict[str, Any]:
        """Return the seven wired unit instances keyed by id."""
        return self._container.units()

    # -- internals -------------------------------------------------------

    def _drive_initialize(self) -> None:
        """Drive each unit's public initialize() in canonical order.

        Units that expose no initializer self-initialise. This is the only
        composition-level orchestration; units never initialise other units
        (E1-001 wiring rule / I1-001 IR4 no lateral wiring).
        """
        for unit_id in ("citizen_host", "capability_manager",
                        "discovery_resolver", "contract_enforcer",
                        "approval_coordinator", "execution_scheduler",
                        "audit_recorder"):
            inst = self._container.units().get(unit_id)
            if inst is None:
                continue
            init = getattr(inst, "initialize", None)
            if callable(init):
                init()
