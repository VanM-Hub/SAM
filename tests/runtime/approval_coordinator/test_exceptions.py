"""Tests: Approval Coordinator exception hierarchy."""

import pytest

from src.sam.runtime.approval_coordinator.exceptions.approval_errors import (
    ApprovalError,
    MissingContractError,
    UnknownCapabilityError,
    RegistryResolutionError,
    InvalidRequestError,
    ExpiredRequestError,
    ApprovalConflictError,
    InvalidTransitionError,
    ApprovalNotFoundError,
    CoordinatorNotOperationalError,
)


class TestExceptionHierarchy:
    """Tests for exception hierarchy and inheritance."""

    def test_all_extend_approval_error(self):
        assert issubclass(MissingContractError, ApprovalError)
        assert issubclass(UnknownCapabilityError, ApprovalError)
        assert issubclass(RegistryResolutionError, ApprovalError)
        assert issubclass(InvalidRequestError, ApprovalError)
        assert issubclass(ExpiredRequestError, ApprovalError)
        assert issubclass(ApprovalConflictError, ApprovalError)
        assert issubclass(InvalidTransitionError, ApprovalError)
        assert issubclass(ApprovalNotFoundError, ApprovalError)
        assert issubclass(CoordinatorNotOperationalError, ApprovalError)

    def test_approval_error_is_exception(self):
        assert issubclass(ApprovalError, Exception)

    def test_can_raise_and_catch(self):
        try:
            raise InvalidRequestError("Bad request")
        except InvalidRequestError as e:
            assert str(e) == "Bad request"

    def test_exceptions_carry_message(self):
        e = ApprovalNotFoundError("ID 'xyz' not found")
        assert "xyz" in str(e)

    def test_can_catch_by_base(self):
        errors = [
            MissingContractError("m"),
            UnknownCapabilityError("u"),
            InvalidRequestError("i"),
            ExpiredRequestError("e"),
        ]
        for err in errors:
            try:
                raise err
            except ApprovalError:
                pass  # All caught by base
            except Exception:
                pytest.fail(f"{type(err).__name__} not caught by ApprovalError")

    def test_default_messages(self):
        e = InvalidRequestError()
        assert isinstance(e, ApprovalError)
