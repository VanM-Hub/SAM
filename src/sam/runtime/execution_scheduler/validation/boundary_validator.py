"""Boundary Validator — ADR-006 external access enforcement.

Validates that only authorized entry points are consumed.
Implements: Contracts + Registry only for external access.
"""

from typing import FrozenSet


class BoundaryValidator:
    """Enforces external access boundaries per ADR-006.

    Only authorized entry points are consumable from outside the unit.
    Internal methods are not accessible through public contract.
    """

    # Authorized public entry points
    AUTHORIZED_ENTRY_POINTS: FrozenSet[str] = frozenset({
        "create_execution",
        "schedule",
        "transition",
        "verify",
        "get",
        "get_health",
    })

    @classmethod
    def is_authorized(cls, method_name: str) -> bool:
        """Check if a method is part of the public API.

        Args:
            method_name: Name of the method to check.

        Returns:
            True if the method is authorized.
        """
        return method_name in cls.AUTHORIZED_ENTRY_POINTS

    @classmethod
    def validate_authorized(cls, method_name: str) -> None:
        """Validate that a method is authorized.

        Args:
            method_name: Name of the method to validate.

        Raises:
            ValueError: if the method is not authorized.
        """
        if not cls.is_authorized(method_name):
            raise ValueError(
                f"Method '{method_name}' is not an authorized "
                f"entry point for Execution Scheduler"
            )

    @classmethod
    def get_authorized_entry_points(cls) -> FrozenSet[str]:
        """Return the set of authorized entry points."""
        return cls.AUTHORIZED_ENTRY_POINTS
