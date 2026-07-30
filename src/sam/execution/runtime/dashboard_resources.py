"""Dashboard Resources Bridge — 5 immutable cards."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.resource_allocator import ResourceAllocator
from sam.execution.runtime.resource_plan import (
    ResourcePlan, ResourceLimits, ResourceAvailability, ResourceSummary,
)
from sam.execution.runtime.dashboard_execution import ExecutionCard


class DashboardResources:
    """Dashboard bridge untuk execution resources — 5 immutable cards."""

    def __init__(self, allocator: ResourceAllocator) -> None:
        self._allocator = allocator

    def plan_card(self) -> ExecutionCard:
        """Card 1: Resource plan info."""
        return ExecutionCard(
            title="Resource Plan",
            description="Rencana resource eksekusi",
            status="ready",
            metrics={
                "plan_builder": True,
                "resource_types": 4,
            },
            items=["cpu", "memory", "storage", "network"],
        )

    def limits_card(self) -> ExecutionCard:
        """Card 2: Resource limits."""
        limits = ResourceLimits()
        return ExecutionCard(
            title="Resource Limits",
            description="Batas maksimum resource",
            status="ready",
            metrics={
                "max_cpu": limits.max_cpu_units,
                "max_mem": limits.max_memory_mb,
                "max_storage": limits.max_storage_mb,
                "max_network": limits.max_network_units,
                "max_duration": limits.max_duration_seconds,
            },
            items=["limits"],
        )

    def availability_card(self) -> ExecutionCard:
        """Card 3: Resource availability."""
        avail = ResourceAvailability()
        return ExecutionCard(
            title="Resource Availability",
            description="Resource yang tersedia",
            status="available",
            metrics={
                "cpu": avail.available_cpu_units,
                "memory": avail.available_memory_mb,
                "storage": avail.available_storage_mb,
                "network": avail.available_network_units,
            },
            items=["available"],
        )

    def allocation_card(self) -> ExecutionCard:
        """Card 4: Allocation status."""
        return ExecutionCard(
            title="Allocation Status",
            description="Status alokasi resource",
            status="ready",
            metrics={"allocator_ready": True},
            items=["allocation"],
        )

    def summary_card(self) -> ExecutionCard:
        """Card 5: Resource summary."""
        return ExecutionCard(
            title="Resource Summary",
            description="Ringkasan resource",
            status="idle",
            metrics={"total_resource_types": 4},
            items=["summary"],
        )
