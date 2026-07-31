"""Memory Metadata — metadata memori (immutable DTO, Sprint 172).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class MemoryMetadata:
    """Metadata memori (immutable)."""
    memory_id: str
    author: str = ""
    created_at: str = ""
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    readonly: bool = True
