"""Sprint 177 — Memory Monitoring Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.memory.monitor.memory_monitor import MemoryMonitor, MemoryStatus
from sam.memory.monitor.memory_metrics import (
    MemoryMetricSample, MemoryMetrics, MemoryMetricsCollector,
)
from sam.memory.monitor.memory_health import MemoryHealth, MemoryHealthCheck
from sam.memory.monitor.memory_snapshot import MemorySnapshot, MemorySnapshotter
from sam.memory.monitor.memory_report import MemoryReport, MemoryReporter
from sam.memory.monitor.conversation_monitor import ConversationMonitorBridge
from sam.memory.monitor.dashboard_monitor import DashboardMonitorBridge
from sam.memory.foundation.memory_registry import MemoryRegistry
from sam.memory.foundation.memory_descriptor import MemoryDescriptor
from sam.memory.foundation.memory_capability import MemoryCapability
from sam.memory.dashboard.memory_dashboard import ExecutionCard


def _registry():
    r = MemoryRegistry()
    r.register(MemoryDescriptor("mem1", "Short", category="short_term"))
    r.attach_capability(MemoryCapability("c1", "mem1", operations=["retain"]))
    r.register(MemoryDescriptor("mem2", "Long", category="long_term"))
    return r


class TestMemoryMonitor:
    def test_status_healthy(self):
        m = MemoryMonitor(_registry())
        s = m.status("mem1")
        assert s.registered is True
        assert s.healthy is True
        assert s.has_capability is True

    def test_status_unhealthy_no_cap(self):
        m = MemoryMonitor(_registry())
        s = m.status("mem2")
        assert s.registered is True
        assert s.has_capability is False
        assert s.healthy is False

    def test_status_missing(self):
        m = MemoryMonitor(_registry())
        s = m.status("nope")
        assert s.registered is False
        assert s.healthy is False

    def test_all_status(self):
        m = MemoryMonitor(_registry())
        assert len(m.all_status()) == 2

    def test_healthy_count(self):
        m = MemoryMonitor(_registry())
        assert m.healthy_count() == 1


class TestMemoryStatus:
    def test_immutable(self):
        s = MemoryStatus("m1")
        with pytest.raises(FrozenInstanceError):
            s.healthy = True


class TestMemoryMetricsCollector:
    def test_collect(self):
        m = MemoryMetricsCollector(_registry()).collect()
        assert m.total == 2
        assert m.external_calls == 0
        assert len(m.samples) == 2


class TestMemoryMetricSample:
    def test_immutable(self):
        s = MemoryMetricSample("m1")
        with pytest.raises(FrozenInstanceError):
            s.healthy = True

    def test_defaults(self):
        s = MemoryMetricSample("m1")
        assert s.preview_count == 0
        assert s.external_calls == 0


class TestMemoryMetrics:
    def test_default(self):
        assert MemoryMetrics().external_calls == 0

    def test_immutable(self):
        m = MemoryMetrics()
        with pytest.raises(FrozenInstanceError):
            m.total = 1


class TestMemoryHealth:
    def test_check(self):
        h = MemoryHealthCheck(_registry()).check()
        assert h.total == 2
        assert h.healthy_memories == 1

    def test_healthy_flag(self):
        h = MemoryHealthCheck(_registry()).check()
        # ada mem2 tanpa capability -> bukan unregistered
        assert "mem2 unregistered" not in h.issues

    def test_missing_unregistered_issue(self):
        # empty registry -> tidak ada issue unregistered, healthy tetap True
        h = MemoryHealthCheck(MemoryRegistry()).check()
        assert h.healthy is True
        assert h.issues == []

    def test_immutable(self):
        h = MemoryHealth()
        with pytest.raises(FrozenInstanceError):
            h.healthy = False


class TestMemoryHealthEmpty:
    def test_empty_registry(self):
        h = MemoryHealthCheck(MemoryRegistry()).check()
        assert h.total == 0
        assert h.healthy_memories == 0
        assert h.healthy is True


class TestMemorySnapshot:
    def test_snapshot(self):
        s = MemorySnapshotter(_registry()).snapshot()
        assert s.total == 2
        assert s.categories["short_term"] == 1

    def test_immutable(self):
        s = MemorySnapshot("m1")
        with pytest.raises(FrozenInstanceError):
            s.total = 1


class TestMemoryReporter:
    def test_report(self):
        r = MemoryReporter(_registry()).report()
        assert r.total == 2
        assert r.healthy == 1
        assert r.external_calls == 0


class TestMemoryReport:
    def test_default(self):
        assert MemoryReport().external_calls == 0

    def test_immutable(self):
        r = MemoryReport()
        with pytest.raises(FrozenInstanceError):
            r.total = 1


class TestConversationMonitorBridge:
    def test_health(self):
        m = MemoryMonitor(_registry())
        b = ConversationMonitorBridge(m)
        assert b.health("mem1") is True

    def test_summary(self):
        m = MemoryMonitor(_registry())
        b = ConversationMonitorBridge(m, MemoryReporter(_registry()))
        assert b.summary()["total"] == 2
        assert b.summary()["external_calls"] == 0


class TestDashboardMonitorBridge:
    def test_five_cards(self):
        b = DashboardMonitorBridge(MemoryMonitor(_registry()))
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardMonitorBridge(MemoryMonitor(_registry()))
        assert b.overview_card().verdict == "ready"


class TestMonitorImmutability:
    DTO_CLASSES = [
        MemoryStatus, MemoryMetricSample, MemoryMetrics,
        MemoryHealth, MemorySnapshot, MemoryReport,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
