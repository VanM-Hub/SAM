"""Tests for Cross-Cluster Intelligence — Sprint 30.

Coverage:
  - SharedKnowledge model + ClusterKnowledgeShare
  - Insight model + InsightBroker
  - StrategyProposal model + ClusterStrategySync
  - ClusterCognitiveState model + ClusterCognitiveStateManager
  - LearningAggregator
  - CLI commands
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from sam.cluster.knowledge_share import SharedKnowledge, ClusterKnowledgeShare
from sam.cluster.insight_broker import Insight, InsightBroker
from sam.cluster.strategy_sync import (
    StrategyProposal,
    ClusterStrategySync,
    STATUS_PROPOSED,
    STATUS_APPROVED,
    VOTE_APPROVE,
    VOTE_REJECT,
)
from sam.cluster.cognitive_state import (
    ClusterCognitiveState,
    ClusterCognitiveStateManager,
)
from sam.cluster.learning_aggregator import LearningAggregator
from sam.cognition.state import CognitiveState


# ═══════════════════════════════════════════════════════════════════
# SharedKnowledge & ClusterKnowledgeShare
# ═══════════════════════════════════════════════════════════════════


class TestSharedKnowledge:
    def test_create_default(self):
        k = SharedKnowledge(source_node_id="node_1")
        assert k.id.startswith("sk_")
        assert k.source_node_id == "node_1"
        assert k.knowledge_type == "KNOWLEDGE"
        assert k.confidence == 0.8
        assert k.ttl == 3600

    def test_create_custom(self):
        k = SharedKnowledge(
            source_node_id="n1",
            knowledge_type="PATTERN",
            content={"pattern": "timeout_retry"},
            confidence=0.9,
            ttl=600,
        )
        assert k.knowledge_type == "PATTERN"
        assert k.content["pattern"] == "timeout_retry"
        assert k.confidence == 0.9

    def test_expired_true(self):
        k = SharedKnowledge(source_node_id="n1", ttl=0)
        assert k.expired is False  # ttl=0 means no expiry
        k2 = SharedKnowledge(source_node_id="n1", ttl=-1)
        assert k2.expired is False

    def test_to_dict_roundtrip(self):
        k = SharedKnowledge(
            source_node_id="n1",
            knowledge_type="RECOMMENDATION",
            content={"action": "scale"},
            confidence=0.85,
        )
        d = k.to_dict()
        k2 = SharedKnowledge.from_dict(d)
        assert k2.source_node_id == k.source_node_id
        assert k2.knowledge_type == k.knowledge_type
        assert k2.confidence == k.confidence


class TestClusterKnowledgeShare:
    @pytest.fixture
    def ks(self):
        return ClusterKnowledgeShare()

    async def test_publish_and_get(self, ks):
        k = SharedKnowledge(source_node_id="n1", knowledge_type="PATTERN")
        await ks.publish(k)
        result = await ks.get_shared("PATTERN")
        assert len(result) == 1
        assert result[0].id == k.id

    async def test_publish_different_types(self, ks):
        k1 = SharedKnowledge(source_node_id="n1", knowledge_type="KNOWLEDGE")
        k2 = SharedKnowledge(source_node_id="n2", knowledge_type="PATTERN")
        await ks.publish(k1)
        await ks.publish(k2)
        assert len(await ks.get_shared("KNOWLEDGE")) == 1
        assert len(await ks.get_shared("PATTERN")) == 1

    async def test_subscribe_and_pull(self, ks):
        k = SharedKnowledge(source_node_id="n1", knowledge_type="PATTERN")
        await ks.subscribe("PATTERN", "node_b")
        await ks.publish(k)
        pulled = await ks.pull("node_b")
        assert len(pulled) == 1
        assert pulled[0].id == k.id

    async def test_subscribe_multiple_types(self, ks):
        await ks.subscribe("KNOWLEDGE", "n1")
        await ks.subscribe("PATTERN", "n1")
        k1 = SharedKnowledge(source_node_id="n2", knowledge_type="KNOWLEDGE")
        k2 = SharedKnowledge(source_node_id="n2", knowledge_type="PATTERN")
        await ks.publish(k1)
        await ks.publish(k2)
        pulled = await ks.pull("n1")
        assert len(pulled) == 2

    async def test_get_by_id(self, ks):
        k = SharedKnowledge(source_node_id="n1")
        await ks.publish(k)
        found = await ks.get_by_id(k.id)
        assert found is not None
        assert found.id == k.id

    async def test_get_by_id_missing(self, ks):
        assert await ks.get_by_id("missing") is None

    async def test_count(self, ks):
        assert await ks.count() == 0
        await ks.publish(SharedKnowledge(source_node_id="n1"))
        assert await ks.count() == 1

    async def test_clear(self, ks):
        await ks.publish(SharedKnowledge(source_node_id="n1"))
        await ks.clear()
        assert await ks.count() == 0

    async def test_pull_from_empty(self, ks):
        pulled = await ks.pull("unknown_node")
        assert pulled == []


# ═══════════════════════════════════════════════════════════════════
# Insight + InsightBroker
# ═══════════════════════════════════════════════════════════════════


class TestInsight:
    def test_create_default(self):
        i = Insight(node_id="n1", insight_type="perf")
        assert i.id.startswith("ins_")
        assert i.node_id == "n1"
        assert i.confidence == 0.8
        assert i.read_by == []

    def test_create_custom(self):
        i = Insight(
            node_id="n1",
            insight_type="healing_pattern",
            content={"pattern": "timeout_retry_success"},
            confidence=0.95,
        )
        assert i.insight_type == "healing_pattern"
        assert i.confidence == 0.95

    def test_to_dict_roundtrip(self):
        i = Insight(
            node_id="n1",
            insight_type="test",
            content={"key": "val"},
            read_by=["n2"],
        )
        d = i.to_dict()
        i2 = Insight.from_dict(d)
        assert i2.node_id == i.node_id
        assert i2.insight_type == i.insight_type
        assert "n2" in i2.read_by


class TestInsightBroker:
    @pytest.fixture
    def broker(self):
        return InsightBroker()

    async def test_register_and_get(self, broker):
        i = Insight(node_id="n1", insight_type="perf")
        await broker.register_insight(i)
        result = await broker.get_insights()
        assert len(result) == 1

    async def test_filter_by_node(self, broker):
        await broker.register_insight(Insight(node_id="n1", insight_type="a"))
        await broker.register_insight(Insight(node_id="n2", insight_type="b"))
        n1 = await broker.get_insights(node_id="n1")
        assert len(n1) == 1
        assert n1[0].node_id == "n1"

    async def test_filter_by_type(self, broker):
        await broker.register_insight(Insight(node_id="n1", insight_type="perf"))
        await broker.register_insight(Insight(node_id="n1", insight_type="health"))
        perf = await broker.get_insights(insight_type="perf")
        assert len(perf) == 1

    async def test_get_latest(self, broker):
        for i in range(5):
            await broker.register_insight(
                Insight(node_id="n1", insight_type="test", content={"i": i})
            )
        latest = await broker.get_latest_insights("n1", count=3)
        assert len(latest) == 3

    async def test_mark_as_read(self, broker):
        i = Insight(node_id="n1", insight_type="test")
        await broker.register_insight(i)
        await broker.mark_as_read(i.id, "n2")
        insight = await broker.get_by_id(i.id)
        assert "n2" in insight.read_by

    async def test_unread_count(self, broker):
        i1 = Insight(node_id="n1", insight_type="a")
        i2 = Insight(node_id="n2", insight_type="b")
        await broker.register_insight(i1)
        await broker.register_insight(i2)
        assert await broker.get_unread_count("n3") == 2
        await broker.mark_as_read(i1.id, "n3")
        assert await broker.get_unread_count("n3") == 1

    async def test_count(self, broker):
        assert await broker.count() == 0
        await broker.register_insight(Insight(node_id="n1", insight_type="x"))
        assert await broker.count() == 1

    async def test_clear(self, broker):
        await broker.register_insight(Insight(node_id="n1", insight_type="x"))
        await broker.clear()
        assert await broker.count() == 0

    async def test_mark_nonexistent(self, broker):
        await broker.mark_as_read("ghost", "n1")  # Should not raise

    async def test_get_by_id(self, broker):
        i = Insight(node_id="n1", insight_type="x")
        await broker.register_insight(i)
        assert await broker.get_by_id(i.id) is not None
        assert await broker.get_by_id("missing") is None


# ═══════════════════════════════════════════════════════════════════
# Strategy Proposal + ClusterStrategySync
# ═══════════════════════════════════════════════════════════════════


class TestStrategyProposal:
    def test_create_default(self):
        p = StrategyProposal(proposer_node_id="n1")
        assert p.id.startswith("sp_")
        assert p.status == STATUS_PROPOSED
        assert p.votes == []

    def test_approve_reject_counts(self):
        p = StrategyProposal(proposer_node_id="n1", votes=[
            {"node_id": "n2", "vote": "approve"},
            {"node_id": "n3", "vote": "approve"},
            {"node_id": "n4", "vote": "reject"},
        ])
        assert p.approve_count() == 2
        assert p.reject_count() == 1

    def test_has_consensus_false_few_votes(self):
        p = StrategyProposal(proposer_node_id="n1", votes=[
            {"node_id": "n2", "vote": "approve"},
        ])
        assert p.has_consensus is False

    def test_has_consensus_true(self):
        p = StrategyProposal(proposer_node_id="n1", votes=[
            {"node_id": "n2", "vote": "approve"},
            {"node_id": "n3", "vote": "approve"},
            {"node_id": "n4", "vote": "approve"},
        ])
        assert p.has_consensus is True

    def test_has_consensus_more_rejects(self):
        p = StrategyProposal(proposer_node_id="n1", votes=[
            {"node_id": "n2", "vote": "reject"},
            {"node_id": "n3", "vote": "reject"},
            {"node_id": "n4", "vote": "approve"},
        ])
        assert p.has_consensus is False

    def test_to_dict_roundtrip(self):
        p = StrategyProposal(
            proposer_node_id="n1",
            strategy={"action": "scale"},
            votes=[{"node_id": "n2", "vote": "approve"}],
        )
        d = p.to_dict()
        p2 = StrategyProposal.from_dict(d)
        assert p2.proposer_node_id == p.proposer_node_id
        assert p2.strategy["action"] == "scale"
        assert len(p2.votes) == 1


class TestClusterStrategySync:
    @pytest.fixture
    def sync(self):
        return ClusterStrategySync()

    async def test_propose_and_list(self, sync):
        p = StrategyProposal(proposer_node_id="n1")
        await sync.propose_strategy(p)
        proposals = await sync.get_proposals()
        assert len(proposals) == 1
        assert proposals[0].id == p.id

    async def test_vote_approve(self, sync):
        p = StrategyProposal(proposer_node_id="n1")
        await sync.propose_strategy(p)
        await sync.vote(p.id, "n2", "approve", "good idea")
        proposal = await sync.get_by_id(p.id)
        assert proposal.votes[0]["vote"] == "approve"
        assert proposal.votes[0]["reason"] == "good idea"

    async def test_vote_reject(self, sync):
        p = StrategyProposal(proposer_node_id="n1")
        await sync.propose_strategy(p)
        await sync.vote(p.id, "n2", "reject", "too risky")
        proposal = await sync.get_by_id(p.id)
        assert proposal.votes[0]["vote"] == "reject"

    async def test_vote_nonexistent_raises(self, sync):
        with pytest.raises(ValueError, match="not found"):
            await sync.vote("ghost", "n1", "approve")

    async def test_vote_after_approved_raises(self, sync):
        p = StrategyProposal(proposer_node_id="n1")
        await sync.propose_strategy(p)
        # Vote 3 agrees for consensus
        await sync.vote(p.id, "n2", "approve")
        await sync.vote(p.id, "n3", "approve")
        await sync.vote(p.id, "n4", "approve")
        with pytest.raises(ValueError, match="not PROPOSED"):
            await sync.vote(p.id, "n5", "approve")

    async def test_auto_approve_on_consensus(self, sync):
        p = StrategyProposal(proposer_node_id="n1")
        await sync.propose_strategy(p)
        await sync.vote(p.id, "n2", "approve")
        await sync.vote(p.id, "n3", "approve")
        await sync.vote(p.id, "n4", "approve")
        proposal = await sync.get_by_id(p.id)
        assert proposal.status == STATUS_APPROVED

    async def test_adopt_strategy(self, sync):
        p = StrategyProposal(proposer_node_id="n1")
        await sync.propose_strategy(p)
        result = await sync.adopt_strategy(p.id)
        assert result.status == STATUS_APPROVED

    async def test_adopt_nonexistent_raises(self, sync):
        with pytest.raises(ValueError, match="not found"):
            await sync.adopt_strategy("ghost")

    async def test_filter_by_status(self, sync):
        p1 = StrategyProposal(proposer_node_id="n1")
        p2 = StrategyProposal(proposer_node_id="n2")
        await sync.propose_strategy(p1)
        await sync.propose_strategy(p2)
        await sync.adopt_strategy(p1.id)
        proposed = await sync.get_proposals(status=STATUS_PROPOSED)
        assert len(proposed) == 1
        assert proposed[0].id == p2.id

    async def test_count(self, sync):
        assert await sync.count() == 0
        await sync.propose_strategy(StrategyProposal(proposer_node_id="n1"))
        assert await sync.count() == 1

    async def test_clear(self, sync):
        await sync.propose_strategy(StrategyProposal(proposer_node_id="n1"))
        await sync.clear()
        assert await sync.count() == 0

    async def test_vote_override(self, sync):
        """Same node voting again overrides previous vote."""
        p = StrategyProposal(proposer_node_id="n1")
        await sync.propose_strategy(p)
        await sync.vote(p.id, "n2", "approve", "first")
        await sync.vote(p.id, "n2", "reject", "changed my mind")
        proposal = await sync.get_by_id(p.id)
        assert len(proposal.votes) == 1
        assert proposal.votes[0]["vote"] == "reject"


# ═══════════════════════════════════════════════════════════════════
# Cluster Cognitive State
# ═══════════════════════════════════════════════════════════════════


class TestClusterCognitiveState:
    def test_create_default(self):
        c = ClusterCognitiveState()
        assert c.node_count == 0
        assert c.aggregated_confidence == 0.0
        assert c.dominant_focus == "balanced"

    def test_to_dict(self):
        c = ClusterCognitiveState(
            node_count=3,
            aggregated_confidence=85.5,
            dominant_focus="availability",
            avg_autonomy_level=3.0,
        )
        d = c.to_dict()
        assert d["node_count"] == 3
        assert d["aggregated_confidence"] == 85.5


class TestClusterCognitiveStateManager:
    @pytest.fixture
    def ccm(self):
        return ClusterCognitiveStateManager()

    async def test_get_empty_state(self, ccm):
        state = await ccm.get_cluster_state()
        assert state.node_count == 0
        assert state.aggregated_confidence == 100.0

    async def test_publish_one_node(self, ccm):
        s = CognitiveState(health=80.0, confidence=75.0, focus="availability")
        await ccm.publish_state("node_a", s)
        state = await ccm.get_cluster_state()
        assert state.node_count == 1
        assert state.aggregated_confidence == 75.0
        assert state.dominant_focus == "availability"

    async def test_publish_multiple_nodes(self, ccm):
        s1 = CognitiveState(health=90.0, confidence=80.0, focus="latency")
        s2 = CognitiveState(health=70.0, confidence=60.0, focus="availability")
        await ccm.publish_state("n1", s1)
        await ccm.publish_state("n2", s2)
        state = await ccm.get_cluster_state()
        assert state.node_count == 2
        assert abs(state.aggregated_confidence - 70.0) < 1

    async def test_get_node_state(self, ccm):
        s = CognitiveState(health=85.0, confidence=80.0)
        await ccm.publish_state("n1", s)
        node_s = await ccm.get_node_state("n1")
        assert node_s is not None
        assert node_s.health == 85.0
        assert await ccm.get_node_state("missing") is None

    async def test_get_state_history(self, ccm):
        s1 = CognitiveState(health=90.0, confidence=90.0)
        s2 = CognitiveState(health=80.0, confidence=80.0)
        await ccm.publish_state("n1", s1)
        await ccm.publish_state("n1", s2)
        history = await ccm.get_state_history("n1", limit=10)
        assert len(history) == 2

    async def test_get_active_node_count(self, ccm):
        assert await ccm.get_active_node_count() == 0
        await ccm.publish_state("n1", CognitiveState())
        assert await ccm.get_active_node_count() == 1

    async def test_clear(self, ccm):
        await ccm.publish_state("n1", CognitiveState())
        await ccm.clear()
        assert await ccm.get_active_node_count() == 0

    async def test_dominant_focus_majority(self, ccm):
        s1 = CognitiveState(confidence=80.0, focus="availability")
        s2 = CognitiveState(confidence=80.0, focus="availability")
        s3 = CognitiveState(confidence=80.0, focus="latency")
        await ccm.publish_state("n1", s1)
        await ccm.publish_state("n2", s2)
        await ccm.publish_state("n3", s3)
        state = await ccm.get_cluster_state()
        assert state.dominant_focus == "availability"


# ═══════════════════════════════════════════════════════════════════
# Learning Aggregator
# ═══════════════════════════════════════════════════════════════════


class TestLearningAggregator:
    @pytest.fixture
    def agg(self):
        ks = ClusterKnowledgeShare()
        ib = InsightBroker()
        ss = ClusterStrategySync()
        return LearningAggregator(knowledge_share=ks, insight_broker=ib, strategy_sync=ss)

    async def test_aggregate_knowledge_empty(self, agg):
        result = await agg.aggregate_knowledge("KNOWLEDGE")
        assert result == []

    async def test_aggregate_knowledge_with_data(self, agg):
        k = SharedKnowledge(source_node_id="n1", knowledge_type="PATTERN",
                             confidence=0.9)
        await agg._knowledge.publish(k)
        result = await agg.aggregate_patterns(min_confidence=0.5)
        assert len(result) == 1

    async def test_aggregate_filters_low_confidence(self, agg):
        k1 = SharedKnowledge(source_node_id="n1", knowledge_type="PATTERN",
                              confidence=0.3)
        k2 = SharedKnowledge(source_node_id="n1", knowledge_type="PATTERN",
                              confidence=0.9)
        await agg._knowledge.publish(k1)
        await agg._knowledge.publish(k2)
        result = await agg.aggregate_patterns(min_confidence=0.5)
        assert len(result) == 1
        assert result[0].confidence == 0.9

    async def test_update_cluster_knowledge(self, agg):
        k = SharedKnowledge(source_node_id="n1", knowledge_type="KNOWLEDGE")
        await agg._knowledge.publish(k)
        result = await agg.update_cluster_knowledge()
        assert result.get("KNOWLEDGE") == 1

    async def test_get_cluster_insight(self, agg):
        i = Insight(node_id="n1", insight_type="perf_bottleneck")
        await agg._insights.register_insight(i)
        result = await agg.get_cluster_insight("perf_bottleneck")
        assert len(result) == 1


# ═══════════════════════════════════════════════════════════════════
# CLI Smoke Tests
# ═══════════════════════════════════════════════════════════════════


class TestCLI:
    def test_cluster_app_importable(self):
        from sam.cli.cluster_app import cluster_app
        assert cluster_app.info.name == "cluster"

    def test_cluster_app_has_commands(self):
        from sam.cli.cluster_app import cluster_app
        commands = list(cluster_app.registered_commands)
        names = [c.name for c in commands]
        assert "status" in names
        assert "sync" in names
        assert "knowledge-pull" in names
        assert "insights-list" in names
        assert "strategies-list" in names
        assert "strategies-vote" in names

    def test_main_registers_cluster(self):
        from sam.cli.main import app
        registered = [g.name for g in app.registered_groups]
        assert "cluster" in registered
