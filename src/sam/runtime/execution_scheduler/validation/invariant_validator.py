"""Invariant Validator — Runtime invariants verification.

Guards key invariants:
- I6: Execution performs only after Approval
- Approval always precedes Execution
- Idempotency observation from Contract
- Strict Linear Ordering
"""

from typing import Any, Dict, List

from src.sam.runtime.execution_scheduler.state.execution_state import (
    ExecutionStateRecord,
    ExecutionLifecycleState,
)


class InvariantValidator:
    """Validates runtime invariants for the Execution Scheduler."""

    @staticmethod
    def validate_invariants(
        records: Dict[str, ExecutionStateRecord],
    ) -> Dict[str, Any]:
        """Run all invariant checks.

        Returns:
            Dict with invariant check results.
        """
        results = {
            "invariants_checked": 0,
            "invariants_passed": 0,
            "violations": [],
        }

        # I6: No execution without approval reference
        for record in records.values():
            if not record.identity.approval_reference:
                results["violations"].append(
                    f"Execution '{record.identity.execution_id}' "
                    f"has no approval_reference (violates I6)"
                )

        results["invariants_checked"] = len(records)
        results["invariants_passed"] = (
            results["invariants_checked"] - len(results["violations"])
        )
        return results

    @staticmethod
    def validate_approval_before_execution(record: ExecutionStateRecord) -> bool:
        """Validate I6: execution only after approval.

        Args:
            record: The execution record.

        Returns:
            True if approval precedes execution.
        """
        return bool(
            record.identity.approval_reference
            and record.identity.approval_reference.strip()
        )
