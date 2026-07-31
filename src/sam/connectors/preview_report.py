"""Preview Report — engine laporan preview.

Sprint 119 — Connector Preview.
Laporan ringkasan preview (read-only, immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .preview_result import PreviewResult


@dataclass(frozen=True)
class PreviewReport:
    """Laporan hasil preview."""
    connector_id: str
    successes: int = 0
    failures: int = 0
    total_external_calls: int = 0
    details: List[str] = field(default_factory=list)


class PreviewReporter:
    """Bangun laporan preview."""

    def report(self, results: List[PreviewResult]) -> PreviewReport:
        connector_id = results[0].connector_id if results else ""
        successes = sum(1 for r in results if r.success)
        calls = sum(r.external_calls for r in results)
        details = [r.message for r in results]
        return PreviewReport(connector_id, successes, len(results) - successes,
                             calls, details)
