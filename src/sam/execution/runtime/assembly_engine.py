"""Execution Assembly Engine — merakit komponen jadi Execution Plan Ready."""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from sam.execution.runtime.assembly import (
    AssemblyComponent, ExecutionAssembly, ReadinessReport, AssemblySummary,
)


class AssemblyEngine:
    """Engine perakitan eksekusi — preview-only."""

    def __init__(self) -> None:
        self._assemblies: Dict[str, ExecutionAssembly] = {}
        self._reports: Dict[str, ReadinessReport] = {}

    def assemble(self, assembly_id: str, execution_plan_id: str,
                 components: Optional[List[AssemblyComponent]] = None) -> ExecutionAssembly:
        """Rakit komponen jadi ExecutionAssembly."""
        components = components or []
        total = len(components)
        ready = sum(1 for c in components if c.status == "ready")
        failed = sum(1 for c in components if c.status == "failed")

        assembly = ExecutionAssembly(
            assembly_id=assembly_id,
            execution_plan_id=execution_plan_id,
            components=tuple(components),
            total_components=total,
            ready_components=ready,
            failed_components=failed,
            is_ready=ready == total and total > 0,
        )
        self._assemblies[assembly_id] = assembly
        return assembly

    def generate_report(self, report_id: str, assembly_id: str) -> Optional[ReadinessReport]:
        """Generate readiness report untuk assembly."""
        assembly = self._assemblies.get(assembly_id)
        if not assembly:
            return None

        readiness: Dict[str, float] = {}
        missing: List[str] = []

        for c in assembly.components:
            if c.status == "ready":
                readiness[c.name] = 1.0
            elif c.status == "partial":
                readiness[c.name] = 0.5
            else:
                readiness[c.name] = 0.0
                missing.append(c.name)

        overall = round(sum(readiness.values()) / len(readiness), 2) if readiness else 0.0

        report = ReadinessReport(
            report_id=report_id,
            assembly_id=assembly_id,
            overall_readiness=overall,
            component_readiness=readiness,
            missing_components=tuple(missing),
            is_ready=len(missing) == 0 and assembly.is_ready,
        )
        self._reports[report_id] = report
        return report

    def get_summary(self) -> AssemblySummary:
        """Buat ringkasan assembly."""
        ready = sum(1 for a in self._assemblies.values() if a.is_ready)
        total_comp = sum(a.total_components for a in self._assemblies.values())

        scores = [
            r.overall_readiness
            for r in self._reports.values()
        ]
        avg = round(sum(scores) / len(scores), 2) if scores else 0.0

        if ready > 0 and ready == len(self._assemblies):
            status = "ready"
        elif self._assemblies:
            status = "partial"
        else:
            status = "not_ready"

        return AssemblySummary(
            total_assemblies=len(self._assemblies),
            ready_assemblies=ready,
            avg_readiness=avg,
            total_components_across=total_comp,
            status=status,
        )
