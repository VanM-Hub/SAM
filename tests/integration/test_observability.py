"""
Integration tests — Observability (Telemetry + API + CLI)

Tests disesuaikan dengan implementasi aktual TelemetryService / MetricsCollector
(runtime_kernel & sam.telemetry) setelah refactor API.

API aktual:
- TelemetryService.emit(TelemetryEvent)  /  emit_event(name, **metadata)
- TelemetryService.query(filters=None)   /  get_recent(limit)
- MetricsCollector(interval=...)  ->  metrics property, get_summary()
- RuntimeMetrics(cpu_percent, memory_percent, uptime_seconds, ...)
"""

import pytest
from sam.telemetry.models import TelemetryEvent, TelemetrySeverity, RuntimeMetrics
from sam.telemetry.service import TelemetryService
from sam.telemetry.collector import MetricsCollector


class TestTelemetryIntegration:
    def test_emit_and_query_roundtrip(self):
        """Emit events lalu query harus konsisten."""
        svc = TelemetryService(max_events=100)

        svc.emit_event("startup.complete", runtime_state="ready")
        svc.emit_event("workflow.started", severity=TelemetrySeverity.DEBUG, component="workflow")
        svc.emit_event("error.test", severity=TelemetrySeverity.ERROR, component="test")

        # Query all (via query tanpa filter)
        all_events = svc.query()
        assert len(all_events) == 3

        # Query by severity — lewat filter
        errors = svc.query({"severity": TelemetrySeverity.ERROR.value})
        assert len(errors) == 1
        assert errors[0].message == "error.test"

        # Debug events
        debug_events = svc.query({"severity": TelemetrySeverity.DEBUG.value})
        assert len(debug_events) == 1
        assert debug_events[0].message == "workflow.started"

    def test_metrics_roundtrip(self):
        """Record metrics lalu query harus konsisten."""
        from sam.runtime_kernel.telemetry_collector import TelemetryCollector
        from sam.runtime_kernel.runtime_telemetry import TelemetryMetric

        collector = TelemetryCollector()
        collector.record_metric(TelemetryMetric(metric_id="m1", name="cpu_percent", value=25.5))
        collector.record_metric(TelemetryMetric(metric_id="m2", name="cpu_percent", value=50.0))

        assert collector.count_metrics() == 2

        all_metrics = collector.get_all_metrics()
        cpu_vals = [m.value for m in all_metrics if m.name == "cpu_percent"]
        assert cpu_vals == [25.5, 50.0]

    def test_correlation_across_events(self):
        """Events dengan correlation_id yang sama harus bisa dilacak."""
        svc = TelemetryService()
        corr_id = "corr-ops-001"

        svc.emit_event("operation.start", correlation_id=corr_id, component="workflow")
        svc.emit_event("operation.progress", correlation_id=corr_id, component="workflow")
        svc.emit_event("operation.complete", correlation_id=corr_id, component="workflow")

        all_events = svc.query()
        corr_events = [e for e in all_events if e.metadata.get("correlation_id") == corr_id]
        assert len(corr_events) == 3
        assert corr_events[0].message == "operation.start"
        assert corr_events[-1].message == "operation.complete"

    def test_large_batch_preserves_order(self):
        """Batch events dalam jumlah besar harus preserve insertion order."""
        svc = TelemetryService(max_events=200)
        for i in range(100):
            svc.emit_event(f"event.{i:03d}")

        events = svc.get_recent(limit=100)
        assert len(events) == 100
        assert events[0].message == "event.000"
        assert events[-1].message == "event.099"

    def test_stats(self):
        """get_stats harus melaporkan harga buffer dan subscriber."""
        svc = TelemetryService(max_events=50)
        for i in range(10):
            svc.emit_event(f"e.{i}")
        stats = svc.get_stats()
        assert stats["total_events"] == 10
        assert stats["max_events"] == 50


class TestMetricsCollectorIntegration:
    @pytest.mark.asyncio
    async def test_collector_manual_collect(self):
        """Collector manual (via _collect) menghasilkan RuntimeMetrics aktual."""
        collector = MetricsCollector(interval=999)
        await collector._collect()

        metrics = collector.metrics
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.uptime_seconds >= 0

    @pytest.mark.asyncio
    async def test_get_summary(self):
        """get_summary harus mengembalikan string ringkasan."""
        collector = MetricsCollector()
        summary = collector.get_summary()
        assert "CPU" in summary and "Memory" in summary


class TestCLIIntegration:
    @pytest.mark.asyncio
    async def test_logs_cli_imports(self):
        """CLI logs harus bisa di-import tanpa error."""
        from sam.cli import logs
        assert hasattr(logs, "app")

    @pytest.mark.asyncio
    async def test_metrics_cli_imports(self):
        """CLI metrics harus bisa di-import tanpa error."""
        from sam.cli import metrics
        assert hasattr(metrics, "app")
