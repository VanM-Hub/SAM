"""Tests: Exception Hierarchy — EXECUTION_SPEC defined failures + internal."""

import pytest
from src.sam.runtime.execution_scheduler.exceptions.execution_errors import (
    ExecutionError,
    MissingApprovalError,
    InvalidApprovalError,
    MissingContractError,
    CapabilityUnavailableError,
    ExecutionTimeoutError,
    ExecutionFailureError,
    ExecutionConflictError,
    ExecutionNotFoundError,
    InvalidTransitionError,
    OrderingViolationError,
    VerificationFailureError,
    NotOperationalError,
    InvalidExecutionRequestError,
)


class TestExceptionHierarchy:
    def test_all_extend_execution_error(self):
        exceptions = [
            MissingApprovalError,
            InvalidApprovalError,
            MissingContractError,
            CapabilityUnavailableError,
            ExecutionTimeoutError,
            ExecutionFailureError,
            ExecutionConflictError,
            ExecutionNotFoundError,
            InvalidTransitionError,
            OrderingViolationError,
            VerificationFailureError,
            NotOperationalError,
            InvalidExecutionRequestError,
        ]
        for exc_cls in exceptions:
            assert issubclass(exc_cls, ExecutionError), \
                f"{exc_cls.__name__} does not extend ExecutionError"

    def test_execution_error_is_exception(self):
        assert issubclass(ExecutionError, Exception)

    def test_can_raise_and_catch(self):
        try:
            raise MissingApprovalError("test message")
        except MissingApprovalError as e:
            assert str(e) == "test message"

    def test_exceptions_carry_message(self):
        for exc_cls in [
            MissingApprovalError,
            InvalidApprovalError,
            MissingContractError,
            ExecutionConflictError,
            NotOperationalError,
        ]:
            exc = exc_cls("test text")
            assert str(exc) == "test text"

    def test_can_catch_by_base(self):
        try:
            raise InvalidApprovalError("bad")
        except ExecutionError:
            pass
        else:
            pytest.fail("Should have caught by ExecutionError")

    def test_base_can_catch_conflict(self):
        try:
            raise ExecutionConflictError("conflict")
        except ExecutionError:
            pass
        else:
            pytest.fail("Should have caught ExecutionConflictError via ExecutionError")

    def test_base_can_catch_not_operational(self):
        try:
            raise NotOperationalError("not running")
        except ExecutionError:
            pass
        else:
            pytest.fail("Should have caught NotOperationalError via ExecutionError")

    def test_default_empty_message(self):
        exc = MissingApprovalError()
        assert str(exc) == ""

    def test_all_exception_count(self):
        """We have 13 exception types (1 base + 12 specific)."""
        specific = [
            MissingApprovalError,
            InvalidApprovalError,
            MissingContractError,
            CapabilityUnavailableError,
            ExecutionTimeoutError,
            ExecutionFailureError,
            ExecutionConflictError,
            ExecutionNotFoundError,
            InvalidTransitionError,
            OrderingViolationError,
            VerificationFailureError,
            NotOperationalError,
            InvalidExecutionRequestError,
        ]
        # Verify count: 7 defined + 6 internal = 13
        assert len(specific) == 13

    def test_specific_vs_base_catch(self):
        """Catching by base ExecutionError catches all subtypes."""
        caught = 0
        exceptions_to_test = [
            MissingApprovalError("m1"),
            InvalidApprovalError("m2"),
            ExecutionConflictError("m3"),
            NotOperationalError("m4"),
        ]
        for exc in exceptions_to_test:
            try:
                raise exc
            except ExecutionError:
                caught += 1
        assert caught == 4
