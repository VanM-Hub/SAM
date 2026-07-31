"""Conversation Monitoring Bridge — 5 read-only queries (Sprint 225)."""
from __future__ import annotations

from .artifact_monitor import ArtifactMonitor
from .artifact_metrics import ArtifactMetricsCollector
from .artifact_health import ArtifactHealthCheck
from .artifact_snapshot import ArtifactSnapshotter
from .artifact_report import ArtifactReporter


class ConversationMonitoringBridge:
    """Bridge conversation — 5 query monitoring artifact."""

    def __init__(self) -> None:
        self._monitor = ArtifactMonitor()
        self._metrics = ArtifactMetricsCollector()
        self._health = ArtifactHealthCheck()
        self._snapshot = ArtifactSnapshotter()
        self._report = ArtifactReporter()

    def query_1_status(self) -> dict:
        s = self._monitor.status()
        return {"state": s.state, "preview_only": s.preview_only}

    def query_2_metrics(self) -> dict:
        m = self._metrics.collect({"report": 2})
        return {"samples": len(m.samples), "external_calls": m.external_calls}

    def query_3_health(self) -> dict:
        h = self._health.check()
        return {"healthy": h.healthy}

    def query_4_snapshot(self) -> dict:
        s = self._snapshot.snapshot(("a", "b"))
        return {"count": len(s.names), "external_calls": s.external_calls}

    def query_5_report(self) -> dict:
        r = self._report.report(3)
        return {"total": r.total, "ready": r.ready}
