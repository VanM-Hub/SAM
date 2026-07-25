"""Cluster Learning Aggregator — Sprint 30.

Aggregates knowledge, patterns, and recommendations from all cluster nodes
to produce collective cluster intelligence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.cluster.knowledge_share import SharedKnowledge, ClusterKnowledgeShare
from sam.cluster.insight_broker import Insight, InsightBroker
from sam.cluster.strategy_sync import StrategyProposal, ClusterStrategySync

logger = structlog.get_logger()


class LearningAggregator:
    """Aggregates learning from all nodes into cluster-wide intelligence.

    Combines knowledge, patterns, recommendations, insights, and strategies
    from across the cluster.
    """

    def __init__(
        self,
        knowledge_share: ClusterKnowledgeShare,
        insight_broker: InsightBroker,
        strategy_sync: ClusterStrategySync,
    ) -> None:
        self._knowledge = knowledge_share
        self._insights = insight_broker
        self._strategies = strategy_sync
        self.logger = logger.bind(component="LearningAggregator")

    async def aggregate_knowledge(
        self,
        knowledge_type: str,
        min_confidence: float = 0.5,
    ) -> List[SharedKnowledge]:
        """Aggregate knowledge of a specific type with minimum confidence."""
        all_knowledge = await self._knowledge.get_shared(knowledge_type, limit=500)
        return [k for k in all_knowledge if k.confidence >= min_confidence]

    async def aggregate_patterns(
        self,
        pattern_type: str = "PATTERN",
        min_confidence: float = 0.6,
    ) -> List[SharedKnowledge]:
        """Aggregate patterns with minimum confidence."""
        patterns = await self._knowledge.get_shared(pattern_type, limit=500)
        return [p for p in patterns if p.confidence >= min_confidence]

    async def aggregate_recommendations(
        self,
        recommendation_type: str = "RECOMMENDATION",
        min_confidence: float = 0.5,
    ) -> List[SharedKnowledge]:
        """Aggregate recommendations with minimum confidence."""
        recs = await self._knowledge.get_shared(recommendation_type, limit=500)
        return [r for r in recs if r.confidence >= min_confidence]

    async def get_cluster_insight(
        self,
        insight_type: str,
    ) -> Option[List[Insight]]:
        """Get all insights of a specific type across the cluster."""
        return await self._insights.get_insights(
            insight_type=insight_type,
            limit=200,
        )

    async def update_cluster_knowledge(self) -> Dict[str, int]:
        """Periodic aggregation — merge and deduplicate cluster knowledge.

        Returns:
            Dict with counts of aggregated items per type.
        """
        result: Dict[str, int] = {}
        for kt in ("KNOWLEDGE", "PATTERN", "RECOMMENDATION"):
            items = await self._knowledge.get_shared(kt, limit=500)
            # Deduplication by content similarity is future work;
            # for now just count
            result[kt] = len(items)
        self.logger.info(
            "Cluster knowledge updated",
            knowledge=result.get("KNOWLEDGE", 0),
            patterns=result.get("PATTERN", 0),
            recommendations=result.get("RECOMMENDATION", 0),
        )
        return result
