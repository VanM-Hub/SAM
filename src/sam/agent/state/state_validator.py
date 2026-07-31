"""State Validator — validasi state (Sprint 158).

Agent Runtime — memvalidasi konsistensi state mission.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .agent_state import ALL_STATES, AgentState


@dataclass(frozen=True)
class StateValidation:
    """Hasil validasi state (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class StateValidator:
    """Validator state. Deterministik."""

    def validate(self, state: AgentState) -> StateValidation:
        issues = []
        if not state.mission_id:
            issues.append("mission_id required")
        if state.state not in ALL_STATES:
            issues.append(f"invalid state: {state.state}")
        return StateValidation(valid=not issues, issues=issues)
