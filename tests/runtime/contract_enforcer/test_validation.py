"""Tests for validation — contract, compatibility, negotiation, idempotency.

Authority: I2-004 §5
"""

import pytest

from sam.runtime.contract_enforcer import (
    Contract,
    InvalidContract,
    MissingField,
)
from sam.runtime.contract_enforcer.validation.contract_validator import (
    ContractValidator,
)
from sam.runtime.contract_enforcer.validation.compatibility_validator import (
    CompatibilityValidator,
    CompatibilityStatus,
)
from sam.runtime.contract_enforcer.validation.negotiation_validator import (
    NegotiationValidator,
)
from sam.runtime.contract_enforcer.validation.idempotency_validator import (
    IdempotencyValidator,
)
from sam.runtime.contracts import (
    ContractIdentity,
    ContractIdempotency,
)


class TestContractValidator:
    """Tests for structural contract validation."""

    def setup_method(self) -> None:
        self.validator = ContractValidator()

    def test_valid_contract(self) -> None:
        """Valid contract passes."""
        c = Contract("test.contract", "1.0.0", "cap://test")
        assert self.validator.validate(c) is True

    def test_empty_contract_id_raises(self) -> None:
        """Empty contract_id raises MissingField."""
        c = Contract("", "1.0.0", "cap://test")
        with pytest.raises(MissingField, match="(?i)contract_id"):
            self.validator.validate(c)

    def test_empty_version_raises(self) -> None:
        """Empty version raises MissingField."""
        c = Contract("test.contract", "", "cap://test")
        with pytest.raises(MissingField, match="(?i)version"):
            self.validator.validate(c)

    def test_empty_capability_reference_raises(self) -> None:
        """Empty capability_reference raises MissingField."""
        c = Contract("test.contract", "1.0.0", "")
        with pytest.raises(MissingField, match="(?i)capability"):
            self.validator.validate(c)

    def test_invalid_version_format(self) -> None:
        """Non-semver version raises InvalidContract."""
        c = Contract("test.contract", "v1.0", "cap://test")
        with pytest.raises(InvalidContract, match="(?i)version"):
            self.validator.validate(c)

    def test_invalid_idempotency_declaration(self) -> None:
        """Invalid idempotency value raises InvalidContract."""
        c = Contract(
            "test.contract", "1.0.0", "cap://test",
            idempotency_declaration="MAYBE",
        )
        with pytest.raises(InvalidContract, match="(?i)idempotency"):
            self.validator.validate(c)

    def test_valid_version_formats(self) -> None:
        """Valid semver formats pass."""
        for ver in ["0.0.1", "1.0.0", "10.20.30"]:
            c = Contract("test.contract", ver, "cap://test")
            assert self.validator.validate(c) is True


class TestCompatibilityValidator:
    """Tests for compatibility verification."""

    def setup_method(self) -> None:
        self.validator = CompatibilityValidator()

    def test_same_contract_id_is_compatible(self) -> None:
        """Same contract_id with backward/forward=True is compatible."""
        old = Contract("test.contract", "1.0.0", "cap://test")
        new = Contract(
            "test.contract", "1.1.0", "cap://test",
            compatibility={"backward": True, "forward": True},
        )
        result = self.validator.verify(new, old)
        assert result.status == CompatibilityStatus.COMPATIBLE
        assert result.is_compatible is True

    def test_different_contract_id_is_unknown(self) -> None:
        """Different contract_id → UNKNOWN."""
        old = Contract("test.contract", "1.0.0", "cap://test")
        new = Contract("other.contract", "1.0.0", "cap://test")
        result = self.validator.verify(new, old)
        assert result.status == CompatibilityStatus.UNKNOWN
        assert result.is_compatible is False

    def test_declared_breaking_is_breaking(self) -> None:
        """Contract declaring breaking changes → BREAKING."""
        old = Contract("test.contract", "1.0.0", "cap://test")
        new = Contract(
            "test.contract", "2.0.0", "cap://test",
            compatibility={
                "backward": False,
                "forward": False,
                "breaking_changes": ["Removed field X"],
            },
        )
        result = self.validator.verify(new, old)
        assert result.status == CompatibilityStatus.BREAKING
        assert result.is_compatible is False

    def test_removed_input_fields_is_breaking(self) -> None:
        """Removing input fields from schema is breaking."""
        old = Contract(
            "test.contract", "1.0.0", "cap://test",
            input_schema={"query": "string", "filter": "string"},
        )
        new = Contract(
            "test.contract", "1.1.0", "cap://test",
            input_schema={"query": "string"},
            compatibility={"backward": True, "forward": True},
        )
        result = self.validator.verify(new, old)
        assert result.status == CompatibilityStatus.BREAKING

    def test_removed_output_fields_is_breaking(self) -> None:
        """Removing output fields is breaking."""
        old = Contract(
            "test.contract", "1.0.0", "cap://test",
            output_schema={"result": "string", "count": "int"},
        )
        new = Contract(
            "test.contract", "1.1.0", "cap://test",
            output_schema={"result": "string"},
            compatibility={"backward": True, "forward": True},
        )
        result = self.validator.verify(new, old)
        assert result.status == CompatibilityStatus.BREAKING

    def test_adding_fields_is_compatible(self) -> None:
        """Adding new fields is compatible."""
        old = Contract(
            "test.contract", "1.0.0", "cap://test",
            input_schema={"query": "string"},
            output_schema={"result": "string"},
        )
        new = Contract(
            "test.contract", "1.1.0", "cap://test",
            input_schema={"query": "string", "limit": "int"},
            output_schema={"result": "string", "total": "int"},
            compatibility={"backward": True, "forward": True},
        )
        result = self.validator.verify(new, old)
        assert result.status == CompatibilityStatus.COMPATIBLE


class TestNegotiationValidator:
    """Tests for negotiation validation."""

    def setup_method(self) -> None:
        self.validator = NegotiationValidator()

    def test_valid_inputs(self) -> None:
        """Valid inputs pass."""
        offered = ContractIdentity("test.contract", "1.0.0", "cap://test")
        supported = [ContractIdentity("test.contract", "1.0.0", "cap://test")]
        assert self.validator.validate_input(offered, supported) is True

    def test_invalid_offered(self) -> None:
        """Invalid offered identity raises ValueError."""
        offered = ContractIdentity("", "1.0.0", "cap://test")
        supported = [ContractIdentity("test.contract", "1.0.0", "cap://test")]
        with pytest.raises(ValueError):
            self.validator.validate_input(offered, supported)

    def test_empty_supported(self) -> None:
        """Empty supported list raises ValueError."""
        offered = ContractIdentity("test.contract", "1.0.0", "cap://test")
        with pytest.raises(ValueError, match="empty"):
            self.validator.validate_input(offered, [])


class TestIdempotencyValidator:
    """Tests for idempotency validation."""

    def setup_method(self) -> None:
        self.validator = IdempotencyValidator()

    def test_valid_idempotent(self) -> None:
        """IDEMPOTENT is valid."""
        c = Contract(
            "test.contract", "1.0.0", "cap://test",
            idempotency_declaration="IDEMPOTENT",
        )
        assert self.validator.validate(c) is True

    def test_valid_non_idempotent(self) -> None:
        """NON_IDEMPOTENT is valid."""
        c = Contract(
            "test.contract", "1.0.0", "cap://test",
            idempotency_declaration="NON_IDEMPOTENT",
        )
        assert self.validator.validate(c) is True

    def test_empty_declaration_raises(self) -> None:
        """Empty declaration raises InvalidContract."""
        c = Contract(
            "test.contract", "1.0.0", "cap://test",
            idempotency_declaration="",
        )
        with pytest.raises(InvalidContract, match="(?i)idempotency"):
            self.validator.validate(c)

    def test_invalid_declaration_raises(self) -> None:
        """Invalid declaration raises InvalidContract."""
        c = Contract(
            "test.contract", "1.0.0", "cap://test",
            idempotency_declaration="UNKNOWN",
        )
        with pytest.raises(InvalidContract, match="(?i)idempotency"):
            self.validator.validate(c)

    def test_resolve_idempotent(self) -> None:
        """resolve_declaration returns IDEMPOTENT enum."""
        c = Contract(
            "test.contract", "1.0.0", "cap://test",
            idempotency_declaration="IDEMPOTENT",
        )
        assert IdempotencyValidator.resolve_declaration(c) == ContractIdempotency.IDEMPOTENT

    def test_resolve_non_idempotent(self) -> None:
        """resolve_declaration returns NON_IDEMPOTENT for non-idempotent."""
        c = Contract(
            "test.contract", "1.0.0", "cap://test",
            idempotency_declaration="NON_IDEMPOTENT",
        )
        assert IdempotencyValidator.resolve_declaration(c) == ContractIdempotency.NON_IDEMPOTENT

    def test_resolve_defaults_to_non_idempotent(self) -> None:
        """resolve_declaration defaults to NON_IDEMPOTENT (safe default)."""
        c = Contract("test.contract", "1.0.0", "cap://test")
        assert IdempotencyValidator.resolve_declaration(c) == ContractIdempotency.NON_IDEMPOTENT
