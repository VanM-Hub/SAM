"""Tests for Execution Models: Identity, Request, Result.

Covers: EXECUTION_SPEC §Execution Identity, §Execution Request, §Execution Result.
"""

import pytest
from src.sam.runtime.execution_scheduler.models.execution_identity import (
    ExecutionIdentity,
)
from src.sam.runtime.execution_scheduler.models.execution_request import (
    ExecutionRequest,
)
from src.sam.runtime.execution_scheduler.models.execution_result import (
    ExecutionResult,
    ExecutionResultState,
)


# ──────────────────────────────────────────────
# ExecutionIdentity
# ──────────────────────────────────────────────

class TestExecutionIdentity:
    def test_create_with_required_fields(self):
        ei = ExecutionIdentity(
            execution_id="exec-001",
            approval_reference="approval-001",
            contract_reference="contract-001",
            capability_reference="cap-001",
        )
        assert ei.execution_id == "exec-001"
        assert ei.approval_reference == "approval-001"

    def test_validate_with_valid_fields(self):
        ei = ExecutionIdentity("e1", "a1", "c1", "cp1")
        assert ei.validate() is True

    def test_validate_empty_execution_id_raises(self):
        ei = ExecutionIdentity("", "a1", "c1", "cp1")
        with pytest.raises(ValueError, match="execution_id"):
            ei.validate()

    def test_validate_empty_approval_ref_raises(self):
        ei = ExecutionIdentity("e1", "", "c1", "cp1")
        with pytest.raises(ValueError, match="approval_reference"):
            ei.validate()

    def test_validate_empty_contract_ref_raises(self):
        ei = ExecutionIdentity("e1", "a1", "", "cp1")
        with pytest.raises(ValueError, match="contract_reference"):
            ei.validate()

    def test_validate_empty_capability_ref_raises(self):
        ei = ExecutionIdentity("e1", "a1", "c1", "")
        with pytest.raises(ValueError, match="capability_reference"):
            ei.validate()

    def test_validate_whitespace_only_raises(self):
        ei = ExecutionIdentity("   ", "a1", "c1", "cp1")
        with pytest.raises(ValueError):
            ei.validate()

    def test_identity_is_frozen(self):
        ei = ExecutionIdentity("e1", "a1", "c1", "cp1")
        with pytest.raises(Exception):
            ei.execution_id = "e2"  # type: ignore

    def test_to_dict(self):
        ei = ExecutionIdentity("e1", "a1", "c1", "cp1")
        d = ei.to_dict()
        assert d["execution_id"] == "e1"
        assert d["approval_reference"] == "a1"
        assert d["contract_reference"] == "c1"
        assert d["capability_reference"] == "cp1"

    def test_repr_contains_key_info(self):
        ei = ExecutionIdentity("e1", "a1", "c1", "cp1")
        r = repr(ei)
        assert "e1" in r
        assert "a1" in r


# ──────────────────────────────────────────────
# ExecutionRequest
# ──────────────────────────────────────────────

class TestExecutionRequest:
    def test_create_with_required_fields(self):
        req = ExecutionRequest(
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
        )
        assert req.approval_reference == "appr-001"
        assert req.context is None

    def test_create_with_optional_context(self):
        req = ExecutionRequest(
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            context={"param": "value"},
        )
        assert req.context == {"param": "value"}

    def test_create_with_metadata(self):
        req = ExecutionRequest(
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            metadata={"key": "val"},
        )
        assert req.metadata == {"key": "val"}

    def test_validate_valid_request(self):
        req = ExecutionRequest("a1", "c1", "cp1")
        assert req.validate() is True

    def test_validate_empty_approval_raises(self):
        req = ExecutionRequest("", "c1", "cp1")
        with pytest.raises(ValueError, match="approval_reference"):
            req.validate()

    def test_validate_empty_contract_raises(self):
        req = ExecutionRequest("a1", "", "cp1")
        with pytest.raises(ValueError, match="contract_reference"):
            req.validate()

    def test_validate_empty_capability_raises(self):
        req = ExecutionRequest("a1", "c1", "")
        with pytest.raises(ValueError, match="capability_reference"):
            req.validate()

    def test_request_is_frozen(self):
        req = ExecutionRequest("a1", "c1", "cp1")
        with pytest.raises(Exception):
            req.approval_reference = "a2"  # type: ignore

    def test_repr_contains_key_info(self):
        req = ExecutionRequest("a1", "c1", "cp1")
        r = repr(req)
        assert "a1" in r
        assert "c1" in r


# ──────────────────────────────────────────────
# ExecutionResult + ExecutionResultState
# ──────────────────────────────────────────────

class TestExecutionResultState:
    def test_has_four_states(self):
        states = list(ExecutionResultState)
        assert len(states) == 4

    def test_contains_expected_values(self):
        values = {s.value for s in ExecutionResultState}
        assert "COMPLETED" in values
        assert "FAILED" in values
        assert "CANCELLED" in values
        assert "TIMED_OUT" in values


class TestExecutionResult:
    def test_completed_factory(self):
        r = ExecutionResult.completed("e1", "done")
        assert r.state == ExecutionResultState.COMPLETED
        assert r.execution_id == "e1"
        assert r.message == "done"

    def test_failed_factory(self):
        r = ExecutionResult.failed("e1", "error")
        assert r.state == ExecutionResultState.FAILED

    def test_cancelled_factory(self):
        r = ExecutionResult.cancelled("e1", "stopped")
        assert r.state == ExecutionResultState.CANCELLED

    def test_timed_out_factory(self):
        r = ExecutionResult.timed_out("e1", "timeout")
        assert r.state == ExecutionResultState.TIMED_OUT

    def test_is_success_completed(self):
        r = ExecutionResult.completed("e1")
        assert r.is_success() is True

    def test_is_success_failed(self):
        r = ExecutionResult.failed("e1")
        assert r.is_success() is False

    def test_is_terminal(self):
        r = ExecutionResult.completed("e1")
        assert r.is_terminal() is True

    def test_result_is_frozen(self):
        r = ExecutionResult.completed("e1")
        with pytest.raises(Exception):
            r.state = ExecutionResultState.FAILED  # type: ignore

    def test_repr_contains_state_and_id(self):
        r = ExecutionResult.completed("e1", "ok")
        rep = repr(r)
        assert "e1" in rep
        assert "COMPLETED" in rep

    def test_metadata_defaults_to_empty_dict(self):
        r = ExecutionResult.completed("e1")
        assert r.metadata == {}

    def test_metadata_with_custom(self):
        r = ExecutionResult.completed("e1", metadata={"k": "v"})
        assert r.metadata == {"k": "v"}
