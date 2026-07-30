"""Conversation Risk Bridge — 8 queries."""
from __future__ import annotations
from typing import Dict, List, Optional
from sam.execution.runtime.risk_engine import RiskEngine


class ConversationRisk:
    """Conversation bridge untuk risk — 8 queries."""

    def __init__(self, engine: RiskEngine) -> None:
        self._engine = engine

    def get_engine(self) -> RiskEngine:
        return self._engine

    def describe_capabilities(self) -> List[str]:
        return ["assess", "batch_assess", "report", "summary", "level_classification"]

    def count_capabilities(self) -> int:
        return len(self.describe_capabilities())

    def get_supported_levels(self) -> List[str]:
        return ["low", "medium", "high", "critical"]

    def count_levels(self) -> int:
        return 4

    def count_assessments(self) -> int:
        return len(self._engine._assessments)

    def latest_assessment_id(self) -> str:
        if self._engine._assessments:
            return list(self._engine._assessments.keys())[-1]
        return ""


class DashboardRisk:
    """Dashboard bridge untuk risk — 5 cards."""

    def __init__(self, engine: RiskEngine) -> None:
        self._engine = engine

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Risk Engine",
            description="Engine penilaian risiko",
            status="ready",
            metrics={"capabilities": 5, "levels": 4},
            items=["assess", "report", "summary"],
        )

    def assessment_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        summary = self._engine.get_summary()
        return ExecutionCard(
            title="Risk Assessments",
            description=f"{summary.total_assessments} total",
            status=summary.status,
            metrics={"total": summary.total_assessments, "avg": summary.avg_score},
            items=["assessments"],
        )

    def report_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._engine.get_summary()
        return ExecutionCard(
            title="Risk Report",
            description=f"{s.critical_count} critical",
            status=s.status,
            metrics={"critical": s.critical_count, "high": s.high_count, "medium": s.medium_count},
            items=["report"],
        )

    def levels_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Risk Levels",
            description="Distribusi level risiko",
            status="ready",
            metrics={"levels": 4},
            items=["low", "medium", "high", "critical"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._engine.get_summary()
        return ExecutionCard(
            title="Risk Summary",
            description="Ringkasan risiko eksekusi",
            status=s.status,
            metrics={"assessments": s.total_assessments, "avg_score": s.avg_score,
                     "critical": s.critical_count},
            items=["summary"],
        )
