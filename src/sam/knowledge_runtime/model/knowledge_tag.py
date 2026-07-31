"""Knowledge Tag — tag knowledge (immutable DTO, Sprint 181).

Phase XVIII — Knowledge Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeTag:
    """Tag knowledge (immutable)."""
    tag_id: str
    name: str = ""
    category: str = "general"
