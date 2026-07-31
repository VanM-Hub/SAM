"""Knowledge Metadata — metadata knowledge (immutable DTO, Sprint 180).

Phase XVIII — Knowledge Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class KnowledgeMetadata:
    """Metadata knowledge (immutable)."""
    knowledge_id: str
    author: str = ""
    created_at: str = ""
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    readonly: bool = True
