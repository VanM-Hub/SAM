"""Cognitive Metadata — metadata unit kognitif (Sprint 188)."""
from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class CognitiveMetadata:
    """Metadata kognitif (immutable)."""
    owner_id: str = ""
    created_at: str = ""
    source_runtime: str = "cognitive"
    version: str = "19.0.0"
    preview_only: bool = True
    no_inference: bool = True

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(
                self, "created_at",
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
            )
