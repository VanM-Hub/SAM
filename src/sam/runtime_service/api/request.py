"""APIRequest (Sprint 267).

Program D - Runtime Services & Deployment.
Request internal (immutable). Belum HTTP.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class APIRequest:
    """Request internal API (immutable, sync)."""
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)
    request_id: str = "req-0"
    service: str = "runtime"

    def __post_init__(self) -> None:
        if not self.action:
            raise ValueError("action is required")

    def as_dict(self) -> dict:
        return {
            "action": self.action,
            "payload": dict(self.payload),
            "request_id": self.request_id,
            "service": self.service,
        }
