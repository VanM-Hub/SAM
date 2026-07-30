"""Conversation Lifecycle Bridge — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.lifecycle_manager import LifecycleManager
from sam.runtime_kernel.startup_manager import StartupManager
from sam.runtime_kernel.shutdown_manager import ShutdownManager
from sam.runtime_kernel.restart_manager import RestartManager


class ConversationLifecycle:
    def __init__(self, mgr: LifecycleManager, startup: StartupManager,
                 shutdown: ShutdownManager, restart: RestartManager) -> None:
        self._mgr = mgr
        self._startup = startup
        self._shutdown = shutdown
        self._restart = restart

    def get_lifecycle_manager(self) -> LifecycleManager:
        return self._mgr

    def get_startup_manager(self) -> StartupManager:
        return self._startup

    def get_shutdown_manager(self) -> ShutdownManager:
        return self._shutdown

    def get_restart_manager(self) -> RestartManager:
        return self._restart

    def describe_phases(self) -> List[str]:
        return ["startup", "shutdown", "restart"]

    def count_phases(self) -> int:
        return 3

    def get_startup_phases(self) -> List[str]:
        return self._startup.get_phase_names()

    def count_startup_phases(self) -> int:
        return self._startup.count_phases()


class DashboardLifecycle:
    def __init__(self, mgr: LifecycleManager, startup: StartupManager) -> None:
        self._mgr = mgr
        self._startup = startup

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Lifecycle Manager",
            description=f"{self._mgr.count_startups()} startups",
            status="ready",
            metrics={"startups": self._mgr.count_startups(),
                     "shutdowns": self._mgr.count_shutdowns(),
                     "restarts": self._mgr.count_restarts()},
            items=["create", "complete", "track"],
        )

    def startup_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Startup Plan",
            description=f"{self._startup.count_phases()} phases",
            status="ready",
            metrics={"phases": self._startup.count_phases()},
            items=self._startup.get_phase_names(),
        )

    def shutdown_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Shutdown Plan",
            description="Shutdown management",
            status="ready",
            metrics={"tasks": 4},
            items=["suspend", "save", "close", "finalize"],
        )

    def restart_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Restart Plan",
            description="Restart management",
            status="ready",
            metrics={"restarts": self._mgr.count_restarts()},
            items=["shutdown", "startup"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Lifecycle Summary",
            description="Ringkasan lifecycle runtime",
            status="ready",
            metrics={"phases": 3, "startup_phases": self._startup.count_phases()},
            items=["startup", "shutdown", "restart"],
        )
