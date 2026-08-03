"""Decision Validator — validates ApprovalDecision per ADR-001."""

from src.sam.runtime.approval_coordinator.models.approval_decision import (
    ApprovalDecision,
    ApprovalDecisionState,
)
from src.sam.runtime.approval_coordinator.exceptions.approval_errors import (
    InvalidRequestError,
)


class DecisionValidator:
    """Validates ApprovalDecision integrity.

    Per ADR-001:
    - Must be one of 6 recognized states (deterministic output shape)
    - Decision reason must be present (explainable)
    - Decision must reference a valid approval_id
    """

    @staticmethod
    def validate(decision: ApprovalDecision) -> bool:
        """Validate decision integrity.

        Returns True if valid.
        Raises InvalidRequestError if invalid.
        """
        if not isinstance(decision.state, ApprovalDecisionState):
            raise InvalidRequestError(
                f"Invalid decision state: {decision.state}"
            )

        if not decision.decision_reason.strip():
            raise InvalidRequestError(
                "Decision must have a non-empty reason "
                "(ADR-001 explainability)"
            )

        if not decision.approval_id.strip():
            raise InvalidRequestError(
                "Decision must reference a valid approval_id"
            )

        if not decision.decided_by.strip():
            raise InvalidRequestError(
                "Decision must record who/what made the decision"
            )

        return True

    @staticmethod
    def is_valid(decision: ApprovalDecision) -> bool:
        """Non-raising check — returns True/False."""
        try:
            DecisionValidator.validate(decision)
            return True
        except InvalidRequestError:
            return False
