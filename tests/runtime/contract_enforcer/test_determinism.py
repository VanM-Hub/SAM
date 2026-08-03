"""Determinism tests for Contract Enforcer.

Contract Enforcer must produce:
    - Same validation result for same contract
    - Same negotiation result for same inputs
    - Same compatibility result for same pair
    - Side-effect free operations
"""

from sam.runtime.contract_enforcer import (
    ContractEnforcer,
    ContractEnforcerLifecycleState,
    Contract,
    CompatibilityStatus,
)
from sam.runtime.contracts import ContractIdentity


class TestDeterminism:
    """Tests for deterministic behavior."""

    def setup_method(self) -> None:
        self.enforcer = ContractEnforcer()
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.INITIALIZING
        )
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.RUNNING
        )

    def test_same_contract_same_validation(self) -> None:
        """Same contract → same validation result every time."""
        c = Contract(
            "test.contract", "1.0.0", "cap://test",
            idempotency_declaration="IDEMPOTENT",
        )
        results = [self.enforcer.validate_contract(c) for _ in range(50)]
        assert all(r is True for r in results)

    def test_same_negotiation_same_result(self) -> None:
        """Same negotiation inputs → same result every time."""
        offered = ContractIdentity("memory.contract", "1.0.0", "cap://memory")
        supported = [
            ContractIdentity("memory.contract", "1.5.0", "cap://memory"),
            ContractIdentity("memory.contract", "1.2.0", "cap://memory"),
        ]
        results = [
            self.enforcer.negotiate_contract(offered, supported)
            for _ in range(30)
        ]
        first = results[0]
        for r in results:
            assert r.status == first.status
            assert r.negotiated_version == first.negotiated_version

    def test_same_compatibility_same_result(self) -> None:
        """Same pair → same compatibility every time."""
        old = Contract(
            "test.contract", "1.0.0", "cap://test",
            input_schema={"q": "string"},
            output_schema={"r": "string"},
        )
        new = Contract(
            "test.contract", "1.1.0", "cap://test",
            input_schema={"q": "string"},
            output_schema={"r": "string", "t": "int"},
            compatibility={"backward": True, "forward": True},
        )
        results = [
            self.enforcer.verify_compatibility(new, old)
            for _ in range(30)
        ]
        first = results[0]
        for r in results:
            assert r.status == first.status
            assert r.is_compatible == first.is_compatible

    def test_registry_not_mutated_by_validation(self) -> None:
        """Validation does not mutate registry."""
        c = Contract("test.contract", "1.0.0", "cap://test")
        initial = len(self.enforcer.list_contracts())
        for _ in range(30):
            self.enforcer.validate_contract(c)
        assert len(self.enforcer.list_contracts()) == initial

    def test_registry_not_mutated_by_negotiation(self) -> None:
        """Negotiation does not mutate registry."""
        offered = ContractIdentity("memory.contract", "1.0.0", "cap://memory")
        supported = [ContractIdentity("memory.contract", "1.0.0", "cap://memory")]
        initial = len(self.enforcer.list_contracts())
        for _ in range(30):
            self.enforcer.negotiate_contract(offered, supported)
        assert len(self.enforcer.list_contracts()) == initial
