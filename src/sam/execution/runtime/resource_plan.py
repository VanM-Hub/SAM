"""Resource Plan — frozen DTO rencana resource eksekusi."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ResourcePlan:
    """Rencana resource — alokasi resource untuk eksekusi."""
    plan_id: str
    execution_plan_id: str
    total_cpu_units: float = 0.0
    total_memory_mb: float = 0.0
    total_storage_mb: float = 0.0
    total_network_units: float = 0.0
    estimated_duration_seconds: float = 0.0
    resource_type: str = "standard"
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResourceAllocation:
    """Alokasi resource untuk satu kandidat."""
    candidate_id: str
    cpu_units: float = 0.0
    memory_mb: float = 0.0
    storage_mb: float = 0.0
    network_units: float = 0.0
    duration_seconds: float = 0.0


@dataclass(frozen=True)
class ResourceLimits:
    """Batas resource maksimum."""
    max_cpu_units: float = 100.0
    max_memory_mb: float = 4096.0
    max_storage_mb: float = 10240.0
    max_network_units: float = 1000.0
    max_duration_seconds: float = 3600.0
    max_concurrent_tasks: int = 10


@dataclass(frozen=True)
class ResourceAvailability:
    """Ketersediaan resource saat ini."""
    available_cpu_units: float = 100.0
    available_memory_mb: float = 4096.0
    available_storage_mb: float = 10240.0
    available_network_units: float = 1000.0
    total_cpu_units: float = 100.0
    total_memory_mb: float = 4096.0
    total_storage_mb: float = 10240.0
    total_network_units: float = 1000.0


@dataclass(frozen=True)
class ResourceSummary:
    """Ringkasan resource."""
    total_plans: int = 0
    total_cpu_allocated: float = 0.0
    total_memory_allocated: float = 0.0
    total_storage_allocated: float = 0.0
    utilization_percent: float = 0.0
    status: str = "idle"
