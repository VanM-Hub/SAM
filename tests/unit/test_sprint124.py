# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 124 - Runtime Discovery tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.orchestrator.runtime_descriptor import RuntimeDescriptor
from sam.orchestrator.runtime_catalog import RuntimeCatalog
from sam.orchestrator.runtime_locator import RuntimeLocator
from sam.orchestrator.runtime_inventory import RuntimeInventory, RuntimeInventoryBuilder
from sam.orchestrator.runtime_validator import RuntimeValidator, DiscoveryValidationReport
from sam.orchestrator.conversation_runtime import ConversationRuntimeBridge
from sam.orchestrator.dashboard_runtime import DashboardRuntimeBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _catalog():
    c = RuntimeCatalog()
    c.add(RuntimeDescriptor("execution", "Execution", version="9.0.0", pipeline_position=6))
    c.add(RuntimeDescriptor("connector", "Connector", version="11.0.0", pipeline_position=8, tags=("external",)))
    c.add(RuntimeDescriptor("orchestration", "Orchestrator", version="12.0.0", pipeline_position=9, tags=("orchestrator",)))
    return c


class TestDescriptorImmutable:
    def test_frozen(self):
        d = RuntimeDescriptor("x", "X")
        with pytest.raises(FrozenInstanceError):
            d.name = "Y"


# ---------- Catalog + Locator ----------
class TestRuntimeCatalog:
    def test_add_count(self):
        assert _catalog().count() == 3

    def test_get(self):
        assert _catalog().get("connector").version == "11.0.0"

    def test_all_ordered(self):
        order = [d.runtime_id for d in _catalog().all()]
        assert order == ["execution", "connector", "orchestration"]


class TestRuntimeLocator:
    def test_by_id(self):
        l = RuntimeLocator(_catalog())
        assert l.by_id("execution").pipeline_position == 6

    def test_by_position(self):
        l = RuntimeLocator(_catalog())
        assert len(l.by_position(9)) == 1

    def test_by_tag(self):
        l = RuntimeLocator(_catalog())
        assert len(l.by_tag("external")) == 1


# ---------- Inventory ----------
class TestRuntimeInventory:
    def test_build(self):
        inv = RuntimeInventoryBuilder(_catalog()).build()
        assert inv.count == 3
        assert inv.ids[0] == "execution"

    def test_frozen(self):
        inv = RuntimeInventoryBuilder(_catalog()).build()
        with pytest.raises(FrozenInstanceError):
            inv.runtimes = ()


# ---------- Validator ----------
class TestRuntimeValidator:
    def test_valid(self):
        r = RuntimeValidator(_catalog()).validate()
        assert r.valid is True

    def test_invalid_negative_position(self):
        c = RuntimeCatalog()
        c.add(RuntimeDescriptor("bad", "Bad", pipeline_position=-1))
        r = RuntimeValidator(c).validate()
        assert r.valid is False
        assert r.issue_count == 1


# ---------- Conversation bridge ----------
class TestConversationRuntimeBridge:
    def test_count(self):
        assert ConversationRuntimeBridge(_catalog()).count() == 3

    def test_locate(self):
        b = ConversationRuntimeBridge(_catalog())
        assert b.locate("connector").name == "Connector"

    def test_inventory(self):
        b = ConversationRuntimeBridge(_catalog())
        assert b.inventory().count == 3

    def test_names(self):
        b = ConversationRuntimeBridge(_catalog())
        assert "Orchestrator" in b.list_names()


# ---------- Dashboard bridge ----------
class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        cards = DashboardRuntimeBridge(_catalog()).cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        b = DashboardRuntimeBridge(_catalog())
        assert "inventory" in b.verdict_card().summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [RuntimeDescriptor, RuntimeInventory, DiscoveryValidationReport]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
