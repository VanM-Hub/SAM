"""Conversation Runtime Bridge — query read-only (Sprint 162)."""
from __future__ import annotations

from .agent_runtime import AgentRuntime
from .runtime_statistics import RuntimeStatisticsCollector


class ConversationRuntimeBridge:
    """Bridge conversation — ringkasan Agent Runtime read-only."""

    def __init__(self, runtime: AgentRuntime) -> None:
        self._runtime = runtime

    def show_agent_status(self) -> dict:
        return {
            "version": AgentRuntime.RUNTIME_VERSION,
            "missions": self._runtime.machine and len(
                getattr(self._runtime.machine, "_states", {})) or 0,
        }

    def show_current_state(self, mission_id: str) -> str:
        st = self._runtime.machine.current(mission_id)
        return st.state if st else "unknown"

    def show_summary(self) -> dict:
        stats = RuntimeStatisticsCollector(self._runtime).collect()
        return {
            "total": stats.total_missions,
            "completed": stats.completed,
            "external_calls": stats.external_calls,
        }
