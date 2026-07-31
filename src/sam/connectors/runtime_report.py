"""Runtime Report — engine laporan runtime connector.

Sprint 121 — Connector Runtime.
Laporan ringkasan runtime (read-only, immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .runtime import ConnectorRuntime


@dataclass(frozen=True)
class RuntimeReport:
    """Laporan runtime connector."""
    ready: bool = False
    stage_count: int = 0
    detail: str = ""


class RuntimeReporter:
    """Bangun laporan runtime."""

    def __init__(self, runtime: ConnectorRuntime) -> None:
        self._runtime = runtime

    def report(self) -> RuntimeReport:
        rd = self._runtime.readiness()
        return RuntimeReport(rd.ready, len(rd.checks),
                             f"{sum(1 for c in rd.checks if c.ok)}/{len(rd.checks)} stages ok")
