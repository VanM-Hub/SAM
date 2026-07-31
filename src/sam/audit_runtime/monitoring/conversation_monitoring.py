"""Conversation Monitoring Bridge — 5 query read-only (Sprint 217)."""
from __future__ import annotations

from ..foundation.audit_descriptor import AuditDescriptor
from .audit_monitor import AuditMonitor
from .audit_metrics import AuditMetricsCollector
from .audit_health import AuditHealthMonitor
from .audit_snapshot import AuditSnapshotter
from .audit_report import AuditReporter


class ConversationMonitoringBridge:
    """Bridge conversation — 5 query read-only monitoring audit."""

    def query_1_status(self) -> dict:
        """Query 1 — status monitoring."""
        s = AuditMonitor().status()
        return {"state": s.state, "immutable": s.immutable}

    def query_2_metrics(self) -> dict:
        """Query 2 — metrik."""
        m = AuditMetricsCollector().collect()
        return {"total_records": m.total_records, "no_execute": m.no_execute}

    def query_3_health(self) -> dict:
        """Query 3 — kesehatan."""
        h = AuditHealthMonitor().check()
        return {"healthy": h.healthy, "checks": [c.name for c in h.checks]}

    def query_4_snapshot(self) -> dict:
        """Query 4 — snapshot."""
        s = AuditSnapshotter().snapshot([])
        return {"total": s.total}

    def query_5_report(self) -> dict:
        """Query 5 — laporan."""
        r = AuditReporter().report(AuditSnapshotter().snapshot([]))
        return {"healthy": r.healthy, "immutable": r.immutable}
