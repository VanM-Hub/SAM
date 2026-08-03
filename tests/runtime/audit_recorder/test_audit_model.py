"""Test audit models: identity, record, verification result.

Covers AUdit_SPEC §Audit Identity, §Audit Record.
"""

import pytest
from src.sam.runtime.audit_recorder.models.audit_identity import AuditIdentity
from src.sam.runtime.audit_recorder.models.audit_record import AuditRecord
from src.sam.runtime.audit_recorder.models.verification_result import (
    VerificationResult,
    VerificationStatus,
)


class TestAuditIdentity:
    """Test AuditIdentity model per AUDIT_SPEC L57-L69."""

    def test_valid_identity(self):
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        assert identity.audit_id == "audit-001"
        assert identity.validate() is True

    def test_identity_is_frozen(self):
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        with pytest.raises(Exception):
            identity.audit_id = "changed"

    def test_empty_audit_id_raises(self):
        identity = AuditIdentity(
            audit_id="",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        with pytest.raises(ValueError, match="audit_id"):
            identity.validate()

    def test_empty_execution_reference_raises(self):
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        with pytest.raises(ValueError, match="execution_reference"):
            identity.validate()

    def test_empty_approval_reference_raises(self):
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        with pytest.raises(ValueError, match="approval_reference"):
            identity.validate()

    def test_empty_contract_reference_raises(self):
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        with pytest.raises(ValueError, match="contract_reference"):
            identity.validate()

    def test_empty_capability_reference_raises(self):
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        with pytest.raises(ValueError, match="capability_reference"):
            identity.validate()

    def test_empty_citizen_reference_raises(self):
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="",
            timestamp="2026-08-03T10:00:00",
        )
        with pytest.raises(ValueError, match="citizen_reference"):
            identity.validate()

    def test_empty_timestamp_raises(self):
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="",
        )
        with pytest.raises(ValueError, match="timestamp"):
            identity.validate()

    def test_to_dict(self):
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        d = identity.to_dict()
        assert d["audit_id"] == "audit-001"
        assert "execution_reference" in d

    def test_multiple_errors_accumulate(self):
        identity = AuditIdentity(
            audit_id="",
            execution_reference="",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        with pytest.raises(ValueError) as exc:
            identity.validate()
        msg = str(exc.value)
        assert "audit_id" in msg
        assert "execution_reference" in msg

    def test_repr(self):
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        r = repr(identity)
        assert "audit-001" in r
        assert "exec-001" in r


class TestAuditRecord:
    """Test AuditRecord model per AUDIT_SPEC L72-L84."""

    def _make_identity(self, aid="audit-001"):
        return AuditIdentity(
            audit_id=aid,
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )

    def test_create_record(self):
        record = AuditRecord(
            identity=self._make_identity(),
            outcome="COMPLETED",
            outcome_message="ok",
        )
        assert record.audit_id == "audit-001"
        assert record.outcome == "COMPLETED"
        assert record.is_verified() is False

    def test_record_is_immutable(self):
        record = AuditRecord(
            identity=self._make_identity(),
            outcome="COMPLETED",
        )
        with pytest.raises(Exception):
            record.outcome = "FAILED"

    def test_shortcut_properties(self):
        record = AuditRecord(
            identity=self._make_identity(),
            outcome="COMPLETED",
        )
        assert record.execution_reference == "exec-001"
        assert record.approval_reference == "appr-001"
        assert record.contract_reference == "ctr-001"
        assert record.capability_reference == "cap-001"
        assert record.citizen_reference == "cit-001"

    def test_is_missing_reference_true(self):
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="",  # missing
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        # Create record bypassing validate (identity is frozen dataclass)
        record = AuditRecord(identity=identity, outcome="COMPLETED")
        assert record.is_missing_reference() is True

    def test_is_missing_reference_false(self):
        record = AuditRecord(
            identity=self._make_identity(),
            outcome="COMPLETED",
        )
        assert record.is_missing_reference() is False

    def test_to_dict(self):
        record = AuditRecord(
            identity=self._make_identity(),
            outcome="COMPLETED",
            outcome_message="ok",
        )
        d = record.to_dict()
        assert d["audit_id"] == "audit-001"
        assert d["outcome"] == "COMPLETED"
        assert "identity" in d

    def test_repr(self):
        record = AuditRecord(
            identity=self._make_identity(),
            outcome="COMPLETED",
        )
        r = repr(record)
        assert "audit-001" in r
        assert "not_verified" in r


class TestVerificationResult:
    """Test VerificationResult model per ADR-007."""

    def test_verified_factory(self):
        v = VerificationResult.verified("all intact")
        assert v.status == VerificationStatus.VERIFIED
        assert v.is_verified() is True
        assert v.evidence == "all intact"

    def test_not_verified_factory(self):
        v = VerificationResult.not_verified(
            "missing refs",
            {"execution": "not found"},
        )
        assert v.status == VerificationStatus.NOT_VERIFIED
        assert v.is_verified() is False
        assert v.has_broken_references() is True
        assert "execution" in v.broken_references

    def test_not_verified_no_broken_refs(self):
        v = VerificationResult.not_verified("generic fail")
        assert v.has_broken_references() is False

    def test_verification_result_is_frozen(self):
        v = VerificationResult.verified("ok")
        with pytest.raises(Exception):
            v.evidence = "changed"

    def test_to_dict(self):
        v = VerificationResult.verified("ok")
        d = v.to_dict()
        assert d["status"] == "VERIFIED"
        assert d["evidence"] == "ok"

    def test_to_dict_with_broken(self):
        v = VerificationResult.not_verified(
            "fail", {"ex": "gone"}
        )
        d = v.to_dict()
        assert d["status"] == "NOT_VERIFIED"
        assert "ex" in d["broken_references"]

    def test_repr(self):
        v = VerificationResult.verified("ok")
        r = repr(v)
        assert "VERIFIED" in r

    def test_repr_not_verified(self):
        v = VerificationResult.not_verified(
            "fail", {"a": "b"}
        )
        r = repr(v)
        assert "NOT_VERIFIED" in r
        assert "broken" in r
