"""Sprint 201 — Workflow Monitoring Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.workflow_runtime.monitoring.workflow_monitor import (
    WorkflowMonitor, WorkflowStatus,
)
from sam.workflow_runtime.monitoring.workflow_metrics import (
    WorkflowMetrics, WorkflowMetricSample, WorkflowMetricsCollector,
)
from sam.workflow_runtime.monitoring.workflow_health import (
    WorkflowHealth, WorkflowHealthCheck,
)
from sam.workflow_runtime.monitoring.workflow_snapshot import (
    WorkflowSnapshot, WorkflowSnapshotter,
)
from sam.workflow_runtime.monitoring.workflow_report import (
    WorkflowReport, WorkflowReporter,
)
from sam.workflow_runtime.monitoring.conversation_monitoring import (
    ConversationMonitoringBridge,
)
from sam.workflow_runtime.monitoring.dashboard_monitoring import (
    DashboardMonitoringBridge,
)
from sam.workflow_runtime.foundation.workflow_registry import WorkflowRegistry
from sam.workflow_runtime.foundation.workflow_descriptor import WorkflowDescriptor
from sam.workflow_runtime.dashboard import WorkflowCard


def _registry():
    r = WorkflowRegistry()
    r.register(WorkflowDescriptor("wf1", "Onboard", category="process"))
    r.register(WorkflowDescriptor("wf2", "Deploy", category="process"))
    return r


class TestWorkflowMonitor:
    def test_status_healthy(self):
        s = WorkflowMonitor(_registry()).status("wf1")
        assert s.registered is True
        assert s.healthy is True

    def test_status_missing(self):
        s = WorkflowMonitor(_registry()).status("nope")
        assert s.registered is False
        assert s.healthy is False

    def test_all_status(self):
        assert len(WorkflowMonitor(_registry()).all_status()) == 2

    def test_healthy_count(self):
        assert WorkflowMonitor(_registry()).healthy_count() == 2


class TestWorkflowStatus:
    def test_immutable(self):
        s = WorkflowStatus("wf1")
        with pytest.raises(FrozenInstanceError):
            s.healthy = True


class TestWorkflowMetricsCollector:
    def test_collect(self):
        m = WorkflowMetricsCollector(_registry()).collect()
        assert m.total == 2
        assert m.external_calls == 0


class TestWorkflowMetricSample:
    def test_default(self):
        assert WorkflowMetricSample("x").external_calls == 0


class TestWorkflowMetrics:
    def test_default(self):
        assert WorkflowMetrics().external_calls == 0

    def test_immutable(self):
        m = WorkflowMetrics()
        with pytest.raises(FrozenInstanceError):
            m.total = 1


class TestWorkflowHealth:
    def test_check(self):
        h = WorkflowHealthCheck(_registry()).check()
        assert h.total == 2
        assert h.healthy_workflow == 2
        assert h.healthy is True

    def test_empty(self):
        h = WorkflowHealthCheck(WorkflowRegistry()).check()
        assert h.total == 0
        assert h.healthy is True

    def test_immutable(self):
        h = WorkflowHealth()
        with pytest.raises(FrozenInstanceError):
            h.total = 1


class TestWorkflowSnapshotter:
    def test_snapshot(self):
        s = WorkflowSnapshotter(_registry()).snapshot()
        assert s.total == 2
        assert s.scope_counts["process"] == 2


class TestWorkflowSnapshot:
    def test_immutable(self):
        s = WorkflowSnapshot()
        with pytest.raises(FrozenInstanceError):
            s.total = 1


class TestWorkflowReporter:
    def test_report(self):
        r = WorkflowReporter(_registry()).report()
        assert r.total == 2
        assert r.healthy == 2
        assert r.external_calls == 0


class TestWorkflowReport:
    def test_immutable(self):
        r = WorkflowReport()
        with pytest.raises(FrozenInstanceError):
            r.total = 1


class TestConversationMonitoringBridge:
    def test_health(self):
        b = ConversationMonitoringBridge(_registry())
        assert b.health("wf1") is True
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
        assert all(isinstance(c, WorkflowCard) for c in cards)

    def test_overview(self):
        b = DashboardMonitoringBridge(_registry())
        assert b.overview_card().verdict == "ready"


class TestMonitorImmutability:
    DTO_CLASSES = [
        WorkflowStatus, WorkflowMetricSample, WorkflowMetrics,
        WorkflowHealth, WorkflowSnapshot, WorkflowReport,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
