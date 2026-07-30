"""Conversation Final Bridge — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.final_inspector import FinalInspector
from sam.runtime_kernel.kernel_reporter import KernelReporter


class ConversationFinal:
    def __init__(self, inspector: FinalInspector, reporter: KernelReporter) -> None:
        self._inspector = inspector
        self._reporter = reporter

    def get_inspector(self) -> FinalInspector:
        return self._inspector

    def get_reporter(self) -> KernelReporter:
        return self._reporter

    def describe_layers(self) -> List[str]:
        return ["inspector", "reporter"]

    def count_layers(self) -> int:
        return 2

    def get_component_count(self) -> int:
        return self._inspector.count_components()

    def get_status(self) -> str:
        return "ready"

    def list_components(self) -> List[str]:
        return self._inspector.list_components()

    def count_components_list(self) -> int:
        return len(self._inspector.list_components())


class DashboardFinal:
    def __init__(self, inspector: FinalInspector, reporter: KernelReporter) -> None:
        self._inspector = inspector
        self._reporter = reporter

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Kernel Final",
            description=f"{self._inspector.count_components()} components",
            status="ready",
            metrics={"components": self._inspector.count_components(),
                     "healthy": sum(1 for c in self._inspector.inspect_components() if c.healthy)},
            items=["inspect", "report"],
        )

    def inspector_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Final Inspector",
            description="Component inspection",
            status="ready",
            metrics={"components": self._inspector.count_components()},
            items=self._inspector.list_components(),
        )

    def report_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Kernel Reporter",
            description="Final reports",
            status="ready",
            metrics={"reports": 0},
            items=["reports"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._inspector.generate_summary()
        return ExecutionCard(
            title="Kernel Summary",
            description=f"v{s.version}",
            status="ready",
            metrics={"total": s.total_components,
                     "healthy": s.healthy_count},
            items=["summary"],
        )

    def verdict_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        v = self._inspector.final_verdict("v_final")
        return ExecutionCard(
            title="Final Verdict",
            description=f"{'READY' if v.ready else 'NOT READY'}",
            status="ready" if v.ready else "degraded",
            metrics={"ready": 1 if v.ready else 0},
            items=[v.reason],
        )
