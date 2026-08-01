"""Sprint 272 - Presentation Layer Foundation: metadata."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PresentationMetadata:
    """Metadata immutable program (versi, program, sprint scope)."""

    program: str = "F"
    program_name: str = "Presentation Layer"
    version: str = "29.0.0"
    branch: str = "phase-xxix"
    sprints: Tuple[int, ...] = (272, 273, 274, 275, 276, 277, 278, 279)
    runtime_type: str = "desktop"

    def as_dict(self) -> dict:
        return {
            "program": self.program,
            "program_name": self.program_name,
            "version": self.version,
            "branch": self.branch,
            "sprints": list(self.sprints),
            "runtime_type": self.runtime_type,
        }
