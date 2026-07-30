"""Conversation Validation Bridge — 8 queries read-only."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.execution_registry import ExecutionRegistry
from sam.execution.runtime.execution_validator import (
    ExecutionValidator, ExecutionRules, ExecutionConstraints, ExecutionReadiness,
)


class ConversationValidation:
    """Conversation bridge untuk execution validation — 8 queries."""

    def __init__(self, validator: ExecutionValidator, rules: ExecutionRules,
                 constraints: ExecutionConstraints, readiness: ExecutionReadiness) -> None:
        self._validator = validator
        self._rules = rules
        self._constraints = constraints
        self._readiness = readiness

    def get_validator(self) -> ExecutionValidator:
        """Query 1: Ambil validator instance."""
        return self._validator

    def get_rules(self) -> ExecutionRules:
        """Query 2: Ambil rules instance."""
        return self._rules

    def get_constraints(self) -> ExecutionConstraints:
        """Query 3: Ambil constraints instance."""
        return self._constraints

    def get_readiness(self) -> ExecutionReadiness:
        """Query 4: Ambil readiness instance."""
        return self._readiness

    def check_environment(self, env: str) -> bool:
        """Query 5: Cek validitas environment."""
        return self._rules.validate_environment(env)

    def check_task_type(self, ttype: str) -> bool:
        """Query 6: Cek validitas task type."""
        return self._rules.validate_task_type(ttype)

    def check_priority(self, priority: int) -> bool:
        """Query 7: Cek validitas priority."""
        return self._rules.validate_priority(priority)

    def list_active_rules(self) -> int:
        """Query 8: Hitung rule aktif."""
        return self._rules.count_active_rules()
