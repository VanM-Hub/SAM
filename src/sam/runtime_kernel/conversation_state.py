"""Conversation State Bridge — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.state_machine import StateMachineEngine
from sam.runtime_kernel.state_snapshot import SnapshotEngine
from sam.runtime_kernel.state_history import StateHistory
from sam.runtime_kernel.state_validator import StateValidator


class ConversationState:
    def __init__(self, machine: StateMachineEngine, snapshot: SnapshotEngine,
                 history: StateHistory, validator: StateValidator) -> None:
        self._machine = machine
        self._snapshot = snapshot
        self._history = history
        self._validator = validator

    def get_machine_engine(self) -> StateMachineEngine:
        return self._machine

    def get_snapshot_engine(self) -> SnapshotEngine:
        return self._snapshot

    def get_history(self) -> StateHistory:
        return self._history

    def get_validator(self) -> StateValidator:
        return self._validator

    def describe_layers(self) -> List[str]:
        return ["machine", "snapshot", "history", "validator"]

    def count_layers(self) -> int:
        return 4

    def get_valid_states(self) -> List[str]:
        return StateValidator.VALID_STATES

    def count_states(self) -> int:
        return len(StateValidator.VALID_STATES)


class DashboardState:
    def __init__(self, machine: StateMachineEngine, snapshot: SnapshotEngine,
                 history: StateHistory) -> None:
        self._machine = machine
        self._snapshot = snapshot
        self._history = history

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="State Machine Engine",
            description=f"{len(self._machine._machines)} machines",
            status="ready",
            metrics={"machines": len(self._machine._machines), "states": 7},
            items=["FSM", "transitions"],
        )

    def snapshot_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="State Snapshots",
            description=f"{self._snapshot.count()} snapshots",
            status="ready",
            metrics={"snapshots": self._snapshot.count()},
            items=["snapshots"],
        )

    def history_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="State History",
            description=f"{self._history.count()} entries",
            status="ready",
            metrics={"entries": self._history.count()},
            items=["history"],
        )

    def validation_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="State Validation",
            description="Validation layer",
            status="ready",
            metrics={"states": 7},
            items=["validate", "is_valid"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="State Summary",
            description="Ringkasan state runtime",
            status="ready",
            metrics={"machines": len(self._machine._machines),
                     "history": self._history.count(),
                     "snapshots": self._snapshot.count()},
            items=["state", "transition", "snapshot", "history"],
        )
