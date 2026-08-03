"""RuntimeComposition — the wired assembly of the 7 runtime units (E1-001).

RuntimeComposition is the immutable-after-build model produced by
RuntimeBuilder. It holds exactly one instance of each canonical unit, the
validated DependencyGraph, the RuntimeRegistry, the RuntimeHealth
aggregator, and the RuntimeLifecycle state machine.

The composition mediates the linear chain (CitizenHost -> ... -> AuditRecorder)
by holding ordered references and exposing them; units never initialise or
import other units (no lateral wiring at unit level, per E1-001 wiring rule).

Authority: E1-001 | R5-001 S2 | I0-001 M1/M2
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .exceptions import CompositionDefinitionError
from .graph import UNIT_CHAIN, DependencyGraph
from .health import HealthStatus, RuntimeHealth
from .lifecycle import RuntimeLifecycle, RuntimeState
from .registry import RuntimeRegistry
from .validator import CompositionValidator


class RuntimeComposition:
    """A fully wired reference runtime.

    Attributes:
        registry: RuntimeRegistry with exactly one instance per unit.
        graph: validated DependencyGraph.
        health: RuntimeHealth aggregator.
        lifecycle: RuntimeLifecycle state machine.
        order: canonical unit order (tuple).
    """

    def __init__(
        self,
        registry: RuntimeRegistry,
        graph: DependencyGraph,
        health: RuntimeHealth,
    ) -> None:
        self._registry = registry
        self._graph = graph
        self._health = health
        self._lifecycle = RuntimeLifecycle(RuntimeState.CREATED)
        self._validator = CompositionValidator(registry, self._lifecycle, health)

    # -- accessors -------------------------------------------------------

    @property
    def registry(self) -> RuntimeRegistry:
        return self._registry

    @property
    def graph(self) -> DependencyGraph:
        return self._graph

    @property
    def health(self) -> RuntimeHealth:
        return self._health

    @property
    def lifecycle(self) -> RuntimeLifecycle:
        return self._lifecycle

    @property
    def order(self) -> Tuple[str, ...]:
        return UNIT_CHAIN

    def unit(self, unit_id: str) -> Any:
        """Return the instance for a canonical unit id."""
        return self._registry.get(unit_id)

    def units(self) -> Dict[str, Any]:
        """Return {unit_id: instance} in canonical order."""
        return {uid: self._registry.get(uid) for uid in UNIT_CHAIN}

    def validate(self) -> bool:
        """Run the full composition validation."""
        lifecycle = self._lifecycle
        if lifecycle.state == RuntimeState.CREATED:
            # CREATED is valid for a built-but-not-started runtime.
            ok = self._validator.check_completeness()
            ok = self._validator.check_dependency(self._graph) and ok
            return bool(ok)
        return self._validator.validate()

    # -- lifecycle -------------------------------------------------------

    def start(self) -> "RuntimeComposition":
        """Deterministic startup: CREATED -> COMPOSED -> STARTING -> RUNNING.

        The composition root drives each unit's public initialize() where it
        exists; units that expose no initializer start internally. This is
        composition-level orchestration only -- units never initialise other
        units (E1-001 wiring rule).
        """
        self._lifecycle.transition_to(RuntimeState.COMPOSED)
        try:
            self._lifecycle.transition_to(RuntimeState.STARTING)
            self._initialize_units()
            self._lifecycle.transition_to(RuntimeState.RUNNING)
        except Exception:
            self._lifecycle.transition_to_if(RuntimeState.FAILED)
            raise
        return self

    def stop(self) -> "RuntimeComposition":
        """Deterministic shutdown in reverse order: RUNNING -> STOPPING -> STOPPED."""
        self._lifecycle.transition_to(RuntimeState.STOPPING)
        self._lifecycle.transition_to(RuntimeState.STOPPED)
        return self

    # -- helpers ---------------------------------------------------------

    def _initialize_units(self) -> None:
        """Drive each unit's public initialize() method, when present.

        Units that expose no initializer are expected to self-initialise.
        Iteration is in canonical chain order for determinism.
        """
        for unit_id in self.order:
            inst = self._registry.get(unit_id)
            init = getattr(inst, "initialize", None)
            if callable(init):
                init()
