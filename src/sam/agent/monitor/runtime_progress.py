"""Runtime Progress — progres runtime (Sprint 161).

Agent Runtime — progres mission read-only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RuntimeProgress:
    """Progres runtime (immutable)."""
    mission_id: str
    completed: int = 0
    total: int = 0
    current_runtime: Optional[str] = None

    @property
    def percent(self) -> int:
        if self.total == 0:
            return 0
        return min(100, int((self.completed / self.total) * 100))

    @property
    def done(self) -> bool:
        return self.total > 0 and self.completed >= self.total
