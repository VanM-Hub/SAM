from __future__ import annotations

import time

import pytest

from sam.operations.brain.orchestrator import MissionOrchestrator
from sam.operations.brain.proposal_queue import ProposalQueue, ProposalState, InvalidTransitionError
from sam.operations.brain.health import evaluate_health
from sam.operations.brain.conversation_v2 import BrainConversationBridgeV2, ConversationContext
from sam.operations.brain.integration_v2 import run_proactive_pipeline


def test_orchestrator_auto_package_critical_separation():
    orchestrator = MissionOrchestrator()
    recommendations = [
        {"id": "r1", "recommendation_id": "r1", "title": "Fix A", "priority": "critical", "affected_resources": ["svc-a"]},
        {"id": "r2", "recommendation_id": "r2", "title": "Fix B", "priority": "high", "affected_resources": ["svc-a", "svc-b"]},
        {"id": "r3", "recommendation_id": "r3", "title": "Tidy C", "priority": "low", "affected_resources": ["svc-c"]},
    ]
    scores = [{"item_id": "r1", "score": 0.95}, {"item_id": "r2", "score": 0.6}]

    packages = orchestrator.auto_package(recommendations, scores)
    assert isinstance(packages, list)
    # critical should be separated into its own package when separate_critical True
    critical_pkgs = [p for p in packages if any(pid == "r1" for pid in p.member_ids)]
    assert critical_pkgs, "Critical recommendation r1 should appear in a package"
    # combined priority for the package containing r1 should be 'critical'
    assert any(p.combined_priority == "critical" for p in critical_pkgs)


def test_proposal_queue_transitions_and_expiry():
    q = ProposalQueue(default_ttl=1.0)
    item = q.add("Test Proposal", description="desc", priority_score=0.5)
    assert item.state == ProposalState.DRAFT

    q.finalize(item.proposal_id)
    assert q.get(item.proposal_id).state == ProposalState.READY

    q.submit(item.proposal_id)
    assert q.get(item.proposal_id).state == ProposalState.WAITING_APPROVAL

    # simulate time passing beyond TTL
    qi = q.get(item.proposal_id)
    qi.updated_at = time.time() - 5.0

    expired_count = q.expire_stale()
    assert expired_count >= 1
    assert q.get(item.proposal_id).state in (ProposalState.EXPIRED, ProposalState.ARCHIVED)

    # invalid transition: approving expired item should raise
    with pytest.raises(InvalidTransitionError):
        q.approve(item.proposal_id)


def test_health_engine_basic_evaluation():
    source_data = {
        "missions": {"active": 2, "failed": 1, "total": 10},
        "approvals": {"pending": 8, "total": 50},
        "trust": {"overall": 0.55, "components_below_threshold": 1},
        "scheduler": {"queue_length": 15, "stalled": 0},
        "health": {"downtime_seconds": 30},
        "replay": {"success_rate": 0.9, "failed": 0},
        "benchmark": {"error_rate": 0.02},
        "audit": {"overridden": 1, "total_decisions": 20},
    }
    h = evaluate_health(source_data)
    assert 0.0 <= h.score <= 1.0
    assert h.status in ("healthy", "degraded", "unhealthy")
    assert "approval" in h.dimensions
    assert "mission" in h.dimensions


def test_conversation_v2_status_and_biggest_problem():
    bridge = BrainConversationBridgeV2()
    ctx = ConversationContext(
        findings=[{"finding_id": "f1", "title": "DB down", "description": "Database connection failures", "severity": "critical", "confidence": 0.9}],
        recommendations=[{"id": "r1", "title": "Restart DB", "priority": "critical", "confidence": 0.9}],
        proposals=[{"proposal_id": "p1", "title": "Restart DB Proposal", "state": "waiting_approval"}],
        correlated_findings=[],
        priority_scores=[],
        packages=[],
        health={"score": 0.4, "status": "degraded"},
        observation={"active_missions": 1, "pending_approvals": 2, "anomalies": 0},
    )
    bridge.update_context(findings=ctx.findings, recommendations=ctx.recommendations, proposals=ctx.proposals, health=ctx.health, observation=ctx.observation)

    status_ans = bridge.ask("status")
    assert hasattr(status_ans, "answer")
    assert "System Status" in status_ans.answer or "Health" in status_ans.answer

    biggest = bridge.ask("What's the biggest problem?")
    assert hasattr(biggest, "answer")
    assert "DB down" in biggest.answer or "Database" in biggest.answer


def test_integration_run_proactive_pipeline_smoke():
    result = run_proactive_pipeline()
    assert hasattr(result, "pipeline_elapsed_ms")
    assert isinstance(result.findings, list)
    assert isinstance(result.recommendations, list)
    assert isinstance(result.packages, list)
    assert result.pipeline_elapsed_ms >= 0

