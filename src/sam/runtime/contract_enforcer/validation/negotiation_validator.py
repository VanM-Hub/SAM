"""NegotiationValidator — validates version negotiation process.

Per CONTRACT_SPEC 'Version Negotiation':
    - Both Citizens SHALL agree on a single version
    - A compatible version SHALL be chosen
    - Preference SHALL be given to non-deprecated
    - If no mutually compatible version → fail
"""

from typing import List, Optional

from sam.runtime.contracts import ContractIdentity


class NegotiationValidator:
    """Validates the negotiation process."""

    def validate_input(
        self,
        offered: ContractIdentity,
        supported: List[ContractIdentity],
    ) -> bool:
        """Validate negotiation inputs.

        Args:
            offered: The offered Contract identity.
            supported: List of supported identities.

        Returns:
            True if inputs are valid.

        Raises:
            ValueError: if inputs are invalid.
        """
        if not offered.validate():
            raise ValueError("Offered contract identity is invalid")

        if not supported:
            raise ValueError("Supported versions list is empty")

        for identity in supported:
            if not identity.validate():
                raise ValueError(
                    f"Invalid supported identity: {identity}"
                )

        return True

    def validate_result(
        self,
        result: "NegotiationResult",
        offered: ContractIdentity,
    ) -> bool:
        """Validate that a negotiation result is consistent with inputs.

        Args:
            result: The negotiation result.
            offered: The offered contract identity.

        Returns:
            True if result is consistent.
        """
        from sam.runtime.contract_enforcer.models.negotiation_result import (
            NegotiationStatus,
        )

        # If resolved, the contract_id must match offered
        if result.status in (
            NegotiationStatus.RESOLVED,
            NegotiationStatus.DEPRECATED_ONLY,
        ):
            if result.negotiated_contract_id != offered.contract_id:
                raise ValueError(
                    f"Negotiated contract_id '{result.negotiated_contract_id}' "
                    f"does not match offered '{offered.contract_id}'"
                )

        return True
