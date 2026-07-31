# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 137 - Mission Resources: conversation_resource.

Read-only conversation bridge for resources.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from .resource_inventory import ResourceInventory
from .resource_allocator import ResourceAllocator, ResourceAllocation
from .resource_descriptor import ResourceDescriptor
from .resource_summary import ResourceSummary


class ConversationResourceBridge:
    """Read-only bridge exposing resource allocation."""

    def __init__(self, inventory: ResourceInventory) -> None:
        self._inventory = inventory
        self._allocator = ResourceAllocator(inventory)

    def add(self, resource_id: str, available: bool = True) -> None:
        self._inventory.add(ResourceDescriptor(resource_id, available=available))

    def allocate(self) -> ResourceAllocation:
        return self._allocator.allocate()

    def locate(self, resource_id: str) -> Optional[ResourceDescriptor]:
        return self._inventory.get(resource_id)

    def summarize(self) -> ResourceSummary:
        allocation = self._allocator.allocate()
        return ResourceSummary(
            allocated_ids=allocation.ids,
            total=self._inventory.count(),
        )
