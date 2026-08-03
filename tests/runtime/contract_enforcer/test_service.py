"""Tests for ContractEnforcer service — main orchestrator.

Authority: I2-004 §4.4
"""

import pytest

from sam.runtime.contract_enforcer import (
    ContractEnforcer,
    ContractEnforcerLifecycleState,
    Contract,
    UnknownContract,
    EnforcerNotOperational,
    InvalidContract,
    CompatibilityStatus,
)
from sam.runtime.contracts import ContractIdempotency


class TestContractEnforcerService:
    """Tests for ContractEnforcer orchestrator."""

    def setup_method(self) -> None:
        self.enforcer = ContractEnforcer()

    def _start(self) -> None:
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.INITIALIZING
        )
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.RUNNING
        )

    def test_not_operational_raises(self) -> None:
        """Operations fail when not RUNNING."""
        c = Contract("test.contract", "1.0.0", "cap://test")
        with pytest.raises(EnforcerNotOperational):
            self.enforcer.validate_contract(c)

    def test_validate_contract(self) -> None:
        """Valid contract passes validation."""
        self._start()
        c = Contract(
            "test.contract", "1.0.0", "cap://test",
            idempotency_declaration="IDEMPOTENT",
        )
        assert self.enforcer.validate_contract(c) is True

    def test_register_and_get_contract(self) -> None:
        """Can register and retrieve a contract."""
        self._start()
        c = Contract(
            "memory.contract", "1.0.0", "cap://memory",
            input_schema={"query": "string"},
            output_schema={"result": "string"},
            idempotency_declaration="IDEMPOTENT",
        )
        self.enforcer.register_contract(c)

        retrieved = self.enforcer.get_contract("memory.contract", "1.0.0")
        assert retrieved.contract_id == "memory.contract"
        assert retrieved.version == "1.0.0"

    def test_get_contract_missing_raises(self) -> None:
        """Missing contract raises UnknownContract."""
        self._start()
        with pytest.raises(UnknownContract, match="(?i)not found"):
            self.enforcer.get_contract("nonexistent", "1.0.0")

    def test_list_contracts(self) -> None:
        """list_contracts returns all registered."""
        self._start()
        c1 = Contract("c1", "1.0.0", "cap://test")
        c2 = Contract("c2", "1.0.0", "cap://test")
        self.enforcer.register_contract(c1)
        self.enforcer.register_contract(c2)
        assert len(self.enforcer.list_contracts()) == 2

    def test_verify_compatibility_compatible(self) -> None:
        """Compatible contracts return COMPATIBLE."""
        self._start()
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
        result = self.enforcer.verify_compatibility(new, old)
        assert result.status == CompatibilityStatus.COMPATIBLE

    def test_verify_compatibility_different_ids(self) -> None:
        """Different contract_ids → UNKNOWN."""
        self._start()
        old = Contract("a", "1.0.0", "cap://test")
        new = Contract("b", "1.0.0", "cap://test")
        result = self.enforcer.verify_compatibility(new, old)
        assert result.status == CompatibilityStatus.UNKNOWN

    def test_get_idempotency(self) -> None:
        """get_idempotency reads declaration (ADR-003)."""
        self._start()
        c = Contract(
            "memory.contract", "1.0.0", "cap://memory",
            idempotency_declaration="IDEMPOTENT",
        )
        self.enforcer.register_contract(c)
        result = self.enforcer.get_idempotency("memory.contract", "1.0.0")
        assert result == ContractIdempotency.IDEMPOTENT

    def test_get_idempotency_non_idempotent(self) -> None:
        """get_idempotency for NON_IDEMPOTENT."""
        self._start()
        c = Contract(
            "memory.contract", "1.0.0", "cap://memory",
            idempotency_declaration="NON_IDEMPOTENT",
        )
        self.enforcer.register_contract(c)
        result = self.enforcer.get_idempotency("memory.contract", "1.0.0")
        assert result == ContractIdempotency.NON_IDEMPOTENT

    def test_register_invalid_contract_raises(self) -> None:
        """Registering invalid contract raises validation error."""
        self._start()
        c = Contract("", "1.0.0", "cap://test")  # empty contract_id
        with pytest.raises(Exception):
            self.enforcer.register_contract(c)

    def test_immutability_after_registration(self) -> None:
        """Registered contract cannot be modified (frozen)."""
        self._start()
        c = Contract("test.contract", "1.0.0", "cap://test")
        self.enforcer.register_contract(c)
        # The stored contract is the frozen original
        retrieved = self.enforcer.get_contract("test.contract", "1.0.0")
        with pytest.raises(Exception):
            retrieved.contract_id = "changed"  # type: ignore[misc]
