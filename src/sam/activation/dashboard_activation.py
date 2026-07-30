"""Dashboard Activation Bridge — 6 immutable cards."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sam.activation.activation_registry import ActivationRegistry
from sam.activation.activation_builder import ActivationBuilder
from sam.activation.activation_context import ActivationContext
from sam.activation.activation_request import ActivationRequest


@dataclass(frozen=True)
class ActivationCard:
    """Satu kartu dashboard — immutable."""
    card_type: str
    title: str
    value: Any = None
    items: List[str] = field(default_factory=list)


class DashboardActivation:
    """Dashboard bridge untuk Activation Runtime — 6 immutable cards."""

    def __init__(self, registry: ActivationRegistry):
        self._registry = registry

    @property
    def card_count(self) -> int:
        return 6

    def get_cards(self, builder: ActivationBuilder,
                  ctx: ActivationContext,
                  req: ActivationRequest) -> List[ActivationCard]:
        return [
            self._overview_card(ctx, req),
            self._candidates_card(builder, ctx, req),
            self._registry_card(),
            self._candidates_preview(builder, ctx, req),
            self._requests_card(),
            self._contexts_card(),
        ]

    def _overview_card(self, ctx: ActivationContext,
                       req: ActivationRequest) -> ActivationCard:
        return ActivationCard(
            card_type="overview",
            title="Activation Overview",
            value={
                "context_id": ctx.context_id,
                "environment": ctx.environment,
                "plan_id": req.plan_id,
                "priority": req.priority,
            },
            items=[
                f"Env: {ctx.environment}",
                f"Plan: {req.plan_id}",
                f"Priority: {req.priority}",
                f"Candidates: {ctx.total_candidates}",
                f"Goals: {ctx.total_goals}",
            ],
        )

    def _candidates_card(self, builder: ActivationBuilder,
                         ctx: ActivationContext,
                         req: ActivationRequest) -> ActivationCard:
        candidates = builder.build(ctx, req)
        return ActivationCard(
            card_type="candidates",
            title="Generated Candidates",
            value=len(candidates),
            items=[f"{c.candidate_id} ({c.candidate_type}, {c.confidence})"
                   for c in candidates],
        )

    def _registry_card(self) -> ActivationCard:
        snap = self._registry.snapshot()
        return ActivationCard(
            card_type="registry",
            title="Registry Status",
            value=f"contexts={snap.contexts}, requests={snap.requests}, candidates={snap.candidates}",
            items=[f"Status: {snap.status}"] if snap.contexts > 0 else ["Status: empty"],
        )

    def _candidates_preview(self, builder: ActivationBuilder,
                            ctx: ActivationContext,
                            req: ActivationRequest) -> ActivationCard:
        return ActivationCard(
            card_type="preview",
            title="Builder Preview",
            value=len(builder.build(ctx, req)),
            items=[f"{t}" for t in builder.build_types_list()],
        )

    def _requests_card(self) -> ActivationCard:
        requests = self._registry.list_requests()
        return ActivationCard(
            card_type="requests",
            title="Activation Requests",
            value=len(requests),
            items=[f"{r.request_id} ({r.priority})" for r in requests],
        )

    def _contexts_card(self) -> ActivationCard:
        contexts = self._registry.list_contexts()
        return ActivationCard(
            card_type="contexts",
            title="Activation Contexts",
            value=len(contexts),
            items=[f"{c.context_id} ({c.environment})" for c in contexts],
        )
