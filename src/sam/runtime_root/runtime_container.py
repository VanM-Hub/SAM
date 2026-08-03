"""RuntimeContainer — immutable holder of the seven Runtime Units (E1-001).

RuntimeContainer is the immutable result produced by RuntimeBuilder. It holds
exactly seven dependencies:

    CitizenHost, CapabilityManager, DiscoveryResolver, ContractEnforcer,
    ApprovalCoordinator, ExecutionScheduler, AuditRecorder

There must be no eighth dependency. The container is purely structural and
immutable once built; lifecycle and health are owned by RuntimeRoot.

Dependency rule (E1-001):
    No global singleton, no service locator. The builder constructs every
    unit; the container only stores and exposes the wired instances.

Authority: E1-001 COMPOSITION ROOT | R5-001 S2 | I1-001 §3 | I0-001 M1
"""

from __future__ import annotations

from typing import Any, Dict

from .exceptions import CompositionDefinitionError


class RuntimeContainer:
    """Immutable aggregate of the seven wired Runtime Units.

    Exposes exactly seven dependencies as read-only properties:
    citizen_host, capability_manager, discovery_resolver, contract_enforcer,
    approval_coordinator, execution_scheduler, audit_recorder.
    """

    #: Canonical dimension — exactly seven dependencies. Adding an eighth
    #: entry here violates the Reference Runtime architecture (R5-001 S1/MC1).
    _DEPENDENCIES = (
        "citizen_host",
        "capability_manager",
        "discovery_resolver",
        "contract_enforcer",
        "approval_coordinator",
        "execution_scheduler",
        "audit_recorder",
    )

    __slots__ = tuple("_%s" % d for d in _DEPENDENCIES) + ("_frozen",)

    def __init__(self, units: Dict[str, Any]) -> None:
        """Build the container from a unit-id -> instance map.

        Args:
            units: exactly the seven canonical unit instances.

        Raises:
            CompositionDefinitionError: if the map is missing a canonical
            unit or contains an extra (eighth+) unit.
        """
        expected = set(self._DEPENDENCIES)
        provided = set(units.keys())
        missing = sorted(expected - provided)
        extra = sorted(provided - expected)
        if missing or extra:
            detail = []
            if missing:
                detail.append("missing=%s" % (missing,))
            if extra:
                detail.append("extra=%s" % (extra,))
            raise CompositionDefinitionError(
                "RuntimeContainer must hold exactly seven units (%s)"
                % "; ".join(detail)
            )
        for dep in self._DEPENDENCIES:
            object.__setattr__(self, "_%s" % dep, units[dep])
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name: str, value: Any) -> None:
        # Immutable after construction.
        if getattr(self, "_frozen", False):
            raise AttributeError(
                "RuntimeContainer is immutable (cannot set %r)" % name
            )
        object.__setattr__(self, name, value)

    # -- seven dependencies (read-only) ----------------------------------

    @property
    def citizen_host(self) -> Any:
        return self._citizen_host

    @property
    def capability_manager(self) -> Any:
        return self._capability_manager

    @property
    def discovery_resolver(self) -> Any:
        return self._discovery_resolver

    @property
    def contract_enforcer(self) -> Any:
        return self._contract_enforcer

    @property
    def approval_coordinator(self) -> Any:
        return self._approval_coordinator

    @property
    def execution_scheduler(self) -> Any:
        return self._execution_scheduler

    @property
    def audit_recorder(self) -> Any:
        return self._audit_recorder

    # -- public accessors ------------------------------------------------

    def units(self) -> Dict[str, Any]:
        """Return {unit_id: instance} for the seven units (canonical order)."""
        return {dep: getattr(self, dep) for dep in self._DEPENDENCIES}

    @property
    def dependency_ids(self) -> tuple:
        """The seven canonical dependency ids (identical every time)."""
        return self._DEPENDENCIES

    def __len__(self) -> int:
        """Exactly seven dependencies."""
        return len(self._DEPENDENCIES)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "RuntimeContainer(units=%d)" % len(self)
