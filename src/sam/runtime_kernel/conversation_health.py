"""Conversation Health Bridge — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.health_checker import HealthChecker
from sam.runtime_kernel.health_engine import HealthEngine
from sam.runtime_kernel.resource_monitor import ResourceMonitor
from sam.runtime_kernel.health_aggregator import HealthAggregator


class ConversationHealth:
    def __init__(self, checker: HealthChecker, engine: HealthEngine,
                 monitor: ResourceMonitor, aggregator: HealthAggregator) -> None:
        self._checker = checker
        self._engine = engine
        self._monitor = monitor
        self._aggregator = aggregator

    def get_checker(self) -> HealthChecker:
        return self._checker

    def get_engine(self) -> HealthEngine:
        return self._engine

    def get_monitor(self) -> ResourceMonitor:
        return self._monitor

    def get_aggregator(self) -> HealthAggregator:
        return self._aggregator

    def describe_layers(self) -> List[str]:
        return ["checker", "engine", "monitor", "aggregator"]

    def count_layers(self) -> int:
        return 4

    def get_health_status(self) -> str:
        return "healthy"

    def get_unhealthy_count(self) -> int:
        return len(self._checker.list_unhealthy())


class DashboardHealth:
    def __init__(self, checker: HealthChecker, engine: HealthEngine,
                 monitor: ResourceMonitor, aggregator: HealthAggregator) -> None:
        self._checker = checker
        self._engine = engine
        self._monitor = monitor
        self._aggregator = aggregator

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Health Engine",
            description=f"{self._checker.count_checks()} checks",
            status="ready",
            metrics={"checks": self._checker.count_checks(),
                     "alerts": self._engine.count_alerts(),
                     "cpu_avg": self._monitor.cpu_avg(),
                     "mem_avg": self._monitor.memory_avg()},
            items=["health", "monitor"],
        )

    def checker_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Health Checker",
            description=f"{self._checker.count_checks()} checks",
            status="ready",
            metrics={"checks": self._checker.count_checks(),
                     "unhealthy": len(self._checker.list_unhealthy())},
            items=["checks"],
        )

    def resource_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Resource Monitor",
            description=f"{self._monitor.count()} records",
            status="ready",
            metrics={"records": self._monitor.count(),
                     "cpu_avg": self._monitor.cpu_avg(),
                     "mem_avg": self._monitor.memory_avg()},
            items=["cpu", "memory"],
        )

    def alert_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Health Alerts",
            description=f"{self._engine.count_alerts()} alerts",
            status="ready",
            metrics={"alerts": self._engine.count_alerts()},
            items=["alerts"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Health Summary",
            description="Ringkasan kesehatan runtime",
            status="ready",
            metrics={"layers": 4, "checks": self._checker.count_checks()},
            items=["checker", "engine", "monitor", "aggregator"],
        )
