"""Conversation Telemetry Bridge — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.telemetry_collector import TelemetryCollector
from sam.runtime_kernel.metrics_aggregator import MetricsAggregator
from sam.runtime_kernel.telemetry_reporter import TelemetryReporter


class ConversationTelemetry:
    def __init__(self, collector: TelemetryCollector, aggregator: MetricsAggregator,
                 reporter: TelemetryReporter) -> None:
        self._collector = collector
        self._aggregator = aggregator
        self._reporter = reporter

    def get_collector(self) -> TelemetryCollector:
        return self._collector

    def get_aggregator(self) -> MetricsAggregator:
        return self._aggregator

    def get_reporter(self) -> TelemetryReporter:
        return self._reporter

    def describe_layers(self) -> List[str]:
        return ["collector", "aggregator", "reporter"]

    def count_layers(self) -> int:
        return 3

    def get_metric_count(self) -> int:
        return self._collector.count_metrics()

    def get_sample_count(self) -> int:
        return self._collector.count_samples()


class DashboardTelemetry:
    def __init__(self, collector: TelemetryCollector, aggregator: MetricsAggregator) -> None:
        self._collector = collector
        self._aggregator = aggregator

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Telemetry Engine",
            description=f"{self._collector.count_metrics()} metrics",
            status="ready",
            metrics={"metrics": self._collector.count_metrics(),
                     "samples": self._collector.count_samples()},
            items=["collector", "aggregator", "reporter"],
        )

    def collector_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Telemetry Collector",
            description=f"{self._collector.count_metrics()} metrics",
            status="ready",
            metrics={"metrics": self._collector.count_metrics(),
                     "samples": self._collector.count_samples()},
            items=["metrics", "samples"],
        )

    def aggregator_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Metrics Aggregator",
            description="Aggregation",
            status="ready",
            metrics={"metrics": self._collector.count_metrics()},
            items=["avg", "min", "max"],
        )

    def reporter_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Telemetry Reporter",
            description="Reports",
            status="ready",
            metrics={"samples": self._collector.count_samples()},
            items=["reports"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Telemetry Summary",
            description="Ringkasan telemetri",
            status="ready",
            metrics={"layers": 3, "metrics": self._collector.count_metrics()},
            items=["collector", "aggregator", "reporter"],
        )
