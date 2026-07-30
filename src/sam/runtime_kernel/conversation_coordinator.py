"""Conversation Coordinator Bridge — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.coordination_engine import CoordinationEngine
from sam.runtime_kernel.sync_coordinator import SyncCoordinator
from sam.runtime_kernel.orchestrator import Orchestrator


class ConversationCoordinator:
    def __init__(self, engine: CoordinationEngine, sync: SyncCoordinator,
                 orch: Orchestrator) -> None:
        self._engine = engine
        self._sync = sync
        self._orch = orch

    def get_engine(self) -> CoordinationEngine:
        return self._engine

    def get_sync_coordinator(self) -> SyncCoordinator:
        return self._sync

    def get_orchestrator(self) -> Orchestrator:
        return self._orch

    def describe_layers(self) -> List[str]:
        return ["engine", "sync", "orchestrator"]

    def count_layers(self) -> int:
        return 3

    def get_plan_count(self) -> int:
        return self._engine.count()

    def get_sync_count(self) -> int:
        return self._sync.count()


class DashboardCoordinator:
    def __init__(self, engine: CoordinationEngine, sync: SyncCoordinator,
                 orch: Orchestrator) -> None:
        self._engine = engine
        self._sync = sync
        self._orch = orch

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Coordination Engine",
            description=f"{self._engine.count()} plans",
            status="ready",
            metrics={"plans": self._engine.count()},
            items=["engine", "sync", "orch"],
        )

    def plan_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Coordination Plans",
            description="Plans",
            status="ready",
            metrics={"plans": self._engine.count()},
            items=["plans"],
        )

    def sync_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Sync Coordinator",
            description=f"{self._sync.count()} points",
            status="ready",
            metrics={"points": self._sync.count(),
                     "unsynced": len(self._sync.list_unsynced())},
            items=["sync"],
        )

    def orcher_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Orchestrator",
            description=f"{self._orch.count()} orders",
            status="ready",
            metrics={"orders": self._orch.count()},
            items=["orders"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Coordinator Summary",
            description="Ringkasan koordinasi",
            status="ready",
            metrics={"layers": 3, "plans": self._engine.count()},
            items=["engine", "sync", "orchestrator"],
        )
