"""Execution Descriptor (Sprint 250).

Program C - Real Execution Runtime.
Immutable, deterministic, preview-only description of an executable task.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ExecutionDescriptor:
    """Deskripsi unit eksekusi (immutable). Read-only, no network."""
    id: str
    name: str
    operation: str
    provider: str = "generic"
    mode: str = "preview"  # preview | execute | rollback
    category: str = "execution"
    description: str = ""
    requires_approval: bool = True
    provider_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id is required")
        if not self.name:
            raise ValueError("name is required")
        if self.mode not in ("preview", "execute", "rollback"):
            raise ValueError("mode must be preview|execute|rollback")
        if self.provider == "generic" and self.provider_ids:
            self.__dict__["provider"] = self.provider_ids[0]

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "operation": self.operation,
            "provider": self.provider,
            "mode": self.mode,
            "category": self.category,
            "description": self.description,
            "requires_approval": self.requires_approval,
            "provider_ids": list(self.provider_ids),
            "tags": list(self.tags),
        }
