"""
Sprint 27 — Guardian Supervisory Runtime Tests

OP-321 through OP-328
"""

import pytest
from datetime import datetime
from sam.operations.brain.guardian import (
    GuardianSupervisor,
    GuardianSupervisorSnapshot,
    ReasoningStatus,
    DecisionStatus,
    BrainStatus,
    MissionStatus,
    SchedulerStatus,
    ProviderStatus,
    GuardianHealthEngine,
    HealthSummary,
    HealthScore,
    HealthIssue,
    GuardianWatchdog,
    GuardianAlert,
    GuardianWarning,
    GuardianIncident,
    GuardianPolicyEvaluator,
    PolicyViolation,
    GuardianRecommendationEngine,
    GuardianRecommendation,
    GuardianSupervisoryConversation,
    GuardianSupervisoryDashboardService,
    GuardianSupervisoryRuntimeIntegration,
)


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════

@pytest.fixture
def supervisor():
    return GuardianSupervisor()


@pytest.fixture
def health_engine():
    return GuardianHealthEngine()


@pytest.fixture
def watchdog():
    return GuardianWatchdog()


@pytest.fixture
def policy_evaluator():
    return GuardianPolicyEvaluator()


@pytest.fixture
def recommendation_engine():
    return GuardianRecommendationEngine()


@pytest.fixture
def conversation(supervisor, health_engine, watchdog, policy_evaluator, recommendation_engine):
    return GuardianSupervisoryConversation(
        health_engine, supervisor, watchdog, policy_evaluator, recommendation_engine,
    )


@pytest.fixture
def dashboard_service(health_engine, supervisor, watchdog, policy_evaluator, recommendation_engine, conversation):
    return GuardianSupervisoryDashboardService(
        health_engine, supervisor, watchdog, policy_evaluator, recommendation_engine, conversation,
    )


@pytest.fixture
def runtime_integration(supervisor, health_engine, watchdog, policy_evaluator, recommendation_engine, conversation, dashboard_service):
    return GuardianSupervisoryRuntimeIntegration(
        supervisor, health_engine, watchdog, policy_evaluator, recommendation_engine,
        conversation, dashboard_service,
    )


# ══════════════════════════════════════════════════════════════════════
# OP-321: Guardian Supervisor
# ══════════════════════════════════════════════════════════════════════

class TestGuardianSupervisor:

    def test_collect_returns_snapshot(self, supervisor):
        snap = supervisor.collect()
        assert isinstance(snap, GuardianSupervisorSnapshot)
        assert snap.timestamp != ""

    def test_latest_returns_none_when_empty(self, supervisor):
        assert supervisor.latest() is None

    def test_latest_returns_last_snapshot(self, supervisor):
        snap1 = supervisor.collect()
        snap2 = supervisor.collect(
            reasoning=ReasoningStatus(active_sessions=5, completed_count=10),
        )
        latest = supervisor.latest()
        assert latest is snap2
        assert latest.reasoning.active_sessions == 5

    def test_history_limited(self, supervisor):
        for _ in range(60):
            supervisor.collect()
        assert supervisor.snapshot_count == 50

    def test_has_overall_issues_scheduler_overloaded(self, supervisor):
        supervisor.collect(scheduler=SchedulerStatus(overloaded=True))
        assert supervisor.has_overall_issues is True

    def test_has_overall_issues_stalled_missions(self, supervisor):
        supervisor.collect(mission=MissionStatus(stalled_missions=2))
        assert supervisor.has_overall_issues is True

    def test_has_overall_issues_no_issues(self, supervisor):
        supervisor.collect()
        assert supervisor.has_overall_issues is False

    def test_snapshot_to_dict(self, supervisor):
        snap = supervisor.collect(
            reasoning=ReasoningStatus(active_sessions=3, failed_count=1),
        )
        d = snap.to_dict()
        assert d["reasoning"]["active_sessions"] == 3
        assert d["reasoning"]["failed_count"] == 1
        assert "timestamp" in d

    def test_clear(self, supervisor):
        supervisor.collect()
        supervisor.collect()
        assert supervisor.snapshot_count == 2
        supervisor.clear()
        assert supervisor.snapshot_count == 0

    def test_has_overall_issues_providers_degraded(self, supervisor):
        supervisor.collect(provider=ProviderStatus(degraded_providers=2))
        assert supervisor.has_overall_issues is True


# ══════════════════════════════════════════════════════════════════════
# OP-322: Guardian Health Engine
# ══════════════════════════════════════════════════════════════════════

class TestGuardianHealthEngine:

    def test_evaluate_healthy(self, health_engine):
        summary = health_engine.evaluate()
        assert summary.status == "healthy"
        assert summary.score.overall_score == 1.0
        assert len(summary.issues) == 0

    def test_evaluate_critical_providers(self, health_engine):
        summary = health_engine.evaluate(provider_healthy=0, provider_degraded=0)
        assert summary.status == "critical"
        assert summary.score.provider_score == 0.0

    def test_evaluate_critical_scheduler(self, health_engine):
        summary = health_engine.evaluate(scheduler_overloaded=True)
        # scheduler_score == 0.3 -> min_score == 0.3 -> critical
        assert summary.status == "critical"
        assert summary.score.scheduler_score < 0.5

    def test_evaluate_high_approval_backlog(self, health_engine):
        summary = health_engine.evaluate(approval_backlog=25)
        assert summary.status != "healthy"
        assert summary.score.approval_score < 0.5

    def test_evaluate_degraded_trust(self, health_engine):
        summary = health_engine.evaluate(trust_level=0.3)
        assert summary.status != "healthy"
        assert summary.score.trust_score == 0.3

    def test_evaluate_queue_critical(self, health_engine):
        summary = health_engine.evaluate(queue_depth=100)
        assert summary.score.queue_score < 0.5

    def test_latest_returns_none(self, health_engine):
        assert health_engine.latest() is None

    def test_latest_after_evaluate(self, health_engine):
        summary = health_engine.evaluate()
        assert health_engine.latest() is summary

    def test_history(self, health_engine):
        for _ in range(5):
            health_engine.evaluate()
        assert len(health_engine.history()) == 5

    def test_dto_immutable(self, health_engine):
        summary = health_engine.evaluate()
        with pytest.raises(Exception):
            summary.score.overall_score = 0.5


# ══════════════════════════════════════════════════════════════════════
# OP-323: Guardian Watchdog
# ══════════════════════════════════════════════════════════════════════

class TestGuardianWatchdog:

    def test_stuck_reasoning_detected(self, watchdog):
        alert = watchdog.check_stuck_reasoning(
            reasoning_sessions=1,
            reasoning_max_duration_ms=120000.0,
            threshold_ms=60000.0,
        )
        assert alert is not None
        assert alert.alert_type == "stuck_reasoning"
        assert alert.severity == "critical"

    def test_stuck_reasoning_not_detected(self, watchdog):
        alert = watchdog.check_stuck_reasoning(
            reasoning_sessions=0,
            reasoning_max_duration_ms=30000.0,
        )
        assert alert is None

    def test_provider_timeout_detected(self, watchdog):
        warn = watchdog.check_provider_timeout(provider_errors=5, error_threshold=3)
        assert warn is not None
        assert warn.warning_type == "provider_timeout"

    def test_provider_timeout_not_detected(self, watchdog):
        warn = watchdog.check_provider_timeout(provider_errors=1)
        assert warn is None

    def test_approval_deadlock_detected(self, watchdog):
        alert = watchdog.check_approval_deadlock(
            pending_approvals=5,
            stale_hours=48.0,
            stale_threshold=24.0,
        )
        assert alert is not None
        assert alert.alert_type == "approval_deadlock"

    def test_queue_starvation_detected(self, watchdog):
        warn = watchdog.check_queue_starvation(
            queue_depth=100, queue_processed=0, starve_threshold=50,
        )
        assert warn is not None
        assert warn.warning_type == "queue_starvation"

    def test_mission_stall_detected(self, watchdog):
        alert = watchdog.check_mission_stall(stalled_missions=3, active_missions=4)
        assert alert is not None
        assert alert.alert_type == "mission_stall"

    def test_retry_loop_detected(self, watchdog):
        warn = watchdog.check_retry_loop(retry_count=10, retry_threshold=5)
        assert warn is not None
        assert warn.warning_type == "retry_loop"

    def test_scheduler_overload_detected(self, watchdog):
        alert = watchdog.check_scheduler_overload(
            tasks_queued=200, scheduler_capacity=100,
        )
        assert alert is not None
        assert alert.alert_type == "scheduler_overload"

    def test_repeated_failures_detected(self, watchdog):
        incident = watchdog.check_repeated_failures(
            failure_count=10, failure_threshold=10,
        )
        assert incident is not None
        assert incident.incident_type == "repeated_failures"

    def test_properties(self, watchdog):
        watchdog.check_stuck_reasoning(1, 120000.0)
        watchdog.check_provider_timeout(5, 3)
        watchdog.check_repeated_failures(10, 10)
        assert len(watchdog.alerts) >= 1
        assert len(watchdog.warnings) >= 1
        assert len(watchdog.incidents) >= 1

    def test_clear(self, watchdog):
        watchdog.check_stuck_reasoning(1, 120000.0)
        assert len(watchdog.alerts) > 0
        watchdog.clear()
        assert len(watchdog.alerts) == 0
        assert len(watchdog.warnings) == 0
        assert len(watchdog.incidents) == 0


# ══════════════════════════════════════════════════════════════════════
# OP-324: Guardian Policy Evaluator
# ══════════════════════════════════════════════════════════════════════

class TestGuardianPolicyEvaluator:

    def test_no_auto_execution_passed(self, policy_evaluator):
        result = policy_evaluator.evaluate_no_auto_execution(False)
        assert result.passed is True

    def test_no_auto_execution_failed(self, policy_evaluator):
        result = policy_evaluator.evaluate_no_auto_execution(True)
        assert result.passed is False

    def test_approval_required_passed(self, policy_evaluator):
        result = policy_evaluator.evaluate_approval_required(True, 0)
        assert result.passed is True

    def test_approval_required_failed(self, policy_evaluator):
        result = policy_evaluator.evaluate_approval_required(False)
        assert result.passed is False

    def test_conversation_only(self, policy_evaluator):
        assert policy_evaluator.evaluate_conversation_only(True).passed is True
        assert policy_evaluator.evaluate_conversation_only(False).passed is False

    def test_read_only(self, policy_evaluator):
        assert policy_evaluator.evaluate_read_only(True).passed is True
        assert policy_evaluator.evaluate_read_only(False).passed is False

    def test_evidence_required(self, policy_evaluator):
        assert policy_evaluator.evaluate_evidence_required(True, 0.8).passed is True
        assert policy_evaluator.evaluate_evidence_required(False).passed is False

    def test_trust_threshold(self, policy_evaluator):
        assert policy_evaluator.evaluate_trust_threshold(0.8, 0.5).passed is True
        assert policy_evaluator.evaluate_trust_threshold(0.3, 0.5).passed is False

    def test_provider_healthy(self, policy_evaluator):
        assert policy_evaluator.evaluate_provider_healthy(3, 3).passed is True
        assert policy_evaluator.evaluate_provider_healthy(0, 3).passed is False
        assert policy_evaluator.evaluate_provider_healthy(0, 0).passed is False

    def test_mission_allowed(self, policy_evaluator):
        assert policy_evaluator.evaluate_mission_allowed(5, 10).passed is True
        assert policy_evaluator.evaluate_mission_allowed(15, 10).passed is False

    def test_evaluate_all(self, policy_evaluator):
        results = policy_evaluator.evaluate_all()
        assert len(results) == 8
        assert policy_evaluator.all_passed is True

    def test_evaluate_all_with_violations(self, policy_evaluator):
        policy_evaluator.evaluate_all(
            has_auto_execution=True,
            has_approval=False,
            providers_healthy=0,
            providers_total=5,
        )
        assert policy_evaluator.all_passed is False
        assert len(policy_evaluator.violations) > 0

    def test_violations_property(self, policy_evaluator):
        policy_evaluator.evaluate_all(has_auto_execution=True)
        vs = policy_evaluator.violations
        assert any(v.policy == "NoAutoExecution" for v in vs)


# ══════════════════════════════════════════════════════════════════════
# OP-325: Guardian Recommendation Engine
# ══════════════════════════════════════════════════════════════════════

class TestGuardianRecommendationEngine:

    def test_from_health_critical(self, recommendation_engine):
        from sam.operations.brain.guardian.health import HealthIssue as HI
        issues = (HI(component="system", severity="critical", message="test"),)
        recs = recommendation_engine.from_health("critical", 0.3, issues)
        types = {r.recommendation_type for r in recs}
        assert "pause_scheduler" in types
        assert "reduce_load" in types

    def test_from_health_provider_issue(self, recommendation_engine):
        from sam.operations.brain.guardian.health import HealthIssue as HI
        issues = (HI(component="provider", severity="medium", message="provider issue"),)
        recs = recommendation_engine.from_health("degraded", 0.6, issues)
        assert any(r.recommendation_type == "rotate_provider" for r in recs)

    def test_from_policy_approval(self, recommendation_engine):
        from sam.operations.brain.guardian.policy_runtime import PolicyViolation as PV
        vs = (PV(policy="ApprovalRequired", severity="high", message="no approval"),)
        recs = recommendation_engine.from_policy(vs)
        assert any(r.recommendation_type == "request_approval" for r in recs)

    def test_from_policy_provider(self, recommendation_engine):
        from sam.operations.brain.guardian.policy_runtime import PolicyViolation as PV
        vs = (PV(policy="ProviderHealthy", severity="critical", message="no providers"),)
        recs = recommendation_engine.from_policy(vs)
        assert any(r.recommendation_type == "retry_later" for r in recs)

    def test_from_watchdog_alerts(self, recommendation_engine):
        from sam.operations.brain.guardian.watchdog import GuardianAlert
        alerts = (
            GuardianAlert(alert_type="stuck_reasoning", severity="critical",
                          component="reasoning", message="stuck"),
            GuardianAlert(alert_type="approval_deadlock", severity="critical",
                          component="approval", message="deadlock"),
            GuardianAlert(alert_type="scheduler_overload", severity="critical",
                          component="scheduler", message="overload"),
        )
        recs = recommendation_engine.from_watchdog(alerts, (), ())
        types = {r.recommendation_type for r in recs}
        assert "investigate_queue" in types
        assert "request_approval" in types
        assert "reduce_load" in types

    def test_from_watchdog_warnings(self, recommendation_engine):
        from sam.operations.brain.guardian.watchdog import GuardianWarning
        warns = (
            GuardianWarning(warning_type="provider_timeout", component="provider",
                            message="timeout", recommendation="rotate"),
            GuardianWarning(warning_type="queue_starvation", component="queue",
                            message="starvation", recommendation="investigate"),
        )
        recs = recommendation_engine.from_watchdog((), warns, ())
        types = {r.recommendation_type for r in recs}
        assert "rotate_provider" in types
        assert "investigate_queue" in types

    def test_from_reasoning_failures(self, recommendation_engine):
        recs = recommendation_engine.from_reasoning(reasoning_failures=10, active_sessions=15)
        types = {r.recommendation_type for r in recs}
        assert "retry_later" in types
        assert "reduce_load" in types

    def test_aggregate_sorts_by_priority(self, recommendation_engine):
        recs = recommendation_engine.aggregate(
            health_status="critical",
            health_score=0.3,
            health_issues=(),
        )
        assert len(recs) > 0
        # critical should come first
        assert recs[0].priority == "critical"

    def test_clear(self, recommendation_engine):
        recommendation_engine.aggregate(health_status="critical", health_score=0.3)
        assert len(recommendation_engine.recommendations) > 0
        recommendation_engine.clear()
        assert len(recommendation_engine.recommendations) == 0

    def test_recommendation_dto_frozen(self):
        r = GuardianRecommendation(
            recommendation_type="test", priority="low", source="test", title="test",
        )
        assert r.recommendation_type == "test"
        with pytest.raises(Exception):
            r.title = "changed"


# ══════════════════════════════════════════════════════════════════════
# OP-326: Guardian Supervisory Conversation
# ══════════════════════════════════════════════════════════════════════

class TestGuardianSupervisoryConversation:

    def test_get_health_returns_response(self, conversation, health_engine):
        health_engine.evaluate()
        resp = conversation.get_health()
        assert resp.success is True
        assert resp.query_type == "health"
        assert "status" in resp.data

    def test_get_issues(self, conversation, health_engine, watchdog):
        health_engine.evaluate(provider_healthy=0, provider_degraded=0)
        watchdog.check_stuck_reasoning(1, 120000.0)
        resp = conversation.get_issues()
        assert resp.success is True
        assert resp.data["count"] >= 1

    def test_get_recommendations(self, conversation, recommendation_engine):
        recommendation_engine.aggregate(health_status="critical", health_score=0.3)
        resp = conversation.get_recommendations()
        assert resp.success is True
        assert resp.data["count"] >= 1

    def test_get_providers(self, conversation, supervisor):
        supervisor.collect(provider=ProviderStatus(active_providers=3, healthy_providers=2))
        resp = conversation.get_providers()
        assert resp.success is True
        assert resp.data["active"] == 3

    def test_get_trust(self, conversation, health_engine):
        health_engine.evaluate(trust_level=0.8)
        resp = conversation.get_trust()
        assert resp.success is True
        assert resp.data["trust_score"] == 0.8

    def test_get_status_no_data(self, conversation):
        resp = conversation.get_status()
        assert resp.success is True
        assert resp.data["supervisor_issues"] is False

    def test_get_status_with_data(self, conversation, supervisor, health_engine):
        supervisor.collect(scheduler=SchedulerStatus(overloaded=True))
        health_engine.evaluate(scheduler_overloaded=True)
        resp = conversation.get_status()
        assert resp.data["health_status"] != "unknown"
        assert resp.data["policies_passed"] is True

    def test_get_queue(self, conversation, supervisor):
        supervisor.collect(scheduler=SchedulerStatus(tasks_queued=25, tasks_completed=100))
        resp = conversation.get_queue()
        assert resp.success is True
        assert resp.data["tasks_queued"] == 25

    def test_get_summary(self, conversation, supervisor, health_engine):
        health_engine.evaluate()
        resp = conversation.get_summary()
        assert resp.success is True
        assert resp.data["health"] != "unknown"

    def test_query_history(self, conversation):
        conversation.get_health()
        conversation.get_status()
        assert len(conversation.query_history) == 2


# ══════════════════════════════════════════════════════════════════════
# OP-327: Guardian Supervisory Dashboard
# ══════════════════════════════════════════════════════════════════════

class TestGuardianSupervisoryDashboard:

    def test_get_dashboard_returns_dto(self, dashboard_service, health_engine, supervisor):
        health_engine.evaluate()
        supervisor.collect()
        db = dashboard_service.get_dashboard()
        assert db.overall_status in ("healthy", "degraded", "critical")
        assert len(db.status_cards) == 4
        assert db.last_updated != ""

    def test_dashboard_health_card(self, dashboard_service, health_engine):
        health_engine.evaluate()
        db = dashboard_service.get_dashboard()
        card = db.status_cards[0]
        assert card.title == "Guardian Health"
        assert card.status == "healthy"

    def test_dashboard_has_panels(self, dashboard_service, health_engine, supervisor):
        health_engine.evaluate()
        supervisor.collect()
        db = dashboard_service.get_dashboard()
        assert len(db.panels) >= 3

    def test_dashboard_to_dict(self, dashboard_service, health_engine):
        health_engine.evaluate()
        db = dashboard_service.get_dashboard()
        d = db.to_dict()
        assert d["overall_status"] in ("healthy", "degraded", "critical")
        assert "last_updated" in d
        assert len(d["status_cards"]) == 4

    def test_dashboard_with_critical_health(self, dashboard_service, health_engine):
        health_engine.evaluate(
            provider_healthy=0, provider_degraded=0,
            scheduler_overloaded=True, approval_backlog=50,
        )
        db = dashboard_service.get_dashboard()
        assert db.overall_status == "critical"
        assert db.status_cards[0].status == "critical"


# ══════════════════════════════════════════════════════════════════════
# OP-328: Guardian Supervisory Runtime Integration
# ══════════════════════════════════════════════════════════════════════

class TestGuardianSupervisoryRuntimeIntegration:

    def test_run_successful(self, runtime_integration):
        result = runtime_integration.run()
        assert result.success is True
        assert result.pipeline_id.startswith("sp-")
        assert result.started_at != ""
        assert result.completed_at != ""

    def test_run_stages_all_true(self, runtime_integration):
        result = runtime_integration.run(
            observation_ok=True, brain_ok=True, reasoning_ok=True, decision_ok=True,
        )
        assert result.observation_ok is True
        assert result.brain_ok is True
        assert result.reasoning_ok is True
        assert result.decision_ok is True

    def test_run_observation_failure(self, runtime_integration):
        result = runtime_integration.run(observation_ok=False)
        assert result.success is False
        assert any("Observation" in e for e in result.errors)

    def test_run_reasoning_failure(self, runtime_integration):
        result = runtime_integration.run(reasoning_ok=False)
        assert result.success is False
        assert any("Reasoning" in e for e in result.errors)

    def test_run_creates_supervisor_snapshot(self, runtime_integration, supervisor):
        runtime_integration.run(reasoning_sessions=3, failure_count=1)
        snap = supervisor.latest()
        assert snap is not None
        assert snap.reasoning.active_sessions == 3
        assert snap.reasoning.failed_count == 1

    def test_run_health_evaluated(self, runtime_integration, health_engine):
        runtime_integration.run(
            provider_healthy=2, provider_degraded=1, pending_approvals=15,
        )
        health = health_engine.latest()
        assert health is not None
        assert health.score.provider_score < 1.0

    def test_run_watchdog_triggered(self, runtime_integration, watchdog):
        runtime_integration.run(
            reasoning_sessions=1,
            reasoning_max_duration_ms=120000.0,
            provider_errors=5,
            pending_approvals=5,
            approvals_stale_hours=48.0,
            queue_depth=200,
            queue_processed=0,
            missions_stalled=3,
            missions_active=4,
            retry_count=10,
            tasks_queued=200,
            failure_count=15,
        )
        assert len(watchdog.alerts) >= 1
        assert len(watchdog.warnings) >= 1

    def test_run_policy_evaluated(self, runtime_integration, policy_evaluator):
        runtime_integration.run(
            has_auto_execution=True,
            has_approval=False,
            provider_healthy=0,
        )
        assert policy_evaluator.all_passed is False

    def test_run_recommendations_generated(self, runtime_integration, recommendation_engine):
        runtime_integration.run(
            provider_healthy=0, provider_degraded=3,
            tasks_queued=150,
        )
        assert len(recommendation_engine.recommendations) >= 1

    def test_run_to_dict(self, runtime_integration):
        result = runtime_integration.run()
        d = result.to_dict()
        assert "pipeline_id" in d
        assert "success" in d
        assert "stages" in d
        assert "errors" in d

    def test_pipeline_count(self, runtime_integration):
        assert runtime_integration.pipeline_count == 0
        runtime_integration.run()
        assert runtime_integration.pipeline_count == 1
        runtime_integration.run()
        assert runtime_integration.pipeline_count == 2

    def test_results_history(self, runtime_integration):
        runtime_integration.run()
        runtime_integration.run()
        assert len(runtime_integration.results) == 2

    def test_full_pipeline_with_all_params(self, runtime_integration):
        result = runtime_integration.run(
            observation_ok=True,
            brain_ok=True,
            reasoning_ok=True,
            reasoning_sessions=2,
            reasoning_max_duration_ms=50000.0,
            decision_ok=True,
            pending_approvals=3,
            approvals_stale_hours=12.0,
            provider_healthy=4,
            provider_degraded=1,
            provider_errors=2,
            trust_level=0.85,
            queue_depth=15,
            queue_processed=10,
            missions_active=3,
            missions_stalled=0,
            retry_count=2,
            tasks_queued=20,
            failure_count=3,
            audit_consistent=True,
            evidence_quality=0.9,
            has_auto_execution=False,
            has_approval=True,
            has_conversation=True,
            has_evidence=True,
            is_read_only=True,
        )
        assert result.success is True
        assert result.pipeline_id != ""
