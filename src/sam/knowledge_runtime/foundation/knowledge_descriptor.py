"""Knowledge Descriptor — deskripsi knowledge (immutable DTO, Sprint 180).

Phase XVIII — Knowledge Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class KnowledgeDescriptor:
    """Deskripsi knowledge (immutable)."""
    id: str
    name: str = ""
    version: str = "1.0.0"
    category: str = "general"
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    fact_types: List[str] = field(default_factory=list)
    relation_types: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
