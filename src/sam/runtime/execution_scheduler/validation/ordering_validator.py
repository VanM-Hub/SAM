"""Ordering Validator — ADR-005 Strict Linear Ordering.

Approval-arrival order = Execution order.
No bypass, no parallel reorder.
One operation reaches terminal state before next begins.
"""

from typing import List

from src.sam.runtime.execution_scheduler.state.execution_state import (
    ExecutionStateRecord,
    ExecutionLifecycleState,
    is_result_state,
)


class OrderingValidator:
    """Enforces ADR-005 Strict Linear Ordering.

    Approval-arrival is tracked via sequence numbers.
    The execution with the lowest sequence number that is not
    yet at a result state must proceed first.
    """

    @staticmethod
    def validate_order(
        record: ExecutionStateRecord,
        all_records: List[ExecutionStateRecord],
    ) -> bool:
        """Validate that this execution can proceed in order.

        Checks that no execution with a lower sequence number
        is ahead and not yet at a result state.

        Args:
            record: The execution to validate.
            all_records: All known executions.

        Returns:
            True if ordering is correct.

        Raises:
            ValueError: if ordering constraint is violated.
        """
        my_seq = record.sequence_number
        for other in all_records:
            if other.identity.execution_id == record.identity.execution_id:
                continue
            if other.sequence_number < my_seq:
                if not is_result_state(other.lifecycle_state):
                    raise ValueError(
                        f"Ordering violation: execution "
                        f"'{record.identity.execution_id}' (seq={my_seq}) "
                        f"cannot proceed before "
                        f"'{other.identity.execution_id}' (seq={other.sequence_number}) "
                        f"which is in state {other.lifecycle_state.value}"
                    )
        return True

    @staticmethod
    def get_next_sequence(existing_records: List[ExecutionStateRecord]) -> int:
        """Compute the next sequence number based on existing records.

        Sequence numbers start at 1 and increment monotonically.
        """
        if not existing_records:
            return 1
        return max(r.sequence_number for r in existing_records) + 1
