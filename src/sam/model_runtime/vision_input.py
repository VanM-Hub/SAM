"""Vision Input — representasi input gambar (Sprint 244).

Program B — Model Runtime Integration.
Hanya representasi metadata gambar; tidak membaca/pakai isi biner. Preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class VisionInput:
    """Representasi input gambar (immutable). Tidak menahan piksel asli."""
    image_id: str
    media_type: str = "image/png"  # image/png | image/jpeg | image/webp
    width: int = 0
    height: int = 0
    description: str = ""
    note: str = "representation only - no pixel data held"

    def as_dict(self) -> dict:
        return {
            "image_id": self.image_id,
            "media_type": self.media_type,
            "width": self.width,
            "height": self.height,
            "description": self.description,
            "note": self.note,
        }
