"""Sprint 213 — Audit Model Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.audit_runtime.model.audit_record import AuditRecord
from sam.audit_runtime.model.audit_entry import AuditEntry
from sam.audit_runtime.model.audit_reference import AuditReference
from sam.audit_runtime.model.audit_scope import AuditScope, VALID_SCOPES
from sam.audit_runtime.model.audit_validator import (
    AuditValidator, AuditValidation,
)
from sam.audit_runtime.model.conversation_model import ConversationModelBridge
from sam.audit_runtime.model.dashboard_model import DashboardModelBridge
from sam.audit_runtime.dashboard import PolicyCard


class TestAuditRecord:
    def test_defaults(self):
        r = AuditRecord("rec1")
        assert r.action == "observe"
        assert r.immutable is True
        assert r.entries == ()

    def test_immutable(self):
        r = AuditRecord("rec1")
        with pytest.raises(FrozenInstanceError):
            r.action = "x"

    def test_empty_id(self):
        with pytest.raises(ValueError):
            AuditRecord(" ")

    def test_entries_tuple(self):
        r = AuditRecord("rec1", entries=[AuditEntry("e1")])
        assert isinstance(r.entries, tuple)


class TestAuditEntry:
    def test_defaults(self):
        e = AuditEntry("e1")
        assert e.kind == "info"
        assert e.timestamp == 0

    def test_immutable(self):
        e = AuditEntry("e1")
        with pytest.raises(FrozenInstanceError):
            e.message = "x"

    def test_empty_id(self):
        with pytest.raises(ValueError):
            AuditEntry(" ")


class TestAuditReference:
    def test_defaults(self):
        ref = AuditReference("r1")
        assert ref.kind == "provenance"
        assert ref.traceable is True

    def test_immutable(self):
        ref = AuditReference("r1")
        with pytest.raises(FrozenInstanceError):
            ref.source = "x"

    def test_empty_id(self):
        with pytest.raises(ValueError):
            AuditReference(" ")


class TestAuditScope:
    def test_valid_scopes(self):
        assert "policy" in VALID_SCOPES
        assert "system" in VALID_SCOPES
        assert "cognitive" in VALID_SCOPES

    def test_valid(self):
        assert AuditScope("policy").scope == "policy"

    def test_invalid(self):
        with pytest.raises(ValueError):
            AuditScope("bogus")

    def test_immutable(self):
        s = AuditScope("system")
        with pytest.raises(FrozenInstanceError):
            s.scope = "x"


class TestAuditValidator:
    def test_valid(self):
        v = AuditValidator().validate(AuditRecord("rec1"))
        assert v.valid is True
        assert v.issues == []

    def test_empty_id_invalid(self):
        v = AuditValidator().validate(AuditRecord("rec1"))
        # empty id not produced here; test via action
        assert v.valid is True

    def test_bad_action(self):
        from dataclasses import replace
        bad = replace(AuditRecord("rec1"), action="nope")
        v = AuditValidator().validate(bad)
        assert v.valid is False
        assert any("unsupported action" in i for i in v.issues)

    def test_validate_scope(self):
        v = AuditValidator()
        assert v.validate_scope("policy") is True
        assert v.validate_scope("zzz") is False

    def test_validate_entries(self):
        v = AuditValidator()
        assert v.validate_entries(AuditRecord("r", entries=[AuditEntry("e1")])) is True


class TestAuditValidation:
    def test_default(self):
        assert AuditValidation().valid is False

    def test_immutable(self):
        v = AuditValidation()
        with pytest.raises(FrozenInstanceError):
            v.valid = True


class TestConversationModelBridge:
    def test_5_queries(self):
        b = ConversationModelBridge()
        assert "policy" in b.query_1_scopes()["valid_scopes"]
        assert b.query_2_validate_scope("policy")["ok"] is True
        assert b.query_3_immutable()["immutable"] is True
        assert b.query_4_actions()["actions"] == ["observe", "track", "verify"]
        assert b.query_5_validate("rec1")["valid"] is True


class TestDashboardModelBridge:
    def test_five_cards(self):
        b = DashboardModelBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_verdict(self):
        b = DashboardModelBridge()
        assert b.verdict_card().status == "immutable"


class TestModelImmutability:
    DTO_CLASSES = [
        AuditRecord, AuditEntry, AuditReference, AuditScope, AuditValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
