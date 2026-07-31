"""Workspace Builder — membangun representasi workspace (Sprint 190)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass(frozen=True)
class CognitiveWorkspaceDTO:
    """Representasi workspace immutable (Sprint 190 — dibangun builder)."""
    workspace_id: str
    items: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    preview_only: bool = True

    def item_count(self) -> int:
        return len(self.items)


class WorkspaceBuilder:
    """Builder workspace. Menyusun DTO saja, TANPA write/external."""

    def build(self, workspace_id: str, items: list = None) -> CognitiveWorkspaceDTO:
        return CognitiveWorkspaceDTO(workspace_id=workspace_id, items=list(items or []))

    def add_item(self, ws: CognitiveWorkspaceDTO, item: str) -> CognitiveWorkspaceDTO:
        return CognitiveWorkspaceDTO(
            workspace_id=ws.workspace_id,
            items=list(ws.items) + [item],
            labels=dict(ws.labels),
        )
