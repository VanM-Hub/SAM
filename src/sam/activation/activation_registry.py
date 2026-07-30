"""Activation Registry — menyimpan kandidat dan konteks aktivasi."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sam.activation.activation_context import ActivationContext
from sam.activation.activation_candidate import ActivationCandidate
from sam.activation.activation_request import ActivationRequest


@dataclass(frozen=True)
class ActivationSnapshot:
    """Snapshot registry — immutable."""
    contexts: int = 0
    requests: int = 0
    candidates: int = 0
    status: str = "empty"


class ActivationRegistry:
    """Registry untuk Activation Runtime — mutable internal, output immutable."""

    def __init__(self):
        self._contexts: Dict[str, ActivationContext] = {}
        self._requests: Dict[str, ActivationRequest] = {}
        self._candidates: Dict[str, ActivationCandidate] = {}

    # --- Context ---

    def register_context(self, ctx: ActivationContext) -> None:
        self._contexts[ctx.context_id] = ctx

    def get_context(self, ctx_id: str) -> Optional[ActivationContext]:
        return self._contexts.get(ctx_id)

    def list_contexts(self) -> List[ActivationContext]:
        return list(self._contexts.values())

    @property
    def context_count(self) -> int:
        return len(self._contexts)

    # --- Request ---

    def register_request(self, req: ActivationRequest) -> None:
        self._requests[req.request_id] = req

    def get_request(self, req_id: str) -> Optional[ActivationRequest]:
        return self._requests.get(req_id)

    def list_requests(self) -> List[ActivationRequest]:
        return list(self._requests.values())

    @property
    def request_count(self) -> int:
        return len(self._requests)

    # --- Candidate ---

    def register_candidate(self, c: ActivationCandidate) -> None:
        self._candidates[c.candidate_id] = c

    def get_candidate(self, cid: str) -> Optional[ActivationCandidate]:
        return self._candidates.get(cid)

    def list_candidates(self) -> List[ActivationCandidate]:
        return list(self._candidates.values())

    def list_candidates_by_type(self, ctype: str) -> List[ActivationCandidate]:
        return [c for c in self._candidates.values() if c.candidate_type == ctype]

    @property
    def candidate_count(self) -> int:
        return len(self._candidates)

    # --- Snapshot ---

    def snapshot(self) -> ActivationSnapshot:
        return ActivationSnapshot(
            contexts=self.context_count,
            requests=self.request_count,
            candidates=self.candidate_count,
            status="active" if self.context_count > 0 else "empty",
        )

    def clear(self) -> None:
        self._contexts.clear()
        self._requests.clear()
        self._candidates.clear()
