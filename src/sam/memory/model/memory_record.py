"""Memory Record — record memori (immutable DTO, Sprint 173).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class MemoryRecord:
    """Record memori (immutable)."""
    record_id: str
    memory_id: str = ""
    name: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    scope: str = "general"
    tags: list = field(default_factory=list)
    preview_only: bool = True

    def is_valid(self) -> bool:
        return bool(self.record_id)
