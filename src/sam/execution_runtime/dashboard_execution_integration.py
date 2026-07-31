"""Dashboard Execution Integration (Sprint 259).

Program C - Real Execution Runtime.
Read-only bridge: ringkasan integrasi execution untuk dashboard.
"""
from __future__ import annotations
from typing import Dict, List

from .execution_integration import ExecutionIntegration, ExecutionIntegrationResult


class DashboardExecutionIntegration:
    """Bridge execution integration <-> dashboard. Read-only, no network."""

    def __init__(self, integration: ExecutionIntegration | None = None) -> None:
        self._integration = integration or ExecutionIntegration()
        self._rows: List[ExecutionIntegrationResult] = []

    def add(self, result: ExecutionIntegrationResult) -> None:
        self._rows.append(result)

    def rows(self) -> List[dict]:
        return [r.as_dict() for r in self._rows]

    def pipeline(self) -> List[str]:
        return self._integration.pipeline()

    def summary(self) -> Dict[str, object]:
        return {
            "integrations": len(self._rows),
            "stages_total": sum(len(r.stages) for r in self._rows),
            "external_calls": sum(r.external_calls for r in self._rows),
        }
