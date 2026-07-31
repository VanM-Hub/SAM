# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 129 - Coordination: coordination_state.

State of a coordinated runtime. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CoordinationState:
    """Immutable state describing a coordination step."""

    runtime_id: str
    state: str = "planned"  # planned | ready | coordinated
    step: int = 0

    @property
    def is_ready(self) -> bool:
        return self.state == "ready"

    @property
    def is_coordinated(self) -> bool:
        return self.state == "coordinated"
