"""RuntimeBuilder — the composition root for the Reference Runtime (E1-001).

RuntimeBuilder is responsible for creating exactly one instance of each
Runtime Unit (CitizenHost, CapabilityManager, DiscoveryResolver,
ContractEnforcer, ApprovalCoordinator, ExecutionScheduler, AuditRecorder),
wiring them in the canonical chain, and producing a RuntimeComposition.

Wiring happens ONLY here. Units never initialise other units; there is no
global singleton, no service locator, and no circular injection.

Authority: E1-001 COMPOSITION ROOT | I0-001 M1/M2/M4
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .composition import RuntimeComposition
from .exceptions import CompositionDefinitionError
from .graph import DependencyGraph
from .health import RuntimeHealth
from .registry import RuntimeRegistry

#: Canonical unit id -> factory callable (no-arg) and health getter name.
#: Factories build exactly one instance of the unit's top-level service.
def _build_citizen_host() -> Any:
    from sam.runtime.citizen_host.services.host_service import HostService
    from sam.runtime.citizen_host.models.domain import BoundedCapabilityDomain

    # One Runtime = one domain = one Citizen (I0-001 M6 / ADR-000).
    domain = BoundedCapabilityDomain(
        identity="sam.runtime",
        display_name="SAM Reference Runtime",
    )
    return HostService(domain=domain)


def _build_capability_manager() -> Any:
    from sam.runtime.capability_manager.services.manager_service import (
        CapabilityManagerService,
    )
    return CapabilityManagerService()


def _build_discovery_resolver() -> Any:
    from sam.runtime.discovery_resolver.services.resolver_service import (
        DiscoveryResolver,
    )
    return DiscoveryResolver()


def _build_contract_enforcer() -> Any:
    from sam.runtime.contract_enforcer.services.enforcer_service import (
        ContractEnforcer,
    )
    return ContractEnforcer()


def _build_approval_coordinator() -> Any:
    from sam.runtime.approval_coordinator.services.coordinator_service import (
        ApprovalCoordinator,
    )
    return ApprovalCoordinator()


def _build_execution_scheduler() -> Any:
    from sam.runtime.execution_scheduler.services.scheduler_service import (
        SchedulerService,
    )
    return SchedulerService()


def _build_audit_recorder() -> Any:
    from sam.runtime.audit_recorder.services.recorder_service import (
        RecorderService,
    )
    return RecorderService()


#: Factory registry in canonical order.
_UNIT_FACTORIES = {
    "citizen_host": _build_citizen_host,
    "capability_manager": _build_capability_manager,
    "discovery_resolver": _build_discovery_resolver,
    "contract_enforcer": _build_contract_enforcer,
    "approval_coordinator": _build_approval_coordinator,
    "execution_scheduler": _build_execution_scheduler,
    "audit_recorder": _build_audit_recorder,
}


class RuntimeBuilder:
    """Composition root: builds a fully wired RuntimeComposition.

    Example::

        builder = RuntimeBuilder()
        runtime = builder.build()       # RuntimeComposition (CREATED)
        runtime.start()                 # RUNNING
        runtime.stop()                  # STOPPED

    Repeated build is supported: each call returns a fresh, identical
    composition (deterministic graph, new instances).
    """

    def build(self) -> RuntimeComposition:
        """Create exactly one instance per unit and wire them.

        Returns:
            A fresh RuntimeComposition in CREATED state.
        """
        registry = RuntimeRegistry()
        health = RuntimeHealth()

        for unit_id in _UNIT_FACTORIES:  # canonical order
            instance = _UNIT_FACTORIES[unit_id]()
            registry.register(unit_id, instance)
            health.register(unit_id, instance.get_health)

        registry.freeze()  # immutable after build
        graph = DependencyGraph.canonical()
        registry.validate_canonical()
        return RuntimeComposition(registry=registry, graph=graph, health=health)
