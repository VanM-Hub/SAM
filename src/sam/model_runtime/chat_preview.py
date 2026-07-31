"""Chat Preview — preview deterministik chat (Sprint 241).

Program B — Model Runtime Integration.
Preview only; tidak ada network call. external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..model_runtime.model_request import ModelRequest
from ..model_runtime.model_message import ModelMessage


@dataclass(frozen=True)
class ChatPreview:
    """Hasil preview chat (immutable, deterministik)."""
    preview_id: str
    request_id: str
    messages: List[ModelMessage] = field(default_factory=list)
    detected_roles: List[str] = field(default_factory=list)
    estimated_tokens: int = 0
    plan_note: str = "preview only - no inference performed"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "preview_id": self.preview_id,
            "request_id": self.request_id,
            "messages": [m.as_dict() for m in self.messages],
            "detected_roles": list(self.detected_roles),
            "estimated_tokens": self.estimated_tokens,
            "plan_note": self.plan_note,
            "external_calls": self.external_calls,
        }


class ChatPreviewEngine:
    """Mesin preview chat. Deterministik, no-network."""

    def preview(self, request: ModelRequest) -> ChatPreview:
        roles = []
        tokens = 0
        for m in request.context.messages:
            roles.append(m.role)
            tokens += len(m.content.split()) + 4  # estimasi deterministik kasar
        # plus system
        if request.context.system:
            tokens += len(request.context.system.split()) + 4
        return ChatPreview(
            preview_id=f"pv-{request.request_id}",
            request_id=request.request_id,
            messages=list(request.context.messages),
            detected_roles=_dedup(roles),
            estimated_tokens=tokens,
            external_calls=0,
        )


def _dedup(items: List[str]) -> List[str]:
    seen: List[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen
