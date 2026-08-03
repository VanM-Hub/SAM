"""Contract Enforcer exception hierarchy.

Per CONTRACT_SPEC 'Failure Behaviour':
    - Unknown Contract
    - Unsupported Version
    - Invalid Contract
    - Malformed Payload
    - Missing Field
    - Incompatible Contract
"""

from typing import Optional


class ContractError(Exception):
    """Base exception for all contract-related errors."""
    pass


class InvalidContract(ContractError):
    """Contract is structurally invalid — malformed or missing required fields."""
    pass


class UnknownContract(ContractError):
    """Contract is not recognized in the system."""
    pass


class UnsupportedVersion(ContractError):
    """Requested Contract version is not supported."""
    pass


class IncompatibleContract(ContractError):
    """No mutually compatible Contract version exists."""
    pass


class NegotiationFailure(ContractError):
    """Version negotiation failed — no agreement reached."""
    pass


class MissingField(ContractError):
    """Required Contract field is absent."""
    pass


class EnforcerNotOperational(ContractError):
    """Contract Enforcer is not in RUNNING state."""
    pass
