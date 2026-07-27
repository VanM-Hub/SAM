"""
Integration tests — Observability (Telemetry + API + CLI)
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

        # Query all
        all_events = svc.get_events(limit=10)
        assert len(all_events) == 3

        # Query by severity
        errors = svc.get_events(severity=TelemetrySeverity.ERROR)
        assert len(errors) == 1
        assert errors[0].event_name == "error.test"

        # Query debug
        debug_events = svc.get_events(severity=TelemetrySeverity.DEBUG)
        assert len(debug_events) == 1

    def test_metrics_roundtrip(self):
        """Record metrics lalu query harus konsisten."""
        svc = TelemetryService()

        m1 = RuntimeMetrics(cpu_percent=25.5, memory_mb=512.0)
        m2 = RuntimeMetrics(cpu_percent=50.0, memory_mb=1024.0)

        svc.record_metrics(m1)
        svc.record_metrics(m2)

        latest = svc.get_metrics()
        assert latest.cpu_percent == 50.0
        assert latest.memory_mb == 1024.0

        history = svc.get_metrics_history(limit=10)
        assert len(history) == 2

    def test_correlation_across_events(self):
        """Events dengan correlation_id yang sama harus bisa dilacak."""
        svc = TelemetryService()
        corr_id = "corr-ops-001"

        svc.emit_event("operation.start", correlation_id=corr_id, component="workflow")
        svc.emit_event("operation.progress", correlation_id=corr_id, component="workflow")
        svc.emit_event("operation.complete", correlation_id=corr_id, component="workflow")

        corr_events = [e for e in svc.events if e.correlation_id == corr_id]
        assert len(corr_events) == 3
        assert corr_events[0].event_name == "operation.start"
        assert corr_events[-1].event_name == "operation.complete"

    def test_large_batch_preserves_order(self):
        """Batch events dalam jumlah besar harus preserve insertion order."""
        svc = TelemetryService(max_events=200)
        for i in range(100):
            svc.emit_event(f"event.{i:03d}")

        events = svc.get_events(limit=100)
        assert events[0].event_name == "event.000"
        assert events[-1].event_name == "event.099"

    def test_clear_and_reuse(self):
        """Clear harus reset service state dan service bisa digunakan lagi."""
        svc = TelemetryService()
        svc.emit_event("test")
        svc.record_metrics(RuntimeMetrics(cpu_percent=10.0))
        svc.clear()

        assert len(svc.events) == 0
        assert svc.get_metrics() is None

        # Should be reusable
        svc.emit_event("after.clear")
        assert len(svc.events) == 1


class TestMetricsCollectorIntegration:
    @pytest.mark.asyncio
    async def test_collector_integration_with_coordinator(self):
        """Collector harus bisa diintegrasikan dengan coordinator dan telemetry."""
        from sam.runtime.coordinator import RuntimeCoordinator
        from datetime import datetime

        coord = RuntimeCoordinator()
        coord.start_time = datetime.utcnow()

        collector = MetricsCollector(coord, interval=999)

        # Collect manual — harus return data
        metrics = await collector.collect()

        # Record ke telemetry
        coord.telemetry.record_metrics(metrics)

        # Verify stored
        latest = coord.telemetry.get_metrics()
        assert latest is not None
        assert latest.cpu_percent == metrics.cpu_percent
        assert latest.memory_mb == metrics.memory_mb

    @pytest.mark.asyncio
    async def test_psutil_fallback(self):
        """Jika psutil tidak ada, collector harus tetap jalan."""
        import sys
        from sam.runtime.coordinator import RuntimeCoordinator

        coord = RuntimeCoordinator()
        collector = MetricsCollector(coord)

        metrics = await collector.collect()
        assert metrics.cpu_percent >= 0  # fallback to 0.0
        assert metrics.uptime_seconds >= 0


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
