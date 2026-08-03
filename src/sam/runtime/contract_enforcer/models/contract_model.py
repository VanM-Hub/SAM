"""Contract model — immutable, frozen representation of a Contract.

Per CONTRACT_SPEC:
    Contract = Input + Output + Metadata + Constraints + Compatibility + Error

Per ADR-003:
    Contract declares idempotency (IDEMPOTENT / NON-IDEMPOTENT)
"""

from dataclasses import dataclass, field
from typing import Dict, Any

from sam.runtime.contracts import ContractIdentity, ContractIdempotency


@dataclass(frozen=True)
class Contract:
    """Immutable Contract per CONTRACT_SPEC.

    A Contract defines the shape of an interaction between two Citizens
    through a Capability, without sharing implementation.

    Fields (from CONTRACT_SPEC):
        contract_id: global identifier
        version: semver version
        capability_reference: reference to the Capability
        input_schema: the information the interaction expects
        output_schema: the information the interaction returns
        metadata: descriptive information
        constraints: conditions the interaction requires/obeys
        compatibility: how this aligns with neighboring versions
        error_definitions: failure outcomes the interaction may produce
        idempotency_declaration: IDEMPOTENT or NON-IDEMPOTENT (ADR-003)
    """
    contract_id: str
    version: str
    capability_reference: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    compatibility: Dict[str, Any] = field(default_factory=dict)
    error_definitions: Dict[str, str] = field(default_factory=dict)
    idempotency_declaration: str = ContractIdempotency.NON_IDEMPOTENT.value

    @property
    def identity(self) -> ContractIdentity:
        """Derived ContractIdentity."""
        return ContractIdentity(
            contract_id=self.contract_id,
            version=self.version,
            capability_reference=self.capability_reference,
        )

    @property
    def major_version(self) -> int:
        """Extract major version component."""
        try:
            return int(self.version.split(".")[0])
        except (ValueError, IndexError):
            return 0

    def validate(self) -> bool:
        """Basic field presence check — all required fields must be non-empty."""
        return bool(
            self.contract_id.strip()
            and self.version.strip()
            and self.capability_reference.strip()
        )

    def is_idempotent(self) -> bool:
        """Check if this Contract declares idempotency (ADR-003)."""
        return self.idempotency_declaration == ContractIdempotency.IDEMPOTENT.value

    def is_deprecated(self) -> bool:
        """Check if this Contract is deprecated."""
        return self.metadata.get("status") == "DEPRECATED"

    def __repr__(self) -> str:
        return (
            f"Contract("
            f"id='{self.contract_id}', "
            f"v='{self.version}', "
            f"idempotent={self.is_idempotent()})"
        )
