"""Mission Step — langkah mission (Sprint 159).

Agent Runtime — satu langkah merujuk ke satu runtime yang dilalui mission.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MissionStep:
    """Langkah mission (immutable)."""
    step_id: str
    plan_id: str
    order: int
    runtime_name: str  # mis. "guardian", "decision", "execution", dst
    dependencies: List[str] = field(default_factory=list)
    preview_only: bool = True

    def depends_on(self, other_step: str) -> bool:
        return other_step in self.dependencies
