"""Execution Rules (Sprint 257).

Program C - Real Execution Runtime.
Kumpulan aturan safety yang dapat dievaluasi per-request (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .execution_request import ExecutionRequest
from .execution_policy import ExecutionPolicy
from .execution_limits import ExecutionLimits


@dataclass(frozen=True)
class RuleEvaluation:
    """Hasil evaluasi satu aturan (immutable)."""
    rule: str
    passed: bool
    message: str = ""

    def as_dict(self) -> dict:
        return {"rule": self.rule, "passed": self.passed, "message": self.message}


class ExecutionRules:
    """Aturan safety. Evaluasi statis, deterministic."""

    def evaluate(self, request: ExecutionRequest, policy: ExecutionPolicy) -> List[RuleEvaluation]:
        results = []
        results.append(RuleEvaluation(
            "timeout", request.timeout_seconds <= policy.max_timeout_seconds,
            f"timeout {request.timeout_seconds}" if request.timeout_seconds > policy.max_timeout_seconds else ""))
        results.append(RuleEvaluation(
            "retry_limit", request.max_retries <= policy.max_retries,
            "retry too high" if request.max_retries > policy.max_retries else ""))
        results.append(RuleEvaluation(
            "approval", (not policy.require_approval) or (request.mode != "execute") or request.approved,
            "approval required" if request.mode == "execute" and not request.approved else ""))
        results.append(RuleEvaluation(
            "provider_available", policy.allows_provider(request.provider_id),
            "provider not allowed" if not policy.allows_provider(request.provider_id) else ""))
        results.append(RuleEvaluation(
            "capability", request.operation != "",
            "operation required" if request.operation == "" else ""))
        return results

    def all_pass(self, request: ExecutionRequest, policy: ExecutionPolicy) -> bool:
        return all(r.passed for r in self.evaluate(request, policy))
