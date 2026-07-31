"""Dashboard Integration — bridge dashboard <-> model integration (Sprint 249).

Program B — Model Runtime Integration.
Read-only bridge ke pipeline akhir. Preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .model_integration import ModelIntegration, ModelIntegrationResult


@dataclass(frozen=True)
class DashboardIntegrationRow:
    """Satu baris integrasi pada dashboard (immutable)."""
    row_id: str
    integration_id: str
    stage_count: int = 0
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "row_id": self.row_id,
            "integration_id": self.integration_id,
            "stage_count": self.stage_count,
            "external_calls": self.external_calls,
        }


class DashboardIntegration:
    """Bridge dashboard <-> model integration. Read-only, no-network."""

    def __init__(self, integration: ModelIntegration | None = None) -> None:
        self._integration = integration or ModelIntegration()
        self._rows: List[DashboardIntegrationRow] = []

    def add(self, result: ModelIntegrationResult) -> None:
        self._rows.append(DashboardIntegrationRow(
            row_id=f"dint-{len(self._rows) + 1}",
            integration_id=result.integration_id,
            stage_count=len(result.stages),
            external_calls=result.external_calls,
        ))

    def rows(self) -> List[DashboardIntegrationRow]:
        return list(self._rows)

    def pipeline(self) -> List[str]:
        return self._integration.pipeline()

    def summary(self) -> Dict[str, object]:
        return {
            "integrations": len(self._rows),
            "stages_total": sum(r.stage_count for r in self._rows),
            "external_calls": sum(r.external_calls for r in self._rows),
        }
