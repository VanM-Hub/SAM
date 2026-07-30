"""Dashboard Planning Bridge — 5 immutable cards."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.execution_strategy import (
    ExecutionStrategy, SequenceBuilder, ExecutionPriority, ExecutionSchedule,
)
from sam.execution.runtime.dashboard_execution import ExecutionCard


class DashboardPlanning:
    """Dashboard bridge untuk execution planning — 5 immutable cards."""

    def __init__(self, strategy: ExecutionStrategy, sequence_builder: SequenceBuilder,
                 priority: ExecutionPriority, schedule: ExecutionSchedule) -> None:
        self._strategy = strategy
        self._sequence_builder = sequence_builder
        self._priority = priority
        self._schedule = schedule

    def strategy_card(self) -> ExecutionCard:
        """Card 1: Strategy info."""
        return ExecutionCard(
            title="Execution Strategy",
            description="Strategi eksekusi yang tersedia",
            status="ready",
            metrics={"available_strategies": 5},
            items=["sequential", "parallel", "prioritized", "conditional", "fallback"],
        )

    def sequence_card(self) -> ExecutionCard:
        """Card 2: Sequence info."""
        return ExecutionCard(
            title="Execution Sequence",
            description="Sequence builder status",
            status="ready",
            metrics={"builder_available": True},
            items=["sequence"],
        )

    def priority_card(self) -> ExecutionCard:
        """Card 3: Priority info."""
        return ExecutionCard(
            title="Priority Engine",
            description="Engine prioritas kandidat",
            status="ready",
            metrics={"range_min": 0.0, "range_max": 1.0},
            items=["priority"],
        )

    def schedule_card(self) -> ExecutionCard:
        """Card 4: Schedule info."""
        return ExecutionCard(
            title="Execution Schedule",
            description="Scheduler capabilities",
            status="ready",
            metrics={"window_support": True},
            items=["scheduling"],
        )

    def summary_card(self) -> ExecutionCard:
        """Card 5: Planning summary."""
        return ExecutionCard(
            title="Planning Summary",
            description="Ringkasan planning engine",
            status="ready",
            metrics={
                "strategies": 5,
                "sequence_builder": True,
                "priority_engine": True,
                "schedule_engine": True,
            },
            items=["planning"],
        )
