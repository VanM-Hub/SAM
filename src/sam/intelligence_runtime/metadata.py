"""Sprint 261 - Intelligence Runtime Foundation: metadata."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class IntelligenceMetadata:
    """Metadata immutable program (versi, program, sprint scope)."""

    program: str = "E"
    program_name: str = "Unified Intelligence Runtime"
    version: str = "28.0.0"
    branch: str = "phase-xxviii"
    sprints: Tuple[int, ...] = (261, 262, 263, 264, 265, 266, 267, 268)
    runtime_type: str = "intelligence"

    def as_dict(self) -> dict:
        return {
            "program": self.program,
            "program_name": self.program_name,
            "version": self.version,
            "branch": self.branch,
            "sprints": list(self.sprints),
            "runtime_type": self.runtime_type,
        }
