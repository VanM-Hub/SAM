"""Knowledge Capability — kapabilitas knowledge (immutable DTO, Sprint 180).

Phase XVIII — Knowledge Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class KnowledgeCapability:
    """Kapabilitas knowledge (immutable). Preview-only default."""
    capability_id: str
    knowledge_id: str
    name: str = ""
    category: str = "knowledge"
    operations: List[str] = field(default_factory=list)
    preview_only: bool = True

    def supports(self, operation: str) -> bool:
        return operation in self.operations
