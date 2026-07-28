"""
Test file for Sprint 20 — Observation Scheduler & Orchestrator.

Tests: Scheduler, MultiSource, Correlation, Priority, Orchestrator,
ProposalQueue, Health, ConversationV2, IntegrationV2.
"""

from __future__ import annotations

import time
import pytest

from sam.operations.brain import (
    # Scheduler
    ObservationScheduler,
    SchedulerConfig,
    SchedulerState,
    VersionedSnapshot,
    create_scheduler,
    # Multi-source
    MultiSourceObserver,
    MultiSourceSnapshot,
    SourceResult,
    observe_all,
    observe_sources,
    # Correlation
    CorrelationEngine,
    CorrelationDef,
    CorrelatedFinding,
    correlate_findings,
    build_finding_dict,
    # Priority
    PriorityEngine,
    PriorityScore,
    PriorityCategory,
    PriorityConfig,
    prioritize,
    build_rec_for_priority,
    # Orchestrator
    MissionOrchestrator,
    OperationalPackage,
    OrchestratorConfig,
    auto_orchestrate,
    # ProposalQueue
    ProposalQueue,
    QueueItem,
    ProposalState,
    InvalidTransitionError,
    create_draft,
    # Health
    OperationalHealthEngine,
    OperationalHealthDTO,
    DimensionHealth,
    evaluate_health,
    # Conversation V2
    BrainConversationBridgeV2,
    ConversationContext,
    BrainQuery,
    BrainAnswer,
    QueryType,
    ask_brain_v2,
    classify_query,
    # Integration V2
    ProactivePipeline,
    ProactivePipelineResult,
    run_proactive_pipeline,
    pipeline_summary,
    # Dependencies from Sprint 19
    ObservationEngine,
    ObservationSnapshot,
    OperationalFinding,
    Severity,
)


# ══════════════════════════════════════════════════════════════════════
# OP-251: ObservationScheduler Tests
# ══════════════════════════════════════════════════════════════════════


class TestObservationScheduler:

    def test_create_scheduler(self):
        """Scheduler can be created with config."""
        config = SchedulerConfig(interval_seconds=60, enabled=True)
        sched = ObservationScheduler(
            callback=lambda: None,
            config=config,
        )
        assert sched.state == SchedulerState.IDLE
        assert sched.config.interval_seconds == 60
        assert sched.sequence == 0
        assert sched.last_snapshot is None

    def test_default_config(self):
        """Default config uses 300s interval."""
        sched = ObservationScheduler(callback=lambda: None)
        assert sched.config.interval_seconds == 300

    def test_run_once(self):
        """run_once executes callback and returns VersionedSnapshot."""
        results = []

        def cb():
            results.append("observed")
            return {"status": "ok"}

        sched = ObservationScheduler(callback=cb)
        vs = sched.run_once()

        assert isinstance(vs, VersionedSnapshot)
        assert vs.sequence == 1
        assert vs.snapshot == {"status": "ok"}
        assert vs.timestamp > 0
        assert len(results) == 1

    def test_run_once_increments_sequence(self):
        """Each run_once increments sequence."""
        sched = ObservationScheduler(callback=lambda: None)
        v1 = sched.run_once()
        v2 = sched.run_once()
        assert v1.sequence == 1
        assert v2.sequence == 2

    def test_start_and_stop(self):
        """Scheduler can start and gracefully stop."""
        sched = ObservationScheduler(
            callback=lambda: {"ok": True},
            config=SchedulerConfig(interval_seconds=3600),  # long interval
        )
        assert sched.state == SchedulerState.IDLE

        sched.start()
        assert sched.state == SchedulerState.RUNNING

        sched.stop(wait=False)
        # May be STOPPED or STOPPING depending on timing
        assert sched.state in (SchedulerState.STOPPED, SchedulerState.STOPPING)

    def test_create_scheduler_factory(self):
        """create_scheduler convenience factory works."""
        sched = create_scheduler(callback=lambda: None, interval_seconds=120)
        assert isinstance(sched, ObservationScheduler)
        assert sched.config.interval_seconds == 120

    def test_versioned_snapshot_repr(self):
        """VersionedSnapshot repr is readable."""
        vs = VersionedSnapshot(sequence=1, timestamp=1000.0, snapshot={})
        r = repr(vs)
        assert "VersionedSnapshot" in r
        assert "seq=1" in r


# ══════════════════════════════════════════════════════════════════════
# OP-252: MultiSourceObserver Tests
# ══════════════════════════════════════════════════════════════════════


class TestMultiSourceObserver:

    def test_create_observer(self):
        """MultiSourceObserver can be instantiated."""
        obs = MultiSourceObserver()
        assert obs.last_snapshot is None

    def test_observe_all_returns_snapshot(self):
        """observe_all returns a MultiSourceSnapshot."""
        obs = MultiSourceObserver()
        snap = obs.observe_all()
        assert isinstance(snap, MultiSourceSnapshot)
        assert snap.timestamp > 0
        assert len(snap.sources) > 0

    def test_all_sources_have_names(self):
        """All sources have names and results."""
        obs = MultiSourceObserver()
        snap = obs.observe_all()
        for name in ("mission", "approval", "trust", "notification", "workspace_lock"):
            assert name in snap.sources, f"Missing source: {name}"

    def test_observe_subset(self):
        """observe_sources works with a subset of sources."""
        obs = MultiSourceObserver()
        snap = obs.observe_sources(["mission", "approval"])
        assert len(snap.sources) == 2
        assert "mission" in snap.sources
        assert "approval" in snap.sources

    def test_observe_unknown_source(self):
        """Unknown source returns FAIL with error."""
        obs = MultiSourceObserver()
        snap = obs.observe_sources(["nonexistent"])
        r = snap.sources.get("nonexistent")
        assert r is not None
        assert not r.success
        assert "UNKNOWN_SOURCE" in (r.error or "")

    def test_source_result_repr(self):
        """SourceResult repr includes status."""
        ok = SourceResult(source_name="test", success=True, data="ok")
        fail = SourceResult(source_name="test", success=False, error="err")
        assert "OK" in repr(ok)
        assert "FAIL" in repr(fail)

    def test_multi_source_snapshot_properties(self):
        """MultiSourceSnapshot properties work."""
        sources = {
            "a": SourceResult("a", True, data=1),
            "b": SourceResult("b", False, error="fail"),
        }
        snap = MultiSourceSnapshot(timestamp=time.time(), sources=sources)
        assert snap.all_ok is False
        assert "b" in snap.failed_sources
        assert "a" in snap.ok_sources

    def test_observe_all_convenience(self):
        """observe_all() convenience works."""
        snap = observe_all()
        assert isinstance(snap, MultiSourceSnapshot)

    def test_observe_sources_convenience(self):
        """observe_sources() convenience works."""
        snap = observe_sources(["mission"])
        assert isinstance(snap, MultiSourceSnapshot)


# ══════════════════════════════════════════════════════════════════════
# OP-253: CorrelationEngine Tests
# ══════════════════════════════════════════════════════════════════════


class DummyFinding:
    """Helper to create findings for testing."""
    @staticmethod
    def make(finding_id, severity="info", confidence=0.8):
        return OperationalFinding(
            finding_id=finding_id,
            title=f"Finding {finding_id}",
            description=f"Test finding {finding_id}",
            severity=Severity(severity),
            confidence=confidence,
            evidence=[{"type": "test", "value": finding_id}],
            affected_resources=["test"],
            recommended_actions=["Do something"],
            source_rules=[f"rule_{finding_id}"],
            timestamp=time.time(),
        )


class TestCorrelationEngine:

    def test_create_engine(self):
        """CorrelationEngine starts with built-in rules."""
        eng = CorrelationEngine()
        assert len(eng.correlations) >= 5  # at least 5 built-in rules

    def test_empty_correlation(self):
        """No findings -> no correlations."""
        eng = CorrelationEngine()
        result = eng.correlate([])
        assert result == []

    def test_single_finding_no_correlation(self):
        """Single finding that doesn't match any rule -> no correlations."""
        eng = CorrelationEngine()
        findings = [DummyFinding.make("unknown_single")]
        result = eng.correlate(findings)
        assert result == []

    def test_matching_correlation(self):
        """Findings that match a rule produce a correlation."""
        eng = CorrelationEngine()
        findings = [
            DummyFinding.make("approval_backlog", "warning"),
            DummyFinding.make("trust_degradation", "critical"),
        ]
        result = eng.correlate(findings)
        assert len(result) >= 1
        gov = [c for c in result if c.correlation_id == "governance_issue"]
        assert len(gov) >= 1
        assert gov[0].confidence > 0

    def test_systemic_failure(self):
        """Mission failure + anomaly cluster -> systemic failure."""
        eng = CorrelationEngine()
        findings = [
            DummyFinding.make("mission_failure", "critical"),
            DummyFinding.make("anomaly_cluster", "critical"),
        ]
        result = eng.correlate(findings)
        systemic = [c for c in result if c.correlation_id == "systemic_failure"]
        assert len(systemic) >= 1

    def test_shared_evidence(self):
        """Correlation includes shared evidence from all findings."""
        eng = CorrelationEngine()
        f1 = DummyFinding.make("approval_backlog", "warning")
        f2 = DummyFinding.make("trust_degradation", "critical")
        result = eng.correlate([f1, f2])
        if result:
            assert len(result[0].shared_evidence) >= 2

    def test_correlated_finding_severity(self):
        """severity is highest among related findings."""
        eng = CorrelationEngine()
        f1 = DummyFinding.make("approval_backlog", "warning")
        f2 = DummyFinding.make("trust_degradation", "critical")
        result = eng.correlate([f1, f2])
        if result:
            assert result[0].severity == "critical"

    def test_add_custom_correlation(self):
        """Custom correlation rules can be added."""
        eng = CorrelationEngine()
        custom = CorrelationDef(
            correlation_id="custom_test",
            name="Custom Rule",
            description="Test custom correlation",
            required_finding_ids=["finding_a", "finding_b"],
        )
        eng.add_correlation(custom)
        assert len(eng.correlations) >= 6
        assert any(c.correlation_id == "custom_test" for c in eng.correlations)

    def test_correlate_findings_convenience(self):
        """correlate_findings() convenience works."""
        findings = [
            DummyFinding.make("approval_backlog", "warning"),
            DummyFinding.make("trust_degradation", "critical"),
        ]
        result = correlate_findings(findings)
        assert isinstance(result, list)

    def test_build_finding_dict(self):
        """build_finding_dict creates lookup dict."""
        findings = [DummyFinding.make("test1"), DummyFinding.make("test2")]
        d = build_finding_dict(findings)
        assert "test1" in d
        assert "test2" in d


# ══════════════════════════════════════════════════════════════════════
# OP-254: PriorityEngine Tests
# ══════════════════════════════════════════════════════════════════════


class TestPriorityEngine:

    def test_create_engine(self):
        """PriorityEngine can be created."""
        eng = PriorityEngine()
        assert eng.config is not None

    def test_empty_findings(self):
        """No findings -> empty scores."""
        eng = PriorityEngine()
        scores = eng.prioritize([])
        assert scores == []

    def test_single_finding_prioritized(self):
        """Single finding gets a score."""
        eng = PriorityEngine()
        finding = DummyFinding.make("test_finding", "warning")
        scores = eng.prioritize([finding])
        assert len(scores) == 1
        assert 0 <= scores[0].score <= 100

    def test_critical_finding_high_score(self):
        """Critical finding gets highest category."""
        eng = PriorityEngine()
        finding = DummyFinding.make("mission_failure", "critical", confidence=0.95)
        scores = eng.prioritize([finding])
        assert scores[0].score > 50

    def test_info_finding_low_score(self):
        """Info finding gets lower score."""
        eng = PriorityEngine()
        finding = DummyFinding.make("system_idle", "info", confidence=0.5)
        scores = eng.prioritize([finding])
        assert scores[0].score <= 60

    def test_priority_sorting(self):
        """Higher priority findings come first."""
        eng = PriorityEngine()
        findings = [
            DummyFinding.make("low_risk", "info"),
            DummyFinding.make("high_risk", "critical", confidence=0.95),
        ]
        scores = eng.prioritize(findings)
        assert len(scores) == 2
        assert scores[0].score >= scores[1].score

    def test_priority_score_components(self):
        """Score includes component breakdown."""
        eng = PriorityEngine()
        finding = DummyFinding.make("test", "warning")
        scores = eng.prioritize([finding])
        assert len(scores[0].components) >= 5

    def test_category_mapping(self):
        """Score maps to correct category."""
        eng = PriorityEngine()
        finding = DummyFinding.make("mission_failure", "critical", confidence=0.95)
        scores = eng.prioritize([finding])
        assert isinstance(scores[0].category, PriorityCategory)

    def test_priority_score_actionable(self):
        """CRITICAL/HIGH/MEDIUM are actionable."""
        s_high = PriorityScore(finding_id="t", score=85.0, category=PriorityCategory.CRITICAL)
        assert s_high.is_actionable

        s_low = PriorityScore(finding_id="t", score=10.0, category=PriorityCategory.INFO)
        assert not s_low.is_actionable

    def test_config_custom(self):
        """Custom config changes scoring."""
        config = PriorityConfig(
            severity_weight=1.0,
            impact_weight=0.0,
            confidence_weight=0.0,
            trust_weight=0.0,
            age_weight=0.0,
            dependency_weight=0.0,
            resource_weight=0.0,
            trend_weight=0.0,
        )
        eng = PriorityEngine(config=config)
        findings = [
            DummyFinding.make("mission_failure", "critical"),
            DummyFinding.make("system_idle", "info"),
        ]
        scores = eng.prioritize(findings)
        assert len(scores) == 2

    def test_prioritize_convenience(self):
        """prioritize() convenience works."""
        findings = [DummyFinding.make("test", "warning")]
        scores = prioritize(findings)
        assert len(scores) == 1

    def test_build_rec_for_priority(self):
        """build_rec_for_priority returns readable string."""
        s = PriorityScore(finding_id="t", score=90.0, category=PriorityCategory.CRITICAL)
        rec = build_rec_for_priority(DummyFinding.make("t", "critical"), s)
        assert isinstance(rec, str)
        assert len(rec) > 5


# ══════════════════════════════════════════════════════════════════════
# OP-255: MissionOrchestrator Tests
# ══════════════════════════════════════════════════════════════════════


class TestMissionOrchestrator:

    def test_create_orchestrator(self):
        """MissionOrchestrator can be created."""
        orch = MissionOrchestrator()
        assert orch.last_package is None
        assert not orch.is_running

    def test_orchestrate_default(self):
        """orchestrate() runs full pipeline and returns package."""
        orch = MissionOrchestrator(config=OrchestratorConfig(
            auto_observe=True,
            run_rules=True,
            run_analysis=True,
            run_correlation=True,
            run_priority=True,
            run_recommendation=True,
            run_proposal=False,
        ))
        pkg = orch.orchestrate(skip_proposals=True)
        assert isinstance(pkg, OperationalPackage)
        assert pkg.success
        assert pkg.sequence >= 1
        assert pkg.snapshot is not None

    def test_orchestrate_with_proposals(self):
        """orchestrate() generates proposals when skip_proposals=False."""
        orch = MissionOrchestrator(config=OrchestratorConfig(
            auto_observe=True,
            run_rules=True,
            run_analysis=True,
            run_recommendation=True,
            run_proposal=True,
        ))
        pkg = orch.orchestrate(skip_proposals=False)
        assert pkg.success

    def test_orchestrate_sequential(self):
        """Pipeline runs stages sequentially."""
        orch = MissionOrchestrator(config=OrchestratorConfig(
            auto_observe=True,
            run_rules=True,
            run_analysis=True,
            run_correlation=True,
            run_priority=True,
            run_recommendation=True,
            run_proposal=False,
        ))
        pkg = orch.orchestrate(skip_proposals=True)
        # Snapshot first, then rules, etc.
        assert pkg.snapshot is not None
        # At least rules evaluated
        assert isinstance(pkg.triggered_rules, list)

    def test_orchestrate_disabled_observation(self):
        """If observation disabled, pipeline fails gracefully."""
        orch = MissionOrchestrator(config=OrchestratorConfig(
            auto_observe=False,
        ))
        pkg = orch.orchestrate()
        assert not pkg.success
        assert pkg.failed_stage == "observation"

    def test_operational_package_properties(self):
        """OperationalPackage has correct properties."""
        pkg = OperationalPackage(timestamp=0.0, sequence=1)
        assert pkg.finding_count == 0
        assert pkg.triggered_count == 0
        assert pkg.recommendation_count == 0
        assert pkg.proposal_count == 0

    def test_auto_orchestrate_convenience(self):
        """auto_orchestrate() convenience works."""
        pkg = auto_orchestrate(config=OrchestratorConfig(
            auto_observe=True,
            run_rules=True,
            run_analysis=True,
            run_proposal=False,
        ))
        assert isinstance(pkg, OperationalPackage)


# ══════════════════════════════════════════════════════════════════════
# OP-256: ProposalQueue Tests
# ══════════════════════════════════════════════════════════════════════


class TestProposalQueue:

    def test_create_queue(self):
        """ProposalQueue can be created."""
        q = ProposalQueue()
        assert q.size == 0
        assert q.ready_count == 0
        assert q.draft_count == 0

    def test_push_draft(self):
        """push creates a draft item."""
        q = ProposalQueue()
        item = q.push("prop-1", "Test proposal", 80.0)
        assert isinstance(item, QueueItem)
        assert item.state == ProposalState.DRAFT
        assert q.size == 1

    def test_state_transitions(self):
        """Valid state transitions work."""
        q = ProposalQueue()
        q.push("prop-1", "Test", 80.0)

        q.mark_ready("prop-1")
        assert q.get("prop-1").state == ProposalState.READY

        q.mark_waiting("prop-1")
        assert q.get("prop-1").state == ProposalState.WAITING

    def test_invalid_transition(self):
        """Invalid transitions raise error."""
        q = ProposalQueue()
        q.push("prop-1", "Test", 80.0)

        with pytest.raises(InvalidTransitionError):
            q.approve("prop-1")  # can't go DRAFT -> APPROVED

    def test_approve_moves_to_history(self):
        """Approved items move to history."""
        q = ProposalQueue()
        q.push("prop-1", "Test", 80.0)
        q.mark_ready("prop-1")
        q.mark_waiting("prop-1")
        q.approve("prop-1")

        assert q.get("prop-1") is None  # removed from active
        assert len(q.list_history()) >= 1

    def test_reject_moves_to_history(self):
        """Rejected items move to history."""
        q = ProposalQueue()
        q.push("prop-1", "Test", 80.0)
        q.mark_ready("prop-1")
        q.mark_waiting("prop-1")
        q.reject("prop-1")
        assert q.get("prop-1") is None

    def test_expired_proposal(self):
        """Expired proposals handled."""
        q = ProposalQueue()
        q.push("prop-1", "Test", 80.0, ttl_seconds=-1)  # already expired
        count = q.expire_stale()
        assert count >= 1

    def test_priority_ordering(self):
        """Queue orders by priority (highest first) then time."""
        q = ProposalQueue()
        q.push("prop-a", "Low priority", 30.0)
        q.push("prop-b", "High priority", 90.0)
        q.push("prop-c", "Medium priority", 60.0)

        ready = q.list_active()
        # High priority first
        assert ready[0].priority_score == 90.0
        assert ready[-1].priority_score == 30.0

    def test_peek_highest_priority(self):
        """peek() returns highest priority item."""
        q = ProposalQueue()
        q.push("prop-a", "Low", 30.0)
        q.push("prop-b", "High", 90.0)
        top = q.peek()
        assert top is not None
        assert top.priority_score == 90.0

    def test_pop_ready(self):
        """pop_ready returns highest priority READY item."""
        q = ProposalQueue()
        q.push("prop-a", "Medium", 60.0)
        q.push("prop-b", "High", 90.0)
        q.mark_ready("prop-b")
        popped = q.pop_ready()
        assert popped is not None
        assert popped.proposal_id == "prop-b"
        assert popped.state == ProposalState.WAITING

    def test_create_draft_convenience(self):
        """create_draft() convenience works."""
        item = create_draft("test-prop", "Test", 70.0)
        assert isinstance(item, QueueItem)
        assert item.state == ProposalState.DRAFT


# ══════════════════════════════════════════════════════════════════════
# OP-257: OperationalHealthEngine Tests
# ══════════════════════════════════════════════════════════════════════


class TestOperationalHealthEngine:

    def test_create_engine(self):
        """OperationalHealthEngine can be created."""
        eng = OperationalHealthEngine()
        assert eng.last_health is None

    def test_evaluate_all_dimensions(self):
        """evaluate() returns health for all dimensions."""
        health = evaluate_health()
        assert isinstance(health, OperationalHealthDTO)
        assert len(health.dimensions) >= 10
        assert 0 <= health.overall_score <= 100

    def test_overall_status(self):
        """Overall status is green/yellow/red."""
        health = evaluate_health()
        assert health.overall_status in ("green", "yellow", "red")

    def test_single_dimension(self):
        """Can evaluate a single dimension."""
        eng = OperationalHealthEngine()
        dim = eng.evaluate_dimension("observation")
        assert isinstance(dim, DimensionHealth)
        assert dim.dimension == "observation"

    def test_dimension_score_range(self):
        """Each dimension has score 0-100."""
        health = evaluate_health()
        for d in health.dimensions:
            assert 0 <= d.score <= 100, f"{d.dimension} score out of range: {d.score}"

    def test_unknown_dimension(self):
        """Unknown dimension returns RED with error."""
        eng = OperationalHealthEngine()
        dim = eng.evaluate_dimension("nonexistent_thing")
        assert dim.status == "red"

    def test_dimension_map(self):
        """dimension_map returns lookup by name."""
        health = evaluate_health()
        dm = health.dimension_map
        assert "observation" in dm
        assert dm["observation"].dimension == "observation"

    def test_red_and_yellow_properties(self):
        """red_dimensions and yellow_dimensions work."""
        health = evaluate_health()
        assert isinstance(health.red_dimensions, list)
        assert isinstance(health.yellow_dimensions, list)

    def test_get_dimension(self):
        """get_dimension returns specific dimension."""
        health = evaluate_health()
        d = health.get_dimension("rules")
        assert d is None or d.dimension == "rules"

    def test_health_status_from_score(self):
        """HealthStatus.from_score maps correctly."""
        from sam.operations.brain.health import HealthStatus
        assert HealthStatus.from_score(90) == "green"
        assert HealthStatus.from_score(65) == "yellow"
        assert HealthStatus.from_score(30) == "red"


# ══════════════════════════════════════════════════════════════════════
# OP-258: BrainConversationBridgeV2 Tests
# ══════════════════════════════════════════════════════════════════════


class TestBrainConversationBridgeV2:

    def test_create_bridge(self):
        """BrainConversationBridgeV2 can be created."""
        bridge = BrainConversationBridgeV2()
        assert bridge.context.turn_count == 0

    def test_ask_health(self):
        """ask_health returns health answer."""
        bridge = BrainConversationBridgeV2()
        answer = bridge.ask_health()
        assert isinstance(answer, BrainAnswer)
        assert answer.query_type == "health"

    def test_ask_trends(self):
        """ask_trends returns trends answer."""
        bridge = BrainConversationBridgeV2()
        answer = bridge.ask_trends(limit=5)
        assert answer.query_type == "trends"

    def test_ask_risks(self):
        """ask_risks returns risk answer."""
        bridge = BrainConversationBridgeV2()
        answer = bridge.ask_risks()
        assert answer.query_type == "risks"

    def test_ask_changes(self):
        """ask_changes returns changes answer."""
        bridge = BrainConversationBridgeV2()
        answer = bridge.ask_changes()
        assert answer.query_type == "changes"

    def test_ask_recommendations(self):
        """ask_recommendations returns recommendations."""
        bridge = BrainConversationBridgeV2()
        answer = bridge.ask_recommendations()
        assert answer.query_type == "recommendations"

    def test_history_tracked(self):
        """Query history is tracked."""
        bridge = BrainConversationBridgeV2()
        bridge.ask_health()
        bridge.ask_trends()
        assert bridge.context.turn_count == 2
        assert len(bridge.context.last_queries) == 2

    def test_brain_query_dto(self):
        """BrainQuery DTO works."""
        q = BrainQuery(query_type=QueryType.HEALTH, limit=5)
        assert q.query_type == QueryType.HEALTH
        assert q.limit == 5
        assert "health" in repr(q)

    def test_brain_answer_dto(self):
        """BrainAnswer DTO works."""
        a = BrainAnswer(
            query_type="health",
            answer="System is healthy",
            timestamp=time.time(),
        )
        assert a.has_answer
        assert not a.error

    def test_empty_answer(self):
        """Empty answer returns has_answer=False."""
        a = BrainAnswer(query_type="test", answer="", timestamp=0.0)
        assert not a.has_answer

    def test_answer_with_error(self):
        """Answer with error has has_answer=False."""
        a = BrainAnswer(query_type="test", answer="", timestamp=0.0, error="fail")
        assert not a.has_answer

    def test_classify_query(self):
        """classify_query maps keywords to types."""
        assert classify_query("health status") == QueryType.HEALTH
        assert classify_query("high risk") == QueryType.RISKS
        assert classify_query("what changed") == QueryType.CHANGES
        assert classify_query("trends") == QueryType.TRENDS
        assert classify_query("explain why") == QueryType.EXPLAIN
        assert classify_query("unknown text") == QueryType.HEALTH  # fallback

    def test_ask_brain_v2_convenience(self):
        """ask_brain_v2 convenience works."""
        answer = ask_brain_v2("health status")
        assert isinstance(answer, BrainAnswer)

    def test_reset_context(self):
        """reset_context clears history."""
        bridge = BrainConversationBridgeV2()
        bridge.ask_health()
        bridge.reset_context()
        assert bridge.context.turn_count == 0


# ══════════════════════════════════════════════════════════════════════
# OP-259: ProactivePipeline Tests
# ══════════════════════════════════════════════════════════════════════


class TestProactivePipeline:

    def test_create_pipeline(self):
        """ProactivePipeline can be created."""
        pipe = ProactivePipeline()
        assert pipe.last_result is None

    def test_run_full_pipeline(self):
        """run() produces complete result."""
        pipe = ProactivePipeline()
        result = pipe.run()
        assert isinstance(result, ProactivePipelineResult)
        assert result.success
        assert result.sequence >= 1

    def test_run_no_observation(self):
        """run(skip_observation=True) skips that step."""
        pipe = ProactivePipeline()
        result = pipe.run(skip_observation=True)
        assert result.observation is None
        assert result.success

    def test_run_no_health(self):
        """run(skip_health=True) skips health."""
        pipe = ProactivePipeline()
        result = pipe.run(skip_health=True)
        assert result.health is None

    def test_run_no_orchestration(self):
        """run(skip_orchestration=True) skips orchestration."""
        pipe = ProactivePipeline()
        result = pipe.run(skip_orchestration=True)
        assert result.orchestration is None

    def test_create_scheduler_integration(self):
        """create_scheduler returns ObservationScheduler."""
        pipe = ProactivePipeline()
        sched = pipe.create_scheduler(interval_seconds=3600)
        assert isinstance(sched, ObservationScheduler)
        assert sched.config.interval_seconds == 3600

    def test_get_health(self):
        """get_health returns health."""
        pipe = ProactivePipeline()
        health = pipe.get_health()
        assert isinstance(health, OperationalHealthDTO)

    def test_pipeline_summary(self):
        """pipeline_summary produces readable output."""
        pipe = ProactivePipeline()
        result = pipe.run()
        summary = pipeline_summary(result)
        assert isinstance(summary, str)
        assert "Pipeline" in summary

    def test_run_proactive_pipeline_convenience(self):
        """run_proactive_pipeline() convenience works."""
        result = run_proactive_pipeline()
        assert isinstance(result, ProactivePipelineResult)
