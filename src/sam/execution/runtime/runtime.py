"""Runtime — entry point Execution Runtime (Sprint 88–89 Foundation + Validation)."""
from typing import Any, Dict, List, Optional
from sam.execution.runtime.execution_context import ExecutionContext
from sam.execution.runtime.execution_request import ExecutionRequest
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.execution_registry import ExecutionRegistry
from sam.execution.runtime.execution_builder import ExecutionBuilder
from sam.execution.runtime.execution_draft import ExecutionDraft
from sam.execution.runtime.execution_validator import (
    ExecutionValidator, ExecutionRules, ExecutionConstraints,
    ExecutionReadiness, ExecutionReportBuilder, ExecutionReport,
)


class ExecutionRuntime:
    """Entry point Execution Runtime — Phase IX.

    Pipeline:
    Context + Request → Builder → Draft → Validator → Report
    """

    def __init__(self):
        self._registry = ExecutionRegistry()
        self._builder = ExecutionBuilder()
        self._validator = ExecutionValidator()
        self._rules = ExecutionRules()
        self._constraints = ExecutionConstraints()
        self._readiness = ExecutionReadiness()
        self._report_builder = ExecutionReportBuilder()

    @property
    def registry(self) -> ExecutionRegistry:
        return self._registry

    @property
    def builder(self) -> ExecutionBuilder:
        return self._builder

    @property
    def validator(self) -> ExecutionValidator:
        return self._validator

    @property
    def rules(self) -> ExecutionRules:
        return self._rules

    @property
    def constraints(self) -> ExecutionConstraints:
        return self._constraints

    @property
    def readiness(self) -> ExecutionReadiness:
        return self._readiness

    @property
    def report_builder(self) -> ExecutionReportBuilder:
        return self._report_builder

    @property
    def conversation(self):
        from sam.execution.runtime.conversation_execution import ConversationExecution
        return ConversationExecution(self._registry)

    @property
    def dashboard(self):
        from sam.execution.runtime.dashboard_execution import DashboardExecution
        return DashboardExecution(self._registry)

    def run(self, ctx: ExecutionContext, req: ExecutionRequest) -> ExecutionDraft:
        """Siklus utama: register → build → draft."""
        self._registry.register_context(ctx)
        self._registry.register_request(req)

        candidates = []
        c1 = self._builder.build_immediate(
            candidate_id=f"c_{req.request_id}_imm",
            context_id=ctx.context_id,
            request_id=req.request_id,
            timestamp=req.timestamp,
            name=f"immediate_{req.request_id}",
        )
        candidates.append(c1)
        self._registry.register_candidate(c1)

        return ExecutionDraft(
            draft_id=f"draft_{ctx.context_id}_{req.request_id}",
            context_id=ctx.context_id,
            candidates=len(candidates),
            types_used=["immediate"],
            summary=f"Generated {len(candidates)} candidate(s)",
        )

    def run_validation(self, env: str = "normal") -> ExecutionReport:
        """Jalankan validasi penuh setelah run()."""
        ctxs = self._registry.list_contexts()
        reqs = self._registry.list_requests()
        if not ctxs:
            return ExecutionReportBuilder().build("empty", self._validator.validate(
                ExecutionDraft("empty", "empty", 0, [], ""), []
            ), ["no_context"], {"ready": False, "score": 0.0, "checks": {}, "passed": 0, "total": 0})

        draft = ExecutionDraft(
            draft_id=f"val_{ctxs[0].context_id}",
            context_id=ctxs[0].context_id,
            candidates=self._registry.snapshot().candidate_count,
            types_used=["immediate"],
            summary="validation run",
        )
        validation = self._validator.validate(draft, self._registry.list_candidates())
        constraints = self._constraints.check_all(
            candidate_count=draft.candidates,
            dependencies_total=0,
            max_effort=100.0,
        )
        readiness = self._readiness.check(
            context_exists=self._registry.snapshot().context_count > 0,
            candidates_ready=self._registry.snapshot().candidate_count > 0,
            request_valid=len(reqs) > 0,
        )
        return self._report_builder.build(
            f"report_{draft.draft_id}", validation, constraints, readiness
        )
