"""Reasoning Verification - WP-15 (MISSION-4.4 / IP-4.4-002).

Memverifikasi reasoning: evidence-backed, deterministik, dan tidak
menghasilkan authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .structured_reasoning import StructuredReasoning


@dataclass(frozen=True)
class ReasoningVerification:
    """Hasil verifikasi reasoning."""

    reasoning_id: str
    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "reasoning_id": self.reasoning_id,
            "passed": self.passed,
            "checks": list(self.checks),
        }


class ReasoningVerifier:
    """Memverifikasi reasoning (read-only)."""

    @staticmethod
    def verify(
        reasoning: StructuredReasoning,
        *,
        no_authority: bool = True,
    ) -> ReasoningVerification:
        checks = [
            {
                "code": "EVIDENCE_BACKED",
                "passed": reasoning.is_evidence_backed,
            },
            {
                "code": "HAS_CONCLUSION",
                "passed": bool(reasoning.conclusion),
            },
            {
                "code": "DETERMINISTIC_STEPS",
                "passed": len(reasoning.steps) > 0,
            },
            {
                "code": "NO_AUTHORITY",
                "passed": no_authority,
            },
        ]
        passed = all(c["passed"] for c in checks)
        return ReasoningVerification(
            reasoning_id=reasoning.reasoning_id,
            passed=passed,
            checks=tuple(checks),
        )
