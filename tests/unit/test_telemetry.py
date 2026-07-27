"""
Unit tests — Telemetry Service, Models, Collector (Phase 1)
"""

import pytest
import asyncio
from datetime import datetime
from sam.telemetry.models import (
    TelemetryEvent, TelemetrySeverity, RuntimeMetrics, MetricPoint,
)
from sam.telemetry.service import TelemetryService
from sam.telemetry.collector import MetricsCollector


class TestTelemetryModels:
    def test_telemetry_event_minimal(self):
        event = TelemetryEvent(event_name="test.event")
        assert event.event_name == "test.event"
        assert event.severity == TelemetrySeverity.INFO
        assert event.component == "runtime"
        assert len(event.event_id) == 12  # uuid hex[:12]

    def test_telemetry_event_custom(self):
        event = TelemetryEvent(
            event_name="custom.event",
            severity=TelemetrySeverity.ERROR,
            component="test",
            runtime_state="running",
            correlation_id="corr-001",
            session_id="sess-001",
            payload={"key": "value"},
        )
        assert event.severity == TelemetrySeverity.ERROR
        assert event.correlation_id == "corr-001"
        assert event.payload["key"] == "value"

    def test_severity_enum_values(self):
        assert TelemetrySeverity.TRACE.value == "trace"
        assert TelemetrySeverity.CRITICAL.value == "critical"

    def test_metric_point_defaults(self):
        mp = MetricPoint(name="cpu_usage", value=42.5)
        assert mp.name == "cpu_usage"
        assert mp.value == 42.5
        assert mp.labels == {}

    def test_runtime_metrics_defaults(self):
        m = RuntimeMetrics()
        assert m.cpu_percent == 0.0
        assert m.health_score == 100.0
        assert m.workflow_count == 0


class TestTelemetryService:
    def test_init_empty(self):
        svc = TelemetryService()
        assert len(svc.events) == 0
        assert svc.get_metrics() is None

    def test_emit_event(self):
        svc = TelemetryService()
        svc.emit_event(
            event_name="test.event",
            severity=TelemetrySeverity.INFO,
            component="test",
        )
        assert len(svc.events) == 1
        assert svc.events[0].event_name == "test.event"

    def test_emit(self):
        svc = TelemetryService()
        event = TelemetryEvent(event_name="direct.event")
        svc.emit(event)
        assert len(svc.events) == 1

    def test_get_events_limit(self):
        svc = TelemetryService()
        for i in range(20):
            svc.emit_event(event_name=f"event.{i}")
        events = svc.get_events(limit=5)
        assert len(events) == 5

    def test_get_events_severity_filter(self):
        svc = TelemetryService()
        svc.emit_event(event_name="info.1", severity=TelemetrySeverity.INFO)
        svc.emit_event(event_name="error.1", severity=TelemetrySeverity.ERROR)
        svc.emit_event(event_name="info.2", severity=TelemetrySeverity.INFO)

        errors = svc.get_events(severity=TelemetrySeverity.ERROR)
        assert len(errors) == 1
        assert errors[0].event_name == "error.1"

        infos = svc.get_events(severity=TelemetrySeverity.INFO)
        assert len(infos) == 2

    def test_clear(self):
        svc = TelemetryService()
        svc.emit_event(event_name="test")
        svc.clear()
        assert len(svc.events) == 0
        assert svc.get_metrics() is None

    def test_max_events_respected(self):
        svc = TelemetryService(max_events=5)
        for i in range(10):
            svc.emit_event(event_name=f"event.{i}")
        assert len(svc.events) == 5
        assert svc.events[0].event_name == "event.5"

    def test_record_metrics(self):
        svc = TelemetryService()
        metrics = RuntimeMetrics(cpu_percent=45.0, memory_mb=1024.0)
        svc.record_metrics(metrics)
        assert svc.get_metrics() is not None
        assert svc.get_metrics().cpu_percent == 45.0
        assert len(svc.metrics_history) == 1

    def test_get_metrics_history(self):
        svc = TelemetryService()
        for i in range(5):
            svc.record_metrics(RuntimeMetrics(cpu_percent=float(i)))
        history = svc.get_metrics_history(limit=3)
        assert len(history) == 3
        assert history[-1].cpu_percent == 4.0

    def test_follow_yields_existing(self):
        svc = TelemetryService()
        svc.emit_event(event_name="e1")
        svc.emit_event(event_name="e2")
        events = list(svc.follow())
        assert len(events) == 2


class TestMetricsCollector:
    @pytest.mark.asyncio
    async def test_collect_returns_runtime_metrics(self):
        """Collect harus return RuntimeMetrics tanpa error."""
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        collector = MetricsCollector(coord)
        metrics = await collector.collect()
        assert metrics.cpu_percent >= 0
        assert metrics.memory_mb >= 0
        assert metrics.workflow_count == 2
        assert metrics.plugin_count == 14

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Start harus berjalan, stop harus memberhentikan loop."""
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        collector = MetricsCollector(coord, interval=999)  # long interval
        task = asyncio.ensure_future(collector.start())
        await asyncio.sleep(0.1)
        await collector.stop()
        assert not collector._running

    @pytest.mark.asyncio
    async def test_uptime_zero_when_no_start_time(self):
        """Uptime harus 0 jika start_time tidak diset."""
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        coord.start_time = None
        collector = MetricsCollector(coord)
        metrics = await collector.collect()
        assert metrics.uptime_seconds == 0.0
