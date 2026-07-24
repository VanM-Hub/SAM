"""Trust Negotiation — Sprint 31.

Trust scores per cluster with dynamic adjustment based on
historical accuracy, reliability, and behavior.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()

DEFAULT_TRUST = 0.5
TRUST_DECAY_RATE = 0.01  # per day
TRUST_BOOST_ON_SUCCESS = 0.05
TRUST_PENALTY_ON_FAILURE = 0.10
MIN_TRUST = 0.0
MAX_TRUST = 1.0


@dataclass
class ClusterTrust:
    """Trust record for a cluster.

    Attributes:
        cluster_id: Target cluster.
        trust_score: 0.0–1.0 current trust.
        interactions: Total interactions count.
        successful_interactions: Count of successful interactions.
        last_interaction: Timestamp of last interaction.
        history: List of recent trust adjustments.
    """
    cluster_id: str = ""
    trust_score: float = DEFAULT_TRUST
    interactions: int = 0
    successful_interactions: int = 0
    last_interaction: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.interactions == 0:
            return 0.0
        return self.successful_interactions / self.interactions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "trust_score": self.trust_score,
            "interactions": self.interactions,
            "successful_interactions": self.successful_interactions,
            "success_rate": self.success_rate,
            "last_interaction": self.last_interaction.isoformat(),
        }


class TrustManager:
    """Manages trust scores for federated clusters."""

    def __init__(self) -> None:
        self._trusts: Dict[str, ClusterTrust] = {}
        self.logger = logger.bind(component="TrustManager")

    async def get_trust(self, cluster_id: str) -> ClusterTrust:
        """Get trust record for a cluster (creates default if none)."""
        if cluster_id not in self._trusts:
            self._trusts[cluster_id] = ClusterTrust(cluster_id=cluster_id)
        return self._trusts[cluster_id]

    async def record_interaction(
        self,
        cluster_id: str,
        success: bool,
        reason: str = "",
    ) -> ClusterTrust:
        """Record a successful or failed interaction and adjust trust."""
        trust = await self.get_trust(cluster_id)
        trust.interactions += 1
        trust.last_interaction = datetime.now(timezone.utc)

        adjustment = TRUST_BOOST_ON_SUCCESS if success else -TRUST_PENALTY_ON_FAILURE
        if success:
            trust.successful_interactions += 1

        new_score = max(MIN_TRUST, min(MAX_TRUST, trust.trust_score + adjustment))
        trust.trust_score = new_score

        trust.history.append({
            "timestamp": trust.last_interaction.isoformat(),
            "success": success,
            "adjustment": adjustment,
            "new_score": new_score,
            "reason": reason,
        })
        if len(trust.history) > 1000:
            trust.history = trust.history[-500:]

        self.logger.debug(
            "Trust updated",
            cluster=cluster_id,
            score=new_score,
            success=success,
        )
        return trust

    async def get_all_trusts(self) -> List[ClusterTrust]:
        return list(self._trusts.values())

    async def apply_decay(self, days: float = 1.0) -> None:
        """Apply trust decay over time."""
        for trust in self._trusts.values():
            decay = TRUST_DECAY_RATE * days
            trust.trust_score = max(MIN_TRUST, trust.trust_score - decay)

    async def clear(self) -> None:
        self._trusts.clear()
