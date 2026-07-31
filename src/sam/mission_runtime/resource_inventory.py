# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 137 - Mission Resources: resource_inventory.

Inventory of resources. Pure in-memory, sync.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .resource_descriptor import ResourceDescriptor


class ResourceInventory:
    """Catalog of resources available for a mission."""

    def __init__(self) -> None:
        self._resources: Dict[str, ResourceDescriptor] = {}

    def add(self, descriptor: ResourceDescriptor) -> None:
        self._resources[descriptor.resource_id] = descriptor

    def get(self, resource_id: str) -> Optional[ResourceDescriptor]:
        return self._resources.get(resource_id)

    def all(self) -> Tuple[ResourceDescriptor, ...]:
        return tuple(sorted(self._resources.values(), key=lambda r: r.resource_id))

    def count(self) -> int:
        return len(self._resources)
