"""Dashboard Execution Request (Sprint 251).

Program C - Real Execution Runtime.
Read-only bridge: ringkasan request eksekusi untuk dashboard.
"""
from __future__ import annotations
from typing import Dict, List

from .execution_request import ExecutionRequest


class DashboardExecutionRequest:
    """Bridge execution request <-> dashboard. Read-only, no network."""

    def __init__(self) -> None:
        self._rows: List[dict] = []

    def add(self, request: ExecutionRequest) -> None:
        self._rows.append(request.as_dict())

    def rows(self) -> List[dict]:
        return list(self._rows)

    def summary(self) -> Dict[str, object]:
        return {
            "requests": len(self._rows),
            "execute_pending": sum(1 for r in self._rows if r["mode"] == "execute" and not r["approved"]),
            "external_calls": 0,
        }
