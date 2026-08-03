"""CompositeComplianceCheck — combines multiple checks using AND/OR logic."""

from __future__ import annotations

from enum import Enum
from typing import List

from .base_check import BaseComplianceCheck
from .check_context import CheckContext
from .check_result import CheckResult


class CompositeMode(Enum):
    """Combination strategy for composite checks."""

    ALL = "ALL"
    """AND — all sub-checks must pass."""

    ANY = "ANY"
    """OR — at least one sub-check must pass."""


class CompositeComplianceCheck(BaseComplianceCheck):
    """Combines multiple checks into a single composite check.

    Each sub-check receives the same CheckContext (with check_id
    overridden to the sub-check's own id). The composite result
    is computed per the CompositeMode.

    Deterministic: sub-checks must be deterministic.
    Stateless: delegates all state to sub-checks.
    Composable: sub-checks can themselves be composites.
    """

    def __init__(
        self,
        checks: List[BaseComplianceCheck],
        mode: CompositeMode = CompositeMode.ALL,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._checks = list(checks)
        self._mode = mode

    @property
    def checks(self) -> List[BaseComplianceCheck]:
        """Return a copy of the sub-check list."""
        return list(self._checks)

    @property
    def mode(self) -> CompositeMode:
        return self._mode

    def execute(self, context: CheckContext) -> CheckResult:
        """Execute all sub-checks and combine results per mode.

        ALL mode: all sub-checks must pass (AND).
        ANY mode: at least one sub-check must pass (OR).
        """
        sub_results = []
        sub_evidences = []

        for check in self._checks:
            sub_ctx = CheckContext(
                target_path=context.target_path,
                options=context.options,
                check_id=check.check_id,
            )
            result = check.execute(sub_ctx)
            sub_results.append(result)
            sub_evidences.append(
                {
                    "check_id": check.check_id,
                    "passed": result.passed,
                    "details": result.details,
                    "evidence": result.evidence,
                }
            )

        if self._mode == CompositeMode.ALL:
            passed = all(r.passed for r in sub_results)
        else:
            passed = any(r.passed for r in sub_results)

        parts = []
        for sr in sub_results:
            parts.append(
                "[%s] %s: %s"
                % ("PASS" if sr.passed else "FAIL", sr.details, "")
            )

        return CheckResult(
            passed=passed,
            details="; ".join(parts),
            evidence={"sub_results": sub_evidences, "mode": self._mode.value},
        )

    def to_config(self) -> dict:
        """Serialize composite check to configuration."""
        config = super().to_config()
        config["mode"] = self._mode.value
        config["checks"] = [c.to_config() for c in self._checks]
        return config
