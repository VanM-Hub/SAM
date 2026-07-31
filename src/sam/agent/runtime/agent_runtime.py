"""Agent Runtime — engine utama Agent Runtime (Sprint 162).

Agent Runtime mengendalikan lifecycle Mission dari Created hingga Completed
dalam mode preview. Tidak memanggil runtime nyata, tidak mengeksekusi,
tidak approval, tidak reasoning, tidak learning. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from ..foundation.agent_registry import AgentRegistry
from ..planner.mission_builder import MissionBuilder, PlanResult
from ..state.state_machine import StateMachine, TransitionResult
from ..state.transition_history import TransitionHistory
from ..coordinator.runtime_registry import RuntimeRegistry
from ..coordinator.runtime_queue import RuntimeQueue
from ..monitor.transition_monitor import TransitionMonitor, TransitionStatus


@dataclass(frozen=True)
class AgentRunResult:
    """Hasil menjalankan pipeline agent (immutable)."""
    mission_id: str
    ok: bool = False
    final_state: str = "Created"
    steps: int = 0
    external_calls: int = 0
    detail: str = ""


class AgentRuntime:
    """Runtime utama agent. Preview-only pipeline lifecycle."""

    RUNTIME_VERSION = "1.0.0"

    def __init__(self, agent_registry: AgentRegistry) -> None:
        self._agents = agent_registry
        self._machine = StateMachine()
        self._history = TransitionHistory()
        self._runtime_registry = RuntimeRegistry()
        self._queue = RuntimeQueue()
        self._builder = MissionBuilder()
        self._plan = None

    # --- setup ---
    def register_runtimes(self, names: list) -> None:
        self._runtime_registry.register_many(names)

    def enqueue_route(self, runtimes: list) -> None:
        self._queue.enqueue_many(runtimes)

    @property
    def machine(self) -> StateMachine:
        return self._machine

    @property
    def history(self) -> TransitionHistory:
        return self._history

    @property
    def runtime_registry(self) -> RuntimeRegistry:
        return self._runtime_registry

    @property
    def queue(self) -> RuntimeQueue:
        return self._queue

    def monitor(self) -> TransitionMonitor:
        return TransitionMonitor(
            self._machine, self._history, self._queue,
            pipeline_length=max(1, len(self._queue.entries())),
        )

    # --- lifecycle pipeline ---
    def build_plan(self, plan_id: str, mission_id: str) -> PlanResult:
        result = self._builder.build_default(plan_id, mission_id)
        if result.valid:
            self._plan = result.plan
        return result

    def run_mission(self, mission_id: str) -> AgentRunResult:
        """Jalankan pipeline lifecycle mission dalam mode preview."""
        state = self._machine.current(mission_id)
        if state is None:
            return AgentRunResult(
                mission_id=mission_id, ok=False, detail="mission not created"
            )
        if state.is_terminal():
            return AgentRunResult(
                mission_id=mission_id, ok=False,
                final_state=state.state, detail="mission already terminal",
            )
        steps = 0
        # Simulasikan kemajuan lewat antrian (preview-only)
        processed = 0
        while not state.is_terminal():
            nxt = self._queue.next_pending()
            to_state = "Completed"
            if nxt is not None:
                steps += 1
                processed += 1
                self._queue.mark_processed(nxt.runtime_name)
                # lanjut ke Running lalu Waiting/Completed simulasi
                if state.state == "Created":
                    self._machine.transition(mission_id, "Preparing")
                    self._machine.transition(mission_id, "Running")
                    self._history.record(
                        self._transition_event(mission_id, "Created", "Running")
                    )
                # setelah semua runtime diproses -> Completed
                if self._queue.next_pending() is None:
                    self._machine.transition(mission_id, "Completed")
                    self._history.record(
                        self._transition_event(mission_id, "Running", "Completed")
                    )
                state = self._machine.current(mission_id)
            else:
                # antrian habis tetapi belum terminal -> Completed
                if state.state != "Completed" and not state.is_terminal():
                    self._machine.transition(mission_id, "Completed")
                    self._history.record(
                        self._transition_event(mission_id, "Running", "Completed")
                    )
                    state = self._machine.current(mission_id)
                break
        final = self._machine.current(mission_id)
        return AgentRunResult(
            mission_id=mission_id,
            ok=final.state == "Completed",
            final_state=final.state,
            steps=processed,
            external_calls=0,
            detail="preview pipeline complete",
        )

    def _transition_event(self, mission_id, fr, to):
        from ..state.transition_history import TransitionEvent
        return TransitionEvent(mission_id=mission_id, from_state=fr, to_state=to)


__all__ = ["AgentRuntime", "AgentRunResult"]
