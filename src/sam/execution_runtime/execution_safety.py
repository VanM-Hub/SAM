"""Execution Safety (Sprint 257).

Program C - Real Execution Runtime.
Facade safety: gabungan policy + guard + rules. Menegakkan bahwa eksekusi
hanya berjalan bila aman (timeout, approval, provider, capability, retry).
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .execution_request import ExecutionRequest
from .execution_policy import ExecutionPolicy
from .execution_guard import ExecutionGuard, GuardDecision


@dataclass(frozen=True)
class SafetyVerdict:
    """Verdict keamanan (immutable)."""
    allowed: bool
    decision: GuardDecision
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {"allowed": self.allowed, "decision": self.decision.as_dict(),
                "external_calls": self.external_calls}


class ExecutionSafety:
    """Facade safety. Mencek semua batasan sebelum execute."""

    def __init__(self, policy: ExecutionPolicy | None = None,
                 guard: ExecutionGuard | None = None) -> None:
        self._policy = policy or ExecutionPolicy(policy_id="pol-safety")
        self._guard = guard or ExecutionGuard(self._policy)

    def assess(self, request: ExecutionRequest) -> SafetyVerdict:
        decision = self._guard.check(f"guard-{request.execution_id}", request)
        return SafetyVerdict(allowed=decision.allowed, decision=decision, external_calls=0)

    @property
    def policy(self) -> ExecutionPolicy:
        return self._policy
