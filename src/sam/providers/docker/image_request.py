"""Docker Image Request — frozen DTO request image (preview).

Sprint 148 — Docker Provider.
Representasi request image tanpa eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ImageRequest:
    """Request image (immutable, preview-only)."""
    request_id: str
    reference: str
    operation: str = "image_pull"
    tag: Optional[str] = None

    def is_valid(self) -> bool:
        return bool(self.request_id) and bool(self.reference)
