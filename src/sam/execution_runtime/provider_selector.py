"""Provider Selector (Sprint 253).

Program C - Real Execution Runtime.
Memilih provider terbaik untuk sebuah request (generic scoring, tidak
provider-specific). Deterministic, no network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .execution_request import ExecutionRequest
from .provider_dispatcher import KNOWN_PROVIDERS


@dataclass(frozen=True)
class SelectorRanking:
    """Ranking satu provider (immutable)."""
    provider_id: str
    score: float = 0.0
    reason: str = ""

    def as_dict(self) -> dict:
        return {"provider_id": self.provider_id, "score": self.score, "reason": self.reason}


class ProviderSelector:
    """Seleksi provider generik. Generic, deterministic."""

    def __init__(self, candidates: tuple = KNOWN_PROVIDERS) -> None:
        self._candidates = tuple(candidates)

    def rank(self, request: ExecutionRequest) -> List[SelectorRanking]:
        order = []
        for i, pid in enumerate(self._candidates):
            score = 1.0 / (i + 1)
            reason = f"priority-{i + 1}"
            if pid == request.provider_id:
                score = 10.0
                reason = "explicit-preference"
            order.append(SelectorRanking(provider_id=pid, score=score, reason=reason))
        order.sort(key=lambda r: (-r.score, r.provider_id))
        return order

    def best(self, request: ExecutionRequest) -> SelectorRanking:
        return self.rank(request)[0]
