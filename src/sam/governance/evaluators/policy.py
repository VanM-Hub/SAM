"""
Policy Evaluator – Sprint 21 Fase 2

Evaluates custom governance rules against the execution graph.
Rules are loaded from the governance_rules table or injected callables.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Callable, List, Dict, Any

from ..evaluator import BaseEvaluator
from ..models import GovernanceDecision, GovernanceResult, GovernanceRule

if TYPE_CHECKING:
    from ...execution.graph import ExecutionGraph
    from ...runtime.context import ExecutionContext


class PolicyEvaluator(BaseEvaluator):
    """Evaluates custom policy guardrails.

    Policies can be provided via:

    - ``get_rules`` () → List[GovernanceRule]
      In production this queries the governance_rules DB table.
      In tests, rules can be directly injected.
    - ``condition_parser`` (condition: str, graph, context) → bool
      Evaluates a condition expression against the graph/context.
      Default: simple key-based matching on graph.metadata.

    Each rule with ``evaluator_type == "POLICY"`` is checked.
    If a rule's condition evaluates to True and it has a ``decision_override``,
    that override is returned. Otherwise the evaluator iterates all rules
    and returns the most restrictive decision found.
    """

    def __init__(
        self,
        *,
        get_rules: Optional[Callable[[], List[GovernanceRule]]] = None,
        condition_parser: Optional[Callable[[str, "ExecutionGraph", "ExecutionContext"], bool]] = None,
    ) -> None:
        super().__init__()
        self._get_rules = get_rules
        self._condition_parser = condition_parser or self._default_condition_parser

    @property
    def name(self) -> str:
        return "policy"

    async def _do_evaluate(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        return self._evaluate_sync(graph, context)

    def _evaluate_sync(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        if not self._get_rules:
            return GovernanceResult.allowed(reason="No policy rules defined")

        rules = self._get_rules()
        policy_rules = [r for r in rules if r.evaluator_type == "POLICY" and r.enabled]

        if not policy_rules:
            return GovernanceResult.allowed(reason="No active policy rules")

        decisions: List[GovernanceDecision] = []
        warnings: List[str] = []
        matched_rules: List[str] = []

        for rule in policy_rules:
            try:
                condition_met = self._condition_parser(rule.condition, graph, context)
            except Exception as exc:
                self._logger.warning(
                    "policy_condition_error",
                    rule_id=rule.id,
                    error=str(exc),
                )
                continue

            if condition_met:
                matched_rules.append(rule.id)
                if rule.decision_override:
                    decisions.append(rule.decision_override)
                    warnings.append(f"Rule '{rule.name}' triggered: {rule.decision_override.value}")

        if not matched_rules:
            return GovernanceResult.allowed(
                reason="No policy rules matched",
                metadata={"rules_checked": len(policy_rules)},
            )

        # If rules matched but none had a decision_override, allow
        if not decisions:
            return GovernanceResult.allowed(
                reason=f"Rules matched but no decisions: {', '.join(matched_rules)}",
                metadata={"matched_rules": matched_rules, "rules_checked": len(policy_rules)},
            )

        # Determine most restrictive decision
        # Priority: ESCALATE > REJECT > REQUIRE_APPROVAL > WAIT > ALLOW_WITH_WARNING > ALLOW
        decision_priority = {
            GovernanceDecision.ESCALATE: 6,
            GovernanceDecision.REJECT: 5,
            GovernanceDecision.REQUIRE_APPROVAL: 4,
            GovernanceDecision.WAIT: 3,
            GovernanceDecision.ALLOW_WITH_WARNING: 2,
            GovernanceDecision.ALLOW: 1,
        }

        final_decision = max(decisions, key=lambda d: decision_priority.get(d, 0))

        # Build result
        reason = f"Policy rules matched: {', '.join(matched_rules)}"
        metadata: Dict[str, Any] = {
            "matched_rules": matched_rules,
            "rules_checked": len(policy_rules),
            "decisions": [d.value for d in decisions],
        }

        if final_decision == GovernanceDecision.ESCALATE:
            return GovernanceResult.escalated(reason=reason, warnings=warnings, metadata=metadata)
        if final_decision == GovernanceDecision.REJECT:
            return GovernanceResult.rejected(reason=reason, metadata=metadata)
        if final_decision == GovernanceDecision.REQUIRE_APPROVAL:
            return GovernanceResult.require_approval(
                reason=reason,
                approvals=["policy-approver"],
                warnings=warnings,
                metadata=metadata,
            )
        if final_decision == GovernanceDecision.WAIT:
            return GovernanceResult.wait(reason=reason, suggested_delay=60, warnings=warnings, metadata=metadata)
        if final_decision == GovernanceDecision.ALLOW_WITH_WARNING:
            return GovernanceResult.allowed_with_warning(reason=reason, warnings=warnings, metadata=metadata)

        return GovernanceResult.allowed(reason=reason, metadata=metadata)

    @staticmethod
    def _default_condition_parser(
        condition: str,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> bool:
        """Default condition parser — simple key=value matching on graph.metadata.

        Syntax:
        - ``key`` → True if key exists and is truthy in graph.metadata
        - ``key=value`` → True if graph.metadata['key'] == value
        - ``key!=value`` → True if graph.metadata['key'] != value
        - ``!key`` → True if key does not exist or is falsy
        """
        if not condition:
            return False

        graph_meta = getattr(graph, "metadata", {}) or {}

        # Negation: !key
        if condition.startswith("!"):
            key = condition[1:]
            return not bool(graph_meta.get(key))

        # Not-equals: key!=value
        if "!=" in condition:
            key, val = condition.split("!=", 1)
            key, val = key.strip(), val.strip()
            actual = graph_meta.get(key)
            return str(actual) != val

        # Equals: key=value
        if "=" in condition:
            key, val = condition.split("=", 1)
            key, val = key.strip(), val.strip()
            actual = graph_meta.get(key)
            # Type-coerce: try numeric comparison if both look numeric
            try:
                if val.lower() in ("true", "false"):
                    return bool(actual) == (val.lower() == "true")
                num_actual = float(str(actual))
                num_val = float(val)
                return num_actual == num_val
            except (ValueError, TypeError):
                return str(actual) == val

        # Simple key existence
        return bool(graph_meta.get(condition))
