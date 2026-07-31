"""Cognitive Manifest — manifest kognitif (Sprint 194)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class CognitiveManifest:
    """Manifest kognitif (immutable)."""
    version: str = "19.0.0"
    runtime: str = "cognitive_runtime"
    subsystems: List[str] = field(default_factory=list)
    preview_only: bool = True
    no_inference: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "subsystems",
            self.subsystems or [
                "foundation", "context", "builder", "runtime", "workspace",
                "monitor", "certification", "conversation", "dashboard",
            ],
        )
