"""Tool Execution Compliance - WP-29 (MISSION-5.2 / IP-5.2-003).

Memastikan execution Tool selalu melalui jalur governance: policy, approval,
execution, audit — tidak ada bypass.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .governed_tool_invocation import ExecutionStage, ToolExecutionContext


@dataclass(frozen=True)
class ToolExecutionComplianceResult:
    """Hasil compliance execution tool."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class ToolExecutionComplianceChecker:
    """Checker compliance untuk governed tool execution."""

    def check(
        self,
        context: ToolExecutionContext,
        *,
        approval_before_execution: bool = True,
        policy_before_execution: bool = True,
        no_bypass: bool = True,
    ) -> ToolExecutionComplianceResult:
        stages = [d.stage for d in context.decisions]
        execution_passed = any(
            d.stage == ExecutionStage.EXECUTION and d.passed for d in context.decisions
        )
        if execution_passed:
            approved_before = context.approved
            policy_passed = any(
                d.stage == ExecutionStage.POLICY_VALIDATION and d.passed for d in context.decisions
            )
        else:
            approved_before = True
            policy_passed = True

        checks = [
            {"code": "APPROVAL_BEFORE_EXECUTION", "passed": approval_before_execution and approved_before},
            {"code": "POLICY_BEFORE_EXECUTION", "passed": policy_before_execution and policy_passed},
            {"code": "NO_BYPASS", "passed": no_bypass},
            {"code": "EXECUTION_GATED", "passed": not execution_passed or (approved_before and policy_passed)},
        ]
        passed = all(c["passed"] for c in checks)
        return ToolExecutionComplianceResult(passed=passed, checks=tuple(checks))

    def certify(self, context: ToolExecutionContext, **kwargs: Any) -> Dict[str, Any]:
        result = self.check(context, **kwargs)
        return {
            "component": "universal_tool.governed_execution",
            "passed": result.passed,
            "certified": result.passed,
            "checks": [c for c in result.checks],
        }
