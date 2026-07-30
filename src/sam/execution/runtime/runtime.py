"""Runtime — entry point Execution Runtime (Sprint 88 Foundation)."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from sam.execution.runtime.execution_context import ExecutionContext
from sam.execution.runtime.execution_request import ExecutionRequest
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.execution_registry import ExecutionRegistry
from sam.execution.runtime.execution_builder import ExecutionBuilder


@dataclass(frozen=True)
class ExecutionDraft:
    """Draft hasil eksekusi runtime."""
    draft_id: str
    context_id: str
    candidates: int
    types_used: List[str]
    summary: str


class ExecutionRuntime:
    """Entry point Execution Runtime — Phase IX Sprint 88.

    Pipeline:
    Context + Request → Builder → Draft
    """

    def __init__(self):
        self._registry = ExecutionRegistry()
        self._builder = ExecutionBuilder()

    @property
    def registry(self) -> ExecutionRegistry:
        return self._registry

    @property
    def builder(self) -> ExecutionBuilder:
        return self._builder

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
