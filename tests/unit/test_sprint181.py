"""Sprint 181 — Knowledge Model Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.knowledge_runtime.model.knowledge_record import KnowledgeRecord
from sam.knowledge_runtime.model.knowledge_fact import KnowledgeFact
from sam.knowledge_runtime.model.knowledge_relation import KnowledgeRelation
from sam.knowledge_runtime.model.knowledge_context import KnowledgeContext
from sam.knowledge_runtime.model.knowledge_tag import KnowledgeTag
from sam.knowledge_runtime.model.knowledge_validator import (
    KnowledgeValidator, KnowledgeValidation,
)
from sam.knowledge_runtime.model.conversation_model import ConversationModelBridge
from sam.knowledge_runtime.model.dashboard_model import DashboardModelBridge
from sam.knowledge_runtime.dashboard.knowledge_dashboard import ExecutionCard


class TestKnowledgeRecord:
    def test_default(self):
        r = KnowledgeRecord("r1", "kn1")
        assert r.scope == "general"
        assert r.preview_only is True
        assert r.facts == []
        assert r.relations == []

    def test_is_valid(self):
        assert KnowledgeRecord("r1", "kn1").is_valid() is True
        assert KnowledgeRecord("", "kn1").is_valid() is False

    def test_immutable(self):
        r = KnowledgeRecord("r1", "kn1")
        with pytest.raises(FrozenInstanceError):
            r.scope = "x"


class TestKnowledgeFact:
    def test_default(self):
        f = KnowledgeFact("f1", "Water", "is", "H2O")
        assert f.predicate == "is"
        assert f.preview_only is True

    def test_is_valid(self):
        assert KnowledgeFact("f1", "Water").is_valid() is True
        assert KnowledgeFact("", "").is_valid() is False

    def test_immutable(self):
        f = KnowledgeFact("f1", "Water")
        with pytest.raises(FrozenInstanceError):
            f.obj = "x"


class TestKnowledgeRelation:
    def test_default(self):
        r = KnowledgeRelation("rel1", "a", "b")
        assert r.rel_type == "relates_to"
        assert r.is_valid() is True
        assert KnowledgeRelation("", "", "").is_valid() is False

    def test_immutable(self):
        r = KnowledgeRelation("rel1", "a", "b")
        with pytest.raises(FrozenInstanceError):
            r.rel_type = "x"


class TestKnowledgeContext:
    def test_default(self):
        c = KnowledgeContext("ctx1", "kn1", {"a": 1})
        assert c.readonly is True
        assert c.values == {"a": 1}

    def test_immutable(self):
        c = KnowledgeContext("ctx1")
        with pytest.raises(FrozenInstanceError):
            c.knowledge_id = "x"


class TestKnowledgeTag:
    def test_default(self):
        assert KnowledgeTag("t1").category == "general"

    def test_immutable(self):
        t = KnowledgeTag("t1")
        with pytest.raises(FrozenInstanceError):
            t.name = "x"


class TestKnowledgeValidator:
    def test_valid_record(self):
        v = KnowledgeValidator().validate(KnowledgeRecord("r1", "kn1"))
        assert v.valid is True

    def test_missing_record(self):
        v = KnowledgeValidator().validate(KnowledgeRecord("", ""))
        assert v.valid is False

    def test_validate_fact(self):
        v = KnowledgeValidator().validate_fact(KnowledgeFact("f1", "Water"))
        assert v.valid is True
        v2 = KnowledgeValidator().validate_fact(KnowledgeFact("", ""))
        assert v2.valid is False

    def test_validate_relation(self):
        v = KnowledgeValidator().validate_relation(
            KnowledgeRelation("r1", "a", "b"))
        assert v.valid is True
        v2 = KnowledgeValidator().validate_relation(KnowledgeRelation("", "", ""))
        assert v2.valid is False

    def test_validate_context(self):
        v = KnowledgeValidator().validate_context(KnowledgeContext("ctx1"))
        assert v.valid is True
        v2 = KnowledgeValidator().validate_context(KnowledgeContext(""))
        assert v2.valid is False


class TestKnowledgeValidation:
    def test_default(self):
        assert KnowledgeValidation().valid is True


class TestConversationModelBridge:
    def test_summary(self):
        b = ConversationModelBridge(KnowledgeRecord(
            "r1", "kn1", facts=["f1"], relations=["rel1"]))
        s = b.summary()
        assert s["has_record"] is True
        assert s["facts"] == 1
        assert s["relations"] == 1

    def test_validity(self):
        b = ConversationModelBridge(KnowledgeRecord("r1", "kn1"))
        assert b.validity()["valid"] is True

    def test_no_record(self):
        b = ConversationModelBridge()
        assert b.summary()["has_record"] is False


class TestDashboardModelBridge:
    def test_five_cards(self):
        b = DashboardModelBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        assert DashboardModelBridge().overview_card().verdict == "ready"


class TestModelImmutability:
    DTO_CLASSES = [
        KnowledgeRecord, KnowledgeFact, KnowledgeRelation,
        KnowledgeContext, KnowledgeTag, KnowledgeValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
