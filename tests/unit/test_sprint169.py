"""Sprint 169 — Monitoring Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.skills.monitor.skill_monitor import SkillMonitor, SkillStatus
from sam.skills.monitor.skill_metrics import SkillMetricSample, SkillMetrics, SkillMetricsCollector
from sam.skills.monitor.skill_health import SkillHealth, SkillHealthCheck
from sam.skills.monitor.skill_snapshot import SkillSnapshot, SkillSnapshotter
from sam.skills.monitor.skill_report import SkillReport, SkillReporter
from sam.skills.monitor.conversation_monitor import ConversationMonitorBridge
from sam.skills.monitor.dashboard_monitor import DashboardMonitorBridge
from sam.skills.foundation.skill_registry import SkillRegistry
from sam.skills.foundation.skill_descriptor import SkillDescriptor
from sam.skills.foundation.skill_capability import SkillCapability
from sam.skills.dashboard.skill_dashboard import ExecutionCard


def _registry():
    r = SkillRegistry()
    r.register(SkillDescriptor("skill1", "Read", category="io"))
    r.attach_capability(SkillCapability("c1", "skill1", operations=["read"]))
    r.register(SkillDescriptor("skill2", "Write", category="io"))
    return r


class TestSkillMonitor:
    def test_status_healthy(self):
        m = SkillMonitor(_registry())
        s = m.status("skill1")
        assert s.registered is True
        assert s.healthy is True
        assert s.has_capability is True

    def test_status_unhealthy_no_cap(self):
        m = SkillMonitor(_registry())
        s = m.status("skill2")
        assert s.registered is True
        assert s.has_capability is False
        assert s.healthy is False

    def test_status_missing(self):
        m = SkillMonitor(_registry())
        s = m.status("nope")
        assert s.registered is False
        assert s.healthy is False

    def test_all_status(self):
        m = SkillMonitor(_registry())
        assert len(m.all_status()) == 2

    def test_healthy_count(self):
        m = SkillMonitor(_registry())
        assert m.healthy_count() == 1


class TestSkillStatus:
    def test_immutable(self):
        s = SkillStatus("s1")
        with pytest.raises(FrozenInstanceError):
            s.healthy = True


class TestSkillMetricsCollector:
    def test_collect(self):
        m = SkillMetricsCollector(_registry()).collect()
        assert m.total == 2
        assert m.external_calls == 0
        assert len(m.samples) == 2

    def test_healthy_flag(self):
        m = SkillMetricsCollector(_registry()).collect()
        assert m.samples[0].healthy is True
        assert m.samples[1].healthy is False


class TestSkillMetricSample:
    def test_immutable(self):
        s = SkillMetricSample("s1")
        with pytest.raises(FrozenInstanceError):
            s.healthy = True


class TestSkillHealth:
    def test_unhealthy_missing(self):
        h = SkillHealthCheck(_registry()).check()
        # skill2 registered tapi tanpa capability -> bukan issue unregistered
        assert "skill2 unregistered" not in h.issues


class TestSkillHealthCheck:
    def test_check(self):
        h = SkillHealthCheck(_registry()).check()
        assert h.total == 2
        assert h.healthy_skills == 1


class TestSkillSnapshot:
    def test_snapshot(self):
        s = SkillSnapshotter(_registry()).snapshot()
        assert s.total == 2
        assert s.categories["io"] == 2

    def test_immutable(self):
        s = SkillSnapshot()
        with pytest.raises(FrozenInstanceError):
            s.total = 1


class TestSkillReporter:
    def test_report(self):
        r = SkillReporter(_registry()).report()
        assert r.total == 2
        assert r.healthy == 1
        assert r.external_calls == 0


class TestSkillReport:
    def test_default(self):
        assert SkillReport().external_calls == 0


class TestConversationMonitorBridge:
    def test_health(self):
        m = SkillMonitor(_registry())
        b = ConversationMonitorBridge(m)
        assert b.health("skill1") is True

    def test_summary(self):
        m = SkillMonitor(_registry())
        b = ConversationMonitorBridge(m, SkillReporter(_registry()))
        assert b.summary()["total"] == 2
        assert b.summary()["external_calls"] == 0


class TestDashboardMonitorBridge:
    def test_five_cards(self):
        b = DashboardMonitorBridge(SkillMonitor(_registry()))
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardMonitorBridge(SkillMonitor(_registry()))
        assert b.overview_card().verdict == "ready"


class TestMonitorImmutability:
    DTO_CLASSES = [
        SkillStatus, SkillMetricSample, SkillMetrics,
        SkillHealth, SkillSnapshot, SkillReport,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
