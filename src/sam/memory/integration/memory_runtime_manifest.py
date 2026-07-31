"""Memory Runtime Manifest — manifest integrasi (Sprint 179)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MemoryRuntimeManifest:
    """Manifest runtime integrasi (immutable)."""
    version: str = "17.0.0"
    runtime: str = "memory"
    integrated_runtimes: List[str] = field(default_factory=list)
    preview_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "integrated_runtimes",
            self.integrated_runtimes or [
                "mission", "agent", "skill", "orchestrator", "connector", "provider",
            ],
        )
