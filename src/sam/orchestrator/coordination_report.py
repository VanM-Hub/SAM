# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 129 - Coordination: coordination_report.

Report of a coordination run. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .coordination_state import CoordinationState


@dataclass(frozen=True)
class CoordinationReport:
    """Immutable report of coordinated runtimes."""

    states: Tuple[CoordinationState, ...] = field(default_factory=tuple)

    @property
    def coordinated_count(self) -> int:
        return sum(1 for s in self.states if s.is_coordinated)

    @property
    def all_coordinated(self) -> bool:
        return bool(self.states) and self.coordinated_count == len(self.states)
