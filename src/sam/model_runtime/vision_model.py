"""Vision Model — representasi model vision (Sprint 244).

Program B — Model Runtime Integration.
Representasi image input; tidak inference. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class VisionModel:
    """Model vision (immutable). No inference performed."""
    vision_id: str
    name: str
    accepts_image: bool = True
    max_images_hint: int = 1
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "vision_id": self.vision_id,
            "name": self.name,
            "accepts_image": self.accepts_image,
            "max_images_hint": self.max_images_hint,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }
