"""CompatibilityValidator — validates compatibility between Contract versions.

Per CONTRACT_SPEC 'Compatibility Rules':
    - Backward compatible: older consumer works with newer
    - Forward compatible: newer consumer works with older
    - Breaking change: breaks backward or forward
    - Compatible change: preserves compatibility
    - Deprecated contract: still defined but not preferred
"""

from typing import List

from sam.runtime.contract_enforcer.models.contract_model import Contract
from sam.runtime.contract_enforcer.models.compatibility_result import (
    CompatibilityResult,
    CompatibilityStatus,
)


class CompatibilityValidator:
    """Validates compatibility between two Contract versions."""

    def verify(
        self,
        contract: Contract,
        predecessor: Contract,
    ) -> CompatibilityResult:
        """Verify compatibility between a Contract and its predecessor.

        Checks:
        1. Same contract_id → valid comparison
        2. Different contract_id → unknown
        3. Contract's own compatibility declaration
        4. Input/output schema structural comparison

        Args:
            contract: The newer Contract version.
            predecessor: The older Contract version.

        Returns:
            CompatibilityResult with status and details.
        """
        # Must be same contract
        if contract.contract_id != predecessor.contract_id:
            return CompatibilityResult.unknown(
                f"Cannot compare different contracts: "
                f"'{contract.contract_id}' vs '{predecessor.contract_id}'"
            )

        # Check declared compatibility
        declared = contract.compatibility
        backward = declared.get("backward", True)
        forward = declared.get("forward", True)
        breaking = declared.get("breaking_changes", [])

        if not backward or not forward:
            return CompatibilityResult.breaking(
                changes=list(breaking) if breaking else ["Unknown breaking change"],
                predecessor_id=predecessor.contract_id,
                successor_id=contract.contract_id,
            )

        # Check for input/output schema changes that could be breaking
        structural_issues = self._check_structural_compatibility(
            contract, predecessor
        )

        if structural_issues:
            return CompatibilityResult.breaking(
                changes=structural_issues,
                predecessor_id=predecessor.contract_id,
                successor_id=contract.contract_id,
            )

        return CompatibilityResult.compatible(
            predecessor_id=predecessor.contract_id,
            successor_id=contract.contract_id,
        )

    @staticmethod
    def _check_structural_compatibility(
        new: Contract, old: Contract
    ) -> List[str]:
        """Check for structural breaking changes between versions."""
        issues: List[str] = []

        # Input schema: new required fields that weren't in old = breaking
        old_input_keys = set(old.input_schema.keys())
        new_input_keys = set(new.input_schema.keys())

        removed_inputs = old_input_keys - new_input_keys
        if removed_inputs:
            issues.append(
                f"Removed input fields: {', '.join(sorted(removed_inputs))}"
            )

        # Output schema: missing outputs that were in old = breaking
        old_output_keys = set(old.output_schema.keys())
        new_output_keys = set(new.output_schema.keys())

        removed_outputs = old_output_keys - new_output_keys
        if removed_outputs:
            issues.append(
                f"Removed output fields: {', '.join(sorted(removed_outputs))}"
            )

        return issues
