"""Telemetry Collector — pengumpul metrik."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_telemetry import TelemetryMetric, TelemetrySample


class TelemetryCollector:
    """Collector telemetri — preview-only."""

    def __init__(self) -> None:
        self._samples: Dict[str, TelemetrySample] = {}
        self._metrics: List[TelemetryMetric] = []

    def record_metric(self, metric: TelemetryMetric) -> None:
        self._metrics.append(metric)

    def create_sample(self, sample_id: str, timestamp: float,
                      metrics: List[TelemetryMetric] = None) -> TelemetrySample:
        metrics = metrics or []
        sample = TelemetrySample(sample_id, metrics, timestamp)
        self._samples[sample_id] = sample
        return sample

    def get_sample(self, sample_id: str) -> TelemetrySample | None:
        return self._samples.get(sample_id)

    def count_metrics(self) -> int:
        return len(self._metrics)

    def count_samples(self) -> int:
        return len(self._samples)

    def get_all_metrics(self) -> List[TelemetryMetric]:
        return list(self._metrics)
