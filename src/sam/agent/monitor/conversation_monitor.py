"""Conversation Monitor Bridge — query read-only (Sprint 161)."""
from __future__ import annotations

from .transition_monitor import TransitionMonitor
from .runtime_summary import RuntimeSummarizer


class ConversationMonitorBridge:
    """Bridge conversation — ringkasan monitoring read-only."""

    def __init__(self, monitor: TransitionMonitor, summarizer: RuntimeSummarizer = None) -> None:
        self._monitor = monitor
        self._summarizer = summarizer

    def show_progress(self, mission_id: str) -> dict:
        st = self._monitor.status(mission_id)
        return {
            "completed": st.completed_steps,
            "remaining": st.remaining_steps,
            "percent": st.progress_percent,
            "state": st.state,
        }

    def show_waiting_reason(self, mission_id: str) -> str:
        return self._monitor.status(mission_id).waiting_reason

    def show_summary(self) -> dict:
        if not self._summarizer:
            return {"total_missions": 0}
        s = self._summarizer.summary()
        return {"total_missions": s.total_missions, "states": s.state_counts}
