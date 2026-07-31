"""Memory Manifest — manifest memori (Sprint 178)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MemoryManifest:
    """Manifest memori (immutable)."""
    version: str = "17.0.0"
    runtime: str = "memory"
    subsystems: List[str] = field(default_factory=list)
    preview_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "subsystems",
            self.subsystems or [
                "foundation", "model", "builder", "runtime", "catalog",
                "monitor", "certification", "conversation", "dashboard",
            ],
        )
