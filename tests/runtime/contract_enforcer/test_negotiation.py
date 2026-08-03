"""Tests for version negotiation.

Per CONTRACT_SPEC 'Version Negotiation':
    agree on single version, prefer compatible, prefer non-deprecated.
"""

import pytest

from sam.runtime.contracts import ContractIdentity
from sam.runtime.contract_enforcer import (
    ContractEnforcer,
    ContractEnforcerLifecycleState,
    NegotiationStatus,
)


class TestNegotiation:
    """Tests for version negotiation."""

    def setup_method(self) -> None:
        self.enforcer = ContractEnforcer()
        self._start()

    def _start(self) -> None:
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.INITIALIZING
        )
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.RUNNING
        )

    def test_single_version_match(self) -> None:
        """Both parties support the same version → RESOLVED."""
        offered = ContractIdentity("memory.contract", "1.0.0", "cap://memory")
        supported = [ContractIdentity("memory.contract", "1.0.0", "cap://memory")]
        result = self.enforcer.negotiate_contract(offered, supported)
        assert result.status == NegotiationStatus.RESOLVED
        assert result.negotiated_version == "1.0.0"

    def test_highest_version_selected(self) -> None:
        """Multiple compatible → highest version selected."""
        offered = ContractIdentity("memory.contract", "1.0.0", "cap://memory")
        supported = [
            ContractIdentity("memory.contract", "1.0.0", "cap://memory"),
            ContractIdentity("memory.contract", "1.5.0", "cap://memory"),
            ContractIdentity("memory.contract", "1.2.0", "cap://memory"),
        ]
        result = self.enforcer.negotiate_contract(offered, supported)
        assert result.status == NegotiationStatus.RESOLVED
        assert result.negotiated_version == "1.5.0"

    def test_no_common_versions(self) -> None:
        """No common contract_id → NO_INTERSECTION."""
        offered = ContractIdentity("memory.contract", "1.0.0", "cap://memory")
        supported = [ContractIdentity("other.contract", "1.0.0", "cap://other")]
        result = self.enforcer.negotiate_contract(offered, supported)
        assert result.status == NegotiationStatus.NO_INTERSECTION

    def test_deterministic_same_input_same_result(self) -> None:
        """Same inputs → same result every time."""
        offered = ContractIdentity("memory.contract", "1.0.0", "cap://memory")
        supported = [
            ContractIdentity("memory.contract", "1.5.0", "cap://memory"),
            ContractIdentity("memory.contract", "1.2.0", "cap://memory"),
        ]
        results = [
            self.enforcer.negotiate_contract(offered, supported)
            for _ in range(20)
        ]
        first = results[0]
        for r in results:
            assert r.status == first.status
            assert r.negotiated_version == first.negotiated_version

    def test_is_success_methods(self) -> None:
        """is_success() and is_failed() behave correctly."""
        offered = ContractIdentity("memory.contract", "1.0.0", "cap://memory")
        supported = [ContractIdentity("memory.contract", "1.0.0", "cap://memory")]
        result = self.enforcer.negotiate_contract(offered, supported)
        assert result.is_success() is True
        assert result.is_failed() is False

        # No intersection
        offered2 = ContractIdentity("memory.contract", "1.0.0", "cap://memory")
        supported2 = [ContractIdentity("other.contract", "1.0.0", "cap://other")]
        result2 = self.enforcer.negotiate_contract(offered2, supported2)
        assert result2.is_failed() is True
        assert result2.is_success() is False

    def test_version_tuple_sorting(self) -> None:
        """Version sorting works with multi-digit versions."""
        offered = ContractIdentity("memory.contract", "1.0.0", "cap://memory")
        supported = [
            ContractIdentity("memory.contract", "1.2.0", "cap://memory"),
            ContractIdentity("memory.contract", "1.12.0", "cap://memory"),
            ContractIdentity("memory.contract", "1.3.0", "cap://memory"),
        ]
        result = self.enforcer.negotiate_contract(offered, supported)
        # 1.12.0 > 1.3.0 (numeric comparison)
        assert result.negotiated_version == "1.12.0"
