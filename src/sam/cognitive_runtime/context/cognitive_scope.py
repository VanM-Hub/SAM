"""Cognitive Scope — batas lingkup kognitif (Sprint 189)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


VALID_SCOPES = ["mission", "agent", "skill", "memory", "knowledge"]


@dataclass(frozen=True)
class CognitiveScope:
    """Lingkup kognitif (immutable)."""
    scope: str = "mission"
    included_runtimes: List[str] = field(default_factory=list)
    preview_only: bool = True

    def __post_init__(self) -> None:
        if self.scope not in VALID_SCOPES:
            raise ValueError(f"invalid scope '{self.scope}'")
        if not self.included_runtimes:
            # default: semua runtime hingga titik ini
            idx = VALID_SCOPES.index(self.scope)
            object.__setattr__(
                self, "included_runtimes", list(VALID_SCOPES[: idx + 1]),
            )
