"""Conversation Assembly Bridge — 8 queries."""
from __future__ import annotations
from typing import Dict, List, Optional
from sam.execution.runtime.assembly_engine import AssemblyEngine


class ConversationAssembly:
    """Conversation bridge untuk assembly — 8 queries."""

    def __init__(self, engine: AssemblyEngine) -> None:
        self._engine = engine

    def get_engine(self) -> AssemblyEngine:
        return self._engine

    def get_component_types(self) -> List[str]:
        return ["plan", "resources", "dependencies", "timeline", "alerts", "risk", "quality"]

    def describe_capabilities(self) -> List[str]:
        return ["assemble", "report", "summary", "readiness_check"]

    def count_capabilities(self) -> int:
        return len(self.describe_capabilities())

    def count_component_types(self) -> int:
        return len(self.get_component_types())

    def count_assemblies(self) -> int:
        return len(self._engine._assemblies)

    def latest_assembly_id(self) -> str:
        if self._engine._assemblies:
            return list(self._engine._assemblies.keys())[-1]
        return ""


class DashboardAssembly:
    """Dashboard bridge untuk assembly — 5 cards."""

    def __init__(self, engine: AssemblyEngine) -> None:
        self._engine = engine

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Assembly Engine",
            description="Engine merakit komponen eksekusi",
            status="ready",
            metrics={"capabilities": 4, "component_types": 7},
            items=["assemble", "report", "readiness"],
        )

    def assembly_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._engine.get_summary()
        return ExecutionCard(
            title="Execution Assemblies",
            description=f"{s.total_assemblies} total, {s.ready_assemblies} ready",
            status=s.status,
            metrics={"total": s.total_assemblies, "ready": s.ready_assemblies},
            items=["assemblies"],
        )

    def readiness_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._engine.get_summary()
        return ExecutionCard(
            title="Readiness Status",
            description=f"Avg readiness {s.avg_readiness}",
            status=s.status,
            metrics={"avg_readiness": s.avg_readiness, "components": s.total_components_across},
            items=["readiness"],
        )

    def report_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._engine.get_summary()
        return ExecutionCard(
            title="Assembly Reports",
            description=f"{len(self._engine._reports)} reports generated",
            status=s.status,
            metrics={"reports": len(self._engine._reports)},
            items=["reports"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._engine.get_summary()
        return ExecutionCard(
            title="Assembly Summary",
            description="Ringkasan perakitan eksekusi",
            status=s.status,
            metrics={"assemblies": s.total_assemblies,
                     "ready": s.ready_assemblies,
                     "readiness": s.avg_readiness},
            items=["summary"],
        )
