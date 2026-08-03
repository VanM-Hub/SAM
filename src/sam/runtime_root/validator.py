"""Composition validator for the Reference Runtime composition (E1-001).

CompositionValidator checks the invariants of a built runtime:

- all canonical units present (exactly one instance each)
- dependency graph acyclic and architecture-valid
- runtime lifecycle in a valid state
- aggregate health valid (not unexpected for the lifecycle)

Authority: E1-001 | I0-001 M1/M2/M4 | R5-001
"""

from __future__ import annotations

from typing import Any, List, Optional

from .exceptions import CompositionValidationError
from .graph import UNIT_CHAIN, DependencyGraph
from .health import HealthStatus
from .lifecycle import RuntimeLifecycle, RuntimeState
from .registry import RuntimeRegistry


class CompositionValidator:
    """Validate a composed runtime's structural and lifecycle integrity."""

    def __init__(
        self,
        registry: RuntimeRegistry,
        lifecycle: Optional[RuntimeLifecycle] = None,
        health=None,
    ) -> None:
        self._registry = registry
        self._lifecycle = lifecycle
        self._health = health

    # -- public checks ---------------------------------------------------

    def validate(self) -> bool:
        """Run all checks; raise CompositionValidationError on first fault."""
        self.check_completeness()
        self.check_dependency(DependencyGraph.canonical())
        self.check_lifecycle()
        if self._health is not None:
            self.check_health(self._health)
        return True

    def check_completeness(self) -> bool:
        """Every canonical unit present with exactly one instance."""
        for unit in UNIT_CHAIN:
            if not self._registry.contains(unit):
                raise CompositionValidationError(
                    "Missing required unit: %s" % unit
                )
        if len(self._registry) != len(UNIT_CHAIN):
            raise CompositionValidationError(
                "Expected %d units, found %d"
                % (len(UNIT_CHAIN), len(self._registry))
            )
        return True

    def check_dependency(self, graph: DependencyGraph) -> bool:
        """Graph must be acyclic and match the canonical chain."""
        if not graph.is_acyclic():
            raise CompositionValidationError(
                "Dependency graph must be acyclic"
            )
        canonical = DependencyGraph.canonical()
        if not graph.equals(canonical):
            raise CompositionValidationError(
                "Dependency graph does not match canonical architecture chain"
            )
        return True

    def check_lifecycle(self) -> bool:
        """Lifecycle must be present and non-terminal."""
        if self._lifecycle is None:
            raise CompositionValidationError(
                "Runtime lifecycle is not available for validation"
            )
        if self._lifecycle.is_stopped():
            raise CompositionValidationError(
                "Runtime cannot be validated in a stopped/failed state: %s"
                % self._lifecycle.state.value
            )
        return True

    def check_health(self, health) -> bool:
        """Aggregate health aggregation must be sound.

        Every registered unit must report a recognisable health status; the
        aggregate must be a known HealthStatus. This checks health-report
        integrity, not a forced AVAILABLE (unit availability is driven by the
        unit internals, which are out of scope for composition).
        """
        per_unit = health.all_health()
        if len(per_unit) == 0:
            raise CompositionValidationError(
                "Runtime health has no unit health producers"
            )
        status = health.aggregate()
        if not isinstance(status, HealthStatus):
            raise CompositionValidationError(
                "Aggregate health is not a known status: %r" % (status,)
            )
        return True
