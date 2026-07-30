"""Conversation Activation Bridge — 10 query read-only."""

from typing import Any, Dict, List, Optional

from sam.activation.activation_context import ActivationContext
from sam.activation.activation_registry import ActivationRegistry
from sam.activation.activation_builder import ActivationBuilder
from sam.activation.activation_candidate import ActivationCandidate
from sam.activation.activation_request import ActivationRequest


class ConversationActivation:
    """Conversation bridge untuk Activation Runtime — 10 query read-only."""

    def __init__(self, registry: ActivationRegistry):
        self._registry = registry

    @property
    def query_count(self) -> int:
        return 10

    def query_context(self, ctx_id: str) -> Optional[Dict[str, Any]]:
        ctx = self._registry.get_context(ctx_id)
        if ctx is None:
            return None
        return ctx.to_dict()

    def query_all_contexts(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._registry.list_contexts()]

    def query_request(self, req_id: str) -> Optional[Dict[str, Any]]:
        req = self._registry.get_request(req_id)
        if req is None:
            return None
        return {
            "request_id": req.request_id,
            "plan_id": req.plan_id,
            "timestamp": req.timestamp,
            "requester": req.requester,
            "priority": req.priority,
            "context_ref": req.context_ref,
        }

    def query_all_requests(self) -> List[Dict[str, Any]]:
        return [
            {
                "request_id": r.request_id,
                "plan_id": r.plan_id,
                "timestamp": r.timestamp,
                "requester": r.requester,
                "priority": r.priority,
            }
            for r in self._registry.list_requests()
        ]

    def query_candidate(self, cid: str) -> Optional[Dict[str, Any]]:
        c = self._registry.get_candidate(cid)
        if c is None:
            return None
        return {
            "candidate_id": c.candidate_id,
            "name": c.name,
            "candidate_type": c.candidate_type,
            "confidence": c.confidence,
            "priority_score": c.priority_score,
            "estimated_duration": c.estimated_duration,
            "prerequisites": list(c.prerequisites),
        }

    def query_all_candidates(self) -> List[Dict[str, Any]]:
        return [
            {
                "candidate_id": c.candidate_id,
                "name": c.name,
                "candidate_type": c.candidate_type,
                "confidence": c.confidence,
                "priority_score": c.priority_score,
            }
            for c in self._registry.list_candidates()
        ]

    def query_candidates_by_type(self, ctype: str) -> List[Dict[str, Any]]:
        return [
            {
                "candidate_id": c.candidate_id,
                "name": c.name,
                "confidence": c.confidence,
            }
            for c in self._registry.list_candidates_by_type(ctype)
        ]

    def query_snapshot(self) -> Dict[str, Any]:
        snap = self._registry.snapshot()
        return {
            "contexts": snap.contexts,
            "requests": snap.requests,
            "candidates": snap.candidates,
            "status": snap.status,
        }

    def query_builder_types(self, builder: ActivationBuilder) -> List[str]:
        return builder.build_types_list()

    def query_builder_preview(self, builder: ActivationBuilder,
                              ctx: ActivationContext,
                              req: ActivationRequest) -> Dict[str, Any]:
        candidates = builder.build(ctx, req)
        return {
            "context_id": ctx.context_id,
            "environment": ctx.environment,
            "total_candidates_generated": len(candidates),
            "candidates": [
                {
                    "candidate_id": c.candidate_id,
                    "candidate_type": c.candidate_type,
                    "confidence": c.confidence,
                }
                for c in candidates
            ],
        }
