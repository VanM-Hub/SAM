"""Vision Validator — validasi representasi vision (Sprint 244).

Program B — Model Runtime Integration.
Deterministik, no inference, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .vision_request import VisionRequest


@dataclass(frozen=True)
class VisionValidation:
    """Hasil validasi (immutable)."""
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"valid": self.valid, "errors": list(self.errors),
                "warnings": list(self.warnings)}


class VisionValidator:
    """Validator representasi vision. Read-only."""

    VALID_MEDIA = ("image/png", "image/jpeg", "image/webp")

    def validate_request(self, request: VisionRequest) -> VisionValidation:
        errors: List[str] = []
        if not request.request_id:
            errors.append("request_id required")
        if not request.images:
            errors.append("images cannot be empty")
        for image in request.images:
            if image.media_type not in self.VALID_MEDIA:
                errors.append(f"invalid media_type: {image.media_type}")
            if not image.image_id:
                errors.append("image_id required")
        if request.external_calls != 0:
            warnings = ["external_calls should be 0 in preview"]
        else:
            warnings = []
        return VisionValidation(valid=not errors, errors=errors, warnings=warnings)
