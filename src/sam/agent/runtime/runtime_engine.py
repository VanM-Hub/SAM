"""Runtime Engine — engine Agent Runtime (Sprint 162).

Delegasi ringan ke AgentRuntime. Preview-only, salah satu runtime engine.
"""
from __future__ import annotations
from dataclasses import dataclass

from .agent_runtime import AgentRuntime, AgentRunResult


@dataclass(frozen=True)
class EngineInfo:
    """Info engine (immutable)."""
    version: str
    preview_only: bool = True
    deterministic: bool = True


class RuntimeEngine:
    """Runtime engine agent. Preview-only engine facade."""

    VERSION = "1.0.0"

    def __init__(self, runtime: AgentRuntime) -> None:
        self._runtime = runtime

    def info(self) -> EngineInfo:
        return EngineInfo(version=self.VERSION)

    def run(self, mission_id: str) -> AgentRunResult:
        return self._runtime.run_mission(mission_id)

    def health(self) -> bool:
        return True


__all__ = ["RuntimeEngine", "EngineInfo"]
