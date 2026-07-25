"""
Decision Node Model – Sprint 23 Fase 2

Enables conditional branching in an ExecutionGraph. A DecisionNode
evaluates a set of DecisionConditions against a collected evidence
dict and returns the next node ID to branch to.

Supports five condition types:

- IF_EVIDENCE:    Check a key in evidence dict
- IF_STATUS:      Check a node's status (COMPLETED, FAILED, etc.)
- IF_CAPABILITY:  Check a capability's health/status
- IF_TIMEOUT:     Check if execution time exceeds threshold
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator, ConfigDict


# ── Decision Types ───────────────────────────────────────────────────


class DecisionType(str, Enum):
    """The kind of condition to evaluate."""

    IF_EVIDENCE = "IF_EVIDENCE"
    IF_STATUS = "IF_STATUS"
    IF_CAPABILITY = "IF_CAPABILITY"
    IF_TIMEOUT = "IF_TIMEOUT"


# ── Operators ────────────────────────────────────────────────────────


OPERATORS = frozenset({
    "==", "!=", ">", "<", ">=", "<=",
    "contains", "starts_with",
})


# ── Decision Condition ────────────────────────────────────────────────


class DecisionCondition(BaseModel):
    """A single condition that determines branching.

    Attributes:
        type: Which kind of evidence/status/capability/timeout to check.
        key: The key to look up (e.g. ``evidence.status``, ``node.result``).
        operator: Comparison operator (==, !=, >, <, >=, <=, contains, starts_with).
        value: The value to compare against. Can be any comparable type.
    """

    model_config = ConfigDict(extra="forbid")

    type: DecisionType = Field(description="Condition type")
    key: str = Field(description="Key to look up in evidence/status")
    operator: str = Field(default="==", description="Comparison operator")
    value: Any = Field(description="Value to compare against")

    @model_validator(mode="after")
    def _validate_operator(self) -> "DecisionCondition":
        if self.operator not in OPERATORS:
            raise ValueError(
                f"Invalid operator '{self.operator}'. "
                f"Must be one of: {', '.join(sorted(OPERATORS))}"
            )
        return self

    def evaluate(self, evidence: Dict[str, Any]) -> bool:
        """Evaluate this condition against the given evidence dict.

        Args:
            evidence: A flat dict of key→value pairs (may include
                      dotted keys like ``node.check_health.outcome``).

        Returns:
            True if the condition matches; False otherwise.
        """
        actual = self._resolve_key(evidence)
        return self._compare(actual)

    def _resolve_key(self, evidence: Dict[str, Any]) -> Any:
        """Resolve ``key`` from evidence, supporting dotted paths."""
        parts = self.key.split(".")
        cur: Any = evidence
        for part in parts:
            if isinstance(cur, dict):
                cur = cur.get(part, _MISSING)
            else:
                return _MISSING
        return cur

    def _compare(self, actual: Any) -> bool:
        """Perform the actual comparison."""
        op = self.operator
        val = self.value

        # If the actual value is MISSING, only == and != make sense
        if actual is _MISSING:
            return op == "!=" and val is not None

        try:
            # Normalize enums to their value
            if hasattr(actual, "value"):
                actual = actual.value
            if hasattr(val, "value"):
                val = val.value

            # Try numeric comparison when both look like numbers
            if op in {">", "<", ">=", "<="}:
                try:
                    a = float(actual)
                    b = float(val)
                    if op == ">":
                        return a > b
                    if op == "<":
                        return a < b
                    if op == ">=":
                        return a >= b
                    if op == "<=":
                        return a <= b
                except Exception:
                    # Fall back to generic comparison
                    pass

            if op == "==":
                return actual == val
            elif op == "!=":
                return actual != val
            elif op == "contains":
                return self._contains(actual, val)
            elif op == "starts_with":
                return self._starts_with(actual, val)
            else:
                return False
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _contains(actual: Any, val: Any) -> bool:
        if isinstance(actual, str) and isinstance(val, str):
            return val in actual
        if isinstance(actual, (list, tuple)):
            return val in actual
        if isinstance(actual, dict):
            return val in actual or val in actual.values()
        return False

    @staticmethod
    def _starts_with(actual: Any, val: Any) -> bool:
        if isinstance(actual, str) and isinstance(val, str):
            return actual.startswith(val)
        return False


# Sentinel for missing keys
_MISSING = object()


# ── Decision Node ──────────────────────────────────────────────────────


class DecisionNode(BaseModel):
    """A decision node that evaluates conditions and branches.

    This model exists separately from ExecutionNode to keep decision
    logic focused. The ExecutionNode that is a decision point has
    ``is_decision=True`` plus a ``decision_id`` that links to this
    DecisionNode instance.

    Attributes:
        id: Unique decision node identifier.
        conditions: Ordered list of DecisionConditions to evaluate.
        branch_targets: Mapping from condition index (str) to node ID.
            The first matching condition triggers its branch target.
        default_target: Fallback node ID if no condition matches.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Unique decision identifier")
    conditions: List[DecisionCondition] = Field(
        default_factory=list,
        description="Ordered list of conditions to evaluate",
    )
    branch_targets: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping: condition_index (str) → target node ID",
    )
    default_target: Optional[str] = Field(
        default=None,
        description="Fallback target if no condition matches",
    )

    def evaluate(self, evidence: Dict[str, Any]) -> Optional[str]:
        """Evaluate conditions against evidence and return the target node ID.

        Args:
            evidence: Collected execution evidence dict.

        Returns:
            The target node ID from the first matching condition,
            ``default_target`` if no condition matches,
            or ``None`` if neither matches nor default is set.
        """
        for idx, cond in enumerate(self.conditions):
            if cond.evaluate(evidence):
                target_idx = str(idx)
                if target_idx in self.branch_targets:
                    return self.branch_targets[target_idx]
        return self.default_target
