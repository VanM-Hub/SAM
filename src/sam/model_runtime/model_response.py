"""Model Response — response generik model (Sprint 240).

Program B — Model Runtime Integration.
Generik, tidak mengenal provider. Immutable, preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .model_context import ModelContext
from .model_message import ModelMessage


@dataclass(frozen=True)
class ModelResponse:
    """Response generik model (immutable)."""
    response_id: str
    request_id: str
    ok: bool = True
    content: str = ""
    messages: List[ModelMessage] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    mode: str = "preview"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "response_id": self.response_id,
            "request_id": self.request_id,
            "ok": self.ok,
            "content": self.content,
            "messages": [m.as_dict() for m in self.messages],
            "usage": dict(self.usage),
            "error_code": self.error_code,
            "error_message": self.error_message,
            "mode": self.mode,
            "external_calls": self.external_calls,
        }
