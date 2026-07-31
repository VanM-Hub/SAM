"""Sprint 180 — Knowledge Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.knowledge_runtime.foundation.knowledge_descriptor import KnowledgeDescriptor
from sam.knowledge_runtime.foundation.knowledge_capability import KnowledgeCapability
from sam.knowledge_runtime.foundation.knowledge_contract import (
    KnowledgeContract, KnowledgeContractCompliance,
)
from sam.knowledge_runtime.foundation.knowledge_metadata import KnowledgeMetadata
from sam.knowledge_runtime.foundation.knowledge_registry import (
    KnowledgeRegistry, KnowledgeRegistrySummary,
)
from sam.knowledge_runtime.foundation.conversation_knowledge import (
    ConversationKnowledgeBridge,
)
from sam.knowledge_runtime.foundation.dashboard_knowledge import DashboardKnowledgeBridge
from sam.knowledge_runtime.dashboard.knowledge_dashboard import ExecutionCard


def _ready_registry():
    r = KnowledgeRegistry()
    r.register(KnowledgeDescriptor("kn1", "Domain Knowledge", category="domain"))
    r.attach_capability(KnowledgeCapability(
        "cap1", "kn1", "organize", operations=["fact", "relation"],
    ))
    r.attach_contract(KnowledgeContract(
        "ct1", "kn1", "knowledge-contract", guarantees=["no-inference"],
    ))
    r.attach_metadata(KnowledgeMetadata("kn1", author="SAM"))
    return r


class TestKnowledgeDescriptor:
    def test_default(self):
        d = KnowledgeDescriptor("k1")
        assert d.category == "general"
        assert d.fact_types == []
        assert d.relation_types == []

    def test_immutable(self):
        d = KnowledgeDescriptor("k1")
        with pytest.raises(FrozenInstanceError):
            d.name = "x"


class TestKnowledgeCapability:
    def test_supports(self):
        c = KnowledgeCapability("c1", "k1", operations=["fact"])
        assert c.supports("fact")
        assert not c.supports("delete")

    def test_preview_default(self):
        assert KnowledgeCapability("c1", "k1").preview_only is True

    def test_immutable(self):
        c = KnowledgeCapability("c1", "k1")
        with pytest.raises(FrozenInstanceError):
            c.name = "x"


class TestKnowledgeContract:
    def test_default(self):
        assert KnowledgeContract("ct1", "k1").guarantees == []

    def test_immutable(self):
        c = KnowledgeContract("ct1", "k1")
        with pytest.raises(FrozenInstanceError):
            c.name = "x"


class TestKnowledgeContractCompliance:
    def test_default(self):
        assert KnowledgeContractCompliance("ct1", "k1").compliant is True


class TestKnowledgeMetadata:
    def test_readonly(self):
        assert KnowledgeMetadata("k1").readonly is True

    def test_immutable(self):
        m = KnowledgeMetadata("k1")
        with pytest.raises(FrozenInstanceError):
            m.author = "x"


class TestKnowledgeRegistry:
    def test_register_find(self):
        r = _ready_registry()
        assert r.exists("kn1")
        assert r.find("kn1").name == "Domain Knowledge"

    def test_list(self):
        r = _ready_registry()
        assert r.list_ids() == ["kn1"]

    def test_duplicate_rejected(self):
        r = KnowledgeRegistry()
        assert r.register(KnowledgeDescriptor("k1"))
        assert not r.register(KnowledgeDescriptor("k1"))

    def test_exists_missing(self):
        assert KnowledgeRegistry().exists("nope") is False

    def test_capabilities(self):
        r = _ready_registry()
        assert r.get_capabilities("kn1")[0].supports("fact")

    def test_contract(self):
        r = _ready_registry()
        assert "no-inference" in r.get_contract("kn1").guarantees

    def test_metadata(self):
        r = _ready_registry()
        assert r.get_metadata("kn1").author == "SAM"

    def test_summary(self):
        r = _ready_registry()
        s = r.summary()
        assert s.total == 1
        assert s.by_category["domain"] == 1

    def test_count(self):
        assert _ready_registry().count() == 1


class TestKnowledgeRegistrySummary:
    def test_default(self):
        assert KnowledgeRegistrySummary().total == 0


class TestConversationKnowledgeBridge:
    def test_query_1_summary(self):
        b = ConversationKnowledgeBridge(_ready_registry())
        assert b.query_1_summary()["total"] == 1

    def test_query_2_list(self):
        b = ConversationKnowledgeBridge(_ready_registry())
        assert b.query_2_list() == ["kn1"]

    def test_query_3_descriptor(self):
        b = ConversationKnowledgeBridge(_ready_registry())
        assert b.query_3_descriptor("kn1") == "Domain Knowledge"

    def test_query_4_metadata(self):
        b = ConversationKnowledgeBridge(_ready_registry())
        assert b.query_4_metadata("kn1")["author"] == "SAM"

    def test_query_5_capability(self):
        b = ConversationKnowledgeBridge(_ready_registry())
        assert b.query_5_capability("kn1") == ["cap1"]


class TestDashboardKnowledgeBridge:
    def test_five_cards(self):
        b = DashboardKnowledgeBridge(_ready_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardKnowledgeBridge(_ready_registry())
        assert b.overview_card().verdict == "ready"


class TestKnowledgeFoundationImmutability:
    DTO_CLASSES = [
        KnowledgeDescriptor, KnowledgeCapability, KnowledgeContract,
        KnowledgeContractCompliance, KnowledgeMetadata,
        KnowledgeRegistrySummary, ExecutionCard,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
