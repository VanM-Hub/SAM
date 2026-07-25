"""Operational Guardrails — Sprint 32.

Guardrails prevent unsafe autonomous actions by defining rules
that must pass before execution.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()

DECISION_ALLOW = "allow"
DECISION_BLOCK = "block"
DECISION_WARN = "warn"
DECISION_ESCALATE = "escalate"


@dataclass
class GuardrailRule:
    """A single guardrail rule.

    Attributes:
        id: Unique rule ID.
        name: Human-readable name.
        description: What this guardrail checks.
        condition: Dict describing the condition (e.g. {"metric": "cpu_usage", "op": "<=", "value": 90}).
        on_violation: What to do: allow, block, warn, escalate.
        enabled: Whether this rule is active.
    """
    id: str = ""
    name: str = ""
    description: str = ""
    condition: Dict[str, Any] = field(default_factory=dict)
    on_violation: str = DECISION_BLOCK
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"gr_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "condition": self.condition,
            "on_violation": self.on_violation,
            "enabled": self.enabled,
        }


@dataclass
class GuardrailResult:
    """Result of evaluating a guardrail rule.

    Attributes:
        decision: allow, block, warn, escalate.
        violations: List of rule names that were violated.
        details: Explanation of what happened.
    """
    decision: str = DECISION_ALLOW
    violations: List[str] = field(default_factory=list)
    details: str = ""

    @property
    def is_safe(self) -> bool:
        return self.decision != DECISION_BLOCK


class Guardrails:
    """Manages and evaluates operational guardrails."""

    def __init__(self) -> None:
        self._rules: Dict[str, GuardrailRule] = {}
        self.logger = logger.bind(component="Guardrails")

    async def add_rule(self, rule: GuardrailRule) -> None:
        self._rules[rule.id] = rule

    async def remove_rule(self, rule_id: str) -> None:
        self._rules.pop(rule_id, None)

    async def get_active_guardrails(self) -> List[GuardrailRule]:
        return [r for r in self._rules.values() if r.enabled]

    async def evaluate(self, action: Dict[str, Any]) -> GuardrailResult:
        """Evaluate an action against all active guardrails.

        Args:
            action: Dict with metric values to check.

        Returns:
            GuardrailResult with the strictest decision.
        """
        violations = []
        strictest_decision = DECISION_ALLOW
        priority = {DECISION_ALLOW: 0, DECISION_WARN: 1, DECISION_ESCALATE: 2, DECISION_BLOCK: 3}

        for rule in self._rules.values():
            if not rule.enabled:
                continue
            if self._check_condition(rule.condition, action):
                continue  # Condition met = no violation

            # Condition not met = violation
            violations.append(rule.name)
            if priority.get(rule.on_violation, 0) > priority.get(strictest_decision, 0):
                strictest_decision = rule.on_violation

        decision = strictest_decision if violations else DECISION_ALLOW
        details = f"Violated {len(violations)} guardrails: {', '.join(violations)}" if violations else "All guardrails passed"

        return GuardrailResult(
            decision=decision,
            violations=violations,
            details=details,
        )

    async def count(self) -> int:
        return len(self._rules)

    async def clear(self) -> None:
        self._rules.clear()

    @staticmethod
    def _check_condition(condition: Dict[str, Any], action: Dict[str, Any]) -> bool:
        """Check if a condition is met by the action."""
        metric = condition.get("metric")
        op = condition.get("op", "<=")
        value = condition.get("value")

        if metric is None or metric not in action:
            return False

        actual = action[metric]
        try:
            if op == "<=":
                return actual <= value
            elif op == "<":
                return actual < value
            elif op == ">=":
                return actual >= value
            elif op == ">":
                return actual > value
            elif op == "==":
                return actual == value
            elif op == "!=":
                return actual != value
        except (TypeError, ValueError):
            return False
        return False
