"""Request Validator — validates ApprovalRequest against APPROVAL_SPEC."""

from src.sam.runtime.approval_coordinator.models.approval_request import (
    ApprovalRequest,
)
from src.sam.runtime.approval_coordinator.exceptions.approval_errors import (
    InvalidRequestError,
    ExpiredRequestError,
)


class RequestValidator:
    """Validates ApprovalRequest fields against APPROVAL_SPEC requirements.

    Checks:
    - Non-empty decision_context
    - Valid contract_reference
    - Non-empty capability_reference
    - Non-empty requested_by
    - Not expired (if expires_at is set)
    """

    @staticmethod
    def validate(request: ApprovalRequest) -> bool:
        """Validate the request.

        Returns True if valid.
        Raises InvalidRequestError or ExpiredRequestError if invalid.
        """
        if not request.decision_context.strip():
            raise InvalidRequestError(
                "Approval request has empty decision_context"
            )

        if not request.capability_reference.strip():
            raise InvalidRequestError(
                "Approval request has empty capability_reference"
            )

        if not request.requested_by.strip():
            raise InvalidRequestError(
                "Approval request has empty requested_by"
            )

        if not request.contract_reference.validate():
            raise InvalidRequestError(
                "Approval request has invalid contract_reference"
            )

        # Check expiry
        if request.is_expired():
            raise ExpiredRequestError(
                f"Approval request for "
                f"'{request.capability_reference}' has expired"
            )

        return True

    @staticmethod
    def is_valid(request: ApprovalRequest) -> bool:
        """Non-raising check — returns True/False."""
        try:
            RequestValidator.validate(request)
            return True
        except (InvalidRequestError, ExpiredRequestError):
            return False
