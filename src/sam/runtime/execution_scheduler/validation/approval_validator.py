"""Approval Validator — ensures execution only proceeds when Approval = Approved.

Authority: EXECUTION_SPEC §Boundaries — Execution runs authorized operations only.
Per I6 invariant: Execution performs only after approval.
"""

from typing import Any


class ApprovalValidator:
    """Validates that an approval reference is in Approved state."""

    # Authorized entry points for public consumption
    AUTHORIZED_METHODS = frozenset({
        "create_execution",
        "schedule",
        "transition",
        "verify",
        "get",
        "get_health",
        "initialize",
        "shutdown",
    })

    @staticmethod
    def validate_approved(approval_state: Any) -> bool:
        """Check if approval state represents Approved.

        Args:
            approval_state: The approval state/decision to check.

        Returns:
            True if the approval is in Approved state.
        """
        if approval_state is None:
            return False
        state_str = str(approval_state).upper()
        return state_str == "APPROVED"

    @staticmethod
    def validate_approval_reference(approval_ref: str) -> bool:
        """Validate approval reference is non-empty.

        Args:
            approval_ref: The approval reference string.

        Returns:
            True if valid.

        Raises:
            ValueError: if reference is empty.
        """
        if not approval_ref or not approval_ref.strip():
            raise ValueError("approval_reference must not be empty")
        return True
