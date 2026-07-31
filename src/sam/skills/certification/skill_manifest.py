"""Skill Manifest — manifest skill (Sprint 170).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SkillManifest:
    """Manifest skill (immutable)."""
    version: str = "16.0.0"
    runtime: str = "skills"
    subsystems: List[str] = field(default_factory=list)
    preview_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "subsystems",
            self.subsystems or [
                "foundation", "definition", "builder", "runtime", "catalog",
                "monitor", "certification", "conversation", "dashboard",
            ],
        )
