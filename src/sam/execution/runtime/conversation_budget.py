"""Conversation Budget Bridge — 8 queries."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.budget_engine import BudgetEngine


class ConversationBudget:
    """Conversation bridge untuk budget/cost — 8 queries."""

    def __init__(self, engine: BudgetEngine) -> None:
        self._engine = engine

    def get_engine(self) -> BudgetEngine:
        return self._engine

    def describe_capabilities(self) -> List[str]:
        return ["register_budget", "estimate", "batch_estimate", "report", "summary"]

    def count_capabilities(self) -> int:
        return len(self.describe_capabilities())

    def get_supported_cost_types(self) -> List[str]:
        return ["cpu", "memory", "storage", "network"]

    def count_cost_types(self) -> int:
        return 4

    def count_budgets(self) -> int:
        return len(self._engine._budgets)

    def count_estimates(self) -> int:
        return len(self._engine._estimates)


class DashboardBudget:
    """Dashboard bridge untuk budget — 5 cards."""

    def __init__(self, engine: BudgetEngine) -> None:
        self._engine = engine

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Budget Engine",
            description="Engine estimasi biaya",
            status="ready",
            metrics={"capabilities": 5, "cost_types": 4},
            items=["register", "estimate", "report"],
        )

    def budget_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Registered Budgets",
            description=f"{self._engine.get_summary().total_budgets} budgets",
            status="ready",
            metrics={"total_budgets": self._engine.get_summary().total_budgets},
            items=["budgets"],
        )

    def estimate_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Cost Estimates",
            description=f"{self._engine.get_summary().total_estimated_cost} total estimated",
            status="active" if self._engine.get_summary().total_estimated_cost > 0 else "idle",
            metrics={"total_estimated": self._engine.get_summary().total_estimated_cost,
                     "estimates": self._engine.get_summary().total_budgets},
            items=["estimates"],
        )

    def report_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        summary = self._engine.get_summary()
        return ExecutionCard(
            title="Budget Report",
            description=f"{summary.over_budget_count} over budget",
            status=summary.status,
            metrics={"over_budget": summary.over_budget_count},
            items=["report"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._engine.get_summary()
        return ExecutionCard(
            title="Budget Summary",
            description="Ringkasan biaya",
            status=s.status,
            metrics={"budgets": s.total_budgets, "cost": s.total_estimated_cost},
            items=["summary"],
        )
