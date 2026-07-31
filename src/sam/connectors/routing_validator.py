"""Routing Validator — engine validasi routing.

Sprint 117 — Connector Routing.
Validasi kebijakan & hasil routing (read-only).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_router import RoutingPolicy


@dataclass(frozen=True)
class RoutingValidationReport:
    policy_id: str
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class RoutingValidator:
    """Validasi kebijakan routing."""

    def validate(self, policy: RoutingPolicy) -> RoutingValidationReport:
        issues = []
        if policy.strategy not in ("capability", "round_robin", "first"):
            issues.append(f"unknown strategy: {policy.strategy}")
        return RoutingValidationReport(policy.policy_id, not issues, issues)
