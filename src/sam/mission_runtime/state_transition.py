# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 139 - Mission State: state_transition.

A transition between mission states. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StateTransition:
    """Immutable record of a state transition."""

    mission_id: str
    from_state: str
    to_state: str

    @property
    def changed(self) -> bool:
        return self.from_state != self.to_state
