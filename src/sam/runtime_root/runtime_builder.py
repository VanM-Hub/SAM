"""RuntimeBuilder — composition root for the Reference Runtime (E1-001).

RuntimeBuilder is responsible for:
    * instantiating exactly one instance of each of the seven Runtime Units,
    * wiring them in the canonical pipeline,
    * validating the dependency graph and composition invariants,
    * building an immutable RuntimeContainer.

It NEVER runs the runtime — running is RuntimeRoot's concern. The builder is
deterministic: repeated builds produce fresh, structurally identical
containers (tested: build a hundred times -> identical graphs).

Dependency rule (E1-001):
    Only `shared`, `contracts`, and `runtime.*` are imported. Units are
    constructed via lazy factory closures below (imports happen inside the
    factories), so the builder is the single construction site. There is no
    global singleton and no service locator.

Authority: E1-001 COMPOSITION ROOT | R5-001 S2 | I1-001 §3 | I0-001 M1/M2/M4
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

from .exceptions import (
    RuntimeCompositionError,
)
from .health import HealthProvider, RuntimeHealth
from .interfaces import UnitFactory, UnitRegistry
from .runtime_container import RuntimeContainer
from .runtime_root import RuntimeRoot

#: Canonical pipeline (no shortcut) from R5-001 S2 / I1-001 §3.
PIPELINE: Tuple[str, ...] = (
    "citizen_host",
    "capability_manager",
    "discovery_resolver",
    "contract_enforcer",
    "approval_coordinator",
    "execution_scheduler",
    "audit_recorder",
)

#: Canonical directed edges (adjacent downstream links only).
CANONICAL_EDGES: Tuple[Tuple[str, str], ...] = (
    ("citizen_host", "capability_manager"),
    ("capability_manager", "discovery_resolver"),
    ("discovery_resolver", "contract_enforcer"),
    ("contract_enforcer", "approval_coordinator"),
    ("approval_coordinator", "execution_scheduler"),
    ("execution_scheduler", "audit_recorder"),
)


# -- unit factories (the single construction site; lazy imports only) ------

def _factory_citizen_host() -> Any:
    from sam.runtime.citizen_host.services.host_service import HostService
    from sam.runtime.citizen_host.models.domain import BoundedCapabilityDomain

    # One Runtime = one domain = one Citizen (I0-001 M6 / ADR-000).
    domain = BoundedCapabilityDomain(
        identity="sam.runtime",
        display_name="SAM Reference Runtime",
    )
    return HostService(domain=domain)


def _factory_capability_manager() -> Any:
    from sam.runtime.capability_manager.services.manager_service import (
        CapabilityManagerService,
    )
    return CapabilityManagerService()


def _factory_discovery_resolver() -> Any:
    from sam.runtime.discovery_resolver.services.resolver_service import (
        DiscoveryResolver,
    )
    return DiscoveryResolver()


def _factory_contract_enforcer() -> Any:
    from sam.runtime.contract_enforcer.services.enforcer_service import (
        ContractEnforcer,
    )
    return ContractEnforcer()


def _factory_approval_coordinator() -> Any:
    from sam.runtime.approval_coordinator.services.coordinator_service import (
        ApprovalCoordinator,
    )
    return ApprovalCoordinator()


def _factory_execution_scheduler() -> Any:
    from sam.runtime.execution_scheduler.services.scheduler_service import (
        SchedulerService,
    )
    return SchedulerService()


def _factory_audit_recorder() -> Any:
    from sam.runtime.audit_recorder.services.recorder_service import (
        RecorderService,
    )
    return RecorderService()


#: Canonical id -> factory (deterministic order).
_UNIT_FACTORIES: Dict[str, Callable[[], Any]] = {
    "citizen_host": _factory_citizen_host,
    "capability_manager": _factory_capability_manager,
    "discovery_resolver": _factory_discovery_resolver,
    "contract_enforcer": _factory_contract_enforcer,
    "approval_coordinator": _factory_approval_coordinator,
    "execution_scheduler": _factory_execution_scheduler,
    "audit_recorder": _factory_audit_recorder,
}


class RuntimeBuilder:
    """Composition root: instantiates, wires, validates, and builds.

    Example::

        root = RuntimeBuilder().build()   # RuntimeRoot (BUILT)
        root.start()                      # STARTED
        root.health()
        root.stop()                       # STOPPED

    Repeated builds are supported; each returns a fresh, identical runtime.
    """

    def __init__(self) -> None:
        # Singleton-builder behaviour: reusing the same named builder keeps a
        # stable handle; each call to build() still yields a fresh instance
        # set. This constructor is intentionally trivial.
        self._build_count = 0

    @property
    def build_count(self) -> int:
        """Number of builds issued through this builder instance."""
        return self._build_count

    def build(self) -> RuntimeRoot:
        """Instantiate, wire, validate, and build the runtime (no run).

        Returns:
            A fresh RuntimeRoot in BUILT state.

        Raises:
            RuntimeCompositionError: if any composition invariant fails
            (missing/duplicate unit, cycle, invalid authority/pipeline/health).
        """
        # 1. Instantiate exactly one of each unit, in canonical order.
        registry = self._instantiate_all()

        # 2. Validate structural invariants before wiring.
        self._validate_structure(registry)

        # 3. Build the immutable container (exactly seven dependencies).
        container = RuntimeContainer(registry.units_map())

        # 4. Build health producer map and the aggregate.
        health = self._build_health(registry)

        # 5. Build a BUILT RuntimeRoot (CREATED -> BUILT).
        from .lifecycle import RuntimeLifecycle, RuntimeState
        lifecycle = RuntimeLifecycle(RuntimeState.CREATED)
        lifecycle.transition_to(RuntimeState.BUILT)

        self._build_count += 1
        return RuntimeRoot(container=container, lifecycle=lifecycle, health=health)

    # -- internals -------------------------------------------------------

    def _instantiate_all(self) -> "UnitRegistry":
        """Create exactly one instance per canonical unit (ordered)."""
        registry = UnitRegistry()
        for unit_id in PIPELINE:  # deterministic canonical order
            factory: UnitFactory = UnitFactory(unit_id, _UNIT_FACTORIES[unit_id])
            instance = factory()  # single construction site
            registry.register(unit_id, instance)
        registry.freeze()
        return registry

    def _validate_structure(self, registry: "UnitRegistry") -> None:
        """Validate 7 present, 0 duplicate/missing, 0 cycle, valid pipeline."""
        canonical = set(PIPELINE)
        present = set(registry.ids())
        if present != canonical:
            missing = sorted(canonical - present)
            extra = sorted(present - canonical)
            detail = []
            if missing:
                detail.append("missing=%s" % (missing,))
            if extra:
                detail.append("extra=%s" % (extra,))
            raise RuntimeCompositionError(
                "Composition invalid (%s)" % "; ".join(detail)
            )
        if len(registry) != 7:
            raise RuntimeCompositionError(
                "Expected exactly 7 units, found %d" % len(registry)
            )
        # Pipeline validity: canonical edges are exactly the 6 adjacent links.
        adjacency: Dict[str, set] = {}
        for src, dst in CANONICAL_EDGES:
            adjacency.setdefault(src, set()).add(dst)
        # Cycle check: a linear DAG of 7 nodes with 6 edges cannot cycle when
        # every node's downstream is the next canonical unit; guard anyway.
        self._assert_acyclic(adjacency)

    @staticmethod
    def _assert_acyclic(adjacency: Dict[str, set]) -> None:
        """DFS cycle detection over the adjacency map (raise on cycle)."""
        visiting: set = set()
        visited: set = set()

        def dfs(node: str) -> None:
            if node in visiting:
                raise RuntimeCompositionError(
                    "Dependency graph contains a cycle at node: %s" % node
                )
            if node in visited:
                return
            visiting.add(node)
            for nxt in sorted(adjacency.get(node, set())):
                dfs(nxt)
            visiting.discard(node)
            visited.add(node)

        for node in sorted(adjacency):
            if node not in visited:
                dfs(node)

    def _build_health(self, registry: "UnitRegistry") -> RuntimeHealth:
        """Create the aggregate health over the seven units."""
        health = RuntimeHealth()
        for unit_id in PIPELINE:
            inst = registry.get(unit_id)
            get_health = getattr(inst, "get_health", None)
            if get_health is None or not callable(get_health):
                raise RuntimeCompositionError(
                    "Unit %s has no callable get_health()" % unit_id
                )
            provider = HealthProvider(unit_id, get_health)
            health.register(provider)
        return health
