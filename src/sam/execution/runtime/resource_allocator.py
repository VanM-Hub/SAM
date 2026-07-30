"""Resource Allocator — preview alokasi resource."""
from __future__ import annotations
from typing import List, Optional
from sam.execution.runtime.resource_plan import (
    ResourcePlan, ResourceAllocation, ResourceLimits,
    ResourceAvailability, ResourceSummary,
)
from sam.execution.runtime.execution_candidate import ExecutionCandidate


class ResourceAllocator:
    """Allocator preview — menghitung alokasi resource secara preview-only."""

    def allocate(self, candidate: ExecutionCandidate,
                 limits: Optional[ResourceLimits] = None) -> ResourceAllocation:
        """Alokasi resource untuk satu kandidat."""
        base_cpu = 1.0
        base_mem = 64.0
        base_storage = 128.0
        base_network = 1.0

        effort_mult = max(0.5, min(2.0, candidate.estimated_effort / 10.0))

        if candidate.candidate_type == "batch":
            batch_size = candidate.metadata.get("batch_size", 1)
            effort_mult *= max(1.0, float(batch_size) / 2.0)
        elif candidate.candidate_type == "pipeline":
            steps = candidate.metadata.get("steps", 1)
            effort_mult *= max(1.0, float(steps))

        return ResourceAllocation(
            candidate_id=candidate.candidate_id,
            cpu_units=base_cpu * effort_mult,
            memory_mb=base_mem * effort_mult,
            storage_mb=base_storage * effort_mult,
            network_units=base_network * effort_mult,
            duration_seconds=candidate.estimated_effort * 60.0,
        )

    def allocate_all(self, candidates: List[ExecutionCandidate],
                     limits: Optional[ResourceLimits] = None) -> List[ResourceAllocation]:
        """Alokasi resource untuk semua kandidat."""
        return [self.allocate(c, limits) for c in candidates]

    def build_plan(self, plan_id: str, execution_plan_id: str,
                   candidates: List[ExecutionCandidate]) -> ResourcePlan:
        """Buat ResourcePlan dari daftar kandidat."""
        allocations = self.allocate_all(candidates)
        return ResourcePlan(
            plan_id=plan_id,
            execution_plan_id=execution_plan_id,
            total_cpu_units=sum(a.cpu_units for a in allocations),
            total_memory_mb=sum(a.memory_mb for a in allocations),
            total_storage_mb=sum(a.storage_mb for a in allocations),
            total_network_units=sum(a.network_units for a in allocations),
            estimated_duration_seconds=sum(a.duration_seconds for a in allocations),
        )

    def check_availability(self, allocations: List[ResourceAllocation],
                           available: ResourceAvailability) -> List[str]:
        """Cek apakah alokasi resource tersedia."""
        issues = []
        total_cpu = sum(a.cpu_units for a in allocations)
        total_mem = sum(a.memory_mb for a in allocations)
        total_stor = sum(a.storage_mb for a in allocations)
        total_net = sum(a.network_units for a in allocations)

        if total_cpu > available.available_cpu_units:
            issues.append(f"CPU: {total_cpu} > {available.available_cpu_units}")
        if total_mem > available.available_memory_mb:
            issues.append(f"Memory: {total_mem} > {available.available_memory_mb}")
        if total_stor > available.available_storage_mb:
            issues.append(f"Storage: {total_stor} > {available.available_storage_mb}")
        if total_net > available.available_network_units:
            issues.append(f"Network: {total_net} > {available.available_network_units}")
        return issues

    def get_summary(self, plans: List[ResourcePlan],
                    limits: ResourceLimits) -> ResourceSummary:
        """Buat ringkasan resource."""
        if not plans:
            return ResourceSummary()
        total_cpu = sum(p.total_cpu_units for p in plans)
        total_mem = sum(p.total_memory_mb for p in plans)
        total_stor = sum(p.total_storage_mb for p in plans)
        max_cpu = limits.max_cpu_units or 1
        usage = min(100.0, (total_cpu / max_cpu) * 100.0)
        return ResourceSummary(
            total_plans=len(plans),
            total_cpu_allocated=total_cpu,
            total_memory_allocated=total_mem,
            total_storage_allocated=total_stor,
            utilization_percent=round(usage, 1),
            status="active" if plans else "idle",
        )
