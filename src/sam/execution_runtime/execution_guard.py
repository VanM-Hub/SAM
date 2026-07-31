"""Execution Guard (Sprint 257).

Program C - Real Execution Runtime.
Guard yang merangkum hasil safety check dan mencegah eksekusi tidak aman.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .execution_request import ExecutionRequest
from .execution_policy import ExecutionPolicy
from .execution_limits import ExecutionLimits
from .execution_rules import ExecutionRules, RuleEvaluation


@dataclass(frozen=True)
class GuardDecision:
    """Keputusan guard (immutable)."""
    guard_id: str
    execution_id: str
    allowed: bool
    limits: ExecutionLimits
    rules: tuple = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"guard_id": self.guard_id, "execution_id": self.execution_id,
                "allowed": self.allowed, "limits": self.limits.as_dict(),
                "rules": [r.as_dict() for r in self.rules]}


class ExecutionGuard:
    """Guard safety. Cek timeout/approval/provider/capability/retry."""

    def __init__(self, policy: ExecutionPolicy | None = None,
                 rules: ExecutionRules | None = None) -> None:
        self._policy = policy or ExecutionPolicy(policy_id="pol-main")
        self._rules = rules or ExecutionRules()

    def check(self, guard_id: str, request: ExecutionRequest) -> GuardDecision:
        rule_results = self._rules.evaluate(request, self._policy)
        approved = (request.mode != "execute") or request.approved
        allowed = all(r.passed for r in rule_results) and approved
        limits = ExecutionLimits(
            limits_id=f"lim-{guard_id}",
            execution_id=request.execution_id,
            within_timeout=next(r.passed for r in rule_results if r.rule == "timeout"),
            within_retry_limit=next(r.passed for r in rule_results if r.rule == "retry_limit"),
            provider_allowed=next(r.passed for r in rule_results if r.rule == "provider_available"),
            capability_ok=next(r.passed for r in rule_results if r.rule == "capability"),
            approved=approved,
        )
        return GuardDecision(guard_id=guard_id, execution_id=request.execution_id,
                             allowed=allowed, limits=limits, rules=tuple(rule_results))
