"""Transform Engine — engine transformasi."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_adapter import TransformRule


class TransformEngine:
    """Engine transformasi — preview-only."""

    def __init__(self) -> None:
        self._rules: Dict[str, TransformRule] = {}

    def add_rule(self, rule: TransformRule) -> None:
        self._rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> TransformRule | None:
        return self._rules.get(rule_id)

    def count(self) -> int:
        return len(self._rules)

    def apply(self, rule_id: str, value: str) -> str:
        rule = self._rules.get(rule_id)
        if not rule:
            return value
        if rule.transform_type == "upper":
            return value.upper()
        elif rule.transform_type == "lower":
            return value.lower()
        elif rule.transform_type == "prefix":
            return f"sam_{value}"
        return value
