"""Idempotency Validator — ADR-003 Operation-Defined Semantics.

Contract declares idempotency; Execution observes.
- IDEMPOTENT: repeated execution allowed
- NON_IDEMPOTENT: repeated execution → Execution Conflict

Observation via lifecycle state + Contract reference:
"Has an identical (approval + contract + capability) already Completed?"
"""

from typing import Dict, List

from src.sam.runtime.contracts import ContractIdentity, ContractIdempotency
from src.sam.runtime.execution_scheduler.state.execution_state import (
    ExecutionStateRecord,
    ExecutionLifecycleState,
)


class IdempotencyValidator:
    """Observes idempotency declarations from Contract (ADR-003).

    Execution Scheduler does NOT define idempotency.
    It reads declarations and enforces behavioral rules.
    """

    @staticmethod
    def observe_idempotency(
        contract_idempotency: ContractIdempotency,
    ) -> bool:
        """Observe the idempotency declaration.

        Returns:
            True if the contract declares IDEMPOTENT.
        """
        return contract_idempotency == ContractIdempotency.IDEMPOTENT

    @staticmethod
    def check_repeat_allowed(
        approval_ref: str,
        contract_ref: str,
        capability_ref: str,
        records: Dict[str, ExecutionStateRecord],
        contract_idempotency: ContractIdempotency,
    ) -> bool:
        """Check if re-creating this execution is allowed.

        Algorithm per ADR-003 Alt B:
        1. Find if identical (approval + contract + capability) already Completed.
        2. If yes and IDEMPOTENT → repeat allowed.
        3. If yes and NON_IDEMPOTENT → repeat NOT allowed → ExecutionConflict.
        4. If not found → new execution, always allowed.

        Args:
            approval_ref: Approval reference.
            contract_ref: Contract reference.
            capability_ref: Capability reference.
            records: All existing execution records.
            contract_idempotency: The contract's idempotency declaration.

        Returns:
            True if repeat is allowed or this is a new operation.

        Raises:
            ValueError: if repeat is not allowed (non-idempotent conflict).
        """
        # Check if any existing execution has the same identity triple
        # and has already reached a Completed state.
        for record in records.values():
            if (
                record.identity.approval_reference == approval_ref
                and record.identity.contract_reference == contract_ref
                and record.identity.capability_reference == capability_ref
                and record.lifecycle_state == ExecutionLifecycleState.COMPLETED
            ):
                if contract_idempotency == ContractIdempotency.IDEMPOTENT:
                    return True
                else:
                    raise ValueError(
                        f"Execution conflict: operation "
                        f"(approval='{approval_ref}', "
                        f"contract='{contract_ref}', "
                        f"capability='{capability_ref}') "
                        f"has already Completed and is NON_IDEMPOTENT"
                    )
        # No prior Completed execution found → new operation, always allowed
        return True

    @staticmethod
    def is_idempotent_declaration_valid(declaration: str) -> bool:
        """Check if an idempotency declaration string is valid.

        Valid values: 'IDEMPOTENT', 'NON_IDEMPOTENT'
        """
        return declaration in {
            ContractIdempotency.IDEMPOTENT.value,
            ContractIdempotency.NON_IDEMPOTENT.value,
        }
