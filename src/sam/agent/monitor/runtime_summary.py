"""Runtime Summary — ringkasan runtime (Sprint 161).

Agent Runtime — ringkasan read-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..state.state_machine import StateMachine


@dataclass(frozen=True)
class RuntimeSummary:
    """Ringkasan runtime (immutable)."""
    total_missions: int = 0
    state_counts: Dict[str, int] = field(default_factory=dict)
    external_calls: int = 0


class RuntimeSummarizer:
    """Summarizer runtime. Read-only."""

    def __init__(self, machine: StateMachine) -> None:
        self._machine = machine

    def summary(self) -> RuntimeSummary:
        # machine menyimpan state per mission
        ids = getattr(self._machine, "_states", {})
        counts: Dict[str, int] = {}
        for state in ids.values():
            counts[state.state] = counts.get(state.state, 0) + 1
        return RuntimeSummary(
            total_missions=len(ids),
            state_counts=counts,
            external_calls=0,
        )
