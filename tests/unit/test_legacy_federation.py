"""Tests for Knowledge Federation — Sprint 31.

Coverage:
  - Federation Manager: cluster registration, lifecycle
  - Protocol: offers, requests, messages
  - Trust: scoring, adjustments, decay
  - Conflict Resolution: 5 strategies
  - Provenance: registration, verification
  - Consensus: weighted, simple majority
  - Sovereignty: policies, access control
"""

import pytest

from sam.federation.manager import (
    FederationManager,
    FederatedCluster,
    CLUSTER_STATUS_ONLINE,
    CLUSTER_STATUS_OFFLINE,
)
from sam.federation.protocol import (
    FederationProtocol,
    KnowledgeOffer,
    KnowledgeRequest,
    FederationMessage,
    MESSAGE_TYPE_OFFER,
    MESSAGE_TYPE_REQUEST,
)
from sam.federation.trust import TrustManager, ClusterTrust
from sam.federation.conflict import (
    ConflictResolver,
    ConflictResult,
    RESOLUTION_ACCEPT_FIRST,
    RESOLUTION_ACCEPT_HIGHER_CONFIDENCE,
    RESOLUTION_ACCEPT_HIGHER_TRUST,
    RESOLUTION_MERGE,
    RESOLUTION_REJECT_BOTH,
)
from sam.federation.provenance import Provenance, ProvenanceManager
from sam.federation.consensus import ConsensusEngine, ConsensusVote
from sam.federation.sovereignty import (
    SovereigntyManager,
    SovereigntyPolicy,
    SharingPolicy,
    POLICY_PUBLIC,
    POLICY_INTERNAL,
    POLICY_RESTRICTED,
)


# ═══════════════════════════════════════════════════════════════════
# Federation Manager
# ═══════════════════════════════════════════════════════════════════


class TestFederatedCluster:
    def test_create_default(self):
        c = FederatedCluster(name="test-cluster", endpoint="http://cluster:8080")
        assert c.id.startswith("fc_")
        assert c.status == CLUSTER_STATUS_ONLINE
        assert c.trust_score == 0.5

    def test_to_dict_roundtrip(self):
        c = FederatedCluster(id="fc_1", name="n1", endpoint="http://e", trust_score=0.8)
        d = c.to_dict()
        c2 = FederatedCluster.from_dict(d)
        assert c2.id == c.id
        assert c2.trust_score == c.trust_score


class TestFederationManager:
    @pytest.fixture
    def fm(self):
        return FederationManager(local_cluster_id="local_cluster")

    async def test_register(self, fm):
        c = await fm.register_cluster("peer_1", "Peer 1", "http://peer1")
        assert c.id == "peer_1"
        assert c.status == CLUSTER_STATUS_ONLINE
        assert await fm.count() == 1

    async def test_register_updates_existing(self, fm):
        await fm.register_cluster("p1", "P1", "http://p1")
        await fm.register_cluster("p1", "P1 Updated", "http://p1-new")
        c = await fm.get_cluster("p1")
        assert c.name == "P1 Updated"

    async def test_unregister(self, fm):
        await fm.register_cluster("p1", "P1", "http://p1")
        await fm.unregister_cluster("p1")
        assert await fm.get_cluster("p1") is None

    async def test_list_clusters(self, fm):
        await fm.register_cluster("p1", "P1", "http://p1")
        await fm.register_cluster("p2", "P2", "http://p2")
        assert len(await fm.list_clusters()) == 2

    async def test_list_by_status(self, fm):
        await fm.register_cluster("p1", "P1", "http://p1")
        await fm.register_cluster("p2", "P2", "http://p2")
        await fm.mark_offline("p2")
        online = await fm.list_clusters(status=CLUSTER_STATUS_ONLINE)
        assert len(online) == 1

    async def test_heartbeat(self, fm):
        await fm.register_cluster("p1", "P1", "http://p1")
        await fm.mark_offline("p1")
        await fm.update_heartbeat("p1")
        c = await fm.get_cluster("p1")
        assert c.status == CLUSTER_STATUS_ONLINE

    async def test_blacklist(self, fm):
        await fm.blacklist_cluster("bad_node")
        assert await fm.is_blacklisted("bad_node") is True
        assert await fm.is_blacklisted("good_node") is False

    async def test_get_local_id(self, fm):
        assert await fm.get_local_cluster_id() == "local_cluster"

    async def test_clear(self, fm):
        await fm.register_cluster("p1", "P1", "http://p1")
        await fm.clear()
        assert await fm.count() == 0

    async def test_get_nonexistent(self, fm):
        assert await fm.get_cluster("ghost") is None


# ═══════════════════════════════════════════════════════════════════
# Protocol
# ═══════════════════════════════════════════════════════════════════


class TestKnowledgeOffer:
    def test_create(self):
        o = KnowledgeOffer(source_cluster_id="c1", insight_type="PATTERN")
        assert o.id.startswith("ko_")
        assert o.sovereignty_policy == "PUBLIC"
        assert o.freshness == 1.0

    def test_to_dict(self):
        o = KnowledgeOffer(source_cluster_id="c1", insight_type="RECOMMENDATION")
        d = o.to_dict()
        assert d["source_cluster_id"] == "c1"


class TestKnowledgeRequest:
    def test_create(self):
        r = KnowledgeRequest(requester_cluster_id="c1", insight_type="PATTERN")
        assert r.id.startswith("kr_")
        assert r.min_confidence == 0.5


class TestFederationProtocol:
    @pytest.fixture
    def proto(self):
        return FederationProtocol()

    async def test_send_offer(self, proto):
        offer = KnowledgeOffer(source_cluster_id="c1", target_cluster_id="c2")
        msg = await proto.send_offer(offer)
        assert msg.message_type == MESSAGE_TYPE_OFFER
        assert msg.source_cluster_id == "c1"

    async def test_send_request(self, proto):
        req = KnowledgeRequest(requester_cluster_id="c1", insight_type="PATTERN")
        msg = await proto.send_request(req)
        assert msg.message_type == MESSAGE_TYPE_REQUEST

    async def test_get_messages(self, proto):
        offer = KnowledgeOffer(source_cluster_id="c1", target_cluster_id="c2")
        await proto.send_offer(offer)
        msgs = await proto.get_messages("c2")
        assert len(msgs) == 1
        assert msgs[0].source_cluster_id == "c1"

    async def test_get_messages_all(self, proto):
        offer = KnowledgeOffer(source_cluster_id="c1", target_cluster_id="ALL")
        await proto.send_offer(offer)
        msgs = await proto.get_messages("c3")
        assert len(msgs) == 1

    async def test_clear(self, proto):
        offer = KnowledgeOffer(source_cluster_id="c1", target_cluster_id="ALL")
        await proto.send_offer(offer)
        await proto.clear()
        assert len(await proto.get_messages("c1")) == 0


# ═══════════════════════════════════════════════════════════════════
# Trust
# ═══════════════════════════════════════════════════════════════════


class TestTrustManager:
    @pytest.fixture
    def tm(self):
        return TrustManager()

    async def test_get_trust_default(self, tm):
        trust = await tm.get_trust("c1")
        assert trust.trust_score == 0.5
        assert trust.interactions == 0

    async def test_record_success(self, tm):
        trust = await tm.record_interaction("c1", success=True, reason="good data")
        assert trust.interactions == 1
        assert trust.successful_interactions == 1
        assert trust.trust_score > 0.5

    async def test_record_failure(self, tm):
        trust = await tm.record_interaction("c1", success=False, reason="bad data")
        assert trust.interactions == 1
        assert trust.successful_interactions == 0
        assert trust.trust_score < 0.5

    async def test_success_rate(self, tm):
        await tm.record_interaction("c1", success=True)
        await tm.record_interaction("c1", success=True)
        await tm.record_interaction("c1", success=False)
        trust = await tm.get_trust("c1")
        assert trust.success_rate == 2 / 3

    async def test_decay(self, tm):
        await tm.record_interaction("c1", success=True)
        before = (await tm.get_trust("c1")).trust_score
        await tm.apply_decay(days=10)
        after = (await tm.get_trust("c1")).trust_score
        assert after < before

    async def test_get_all(self, tm):
        await tm.record_interaction("c1", success=True)
        await tm.record_interaction("c2", success=False)
        all_t = await tm.get_all_trusts()
        assert len(all_t) == 2

    async def test_clear(self, tm):
        await tm.record_interaction("c1", success=True)
        await tm.clear()
        assert len(await tm.get_all_trusts()) == 0

    async def test_bounds_not_exceeded(self, tm):
        for _ in range(100):
            await tm.record_interaction("c1", success=True)
        trust = await tm.get_trust("c1")
        assert trust.trust_score <= 1.0


# ═══════════════════════════════════════════════════════════════════
# Conflict Resolution
# ═══════════════════════════════════════════════════════════════════


class TestConflictResolver:
    @pytest.fixture
    def resolver(self):
        return ConflictResolver(TrustManager())

    async def test_empty_candidates(self, resolver):
        result = await resolver.resolve([])
        assert result.reason == "No candidates provided"

    async def test_single_candidate(self, resolver):
        result = await resolver.resolve([{"id": "i1", "cluster_id": "c1", "confidence": 0.9}])
        assert result.winner_id == "i1"
        assert result.resolution_strategy == "single_candidate"

    async def test_accept_first(self, resolver):
        result = await resolver.resolve([
            {"id": "i1", "cluster_id": "c1", "confidence": 0.5},
            {"id": "i2", "cluster_id": "c2", "confidence": 0.9},
        ], strategy=RESOLUTION_ACCEPT_FIRST)
        assert result.winner_id == "i1"
        assert result.resolution_strategy == RESOLUTION_ACCEPT_FIRST

    async def test_accept_higher_confidence(self, resolver):
        result = await resolver.resolve([
            {"id": "i1", "cluster_id": "c1", "confidence": 0.5},
            {"id": "i2", "cluster_id": "c2", "confidence": 0.9},
        ], strategy=RESOLUTION_ACCEPT_HIGHER_CONFIDENCE)
        assert result.winner_id == "i2"
        assert result.winner_confidence == 0.9

    async def test_accept_higher_trust(self, resolver):
        """If confidence equal, trust decides."""
        tm = TrustManager()
        await tm.record_interaction("c1", success=True, reason="reliable")
        await tm.record_interaction("c1", success=True, reason="reliable again")
        resolver2 = ConflictResolver(tm)
        result = await resolver2.resolve([
            {"id": "i1", "cluster_id": "c1", "confidence": 0.7},
            {"id": "i2", "cluster_id": "c2", "confidence": 0.7},  # lower trust
        ], strategy=RESOLUTION_ACCEPT_HIGHER_TRUST)
        assert result.winner_id == "i1"  # c1 has higher trust

    async def test_merge(self, resolver):
        result = await resolver.resolve([
            {"id": "i1", "cluster_id": "c1", "confidence": 0.8},
            {"id": "i2", "cluster_id": "c2", "confidence": 0.6},
        ], strategy=RESOLUTION_MERGE)
        assert result.resolution_strategy == RESOLUTION_MERGE
        assert abs(result.winner_confidence - 0.7) < 0.01

    async def test_reject_both(self, resolver):
        result = await resolver.resolve([
            {"id": "i1", "cluster_id": "c1", "confidence": 0.5},
            {"id": "i2", "cluster_id": "c2", "confidence": 0.4},
        ], strategy=RESOLUTION_REJECT_BOTH)
        assert result.winner_id == ""

    async def test_confidence_gap(self, resolver):
        result = await resolver.resolve([
            {"id": "i1", "cluster_id": "c1", "confidence": 0.9},
            {"id": "i2", "cluster_id": "c2", "confidence": 0.5},
        ])
        assert result.confidence_gap == 0.4


# ═══════════════════════════════════════════════════════════════════
# Provenance
# ═══════════════════════════════════════════════════════════════════


class TestProvenance:
    def test_create(self):
        p = Provenance(origin_cluster_id="c1", evidence_ids=["e1", "e2"])
        assert p.origin_cluster_id == "c1"
        assert len(p.evidence_ids) == 2

    def test_to_dict_roundtrip(self):
        p = Provenance(
            origin_cluster_id="c1",
            origin_node_id="n1",
            confidence_at_origin=0.95,
        )
        d = p.to_dict()
        p2 = Provenance.from_dict(d)
        assert p2.origin_cluster_id == p.origin_cluster_id
        assert p2.confidence_at_origin == p.confidence_at_origin


class TestProvenanceManager:
    @pytest.fixture
    def pm(self):
        return ProvenanceManager()

    async def test_register_and_get(self, pm):
        p = Provenance(origin_cluster_id="c1")
        await pm.register("insight_1", p)
        result = await pm.get("insight_1")
        assert result is not None
        assert result.origin_cluster_id == "c1"

    async def test_verify_exists(self, pm):
        p = Provenance(origin_cluster_id="c1")
        await pm.register("insight_1", p)
        assert await pm.verify("insight_1") is True
        assert await pm.verify("missing") is False

    async def test_count(self, pm):
        assert await pm.count() == 0
        await pm.register("i1", Provenance(origin_cluster_id="c1"))
        assert await pm.count() == 1

    async def test_clear(self, pm):
        await pm.register("i1", Provenance(origin_cluster_id="c1"))
        await pm.clear()
        assert await pm.count() == 0


# ═══════════════════════════════════════════════════════════════════
# Consensus
# ═══════════════════════════════════════════════════════════════════


class TestConsensusEngine:
    @pytest.fixture
    def engine(self):
        return ConsensusEngine(TrustManager())

    async def test_no_votes(self, engine):
        result = await engine.compute_weighted_consensus([])
        assert result["winner"] == ""

    async def test_single_vote(self, engine):
        votes = [ConsensusVote(cluster_id="c1", option="A", confidence=0.9)]
        result = await engine.compute_weighted_consensus(votes)
        assert result["winner"] == "A"

    async def test_majority_wins(self, engine):
        votes = [
            ConsensusVote(cluster_id="c1", option="A", confidence=0.8),
            ConsensusVote(cluster_id="c2", option="A", confidence=0.7),
            ConsensusVote(cluster_id="c3", option="B", confidence=0.9),
        ]
        result = await engine.compute_weighted_consensus(votes)
        assert result["winner"] == "A"

    async def test_simple_majority(self, engine):
        votes = [
            ConsensusVote(cluster_id="c1", option="A", confidence=0.8),
            ConsensusVote(cluster_id="c2", option="B", confidence=0.7),
            ConsensusVote(cluster_id="c3", option="A", confidence=0.6),
        ]
        result = await engine.simple_majority(votes)
        assert result["winner"] == "A"
        assert result["options"]["A"] == 2

    async def test_tie_in_simple_majority(self, engine):
        votes = [
            ConsensusVote(cluster_id="c1", option="A", confidence=0.8),
            ConsensusVote(cluster_id="c2", option="B", confidence=0.8),
        ]
        result = await engine.simple_majority(votes)
        assert result["winner"] in ("A", "B")

    async def test_weighted_consensus_trust_matters(self, engine):
        # c1 = high trust, c2 = low trust
        tm = engine._trust
        await tm.record_interaction("c1", success=True, reason="reliable")
        await tm.record_interaction("c1", success=True, reason="reliable")
        await tm.record_interaction("c2", success=False, reason="unreliable")

        votes = [
            ConsensusVote(cluster_id="c1", option="A", confidence=0.7),
            ConsensusVote(cluster_id="c2", option="B", confidence=0.9),
        ]
        result = await engine.compute_weighted_consensus(votes)
        # c1 has much higher trust, so A should win despite lower confidence
        assert result["winner"] == "A"


# ═══════════════════════════════════════════════════════════════════
# Sovereignty
# ═══════════════════════════════════════════════════════════════════


class TestSovereigntyManager:
    @pytest.fixture
    def sm(self):
        return SovereigntyManager()

    async def test_public_access(self, sm):
        policy = SovereigntyPolicy(
            knowledge_type="PATTERN",
            sharing_policy=POLICY_PUBLIC,
        )
        await sm.set_policy(policy)
        access = await sm.check_access("PATTERN", "any_cluster")
        assert access.can_view is True
        assert access.can_redistribute is True

    async def test_internal_access(self, sm):
        policy = SovereigntyPolicy(
            knowledge_type="INTERNAL_KNOWLEDGE",
            sharing_policy=POLICY_INTERNAL,
        )
        await sm.set_policy(policy)
        access = await sm.check_access("INTERNAL_KNOWLEDGE", "any_cluster")
        assert access.can_view is True
        assert access.can_redistribute is False

    async def test_restricted_access_allowed(self, sm):
        policy = SovereigntyPolicy(
            knowledge_type="SECRET",
            sharing_policy=POLICY_RESTRICTED,
            allowed_clusters=["trusted_cluster"],
        )
        await sm.set_policy(policy)
        access = await sm.check_access("SECRET", "trusted_cluster")
        assert access.can_view is True
        access2 = await sm.check_access("SECRET", "untrusted_cluster")
        assert access2.can_view is False

    async def test_default_public(self, sm):
        access = await sm.check_access("UNKNOWN_TYPE", "any_cluster")
        assert access.can_view is True

    async def test_set_default_policy(self, sm):
        restricted = SovereigntyPolicy(
            id="global_restrict",
            sharing_policy=POLICY_RESTRICTED,
            allowed_clusters=[],
        )
        await sm.set_default_policy(restricted)
        access = await sm.check_access("ANY", "stranger")
        assert access.can_view is False

    async def test_list_policies(self, sm):
        await sm.set_policy(SovereigntyPolicy(
            knowledge_type="A", sharing_policy=POLICY_PUBLIC,
        ))
        await sm.set_policy(SovereigntyPolicy(
            knowledge_type="B", sharing_policy=POLICY_INTERNAL,
        ))
        assert len(await sm.list_policies()) == 2

    async def test_get_policies_for_cluster(self, sm):
        await sm.set_policy(SovereigntyPolicy(
            cluster_id="c1", knowledge_type="X", sharing_policy=POLICY_PUBLIC,
        ))
        await sm.set_policy(SovereigntyPolicy(
            cluster_id="c1", knowledge_type="Y", sharing_policy=POLICY_INTERNAL,
        ))
        c1_policies = await sm.get_policies_for_cluster("c1")
        assert len(c1_policies) == 2

    async def test_clear(self, sm):
        await sm.set_policy(SovereigntyPolicy(
            knowledge_type="X", sharing_policy=POLICY_PUBLIC,
        ))
        await sm.clear()
        assert len(await sm.list_policies()) == 0
