"""RuntimeContainer — public facade for the composed Reference Runtime (E1-001).

RuntimeContainer wraps a RuntimeComposition and exposes the E1-001 public API:

    RuntimeContainer.start()      # deterministic startup
    RuntimeContainer.stop()       # deterministic shutdown (reverse order)
    RuntimeContainer.health()     # aggregate health
    RuntimeContainer.validate()   # full composition validation

It also provides direct access to each composed unit and the immutable unit
registry.

Authority: E1-001 PUBLIC API | I0-001
"""

from __future__ import annotations

from typing import Any, Dict

from .composition import RuntimeComposition
from .exceptions import CompositionValidationError
from .graph import UNIT_CHAIN
from .health import HealthStatus
from .lifecycle import RuntimeState
from .validator import CompositionValidator


class RuntimeContainer:
    """Public runtime handle over a wired RuntimeComposition."""

    def __init__(self, composition: RuntimeComposition) -> None:
        self._composition = composition

    # -- public API -------------------------------------------------------

    def start(self) -> "RuntimeContainer":
        """Start the runtime (CREATED -> ... -> RUNNING)."""
        self._composition.start()
        return self

    def stop(self) -> "RuntimeContainer":
        """Stop the runtime (RUNNING -> ... -> STOPPED)."""
        self._composition.stop()
        return self

    def health(self) -> HealthStatus:
        """Aggregate runtime health."""
        return self._composition.health.aggregate()

    def validate(self) -> bool:
        """Validate composition; raises CompositionValidationError on fault."""
        return self._composition.validate()

    # -- unit access -----------------------------------------------------

    @property
    def composition(self) -> RuntimeComposition:
        """The underlying composition."""
        return self._composition

    @property
    def lifecycle(self):
        """Runtime lifecycle (read-only accessor)."""
        return self._composition.lifecycle

    @property
    def graph(self):
        """Validated dependency graph."""
        return self._composition.graph

    @property
    def registry(self):
        """Immutable unit registry."""
        return self._composition.registry

    # Canonical unit accessors (E1-001 container role).
    @property
    def citizen_host(self) -> Any:
        return self._composition.unit("citizen_host")

    @property
    def capability_manager(self) -> Any:
        return self._composition.unit("capability_manager")

    @property
    def discovery_resolver(self) -> Any:
        return self._composition.unit("discovery_resolver")

    @property
    def contract_enforcer(self) -> Any:
        return self._composition.unit("contract_enforcer")

    @property
    def approval_coordinator(self) -> Any:
        return self._composition.unit("approval_coordinator")

    @property
    def execution_scheduler(self) -> Any:
        return self._composition.unit("execution_scheduler")

    @property
    def audit_recorder(self) -> Any:
        return self._composition.unit("audit_recorder")

    def units(self) -> Dict[str, Any]:
        """Return {unit_id: instance} in canonical order."""
        return self._composition.units()
