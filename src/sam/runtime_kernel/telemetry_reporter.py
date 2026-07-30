"""Telemetry Reporter — pembuat laporan."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_telemetry import TelemetrySample, TelemetryReport


class TelemetryReporter:
    """Pembuat laporan — preview-only."""

    def generate_report(self, report_id: str, timestamp: float,
                        samples: List[TelemetrySample]) -> TelemetryReport:
        total = sum(len(s.metrics) for s in samples)
        return TelemetryReport(report_id, timestamp, samples, total)

    def count_samples(self, samples: List[TelemetrySample]) -> int:
        return len(samples)
