"""Conversation Alerts Bridge — 8 queries & conversations."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.alert_engine import AlertEngine


class ConversationAlerts:
    """Conversation bridge untuk execution alerts — 8 queries."""

    def __init__(self, engine: AlertEngine) -> None:
        self._engine = engine

    def get_engine(self) -> AlertEngine:
        return self._engine

    def describe_capabilities(self) -> List[str]:
        return ["rule_register", "rule_unregister", "evaluate_value",
                "acknowledge", "history", "summary"]

    def count_capabilities(self) -> int:
        return len(self.describe_capabilities())

    def get_supported_severities(self) -> List[str]:
        return ["critical", "warning", "info"]

    def get_supported_operators(self) -> List[str]:
        return ["gt", "lt", "gte", "lte", "eq"]

    def get_rules(self) -> dict:
        return self._engine.get_rules()

    def count_rules(self) -> int:
        return len(self._engine.get_rules())


class DashboardAlerts:
    """Dashboard bridge untuk execution alerts — 5 cards."""

    def __init__(self, engine: AlertEngine) -> None:
        self._engine = engine

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Alert Engine",
            description="Engine monitoring eksekusi",
            status="ready",
            metrics={"engine_ready": True, "capabilities": 6},
            items=["rules", "evaluation", "history"],
        )

    def rules_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Alert Rules",
            description="Aturan alert terdaftar",
            status="ready",
            metrics={"rule_count": self._engine.get_rules().__len__()},
            items=["rules"],
        )

    def alerts_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        summary = self._engine.get_summary()
        return ExecutionCard(
            title="Active Alerts",
            description=f"{summary.total_alerts} total alerts",
            status=summary.status,
            metrics={"total": summary.total_alerts, "critical": summary.critical_count,
                     "warning": summary.warning_count},
            items=["alerts"],
        )

    def history_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        history = self._engine.get_history()
        return ExecutionCard(
            title="Alert History",
            description=f"{history.total_alerts} historical alerts",
            status="active" if history.total_alerts > 0 else "idle",
            metrics={"total": history.total_alerts,
                     "latest_ts": history.latest_timestamp},
            items=["history"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        summary = self._engine.get_summary()
        return ExecutionCard(
            title="Alert Summary",
            description="Ringkasan status monitoring",
            status=summary.status,
            metrics={"acknowledged": summary.acknowledged_count},
            items=["summary"],
        )
