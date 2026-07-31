"""Sprint 174 — Memory Builder Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.memory.builder.memory_builder import MemoryBuilder, MemoryBuildResult
from sam.memory.builder.context_builder import ContextBuilder, MemoryContext
from sam.memory.builder.reference_builder import ReferenceBuilder
from sam.memory.builder.snapshot_builder import SnapshotBuilder, MemorySnapshotDTO
from sam.memory.builder.preview_builder import PreviewBuilder, MemoryPreviewDTO
from sam.memory.builder.conversation_builder import ConversationBuilderBridge
from sam.memory.builder.dashboard_builder import DashboardBuilderBridge
from sam.memory.dashboard.memory_dashboard import ExecutionCard


class TestMemoryBuilder:
    def test_build(self):
        res = MemoryBuilder().build("mem1", name="Short", category="short_term")
        assert res.valid is True
        assert res.descriptor.id == "mem1"
        assert res.descriptor.category == "short_term"
        assert res.record.memory_id == "mem1"

    def test_build_missing(self):
        res = MemoryBuilder().build("")
        assert res.valid is False

    def test_default_name(self):
        res = MemoryBuilder().build("m1")
        assert res.descriptor.name == "m1"

    def test_no_store(self):
        res = MemoryBuilder().build("mem1")
        # build tidak menyimpan apa pun ke registry/database
        assert res.record.data == {}


class TestMemoryBuildResult:
    def test_default(self):
        assert MemoryBuildResult().valid is False

    def test_immutable(self):
        res = MemoryBuildResult()
        with pytest.raises(FrozenInstanceError):
            res.valid = True


class TestContextBuilder:
    def test_build(self):
        c = ContextBuilder().build("ctx1", "mem1", {"a": 1})
        assert c.values == {"a": 1}

    def test_build_no_values(self):
        assert ContextBuilder().build("ctx1", "mem1").values == {}

    def test_readonly(self):
        assert ContextBuilder().build("ctx1").readonly is True

    def test_immutable(self):
        c = MemoryContext("ctx1")
        with pytest.raises(FrozenInstanceError):
            c.memory_id = "x"


class TestReferenceBuilder:
    def test_build(self):
        r = ReferenceBuilder().build("ref1", "a", "b", "links_to")
        assert r.source_id == "a"
        assert r.target_id == "b"
        assert r.ref_type == "links_to"

    def test_default_type(self):
        r = ReferenceBuilder().build("ref1", "a", "b")
        assert r.ref_type == "points_to"

    def test_empty_ref_invalid(self):
        assert ReferenceBuilder().build("", "", "").is_valid() is False


class TestSnapshotBuilder:
    def test_build(self):
        s = SnapshotBuilder().build("snap1", "mem1", {"k": "v"})
        assert s.state == {"k": "v"}
        assert s.external_calls == 0

    def test_build_no_state(self):
        assert SnapshotBuilder().build("snap1", "mem1").state == {}

    def test_immutable(self):
        s = MemorySnapshotDTO("snap1")
        with pytest.raises(FrozenInstanceError):
            s.external_calls = 1


class TestPreviewBuilder:
    def test_build(self):
        p = PreviewBuilder().build("pv1", "mem1")
        assert p.preview is True
        assert p.stored is False
        assert p.external_calls == 0

    def test_no_store(self):
        p = PreviewBuilder().build("pv1", "mem1")
        assert p.stored is False

    def test_build_default_memory(self):
        assert PreviewBuilder().build("pv1").memory_id == ""

    def test_build_external_zero(self):
        assert PreviewBuilder().build("pv1", "mem1").external_calls == 0

    def test_immutable(self):
        p = MemoryPreviewDTO("pv1")
        with pytest.raises(FrozenInstanceError):
            p.stored = True


class TestConversationBuilderBridge:
    def test_summary_valid(self):
        b = ConversationBuilderBridge()
        assert b.summary("mem1")["valid"] is True

    def test_summary_invalid(self):
        b = ConversationBuilderBridge()
        assert b.summary("")["valid"] is False

    def test_describe(self):
        b = ConversationBuilderBridge()
        assert "no store" in b.describe_builder()


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
        MemoryBuildResult, MemoryContext, MemorySnapshotDTO, MemoryPreviewDTO,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
