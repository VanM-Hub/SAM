# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 141 - Mission Monitoring tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.mission_runtime.mission_metrics import MissionMetrics
from sam.mission_runtime.mission_health import MissionHealth
from sam.mission_runtime.mission_history import MissionHistory
from sam.mission_runtime.mission_statistics import MissionStatistics
from sam.mission_runtime.mission_report import MissionReport
from sam.mission_runtime.conversation_monitor import ConversationMonitorBridge
from sam.mission_runtime.dashboard_monitor import DashboardMonitorBridge
from sam.connectors.dashboard_connector import ExecutionCard


class TestMetricsImmutable:
    def test_frozen(self):
        m = MissionMetrics("m")
        with pytest.raises(FrozenInstanceError):
            m.objectives_total = 1

    def test_preview_always(self):
        assert MissionMetrics("m", external_calls=0).is_preview is True

    def test_external_zero(self):
        assert MissionMetrics("m").external_calls == 0


class TestHealthImmutable:
    def test_frozen(self):
        h = MissionHealth("m")
        with pytest.raises(FrozenInstanceError):
            h.state = "critical"

    def test_properties(self):
        assert MissionHealth("m", "healthy").is_healthy is True
        assert MissionHealth("m", "critical").is_critical is True


class TestStatisticsImmutable:
    def test_frozen(self):
        s = MissionStatistics("m")
        with pytest.raises(FrozenInstanceError):
            s.progress = 1.0


class TestReportImmutable:
    def test_frozen(self):
        r = MissionReport(MissionMetrics("m"), MissionHealth("m"), MissionStatistics("m"))
        with pytest.raises(FrozenInstanceError):
            r.metrics = MissionMetrics("x")

    def test_ok(self):
        r = MissionReport(
            MissionMetrics("m", external_calls=0),
            MissionHealth("m", "healthy"),
            MissionStatistics("m"),
        )
        assert r.ok is True

    def test_not_ok_critical(self):
        r = MissionReport(
            MissionMetrics("m", external_calls=0),
            MissionHealth("m", "critical"),
            MissionStatistics("m"),
        )
        assert r.ok is False


class TestMissionHistory:
    def test_record(self):
        h = MissionHistory()
        h.record(MissionHealth("m"))
        assert h.count() == 1

    def test_clear(self):
        h = MissionHistory()
        h.record(MissionHealth("m"))
        h.clear()
        assert h.count() == 0


# ---------- Conversation bridge ----------
class TestConversationMonitorBridge:
    def test_report(self):
        r = ConversationMonitorBridge().report("m")
        assert r.ok is True

    def test_health(self):
        assert ConversationMonitorBridge().health("m").is_healthy is True


# ---------- Dashboard bridge ----------
class TestDashboardMonitorBridge:
    def test_five_cards(self):
        r = ConversationMonitorBridge().report("m")
        cards = DashboardMonitorBridge().cards_for(r)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        r = ConversationMonitorBridge().report("m")
        b = DashboardMonitorBridge()
        assert "preview" in b.verdict_card(r).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [MissionMetrics, MissionHealth, MissionStatistics, MissionReport]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
