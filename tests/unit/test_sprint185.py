"""Sprint 185 — Knowledge Monitoring Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.knowledge_runtime.monitor.knowledge_monitor import KnowledgeMonitor, KnowledgeStatus
from sam.knowledge_runtime.monitor.knowledge_metrics import (
    KnowledgeMetricSample, KnowledgeMetrics, KnowledgeMetricsCollector,
)
from sam.knowledge_runtime.monitor.knowledge_health import (
    KnowledgeHealth, KnowledgeHealthCheck,
)
from sam.knowledge_runtime.monitor.knowledge_snapshot import (
    KnowledgeSnapshot, KnowledgeSnapshotter,
)
from sam.knowledge_runtime.monitor.knowledge_report import (
    KnowledgeReport, KnowledgeReporter,
)
from sam.knowledge_runtime.monitor.conversation_monitor import ConversationMonitorBridge
from sam.knowledge_runtime.monitor.dashboard_monitor import DashboardMonitorBridge
from sam.knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
from sam.knowledge_runtime.foundation.knowledge_descriptor import KnowledgeDescriptor
from sam.knowledge_runtime.foundation.knowledge_capability import KnowledgeCapability
from sam.knowledge_runtime.dashboard.knowledge_dashboard import ExecutionCard


def _registry():
    r = KnowledgeRegistry()
    r.register(KnowledgeDescriptor("kn1", "Domain", category="domain"))
    r.attach_capability(KnowledgeCapability("c1", "kn1", operations=["fact"]))
    r.register(KnowledgeDescriptor("kn2", "Tech", category="tech"))
    return r


class TestKnowledgeMonitor:
    def test_status_healthy(self):
        m = KnowledgeMonitor(_registry())
        s = m.status("kn1")
        assert s.registered is True
        assert s.healthy is True
        assert s.has_capability is True

    def test_status_unhealthy_no_cap(self):
        m = KnowledgeMonitor(_registry())
        s = m.status("kn2")
        assert s.registered is True
        assert s.has_capability is False
        assert s.healthy is False

    def test_status_missing(self):
        m = KnowledgeMonitor(_registry())
        s = m.status("nope")
        assert s.registered is False
        assert s.healthy is False

    def test_all_status(self):
        m = KnowledgeMonitor(_registry())
        assert len(m.all_status()) == 2

    def test_healthy_count(self):
        m = KnowledgeMonitor(_registry())
        assert m.healthy_count() == 1


class TestKnowledgeStatus:
    def test_immutable(self):
        s = KnowledgeStatus("kn1")
        with pytest.raises(FrozenInstanceError):
            s.healthy = True


class TestKnowledgeMetricsCollector:
    def test_collect(self):
        m = KnowledgeMetricsCollector(_registry()).collect()
        assert m.total == 2
        assert m.external_calls == 0
        assert len(m.samples) == 2


class TestKnowledgeMetricSample:
    def test_immutable(self):
        s = KnowledgeMetricSample("kn1")
        with pytest.raises(FrozenInstanceError):
            s.healthy = True

    def test_defaults(self):
        s = KnowledgeMetricSample("kn1")
        assert s.preview_count == 0
        assert s.external_calls == 0


class TestKnowledgeMetrics:
    def test_default(self):
        assert KnowledgeMetrics().external_calls == 0

    def test_immutable(self):
        m = KnowledgeMetrics()
        with pytest.raises(FrozenInstanceError):
            m.total = 1


class TestKnowledgeHealth:
    def test_check(self):
        h = KnowledgeHealthCheck(_registry()).check()
        assert h.total == 2
        assert h.healthy_knowledge == 1

    def test_empty_registry(self):
        h = KnowledgeHealthCheck(KnowledgeRegistry()).check()
        assert h.total == 0
        assert h.healthy is True

    def test_immutable(self):
        h = KnowledgeHealth()
        with pytest.raises(FrozenInstanceError):
            h.healthy = False


class TestKnowledgeSnapshot:
    def test_snapshot(self):
        s = KnowledgeSnapshotter(_registry()).snapshot()
        assert s.total == 2
        assert s.categories["domain"] == 1

    def test_immutable(self):
        s = KnowledgeSnapshot("kn1")
        with pytest.raises(FrozenInstanceError):
            s.total = 1


class TestKnowledgeSnapshotDefault:
    def test_default_total(self):
        assert KnowledgeSnapshot().total == 0


class TestKnowledgeReporter:
    def test_report(self):
        r = KnowledgeReporter(_registry()).report()
        assert r.total == 2
        assert r.healthy == 1
        assert r.external_calls == 0


class TestKnowledgeReport:
    def test_default(self):
        assert KnowledgeReport().external_calls == 0

    def test_immutable(self):
        r = KnowledgeReport()
        with pytest.raises(FrozenInstanceError):
            r.total = 1


class TestConversationMonitorBridge:
    def test_health(self):
        m = KnowledgeMonitor(_registry())
        b = ConversationMonitorBridge(m)
        assert b.health("kn1") is True

    def test_summary(self):
        m = KnowledgeMonitor(_registry())
        b = ConversationMonitorBridge(m, KnowledgeReporter(_registry()))
        assert b.summary()["total"] == 2
        assert b.summary()["external_calls"] == 0


class TestDashboardMonitorBridge:
    def test_five_cards(self):
        b = DashboardMonitorBridge(KnowledgeMonitor(_registry()))
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardMonitorBridge(KnowledgeMonitor(_registry()))
        assert b.overview_card().verdict == "ready"


class TestMonitorImmutability:
    DTO_CLASSES = [
        KnowledgeStatus, KnowledgeMetricSample, KnowledgeMetrics,
        KnowledgeHealth, KnowledgeSnapshot, KnowledgeReport,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
