"""Sprint 116 — Connector Session Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.connectors.session_context import SessionContext
from sam.connectors.connector_session import ConnectorSessionManager
from sam.connectors.session_registry import SessionRegistry
from sam.connectors.session_snapshot import SessionSnapshot
from sam.connectors.session_summary import SessionSummary, SessionSummarizer
from sam.connectors.conversation_session import ConversationSessionBridge
from sam.connectors.dashboard_session import DashboardSessionBridge
from sam.connectors.dashboard_connector import ExecutionCard


# ============================================================
# DTO
# ============================================================
class TestSessionContext:
    def test_create(self):
        c = SessionContext("s1", "c1", "b1", "active")
        assert c.session_id == "s1"
        assert c.state == "active"

    def test_defaults(self):
        c = SessionContext("s1", "c1")
        assert c.state == "created"
        assert c.binding_id == ""

    def test_immutable(self):
        c = SessionContext("s1", "c1")
        with pytest.raises(FrozenInstanceError):
            c.state = "active"


class TestSessionSnapshot:
    def test_create(self):
        s = SessionSnapshot("s1", "active", "c1")
        assert s.state == "active"

    def test_immutable(self):
        s = SessionSnapshot("s1")
        with pytest.raises(FrozenInstanceError):
            s.state = "x"


# ============================================================
# Engine — ConnectorSessionManager
# ============================================================
class TestConnectorSessionManager:
    def test_create(self):
        m = ConnectorSessionManager()
        ctx = m.create("s1", "c1", "b1")
        assert ctx.state == "created"
        assert m.count() == 1

    def test_activate(self):
        m = ConnectorSessionManager()
        m.create("s1", "c1")
        ctx = m.activate("s1")
        assert ctx.state == "active"

    def test_close(self):
        m = ConnectorSessionManager()
        m.create("s1", "c1")
        m.activate("s1")
        ctx = m.close("s1")
        assert ctx.state == "closed"

    def test_activate_missing(self):
        m = ConnectorSessionManager()
        assert m.activate("nope") is None

    def test_get(self):
        m = ConnectorSessionManager()
        m.create("s1", "c1")
        assert m.get("s1").connector_id == "c1"


# ============================================================
# Engine — SessionRegistry
# ============================================================
class TestSessionRegistry:
    def test_register_and_get(self):
        r = SessionRegistry()
        r.register(SessionContext("s1", "c1"))
        assert r.get("s1").connector_id == "c1"
        assert r.count() == 1

    def test_by_connector(self):
        r = SessionRegistry()
        r.register(SessionContext("s1", "c1"))
        r.register(SessionContext("s2", "c1"))
        r.register(SessionContext("s3", "c2"))
        assert r.by_connector("c1") == ["s1", "s2"]


# ============================================================
# Engine — SessionSummarizer
# ============================================================
class TestSessionSummarizer:
    def test_summary(self):
        m = ConnectorSessionManager()
        m.create("s1", "c1")
        m.create("s2", "c1")
        m.create("s3", "c1")
        m.activate("s1")
        m.close("s2")
        s = SessionSummarizer(m).summarize()
        assert s.total_sessions == 3
        assert s.active == 1
        assert s.closed == 1
        assert s.created == 1


# ============================================================
# Bridges
# ============================================================
class TestConversationSessionBridge:
    def test_summary(self):
        m = ConnectorSessionManager()
        m.create("s1", "c1")
        b = ConversationSessionBridge(m)
        assert b.count() == 1
        assert b.summary().total_sessions == 1


class TestDashboardSessionBridge:
    def test_five_cards(self):
        m = ConnectorSessionManager()
        m.create("s1", "c1")
        b = DashboardSessionBridge(m)
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)


# ============================================================
# Immutability
# ============================================================
class TestSessionImmutability:
    DTO_CLASSES = [SessionContext, SessionSnapshot, SessionSummary]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
