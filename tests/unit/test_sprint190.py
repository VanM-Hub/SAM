"""Sprint 190 — Cognitive Builder Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.cognitive_runtime.builder.cognitive_builder import (
    CognitiveBuilder, CognitiveBuildResult,
)
from sam.cognitive_runtime.builder.context_builder import ContextBuilder
from sam.cognitive_runtime.builder.snapshot_builder import SnapshotBuilder
from sam.cognitive_runtime.builder.workspace_builder import (
    WorkspaceBuilder, CognitiveWorkspaceDTO,
)
from sam.cognitive_runtime.builder.preview_builder import (
    PreviewBuilder, CognitivePreviewDTO,
)
from sam.cognitive_runtime.builder.conversation_builder import ConversationBuilderBridge
from sam.cognitive_runtime.builder.dashboard_builder import DashboardBuilderBridge
from sam.cognitive_runtime.context.cognitive_context import CognitiveContext
from sam.cognitive_runtime.context.cognitive_snapshot import CognitiveSnapshot
from sam.cognitive_runtime.dashboard import ExecutionCard


class TestCognitiveBuilder:
    def test_build_context(self):
        r = CognitiveBuilder().build_context("c1")
        assert r.ok is True
        assert r.context.cognitive_id == "c1"

    def test_build_scope(self):
        r = CognitiveBuilder().build_context("c1", "knowledge")
        assert r.context.scope == "knowledge"

    def test_result_default(self):
        assert CognitiveBuildResult().ok is True

    def test_result_immutable(self):
        r = CognitiveBuildResult()
        with pytest.raises(FrozenInstanceError):
            r.ok = False


class TestContextBuilder:
    def test_build(self):
        ctx = ContextBuilder().build("c1")
        assert ctx.cognitive_id == "c1"

    def test_build_entries(self):
        ctx = ContextBuilder().build("c1", entries=["a", "b"])
        assert ctx.entry_count() == 2

    def test_add_entry_immutable(self):
        cb = ContextBuilder()
        ctx = cb.build("c1")
        new = cb.add_entry(ctx, "x")
        assert new.entry_count() == 1
        assert ctx.entry_count() == 0  # original unchanged (immutable)
        assert new.cognitive_id == "c1"


class TestSnapshotBuilder:
    def test_build(self):
        ctx = ContextBuilder().build("c1")
        s = SnapshotBuilder().build("s1", ctx, sources=["k"])
        assert s.snapshot_id == "s1"
        assert s.sources == ["k"]
        assert s.created_at != ""

    def test_default_sources(self):
        s = SnapshotBuilder().build("s1", CognitiveContext())
        assert s.sources == []


class TestWorkspaceBuilder:
    def test_build(self):
        ws = WorkspaceBuilder().build("w1", items=["a"])
        assert ws.workspace_id == "w1"
        assert ws.item_count() == 1

    def test_preview_only(self):
        assert WorkspaceBuilder().build("w1").preview_only is True

    def test_add_item_immutable(self):
        wb = WorkspaceBuilder()
        ws = wb.build("w1")
        new = wb.add_item(ws, "x")
        assert new.item_count() == 1
        assert ws.item_count() == 0

    def test_workspace_dto_immutable(self):
        ws = CognitiveWorkspaceDTO("w1")
        with pytest.raises(FrozenInstanceError):
            ws.workspace_id = "x"


class TestPreviewBuilder:
    def test_build(self):
        p = PreviewBuilder().build("label", CognitiveContext(cognitive_id="c1"))
        assert p.label == "label"
        assert p.composed is True

    def test_no_inference_default(self):
        p = PreviewBuilder().build("l", CognitiveContext())
        assert p.inferred is False
        assert p.external_calls == 0

    def test_forbid_inference(self):
        with pytest.raises(ValueError):
            CognitivePreviewDTO(label="l", inferred=True)

    def test_forbid_external(self):
        with pytest.raises(ValueError):
            CognitivePreviewDTO(label="l", external_calls=1)

    def test_preview_dto_immutable(self):
        p = CognitivePreviewDTO()
        with pytest.raises(FrozenInstanceError):
            p.label = "x"


class TestConversationBuilderBridge:
    def test_5_queries(self):
        b = ConversationBuilderBridge()
        ctx = b.query_1_context("c1")
        assert ctx.cognitive_id == "c1"
        snap = b.query_2_snapshot("s1", ctx)
        assert isinstance(snap, CognitiveSnapshot)
        ws = b.query_3_workspace("w1")
        assert ws.workspace_id == "w1"
        prev = b.query_4_preview("l", ctx)
        assert prev.inferred is False
        comp = b.query_5_compose("c2")
        assert comp["cognitive_id"] == "c2"


class TestDashboardBuilderBridge:
    def test_five_cards(self):
        b = DashboardBuilderBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardBuilderBridge()
        assert b.overview_card().group == "builder"


class TestBuilderImmutability:
    DTO_CLASSES = [
        CognitiveBuildResult, CognitiveWorkspaceDTO, CognitivePreviewDTO,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
