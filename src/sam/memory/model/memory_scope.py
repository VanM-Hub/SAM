"""Memory Scope — lingkup memori (immutable DTO, Sprint 173).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MemoryScope:
    """Lingkup memori (immutable)."""
    scope_id: str
    name: str = ""
    parent: str = ""
    allowed_tags: List[str] = field(default_factory=list)

    def allows(self, tag: str) -> bool:
        if not self.allowed_tags:
            return True
        return tag in self.allowed_tags
