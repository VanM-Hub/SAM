"""Cognitive Reference — referensi runtime (Sprint 189)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class CognitiveReference:
    """Referensi antar-runtime (immutable). Read-only."""
    runtime: str = "knowledge"
    source_id: str = ""
    kind: str = "context"
    preview_only: bool = True

    def __post_init__(self) -> None:
        if not self.runtime:
            raise ValueError("runtime is required")
