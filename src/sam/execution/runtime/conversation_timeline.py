"""Conversation Timeline Bridge — 8 queries."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.timeline_builder import TimelineBuilder


class ConversationTimeline:
    """Conversation bridge untuk execution timeline — 8 queries."""

    def __init__(self, builder: TimelineBuilder) -> None:
        self._builder = builder

    def get_builder(self) -> TimelineBuilder:
        return self._builder

    def describe_types(self) -> List[str]:
        return ["timeline", "window", "milestone", "snapshot"]

    def count_components(self) -> int:
        return 4

    def get_supported_event_types(self) -> List[str]:
        return ["immediate", "scheduled", "conditional", "batch", "pipeline"]

    def get_supported_window_types(self) -> List[str]:
        return ["execution", "preparation", "validation", "review"]

    def get_milestone_types(self) -> List[str]:
        return ["checkpoint", "approval", "review", "handoff"]

    def estimate_duration(self, timeline) -> float:
        return timeline.estimated_duration if hasattr(timeline, 'estimated_duration') else 0.0


class DashboardTimeline:
    """Dashboard bridge untuk execution timeline — 5 cards."""

    def __init__(self, builder: TimelineBuilder) -> None:
        self._builder = builder

    def timeline_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Execution Timeline",
            description="Timeline eksekusi",
            status="ready",
            metrics={"builder_ready": True},
            items=["timeline"],
        )

    def windows_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Execution Windows",
            description="Window eksekusi",
            status="ready",
            metrics={"window_types": 4},
            items=["execution", "preparation", "validation", "review"],
        )

    def milestones_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Milestones",
            description="Milestone tracking",
            status="ready",
            metrics={"milestone_types": 4},
            items=["checkpoint", "approval", "review", "handoff"],
        )

    def snapshot_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Timeline Snapshot",
            description="Snapshot timeline terkini",
            status="pending",
            metrics={"events": 0, "windows": 0, "milestones": 0},
            items=["snapshot"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Timeline Summary",
            description="Ringkasan timeline engine",
            status="ready",
            metrics={"components": 4},
            items=["summary"],
        )
