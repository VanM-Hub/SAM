# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 137 - Mission Resources tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.mission_runtime.resource_descriptor import ResourceDescriptor
from sam.mission_runtime.resource_inventory import ResourceInventory
from sam.mission_runtime.resource_allocator import ResourceAllocator, ResourceAllocation
from sam.mission_runtime.resource_validator import (
    ResourceValidator,
    ResourceValidationReport,
)
from sam.mission_runtime.resource_summary import ResourceSummary
from sam.mission_runtime.conversation_resource import ConversationResourceBridge
from sam.mission_runtime.dashboard_resource import DashboardResourceBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _inventory():
    inv = ResourceInventory()
    inv.add(ResourceDescriptor("r1", available=True))
    inv.add(ResourceDescriptor("r2", available=False))
    inv.add(ResourceDescriptor("r3", available=True))
    return inv


class TestDescriptorImmutable:
    def test_frozen(self):
        d = ResourceDescriptor("r")
        with pytest.raises(FrozenInstanceError):
            d.name = "x"


class TestInventory:
    def test_count(self):
        assert _inventory().count() == 3

    def test_get(self):
        assert _inventory().get("r2").available is False


class TestAllocator:
    def test_allocate_available_only(self):
        allocation = ResourceAllocator(_inventory()).allocate()
        assert allocation.ids == ("r1", "r3")
        assert allocation.count == 2

    def test_allocation_frozen(self):
        a = ResourceAllocator(_inventory()).allocate()
        with pytest.raises(FrozenInstanceError):
            a.allocated = ()


class TestResourceValidator:
    def test_valid(self):
        a = ResourceAllocator(_inventory()).allocate()
        assert ResourceValidator().validate(a).valid is True

    def test_duplicate_invalid(self):
        a = ResourceAllocation(
            (ResourceDescriptor("r1"), ResourceDescriptor("r1")),
        )
        assert ResourceValidator().validate(a).valid is False


class TestResourceSummary:
    def test_frozen(self):
        s = ResourceSummary(("a",))
        with pytest.raises(FrozenInstanceError):
            s.total = 9


# ---------- Conversation bridge ----------
class TestConversationResourceBridge:
    def test_add_allocate(self):
        b = ConversationResourceBridge(ResourceInventory())
        b.add("r1")
        b.add("r2", available=False)
        assert b.allocate().count == 1

    def test_summarize(self):
        b = ConversationResourceBridge(ResourceInventory())
        b.add("r1")
        s = b.summarize()
        assert s.total == 1


# ---------- Dashboard bridge ----------
class TestDashboardResourceBridge:
    def test_five_cards(self):
        b = ConversationResourceBridge(ResourceInventory())
        b.add("r1", available=True)
        cards = DashboardResourceBridge().cards_for(b.summarize())
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        s = ResourceSummary(("a",))
        b = DashboardResourceBridge()
        assert "allocated" in b.verdict_card(s).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [ResourceDescriptor, ResourceAllocation, ResourceValidationReport, ResourceSummary]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
