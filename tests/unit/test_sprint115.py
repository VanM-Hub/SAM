"""Sprint 115 — Connector Binding Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.connectors.connector_descriptor import ConnectorDescriptor
from sam.connectors.connector_capability import ConnectorCapability
from sam.connectors.connector_registry import ConnectorRegistry
from sam.connectors.binding_request import BindingRequest
from sam.connectors.binding_result import BindingResult
from sam.connectors.binding_registry import BindingRegistry
from sam.connectors.binding_validator import BindingValidator, BindingValidationReport
from sam.connectors.binding_history import BindingHistory, BindingHistoryEntry
from sam.connectors.conversation_binding import ConversationBindingBridge
from sam.connectors.dashboard_binding import DashboardBindingBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _make_connectors():
    r = ConnectorRegistry()
    r.register(ConnectorDescriptor("c1", "OpenAI", "llm"))
    r.attach_capability(ConnectorCapability("cap1", "c1", "generate", "llm"))
    return r


# ============================================================
# DTO
# ============================================================
class TestBindingRequest:
    def test_create(self):
        req = BindingRequest("b1", "c1", ["cap1"], "qa")
        assert req.request_id == "b1"
        assert req.purpose == "qa"

    def test_immutable(self):
        req = BindingRequest("b1", "c1")
        with pytest.raises(FrozenInstanceError):
            req.connector_id = "x"


class TestBindingResult:
    def test_create(self):
        r = BindingResult("b1", "c1", True, "ok", ["cap1"])
        assert r.success is True

    def test_immutable(self):
        r = BindingResult("b1", "c1")
        with pytest.raises(FrozenInstanceError):
            r.success = True


# ============================================================
# Engine — BindingRegistry
# ============================================================
class TestBindingRegistry:
    def test_bind_success(self):
        br = BindingRegistry(_make_connectors())
        res = br.bind(BindingRequest("b1", "c1", ["cap1"]))
        assert res.success is True
        assert br.count() == 1

    def test_bind_unknown_connector(self):
        br = BindingRegistry(_make_connectors())
        res = br.bind(BindingRequest("b1", "ghost", ["cap1"]))
        assert res.success is False

    def test_bind_missing_capability(self):
        br = BindingRegistry(_make_connectors())
        res = br.bind(BindingRequest("b1", "c1", ["nope"]))
        assert res.success is False
        assert "missing" in res.message

    def test_get(self):
        br = BindingRegistry(_make_connectors())
        br.bind(BindingRequest("b1", "c1", ["cap1"]))
        assert br.get("b1").success is True

    def test_get_missing(self):
        br = BindingRegistry(_make_connectors())
        assert br.get("ghost") is None


# ============================================================
# Engine — BindingValidator
# ============================================================
class TestBindingValidator:
    def test_valid(self):
        v = BindingValidator(_make_connectors())
        report = v.validate(BindingRequest("b1", "c1", ["cap1"]))
        assert report.valid is True

    def test_invalid_connector(self):
        v = BindingValidator(_make_connectors())
        report = v.validate(BindingRequest("b1", "ghost", ["cap1"]))
        assert report.valid is False
        assert any("connector" in i for i in report.issues)

    def test_no_capabilities(self):
        v = BindingValidator(_make_connectors())
        report = v.validate(BindingRequest("b1", "c1", []))
        assert report.valid is False


# ============================================================
# Engine — BindingHistory
# ============================================================
class TestBindingHistory:
    def test_record_and_all(self):
        h = BindingHistory()
        h.record(BindingResult("b1", "c1", True))
        h.record(BindingResult("b2", "c2", False))
        assert h.count() == 2

    def test_by_connector(self):
        h = BindingHistory()
        h.record(BindingResult("b1", "c1", True))
        h.record(BindingResult("b2", "c1", True))
        h.record(BindingResult("b3", "c2", True))
        assert len(h.by_connector("c1")) == 2


# ============================================================
# Bridges
# ============================================================
class TestConversationBindingBridge:
    def test_count(self):
        br = BindingRegistry(_make_connectors())
        br.bind(BindingRequest("b1", "c1", ["cap1"]))
        b = ConversationBindingBridge(br)
        assert b.count() == 1


class TestDashboardBindingBridge:
    def test_five_cards(self):
        br = BindingRegistry(_make_connectors())
        b = DashboardBindingBridge(br)
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)


# ============================================================
# Immutability
# ============================================================
class TestBindingImmutability:
    DTO_CLASSES = [BindingRequest, BindingResult, BindingValidationReport, BindingHistoryEntry]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
