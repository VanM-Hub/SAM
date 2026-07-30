"""Runtime — entry point Activation Runtime Sprint 82."""

from typing import Any, Dict, List, Optional

from sam.activation.activation_context import ActivationContext
from sam.activation.activation_request import ActivationRequest
from sam.activation.activation_candidate import ActivationCandidate
from sam.activation.activation_registry import ActivationRegistry
from sam.activation.activation_builder import ActivationBuilder
from sam.activation.activation_draft import ActivationDraft
from sam.activation.conversation_activation import ConversationActivation
from sam.activation.dashboard_activation import DashboardActivation


class ActivationRuntime:
    """Entry point Activation Runtime — Sprint 82.

    1. Accept OperationalContext → ActivationContext
    2. Accept ActivationRequest
    3. Register context + request di registry
    4. Builder → candidates
    5. Draft output
    """

    def __init__(self):
        self._registry = ActivationRegistry()
        self._builder = ActivationBuilder()

    @property
    def registry(self) -> ActivationRegistry:
        return self._registry

    @property
    def builder(self) -> ActivationBuilder:
        return self._builder

    @property
    def conversation(self) -> ConversationActivation:
        return ConversationActivation(self._registry)

    @property
    def dashboard(self) -> DashboardActivation:
        return DashboardActivation(self._registry)

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

    def snapshot(self) -> Dict[str, Any]:
        snap = self._registry.snapshot()
        return {
            "contexts": snap.contexts,
            "requests": snap.requests,
            "candidates": snap.candidates,
            "status": snap.status,
        }
