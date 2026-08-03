"""Contract Enforcer Unit — immutable Contracts, idempotency declaration,
version negotiation, compatibility verification.

Authority: R5-001 §2.4 | I0-001 §2.4 | CONTRACT_SPEC | ADR-003
"""

from sam.runtime.contract_enforcer.models.contract_model import Contract
from sam.runtime.contract_enforcer.models.compatibility_result import (
    CompatibilityResult,
    CompatibilityStatus,
)
from sam.runtime.contract_enforcer.models.negotiation_result import (
    NegotiationResult,
    NegotiationStatus,
)
from sam.runtime.contract_enforcer.interfaces.enforcer_interface import (
    ContractEnforcerInterface,
)
from sam.runtime.contract_enforcer.services.enforcer_service import (
    ContractEnforcer,
)
from sam.runtime.contract_enforcer.lifecycle.enforcer_lifecycle import (
    ContractEnforcerLifecycle,
    ContractEnforcerLifecycleState,
)
from sam.runtime.contract_enforcer.exceptions.contract_errors import (
    ContractError,
    InvalidContract,
    UnknownContract,
    UnsupportedVersion,
    IncompatibleContract,
    NegotiationFailure,
    MissingField,
    EnforcerNotOperational,
)

__all__ = [
    # Models
    "Contract",
    "CompatibilityResult",
    "CompatibilityStatus",
    "NegotiationResult",
    "NegotiationStatus",
    # Interface
    "ContractEnforcerInterface",
    # Service
    "ContractEnforcer",
    # Lifecycle
    "ContractEnforcerLifecycle",
    "ContractEnforcerLifecycleState",
    # Exceptions
    "ContractError",
    "InvalidContract",
    "UnknownContract",
    "UnsupportedVersion",
    "IncompatibleContract",
    "NegotiationFailure",
    "MissingField",
    "EnforcerNotOperational",
]
