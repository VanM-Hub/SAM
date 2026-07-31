"""Sprint 209 — Policy Monitoring Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.policy_runtime.monitoring.policy_monitor import (
    PolicyMonitor, PolicyStatus,
)
from sam.policy_runtime.monitoring.policy_metrics import (
    PolicyMetrics, PolicyMetricSample, PolicyMetricsCollector,
)
from sam.policy_runtime.monitoring.policy_health import (
    PolicyHealth, PolicyHealthCheck,
)
from sam.policy_runtime.monitoring.policy_snapshot import (
    PolicySnapshot, PolicySnapshotter,
)
from sam.policy_runtime.monitoring.policy_report import (
    PolicyReport, PolicyReporter,
)
from sam.policy_runtime.monitoring.conversation_monitoring import (
    ConversationMonitoringBridge,
)
from sam.policy_runtime.monitoring.dashboard_monitoring import (
    DashboardMonitoringBridge,
)
from sam.policy_runtime.foundation.policy_registry import PolicyRegistry
from sam.policy_runtime.foundation.policy_descriptor import PolicyDescriptor
from sam.policy_runtime.dashboard import PolicyCard


def _registry():
    r = PolicyRegistry()
    r.register(PolicyDescriptor("pol1", "AccessControl", category="security"))
    r.register(PolicyDescriptor("pol2", "Throttle", category="performance"))
    return r


class TestPolicyMonitor:
    def test_status_healthy(self):
        s = PolicyMonitor(_registry()).status("pol1")
        assert s.registered is True
        assert s.healthy is True

    def test_status_missing(self):
        s = PolicyMonitor(_registry()).status("nope")
        assert s.registered is False
        assert s.healthy is False

    def test_all_status(self):
        assert len(PolicyMonitor(_registry()).all_status()) == 2

    def test_healthy_count(self):
        assert PolicyMonitor(_registry()).healthy_count() == 2


class TestPolicyStatus:
    def test_immutable(self):
        s = PolicyStatus("pol1")
        with pytest.raises(FrozenInstanceError):
            s.healthy = True


class TestPolicyMetricsCollector:
    def test_collect(self):
        m = PolicyMetricsCollector(_registry()).collect()
        assert m.total == 2
        assert m.external_calls == 0


class TestPolicyMetricSample:
    def test_default(self):
        assert PolicyMetricSample("x").external_calls == 0


class TestPolicyMetrics:
    def test_default(self):
        assert PolicyMetrics().external_calls == 0

    def test_immutable(self):
        m = PolicyMetrics()
        with pytest.raises(FrozenInstanceError):
            m.total = 1


class TestPolicyHealth:
    def test_check(self):
        h = PolicyHealthCheck(_registry()).check()
        assert h.total == 2
        assert h.healthy_policy == 2
        assert h.healthy is True

    def test_empty(self):
        h = PolicyHealthCheck(PolicyRegistry()).check()
        assert h.total == 0
        assert h.healthy is True

    def test_immutable(self):
        h = PolicyHealth()
        with pytest.raises(FrozenInstanceError):
            h.total = 1


class TestPolicySnapshotter:
    def test_snapshot(self):
        s = PolicySnapshotter(_registry()).snapshot()
        assert s.total == 2
        assert s.category_counts["security"] == 1
        assert s.category_counts["performance"] == 1


class TestPolicySnapshot:
    def test_immutable(self):
        s = PolicySnapshot()
        with pytest.raises(FrozenInstanceError):
            s.total = 1


class TestPolicyReporter:
    def test_report(self):
        r = PolicyReporter(_registry()).report()
        assert r.total == 2
        assert r.healthy == 2
        assert r.external_calls == 0


class TestPolicyReport:
    def test_immutable(self):
        r = PolicyReport()
        with pytest.raises(FrozenInstanceError):
            r.total = 1


class TestConversationMonitoringBridge:
    def test_health(self):
        b = ConversationMonitoringBridge(_registry())
        assert b.health("pol1") is True
        assert b.health("nope") is False

    def test_summary(self):
        b = ConversationMonitoringBridge(_registry())
        assert b.summary()["total"] == 2
        assert b.summary()["external_calls"] == 0

    def test_metrics(self):
        b = ConversationMonitoringBridge(_registry())
        assert b.metrics()["external_calls"] == 0


class TestDashboardMonitoringBridge:
    def test_five_cards(self):
        b = DashboardMonitoringBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_overview(self):
        b = DashboardMonitoringBridge(_registry())
        assert b.overview_card().verdict == "ready"


class TestMonitorImmutability:
    DTO_CLASSES = [
        PolicyStatus, PolicyMetricSample, PolicyMetrics,
        PolicyHealth, PolicySnapshot, PolicyReport,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
