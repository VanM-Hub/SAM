"""Conversation Resources Bridge — 8 queries read-only."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.resource_allocator import ResourceAllocator
from sam.execution.runtime.resource_plan import ResourceLimits, ResourceAvailability


class ConversationResources:
    """Conversation bridge untuk execution resources — 8 queries."""

    def __init__(self, allocator: ResourceAllocator) -> None:
        self._allocator = allocator

    def get_allocator(self) -> ResourceAllocator:
        return self._allocator

    def describe_default_limits(self) -> Dict[str, Any]:
        limits = ResourceLimits()
        return {
            "max_cpu": limits.max_cpu_units,
            "max_memory_mb": limits.max_memory_mb,
            "max_storage_mb": limits.max_storage_mb,
            "max_network": limits.max_network_units,
            "max_duration": limits.max_duration_seconds,
            "max_concurrent": limits.max_concurrent_tasks,
        }

    def default_availability(self) -> ResourceAvailability:
        return ResourceAvailability()

    def count_resource_types(self) -> int:
        return 4  # cpu, memory, storage, network

    def count_limits(self) -> int:
        return 6

    def allocation_summary(self, allocations: List) -> Dict[str, float]:
        return {
            "total_cpu": sum(a.cpu_units for a in allocations),
            "total_memory": sum(a.memory_mb for a in allocations),
            "total_storage": sum(a.storage_mb for a in allocations),
            "total_network": sum(a.network_units for a in allocations),
        } if allocations else {
            "total_cpu": 0.0, "total_memory": 0.0,
            "total_storage": 0.0, "total_network": 0.0,
        }

    def get_resource_types(self) -> List[str]:
        return ["cpu", "memory", "storage", "network"]

    def get_available_resource_types(self) -> List[str]:
        return self.get_resource_types()
