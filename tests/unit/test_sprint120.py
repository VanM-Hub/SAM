"""Sprint 120 — Connector Monitoring Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.connectors.connector_descriptor import ConnectorDescriptor
from sam.connectors.connector_capability import ConnectorCapability
from sam.connectors.connector_registry import ConnectorRegistry
from sam.connectors.connector_metrics import ConnectorMetrics
from sam.connectors.connector_health import ConnectorHealth, ConnectorHealthChecker
from sam.connectors.connector_statistics import (
    ConnectorStatistics, ConnectorStatisticsCollector,
)
from sam.connectors.connector_snapshot import ConnectorSnapshot
from sam.connectors.connector_history import ConnectorHistory
from sam.connectors.conversation_monitor import ConversationMonitorBridge
from sam.connectors.dashboard_monitor import DashboardMonitorBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _make_registry():
    r = ConnectorRegistry()
    r.register(ConnectorDescriptor("c1", "OpenAI", "llm"))
    r.attach_capability(ConnectorCapability("cap1", "c1", "generate", "llm"))
    r.register(ConnectorDescriptor("c2", "Postgres", "db"))  # no capability -> degraded
    return r


# ============================================================
# DTO
# ============================================================
class TestConnectorMetrics:
    def test_create(self):
        m = ConnectorMetrics("c1", bindings=2, sessions=3)
        assert m.bindings == 2

    def test_immutable(self):
        m = ConnectorMetrics("c1")
        with pytest.raises(FrozenInstanceError):
            m.bindings = 5


class TestConnectorHealth:
    def test_default(self):
        h = ConnectorHealth("c1")
        assert h.status == "unknown"

    def test_immutable(self):
        h = ConnectorHealth("c1")
        with pytest.raises(FrozenInstanceError):
            h.status = "healthy"


class TestConnectorSnapshot:
    def test_default(self):
        s = ConnectorSnapshot("c1")
        assert s.state == "unknown"

    def test_immutable(self):
        s = ConnectorSnapshot("c1")
        with pytest.raises(FrozenInstanceError):
            s.health = "ok"


# ============================================================
# Engine — ConnectorHealthChecker
# ============================================================
class TestConnectorHealthChecker:
    def test_healthy(self):
        c = ConnectorHealthChecker(_make_registry())
        h = c.check("c1")
        assert h.status == "healthy"

    def test_degraded_no_capability(self):
        c = ConnectorHealthChecker(_make_registry())
        h = c.check("c2")
        assert h.status == "degraded"
        assert any("capabilities" in i for i in h.issues)

    def test_unknown(self):
        c = ConnectorHealthChecker(_make_registry())
        h = c.check("ghost")
        assert h.status == "unknown"
        assert h.registered is False


# ============================================================
# Engine — ConnectorStatisticsCollector
# ============================================================
class TestConnectorStatisticsCollector:
    def test_collect(self):
        s = ConnectorStatisticsCollector(_make_registry()).collect()
        assert s.total_connectors == 2
        assert s.healthy == 1
        assert s.degraded == 1
        assert s.by_type["llm"] == 1


# ============================================================
# Engine — ConnectorHistory
# ============================================================
class TestConnectorHistory:
    def test_record_and_by_connector(self):
        h = ConnectorHistory()
        h.record(ConnectorSnapshot("c1", "active"))
        h.record(ConnectorSnapshot("c1", "closed"))
        h.record(ConnectorSnapshot("c2", "active"))
        assert h.count() == 3
        assert len(h.by_connector("c1")) == 2


# ============================================================
# Bridges
# ============================================================
class TestConversationMonitorBridge:
    def test_health(self):
        b = ConversationMonitorBridge(_make_registry())
        assert b.health("c1").status == "healthy"

    def test_statistics(self):
        b = ConversationMonitorBridge(_make_registry())
        assert b.statistics().total_connectors == 2

    def test_healthy_ids(self):
        b = ConversationMonitorBridge(_make_registry())
        assert b.healthy_ids() == ["c1"]


class TestDashboardMonitorBridge:
    def test_five_cards(self):
        b = DashboardMonitorBridge(_make_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)


# ============================================================
# Immutability
# ============================================================
class TestMonitorImmutability:
    DTO_CLASSES = [ConnectorMetrics, ConnectorHealth, ConnectorStatistics, ConnectorSnapshot]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
