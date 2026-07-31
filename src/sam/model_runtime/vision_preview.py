"""Vision Preview — preview deterministik vision (Sprint 244).

Program B — Model Runtime Integration.
Representasi image input; tidak inference. Preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .vision_request import VisionRequest


@dataclass(frozen=True)
class VisionPreview:
    """Preview vision (immutable, representasi)."""
    preview_id: str
    request_id: str
    image_count: int = 0
    note: str = "representation only - no inference performed"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "preview_id": self.preview_id,
            "request_id": self.request_id,
            "image_count": self.image_count,
            "note": self.note,
            "external_calls": self.external_calls,
        }


class VisionPreviewEngine:
    """Preview vision. Menyiapkan representasi input, tanpa inferensi."""

    def preview(self, request: VisionRequest) -> VisionPreview:
        return VisionPreview(
            preview_id=f"pv-{request.request_id}",
            request_id=request.request_id,
            image_count=len(request.images),
            note="representation only - no inference performed",
            external_calls=0,
        )
