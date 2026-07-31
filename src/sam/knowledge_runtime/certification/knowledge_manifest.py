"""Knowledge Manifest — manifest knowledge (Sprint 186)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class KnowledgeManifest:
    """Manifest knowledge (immutable)."""
    version: str = "18.0.0"
    runtime: str = "knowledge_runtime"
    subsystems: List[str] = field(default_factory=list)
    preview_only: bool = True
    no_inference: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "subsystems",
            self.subsystems or [
                "foundation", "model", "builder", "runtime", "catalog",
                "monitor", "certification", "conversation", "dashboard",
            ],
        )
