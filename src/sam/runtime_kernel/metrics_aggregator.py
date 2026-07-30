"""Metrics Aggregator — agregasi metrik."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_telemetry import TelemetryMetric, MetricSummary


class MetricsAggregator:
    """Agregator metrik — preview-only."""

    def summarize(self, metric_name: str, metrics: List[TelemetryMetric]) -> MetricSummary:
        filtered = [m for m in metrics if m.name == metric_name]
        if not filtered:
            return MetricSummary(f"sum_{metric_name}", metric_name, count=0)
        values = [m.value for m in filtered]
        return MetricSummary(
            summary_id=f"sum_{metric_name}",
            metric_name=metric_name,
            avg=sum(values) / len(values),
            min=min(values),
            max=max(values),
            count=len(values),
        )

    def group_by_subsystem(self, metrics: List[TelemetryMetric]) -> Dict[str, List[TelemetryMetric]]:
        groups: Dict[str, List[TelemetryMetric]] = {}
        for m in metrics:
            if m.subsystem not in groups:
                groups[m.subsystem] = []
            groups[m.subsystem].append(m)
        return groups
