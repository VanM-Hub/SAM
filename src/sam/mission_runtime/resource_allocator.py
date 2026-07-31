# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 137 - Mission Resources: resource_allocator.

Allocates available resources for a mission (planning only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .resource_inventory import ResourceInventory
from .resource_descriptor import ResourceDescriptor


@dataclass(frozen=True)
class ResourceAllocation:
    """Immutable allocation of resources."""

    allocated: Tuple[ResourceDescriptor, ...] = field(default_factory=tuple)

    @property
    def count(self) -> int:
        return len(self.allocated)

    @property
    def ids(self) -> Tuple[str, ...]:
        return tuple(r.resource_id for r in self.allocated)


class ResourceAllocator:
    """Allocates the available resources (deterministic)."""

    def __init__(self, inventory: ResourceInventory) -> None:
        self._inventory = inventory

    def allocate(self) -> ResourceAllocation:
        available = tuple(r for r in self._inventory.all() if r.available)
        return ResourceAllocation(allocated=available)
