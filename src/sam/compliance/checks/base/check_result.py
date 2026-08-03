"""CheckResult — immutable result of a compliance check execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class CheckResult:
    """Immutable result of executing a single compliance check.

    Deterministic: for the same CheckContext, the same check MUST
    produce the same CheckResult.
    """

    passed: bool
    """Whether the check passed (True) or failed (False)."""

    details: str = ""
    """Human-readable description of the result."""

    evidence: Dict[str, Any] = field(default_factory=dict)
    """Supporting evidence as key-value pairs (file paths, line numbers, etc.)."""

    @classmethod
    def success(
        cls, details: str = "", evidence: Dict[str, Any] = None
    ) -> "CheckResult":
        """Create a passing result."""
        return cls(passed=True, details=details, evidence=evidence or {})

    @classmethod
    def failure(
        cls, details: str = "", evidence: Dict[str, Any] = None
    ) -> "CheckResult":
        """Create a failing result."""
        return cls(passed=False, details=details, evidence=evidence or {})
