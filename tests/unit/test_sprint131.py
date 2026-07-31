# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 131 - Monitoring tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.orchestrator.orchestration_metrics import OrchestrationMetrics
from sam.orchestrator.orchestration_health import OrchestrationHealth
from sam.orchestrator.orchestration_history import OrchestrationHistory
from sam.orchestrator.orchestration_statistics import OrchestrationStatistics
from sam.orchestrator.orchestration_report import OrchestrationReport
from sam.orchestrator.conversation_monitor import ConversationMonitorBridge
from sam.orchestrator.dashboard_monitor import DashboardMonitorBridge
from sam.connectors.dashboard_connector import ExecutionCard


class TestMetricsImmutable:
    def test_frozen(self):
        m = OrchestrationMetrics()
        with pytest.raises(FrozenInstanceError):
            m.plans_built = 1

    def test_preview_always(self):
        m = OrchestrationMetrics(external_calls=0)
        assert m.is_preview is True

    def test_external_calls_zero_default(self):
        assert OrchestrationMetrics().external_calls == 0


class TestHealthImmutable:
    def test_frozen(self):
        h = OrchestrationHealth()
        with pytest.raises(FrozenInstanceError):
            h.state = "degraded"

    def test_properties(self):
        assert OrchestrationHealth("healthy").is_healthy is True
        assert OrchestrationHealth("degraded").is_degraded is True


class TestStatisticsImmutable:
    def test_frozen(self):
        s = OrchestrationStatistics()
        with pytest.raises(FrozenInstanceError):
            s.plans = 1


class TestReportImmutable:
    def test_frozen(self):
        r = OrchestrationReport(
            OrchestrationMetrics(),
            OrchestrationHealth(),
            OrchestrationStatistics(),
        )
        with pytest.raises(FrozenInstanceError):
            r.metrics = OrchestrationMetrics()

    def test_ok(self):
        r = OrchestrationReport(
            OrchestrationMetrics(external_calls=0),
            OrchestrationHealth("healthy"),
            OrchestrationStatistics(),
        )
        assert r.ok is True

    def test_not_ok_degraded(self):
        r = OrchestrationReport(
            OrchestrationMetrics(external_calls=0),
            OrchestrationHealth("degraded"),
            OrchestrationStatistics(),
        )
        assert r.ok is False


class TestOrchestrationHistory:
    def test_record_count(self):
        h = OrchestrationHistory()
        h.record(OrchestrationHealth("healthy"))
        h.record(OrchestrationHealth("degraded"))
        assert h.count() == 2

    def test_clear(self):
        h = OrchestrationHistory()
        h.record(OrchestrationHealth())
        h.clear()
        assert h.count() == 0


# ---------- Conversation bridge ----------
class TestConversationMonitorBridge:
    def test_report(self):
        r = ConversationMonitorBridge().report()
        assert r.ok is True

    def test_health(self):
        assert ConversationMonitorBridge().health().is_healthy is True


# ---------- Dashboard bridge ----------
class TestDashboardMonitorBridge:
    def test_five_cards(self):
        r = ConversationMonitorBridge().report()
        cards = DashboardMonitorBridge().cards_for(r)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        r = ConversationMonitorBridge().report()
        b = DashboardMonitorBridge()
        assert "preview" in b.verdict_card(r).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        OrchestrationMetrics,
        OrchestrationHealth,
        OrchestrationStatistics,
        OrchestrationReport,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
