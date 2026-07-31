"""Cognitive Descriptor — deskripsi runtime kognitif (Sprint 188)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class CognitiveDescriptor:
    """Deskripsi unit kognitif (immutable)."""
    id: str
    name: str
    category: str = "cognitive"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    integrated_runtimes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id is required")
