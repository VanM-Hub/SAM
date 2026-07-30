"""Conversation Quality Bridge — 8 queries."""
from __future__ import annotations
from typing import Dict, List, Optional
from sam.execution.runtime.quality_engine import QualityEngine


class ConversationQuality:
    """Conversation bridge untuk quality — 8 queries."""

    def __init__(self, engine: QualityEngine) -> None:
        self._engine = engine

    def get_engine(self) -> QualityEngine:
        return self._engine

    def describe_capabilities(self) -> List[str]:
        return ["assess", "gate_create", "gate_evaluate", "summary", "metrics"]

    def count_capabilities(self) -> int:
        return len(self.describe_capabilities())

    def get_metric_names(self) -> List[str]:
        return ["effort_variance", "dependency_coverage", "type_diversity"]

    def count_metrics(self) -> int:
        return 3

    def count_assessments(self) -> int:
        return len(self._engine._assessments)

    def count_gates(self) -> int:
        return len(self._engine._gates)


class DashboardQuality:
    """Dashboard bridge untuk quality — 5 cards."""

    def __init__(self, engine: QualityEngine) -> None:
        self._engine = engine

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Quality Engine",
            description="Engine validasi kualitas",
            status="ready",
            metrics={"capabilities": 5, "metrics": 3},
            items=["assess", "gate", "summary"],
        )

    def assessment_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._engine.get_summary()
        return ExecutionCard(
            title="Quality Assessments",
            description=f"{s.total_assessments} total, avg {s.avg_score}",
            status=s.status,
            metrics={"total": s.total_assessments, "avg": s.avg_score},
            items=["assessments"],
        )

    def gate_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._engine.get_summary()
        return ExecutionCard(
            title="Quality Gates",
            description=f"{s.gates_passed} passed, {s.gates_failed} failed",
            status=s.status,
            metrics={"passed": s.gates_passed, "failed": s.gates_failed},
            items=["gates"],
        )

    def metrics_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Quality Metrics",
            description="3 metrics used for assessment",
            status="ready",
            metrics={"effort_variance": 1.0, "dependency_coverage": 0.8, "type_diversity": 0.5},
            items=["effort_variance", "dependency_coverage", "type_diversity"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._engine.get_summary()
        return ExecutionCard(
            title="Quality Summary",
            description="Ringkasan kualitas eksekusi",
            status=s.status,
            metrics={"assessments": s.total_assessments, "gates": s.gates_passed + s.gates_failed},
            items=["summary"],
        )
