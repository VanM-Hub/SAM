"""ContractValidator — validates full Contract structure.

Per CONTRACT_SPEC: validates that all required fields are present and valid.
Also validates idempotency declaration per ADR-003.
"""

from typing import Dict, Any, Set

from sam.runtime.contract_enforcer.models.contract_model import Contract
from sam.runtime.contract_enforcer.exceptions.contract_errors import (
    InvalidContract,
    MissingField,
)
from sam.runtime.contracts import ContractIdempotency

# Required fields from CONTRACT_SPEC
_REQUIRED_FIELDS: Set[str] = {
    "contract_id",
    "version",
    "capability_reference",
}

# Valid idempotency values (ADR-003)
_VALID_IDEMPOTENCY: Set[str] = {
    ContractIdempotency.IDEMPOTENT.value,
    ContractIdempotency.NON_IDEMPOTENT.value,
}


class ContractValidator:
    """Validates a Contract's full structural integrity."""

    def validate(self, contract: Contract) -> bool:
        """Validate a Contract.

        Checks:
        1. All required fields are non-empty
        2. Idempotency declaration is valid
        3. Version format is plausible

        Args:
            contract: The Contract to validate.

        Returns:
            True if valid.

        Raises:
            MissingField: if a required field is empty/missing.
            InvalidContract: if the contract is structurally invalid.
        """
        # Required fields presence
        if not contract.contract_id or not contract.contract_id.strip():
            raise MissingField("Contract contract_id is required")
        if not contract.version or not contract.version.strip():
            raise MissingField("Contract version is required")
        if (
            not contract.capability_reference
            or not contract.capability_reference.strip()
        ):
            raise MissingField("Contract capability_reference is required")

        # Version format: must be semver-like
        if not self._is_valid_version(contract.version):
            raise InvalidContract(
                f"Invalid version format: '{contract.version}'"
            )

        # Idempotency declaration (ADR-003)
        if contract.idempotency_declaration not in _VALID_IDEMPOTENCY:
            raise InvalidContract(
                f"Invalid idempotency declaration: "
                f"'{contract.idempotency_declaration}'. "
                f"Must be IDEMPOTENT or NON_IDEMPOTENT"
            )

        return True

    @staticmethod
    def _is_valid_version(version: str) -> bool:
        """Check if version string is semver-like (MAJOR.MINOR.PATCH)."""
        parts = version.split(".")
        if len(parts) != 3:
            return False
        return all(p.isdigit() for p in parts)
