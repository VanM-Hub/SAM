"""Memory Capability — kapabilitas memori (immutable DTO, Sprint 172).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MemoryCapability:
    """Kapabilitas memori (immutable). Preview-only default."""
    capability_id: str
    memory_id: str
    name: str = ""
    category: str = "memory"
    operations: List[str] = field(default_factory=list)
    preview_only: bool = True

    def supports(self, operation: str) -> bool:
        return operation in self.operations
