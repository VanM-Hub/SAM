"""Test traceability chain validation.

Per AUDIT_SPEC §Traceability Rules: every record must reference
Execution, Approval, Contract, Capability, and Citizen.
"""

import pytest
from src.sam.runtime.audit_recorder.models.audit_identity import AuditIdentity
from src.sam.runtime.audit_recorder.validation.traceability_validator import (
    validate_traceability,
    validate_traceability_chain,
    REQUIRED_REFERENCES,
)


def _make_identity(**overrides):
    kwargs = {
        "audit_id": "audit-001",
        "execution_reference": "exec-001",
        "approval_reference": "appr-001",
        "contract_reference": "ctr-001",
        "capability_reference": "cap-001",
        "citizen_reference": "cit-001",
        "timestamp": "2026-08-03T10:00:00",
    }
    kwargs.update(overrides)
    return AuditIdentity(**kwargs)


class FakeRecord:
    def __init__(self, identity):
        self.identity = identity
        self.outcome = "COMPLETED"


class TestTraceabilityValidator:
    """Verify traceability chain validation."""

    def test_all_references_present(self):
        record = FakeRecord(_make_identity())
        errors = validate_traceability(record)
        assert len(errors) == 0

    def test_missing_execution_reference(self):
        record = FakeRecord(_make_identity(execution_reference=""))
        errors = validate_traceability(record)
        assert any("execution_reference" in e for e in errors)

    def test_missing_approval_reference(self):
        record = FakeRecord(_make_identity(approval_reference=""))
        errors = validate_traceability(record)
        assert any("approval_reference" in e for e in errors)

    def test_missing_contract_reference(self):
        record = FakeRecord(_make_identity(contract_reference=""))
        errors = validate_traceability(record)
        assert any("contract_reference" in e for e in errors)

    def test_missing_capability_reference(self):
        record = FakeRecord(_make_identity(capability_reference=""))
        errors = validate_traceability(record)
        assert any("capability_reference" in e for e in errors)

    def test_missing_citizen_reference(self):
        record = FakeRecord(_make_identity(citizen_reference=""))
        errors = validate_traceability(record)
        assert any("citizen_reference" in e for e in errors)

    def test_none_record_fails(self):
        errors = validate_traceability(None)
        assert len(errors) > 0

    def test_no_identity_fails(self):
        record = FakeRecord(None)
        record.identity = None
        errors = validate_traceability(record)
        assert len(errors) > 0

    def test_chain_empty_map_passes(self):
        """Empty reference map always passes chain check."""
        record = FakeRecord(_make_identity())
        errors = validate_traceability_chain(record, {})
        assert len(errors) == 0

    def test_chain_with_valid_refs(self):
        """All references found in map."""
        record = FakeRecord(_make_identity())
        ref_map = {
            "exec-001": True,
            "appr-001": True,
            "ctr-001": True,
            "cap-001": True,
            "cit-001": True,
        }
        errors = validate_traceability_chain(record, ref_map)
        assert len(errors) == 0

    def test_chain_with_broken_refs(self):
        """Missing from reference map reports broken traceability."""
        record = FakeRecord(_make_identity())
        # Map has entries but not the ones we need — refs are broken
        ref_map = {"other-exec": True, "other-appr": True}
        errors = validate_traceability_chain(record, ref_map)
        assert len(errors) > 0
        assert any("Broken traceability" in e for e in errors)

    def test_required_references_constant(self):
        """REQUIRED_REFERENCES has exactly 5 fields."""
        assert len(REQUIRED_REFERENCES) == 5
        assert "execution_reference" in REQUIRED_REFERENCES
        assert "approval_reference" in REQUIRED_REFERENCES
        assert "contract_reference" in REQUIRED_REFERENCES
        assert "capability_reference" in REQUIRED_REFERENCES
        assert "citizen_reference" in REQUIRED_REFERENCES
