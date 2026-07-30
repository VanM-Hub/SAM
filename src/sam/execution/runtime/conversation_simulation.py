"""Conversation Simulation Bridge — 8 queries."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.simulation_engine import SimulationEngine


class ConversationSimulation:
    """Conversation bridge untuk execution simulation — 8 queries."""

    def __init__(self, engine: SimulationEngine) -> None:
        self._engine = engine

    def get_engine(self) -> SimulationEngine:
        return self._engine

    def describe_capabilities(self) -> List[str]:
        return ["simulate", "step_tracking", "summary", "scenario_run"]

    def count_capabilities(self) -> int:
        return len(self.describe_capabilities())

    def get_supported_actions(self) -> List[str]:
        return ["pending", "execute", "batch", "pipeline", "validate"]

    def count_simulations(self) -> int:
        return len(self._engine._results)

    def get_result_count(self) -> int:
        return len(self._engine._results)

    def latest_result_id(self) -> str:
        if self._engine._results:
            return self._engine._results[-1].simulation_id
        return ""


class DashboardSimulation:
    """Dashboard bridge untuk execution simulation — 5 cards."""

    def __init__(self, engine: SimulationEngine) -> None:
        self._engine = engine

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Simulation Engine",
            description="Engine simulasi preview",
            status="ready",
            metrics={"capabilities": 4},
            items=["simulate", "steps", "summary"],
        )

    def run_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Simulation Run",
            description="Jalankan simulasi",
            status="ready",
            metrics={"actions": 5},
            items=["execute", "batch", "pipeline", "validate"],
        )

    def results_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Simulation Results",
            description=f"{self._engine.get_summary().total_simulations} runs",
            status=self._engine.get_summary().status,
            metrics={"total_runs": self._engine.get_summary().total_simulations,
                     "avg_duration_ms": self._engine.get_summary().avg_duration_ms},
            items=["results"],
        )

    def steps_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Simulation Steps",
            description=f"{self._engine.get_summary().total_steps_across} total steps",
            status="active" if self._engine.get_summary().total_steps_across > 0 else "idle",
            metrics={"total_steps": self._engine.get_summary().total_steps_across},
            items=["steps"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        s = self._engine.get_summary()
        return ExecutionCard(
            title="Simulation Summary",
            description="Ringkasan simulasi",
            status=s.status,
            metrics={"runs": s.total_simulations, "scenarios": len(s.scenarios)},
            items=["summary"],
        )
