"""Dashboard Vision — bridge dashboard <-> vision (Sprint 244).

Program B — Model Runtime Integration.
Read-only bridge; representasi image input, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .vision_preview import VisionPreview


@dataclass(frozen=True)
class DashboardVisionRow:
    """Satu baris vision pada dashboard (immutable)."""
    row_id: str
    request_id: str
    image_count: int = 0
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "row_id": self.row_id,
            "request_id": self.request_id,
            "image_count": self.image_count,
            "external_calls": self.external_calls,
        }


class DashboardVision:
    """Bridge dashboard <-> vision. Read-only, no network."""

    def __init__(self) -> None:
        self._rows: List[DashboardVisionRow] = []

    def add(self, preview: VisionPreview) -> None:
        self._rows.append(DashboardVisionRow(
            row_id=f"dvis-{len(self._rows) + 1}",
            request_id=preview.request_id,
            image_count=preview.image_count,
            external_calls=preview.external_calls,
        ))

    def rows(self) -> List[DashboardVisionRow]:
        return list(self._rows)

    def summary(self) -> Dict[str, object]:
        return {
            "previews": len(self._rows),
            "images": sum(r.image_count for r in self._rows),
            "external_calls": sum(r.external_calls for r in self._rows),
        }
