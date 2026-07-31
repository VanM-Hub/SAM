"""Sprint 117 — Connector Routing Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.connectors.connector_descriptor import ConnectorDescriptor
from sam.connectors.connector_capability import ConnectorCapability
from sam.connectors.connector_registry import ConnectorRegistry
from sam.connectors.connector_router import ConnectorRouter, RoutingPolicy, RoutingResult
from sam.connectors.routing_validator import RoutingValidator, RoutingValidationReport
from sam.connectors.routing_summary import RoutingSummary, RoutingSummarizer
from sam.connectors.conversation_routing import ConversationRoutingBridge
from sam.connectors.dashboard_routing import DashboardRoutingBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _make_registry():
    r = ConnectorRegistry()
    r.register(ConnectorDescriptor("c1", "OpenAI", "llm"))
    r.register(ConnectorDescriptor("c2", "Anthropic", "llm"))
    r.register(ConnectorDescriptor("c3", "Postgres", "db"))
    r.attach_capability(ConnectorCapability("cap1", "c1", "generate", "llm"))
    r.attach_capability(ConnectorCapability("cap2", "c2", "generate", "llm"))
    r.attach_capability(ConnectorCapability("cap3", "c3", "query", "db"))
    return r


# ============================================================
# RoutingPolicy / RoutingResult DTO
# ============================================================
class TestRoutingPolicy:
    def test_create(self):
        p = RoutingPolicy("p1", "capability", ["llm"])
        assert p.strategy == "capability"

    def test_defaults(self):
        p = RoutingPolicy("p1")
        assert p.strategy == "capability"
        assert p.preferred_types == []

    def test_immutable(self):
        p = RoutingPolicy("p1")
        with pytest.raises(FrozenInstanceError):
            p.strategy = "x"


class TestRoutingResult:
    def test_create(self):
        r = RoutingResult("generate", "c1", "p1", True, "routed")
        assert r.routed is True

    def test_immutable(self):
        r = RoutingResult("gen")
        with pytest.raises(FrozenInstanceError):
            r.routed = True


# ============================================================
# Engine — ConnectorRouter
# ============================================================
class TestConnectorRouter:
    def test_route_success(self):
        router = ConnectorRouter(_make_registry())
        res = router.route("generate", RoutingPolicy("p1"))
        assert res.routed is True
        assert res.selected_connector_id in ("c1", "c2")

    def test_route_no_capability(self):
        router = ConnectorRouter(_make_registry())
        res = router.route("stream", RoutingPolicy("p1"))
        assert res.routed is False

    def test_route_preferred_type(self):
        router = ConnectorRouter(_make_registry())
        res = router.route("generate", RoutingPolicy("p1", preferred_types=["db"]))
        assert res.routed is False  # db tidak support generate

    def test_route_deterministic(self):
        router = ConnectorRouter(_make_registry())
        res1 = router.route("generate", RoutingPolicy("p1"))
        res2 = router.route("generate", RoutingPolicy("p1"))
        assert res1.selected_connector_id == res2.selected_connector_id


# ============================================================
# Engine — RoutingValidator
# ============================================================
class TestRoutingValidator:
    def test_valid(self):
        v = RoutingValidator()
        report = v.validate(RoutingPolicy("p1"))
        assert report.valid is True

    def test_invalid_strategy(self):
        v = RoutingValidator()
        report = v.validate(RoutingPolicy("p1", "bad_strategy"))
        assert report.valid is False


# ============================================================
# Engine — RoutingSummarizer
# ============================================================
class TestRoutingSummarizer:
    def test_summary(self):
        s = RoutingSummarizer()
        res = RoutingSummarizer().summarize([
            RoutingResult("a", "c1", routed=True),
            RoutingResult("b", routed=False),
        ])
        assert res.total_routes == 2
        assert res.routed == 1
        assert res.failures == 1


# ============================================================
# Bridges
# ============================================================
class TestConversationRoutingBridge:
    def test_route(self):
        b = ConversationRoutingBridge(_make_registry())
        res = b.route("generate")
        assert res.routed is True

    def test_available_capabilities(self):
        b = ConversationRoutingBridge(_make_registry())
        assert b.available_capabilities() == ["generate", "query"]


class TestDashboardRoutingBridge:
    def test_five_cards(self):
        b = DashboardRoutingBridge(_make_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)


# ============================================================
# Immutability
# ============================================================
class TestRoutingImmutability:
    DTO_CLASSES = [RoutingPolicy, RoutingResult, RoutingValidationReport, RoutingSummary]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
