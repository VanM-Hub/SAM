"""Tool Result — hasil tool generik (Sprint 245).

Program B — Model Runtime Integration.
Generic; tidak execute tool. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ToolResult:
    """Hasil tool (immutable). Tidak berasal dari eksekusi nyata."""
    call_id: str
    ok: bool = True
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    executed: bool = False  # preview: tidak pernah dieksekusi
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "ok": self.ok,
            "data": dict(self.data),
            "error": self.error,
            "executed": self.executed,
            "external_calls": self.external_calls,
        }
