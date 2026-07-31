"""Audit Descriptor — deskripsi audit (Sprint 212)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AuditDescriptor:
    """Deskriptor audit immutable (frozen)."""
    audit_id: str
    category: str = "general"
    description: str = ""
    provenance: bool = True
    traceability: bool = True
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))
        if not self.audit_id.strip():
            raise ValueError("audit_id cannot be empty")
