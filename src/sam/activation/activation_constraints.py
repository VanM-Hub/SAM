"""Activation Constraints — batasan aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConstraintResult:
    constraint_id: str = ""
    name: str = ""
    passed: bool = False
    reason: str = ""


class ActivationConstraints:
    """Constraint checker untuk aktivasi."""

    def check_environment(self, env: str) -> ConstraintResult:
        valid = env in ("normal", "busy", "idle", "emergency")
        return ConstraintResult(
            "env_check", "Environment Valid",
            valid, f"Environment {env} {'valid' if valid else 'invalid'}"
        )

    def check_candidates_min(self, count: int, minimum: int = 1) -> ConstraintResult:
        ok = count >= minimum
        return ConstraintResult(
            "min_candidates", "Minimum Candidates",
            ok, f"Candidates {count} >= {minimum}: {ok}"
        )

    def check_confidence(self, candidates: List[Any]) -> ConstraintResult:
        if not candidates:
            return ConstraintResult("confidence", "Confidence Check", False, "No candidates")
        avg = sum(c.confidence for c in candidates) / len(candidates)
        ok = avg >= 0.1
        return ConstraintResult(
            "confidence", "Confidence Threshold",
            ok, f"Avg confidence {avg:.2f} >= 0.1: {ok}"
        )

    def check_all(self, env: str, candidate_count: int,
                  candidates: List[Any]) -> List[ConstraintResult]:
        return [
            self.check_environment(env),
            self.check_candidates_min(candidate_count),
            self.check_confidence(candidates),
        ]
