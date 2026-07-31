"""Sprint 225 — Artifact Monitoring Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.artifact_runtime.monitoring.artifact_monitor import (
    ArtifactMonitor, ArtifactStatus,
)
from sam.artifact_runtime.monitoring.artifact_metrics import (
    ArtifactMetrics, ArtifactMetricSample, ArtifactMetricsCollector,
)
from sam.artifact_runtime.monitoring.artifact_health import (
    ArtifactHealth, ArtifactHealthCheck,
)
from sam.artifact_runtime.monitoring.artifact_snapshot import (
    ArtifactSnapshot, ArtifactSnapshotter,
)
from sam.artifact_runtime.monitoring.artifact_report import (
    ArtifactReport, ArtifactReporter,
)
from sam.artifact_runtime.monitoring.conversation_monitoring import (
    ConversationMonitoringBridge,
)
from sam.artifact_runtime.monitoring.dashboard_monitoring import (
    DashboardMonitoringBridge,
)
from sam.artifact_runtime.dashboard import PolicyCard


class TestArtifactMonitor:
    def test_status(self):
        s = ArtifactMonitor().status()
        assert s.state == "ready"
        assert s.external_calls == 0


class TestArtifactStatus:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactStatus().state = "x"


class TestArtifactMetricsCollector:
    def test_collect(self):
        m = ArtifactMetricsCollector().collect({"report": 2, "log": 1})
        assert len(m.samples) == 2
        assert m.external_calls == 0

    def test_sorted(self):
        m = ArtifactMetricsCollector().collect({"b": 1, "a": 2})
        assert [s.kind for s in m.samples] == ["a", "b"]


class TestArtifactMetrics:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactMetrics().external_calls = 1


class TestArtifactMetricSample:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactMetricSample().value = 5


class TestArtifactHealthCheck:
    def test_check(self):
        assert ArtifactHealthCheck().check().healthy is True


class TestArtifactHealth:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactHealth().healthy = False


class TestArtifactSnapshotter:
    def test_snapshot(self):
        s = ArtifactSnapshotter().snapshot(("a", "b"))
        assert len(s.names) == 2
        assert s.external_calls == 0


class TestArtifactSnapshot:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactSnapshot().names = ("x",)


class TestArtifactReporter:
    def test_report(self):
        r = ArtifactReporter().report(3)
        assert r.total == 3
        assert r.ready is True


class TestArtifactReport:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactReport().total = 1


class TestConversationMonitoringBridge:
    def test_five_queries(self):
        b = ConversationMonitoringBridge()
        assert b.query_1_status()["state"] == "ready"
        assert b.query_2_metrics()["external_calls"] == 0
        assert b.query_3_health()["healthy"] is True
        assert b.query_4_snapshot()["count"] == 2
        assert b.query_5_report()["ready"] is True


class TestDashboardMonitoringBridge:
    def test_five_cards(self):
        cards = DashboardMonitoringBridge().cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)


class TestMonitoringImmutability:
    DTO = [ArtifactStatus, ArtifactMetrics, ArtifactMetricSample, ArtifactHealth,
           ArtifactSnapshot, ArtifactReport]

    def test_all_frozen(self):
        for cls in self.DTO:
            assert cls.__dataclass_params__.frozen
