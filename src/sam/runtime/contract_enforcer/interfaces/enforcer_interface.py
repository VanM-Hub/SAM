"""ContractEnforcerInterface — Protocol defining the public contract.

Authority: I0-001 §2.4 | R5-001 §2.4
"""

from typing import Protocol, runtime_checkable

from sam.runtime.contract_enforcer.models.contract_model import Contract
from sam.runtime.contract_enforcer.models.compatibility_result import (
    CompatibilityResult,
)
from sam.runtime.contract_enforcer.models.negotiation_result import (
    NegotiationResult,
)
from sam.runtime.contracts import ContractIdentity


@runtime_checkable
class ContractEnforcerInterface(Protocol):
    """Public interface for Contract Enforcer.

    Only these four entry points are publicly consumable:
    - validate_contract — full structure validation
    - negotiate_contract — version negotiation between two parties
    - verify_compatibility — compatibility between contract versions
    - get_health — lifecycle health check
    """

    def validate_contract(self, contract: Contract) -> bool:
        """Validate a Contract's full structure.

        Returns True if the Contract satisfies all structural requirements
        (all required fields present, valid idempotency declaration, etc.).

        Args:
            contract: The Contract to validate.

        Returns:
            True if valid.

        Raises:
            InvalidContract: if the Contract is structurally invalid.
            MissingField: if a required field is absent.
        """
        ...

    def negotiate_contract(
        self,
        offered: ContractIdentity,
        supported_versions: list,
    ) -> NegotiationResult:
        """Negotiate a Contract version between two parties.

        Per CONTRACT_SPEC: agree on single version, prefer compatible,
        prefer non-deprecated. No interaction occurs if no mutually
        compatible version exists.

        Args:
            offered: The Contract identity offered by one party.
            supported_versions: List of ContractIdentity supported by the other.

        Returns:
            NegotiationResult with the agreed version or failure reason.
        """
        ...

    def verify_compatibility(
        self,
        contract: Contract,
        predecessor: Contract,
    ) -> CompatibilityResult:
        """Verify compatibility between two Contract versions.

        Checks whether the new version is backward/forward compatible
        with the predecessor.

        Args:
            contract: The newer Contract version.
            predecessor: The older Contract version.

        Returns:
            CompatibilityResult indicating compatibility status.
        """
        ...

    def get_health(self) -> str:
        """Return health status based on lifecycle.

        Returns:
            One of: 'available', 'degraded', 'unavailable'
        """
        ...
