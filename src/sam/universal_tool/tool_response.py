"""Tool Response Model & Result Verification - WP-25/WP-26 (MISSION-5.2 / IP-5.2-003).

Model response Tool + verifikasi hasil Tool.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class ToolResultState(str, Enum):
    """Keadaan hasil Tool."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ToolResponse:
    """Response Tool universal."""

    request_id: str
    tool_id: str
    state: ToolResultState = ToolResultState.UNKNOWN
    data: Optional[Dict[str, Any]] = None
    error: str = ""
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    @property
    def successful(self) -> bool:
        return self.state == ToolResultState.SUCCESS

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "tool_id": self.tool_id,
            "state": self.state.value,
            "data": self.data,
            "error": self.error,
            "metadata": dict(self.metadata),
            "successful": self.successful,
            "created_at": self.created_at,
        }


class ToolResultVerifier:
    """Memverifikasi hasil Tool terhadap ekspektasi."""

    def verify(self, response: ToolResponse, *, expected_keys: Tuple[str, ...] = ()) -> bool:
        if not response.successful:
            return False
        if not expected_keys:
            return response.data is not None
        if response.data is None:
            return False
        return all(k in response.data for k in expected_keys)
