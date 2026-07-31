"""Memory Descriptor — deskripsi memori (immutable DTO, Sprint 172).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MemoryDescriptor:
    """Deskripsi memori (immutable)."""
    id: str
    name: str = ""
    version: str = "1.0.0"
    category: str = "general"
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    scopes: List[str] = field(default_factory=list)
    reference_types: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
