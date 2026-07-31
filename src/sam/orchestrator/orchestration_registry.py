# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 123 - Orchestration Foundation: orchestration_registry.

Registry that holds orchestration descriptors. The registry is a pure
in-memory catalog; it does not run any runtime.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, FrozenSet

from .orchestration_descriptor import OrchestrationDescriptor


@dataclass(frozen=True)
class OrchestrationRegistrationResult:
    """Immutable result of registering a descriptor."""

    runtime_id: str
    accepted: bool
    reason: str = ""


class OrchestrationRegistry:
    """Catalog of orchestratable runtime descriptors (sync, deterministic)."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, OrchestrationDescriptor] = {}

    def register(self, descriptor: OrchestrationDescriptor) -> OrchestrationRegistrationResult:
        """Register or update a descriptor."""
        self._descriptors[descriptor.runtime_id] = descriptor
        return OrchestrationRegistrationResult(
            runtime_id=descriptor.runtime_id,
            accepted=True,
            reason="registered",
        )

    def get(self, runtime_id: str) -> Optional[OrchestrationDescriptor]:
        """Return descriptor by id or None."""
        return self._descriptors.get(runtime_id)

    def all(self) -> Tuple[OrchestrationDescriptor, ...]:
        """Return all descriptors ordered by pipeline position."""
        return tuple(
            sorted(
                self._descriptors.values(),
                key=lambda d: (d.pipeline_position, d.runtime_id),
            )
        )

    def ids(self) -> FrozenSet[str]:
        """Return registered runtime ids."""
        return frozenset(self._descriptors.keys())

    def count(self) -> int:
        """Number of registered descriptors."""
        return len(self._descriptors)

    def clear(self) -> None:
        """Remove all descriptors."""
        self._descriptors.clear()
