"""
Sprint 28 — Guardian Runtime V2 Integration Tests

OP-331 through OP-338
"""

import pytest
from datetime import datetime

# Fixtures module-level untuk semua class
from sam.operations.brain.guardian.health import GuardianHealthEngine as _HE
from sam.operations.brain.guardian.watchdog import GuardianWatchdog as _WD
from sam.operations.brain.guardian.policy_runtime import GuardianPolicyEvaluator as _PE
from sam.operations.brain.guardian.recommendation import GuardianRecommendationEngine as _RE
from sam.operations.brain.guardian.supervisor import GuardianSupervisor as _SU

@pytest.fixture
def health_engine():
    return _HE()

@pytest.fixture
def watchdog():
    return _WD()

@pytest.fixture
def policy_evaluator():
    return _PE()

@pytest.fixture
def recommendation_engine():
    return _RE()

@pytest.fixture
def supervisor():
    return _SU()


from sam.operations.brain.guardian import (
    # OP-331
    GuardianRuntimeV2, RuntimeV2Result, StageResult,
    # OP-332
    GuardianSnapshotEngine, GuardianSnapshot, GuardianSection,
    GuardianMetrics, GuardianHealthSnapshot,
    # OP-333
    GuardianHistoryService, GuardianEvent, GuardianTimeline,
    # OP-334
    GuardianTrendAnalyzer, GuardianTrend,
    # OP-335
    GuardianSummaryBuilder, GuardianSummary, GuardianSummarySection,
    GuardianFinding, GuardianRisk, GuardianPriority,
    # OP-336
    GuardianConversationV2, GuardianV2Response,
    # OP-337
    GuardianDashboardV2Service,
    GuardianHealthCard, GuardianPolicyCard, GuardianTrendCard,
    GuardianRecommendationCard, GuardianRiskCard, GuardianSummaryCard,
    # OP-338
    GuardianRoutingV2Integration, RoutingV2Result,
    # Sprint 27 (dependency)
    GuardianHealthEngine, GuardianWatchdog, GuardianPolicyEvaluator,
    GuardianRecommendationEngine, GuardianSupervisor,
)


# ══════════════════════════════════════════════════════════════════════
# OP-331: Guardian Runtime V2
# ══════════════════════════════════════════════════════════════════════

class TestGuardianRuntimeV2:

    @pytest.fixture
    def runtime(self):
        return GuardianRuntimeV2()

    def test_run_returns_result(self, runtime):
        result = runtime.run()
        assert isinstance(result, RuntimeV2Result)
        assert result.pipeline_id.startswith("gv2-")
        assert result.stage_count == 10

    def test_stage_names(self, runtime):
        result = runtime.run()
        stages = [s.stage for s in result.stages]
        expected = [
            "collect_state", "health", "watchdog", "policy", "reasoning",
            "decision", "recommendation", "audit", "dashboard", "conversation",
        ]
        assert stages == expected

    def test_run_successful_no_engines(self, runtime):
        result = runtime.run()
        assert result.success is True
        assert len(result.errors) == 0

    def test_with_engines(self, health_engine, watchdog, policy_evaluator, recommendation_engine, supervisor):
        runtime = GuardianRuntimeV2(
            health_engine=health_engine,
            watchdog=watchdog,
            policy_evaluator=policy_evaluator,
            recommendation_engine=recommendation_engine,
            supervisor=supervisor,
        )
        result = runtime.run()
        assert result.success is True

    def test_pipeline_count(self, runtime):
        assert runtime.pipeline_count == 0
        runtime.run()
        assert runtime.pipeline_count == 1
        runtime.run()
        assert runtime.pipeline_count == 2

    def test_last_result(self, runtime):
        assert runtime.last_result is None
        r1 = runtime.run()
        assert runtime.last_result is r1
        r2 = runtime.run()
        assert runtime.last_result is r2

    def test_healthy_property(self, runtime):
        assert runtime.healthy is False
        runtime.run()
        assert runtime.healthy is True

    def test_stage_result_dto(self):
        sr = StageResult(stage="health", success=True, data={"status": "ok"})
        assert sr.stage == "health"
        assert sr.success is True
        assert sr.data["status"] == "ok"

    def test_stage_result_frozen(self):
        sr = StageResult(stage="test", success=True)
        with pytest.raises(Exception):
            sr.stage = "changed"

    def test_runtime_v2_result_frozen(self):
        result = RuntimeV2Result(pipeline_id="test", success=True)
        with pytest.raises(Exception):
            result.success = False

    def test_result_to_dict(self, runtime):
        result = runtime.run()
        d = result.to_dict()
        assert "pipeline_id" in d
        assert d["stage_count"] == 10
        assert "failed_stages" in d

    def test_failed_stages_empty(self, runtime):
        result = runtime.run()
        assert result.failed_stages == []

    def test_to_dict_no_pipeline_data(self, runtime):
        result = runtime.run()
        assert result.pipeline_data is not None

    def test_health_stage_runs(self, runtime):
        result = runtime.run(health_status="healthy", health_score=1.0)
        health_stage = [s for s in result.stages if s.stage == "health"][0]
        assert health_stage.success is True


# ══════════════════════════════════════════════════════════════════════
# OP-332: Guardian Snapshot Engine
# ══════════════════════════════════════════════════════════════════════

class TestGuardianSnapshotEngine:

    @pytest.fixture
    def engine(self):
        return GuardianSnapshotEngine()

    def test_collect_returns_snapshot(self, engine):
        snap = engine.collect()
        assert isinstance(snap, GuardianSnapshot)
        assert snap.timestamp != ""

    def test_snapshot_has_health(self, engine):
        snap = engine.collect()
        assert isinstance(snap.health, GuardianHealthSnapshot)

    def test_snapshot_has_metrics(self, engine):
        snap = engine.collect()
        assert isinstance(snap.metrics, GuardianMetrics)

    def test_snapshot_system_status(self, engine):
        snap = engine.collect()
        assert snap.system_status == "healthy"

    def test_with_kwargs(self, engine):
        snap = engine.collect(
            reasoning_sessions=5, failure_count=2,
            pending_approvals=10, provider_healthy=3,
            queue_depth=25,
        )
        assert snap.metrics.reasoning_sessions == 5
        assert snap.metrics.reasoning_failures == 2

    def test_snapshot_count(self, engine):
        engine.collect()
        engine.collect()
        assert engine.snapshot_count == 2

    def test_last_snapshot(self, engine):
        assert engine.last_snapshot is None
        s1 = engine.collect()
        assert engine.last_snapshot is s1
        s2 = engine.collect()
        assert engine.last_snapshot is s2

    def test_clear(self, engine):
        engine.collect()
        engine.collect()
        assert engine.snapshot_count == 2
        engine.clear()
        assert engine.snapshot_count == 0

    def test_snapshot_to_dict(self, engine):
        snap = engine.collect()
        d = snap.to_dict()
        assert "timestamp" in d
        assert "health" in d
        assert "metrics" in d
        assert "errors" in d

    def test_snapshot_frozen(self, engine):
        snap = engine.collect()
        with pytest.raises(Exception):
            snap.system_status = "critical"

    def test_metrics_frozen(self):
        m = GuardianMetrics(reasoning_sessions=5)
        with pytest.raises(Exception):
            m.reasoning_sessions = 10

    def test_section_dto(self):
        s = GuardianSection(name="test", status="ok", score=0.9)
        assert s.name == "test"
        with pytest.raises(Exception):
            s.status = "fail"

    def test_health_snapshot_dto(self):
        hs = GuardianHealthSnapshot(status="healthy", overall_score=0.95)
        assert hs.status == "healthy"
        with pytest.raises(Exception):
            hs.status = "critical"


# ══════════════════════════════════════════════════════════════════════
# OP-333: Guardian History
# ══════════════════════════════════════════════════════════════════════

class TestGuardianHistory:

    @pytest.fixture
    def history(self):
        return GuardianHistoryService()

    def test_empty_on_init(self, history):
        assert history.event_count == 0

    def test_append_event(self, history):
        event = history.append_event("info", "low", "test", "detail")
        assert isinstance(event, GuardianEvent)
        assert event.category == "info"
        assert event.event_id != ""

    def test_latest(self, history):
        history.append_event("info", "low", "first")
        history.append_event("info", "low", "second")
        latest = history.latest(1)
        assert len(latest) == 1
        assert latest[0].message == "second"

    def test_by_severity(self, history):
        history.append_event("info", "low", "low")
        history.append_event("info", "high", "high1")
        history.append_event("info", "high", "high2")
        high = history.by_severity("high")
        assert len(high) == 2

    def test_by_category(self, history):
        history.append_event("health", "low", "health event")
        history.append_event("policy", "low", "policy event")
        assert len(history.by_category("health")) == 1
        assert len(history.by_category("policy")) == 1

    def test_by_policy(self, history):
        history.append_event("policy", "high", "violation")
        history.append_event("info", "low", "info")
        assert len(history.by_policy()) == 1

    def test_by_health(self, history):
        history.append_event("health", "medium", "degraded")
        assert len(history.by_health()) == 1

    def test_by_watchdog(self, history):
        history.append_event("watchdog", "critical", "alert")
        assert len(history.by_watchdog()) == 1

    def test_max_events(self):
        h = GuardianHistoryService(max_events=5)
        for _ in range(10):
            h.append_event("info", "low", "test")
        assert h.event_count <= 5

    def test_clear(self, history):
        history.append_event("info", "low", "test")
        assert history.event_count == 1
        history.clear()
        assert history.event_count == 0

    def test_all_events(self, history):
        history.append_event("info", "low", "e1")
        history.append_event("info", "low", "e2")
        assert len(history.all_events) == 2

    def test_to_timeline(self, history):
        history.append_event("info", "low", "test")
        tl = history.to_timeline("guardian_test")
        assert isinstance(tl, GuardianTimeline)
        assert tl.count == 1
        assert tl.source == "guardian_test"

    def test_event_to_dict(self, history):
        event = history.append_event("test", "low", "msg", "detail")
        d = event.to_dict()
        assert d["category"] == "test"
        assert d["message"] == "msg"

    def test_guardian_timeline_count(self):
        from sam.operations.brain.guardian.history import GuardianTimeline
        from sam.operations.brain.guardian.history import GuardianEvent
        e = GuardianEvent(message="test", timestamp="now")
        tl = GuardianTimeline(events=(e,))
        assert tl.count == 1
        assert tl.source == "guardian"


# ══════════════════════════════════════════════════════════════════════
# OP-334: Guardian Trend Analyzer
# ══════════════════════════════════════════════════════════════════════

class TestGuardianTrendAnalyzer:

    @pytest.fixture
    def analyzer(self):
        return GuardianTrendAnalyzer()

    def test_analyze_returns_trend(self, analyzer):
        t = analyzer.analyze()
        assert isinstance(t, GuardianTrend)
        assert t.health_trend == "stable"
        assert t.timestamp != ""

    def test_with_health_degrading(self, analyzer):
        t = analyzer.analyze(health_trend="degrading")
        assert t.health_trend == "degrading"
        assert "health_degrading" in t.signals

    def test_with_watchdog_alerts(self, analyzer):
        t = analyzer.analyze(watchdog_trend="critical", watchdog_alerts=6)
        assert t.watchdog_trend == "critical"

    def test_with_stalled_missions(self, analyzer):
        t = analyzer.analyze(stalled_missions=2)
        assert "mission_stall_detected" in t.signals

    def test_with_retry_loop(self, analyzer):
        t = analyzer.analyze(retry_count=10)
        assert "retry_loop_detected" in t.signals

    def test_with_queue_backlog(self, analyzer):
        t = analyzer.analyze(queue_depth=60)
        assert "queue_backlog" in t.signals

    def test_with_approval_backlog(self, analyzer):
        t = analyzer.analyze(pending_approvals=15)
        assert "approval_backlog" in t.signals

    def test_pattern_system_degradation(self, analyzer):
        t = analyzer.analyze(health_trend="degrading", watchdog_trend="critical")
        assert "system_degradation_with_alerts" in t.patterns

    def test_pattern_failure_retry(self, analyzer):
        t = analyzer.analyze(failure_count=10, retry_count=5)
        assert "failure_retry_loop" in t.patterns

    def test_pattern_provider_degradation(self, analyzer):
        t = analyzer.analyze(provider_healthy=0, provider_degraded=3)
        assert "provider_degradation" in t.patterns

    def test_pattern_stall_risk(self, analyzer):
        t = analyzer.analyze(pending_approvals=15, queue_depth=40)
        assert "stall_risk" in t.patterns

    def test_trend_count(self, analyzer):
        analyzer.analyze()
        analyzer.analyze()
        assert analyzer.trend_count == 2

    def test_last_trend(self, analyzer):
        assert analyzer.last_trend is None
        t1 = analyzer.analyze()
        assert analyzer.last_trend is t1
        t2 = analyzer.analyze()
        assert analyzer.last_trend is t2

    def test_trend_to_dict(self, analyzer):
        t = analyzer.analyze(health_trend="degrading")
        d = t.to_dict()
        assert d["health_trend"] == "degrading"
        assert "signals" in d

    def test_trend_frozen(self, analyzer):
        t = analyzer.analyze()
        with pytest.raises(Exception):
            t.health_trend = "changed"


# ══════════════════════════════════════════════════════════════════════
# OP-335: Guardian Summary Builder
# ══════════════════════════════════════════════════════════════════════

class TestGuardianSummaryBuilder:

    @pytest.fixture
    def builder(self):
        return GuardianSummaryBuilder()

    def test_build_returns_summary(self, builder):
        sm = builder.build()
        assert isinstance(sm, GuardianSummary)
        assert sm.timestamp != ""

    def test_summary_sections(self, builder):
        sm = builder.build()
        assert len(sm.sections) >= 1
        assert sm.sections[0].title == "Current Health"

    def test_summary_with_policy(self, policy_evaluator):
        builder = GuardianSummaryBuilder(policy_evaluator=policy_evaluator)
        policy_evaluator.evaluate_all(has_auto_execution=True)
        sm = builder.build()
        assert len(sm.findings) > 0

    def test_summary_to_dict(self, builder):
        sm = builder.build()
        d = sm.to_dict()
        assert "current_health" in d
        assert "findings_count" in d

    def test_summary_count(self, builder):
        builder.build()
        builder.build()
        assert builder.summary_count == 2

    def test_last_summary(self, builder):
        assert builder.last_summary is None
        s1 = builder.build()
        assert builder.last_summary is s1

    def test_summary_section_dto(self):
        s = GuardianSummarySection(title="test", content="content", details=("a", "b"))
        assert s.title == "test"
        assert len(s.details) == 2
        with pytest.raises(Exception):
            s.title = "changed"

    def test_finding_dto(self):
        f = GuardianFinding(category="policy", severity="high", message="violation")
        with pytest.raises(Exception):
            f.message = "changed"

    def test_risk_dto(self):
        r = GuardianRisk(category="signal", severity="medium", message="risk")
        with pytest.raises(Exception):
            r.category = "changed"

    def test_priority_dto(self):
        p = GuardianPriority(urgency="critical", area="health", message="urgent")
        with pytest.raises(Exception):
            p.urgency = "low"

    def test_summary_frozen(self, builder):
        sm = builder.build()
        with pytest.raises(Exception):
            sm.current_health_status = "critical"

    def test_summary_with_recommendations(self, recommendation_engine):
        recommendation_engine.aggregate(health_status="critical", health_score=0.3)
        builder = GuardianSummaryBuilder(recommendation_engine=recommendation_engine)
        sm = builder.build()
        # Harus ada priorities karena ada rec critical
        assert len(sm.priorities) >= 1


# ══════════════════════════════════════════════════════════════════════
# OP-336: Guardian Conversation V2
# ══════════════════════════════════════════════════════════════════════

class TestGuardianConversationV2:

    @pytest.fixture
    def conv(self):
        return GuardianConversationV2()

    def test_query_summary_no_data(self, conv):
        resp = conv.query_summary()
        assert resp.success is False
        assert resp.query_type == "summary"

    def test_query_trend_no_data(self, conv):
        resp = conv.query_trend()
        assert resp.success is False

    def test_query_health_no_data(self, conv):
        resp = conv.query_health()
        assert resp.success is False

    def test_query_policy_no_data(self, conv):
        resp = conv.query_policy()
        assert resp.success is False

    def test_query_recommendation_no_data(self, conv):
        resp = conv.query_recommendation()
        assert resp.success is False

    def test_query_finding_no_data(self, conv):
        resp = conv.query_finding()
        assert resp.success is True  # empty findings is ok
        assert resp.data["count"] == 0

    def test_query_risk_no_data(self, conv):
        resp = conv.query_risk()
        assert resp.success is True

    def test_query_timeline_no_data(self, conv):
        resp = conv.query_timeline()
        assert resp.success is False

    def test_query_snapshot_no_data(self, conv):
        resp = conv.query_snapshot()
        assert resp.success is False

    def test_query_status_no_data(self, conv):
        resp = conv.query_status()
        assert resp.success is True  # status always works
        assert resp.data["health_status"] == "unknown"

    def test_with_engines(self, health_engine, policy_evaluator, recommendation_engine):
        health_engine.evaluate()
        recommendation_engine.aggregate(health_status="healthy", health_score=1.0)
        conv = GuardianConversationV2(
            health_engine=health_engine,
            policy_evaluator=policy_evaluator,
            recommendation_engine=recommendation_engine,
        )
        hr = conv.query_health()
        assert hr.success is True
        assert hr.data["status"] == "healthy"

        pr = conv.query_policy()
        assert pr.success is True
        assert "all_passed" in pr.data

        rr = conv.query_recommendation()
        assert rr.success is True

    def test_query_history(self, conv):
        conv.query_status()
        conv.query_health()
        assert len(conv.query_history) == 2

    def test_v2_response_ok(self):
        resp = GuardianV2Response.ok("test", {"key": "val"}, "ok")
        assert resp.success is True
        assert resp.query_type == "test"

    def test_v2_response_error(self):
        resp = GuardianV2Response.error("test", "failed")
        assert resp.success is False
        assert resp.message == "failed"

    def test_v2_response_frozen(self):
        resp = GuardianV2Response.ok("test", {})
        with pytest.raises(Exception):
            resp.success = False


# ══════════════════════════════════════════════════════════════════════
# OP-337: Dashboard V2
# ══════════════════════════════════════════════════════════════════════

class TestDashboardV2:

    @pytest.fixture
    def service(self):
        return GuardianDashboardV2Service()

    def test_health_card_default(self, service):
        card = service.build_health_card()
        assert card.status == "unknown"
        assert card.score == 0.0

    def test_policy_card_default(self, service):
        card = service.build_policy_card()
        assert card.all_passed is True

    def test_trend_card_default(self, service):
        card = service.build_trend_card()
        assert card.health_trend == "stable"

    def test_recommendation_card_default(self, service):
        card = service.build_recommendation_card()
        assert card.count == 0

    def test_risk_card_default(self, service):
        card = service.build_risk_card()
        assert card.count == 0

    def test_summary_card_default(self, service):
        card = service.build_summary_card()
        assert card.health_status == "unknown"

    def test_health_card_with_engine(self, health_engine):
        health_engine.evaluate()
        service = GuardianDashboardV2Service(health_engine=health_engine)
        card = service.build_health_card()
        assert card.status == "healthy"

    def test_health_card_to_dict(self, service):
        card = service.build_health_card()
        d = card.to_dict()
        assert d["status"] == "unknown"

    def test_policy_card_to_dict(self, service):
        card = service.build_policy_card()
        d = card.to_dict()
        assert "all_passed" in d

    def test_trend_card_to_dict(self, service):
        card = service.build_trend_card()
        d = card.to_dict()
        assert d["health_trend"] == "stable"

    def test_recommendation_card_to_dict(self, service):
        card = service.build_recommendation_card()
        d = card.to_dict()
        assert d["count"] == 0

    def test_risk_card_to_dict(self, service):
        card = service.build_risk_card()
        d = card.to_dict()
        assert d["count"] == 0

    def test_summary_card_to_dict(self, service):
        card = service.build_summary_card()
        d = card.to_dict()
        assert d["health_status"] == "unknown"

    def test_all_cards_frozen(self, service):
        h = service.build_health_card()
        p = service.build_policy_card()
        t = service.build_trend_card()
        r = service.build_recommendation_card()
        k = service.build_risk_card()
        s = service.build_summary_card()
        for card in (h, p, t, r, k, s):
            with pytest.raises(Exception):
                setattr(card, "count", 999)

    def test_policy_card_with_violations(self, policy_evaluator):
        policy_evaluator.evaluate_all(has_auto_execution=True)
        service = GuardianDashboardV2Service(policy_evaluator=policy_evaluator)
        card = service.build_policy_card()
        assert card.all_passed is False
        assert card.violations_count > 0

    def test_recommendation_card_with_data(self, recommendation_engine):
        recommendation_engine.aggregate(health_status="critical", health_score=0.3)
        service = GuardianDashboardV2Service(recommendation_engine=recommendation_engine)
        card = service.build_recommendation_card()
        assert card.count > 0


# ══════════════════════════════════════════════════════════════════════
# OP-338: Guardian Routing V2 Integration
# ══════════════════════════════════════════════════════════════════════

class TestGuardianRoutingV2Integration:

    def test_run_without_engines(self):
        routing = GuardianRoutingV2Integration()
        result = routing.run()
        assert isinstance(result, RoutingV2Result)
        assert result.success is True  # all empty stages succeed
        assert result.pipeline_id.startswith("rtv2-")

    def test_run_with_full_pipeline(self):
        # Bangun seluruh engine
        health = GuardianHealthEngine()
        watchdog = GuardianWatchdog()
        policy = GuardianPolicyEvaluator()
        recommendation = GuardianRecommendationEngine()
        supervisor = GuardianSupervisor()

        snapshot = GuardianSnapshotEngine(health_engine=health, supervisor=supervisor)
        history = GuardianHistoryService()
        trend = GuardianTrendAnalyzer(history=history)
        summary = GuardianSummaryBuilder()
        dashboard = GuardianDashboardV2Service(health_engine=health)
        conv = GuardianConversationV2(health_engine=health)

        runtime = GuardianRuntimeV2(
            health_engine=health, watchdog=watchdog,
            policy_evaluator=policy, supervisor=supervisor,
            recommendation_engine=recommendation,
        )

        routing = GuardianRoutingV2Integration(
            runtime_v2=runtime,
            snapshot_engine=snapshot,
            history=history,
            trend=trend,
            summary_builder=summary,
            dashboard_v2=dashboard,
            conversation_v2=conv,
        )

        result = routing.run(
            reasoning_sessions=3, failure_count=1, pending_approvals=5,
            provider_healthy=4, provider_degraded=1,
        )
        assert result.success is True
        assert result.runtime_ok is True
        assert result.snapshot_ok is True
        assert result.history_ok is True
        assert result.trend_ok is True
        assert result.summary_ok is True
        assert result.dashboard_ok is True
        assert result.conversation_ok is True

    def test_result_count(self):
        routing = GuardianRoutingV2Integration()
        assert routing.result_count == 0
        routing.run()
        assert routing.result_count == 1
        routing.run()
        assert routing.result_count == 2

    def test_last_result(self):
        routing = GuardianRoutingV2Integration()
        assert routing.last_result is None
        r1 = routing.run()
        assert routing.last_result is r1

    def test_result_to_dict(self):
        routing = GuardianRoutingV2Integration()
        result = routing.run()
        d = result.to_dict()
        assert d["success"] is True
        assert "pipeline_id" in d
        assert "runtime_ok" in d
        assert "snapshot_ok" in d

    def test_routing_frozen(self):
        r = RoutingV2Result(success=True)
        with pytest.raises(Exception):
            r.success = False

    def test_snapshot_populated_after_run(self):
        health = GuardianHealthEngine()
        health.evaluate()
        snapshot = GuardianSnapshotEngine(health_engine=health)
        routing = GuardianRoutingV2Integration(
            snapshot_engine=snapshot,
        )
        routing.run()
        assert snapshot.last_snapshot is not None

    def test_history_populated_after_run(self):
        history = GuardianHistoryService()
        routing = GuardianRoutingV2Integration(history=history)
        routing.run()
        assert history.event_count >= 1

    def test_full_pipeline_with_alerts(
        self, health_engine, watchdog, policy_evaluator,
        recommendation_engine, supervisor,
    ):
        snapshot = GuardianSnapshotEngine(
            health_engine=health_engine, supervisor=supervisor,
        )
        history = GuardianHistoryService()
        trend = GuardianTrendAnalyzer(history=history)
        summary = GuardianSummaryBuilder(snapshot_engine=snapshot)
        dashboard = GuardianDashboardV2Service(health_engine=health_engine)
        conv = GuardianConversationV2(health_engine=health_engine)

        runtime = GuardianRuntimeV2(
            health_engine=health_engine, watchdog=watchdog,
            policy_evaluator=policy_evaluator, supervisor=supervisor,
            recommendation_engine=recommendation_engine,
        )

        routing = GuardianRoutingV2Integration(
            runtime_v2=runtime,
            snapshot_engine=snapshot,
            history=history,
            trend=trend,
            summary_builder=summary,
            dashboard_v2=dashboard,
            conversation_v2=conv,
        )

        result = routing.run(
            reasoning_sessions=1, reasoning_max_duration_ms=120000.0,
            provider_healthy=0, provider_degraded=3,
            pending_approvals=15, queue_depth=60,
            has_auto_execution=True, has_approval=False,
        )
        assert result.success is True
        assert snapshot.last_snapshot is not None
        assert history.event_count >= 1
