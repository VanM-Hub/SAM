"""State Validator — validasi transisi state."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.runtime_state import StateValidation


class StateValidator:
    """Validator state — preview-only."""

    VALID_STATES = ["initial", "booting", "ready", "active", "suspended", "failed", "shutdown"]

    def validate(self, validation_id: str, state: str) -> StateValidation:
        errors: List[str] = []
        if state not in self.VALID_STATES:
            errors.append(f"Invalid state: {state}")
        return StateValidation(
            validation_id=validation_id,
            valid=len(errors) == 0,
            errors=errors,
        )

    def is_valid(self, state: str) -> bool:
        return state in self.VALID_STATES
