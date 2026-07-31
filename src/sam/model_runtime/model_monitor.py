"""Model Monitor — monitor runtime model (Sprint 246).

Program B — Model Runtime Integration.
Read-only monitoring, deterministik, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .model_report import ModelReport


@dataclass(frozen=True)
class ModelHealth:
    """Status kesehatan model (immutable)."""
    healthy: bool = True
    detail: str = "ok"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "healthy": self.healthy,
            "detail": self.detail,
            "external_calls": self.external_calls,
        }


@dataclass(frozen=True)
class ModelMetric:
    """Satu metrik (immutable)."""
    name: str
    value: float = 0.0

    def as_dict(self) -> dict:
        return {"name": self.name, "value": self.value}


class ModelMonitor:
    """Monitor model. Read-only, no-network."""

    def __init__(self) -> None:
        self._reports: List[ModelReport] = []

    def observe(self, report: ModelReport) -> None:
        self._reports.append(report)

    def health(self) -> ModelHealth:
        failures = sum(1 for r in self._reports if not r.ok)
        if failures:
            return ModelHealth(healthy=False, detail=f"{failures} failed reports")
        return ModelHealth(healthy=True, detail="ok", external_calls=0)

    def metrics(self) -> List[ModelMetric]:
        total = len(self._reports)
        ok = sum(1 for r in self._reports if r.ok)
        return [
            ModelMetric("reports", total),
            ModelMetric("ok", ok),
            ModelMetric("failed", total - ok),
        ]

    def report_count(self) -> int:
        return len(self._reports)
