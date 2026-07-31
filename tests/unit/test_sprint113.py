"""Sprint 113 — Connector Discovery Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.connectors.connector_descriptor import ConnectorDescriptor
from sam.connectors.connector_registry import ConnectorRegistry
from sam.connectors.connector_discovery import DiscoveryResult, DiscoveryReport
from sam.connectors.connector_locator import ConnectorLocator
from sam.connectors.connector_catalog import ConnectorCatalog
from sam.connectors.connector_filter import ConnectorFilter
from sam.connectors.connector_validator import (
    ConnectorValidator, ValidationIssue, ValidationReport,
)
from sam.connectors.conversation_discovery import ConversationDiscoveryBridge
from sam.connectors.dashboard_discovery import DashboardDiscoveryBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _make_registry():
    r = ConnectorRegistry()
    r.register(ConnectorDescriptor("c1", "OpenAI", "llm", tags=["ai", "cloud"]))
    r.register(ConnectorDescriptor("c2", "Postgres", "db", tags=["storage"]))
    r.register(ConnectorDescriptor("c3", "Anthropic", "llm", tags=["ai"]))
    return r


# ============================================================
# DTO — DiscoveryResult / DiscoveryReport
# ============================================================
class TestDiscoveryResult:
    def test_create(self):
        r = DiscoveryResult("c1", "OpenAI", "llm", found=True)
        assert r.connector_id == "c1"
        assert r.found is True

    def test_defaults(self):
        r = DiscoveryResult("c1", "OpenAI")
        assert r.connector_type == "generic"
        assert r.source == "registry"
        assert r.found is False

    def test_immutable(self):
        r = DiscoveryResult("c1", "OpenAI")
        with pytest.raises(FrozenInstanceError):
            r.found = True


class TestDiscoveryReport:
    def test_default(self):
        r = DiscoveryReport()
        assert r.total_scanned == 0
        assert r.results == []

    def test_immutable(self):
        r = DiscoveryReport()
        with pytest.raises(FrozenInstanceError):
            r.found = 5


# ============================================================
# Engine — ConnectorLocator
# ============================================================
class TestConnectorLocator:
    def test_locate(self):
        loc = ConnectorLocator(_make_registry())
        assert loc.locate("c1").name == "OpenAI"

    def test_locate_missing(self):
        loc = ConnectorLocator(_make_registry())
        assert loc.locate("ghost") is None

    def test_locate_by_type(self):
        loc = ConnectorLocator(_make_registry())
        found = loc.locate_by_type("llm")
        assert len(found) == 2
        assert {d.connector_id for d in found} == {"c1", "c3"}

    def test_locate_by_tag(self):
        loc = ConnectorLocator(_make_registry())
        found = loc.locate_by_tag("ai")
        assert len(found) == 2

    def test_scan_all(self):
        loc = ConnectorLocator(_make_registry())
        report = loc.scan_all()
        assert report.total_scanned == 3
        assert report.found == 3
        assert len(report.results) == 3


# ============================================================
# Engine — ConnectorCatalog
# ============================================================
class TestConnectorCatalog:
    def test_index(self):
        cat = ConnectorCatalog(_make_registry())
        idx = cat.index()
        assert len(idx) == 3
        assert idx["c1"].name == "OpenAI"

    def test_categories(self):
        cat = ConnectorCatalog(_make_registry())
        assert cat.categories() == ["db", "llm"]

    def test_by_category(self):
        cat = ConnectorCatalog(_make_registry())
        found = cat.by_category("llm")
        assert len(found) == 2


# ============================================================
# Engine — ConnectorFilter
# ============================================================
class TestConnectorFilter:
    def test_by_type(self):
        f = ConnectorFilter(_make_registry())
        assert len(f.by_type("db")) == 1

    def test_by_tag(self):
        f = ConnectorFilter(_make_registry())
        assert len(f.by_tag("ai")) == 2

    def test_by_name_contains(self):
        f = ConnectorFilter(_make_registry())
        found = f.by_name_contains("open")
        assert len(found) == 1
        assert found[0].connector_id == "c1"

    def test_by_name_case_insensitive(self):
        f = ConnectorFilter(_make_registry())
        assert len(f.by_name_contains("OPEN")) == 1

    def test_by_version(self):
        f = ConnectorFilter(_make_registry())
        # semua default version 1.0.0
        assert len(f.by_version("1.0.0")) == 3


# ============================================================
# Engine — ConnectorValidator
# ============================================================
class TestConnectorValidator:
    def test_valid(self):
        v = ConnectorValidator(_make_registry())
        report = v.validate("c1")
        assert report.valid is True

    def test_missing(self):
        v = ConnectorValidator(_make_registry())
        report = v.validate("ghost")
        assert report.valid is False
        assert report.error_count == 1

    def test_validate_all(self):
        v = ConnectorValidator(_make_registry())
        reports = v.validate_all()
        assert len(reports) == 3
        assert all(r.valid for r in reports)


# ============================================================
# Bridges
# ============================================================
class TestConversationDiscoveryBridge:
    def test_scan(self):
        b = ConversationDiscoveryBridge(_make_registry())
        report = b.scan()
        assert report.found == 3

    def test_categories(self):
        b = ConversationDiscoveryBridge(_make_registry())
        assert b.categories() == ["db", "llm"]

    def test_by_type(self):
        b = ConversationDiscoveryBridge(_make_registry())
        assert b.by_type("llm") == ["c1", "c3"]

    def test_total(self):
        b = ConversationDiscoveryBridge(_make_registry())
        assert b.total_discovered() == 3


class TestDashboardDiscoveryBridge:
    def test_five_cards(self):
        b = DashboardDiscoveryBridge(_make_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_engine_card(self):
        b = DashboardDiscoveryBridge(_make_registry())
        assert "discovered" in b.engine_card().summary


# ============================================================
# Immutability
# ============================================================
class TestDiscoveryImmutability:
    DTO_CLASSES = [DiscoveryResult, DiscoveryReport, ValidationIssue, ValidationReport]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
