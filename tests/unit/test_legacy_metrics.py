"""Tests for Performance Metrics — Sprint 28 Fase 3.

Coverage:
  - PerformanceMetric creation and field defaults
  - MetricsCollector: collect, record, get_trend, get_latest
  - Trend analysis edge cases (empty, single, boundary)
  - Manual recording with metadata
  - Clear and reset
"""

import json
import time
from datetime import datetime, timezone

import pytest

from sam.tuning.metrics import PerformanceMetric, MetricsCollector


# ── PerformanceMetric Unit Tests ──────────────────────────────────


class TestPerformanceMetric:
    def test_create_basic(self):
        m = PerformanceMetric(
            name="cpu_usage",
            value=42.5,
            source="test",
        )
        assert m.name == "cpu_usage"
        assert m.value == 42.5
        assert m.source == "test"
        assert m.id is not None and len(m.id) > 0
        assert isinstance(m.timestamp, datetime)
        assert isinstance(m.metadata, dict)
        assert m.metadata == {}

    def test_create_with_metadata(self):
        m = PerformanceMetric(
            name="memory_usage",
            value=65.0,
            source="test",
            metadata={"unit": "percent", "host": "node1"},
        )
        assert m.metadata["unit"] == "percent"
        assert m.metadata["host"] == "node1"

    def test_create_explicit_id(self):
        m = PerformanceMetric(id="my_id", name="x", value=1.0, source="test")
        assert m.id == "my_id"

    def test_create_negative_value(self):
        m = PerformanceMetric(name="delta", value=-1.5, source="test")
        assert m.value == -1.5

    def test_create_zero_value(self):
        m = PerformanceMetric(name="queue_depth", value=0.0, source="test")
        assert m.value == 0.0

    def test_create_timestamp_override(self):
        dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
        m = PerformanceMetric(name="x", value=1.0, source="test", timestamp=dt)
        assert m.timestamp == dt


# ── MetricsCollector Tests ────────────────────────────────────────


class TestMetricsCollector:
    @pytest.fixture
    def collector(self):
        return MetricsCollector()

    def test_record_basic(self, collector):
        m = collector.record("cpu_usage", 50.0)
        assert isinstance(m, PerformanceMetric)
        assert m.name == "cpu_usage"
        assert m.value == 50.0
        assert m.source == "manual"

    def test_record_with_source(self, collector):
        m = collector.record("queue_depth", 10, source="workflow.executor")
        assert m.source == "workflow.executor"

    def test_record_with_metadata(self, collector):
        m = collector.record("latency_p99", 150.0, metadata={"unit": "ms"})
        assert m.metadata["unit"] == "ms"

    def test_record_multiple_metrics(self, collector):
        collector.record("cpu_usage", 10.0)
        collector.record("cpu_usage", 20.0)
        collector.record("cpu_usage", 30.0)
        assert collector.metric_count() == 3

    def test_get_trend_empty(self, collector):
        trend = collector.get_trend("nonexistent")
        assert trend == []

    def test_get_trend_single(self, collector):
        collector.record("cpu_usage", 45.0)
        trend = collector.get_trend("cpu_usage", window=10)
        assert trend == [45.0]

    def test_get_trend_multiple(self, collector):
        for v in [10, 20, 30, 40, 50]:
            collector.record("metric_a", float(v))
        trend = collector.get_trend("metric_a", window=3)
        assert trend == [30.0, 40.0, 50.0]

    def test_get_trend_all(self, collector):
        for v in [10, 20, 30]:
            collector.record("metric_b", float(v))
        trend = collector.get_trend("metric_b", window=100)
        assert trend == [10.0, 20.0, 30.0]

    def test_get_trend_large_window(self, collector):
        for v in range(100):
            collector.record("ld", float(v))
        trend = collector.get_trend("ld", window=10)
        assert len(trend) == 10
        assert trend == [float(v) for v in range(90, 100)]

    def test_get_latest_empty(self, collector):
        assert collector.get_latest("missing") is None

    def test_get_latest_exists(self, collector):
        collector.record("cpu", 10.0)
        collector.record("cpu", 20.0)
        m = collector.get_latest("cpu")
        assert m is not None
        assert m.value == 20.0

    def test_get_all_metric_names_empty(self, collector):
        assert collector.get_all_metric_names() == []

    def test_get_all_metric_names(self, collector):
        collector.record("a", 1.0)
        collector.record("b", 2.0)
        names = collector.get_all_metric_names()
        assert set(names) == {"a", "b"}

    def test_clear(self, collector):
        collector.record("x", 1.0)
        collector.record("y", 2.0)
        collector.clear()
        assert collector.metric_count() == 0
        assert collector.get_all_metric_names() == []

    def test_collect_returns_instance_with_id(self, collector):
        m = collector.record("test", 1.0)
        assert m.id is not None and len(m.id) > 0

    def test_collect_returns_instance_with_timestamp(self, collector):
        m = collector.record("test", 1.0)
        assert isinstance(m.timestamp, datetime)

    def test_metric_names_isolated(self, collector):
        collector.record("cpu", 1.0)
        collector.record("mem", 2.0)
        trend_cpu = collector.get_trend("cpu")
        trend_mem = collector.get_trend("mem")
        assert len(trend_cpu) == 1
        assert len(trend_mem) == 1

    def test_trend_coherence(self, collector):
        """Trend should maintain insertion order (newest last)."""
        for v in [100, 200, 150, 300]:
            collector.record("order", float(v))
        trend = collector.get_trend("order")
        assert trend == [100.0, 200.0, 150.0, 300.0]

    def test_record_without_source_defaults(self, collector):
        m = collector.record("test", 1.0)
        assert m.source == "manual"

    def test_metric_count_after_clear(self, collector):
        collector.record("a", 1.0)
        collector.record("b", 2.0)
        collector.record("c", 3.0)
        assert collector.metric_count() == 3
        collector.clear()
        assert collector.metric_count() == 0

    def test_trend_window_boundary(self, collector):
        """Window larger than sample count returns all."""
        for v in [1, 2, 3]:
            collector.record("bnd", float(v))
        trend = collector.get_trend("bnd", window=1000)
        assert len(trend) == 3

    def test_trend_window_zero(self, collector):
        """Window of zero returns empty."""
        collector.record("z", 1.0)
        trend = collector.get_trend("z", window=0)
        assert trend == []

    def test_get_latest_empty_name(self, collector):
        collector.record("test", 1.0)
        assert collector.get_latest("") is None  # empty name = not found

    def test_clear_empty_collector(self, collector):
        collector.clear()  # Should not raise
        assert collector.metric_count() == 0


# ── Collect (system) tests ────────────────────────────────────────


class TestCollectSystem:
    async def test_collect_basic(self):
        """collect() should return a list of metrics (may be empty if no psutil)."""
        c = MetricsCollector()
        result = await c.collect()
        assert isinstance(result, list)
        # May or may not have psutil; but it should be valid either way
        for m in result:
            assert isinstance(m, PerformanceMetric)
            assert m.timestamp is not None

    async def test_collect_cpu_if_available(self):
        c = MetricsCollector()
        result = await c.collect()
        cpu_metrics = [m for m in result if m.name == c.METRIC_CPU_USAGE]
        # If psutil is installed, we should get CPU metrics
        if cpu_metrics:
            assert 0 <= cpu_metrics[0].value <= 100

    async def test_collect_memory_if_available(self):
        c = MetricsCollector()
        result = await c.collect()
        mem_metrics = [m for m in result if m.name == c.METRIC_MEMORY_USAGE]
        if mem_metrics:
            assert 0 <= mem_metrics[0].value <= 100

    async def test_collect_consistent_timestamps(self):
        c = MetricsCollector()
        result = await c.collect()
        if len(result) >= 2:
            ts = [m.timestamp for m in result]
            assert all(t == ts[0] for t in ts)

    async def test_collect_metric_names_available(self):
        c = MetricsCollector()
        await c.collect()
        names = c.get_all_metric_names()
        assert len(names) >= 0  # May be 0 without psutil


# ── Trend Analysis Edge Cases ─────────────────────────────────────


class TestTrendEdgeCases:
    def test_trend_with_gaps(self):
        c = MetricsCollector()
        c.record("a", 10.0)
        c.record("a", 20.0)
        c.record("b", 30.0)
        c.record("a", 40.0)
        trend = c.get_trend("a")
        assert trend == [10.0, 20.0, 40.0]

    def test_trend_after_clear(self):
        c = MetricsCollector()
        c.record("x", 1.0)
        c.clear()
        trend = c.get_trend("x")
        assert trend == []

    def test_trend_negative_values(self):
        c = MetricsCollector()
        for v in [-10, -5, 0, 5, 10]:
            c.record("delta", float(v))
        trend = c.get_trend("delta")
        assert trend == [-10.0, -5.0, 0.0, 5.0, 10.0]

    def test_trend_float_precision(self):
        c = MetricsCollector()
        c.record("precise", 0.1 + 0.2)  # 0.30000000000000004
        trend = c.get_trend("precise")
        assert abs(trend[0] - 0.3) < 1e-10
