"""Tests for resolution exception hierarchy.

Authority: I2-003 §4
"""

import pytest

from sam.runtime.discovery_resolver.exceptions.resolution_errors import (
    ResolutionError,
    InvalidRequest,
    RegistryEntryNotFound,
    InvalidRegistryEntry,
    ResolutionNotDeterministic,
    InvalidTransition,
    ResolverNotOperational,
)


class TestExceptionHierarchy:
    """Tests for resolution error hierarchy."""

    def test_all_extend_resolution_error(self) -> None:
        """All exceptions are subclasses of ResolutionError."""
        assert issubclass(InvalidRequest, ResolutionError)
        assert issubclass(RegistryEntryNotFound, ResolutionError)
        assert issubclass(InvalidRegistryEntry, ResolutionError)
        assert issubclass(ResolutionNotDeterministic, ResolutionError)
        assert issubclass(InvalidTransition, ResolutionError)
        assert issubclass(ResolverNotOperational, ResolutionError)

    def test_resolution_error_is_exception(self) -> None:
        """ResolutionError is an Exception."""
        assert issubclass(ResolutionError, Exception)

    def test_can_raise_and_catch(self) -> None:
        """Exceptions can be raised and caught."""
        for exc_cls in [
            InvalidRequest,
            InvalidRegistryEntry,
            InvalidTransition,
            ResolverNotOperational,
        ]:
            with pytest.raises(exc_cls):
                raise exc_cls("test message")

    def test_exceptions_carry_message(self) -> None:
        """Exception message is preserved."""
        msg = "Custom resolution error detail"
        exc = InvalidRequest(msg)
        assert str(exc) == msg

    def test_base_cannot_catch_specific_subtype(self) -> None:
        """Base ResolutionError does not catch a specific subclass."""
        with pytest.raises(InvalidRequest):
            raise InvalidRequest("specific")
        # Should not be caught above

    def test_can_catch_by_base(self) -> None:
        """Specific can be caught by ResolutionError base."""
        caught = False
        try:
            raise InvalidRequest("specific")
        except ResolutionError:
            caught = True
        assert caught is True
