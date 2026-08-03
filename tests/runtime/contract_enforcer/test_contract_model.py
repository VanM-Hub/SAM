"""Tests for Contract model.

Authority: I2-004 §4 | CONTRACT_SPEC
"""

import pytest

from sam.runtime.contract_enforcer import Contract
from sam.runtime.contracts import ContractIdempotency


class TestContract:
    """Tests for Contract frozen model."""

    def test_create_with_required_fields(self) -> None:
        """Can create with required fields."""
        c = Contract("memory.contract", "1.0.0", "cap://memory")
        assert c.contract_id == "memory.contract"
        assert c.version == "1.0.0"
        assert c.capability_reference == "cap://memory"

    def test_create_with_all_fields(self) -> None:
        """Can create with all optional fields."""
        c = Contract(
            contract_id="memory.contract",
            version="1.0.0",
            capability_reference="cap://memory",
            input_schema={"query": "string"},
            output_schema={"result": "string"},
            metadata={"description": "Memory lookup contract"},
            constraints={"max_length": 1000},
            compatibility={"backward": True, "forward": True},
            error_definitions={"NOT_FOUND": "Memory entry not found"},
            idempotency_declaration="IDEMPOTENT",
        )
        assert c.input_schema == {"query": "string"}
        assert c.output_schema == {"result": "string"}
        assert c.idempotency_declaration == "IDEMPOTENT"

    def test_validate_valid_contract(self) -> None:
        """validate() returns True for complete contract."""
        c = Contract("memory.contract", "1.0.0", "cap://memory")
        assert c.validate() is True

    def test_validate_empty_contract_id(self) -> None:
        """validate() returns False for empty contract_id."""
        c = Contract("", "1.0.0", "cap://memory")
        assert c.validate() is False

    def test_validate_empty_version(self) -> None:
        """validate() returns False for empty version."""
        c = Contract("memory.contract", "", "cap://memory")
        assert c.validate() is False

    def test_validate_empty_capability_reference(self) -> None:
        """validate() returns False for empty capability_reference."""
        c = Contract("memory.contract", "1.0.0", "")
        assert c.validate() is False

    def test_validate_whitespace_only(self) -> None:
        """validate() returns False for whitespace-only fields."""
        c = Contract("  ", "1.0.0", "cap://memory")
        assert c.validate() is False

    def test_default_idempotency_is_non_idempotent(self) -> None:
        """Default idempotency_declaration is NON_IDEMPOTENT (safe default)."""
        c = Contract("memory.contract", "1.0.0", "cap://memory")
        assert c.idempotency_declaration == "NON_IDEMPOTENT"

    def test_is_idempotent_returns_true(self) -> None:
        """is_idempotent() returns True for IDEMPOTENT."""
        c = Contract(
            "memory.contract", "1.0.0", "cap://memory",
            idempotency_declaration="IDEMPOTENT",
        )
        assert c.is_idempotent() is True

    def test_is_idempotent_returns_false(self) -> None:
        """is_idempotent() returns False for NON_IDEMPOTENT."""
        c = Contract(
            "memory.contract", "1.0.0", "cap://memory",
            idempotency_declaration="NON_IDEMPOTENT",
        )
        assert c.is_idempotent() is False

    def test_identity_property(self) -> None:
        """identity property returns ContractIdentity."""
        c = Contract("memory.contract", "2.0.0", "cap://memory")
        ident = c.identity
        assert ident.contract_id == "memory.contract"
        assert ident.version == "2.0.0"
        assert ident.capability_reference == "cap://memory"

    def test_major_version(self) -> None:
        """major_version extracts major component."""
        c = Contract("x", "3.2.1", "y")
        assert c.major_version == 3

    def test_major_version_invalid(self) -> None:
        """major_version returns 0 for invalid version."""
        c = Contract("x", "abc", "y")
        assert c.major_version == 0

    def test_is_deprecated(self) -> None:
        """is_deprecated() checks metadata status."""
        c = Contract("x", "1.0.0", "y", metadata={"status": "DEPRECATED"})
        assert c.is_deprecated() is True

    def test_is_not_deprecated_by_default(self) -> None:
        """New contract is not deprecated."""
        c = Contract("x", "1.0.0", "y")
        assert c.is_deprecated() is False

    def test_contract_is_frozen(self) -> None:
        """Contract dataclass is frozen — immutable."""
        c = Contract("memory.contract", "1.0.0", "cap://memory")
        with pytest.raises(Exception):
            c.contract_id = "changed"  # type: ignore[misc]

    def test_repr_includes_key_info(self) -> None:
        """repr includes id and idempotency."""
        c = Contract("memory.contract", "1.0.0", "cap://memory")
        r = repr(c)
        assert "memory.contract" in r
        assert "1.0.0" in r
        assert "idempotent=False" in r
