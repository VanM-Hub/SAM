"""Conflict Resolution — Sprint 31.

When two clusters provide different recommendations or insights,
resolve the conflict using trust, confidence, and freshness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.federation.trust import TrustManager
from sam.federation.provenance import Provenance

logger = structlog.get_logger()

RESOLUTION_ACCEPT_FIRST = "accept_first"
RESOLUTION_ACCEPT_HIGHER_CONFIDENCE = "accept_higher_confidence"
RESOLUTION_ACCEPT_HIGHER_TRUST = "accept_higher_trust"
RESOLUTION_MERGE = "merge"
RESOLUTION_REJECT_BOTH = "reject_both"


@dataclass
class ConflictResult:
    """Result of a conflict resolution.

    Attributes:
        winner_id: ID of the winning insight/recommendation.
        resolution_strategy: Which strategy was used.
        winner_confidence: Confidence of the winner.
        confidence_gap: Difference between winner and runner-up.
        reason: Human-readable explanation.
    """
    winner_id: str = ""
    resolution_strategy: str = ""
    winner_confidence: float = 0.0
    confidence_gap: float = 0.0
    reason: str = ""


class ConflictResolver:
    """Resolves conflicts between competing insights from different clusters."""

    def __init__(self, trust_manager: TrustManager) -> None:
        self._trust = trust_manager
        self.logger = logger.bind(component="ConflictResolver")

    async def resolve(
        self,
        candidates: List[Dict[str, Any]],
        strategy: str = RESOLUTION_ACCEPT_HIGHER_CONFIDENCE,
    ) -> ConflictResult:
        """Resolve a conflict among candidate insights.

        Args:
            candidates: List of dicts with 'id', 'cluster_id', 'confidence'.
            strategy: Resolution strategy to use.

        Returns:
            ConflictResult with the winner.
        """
        if not candidates:
            return ConflictResult(reason="No candidates provided")

        if len(candidates) == 1:
            c = candidates[0]
            return ConflictResult(
                winner_id=c.get("id", ""),
                resolution_strategy="single_candidate",
                winner_confidence=float(c.get("confidence", 0.0)),
                confidence_gap=0.0,
                reason="Only one candidate available",
            )

        if strategy == RESOLUTION_ACCEPT_FIRST:
            return self._resolve_first(candidates)

        elif strategy == RESOLUTION_ACCEPT_HIGHER_CONFIDENCE:
            return await self._resolve_by_confidence(candidates)

        elif strategy == RESOLUTION_ACCEPT_HIGHER_TRUST:
            return await self._resolve_by_trust(candidates)

        elif strategy == RESOLUTION_MERGE:
            return await self._resolve_merge(candidates)

        elif strategy == RESOLUTION_REJECT_BOTH:
            return ConflictResult(
                resolution_strategy=strategy,
                reason="Both candidates rejected",
            )

        return await self._resolve_by_confidence(candidates)

    @staticmethod
    def _resolve_first(candidates: List[Dict[str, Any]]) -> ConflictResult:
        c = candidates[0]
        return ConflictResult(
            winner_id=c.get("id", ""),
            resolution_strategy=RESOLUTION_ACCEPT_FIRST,
            winner_confidence=float(c.get("confidence", 0.0)),
            confidence_gap=0.0,
            reason="Accepted first candidate",
        )

    async def _resolve_by_confidence(
        self,
        candidates: List[Dict[str, Any]],
    ) -> ConflictResult:
        sorted_c = sorted(
            candidates,
            key=lambda c: float(c.get("confidence", 0)),
            reverse=True,
        )
        winner = sorted_c[0]
        runner_up = sorted_c[1] if len(sorted_c) > 1 else None
        gap = (float(winner.get("confidence", 0)) -
               float(runner_up.get("confidence", 0))) if runner_up else 0
        return ConflictResult(
            winner_id=winner.get("id", ""),
            resolution_strategy=RESOLUTION_ACCEPT_HIGHER_CONFIDENCE,
            winner_confidence=float(winner.get("confidence", 0)),
            confidence_gap=round(gap, 4),
            reason=f"Highest confidence: {winner.get('confidence')}",
        )

    async def _resolve_by_trust(
        self,
        candidates: List[Dict[str, Any]],
    ) -> ConflictResult:
        scored = []
        for c in candidates:
            trust = await self._trust.get_trust(c.get("cluster_id", ""))
            combined = float(c.get("confidence", 0)) * trust.trust_score
            scored.append((combined, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        winner = scored[0][1]
        runner_up = scored[1][1] if len(scored) > 1 else None
        gap = scored[0][0] - (scored[1][0] if len(scored) > 1 else 0)
        return ConflictResult(
            winner_id=winner.get("id", ""),
            resolution_strategy=RESOLUTION_ACCEPT_HIGHER_TRUST,
            winner_confidence=float(winner.get("confidence", 0)),
            confidence_gap=round(gap, 4),
            reason=f"Highest trust × confidence combined score",
        )

    async def _resolve_merge(
        self,
        candidates: List[Dict[str, Any]],
    ) -> ConflictResult:
        """Merge: average confidence, pick first content."""
        merged = candidates[0]
        avg_conf = sum(float(c.get("confidence", 0)) for c in candidates) / len(candidates)
        return ConflictResult(
            winner_id=merged.get("id", ""),
            resolution_strategy=RESOLUTION_MERGE,
            winner_confidence=round(avg_conf, 4),
            confidence_gap=0.0,
            reason=f"Merged {len(candidates)} candidates, avg confidence {avg_conf:.2f}",
        )
