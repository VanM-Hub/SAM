"""Sprint 182 — Knowledge Builder Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.knowledge_runtime.builder.knowledge_builder import (
    KnowledgeBuilder, KnowledgeBuildResult,
)
from sam.knowledge_runtime.builder.fact_builder import FactBuilder
from sam.knowledge_runtime.builder.relation_builder import RelationBuilder
from sam.knowledge_runtime.builder.context_builder import ContextBuilder
from sam.knowledge_runtime.builder.preview_builder import (
    PreviewBuilder, KnowledgePreviewDTO,
)
from sam.knowledge_runtime.builder.conversation_builder import ConversationBuilderBridge
from sam.knowledge_runtime.builder.dashboard_builder import DashboardBuilderBridge
from sam.knowledge_runtime.dashboard.knowledge_dashboard import ExecutionCard


class TestKnowledgeBuilder:
    def test_build(self):
        res = KnowledgeBuilder().build("kn1", name="Domain", category="domain")
        assert res.valid is True
        assert res.descriptor.id == "kn1"
        assert res.descriptor.category == "domain"
        assert res.record.knowledge_id == "kn1"

    def test_build_missing(self):
        res = KnowledgeBuilder().build("")
        assert res.valid is False

    def test_default_name(self):
        res = KnowledgeBuilder().build("kn1")
        assert res.descriptor.name == "kn1"

    def test_no_infer_no_store(self):
        res = KnowledgeBuilder().build("kn1")
        assert res.record.facts == []
        assert res.record.relations == []


class TestKnowledgeBuildResult:
    def test_default(self):
        assert KnowledgeBuildResult().valid is False

    def test_immutable(self):
        res = KnowledgeBuildResult()
        with pytest.raises(FrozenInstanceError):
            res.valid = True


class TestFactBuilder:
    def test_build(self):
        f = FactBuilder().build("f1", "Water", "is", "H2O", "chemistry")
        assert f.subject == "Water"
        assert f.predicate == "is"
        assert f.obj == "H2O"
        assert f.source == "chemistry"

    def test_default_predicate(self):
        assert FactBuilder().build("f1", "Water").predicate == "is"

    def test_no_inference(self):
        f = FactBuilder().build("f1", "Water")
        assert f.preview_only is True


class TestRelationBuilder:
    def test_build(self):
        r = RelationBuilder().build("rel1", "a", "b", "depends_on")
        assert r.source_id == "a"
        assert r.target_id == "b"
        assert r.rel_type == "depends_on"

    def test_default_type(self):
        assert RelationBuilder().build("rel1", "a", "b").rel_type == "relates_to"

    def test_invalid_empty(self):
        assert RelationBuilder().build("", "", "").is_valid() is False


class TestContextBuilder:
    def test_build(self):
        c = ContextBuilder().build("ctx1", "kn1", {"a": 1})
        assert c.values == {"a": 1}

    def test_readonly(self):
        assert ContextBuilder().build("ctx1").readonly is True

    def test_empty_values(self):
        assert ContextBuilder().build("ctx1", "kn1").values == {}


class TestPreviewBuilder:
    def test_build(self):
        p = PreviewBuilder().build("pv1", "kn1")
        assert p.preview is True
        assert p.stored is False
        assert p.inferred is False
        assert p.external_calls == 0

    def test_no_infer_no_store(self):
        p = PreviewBuilder().build("pv1", "kn1")
        assert p.inferred is False
        assert p.stored is False

    def test_external_zero(self):
        assert PreviewBuilder().build("pv1", "kn1").external_calls == 0

    def test_immutable(self):
        p = KnowledgePreviewDTO("pv1")
        with pytest.raises(FrozenInstanceError):
            p.inferred = True


class TestConversationBuilderBridge:
    def test_summary_valid(self):
        b = ConversationBuilderBridge()
        assert b.summary("kn1")["valid"] is True

    def test_summary_invalid(self):
        b = ConversationBuilderBridge()
        assert b.summary("")["valid"] is False

    def test_describe(self):
        b = ConversationBuilderBridge()
        assert "no inference" in b.describe_builder()


class TestDashboardBuilderBridge:
    def test_five_cards(self):
        b = DashboardBuilderBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardBuilderBridge()
        assert b.overview_card().verdict == "ready"


class TestBuilderImmutability:
    DTO_CLASSES = [
        KnowledgeBuildResult, KnowledgePreviewDTO,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
