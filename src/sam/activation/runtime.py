"""Runtime — entry point Activation Runtime (extendable per sprint)."""

from typing import Any, Dict, List, Optional

from sam.activation.activation_context import ActivationContext
from sam.activation.activation_request import ActivationRequest
from sam.activation.activation_candidate import ActivationCandidate
from sam.activation.activation_registry import ActivationRegistry
from sam.activation.activation_builder import ActivationBuilder
from sam.activation.activation_draft import ActivationDraft
from sam.activation.activation_validator import ActivationValidator, ValidationReport
from sam.activation.activation_rules import ActivationRules
from sam.activation.activation_constraints import ActivationConstraints
from sam.activation.activation_readiness import ActivationReadiness
from sam.activation.activation_report import ActivationReport, ActivationReportBuilder
from sam.activation.conversation_activation import ConversationActivation
from sam.activation.conversation_validation import ConversationValidation
from sam.activation.dashboard_activation import DashboardActivation
from sam.activation.dashboard_validation import DashboardValidation


class ActivationRuntime:
    """Entry point Activation Runtime — Phase VIII.

    Pipeline:
    Context + Request → Builder → Draft → Validator → Report
    """

    def __init__(self):
        self._registry = ActivationRegistry()
        self._builder = ActivationBuilder()
        self._validator = ActivationValidator()
        self._rules = ActivationRules()
        self._constraints = ActivationConstraints()
        self._readiness = ActivationReadiness()
        self._report_builder = ActivationReportBuilder()

    @property
    def registry(self) -> ActivationRegistry:
        return self._registry

    @property
    def builder(self) -> ActivationBuilder:
        return self._builder

    @property
    def validator(self) -> ActivationValidator:
        return self._validator

    @property
    def rules(self) -> ActivationRules:
        return self._rules

    @property
    def constraints(self) -> ActivationConstraints:
        return self._constraints

    @property
    def readiness(self) -> ActivationReadiness:
        return self._readiness

    @property
    def report_builder(self) -> ActivationReportBuilder:
        return self._report_builder

    @property
    def conversation(self) -> ConversationActivation:
        return ConversationActivation(self._registry)

    @property
    def conversation_validation(self) -> ConversationValidation:
        return ConversationValidation(self._registry)

    @property
    def dashboard(self) -> DashboardActivation:
        return DashboardActivation(self._registry)

    @property
    def dashboard_validation(self) -> DashboardValidation:
        return DashboardValidation(self._registry)

    def run(self, ctx: ActivationContext,
            req: ActivationRequest) -> ActivationDraft:
        """Siklus utama: register → build → draft."""
        self._registry.register_context(ctx)
        self._registry.register_request(req)
        candidates = self._builder.build(ctx, req)
        for c in candidates:
            self._registry.register_candidate(c)

        types_used = list({c.candidate_type for c in candidates})
        top = max(candidates, key=lambda x: x.priority_score) if candidates else None

        return ActivationDraft(
            draft_id=f"draft_{ctx.context_id}_{req.request_id}",
            context_id=ctx.context_id,
            candidates=len(candidates),
            types_used=types_used,
            top_candidate=top.candidate_id if top else "",
            summary=f"Generated {len(candidates)} candidates ({', '.join(types_used)})",
        )

    def run_validation(self, env: str = "normal") -> ActivationReport:
        """Jalankan validasi penuh setelah run()."""
        draft = ActivationDraft(
            draft_id=f"val_{self._registry.list_contexts()[0].context_id}" if self._registry.context_count > 0 else "empty",
            context_id=self._registry.list_contexts()[0].context_id if self._registry.context_count > 0 else "empty",
            candidates=self._registry.candidate_count,
            top_candidate=self._registry.list_candidates()[0].candidate_id if self._registry.candidate_count > 0 else "",
        )
        validation = self._validator.validate(draft, self._registry.list_candidates())
        constraints = self._constraints.check_all(env, draft.candidates, self._registry.list_candidates())
        readiness = self._readiness.check(
            context_exists=self._registry.context_count > 0,
            candidates_ready=self._registry.candidate_count > 0,
        )
        return self._report_builder.build(
            f"report_{draft.draft_id}", validation, constraints, readiness
        )

    def snapshot(self) -> Dict[str, Any]:
        snap = self._registry.snapshot()
        return {
            "contexts": snap.contexts,
            "requests": snap.requests,
            "candidates": snap.candidates,
            "status": snap.status,
        }
