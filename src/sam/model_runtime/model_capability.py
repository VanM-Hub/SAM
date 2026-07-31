"""Model Capability — kapabilitas model (Sprint 239).

Program B — Model Runtime Integration.
Immutable, deterministik, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ModelCapability:
    """Kapabilitas model (immutable). Read-only."""
    id: str
    owner_id: str
    capability: str = "predict"
    operations: List[str] = field(default_factory=list)
    preview_only: bool = True
    no_inference: bool = True
    external_calls: int = 0

    def __post_init__(self) -> None:
        if not self.owner_id:
            raise ValueError("owner_id is required")

    def can(self, operation: str) -> bool:
        return operation in self.operations

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "capability": self.capability,
            "operations": list(self.operations),
            "preview_only": self.preview_only,
            "no_inference": self.no_inference,
            "external_calls": self.external_calls,
        }
