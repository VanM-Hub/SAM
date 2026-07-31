"""Cognitive Workspace — representasi workspace immutable (Sprint 192)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass(frozen=True)
class CognitiveWorkspace:
    """Workspace kognitif — representasi immutable, TANPA write."""
    workspace_id: str
    items: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    preview_only: bool = True

    def item_count(self) -> int:
        return len(self.items)
