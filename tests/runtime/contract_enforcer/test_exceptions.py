"""Tests for Contract Enforcer exception hierarchy.

Authority: I2-004 §4.7
"""

import pytest

from sam.runtime.contract_enforcer import (
    ContractError,
    InvalidContract,
    UnknownContract,
    UnsupportedVersion,
    IncompatibleContract,
    NegotiationFailure,
    MissingField,
    EnforcerNotOperational,
)


class TestExceptionHierarchy:
    """Tests for contract enforcer exception hierarchy."""

    def test_all_extend_contract_error(self) -> None:
        """All exceptions subclass ContractError."""
        assert issubclass(InvalidContract, ContractError)
        assert issubclass(UnknownContract, ContractError)
        assert issubclass(UnsupportedVersion, ContractError)
        assert issubclass(IncompatibleContract, ContractError)
        assert issubclass(NegotiationFailure, ContractError)
        assert issubclass(MissingField, ContractError)
        assert issubclass(EnforcerNotOperational, ContractError)

    def test_contract_error_is_exception(self) -> None:
        """ContractError is an Exception."""
        assert issubclass(ContractError, Exception)

    def test_can_raise_and_catch(self) -> None:
        """Each exception can be raised and caught."""
        for exc_cls in [
            InvalidContract,
            UnknownContract,
            MissingField,
            EnforcerNotOperational,
        ]:
            with pytest.raises(exc_cls):
                raise exc_cls("test message")

    def test_exceptions_carry_message(self) -> None:
        """Exception message preserved."""
        msg = "Custom detail"
        exc = InvalidContract(msg)
        assert str(exc) == msg

    def test_can_catch_by_base(self) -> None:
        """Specific caught by ContractError."""
        caught = False
        try:
            raise InvalidContract("specific")
        except ContractError:
            caught = True
        assert caught is True
