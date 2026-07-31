"""Audit Metrics — metrik audit (Sprint 217)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class AuditMetricSample:
    """Sampel metrik immutable."""
    name: str = ""
    value: int = 0


@dataclass(frozen=True)
class AuditMetrics:
    """Metrik immutable."""
    total_records: int = 0
    immutable_records: int = 0
    no_execute: bool = True


class AuditMetricsCollector:
    """Kolektor metrik audit read-only."""

    def collect(self) -> AuditMetrics:
        return AuditMetrics(total_records=0, immutable_records=0, no_execute=True)
