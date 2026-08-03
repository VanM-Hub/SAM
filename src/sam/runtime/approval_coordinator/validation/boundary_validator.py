"""Boundary Validator — ensures access only through public API."""

from typing import List

# Authorized entry points per ADR-006
_AUTHORIZED_ENTRY_POINTS: List[str] = [
    "create_approval",
    "evaluate",
    "transition",
    "get",
    "get_health",
]


class BoundaryValidator:
    """Ensures access to Approval Coordinator only through public API.

    Per ADR-006: External access = Contracts + Registry only.
    For Approval Coordinator: public API = 5 methods.
    """

    @staticmethod
    def validate_entry_point(method_name: str) -> bool:
        """Check whether method_name is an authorized entry point.

        Returns True if authorized.
        Raises ValueError if not.
        """
        if method_name not in _AUTHORIZED_ENTRY_POINTS:
            raise ValueError(
                f"Unauthorized entry point: '{method_name}'. "
                f"Approval Coordinator only exposes: "
                f"{', '.join(_AUTHORIZED_ENTRY_POINTS)}"
            )
        return True

    @staticmethod
    def is_authorized(method_name: str) -> bool:
        """Non-raising check."""
        try:
            BoundaryValidator.validate_entry_point(method_name)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_authorized_entry_points() -> List[str]:
        """Return list of authorized entry points."""
        return list(_AUTHORIZED_ENTRY_POINTS)
