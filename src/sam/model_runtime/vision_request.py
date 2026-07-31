"""Vision Request — request vision (Sprint 244).

Program B — Model Runtime Integration.
Representasi image input; tidak inference. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .vision_input import VisionInput


@dataclass(frozen=True)
class VisionRequest:
    """Request vision (immutable). Holds image representations only."""
    request_id: str
    prompt: str = ""
    images: List[VisionInput] = field(default_factory=list)
    mode: str = "preview"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "prompt": self.prompt,
            "images": [i.as_dict() for i in self.images],
            "mode": self.mode,
            "external_calls": self.external_calls,
        }
