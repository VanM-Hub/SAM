"""Skill Runtime Manifest — manifest integrasi (Sprint 171)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SkillRuntimeManifest:
    """Manifest runtime integrasi (immutable)."""
    version: str = "16.0.0"
    runtime: str = "skills"
    integrated_runtimes: List[str] = field(default_factory=list)
    preview_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "integrated_runtimes",
            self.integrated_runtimes or [
                "mission", "agent", "orchestrator", "connector", "provider",
            ],
        )
