"""Vision Summary — ringkasan vision (Sprint 244).

Program B — Model Runtime Integration.
Representasi ringkasan; tidak inference. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .vision_input import VisionInput


@dataclass(frozen=True)
class VisionSummary:
    """Ringkasan vision (immutable, representasi)."""
    summary_id: str
    images: List[VisionInput] = field(default_factory=list)
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "summary_id": self.summary_id,
            "image_count": len(self.images),
            "images": [i.as_dict() for i in self.images],
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }
