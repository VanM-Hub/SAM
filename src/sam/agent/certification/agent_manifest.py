"""Agent Manifest — manifest agent (Sprint 163).

Agent Runtime — manifest mendeklarasikan komponen agent runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AgentManifest:
    """Manifest agent (immutable)."""
    version: str = "15.0.0"
    runtime: str = "agent"
    subsystems: List[str] = field(default_factory=list)
    preview_only: bool = True

    def __post_init__(self) -> None:
        # diisi otomatis jika kosong
        object.__setattr__(
            self, "subsystems",
            self.subsystems or [
                "foundation", "session", "state", "planner", "coordinator",
                "monitor", "runtime", "certification", "conversation", "dashboard",
            ],
        )
