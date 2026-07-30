"""Conversation Planning Bridge — 8 queries read-only."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.execution_strategy import (
    ExecutionStrategy, SequenceBuilder, ExecutionPriority, ExecutionSchedule,
)


class ConversationPlanning:
    """Conversation bridge untuk execution planning — 8 queries."""

    def __init__(self, strategy: ExecutionStrategy, sequence_builder: SequenceBuilder,
                 priority: ExecutionPriority, schedule: ExecutionSchedule) -> None:
        self._strategy = strategy
        self._sequence_builder = sequence_builder
        self._priority = priority
        self._schedule = schedule

    def get_strategy(self) -> ExecutionStrategy:
        return self._strategy

    def get_sequence_builder(self) -> SequenceBuilder:
        return self._sequence_builder

    def get_priority(self) -> ExecutionPriority:
        return self._priority

    def get_schedule(self) -> ExecutionSchedule:
        return self._schedule

    def count_strategies(self) -> int:
        """Hitung jumlah tipe strategi yang tersedia."""
        return 5

    def describe_strategies(self) -> List[str]:
        """Deskripsi semua tipe strategi."""
        return ["sequential", "parallel", "prioritized", "conditional", "fallback"]

    def get_priority_range(self) -> Dict[str, float]:
        """Range prioritas."""
        return {"min": 0.0, "max": 1.0}

    def get_schedule_capabilities(self) -> List[str]:
        """Kapabilitas schedule."""
        return ["window_creation", "time_slot_allocation"]
