"""IdempotencyValidator — validates idempotency declarations.

Per ADR-003:
    - Contract declares idempotency (IDEMPOTENT / NON-IDEMPOTENT)
    - Safe default: no declaration → assume non-idempotent
    - Declaration must be explicit
"""

from typing import Set

from sam.runtime.contract_enforcer.models.contract_model import Contract
from sam.runtime.contract_enforcer.exceptions.contract_errors import (
    InvalidContract,
)
from sam.runtime.contracts import ContractIdempotency

_VALID_DECLARATIONS: Set[str] = {
    ContractIdempotency.IDEMPOTENT.value,
    ContractIdempotency.NON_IDEMPOTENT.value,
}


class IdempotencyValidator:
    """Validates idempotency declarations per ADR-003."""

    def validate(self, contract: Contract) -> bool:
        """Validate the idempotency declaration of a Contract.

        Per ADR-003:
        - Declaration must be explicit (not empty/None)
        - Must be one of: IDEMPOTENT, NON_IDEMPOTENT
        - Safe default: missing → NON_IDEMPOTENT

        Args:
            contract: The Contract to validate.

        Returns:
            True if the declaration is valid.

        Raises:
            InvalidContract: if declaration is invalid.
        """
        declaration = contract.idempotency_declaration

        if not declaration or not declaration.strip():
            raise InvalidContract(
                "Idempotency declaration is required per ADR-003. "
                "Must be IDEMPOTENT or NON_IDEMPOTENT"
            )

        if declaration not in _VALID_DECLARATIONS:
            raise InvalidContract(
                f"Invalid idempotency declaration: '{declaration}'. "
                f"Must be one of: {', '.join(sorted(_VALID_DECLARATIONS))}"
            )

        return True

    @staticmethod
    def resolve_declaration(contract: Contract) -> ContractIdempotency:
        """Resolve effective idempotency — safe default non-idempotent.

        Returns:
            ContractIdempotency value.
        """
        if contract.idempotency_declaration == ContractIdempotency.IDEMPOTENT.value:
            return ContractIdempotency.IDEMPOTENT
        return ContractIdempotency.NON_IDEMPOTENT
