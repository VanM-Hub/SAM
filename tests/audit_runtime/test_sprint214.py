"""Sprint 214 — Audit Builder Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.audit_runtime.builder.audit_builder import (
    AuditBuilder, AuditBuildResult,
)
from sam.audit_runtime.builder.entry_builder import EntryBuilder
from sam.audit_runtime.builder.reference_builder import ReferenceBuilder
from sam.audit_runtime.builder.scope_builder import ScopeBuilder
from sam.audit_runtime.builder.preview_builder import (
    PreviewBuilder, AuditPreviewDTO,
)
from sam.audit_runtime.builder.conversation_builder import (
    ConversationBuilderBridge,
)
from sam.audit_runtime.builder.dashboard_builder import DashboardBuilderBridge
from sam.audit_runtime.model.audit_record import AuditRecord
from sam.audit_runtime.model.audit_entry import AuditEntry
from sam.audit_runtime.dashboard import PolicyCard


class TestAuditBuilder:
    def test_build(self):
        res = AuditBuilder().build("rec1")
        assert res.ok is True
        assert res.record.record_id == "rec1"

    def test_add_entry(self):
        b = AuditBuilder().add_entry(AuditEntry("e1"))
        res = b.build("rec1")
        assert len(res.record.entries) == 1

    def test_no_storage(self):
        # builder tidak menyimpan ke registry — hanya membentuk DTO
        res = AuditBuilder().build("rec1")
        assert res.record is not None
        assert res.ok is True


class TestAuditBuildResult:
    def test_default(self):
        assert AuditBuildResult().ok is False

    def test_immutable(self):
        res = AuditBuildResult()
        with pytest.raises(FrozenInstanceError):
            res.ok = True


class TestEntryBuilder:
    def test_build(self):
        e = EntryBuilder().build("e1", kind="track")
        assert e.kind == "track"
        assert e.entry_id == "e1"


class TestReferenceBuilder:
    def test_build(self):
        ref = ReferenceBuilder().build("r1", source="mission")
        assert ref.source == "mission"
        assert ref.traceable is True


class TestScopeBuilder:
    def test_build(self):
        s = ScopeBuilder().build("policy")
        assert s.scope == "policy"


class TestPreviewBuilder:
    def test_build_preview(self):
        res = AuditBuilder().build("rec1")
        p = PreviewBuilder().build(res.record)
        assert p.decided is False
        assert p.external_calls == 0
        assert p.stored is False


class TestAuditPreviewDTO:
    def test_forbidden_decided(self):
        res = AuditBuilder().build("rec1")
        with pytest.raises(ValueError):
            AuditPreviewDTO(record=res.record, decided=True)

    def test_forbidden_external_calls(self):
        res = AuditBuilder().build("rec1")
        with pytest.raises(ValueError):
            AuditPreviewDTO(record=res.record, external_calls=1)

    def test_forbidden_stored(self):
        res = AuditBuilder().build("rec1")
        with pytest.raises(ValueError):
            AuditPreviewDTO(record=res.record, stored=True)

    def test_immutable(self):
        res = AuditBuilder().build("rec1")
        p = PreviewBuilder().build(res.record)
        with pytest.raises(FrozenInstanceError):
            p.decided = True


class TestConversationBuilderBridge:
    def test_5_queries(self):
        b = ConversationBuilderBridge()
        assert b.query_1_build("rec1")["ok"] is True
        assert b.query_2_build_entry("e1")["kind"] == "info"
        assert b.query_3_preview("rec1")["external_calls"] == 0
        assert b.query_4_no_storage()["stored"] is False
        assert b.query_5_decided()["decided"] is False


class TestDashboardBuilderBridge:
    def test_five_cards(self):
        b = DashboardBuilderBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_verdict(self):
        b = DashboardBuilderBridge()
        assert b.verdict_card().status == "preview_only"


class TestBuilderImmutability:
    DTO_CLASSES = [AuditBuildResult, AuditPreviewDTO]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
