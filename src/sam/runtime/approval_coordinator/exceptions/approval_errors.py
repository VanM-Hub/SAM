"""Approval Coordinator exceptions.

Defined failures per APPROVAL_SPEC 'Failure Behaviour':
- Missing Contract: the referenced Contract is absent
- Unknown Capability: the referenced Capability is not recognized
- Registry Resolution Failed: the Capability could not be resolved
- Invalid Request: the Approval Request is malformed
- Expired Request: the Approval Request is no longer valid
- Approval Conflict: an Approval State contradicts the requested operation
"""


class ApprovalError(Exception):
    """Base exception for all approval-related failures."""
    pass


class MissingContractError(ApprovalError):
    """The referenced Contract is absent."""
    pass


class UnknownCapabilityError(ApprovalError):
    """The referenced Capability is not recognized."""
    pass


class RegistryResolutionError(ApprovalError):
    """The Capability could not be resolved."""
    pass


class InvalidRequestError(ApprovalError):
    """The Approval Request is malformed."""
    pass


class ExpiredRequestError(ApprovalError):
    """The Approval Request is no longer valid."""
    pass


class ApprovalConflictError(ApprovalError):
    """An Approval State contradicts the requested operation."""
    pass


class InvalidTransitionError(ApprovalError):
    """An illegal lifecycle state transition was attempted."""
    pass


class ApprovalNotFoundError(ApprovalError):
    """The referenced Approval does not exist."""
    pass


class CoordinatorNotOperationalError(ApprovalError):
    """The Approval Coordinator is not in an operational state."""
    pass
