"""Cross-Cluster Intelligence — Sprint 30.

Modules:
    knowledge_share: publish/subscribe knowledge across nodes
    insight_broker: manage insights from all nodes
    strategy_sync: propose/vote/adopt strategies
    cognitive_state: share cognitive state across cluster
    learning_aggregator: aggregate learning from all nodes
"""

from sam.cluster.knowledge_share import ClusterKnowledgeShare, SharedKnowledge
from sam.cluster.insight_broker import InsightBroker, Insight
from sam.cluster.strategy_sync import ClusterStrategySync, StrategyProposal
from sam.cluster.cognitive_state import (
    ClusterCognitiveStateManager,
    ClusterCognitiveState,
)
from sam.cluster.learning_aggregator import LearningAggregator

__all__ = [
    "ClusterCognitiveState",
    "ClusterCognitiveStateManager",
    "ClusterKnowledgeShare",
    "ClusterStrategySync",
    "Insight",
    "InsightBroker",
    "LearningAggregator",
    "SharedKnowledge",
    "StrategyProposal",
]
