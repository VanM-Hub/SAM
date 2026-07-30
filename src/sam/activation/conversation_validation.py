"""Conversation Validation Bridge — Sprint 83, 8 queries."""
from typing import Any, Dict, List, Optional
from sam.activation.activation_validator import ActivationValidator, ValidationReport
from sam.activation.activation_rules import ActivationRules, ActivationRule
from sam.activation.activation_constraints import ActivationConstraints, ConstraintResult
from sam.activation.activation_readiness import ActivationReadiness, ReadinessCheck
from sam.activation.activation_report import ActivationReport, ActivationReportBuilder
from sam.activation.activation_draft import ActivationDraft
from sam.activation.activation_candidate import ActivationCandidate
from sam.activation.activation_registry import ActivationRegistry


class ConversationValidation:
    """Conversation bridge untuk Validation module — 8 queries."""

    def __init__(self, registry: ActivationRegistry):
        self._registry = registry

    @property
    def query_count(self) -> int:
        return 8

    def query_validation_report(self, validator: ActivationValidator,
                                draft: ActivationDraft) -> Dict[str, Any]:
        candidates = self._registry.list_candidates()
        report = validator.validate(draft, candidates)
        return {
            "draft_id": report.draft_id,
            "valid": report.valid,
            "total_errors": report.total_errors,
            "total_warnings": report.total_warnings,
            "summary": report.summary,
        }

    def query_rules_list(self, rules: ActivationRules) -> List[Dict[str, Any]]:
        return [
            {"name": r.name, "description": r.description, "applies_to": r.applies_to}
            for r in rules.list_rules()
        ]

    def query_constraints_check(self, constraints: ActivationConstraints,
                                env: str, candidates: List[ActivationCandidate]) -> List[Dict[str, Any]]:
        results = constraints.check_all(env, len(candidates), candidates)
        return [
            {"constraint": r.constraint_id, "passed": r.passed, "reason": r.reason}
            for r in results
        ]

    def query_readiness(self, readiness: ActivationReadiness) -> List[Dict[str, Any]]:
        results = readiness.check()
        return [
            {"check": r.check_id, "name": r.name, "passed": r.passed, "score": r.score}
            for r in results
        ]

    def query_readiness_all(self, readiness: ActivationReadiness) -> List[str]:
        return readiness.all_checks()

    def query_full_report(self, builder: ActivationReportBuilder,
                          validator: ActivationValidator,
                          draft: ActivationDraft,
                          env: str) -> Dict[str, Any]:
        candidates = self._registry.list_candidates()
        val = validator.validate(draft, candidates)
        constraints = ActivationConstraints()
        const_res = constraints.check_all(env, draft.candidates, candidates)
        readiness = ActivationReadiness()
        read_res = readiness.check()
        report = builder.build(f"rep_{draft.draft_id}", val, const_res, read_res)
        return {
            "report_id": report.report_id,
            "valid": report.valid,
            "ready_score": report.ready_score,
            "summary": report.summary,
        }

    def query_validator_info(self, validator: ActivationValidator) -> Dict[str, Any]:
        return {"valid_types": sorted(list(validator.VALID_TYPES))}

    def query_report_detail(self, report: ActivationReport) -> Dict[str, Any]:
        return {
            "report_id": report.report_id,
            "valid": report.valid,
            "ready_score": report.ready_score,
            "summary": report.summary,
        }
