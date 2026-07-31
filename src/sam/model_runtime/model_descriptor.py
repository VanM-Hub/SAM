"""Model Descriptor — deskripsi unit model (Sprint 239).

Program B — Model Runtime Integration.
Immutable, deterministik, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ModelDescriptor:
    """Deskripsi model (immutable). Read-only, no network."""
    id: str
    name: str
    category: str = "model"
    model_type: str = "chat"  # chat | embedding | reasoning | vision | tool
    description: str = ""
    tags: List[str] = field(default_factory=list)
    integrated_runtimes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id is required")
        if not self.name:
            raise ValueError("name is required")

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "model_type": self.model_type,
            "description": self.description,
            "tags": list(self.tags),
            "integrated_runtimes": list(self.integrated_runtimes),
        }
