"""Sprint 193 — Cognitive Monitoring Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.cognitive_runtime.monitor.cognitive_monitor import (
    CognitiveMonitor, CognitiveStatus,
)
from sam.cognitive_runtime.monitor.cognitive_metrics import (
    CognitiveMetrics, CognitiveMetricSample, CognitiveMetricsCollector,
)
from sam.cognitive_runtime.monitor.cognitive_health import (
    CognitiveHealth, CognitiveHealthCheck,
)
from sam.cognitive_runtime.monitor.cognitive_snapshot_report import (
    CognitiveSnapshot as CSnapshot, CognitiveSnapshotter,
)
from sam.cognitive_runtime.monitor.cognitive_report import (
    CognitiveReport, CognitiveReporter,
)
from sam.cognitive_runtime.monitor.conversation_monitor import ConversationMonitorBridge
from sam.cognitive_runtime.monitor.dashboard_monitor import DashboardMonitorBridge
from sam.cognitive_runtime.foundation.cognitive_registry import CognitiveRegistry
from sam.cognitive_runtime.foundation.cognitive_descriptor import CognitiveDescriptor
from sam.cognitive_runtime.dashboard import ExecutionCard


def _registry():
    r = CognitiveRegistry()
    r.register(CognitiveDescriptor("cog1", "Core", category="core"))
    r.register(CognitiveDescriptor("cog2", "Insight", category="insight"))
    return r


class TestCognitiveMonitor:
    def test_status_healthy(self):
        s = CognitiveMonitor(_registry()).status("cog1")
        assert s.registered is True
        assert s.healthy is True

    def test_status_missing(self):
        s = CognitiveMonitor(_registry()).status("nope")
        assert s.registered is False
        assert s.healthy is False

    def test_all_status(self):
        assert len(CognitiveMonitor(_registry()).all_status()) == 2

    def test_healthy_count(self):
        assert CognitiveMonitor(_registry()).healthy_count() == 2


class TestCognitiveStatus:
    def test_immutable(self):
        s = CognitiveStatus("cog1")
        with pytest.raises(FrozenInstanceError):
            s.healthy = True


class TestCognitiveMetricsCollector:
    def test_collect(self):
        m = CognitiveMetricsCollector(_registry()).collect()
        assert m.total == 2
        assert m.external_calls == 0


class TestCognitiveMetricSample:
    def test_default(self):
        assert CognitiveMetricSample("x").external_calls == 0


class TestCognitiveMetrics:
    def test_default(self):
        assert CognitiveMetrics().external_calls == 0

    def test_immutable(self):
        m = CognitiveMetrics()
        with pytest.raises(FrozenInstanceError):
            m.total = 1


class TestCognitiveHealth:
    def test_check(self):
        h = CognitiveHealthCheck(_registry()).check()
        assert h.total == 2
        assert h.healthy_cognitive == 2
        assert h.healthy is True

    def test_empty(self):
        h = CognitiveHealthCheck(CognitiveRegistry()).check()
        assert h.total == 0
        assert h.healthy is True

    def test_immutable(self):
        h = CognitiveHealth()
        with pytest.raises(FrozenInstanceError):
            h.total = 1


class TestCognitiveSnapshotter:
    def test_snapshot(self):
        s = CognitiveSnapshotter(_registry()).snapshot()
        assert s.total == 2
        assert s.scope_counts["core"] == 1
        assert s.scope_counts["insight"] == 1


class TestCSnapshot:
    def test_immutable(self):
        s = CSnapshot()
        with pytest.raises(FrozenInstanceError):
            s.total = 1


class TestCognitiveReporter:
    def test_report(self):
        r = CognitiveReporter(_registry()).report()
        assert r.total == 2
        assert r.healthy == 2
        assert r.external_calls == 0


class TestCognitiveReport:
    def test_immutable(self):
        r = CognitiveReport()
        with pytest.raises(FrozenInstanceError):
            r.total = 1


class TestConversationMonitorBridge:
    def test_health(self):
        b = ConversationMonitorBridge(_registry())
        assert b.health("cog1") is True
        assert b.health("nope") is False

    def test_summary(self):
        b = ConversationMonitorBridge(_registry())
        assert b.summary()["total"] == 2
        assert b.summary()["external_calls"] == 0

    def test_metrics(self):
        b = ConversationMonitorBridge(_registry())
        assert b.metrics()["external_calls"] == 0


class TestDashboardMonitorBridge:
    def test_five_cards(self):
        b = DashboardMonitorBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardMonitorBridge(_registry())
        assert b.overview_card().verdict == "ready"


class TestMonitorImmutability:
    DTO_CLASSES = [
        CognitiveStatus, CognitiveMetricSample, CognitiveMetrics,
        CognitiveHealth, CSnapshot, CognitiveReport,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
