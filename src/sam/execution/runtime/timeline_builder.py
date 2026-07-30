"""Timeline Builder — membangun timeline eksekusi."""
from __future__ import annotations
from typing import List, Optional
from sam.execution.runtime.timeline import (
    Timeline, TimelineEvent, ExecutionWindow, Milestone, TimelineSnapshot,
)
from sam.execution.runtime.execution_candidate import ExecutionCandidate


class TimelineBuilder:
    """Builder untuk timeline eksekusi."""

    def build(self, timeline_id: str, execution_order_id: str,
              candidates: List[ExecutionCandidate],
              start_time: float = 0.0) -> Timeline:
        """Bangun timeline dari kandidat."""
        events = []
        current_time = start_time

        for i, c in enumerate(candidates):
            event = TimelineEvent(
                event_id=f"ev_{c.candidate_id}",
                timestamp=current_time,
                event_type=c.candidate_type,
                description=f"Execute {c.name or c.candidate_id}",
                candidate_ids=(c.candidate_id,),
            )
            events.append(event)
            current_time += c.estimated_effort

        return Timeline(
            timeline_id=timeline_id,
            execution_order_id=execution_order_id,
            events=tuple(events),
            total_events=len(events),
            start_time=start_time,
            end_time=current_time,
            estimated_duration=current_time - start_time,
        )

    def create_window(self, window_id: str, timeline_id: str,
                      start: float, end: float,
                      candidates: List[ExecutionCandidate],
                      window_type: str = "execution") -> ExecutionWindow:
        """Buat execution window."""
        return ExecutionWindow(
            window_id=window_id,
            timeline_id=timeline_id,
            start_time=start,
            end_time=end,
            candidate_ids=tuple(c.candidate_id for c in candidates),
            window_type=window_type,
        )

    def create_milestone(self, milestone_id: str, timestamp: float,
                         name: str, description: str = "",
                         milestone_type: str = "checkpoint") -> Milestone:
        """Buat milestone."""
        return Milestone(
            milestone_id=milestone_id,
            timestamp=timestamp,
            name=name,
            description=description,
            milestone_type=milestone_type,
        )

    def snapshot(self, timeline: Timeline, windows: List[ExecutionWindow],
                 milestones: List[Milestone]) -> TimelineSnapshot:
        """Ambil snapshot timeline."""
        return TimelineSnapshot(
            timeline_id=timeline.timeline_id,
            total_events=timeline.total_events,
            total_windows=len(windows),
            total_milestones=len(milestones),
            estimated_duration=timeline.estimated_duration,
            status="ready" if timeline.total_events > 0 else "pending",
        )
