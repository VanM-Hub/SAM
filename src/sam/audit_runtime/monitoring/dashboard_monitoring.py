"""Dashboard Monitoring Bridge — 5 PolicyCards (Sprint 217)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from .audit_health import AuditHealthMonitor
from .audit_metrics import AuditMetricsCollector


class DashboardMonitoringBridge:
    """Bridge dashboard — 5 kartu monitoring audit."""

    def cards(self):
        h = AuditHealthMonitor().check()
        m = AuditMetricsCollector().collect()
        state = "ready" if h.healthy else "error"
        return [
            PolicyCard("am.on.status", "audit", state,
                          "audit monitor ready" if h.healthy else "audit error",
                          "monitoring", state),
            PolicyCard("am.on.health", "audit", "healthy" if h.healthy else "unhealthy",
                          f"{len(h.checks)} health checks",
                          "monitoring", "healthy"),
            PolicyCard("am.on.immutable", "audit", "immutable",
                          "immutable audit records",
                          "monitoring", "immutable"),
            PolicyCard("am.on.preview", "audit", "preview_only",
                          "preview-only monitoring (no write)",
                          "monitoring", "preview_only"),
            PolicyCard("am.on.noexec", "audit", "ready",
                          "no_execute=true",
                          "monitoring", "ready"),
        ]

    def verdict_card(self):
        return self.cards()[0]
