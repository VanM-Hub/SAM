"""Sprint 173 — Memory Model Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.memory.model.memory_record import MemoryRecord
from sam.memory.model.memory_entry import MemoryEntry
from sam.memory.model.memory_reference import MemoryReference
from sam.memory.model.memory_scope import MemoryScope
from sam.memory.model.memory_tag import MemoryTag
from sam.memory.model.memory_validator import MemoryValidator, MemoryValidation
from sam.memory.model.conversation_model import ConversationModelBridge
from sam.memory.model.dashboard_model import DashboardModelBridge
from sam.memory.dashboard.memory_dashboard import ExecutionCard


class TestMemoryRecord:
    def test_default(self):
        r = MemoryRecord("r1", "mem1")
        assert r.scope == "general"
        assert r.preview_only is True

    def test_is_valid(self):
        assert MemoryRecord("r1", "mem1").is_valid() is True
        assert MemoryRecord("", "mem1").is_valid() is False

    def test_immutable(self):
        r = MemoryRecord("r1", "mem1")
        with pytest.raises(FrozenInstanceError):
            r.scope = "x"


class TestMemoryEntry:
    def test_default(self):
        e = MemoryEntry("e1", "r1")
        assert e.readonly is True

    def test_immutable(self):
        e = MemoryEntry("e1")
        with pytest.raises(FrozenInstanceError):
            e.key = "x"


class TestMemoryReference:
    def test_default(self):
        r = MemoryReference("ref1", "a", "b")
        assert r.ref_type == "points_to"
        assert r.is_valid() is True
        assert MemoryReference("", "", "").is_valid() is False

    def test_immutable(self):
        r = MemoryReference("ref1", "a", "b")
        with pytest.raises(FrozenInstanceError):
            r.ref_type = "x"


class TestMemoryScope:
    def test_allows(self):
        s = MemoryScope("sc1", allowed_tags=["a", "b"])
        assert s.allows("a") is True
        assert s.allows("c") is False

    def test_allows_all_when_empty(self):
        assert MemoryScope("sc1").allows("zzz") is True

    def test_immutable(self):
        s = MemoryScope("sc1")
        with pytest.raises(FrozenInstanceError):
            s.name = "x"


class TestMemoryTag:
    def test_default(self):
        assert MemoryTag("t1").category == "general"

    def test_immutable(self):
        t = MemoryTag("t1")
        with pytest.raises(FrozenInstanceError):
            t.name = "x"


class TestMemoryValidator:
    def test_valid(self):
        v = MemoryValidator().validate(MemoryRecord("r1", "mem1"))
        assert v.valid is True

    def test_missing(self):
        v = MemoryValidator().validate(MemoryRecord("", ""))
        assert v.valid is False

    def test_validate_scope(self):
        v = MemoryValidator().validate_scope(MemoryScope("sc1"))
        assert v.valid is True

    def test_validate_reference(self):
        v = MemoryValidator().validate_reference(
            MemoryReference("r1", "a", "b"))
        assert v.valid is True
        v2 = MemoryValidator().validate_reference(MemoryReference("", "", ""))
        assert v2.valid is False

    def test_validate_tags(self):
        v = MemoryValidator().validate_tags([MemoryTag("t1"), MemoryTag("t2")])
        assert v.valid is True
        v2 = MemoryValidator().validate_tags([MemoryTag("")])
        assert v2.valid is False


class TestMemoryValidation:
    def test_default(self):
        assert MemoryValidation().valid is True


class TestConversationModelBridge:
    def test_summary(self):
        b = ConversationModelBridge(MemoryRecord("r1", "mem1"))
        assert b.summary()["has_record"] is True

    def test_validity(self):
        b = ConversationModelBridge(MemoryRecord("r1", "mem1"))
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
        MemoryRecord, MemoryEntry, MemoryReference,
        MemoryScope, MemoryTag, MemoryValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
