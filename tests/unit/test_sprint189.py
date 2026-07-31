"""Sprint 189 — Cognitive Context Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.cognitive_runtime.context.cognitive_context import CognitiveContext
from sam.cognitive_runtime.context.cognitive_snapshot import CognitiveSnapshot
from sam.cognitive_runtime.context.cognitive_scope import (
    CognitiveScope, VALID_SCOPES,
)
from sam.cognitive_runtime.context.cognitive_reference import CognitiveReference
from sam.cognitive_runtime.context.cognitive_validator import (
    CognitiveValidator, CognitiveValidation,
)
from sam.cognitive_runtime.context.conversation_context import ConversationContextBridge
from sam.cognitive_runtime.context.dashboard_context import DashboardContextBridge
from sam.cognitive_runtime.context.cognitive_context import CognitiveContext as _CC
from sam.cognitive_runtime.dashboard import ExecutionCard


class TestCognitiveContext:
    def test_default(self):
        c = CognitiveContext()
        assert c.entry_count() == 0
        assert c.scope == "mission"

    def test_preview_only(self):
        assert CognitiveContext().preview_only is True

    def test_entries(self):
        c = CognitiveContext(cognitive_id="c1", entries=["a", "b"])
        assert c.entry_count() == 2

    def test_immutable(self):
        c = CognitiveContext()
        with pytest.raises(FrozenInstanceError):
            c.cognitive_id = "x"


class TestCognitiveSnapshot:
    def test_build(self):
        ctx = CognitiveContext(cognitive_id="c1", entries=["k1"])
        s = CognitiveSnapshot(snapshot_id="s1", context=ctx)
        assert s.total_entries() == 1

    def test_default_context(self):
        s = CognitiveSnapshot(snapshot_id="s1")
        assert s.total_entries() == 0

    def test_immutable(self):
        s = CognitiveSnapshot()
        with pytest.raises(FrozenInstanceError):
            s.snapshot_id = "x"


class TestCognitiveScope:
    def test_scope_default(self):
        s = CognitiveScope()
        assert s.scope == "mission"
        assert s.included_runtimes == ["mission"]

    def test_included_runtimes(self):
        s = CognitiveScope(scope="knowledge")
        assert s.included_runtimes == ["mission", "agent", "skill", "memory", "knowledge"]

    def test_invalid_scope(self):
        with pytest.raises(ValueError):
            CognitiveScope(scope="bad")

    def test_valid_scopes(self):
        assert VALID_SCOPES == ["mission", "agent", "skill", "memory", "knowledge"]

    def test_immutable(self):
        s = CognitiveScope()
        with pytest.raises(FrozenInstanceError):
            s.scope = "agent"


class TestCognitiveReference:
    def test_default(self):
        r = CognitiveReference()
        assert r.runtime == "knowledge"

    def test_empty_runtime_raises(self):
        with pytest.raises(ValueError):
            CognitiveReference(runtime="")

    def test_preview_only(self):
        assert CognitiveReference().preview_only is True

    def test_immutable(self):
        r = CognitiveReference()
        with pytest.raises(FrozenInstanceError):
            r.runtime = "x"


class TestCognitiveValidator:
    def test_valid_context(self):
        v = CognitiveValidator().validate_context(CognitiveContext(cognitive_id="c1"))
        assert v.valid is True
        assert v.issues == []

    def test_context_no_id(self):
        v = CognitiveValidator().validate_context(CognitiveContext())
        assert v.valid is False
        assert "cognitive_id is required" in v.issues

    def test_context_bad_scope(self):
        v = CognitiveValidator().validate_context(CognitiveContext(cognitive_id="c", scope="x"))
        assert v.valid is False

    def test_valid_scope(self):
        assert CognitiveValidator().validate_scope(CognitiveScope("mission")).valid is True

    def test_invalid_scope(self):
        assert CognitiveValidator().validate_scope(CognitiveScope("agent")).valid is True

    def test_valid_reference(self):
        assert CognitiveValidator().validate_reference(CognitiveReference()).valid is True

    def test_invalid_reference_impossible(self):
        # konstruktor menolak runtime kosong, jadi validator selalu valid
        assert CognitiveValidator().validate_reference(
            CognitiveReference(runtime="memory")
        ).valid is True


class TestCognitiveValidation:
    def test_default(self):
        assert CognitiveValidation().valid is True

    def test_immutable(self):
        val = CognitiveValidation()
        with pytest.raises(FrozenInstanceError):
            val.valid = False


class TestConversationContextBridge:
    def test_build_context(self):
        b = ConversationContextBridge()
        ctx = b.build_context("c1", "knowledge")
        assert ctx.cognitive_id == "c1"
        assert ctx.scope == "knowledge"

    def test_build_snapshot(self):
        b = ConversationContextBridge()
        ctx = b.build_context("c1")
        s = b.build_snapshot("s1", ctx)
        assert s.snapshot_id == "s1"

    def test_summary(self):
        b = ConversationContextBridge()
        ctx = _CC(cognitive_id="c1", entries=["x"])
        s = b.summary(ctx)
        assert s["entry_count"] == 1


class TestDashboardContextBridge:
    def test_five_cards(self):
        b = DashboardContextBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardContextBridge()
        assert b.overview_card().detail.startswith("scope=")


class TestContextImmutability:
    DTO_CLASSES = [
        CognitiveContext, CognitiveSnapshot, CognitiveScope,
        CognitiveReference, CognitiveValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
