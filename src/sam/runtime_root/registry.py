"""Composition-layer registry of runtime unit instances (E1-001).

RuntimeRegistry holds exactly one instance per composed unit. It is used by
the RuntimeContainer to expose the wired units and by the validator to check
singleton/completeness. Registration is idempotent-guarded: a unit may be
registered only once (exactly one instance per unit).

This is a composition concern, NOT the `sam.runtime.registry` infrastructure
package (registry infrastructure is empty by design per I1-001).

Authority: E1-001 | I0-001 M1 (exactly one instance per unit)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .exceptions import CompositionDefinitionError


class RuntimeRegistry:
    """Immutable-after-build registry of composed unit instances."""

    def __init__(self) -> None:
        self._units: Dict[str, Any] = {}
        self._frozen = False

    def register(self, unit_id: str, instance: Any) -> None:
        """Register a single unit instance (exactly once per id).

        Raises:
            CompositionDefinitionError: if id already registered or frozen.
        """
        if self._frozen:
            raise CompositionDefinitionError(
                "Runtime registry is frozen; cannot register %s" % unit_id
            )
        if unit_id in self._units:
            raise CompositionDefinitionError(
                "Unit already registered (exactly one instance allowed): %s"
                % unit_id
            )
        if instance is None:
            raise CompositionDefinitionError(
                "Cannot register None instance for unit: %s" % unit_id
            )
        self._units[unit_id] = instance

    def freeze(self) -> None:
        """Lock the registry against further mutation (immutable container)."""
        self._frozen = True

    def get(self, unit_id: str) -> Any:
        """Return the instance for a unit id.

        Raises:
            CompositionDefinitionError: if unit id is not registered.
        """
        try:
            return self._units[unit_id]
        except KeyError:
            raise CompositionDefinitionError(
                "No unit registered for id: %s" % unit_id
            )

    def ids(self) -> List[str]:
        """All registered unit ids (stable order)."""
        return sorted(self._units.keys())

    def items(self) -> List[Any]:
        """All unit instances in id order (for iteration)."""
        return [self._units[uid] for uid in self.ids()]

    def contains(self, unit_id: str) -> bool:
        """True iff a unit id is registered."""
        return unit_id in self._units

    def validate_canonical(self) -> bool:
        """Ensure the registry holds exactly the 7 canonical units."""
        from .graph import UNIT_CHAIN

        expected = set(UNIT_CHAIN)
        if set(self._units.keys()) != expected:
            missing = sorted(expected - set(self._units.keys()))
            extra = sorted(set(self._units.keys()) - expected)
            msg = []
            if missing:
                msg.append("missing=%s" % (missing,))
            if extra:
                msg.append("extra=%s" % (extra,))
            raise CompositionDefinitionError(
                "Registry is not canonical (%s)" % "; ".join(msg)
            )
        return True

    def __len__(self) -> int:
        return len(self._units)
