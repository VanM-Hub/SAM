"""Dashboard Tool — bridge dashboard <-> tool (Sprint 245).

Program B — Model Runtime Integration.
Read-only bridge; generic, tidak execute tool, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .tool_preview import ToolPreview


@dataclass(frozen=True)
class DashboardToolRow:
    """Satu baris tool pada dashboard (immutable)."""
    row_id: str
    preview_id: str
    call_count: int = 0
    would_execute: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "row_id": self.row_id,
            "preview_id": self.preview_id,
            "call_count": self.call_count,
            "would_execute": self.would_execute,
            "external_calls": self.external_calls,
        }


class DashboardTool:
    """Bridge dashboard <-> tool. Read-only, no network."""

    def __init__(self) -> None:
        self._rows: List[DashboardToolRow] = []

    def add(self, preview: ToolPreview) -> None:
        self._rows.append(DashboardToolRow(
            row_id=f"dtool-{len(self._rows) + 1}",
            preview_id=preview.preview_id,
            call_count=len(preview.calls),
            would_execute=preview.would_execute,
            external_calls=preview.external_calls,
        ))

    def rows(self) -> List[DashboardToolRow]:
        return list(self._rows)

    def summary(self) -> Dict[str, object]:
        return {
            "previews": len(self._rows),
            "calls": sum(r.call_count for r in self._rows),
            "external_calls": sum(r.external_calls for r in self._rows),
        }
