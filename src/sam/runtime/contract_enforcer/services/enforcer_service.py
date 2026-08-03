"""ContractEnforcer — main orchestrator service.

Implements ContractEnforcerInterface.
Orchestrates validation, negotiation, compatibility verification.

Authority: I2-004 §4.4
"""

from typing import Dict, List, Tuple

from sam.runtime.contracts import ContractIdentity, ContractIdempotency
from sam.runtime.contract_enforcer.models.contract_model import Contract
from sam.runtime.contract_enforcer.models.compatibility_result import (
    CompatibilityResult,
)
from sam.runtime.contract_enforcer.models.negotiation_result import (
    NegotiationResult,
)
from sam.runtime.contract_enforcer.lifecycle.enforcer_lifecycle import (
    ContractEnforcerLifecycle,
    ContractEnforcerLifecycleState,
)
from sam.runtime.contract_enforcer.services.health_service import HealthService
from sam.runtime.contract_enforcer.services.negotiator_service import (
    NegotiatorService,
)
from sam.runtime.contract_enforcer.validation.contract_validator import (
    ContractValidator,
)
from sam.runtime.contract_enforcer.validation.compatibility_validator import (
    CompatibilityValidator,
)
from sam.runtime.contract_enforcer.validation.negotiation_validator import (
    NegotiationValidator,
)
from sam.runtime.contract_enforcer.validation.idempotency_validator import (
    IdempotencyValidator,
)
from sam.runtime.contract_enforcer.exceptions.contract_errors import (
    InvalidContract,
    UnknownContract,
    EnforcerNotOperational,
)


class ContractEnforcer:
    """Contract Enforcer — immutable Contracts, idempotency, negotiation.

    Provides:
    - validate_contract: full structural validation
    - negotiate_contract: version negotiation between parties
    - verify_compatibility: compatibility between versions
    - get_health: lifecycle health

    Dependencies: shared + contracts only.
    """

    def __init__(self) -> None:
        self.lifecycle = ContractEnforcerLifecycle()
        self._contracts: Dict[Tuple[str, str], Contract] = {}
        self._contract_validator = ContractValidator()
        self._compatibility_validator = CompatibilityValidator()
        self._negotiation_validator = NegotiationValidator()
        self._idempotency_validator = IdempotencyValidator()
        self._negotiator = NegotiatorService()
        self._health = HealthService()

    # ── Public API ────────────────────────────────────────

    def validate_contract(self, contract: Contract) -> bool:
        """Validate a Contract's full structure.

        Combines structural validation + idempotency validation.
        """
        self._ensure_operational()
        self._contract_validator.validate(contract)
        self._idempotency_validator.validate(contract)
        return True

    def negotiate_contract(
        self,
        offered: ContractIdentity,
        supported_versions: List[ContractIdentity],
    ) -> NegotiationResult:
        """Negotiate a compatible version between two parties."""
        self._ensure_operational()
        self._negotiation_validator.validate_input(offered, supported_versions)
        return self._negotiator.negotiate(offered, supported_versions)

    def verify_compatibility(
        self,
        contract: Contract,
        predecessor: Contract,
    ) -> CompatibilityResult:
        """Verify compatibility between two Contract versions."""
        self._ensure_operational()
        return self._compatibility_validator.verify(contract, predecessor)

    def get_health(self) -> str:
        """Return health status."""
        return self._health.get_health(self.lifecycle.state)

    # ── Internal Contract Registry ─────────────────────────

    def register_contract(self, contract: Contract) -> None:
        """Register a Contract in the internal registry.

        The Contract is stored immutably by (contract_id, version).
        """
        self._ensure_operational()
        self.validate_contract(contract)
        key = (contract.contract_id, contract.version)
        self._contracts[key] = contract

    def get_contract(
        self, contract_id: str, version: str
    ) -> Contract:
        """Retrieve a registered Contract.

        Raises:
            UnknownContract: if not found.
        """
        key = (contract_id, version)
        if key not in self._contracts:
            raise UnknownContract(
                f"Contract '{contract_id}' version '{version}' not found"
            )
        return self._contracts[key]

    def list_contracts(self) -> List[Contract]:
        """List all registered Contracts."""
        return list(self._contracts.values())

    def get_idempotency(
        self, contract_id: str, version: str
    ) -> ContractIdempotency:
        """Read idempotency declaration for a Contract (ADR-003).

        This is the method Execution Scheduler would call to observe
        the idempotency declaration.

        Returns:
            ContractIdempotency value.
        """
        contract = self.get_contract(contract_id, version)
        return IdempotencyValidator.resolve_declaration(contract)

    # ── Internal ──────────────────────────────────────────

    def _ensure_operational(self) -> None:
        """Raise if not in RUNNING state."""
        if not self.lifecycle.is_operational():
            raise EnforcerNotOperational(
                f"Contract Enforcer is not operational "
                f"(state={self.lifecycle.state.value})"
            )
