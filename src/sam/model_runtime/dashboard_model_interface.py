"""Dashboard Model Interface — bridge dashboard <-> model interface (Sprint 240).

Program B — Model Runtime Integration.
Read-only bridge; tidak mengenal provider.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .model_request import ModelRequest
from .model_response import ModelResponse


@dataclass(frozen=True)
class DashboardInterfaceRow:
    """Satu baris ringkasan pada dashboard interface (immutable)."""
    row_id: str
    request_id: str
    task: str
    ok: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "row_id": self.row_id,
            "request_id": self.request_id,
            "task": self.task,
            "ok": self.ok,
            "external_calls": self.external_calls,
        }


class DashboardModelInterface:
    """Bridge dashboard <-> model interface. Read-only, no provider."""

    def __init__(self) -> None:
        self._rows: List[DashboardInterfaceRow] = []

    def add(self, request: ModelRequest, response: ModelResponse) -> None:
        row = DashboardInterfaceRow(
            row_id=f"row-{len(self._rows) + 1}",
            request_id=request.request_id,
            task=request.task,
            ok=response.ok,
            external_calls=response.external_calls,
        )
        self._rows.append(row)

    def rows(self) -> List[DashboardInterfaceRow]:
        return list(self._rows)

    def summary(self) -> Dict[str, object]:
        ok = sum(1 for r in self._rows if r.ok)
        return {
            "total": len(self._rows),
            "ok": ok,
            "failed": len(self._rows) - ok,
            "external_calls": sum(r.external_calls for r in self._rows),
        }

    def as_dict(self) -> Dict[str, object]:
        return {
            "rows": [r.as_dict() for r in self._rows],
            "summary": self.summary(),
        }
