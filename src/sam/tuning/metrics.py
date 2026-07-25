"""Performance Metrics — Sprint 28 Fase 3.

Defines PerformanceMetric model and MetricsCollector for collecting
runtime system metrics (CPU, memory, queue depth, execution duration, etc.)
with trend analysis.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.evolution.params import ParamManager


logger = structlog.get_logger()


@dataclass
class PerformanceMetric:
    """A single sampled performance data point.

    Attributes:
        id: Unique identifier (UUID).
        name: Metric name like 'cpu_usage', 'memory_usage', 'queue_depth',
              'execution_duration', 'cache_hit_ratio', 'connection_pool_utilization',
              'throughput', 'error_rate', 'latency_p99'.
        value: Numeric value of the metric.
        timestamp: When the sample was taken (UTC).
        source: The component/capability/workflow that produced the metric.
        metadata: Additional context (e.g. {"unit":"percent"}).
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    value: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects runtime system performance metrics.

    Supports:
      - collect(): gather current system metrics (CPU, memory, queue, etc.)
      - get_trend(): retrieve recent values for a metric name
      - window-based trend analysis
    """

    # Hard-coded metric names for reference
    METRIC_CPU_USAGE = "cpu_usage"
    METRIC_MEMORY_USAGE = "memory_usage"
    METRIC_QUEUE_DEPTH = "queue_depth"
    METRIC_EXECUTION_DURATION = "execution_duration"
    METRIC_CACHE_HIT_RATIO = "cache_hit_ratio"
    METRIC_CONNECTION_POOL_UTIL = "connection_pool_utilization"
    METRIC_THROUGHPUT = "throughput"
    METRIC_ERROR_RATE = "error_rate"
    METRIC_LATENCY_P99 = "latency_p99"
    METRIC_BATCH_SIZE = "batch_size"
    METRIC_TIMEOUT_RATIO = "timeout_ratio"
    METRIC_THREAD_POOL_UTIL = "thread_pool_utilization"

    def __init__(self) -> None:
        self._history: Dict[str, List[PerformanceMetric]] = {}
        self.logger = logger.bind(component="MetricsCollector")

    def _store(self, metric: PerformanceMetric) -> None:
        """Store metric in local history buffer."""
        if metric.name not in self._history:
            self._history[metric.name] = []
        self._history[metric.name].append(metric)
        # Keep only last 10_000 per metric
        if len(self._history[metric.name]) > 10_000:
            self._history[metric.name] = self._history[metric.name][-5000:]

    def _read_system_metric(self, metric_name: str) -> Optional[float]:
        """Read a single system metric (CPU, memory, etc.) using platform APIs.

        Returns None if the metric cannot be read.
        """
        try:
            if metric_name == self.METRIC_CPU_USAGE:
                import psutil
                return psutil.cpu_percent(interval=0.1)
            if metric_name == self.METRIC_MEMORY_USAGE:
                import psutil
                mem = psutil.virtual_memory()
                return mem.percent
            if metric_name == self.METRIC_THREAD_POOL_UTIL:
                import threading
                active = threading.active_count()
                # Rough estimate; no standard max for Python threads
                return float(active)
        except ImportError:
            pass
        except Exception:
            pass
        return None

    async def collect(self) -> List[PerformanceMetric]:
        """Collect current system metrics.

        Returns a list of PerformanceMetric instances sampled now.
        """
        now = datetime.now(timezone.utc)
        metrics: List[PerformanceMetric] = []
        source = "system"

        cpu = self._read_system_metric(self.METRIC_CPU_USAGE)
        if cpu is not None:
            m = PerformanceMetric(
                name=self.METRIC_CPU_USAGE, value=cpu,
                timestamp=now, source=source,
                metadata={"unit": "percent"},
            )
            metrics.append(m)
            self._store(m)

        mem = self._read_system_metric(self.METRIC_MEMORY_USAGE)
        if mem is not None:
            m = PerformanceMetric(
                name=self.METRIC_MEMORY_USAGE, value=mem,
                timestamp=now, source=source,
                metadata={"unit": "percent"},
            )
            metrics.append(m)
            self._store(m)

        thread = self._read_system_metric(self.METRIC_THREAD_POOL_UTIL)
        if thread is not None:
            m = PerformanceMetric(
                name=self.METRIC_THREAD_POOL_UTIL, value=thread,
                timestamp=now, source=source,
                metadata={"unit": "threads"},
            )
            metrics.append(m)
            self._store(m)

        self.logger.debug("Metrics collected", count=len(metrics))
        return metrics

    def record(
        self,
        name: str,
        value: float,
        source: str = "manual",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PerformanceMetric:
        """Manually record a metric value.

        Useful for injecting metrics from capabilities/workflows.
        """
        metric = PerformanceMetric(
            name=name, value=value,
            timestamp=datetime.now(timezone.utc),
            source=source,
            metadata=metadata or {},
        )
        self._store(metric)
        return metric

    def get_trend(
        self,
        metric_name: str,
        window: int = 60,
    ) -> List[float]:
        """Return recent values for a metric (last `window` samples).

        Args:
            metric_name: Name of the metric.
            window: How many recent samples to include.

        Returns:
            List of float values, newest last (or empty if none).
        """
        history = self._history.get(metric_name, [])
        if not history or window <= 0:
            return []
        samples = history[-window:]
        return [m.value for m in samples]

    def get_latest(self, metric_name: str) -> Optional[PerformanceMetric]:
        """Get the most recent sample for a metric."""
        history = self._history.get(metric_name, [])
        if not history:
            return None
        return history[-1]

    def get_all_metric_names(self) -> List[str]:
        """Return names of all stored metrics."""
        return list(self._history.keys())

    def clear(self) -> None:
        """Clear all stored metrics."""
        self._history.clear()

    def metric_count(self) -> int:
        """Total stored samples."""
        return sum(len(v) for v in self._history.values())
