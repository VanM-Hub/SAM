"""Dashboard Validation Bridge — Sprint 83, 5 cards."""
from typing import Any, Dict, List
from dataclasses import dataclass, field
from sam.activation.activation_draft import ActivationDraft
from sam.activation.activation_validator import ActivationValidator
from sam.activation.activation_rules import ActivationRules
from sam.activation.activation_constraints import ActivationConstraints
from sam.activation.activation_readiness import ActivationReadiness
from sam.activation.activation_report import ActivationReportBuilder
from sam.activation.activation_registry import ActivationRegistry


@dataclass(frozen=True)
class ValidationCard:
    card_type: str = ""
    title: str = ""
    items: List[str] = field(default_factory=list)


class DashboardValidation:
    """Dashboard bridge untuk Validation — 5 cards."""

    def __init__(self, registry: ActivationRegistry):
        self._registry = registry

    @property
    def card_count(self) -> int:
        return 5

    def get_cards(self, validator: ActivationValidator, draft: ActivationDraft,
                  rules: ActivationRules) -> List[ValidationCard]:
        return [
            self._validation_card(validator, draft),
            self._rules_card(rules),
            self._constraints_card(draft),
            self._readiness_card(),
            self._summary_card(validator, draft, rules),
        ]

    def _validation_card(self, validator: ActivationValidator,
                         draft: ActivationDraft) -> ValidationCard:
        report = validator.validate(draft, self._registry.list_candidates())
        return ValidationCard(
            "validation", "Validation Report",
            [f"Valid: {report.valid}", f"Errors: {report.total_errors}",
             f"Warnings: {report.total_warnings}", report.summary],
        )

    def _rules_card(self, rules: ActivationRules) -> ValidationCard:
        return ValidationCard(
            "rules", "Activation Rules",
            [f"{r.name} ({r.applies_to})" for r in rules.list_rules()],
        )

    def _constraints_card(self, draft: ActivationDraft) -> ValidationCard:
        constraints = ActivationConstraints()
        results = constraints.check_all("normal", draft.candidates, self._registry.list_candidates())
        return ValidationCard(
            "constraints", "Constraint Results",
            [f"{r.constraint_id}: {'PASS' if r.passed else 'FAIL'} ({r.reason})" for r in results],
        )

    def _readiness_card(self) -> ValidationCard:
        readiness = ActivationReadiness()
        checks = readiness.check(
            context_exists=self._registry.context_count > 0,
            candidates_ready=self._registry.candidate_count > 0,
        )
        return ValidationCard(
            "readiness", "Readiness Checks",
            [f"{r.name}: {'✅' if r.passed else '❌'} ({r.score})" for r in checks],
        )

    def _summary_card(self, validator: ActivationValidator,
                      draft: ActivationDraft,
                      rules: ActivationRules) -> ValidationCard:
        constraints = ActivationConstraints()
        cands = self._registry.list_candidates()
        const_res = constraints.check_all("normal", draft.candidates, cands)
        readiness = ActivationReadiness()
        read_res = readiness.check()
        val = validator.validate(draft, cands)
        builder = ActivationReportBuilder()
        report = builder.build("sum_" + draft.draft_id, val, const_res, read_res)
        return ValidationCard(
            "summary", "Validation Summary",
            [f"All valid: {report.valid}", f"Ready Score: {report.ready_score}", report.summary],
        )
