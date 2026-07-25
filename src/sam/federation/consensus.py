"""Federated Consensus — Sprint 31.

Weighted trust × confidence × historical accuracy consensus
for making decisions across federated clusters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.federation.trust import TrustManager

logger = structlog.get_logger()

WEIGHT_TRUST = 0.4
WEIGHT_CONFIDENCE = 0.35
WEIGHT_HISTORY = 0.25


@dataclass
class ConsensusVote:
    """A single vote in the consensus process.

    Attributes:
        cluster_id: Voting cluster.
        option: Selected option / proposal ID.
        confidence: Cluster's confidence in this vote.
        trust_score: Trust score of the voting cluster.
        weight: Computed weight for this vote.
    """
    cluster_id: str = ""
    option: str = ""
    confidence: float = 0.0
    trust_score: float = 0.0
    weight: float = 0.0


class ConsensusEngine:
    """Weighted consensus engine for federated decision making."""

    def __init__(self, trust_manager: TrustManager) -> None:
        self._trust = trust_manager
        self.logger = logger.bind(component="ConsensusEngine")

    async def compute_weighted_consensus(
        self,
        votes: List[ConsensusVote],
    ) -> Dict[str, Any]:
        """Compute weighted consensus from votes.

        Each vote weight = (trust × WEIGHT_TRUST) + (confidence × WEIGHT_CONFIDENCE)
                        + (historical_accuracy × WEIGHT_HISTORY)

        Returns dict with winning option, confidence breakdown, and per-option scores.
        """
        if not votes:
            return {"winner": "", "confidence": 0.0, "options": {}}

        # Compute weights for each vote
        for vote in votes:
            trust_record = await self._trust.get_trust(vote.cluster_id)
            hist_acc = trust_record.success_rate
            vote.trust_score = trust_record.trust_score
            vote.weight = (
                trust_record.trust_score * WEIGHT_TRUST +
                vote.confidence * WEIGHT_CONFIDENCE +
                hist_acc * WEIGHT_HISTORY
            )

        # Aggregate by option
        options: Dict[str, float] = {}
        option_clusters: Dict[str, List[str]] = {}
        for vote in votes:
            options[vote.option] = options.get(vote.option, 0) + vote.weight
            if vote.option not in option_clusters:
                option_clusters[vote.option] = []
            option_clusters[vote.option].append(vote.cluster_id)

        # Find winner
        winner = max(options, key=options.get)
        total_weight = sum(options.values())
        winner_confidence = options[winner] / total_weight if total_weight > 0 else 0

        return {
            "winner": winner,
            "confidence": round(winner_confidence, 4),
            "options": {k: round(v, 4) for k, v in options.items()},
            "option_clusters": option_clusters,
            "total_votes": len(votes),
        }

    async def simple_majority(
        self,
        votes: List[ConsensusVote],
    ) -> Dict[str, Any]:
        """Simple majority consensus (each cluster = 1 vote)."""
        counts: Dict[str, int] = {}
        for v in votes:
            counts[v.option] = counts.get(v.option, 0) + 1

        if not counts:
            return {"winner": "", "confidence": 0.0, "options": {}}

        winner = max(counts, key=counts.get)
        total = sum(counts.values())
        return {
            "winner": winner,
            "confidence": round(counts[winner] / total, 4),
            "options": counts,
            "total_votes": total,
        }
