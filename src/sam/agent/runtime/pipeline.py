"""Pipeline — pipeline Agent Runtime (Sprint 162).

Pipeline:
Mission -> State -> Planner -> Coordinator -> Monitor -> Summary
Belum memanggil runtime nyata. Preview only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .agent_runtime import AgentRuntime
from ..state.state_machine import CREATED, COMPLETED


@dataclass(frozen=True)
class PipelineStage:
    """Satu tahap pipeline (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class PipelineRun:
    """Hasil satu kali run pipeline (immutable)."""
    ok: bool = False
    mission_id: str = ""
    final_state: str = CREATED
    stages: List[PipelineStage] = field(default_factory=list)
    external_calls: int = 0


class Pipeline:
    """Pipeline Agent Runtime. Deterministik, preview-only."""

    def __init__(self, runtime: AgentRuntime) -> None:
        self._runtime = runtime

    def run(self, mission_id: str) -> PipelineRun:
        stages = []
        stages.append(PipelineStage(
            "mission", True,
            self._runtime.machine.create(mission_id).state,
        ))
        # State
        state = self._runtime.machine.current(mission_id).state
        stages.append(PipelineStage("state", True, state))
        # Planner
        plan = self._runtime.build_plan(f"plan.{mission_id}", mission_id)
        stages.append(PipelineStage("planner", plan.valid, f"{plan.plan.step_count} steps"))
        # Coordinator -> queue harus terisi
        if self._runtime.queue.count() == 0:
            self._runtime.enqueue_route(self._runtime.runtime_registry.names())
        stages.append(PipelineStage("coordinator", True, "route queued"))
        # Monitor
        monitor = self._runtime.monitor()
        st = monitor.status(mission_id)
        stages.append(PipelineStage("monitor", True, f"state={st.state}"))
        # Summary
        run = self._runtime.run_mission(mission_id)
        stages.append(PipelineStage("summary", run.ok, run.final_state))
        return PipelineRun(
            ok=run.ok,
            mission_id=mission_id,
            final_state=run.final_state,
            stages=stages,
            external_calls=0,
        )


__all__ = ["Pipeline", "PipelineRun", "PipelineStage"]
