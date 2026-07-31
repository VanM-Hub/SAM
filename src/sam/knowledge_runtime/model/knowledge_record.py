"""Knowledge Record — record knowledge (immutable DTO, Sprint 181).

Phase XVIII — Knowledge Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class KnowledgeRecord:
    """Record knowledge (immutable)."""
    record_id: str
    knowledge_id: str = ""
    name: str = ""
    facts: List[str] = field(default_factory=list)  # fact ids
    relations: List[str] = field(default_factory=list)  # relation ids
    scope: str = "general"
    data: Dict[str, Any] = field(default_factory=dict)
    preview_only: bool = True

    def is_valid(self) -> bool:
        return bool(self.record_id)
