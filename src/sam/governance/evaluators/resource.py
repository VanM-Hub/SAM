"""
Resource Evaluator – Sprint 21 Fase 2

Evaluates resource availability (CPU, memory) against graph requirements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Callable, Dict, Any, List

from ..evaluator import BaseEvaluator
from ..models import GovernanceDecision, GovernanceResult

if TYPE_CHECKING:
    from ...execution.graph import ExecutionGraph
    from ...runtime.context import ExecutionContext


class ResourceEvaluator(BaseEvaluator):
    """Evaluates node resource availability.

    Accepts optional callables for dependency injection:

    - ``get_available_memory_mb`` () → float
    - ``get_available_cpu_cores`` () → float
    - ``get_resource_status`` () → dict with ``memory``, ``cpu``, ``disk`` keys

    Graph metadata can specify:
    - ``required_memory_mb`` (int/float) — minimum memory needed
    - ``required_cpu_cores`` (int/float) — minimum CPU needed
    - ``required_disk_mb`` (int/float) — minimum disk space needed

    Thresholds:
    - Required resource missing → REJECT (cannot run)
    - Available < required → WAIT (insufficient, retry later)
    - All resources sufficient → ALLOW
    """

    def __init__(
        self,
        *,
        get_available_memory_mb: Optional[Callable[[], float]] = None,
        get_available_cpu_cores: Optional[Callable[[], float]] = None,
        get_available_disk_mb: Optional[Callable[[], float]] = None,
        get_resource_status: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> None:
        super().__init__()
        self._get_available_memory_mb = get_available_memory_mb
        self._get_available_cpu_cores = get_available_cpu_cores
        self._get_available_disk_mb = get_available_disk_mb
        self._get_resource_status = get_resource_status

    @property
    def name(self) -> str:
        return "resource"

    async def _do_evaluate(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        return self._evaluate_sync(graph)

    def _evaluate_sync(self, graph: "ExecutionGraph") -> GovernanceResult:
        graph_meta = getattr(graph, "metadata", {}) or {}
        warnings: List[str] = []
        metadata_bag: Dict[str, Any] = {}

        required_memory = graph_meta.get("required_memory_mb")
        required_cpu = graph_meta.get("required_cpu_cores")
        required_disk = graph_meta.get("required_disk_mb")

        # If no resource requirements specified, allow
        if not any([required_memory, required_cpu, required_disk]):
            return GovernanceResult.allowed(reason="No resource requirements specified")

        # Check memory
        if required_memory and self._get_available_memory_mb:
            available = self._get_available_memory_mb()
            metadata_bag["available_memory_mb"] = available
            metadata_bag["required_memory_mb"] = required_memory

            if available < 0:
                return GovernanceResult.rejected(
                    reason="Memory status unavailable",
                    metadata=metadata_bag,
                )
            if available < required_memory:
                warnings.append(
                    f"Memory: {available:.0f}MB available, "
                    f"{required_memory}MB required"
                )

        # Check CPU
        if required_cpu and self._get_available_cpu_cores:
            available = self._get_available_cpu_cores()
            metadata_bag["available_cpu_cores"] = available
            metadata_bag["required_cpu_cores"] = required_cpu

            if available < 0:
                return GovernanceResult.rejected(
                    reason="CPU status unavailable",
                    metadata=metadata_bag,
                )
            if available < required_cpu:
                warnings.append(
                    f"CPU: {available:.1f} cores available, "
                    f"{required_cpu} required"
                )

        # Check disk
        if required_disk and self._get_available_disk_mb:
            available = self._get_available_disk_mb()
            metadata_bag["available_disk_mb"] = available
            metadata_bag["required_disk_mb"] = required_disk

            if available < 0:
                return GovernanceResult.rejected(
                    reason="Disk status unavailable",
                    metadata=metadata_bag,
                )
            if available < required_disk:
                warnings.append(
                    f"Disk: {available:.0f}MB available, "
                    f"{required_disk}MB required"
                )

        # Check full resource status
        if self._get_resource_status:
            status = self._get_resource_status()
            metadata_bag["resource_status"] = status
            # Also check from status dict if specific callables not set
            if not required_memory or not self._get_available_memory_mb:
                mem = status.get("memory")
                if mem and required_memory and mem < required_memory:
                    warnings.append(f"Memory (from status): {mem}MB < {required_memory}MB")
            if not required_cpu or not self._get_available_cpu_cores:
                cpu = status.get("cpu")
                if cpu and required_cpu and cpu < required_cpu:
                    warnings.append(f"CPU (from status): {cpu} < {required_cpu}")
            if not required_disk or not self._get_available_disk_mb:
                disk = status.get("disk")
                if disk and required_disk and disk < required_disk:
                    warnings.append(f"Disk (from status): {disk}MB < {required_disk}MB")

        if warnings:
            return GovernanceResult.wait(
                reason="Insufficient resources — retry later",
                suggested_delay=60,
                warnings=warnings,
                metadata=metadata_bag,
            )

        return GovernanceResult.allowed(
            reason="Resources sufficient",
            metadata=metadata_bag,
        )
