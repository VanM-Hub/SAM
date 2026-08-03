"""Interfaces for the Reference Runtime composition layer (E1-001).

This module defines the minimal abstractions the composition root relies on.
It keeps the Composition Root decoupled from the concrete unit internals: the
builder depends on these contracts, never on lateral unit imports.

Dependency rule (E1-001):
    runtime_root may import only `shared`, `contracts`, and `runtime.*`.
    Runtime units must never instantiate each other; there is no global
    singleton and no service locator. The builder creates everything.

Authority: E1-001 COMPOSITION ROOT | R5-001 S2 | I1-001 §3 | I0-001 M1/M2
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from .exceptions import CompositionDefinitionError


class UnitFactory:
    """Callable contract for constructing exactly one unit instance.

    A UnitFactory is a no-argument callable returning a fresh, fully
    constructed unit service instance. Factories live only in the builder;
    units never construct other units.
    """

    __slots__ = ("_fn", "_unit_id")

    def __init__(self, unit_id: str, fn: Callable[[], Any]) -> None:
        self._unit_id = unit_id
        self._fn = fn

    @property
    def unit_id(self) -> str:
        """The canonical unit identity this factory produces."""
        return self._unit_id

    def __call__(self) -> Any:
        """Build a fresh unit instance."""
        return self._fn()

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "UnitFactory(%s)" % self._unit_id


class HealthProvider:
    """Callable contract returning a unit's health report.

    Unit health reports are heterogeneous (string status or dict with
    status/lifecycle keys). The composition layer normalises them; it never
    forces a status value that a unit did not report.
    """

    __slots__ = ("_unit_id", "_fn")

    def __init__(self, unit_id: str, fn: Callable[[], object]) -> None:
        self._unit_id = unit_id
        self._fn = fn

    @property
    def unit_id(self) -> str:
        return self._unit_id

    def __call__(self) -> object:
        return self._fn()

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "HealthProvider(%s)" % self._unit_id


class UnitRegistry:
    """Immutable-after-build registry of exactly one instance per unit.

    Registration is exactly-once guarded; after freeze() the registry can no
    longer be mutated. This is a composition concern, distinct from the
    (empty by design, I1-001) `sam.runtime.registry` infrastructure package.
    """

    def __init__(self) -> None:
        self._units: Dict[str, Any] = {}
        self._frozen = False

    def register(self, unit_id: str, instance: Any) -> None:
        """Register a single unit instance (exactly once per id).

        Raises:
            CompositionDefinitionError: if the id is already registered, the
            registry is frozen, or the instance is None.
        """
        if self._frozen:
            raise CompositionDefinitionError(
                "Runtime registry is frozen; cannot register %s" % unit_id
            )
        if unit_id in self._units:
            raise CompositionDefinitionError(
                "Unit already registered (exactly one instance): %s" % unit_id
            )
        if instance is None:
            raise CompositionDefinitionError(
                "Cannot register None instance for unit: %s" % unit_id
            )
        self._units[unit_id] = instance

    def freeze(self) -> None:
        """Lock the registry against further mutation."""
        self._frozen = True

    def get(self, unit_id: str) -> Any:
        """Return the instance for a unit id (raises if missing)."""
        try:
            return self._units[unit_id]
        except KeyError:
            raise CompositionDefinitionError(
                "No unit registered for id: %s" % unit_id
            )

    def contains(self, unit_id: str) -> bool:
        """True iff a unit id is registered."""
        return unit_id in self._units

    def ids(self) -> list:
        """All registered unit ids (stable order)."""
        return sorted(self._units.keys())

    def items(self) -> list:
        """All unit instances in id order (for iteration)."""
        return [self._units[uid] for uid in self.ids()]

    def units_map(self) -> Dict[str, Any]:
        """Return a plain {unit_id: instance} map (canonical pipeline order)."""
        from .runtime_builder import PIPELINE

        # PIPELINE order is authoritative; fall back to sorted ids if the
        # registry somehow holds a non-canonical id.
        ordered = {uid: self._units[uid] for uid in PIPELINE if uid in self._units}
        return ordered

    def __len__(self) -> int:
        return len(self._units)
