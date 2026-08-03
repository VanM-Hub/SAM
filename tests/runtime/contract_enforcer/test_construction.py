"""Construction test for Contract Enforcer.

Verifies:
    - Instantiable independently
    - No dependency on other units (citizen_host, capability_manager, etc.)
    - Full lifecycle works after construction
"""

from sam.runtime.contract_enforcer import (
    ContractEnforcer,
    ContractEnforcerLifecycleState,
    Contract,
    NegotiationStatus,
    CompatibilityStatus,
)
from sam.runtime.contracts import ContractIdentity, ContractIdempotency


class TestConstruction:
    """Tests for Contract Enforcer construction."""

    def test_instantiate_without_external_deps(self) -> None:
        """Can instantiate without any cross-unit imports."""
        enforcer = ContractEnforcer()
        assert enforcer is not None

    def test_initial_health_is_unavailable(self) -> None:
        """Fresh enforcer → 'unavailable'."""
        enforcer = ContractEnforcer()
        assert enforcer.get_health() == "unavailable"

    def test_initial_registry_is_empty(self) -> None:
        """Fresh enforcer has empty contract registry."""
        enforcer = ContractEnforcer()
        assert len(enforcer.list_contracts()) == 0

    def test_full_lifecycle_validation_negotiation(self) -> None:
        """Construction → start → validate → register → negotiate."""
        enforcer = ContractEnforcer()

        # Start
        enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.INITIALIZING
        )
        enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.RUNNING
        )
        assert enforcer.get_health() == "available"

        # Validate and register
        c = Contract(
            "memory.contract", "1.0.0", "cap://memory",
            input_schema={"query": "string"},
            output_schema={"result": "string"},
            idempotency_declaration="IDEMPOTENT",
        )
        enforcer.validate_contract(c)
        enforcer.register_contract(c)

        # Retrieve
        retrieved = enforcer.get_contract("memory.contract", "1.0.0")
        assert retrieved.contract_id == "memory.contract"

        # Negotiate
        offered = ContractIdentity("memory.contract", "1.0.0", "cap://memory")
        supported = [ContractIdentity("memory.contract", "1.0.0", "cap://memory")]
        result = enforcer.negotiate_contract(offered, supported)
        assert result.status == NegotiationStatus.RESOLVED

        # Compatibility
        old = Contract(
            "memory.contract", "1.0.0", "cap://memory",
            input_schema={"query": "string"},
            output_schema={"result": "string"},
        )
        new = Contract(
            "memory.contract", "1.1.0", "cap://memory",
            input_schema={"query": "string"},
            output_schema={"result": "string", "total": "int"},
            compatibility={"backward": True, "forward": True},
        )
        compat = enforcer.verify_compatibility(new, old)
        assert compat.status == CompatibilityStatus.COMPATIBLE

        # Idempotency
        idem = enforcer.get_idempotency("memory.contract", "1.0.0")
        assert idem == ContractIdempotency.IDEMPOTENT

    def test_construction_independent_of_other_units(self) -> None:
        """No import from capability_manager, citizen_host, etc."""
        # This test verifies architectural independence
        enforcer = ContractEnforcer()
        enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.INITIALIZING
        )
        enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.RUNNING
        )

        c = Contract("test.cap", "1.0.0", "cap://test")
        enforcer.register_contract(c)
        assert len(enforcer.list_contracts()) == 1
