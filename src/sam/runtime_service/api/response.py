"""APIResponse (Sprint 267).

Program D - Runtime Services & Deployment.
Response internal (immutable). Belum HTTP.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class APIResponse:
    """Response internal API (immutable, sync)."""
    request_id: str
    status: str = "ok"  # ok | error
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def is_ok(self) -> bool:
        return self.status == "ok" and self.error is None

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "data": dict(self.data),
            "error": self.error,
        }
