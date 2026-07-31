"""Sprint 172 — Memory Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.memory.foundation.memory_descriptor import MemoryDescriptor
from sam.memory.foundation.memory_capability import MemoryCapability
from sam.memory.foundation.memory_contract import MemoryContract, MemoryContractCompliance
from sam.memory.foundation.memory_metadata import MemoryMetadata
from sam.memory.foundation.memory_registry import MemoryRegistry, MemoryRegistrySummary
from sam.memory.foundation.conversation_memory import ConversationMemoryBridge
from sam.memory.foundation.dashboard_memory import DashboardMemoryBridge
from sam.memory.dashboard.memory_dashboard import ExecutionCard


def _ready_registry():
    r = MemoryRegistry()
    r.register(MemoryDescriptor("mem1", "Short Term", category="short_term"))
    r.attach_capability(MemoryCapability("cap1", "mem1", "retain",
                                         operations=["retain", "recall"]))
    r.attach_contract(MemoryContract("ct1", "mem1", "memory-contract",
                                     guarantees=["preview-only"]))
    r.attach_metadata(MemoryMetadata("mem1", author="SAM"))
    return r


class TestMemoryDescriptor:
    def test_default(self):
        d = MemoryDescriptor("m1")
        assert d.category == "general"
        assert d.tags == []
        assert d.scopes == []

    def test_immutable(self):
        d = MemoryDescriptor("m1")
        with pytest.raises(FrozenInstanceError):
            d.name = "x"


class TestMemoryCapability:
    def test_supports(self):
        c = MemoryCapability("c1", "m1", operations=["retain"])
        assert c.supports("retain")
        assert not c.supports("delete")

    def test_preview_default(self):
        assert MemoryCapability("c1", "m1").preview_only is True

    def test_immutable(self):
        c = MemoryCapability("c1", "m1")
        with pytest.raises(FrozenInstanceError):
            c.name = "x"


class TestMemoryContract:
    def test_default(self):
        assert MemoryContract("ct1", "m1").guarantees == []

    def test_immutable(self):
        c = MemoryContract("ct1", "m1")
        with pytest.raises(FrozenInstanceError):
            c.name = "x"


class TestMemoryContractCompliance:
    def test_default(self):
        assert MemoryContractCompliance("ct1", "m1").compliant is True


class TestMemoryMetadata:
    def test_readonly(self):
        assert MemoryMetadata("m1").readonly is True

    def test_immutable(self):
        m = MemoryMetadata("m1")
        with pytest.raises(FrozenInstanceError):
            m.author = "x"


class TestMemoryRegistry:
    def test_register_find(self):
        r = _ready_registry()
        assert r.exists("mem1")
        assert r.find("mem1").name == "Short Term"

    def test_list(self):
        r = _ready_registry()
        assert r.list_ids() == ["mem1"]

    def test_duplicate_rejected(self):
        r = MemoryRegistry()
        assert r.register(MemoryDescriptor("m1"))
        assert not r.register(MemoryDescriptor("m1"))

    def test_exists_missing(self):
        assert MemoryRegistry().exists("nope") is False

    def test_capabilities(self):
        r = _ready_registry()
        assert r.get_capabilities("mem1")[0].supports("retain")

    def test_contract(self):
        r = _ready_registry()
        assert "preview-only" in r.get_contract("mem1").guarantees

    def test_metadata(self):
        r = _ready_registry()
        assert r.get_metadata("mem1").author == "SAM"

    def test_summary(self):
        r = _ready_registry()
        s = r.summary()
        assert s.total == 1
        assert s.by_category["short_term"] == 1

    def test_count(self):
        r = _ready_registry()
        assert r.count() == 1


class TestMemoryRegistrySummary:
    def test_default(self):
        assert MemoryRegistrySummary().total == 0


class TestConversationMemoryBridge:
    def test_query_1_summary(self):
        b = ConversationMemoryBridge(_ready_registry())
        assert b.query_1_summary()["total"] == 1

    def test_query_2_list(self):
        b = ConversationMemoryBridge(_ready_registry())
        assert b.query_2_list() == ["mem1"]

    def test_query_3_descriptor(self):
        b = ConversationMemoryBridge(_ready_registry())
        assert b.query_3_descriptor("mem1") == "Short Term"

    def test_query_4_metadata(self):
        b = ConversationMemoryBridge(_ready_registry())
        assert b.query_4_metadata("mem1")["author"] == "SAM"

    def test_query_5_capability(self):
        b = ConversationMemoryBridge(_ready_registry())
        assert b.query_5_capability("mem1") == ["cap1"]


class TestDashboardMemoryBridge:
    def test_five_cards(self):
        b = DashboardMemoryBridge(_ready_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardMemoryBridge(_ready_registry())
        assert b.overview_card().verdict == "ready"


class TestMemoryFoundationImmutability:
    DTO_CLASSES = [
        MemoryDescriptor, MemoryCapability, MemoryContract,
        MemoryContractCompliance, MemoryMetadata, MemoryRegistrySummary, ExecutionCard,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
