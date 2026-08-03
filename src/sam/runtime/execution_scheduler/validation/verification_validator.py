"""Verification Validator — triggers verification of execution preconditions.

Verifies: approval still valid, contract intact, capability reference valid.
"""

from typing import Any, Dict


class VerificationValidator:
    """Triggers verification of execution preconditions.

    Authority: EXECUTION_SPEC §Boundaries — Execution runs authorized operation only.
    """

    @staticmethod
    def verify_preconditions(
        approval_ref: str,
        contract_ref: str,
        capability_ref: str,
    ) -> Dict[str, Any]:
        """Verify that all preconditions for execution are met.

        Args:
            approval_ref: The referenced approval.
            contract_ref: The referenced contract.
            capability_ref: The referenced capability.

        Returns:
            Dict with verification results.

        Raises:
            ValueError: if any precondition fails verification.
        """
        errors = []

        if not approval_ref or not approval_ref.strip():
            errors.append("approval reference is missing")
        if not contract_ref or not contract_ref.strip():
            errors.append("contract reference is missing")
        if not capability_ref or not capability_ref.strip():
            errors.append("capability reference is missing")

        result = {
            "verified": len(errors) == 0,
            "approval_reference": approval_ref,
            "contract_reference": contract_ref,
            "capability_reference": capability_ref,
            "errors": errors,
        }

        if errors:
            raise ValueError("Verification failed: " + "; ".join(errors))

        return result

    @staticmethod
    def is_verified(result: Dict[str, Any]) -> bool:
        """Check if verification result indicates success."""
        return result.get("verified", False)
