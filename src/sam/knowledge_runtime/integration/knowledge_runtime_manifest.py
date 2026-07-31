"""Knowledge Runtime Manifest — manifest integrasi (Sprint 187)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class KnowledgeRuntimeManifest:
    """Manifest runtime integrasi (immutable)."""
    version: str = "18.0.0"
    runtime: str = "knowledge_runtime"
    integrated_runtimes: List[str] = field(default_factory=list)
    preview_only: bool = True
    no_inference: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "integrated_runtimes",
            self.integrated_runtimes or [
                "mission", "agent", "skill", "memory",
                "orchestrator", "connector", "provider",
            ],
        )
