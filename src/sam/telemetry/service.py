"""
Telemetry Service — Phase 1

Structured event ingestion, metrics recording, dan query.
"""

import structlog
from typing import List, Optional, Generator, Dict, Any
from collections import deque
from .models import TelemetryEvent, TelemetrySeverity, RuntimeMetrics

logger = structlog.get_logger()


class TelemetryService:
    """Telemetry Service — event store, query, dan streaming."""

    def __init__(self, max_events: int = 10000):
        self.events: deque = deque(maxlen=max_events)
        self.metrics_history: List[RuntimeMetrics] = []
        self._latest_metrics: Optional[RuntimeMetrics] = None

    def emit(self, event: TelemetryEvent) -> None:
        """Catat event ke telemetry store."""
        self.events.append(event)
        # Python 3.8 compat — dict() instead of .dict()
        event_dict = {
            "event_id": event.event_id,
            "event_name": event.event_name,
            "severity": event.severity.value,
        }
        logger.info("telemetry_event", **event_dict)

    def emit_event(
        self,
        event_name: str,
        severity: TelemetrySeverity = TelemetrySeverity.INFO,
        component: str = "runtime",
        runtime_state: Optional[str] = None,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        payload: Dict[str, Any] = None,
    ) -> TelemetryEvent:
        """Convenience method untuk emit event langsung."""
        event = TelemetryEvent(
            event_name=event_name,
            severity=severity,
            component=component,
            runtime_state=runtime_state,
            correlation_id=correlation_id,
            session_id=session_id,
            payload=payload or {},
        )
        self.emit(event)
        return event

    def get_events(
        self,
        limit: int = 100,
        severity: Optional[TelemetrySeverity] = None,
    ) -> List[TelemetryEvent]:
        """Ambil event, difilter severity dan dibatasi."""
        if severity:
            filtered = [e for e in self.events if e.severity == severity]
        else:
            filtered = list(self.events)
        return filtered[-limit:] if limit else filtered

    def follow(self) -> Generator[TelemetryEvent, None, None]:
        """Generator untuk live streaming event.

        Yields existing events, kemudian siap untuk live streaming
        (akan di-handle di CLI dengan polling loop).
        """
        # Yield existing events
        for event in self.events:
            yield event
        # Live stream akan di-handle di CLI dengan polling

    def record_metrics(self, metrics: RuntimeMetrics) -> None:
        """Rekam snapshot metrics."""
        self.metrics_history.append(metrics)
        self._latest_metrics = metrics
        logger.info("metrics_recorded", cpu=metrics.cpu_percent, mem=metrics.memory_mb)

    def get_metrics(self) -> Optional[RuntimeMetrics]:
        """Ambil metrics terbaru."""
        return self._latest_metrics

    def emit_openclaw_event(
        self,
        event_name: str,
        severity: TelemetrySeverity = TelemetrySeverity.INFO,
        payload: Dict[str, Any] = None,
        workspace_path: str = "",
    ) -> TelemetryEvent:
        """Emit event spesifik OpenClaw ke telemetry."""
        event = TelemetryEvent(
            event_name=event_name,
            severity=severity,
            component="openclaw",
            payload={
                "workspace": workspace_path,
                **(payload or {}),
            },
        )
        self.emit(event)
        return event

    def get_metrics_history(self, limit: int = 100) -> List[RuntimeMetrics]:
        """Ambil riwayat metrics."""
        return self.metrics_history[-limit:] if limit else self.metrics_history

    def clear(self) -> None:
        """Bersihkan semua event dan metrics."""
        self.events.clear()
        self.metrics_history.clear()
        self._latest_metrics = None
