"""Shared Contract infrastructure.

Contract definitions, identity types, and idempotency declarations
used by all units that interact with Contracts.

Authority: CONTRACT_SPEC | ADR-003
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any


# ──────────────────────────────────────────────
# Idempotency Declaration (ADR-003)
# ──────────────────────────────────────────────

class ContractIdempotency(str, Enum):
    """Idempotency declaration per ADR-003.

    Contract declares; Execution observes.
    """
    IDEMPOTENT = "IDEMPOTENT"
    NON_IDEMPOTENT = "NON_IDEMPOTENT"


# ──────────────────────────────────────────────
# Contract Identity (CONTRACT_SPEC)
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class ContractIdentity:
    """Contract identity per CONTRACT_SPEC.

    Every Contract possesses a distinct identity:
    - contract_id: global identifier
    - version: semver version
    - capability_reference: reference to the Capability
    """
    contract_id: str
    version: str
    capability_reference: str

    def validate(self) -> bool:
        """Basic field presence check."""
        return bool(
            self.contract_id.strip()
            and self.version.strip()
            and self.capability_reference.strip()
        )

    def major_version(self) -> int:
        """Extract major version component."""
        try:
            return int(self.version.split(".")[0])
        except (ValueError, IndexError):
            return 0

    def __repr__(self) -> str:
        return (
            f"ContractIdentity("
            f"id='{self.contract_id}', "
            f"v='{self.version}', "
            f"cap='{self.capability_reference}')"
        )


# ──────────────────────────────────────────────
# Compatibility Types
# ──────────────────────────────────────────────

class CompatibilityDirection(str, Enum):
    """Direction of compatibility between Contract versions."""
    BACKWARD = "BACKWARD"   # older consumer works with newer
    FORWARD = "FORWARD"     # newer consumer works with older
    BREAKING = "BREAKING"   # breaks backward or forward
    COMPATIBLE = "COMPATIBLE"  # preserves compatibility


class ContractStatus(str, Enum):
    """Contract evolution status (CONTRACT_SPEC 'Evolution')."""
    COMPATIBLE = "COMPATIBLE"
    DEPRECATED = "DEPRECATED"
    REPLACED = "REPLACED"
    RETIRED = "RETIRED"
