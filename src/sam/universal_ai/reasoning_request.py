"""Reasoning Request - WP-36 (MISSION-5.1 / IP-5.1-004).

Model request untuk reasoning. Immutable setelah dikirim ke Provider.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple

from .context_resolution import ResolvedReasoningContext


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ReasoningRequest:
    """Request reasoning lengkap (immutable)."""

    request_id: str
    conversation_id: str = ""
    objective: str = ""
    resolved_context: "ResolvedReasoningContext | None" = None
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)
    constraints: Tuple[str, ...] = field(default_factory=tuple)
    provider_id: str = ""
    model_id: str = ""
    timestamp: str = field(default_factory=_now_utc)

    @property
    def is_immutable(self) -> bool:
        return True

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "conversation_id": self.conversation_id,
            "objective": self.objective,
            "resolved_context": (
                self.resolved_context.as_dict() if self.resolved_context else None
            ),
            "evidence_refs": list(self.evidence_refs),
            "constraints": list(self.constraints),
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "timestamp": self.timestamp,
        }
