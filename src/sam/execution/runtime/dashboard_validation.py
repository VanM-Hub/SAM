"""Dashboard Validation Bridge — 5 immutable cards."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from sam.execution.runtime.execution_registry import ExecutionRegistry
from sam.execution.runtime.execution_validator import (
    ExecutionValidator, ExecutionRules, ExecutionConstraints, ExecutionReadiness,
)
from sam.execution.runtime.dashboard_execution import ExecutionCard


class DashboardValidation:
    """Dashboard bridge untuk execution validation — 5 immutable cards."""

    def __init__(self, registry: ExecutionRegistry, validator: ExecutionValidator,
                 rules: ExecutionRules, constraints: ExecutionConstraints,
                 readiness: ExecutionReadiness) -> None:
        self._registry = registry
        self._validator = validator
        self._rules = rules
        self._constraints = constraints
        self._readiness = readiness

    def validator_card(self) -> ExecutionCard:
        """Card 1: Validator status."""
        return ExecutionCard(
            title="Execution Validator",
            description="Status validator",
            status="ready",
            metrics={"valid_types": len(ExecutionValidator.VALID_TYPES)},
            items=list(ExecutionValidator.VALID_TYPES),
        )

    def rules_card(self) -> ExecutionCard:
        """Card 2: Rules info."""
        return ExecutionCard(
            title="Execution Rules",
            description="Daftar rule aktif",
            status="active",
            metrics={"active_rules": self._rules.count_active_rules()},
            items=["environment", "task_type", "priority", "effort", "candidate_type"],
        )

    def constraints_card(self) -> ExecutionCard:
        """Card 3: Constraints info."""
        return ExecutionCard(
            title="Execution Constraints",
            description="Batas-batas constraint",
            status="ready",
            metrics={
                "max_candidates": ExecutionConstraints.MAX_CANDIDATES,
                "max_dependencies": ExecutionConstraints.MAX_DEPENDENCIES,
                "max_effort": ExecutionConstraints.MAX_EFFORT,
            },
            items=["candidates", "dependencies", "effort"],
        )

    def readiness_card(self) -> ExecutionCard:
        """Card 4: Readiness status."""
        snap = self._registry.snapshot()
        rd = self._readiness.check(
            context_exists=snap.context_count > 0,
            candidates_ready=snap.candidate_count > 0,
            request_valid=snap.request_count > 0,
        )
        return ExecutionCard(
            title="Execution Readiness",
            description="Kesiapan eksekusi",
            status="ready" if rd["ready"] else "not_ready",
            metrics={
                "score": rd["score"],
                "passed": rd["passed"],
                "total": rd["total"],
            },
            items=[str(k) for k, v in rd["checks"].items() if v],
        )

    def validation_report_card(self, report) -> ExecutionCard:
        """Card 5: Validation report status."""
        if report is None or report.validation is None:
            return ExecutionCard(
                title="Validation Report",
                description="Belum ada validasi",
                status="empty",
                metrics={"valid": False},
                items=["no_report"],
            )
        return ExecutionCard(
            title="Validation Report",
            description=report.summary,
            status="passed" if report.overall_valid else "failed",
            metrics={
                "valid": report.overall_valid,
                "errors": report.validation.total_errors,
                "warnings": report.validation.total_warnings,
            },
            items=[f"valid={report.overall_valid}"],
        )
