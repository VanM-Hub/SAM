"""Sprint 217 — Audit Monitoring Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.audit_runtime.monitoring.audit_monitor import (
    AuditMonitor, AuditStatus,
)
from sam.audit_runtime.monitoring.audit_metrics import (
    AuditMetrics, AuditMetricSample, AuditMetricsCollector,
)
from sam.audit_runtime.monitoring.audit_health import (
    AuditHealth, AuditHealthCheck, AuditHealthMonitor,
)
from sam.audit_runtime.monitoring.audit_snapshot import (
    AuditSnapshot, AuditSnapshotter,
)
from sam.audit_runtime.monitoring.audit_report import (
    AuditReport, AuditReporter,
)
from sam.audit_runtime.monitoring.conversation_monitoring import (
    ConversationMonitoringBridge,
)
from sam.audit_runtime.monitoring.dashboard_monitoring import (
    DashboardMonitoringBridge,
)
from sam.audit_runtime.foundation.audit_descriptor import AuditDescriptor
from sam.audit_runtime.dashboard import PolicyCard


class TestAuditMonitor:
    def test_status(self):
        s = AuditMonitor().status()
        assert s.state == "ready"
        assert s.immutable is True


class TestAuditStatus:
    def test_invalid(self):
        with pytest.raises(ValueError):
            AuditStatus(state="bogus")

    def test_immutable(self):
        s = AuditStatus()
        with pytest.raises(FrozenInstanceError):
            s.state = "x"


class TestAuditMetricsCollector:
    def test_collect(self):
        m = AuditMetricsCollector().collect()
        assert m.no_execute is True
        assert m.immutable_records == 0


class TestAuditMetrics:
    def test_immutable(self):
        m = AuditMetrics()
        with pytest.raises(FrozenInstanceError):
            m.total_records = 1


class TestAuditMetricSample:
    def test_immutable(self):
        s = AuditMetricSample()
        with pytest.raises(FrozenInstanceError):
            s.value = 1


class TestAuditHealthMonitor:
    def test_check(self):
        h = AuditHealthMonitor().check()
        assert h.healthy is True
        assert len(h.checks) == 3


class TestAuditHealth:
    def test_immutable(self):
        h = AuditHealth()
        with pytest.raises(FrozenInstanceError):
            h.healthy = False


class TestAuditHealthCheck:
    def test_immutable(self):
        c = AuditHealthCheck()
        with pytest.raises(FrozenInstanceError):
            c.ok = False


class TestAuditSnapshotter:
    def test_snapshot(self):
        s = AuditSnapshotter().snapshot([
            AuditDescriptor("a", category="security"),
            AuditDescriptor("b", category="operations"),
        ])
        assert s.total == 2
        assert s.categories == ("operations", "security")


class TestAuditSnapshot:
    def test_immutable(self):
        s = AuditSnapshot()
        with pytest.raises(FrozenInstanceError):
            s.total = 1


class TestAuditReporter:
    def test_report(self):
        s = AuditSnapshotter().snapshot([AuditDescriptor("a")])
        r = AuditReporter().report(s)
        assert r.total == 1
        assert r.healthy is True
        assert r.immutable is True


class TestAuditReport:
    def test_immutable(self):
        r = AuditReport()
        with pytest.raises(FrozenInstanceError):
            r.healthy = False


class TestConversationMonitoringBridge:
    def test_5_queries(self):
        b = ConversationMonitoringBridge()
        assert b.query_1_status()["state"] == "ready"
        assert b.query_2_metrics()["no_execute"] is True
        assert b.query_3_health()["healthy"] is True
        assert b.query_4_snapshot()["total"] == 0
        assert b.query_5_report()["immutable"] is True


class TestDashboardMonitoringBridge:
    def test_five_cards(self):
        b = DashboardMonitoringBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_verdict(self):
        b = DashboardMonitoringBridge()
        assert b.verdict_card().status == "ready"


class TestMonitoringImmutability:
    DTO_CLASSES = [
        AuditStatus, AuditMetrics, AuditMetricSample, AuditHealth,
        AuditHealthCheck, AuditSnapshot, AuditReport,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
