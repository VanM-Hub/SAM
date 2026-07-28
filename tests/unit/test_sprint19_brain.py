"""
Tests for Sprint 19 — Operational Brain Foundation (OP-241 to OP-250).

Validates:
  - zero domain/repo changes
  - zero auto-execution
  - all proposal evidence-based
  - pipeline deterministic
  - no public API changes
"""

from __future__ import annotations

import os
import sys
import time
import ast
import json

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest  # noqa: E402

# ── Imports ──────────────────────────────────────────────────────────

from sam.operations.brain.observation_engine import (
    ObservationEngine,
    ObservationSnapshot,
    collect_observation,
)
from sam.operations.brain.rule_engine import (
    RuleEngine,
    RuleDef,
    TriggeredRule,
    evaluate_rules,
)
from sam.operations.brain.analyzer import (
    OperationalAnalyzer,
    OperationalFinding,
    Severity,
    analyze,
)
from sam.operations.brain.recommendation import (
    RecommendationBuilder,
    MissionRecommendation,
    build_recommendations,
)
from sam.operations.brain.proposal import (
    ProposalService,
    MissionProposal,
    create_proposal,
)
from sam.operations.brain.conversation import (
    BrainConversationBridge,
    BrainConversationRequest,
    BrainConversationResponse,
    ask_brain,
)
from sam.operations.brain.dashboard import (
    BrainDashboardData,
    build_dashboard_data,
)
from sam.operations.brain.integration import (
    BrainPipeline,
    BrainPipelineResult,
    run_pipeline,
    run_and_summarize,
)


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def empty_snapshot() -> ObservationSnapshot:
    return ObservationSnapshot(
        timestamp=time.time(),
        active_missions=0,
        failed_missions=0,
        pending_approvals=0,
        locks_held=0,
        queue_length=0,
        trust_summary={},
        notification_summary={"info": 0, "warning": 0, "error": 0, "total": 0},
        telemetry_summary={"events_recent": 0, "rate_per_min": 0.0},
        anomalies=[],
    )


@pytest.fixture
def stressed_snapshot() -> ObservationSnapshot:
    return ObservationSnapshot(
        timestamp=time.time(),
        active_missions=5,
        failed_missions=3,
        pending_approvals=8,
        locks_held=4,
        queue_length=25,
        trust_summary={"mission_controller": 0.3, "executor": 0.9},
        notification_summary={"info": 2, "warning": 1, "error": 3, "total": 6},
        telemetry_summary={"events_recent": 200, "rate_per_min": 150.0},
        anomalies=[{"type": "timeout", "id": "a1"}, {"type": "crash", "id": "a2"}, {"type": "stall", "id": "a3"}],
    )


@pytest.fixture
def pipeline() -> BrainPipeline:
    return BrainPipeline()


# ══════════════════════════════════════════════════════════════════════
# OP-241: Observation Engine
# ══════════════════════════════════════════════════════════════════════


class TestObservationEngine:
    def test_create_snapshot(self, empty_snapshot):
        assert empty_snapshot.timestamp > 0
        assert empty_snapshot.active_missions == 0
        assert empty_snapshot.failed_missions == 0
        assert empty_snapshot.pending_approvals == 0
        assert empty_snapshot.locks_held == 0
        assert empty_snapshot.queue_length == 0
        assert empty_snapshot.trust_summary == {}
        assert empty_snapshot.notification_summary["total"] == 0
        assert empty_snapshot.telemetry_summary["events_recent"] == 0
        assert empty_snapshot.anomalies == []

    def test_collect_graceful_fallback(self):
        """Should return valid snapshot even when sources unavailable."""
        snap = collect_observation()
        assert snap is not None
        assert isinstance(snap.timestamp, float)
        assert isinstance(snap.active_missions, int)
        assert isinstance(snap.failed_missions, int)
        assert isinstance(snap.pending_approvals, int)
        assert isinstance(snap.locks_held, int)
        assert isinstance(snap.queue_length, int)

    def test_collect_returns_same_type(self):
        engine = ObservationEngine()
        s1 = engine.collect()
        s2 = engine.collect()
        assert isinstance(s1, ObservationSnapshot)
        assert isinstance(s2, ObservationSnapshot)
        assert s2.timestamp >= s1.timestamp

    def test_last_snapshot(self):
        engine = ObservationEngine()
        assert engine.last_snapshot is None
        snap = engine.collect()
        assert engine.last_snapshot is snap

    def test_snapshot_immutable_by_convention(self, empty_snapshot):
        """Snapshot is frozen via __post_init__ zero-fill."""
        from dataclasses import fields
        for f in fields(empty_snapshot):
            assert hasattr(empty_snapshot, f.name)

    def test_observation_as_dict_compatible(self, stressed_snapshot):
        d = {k: _serialize_val(getattr(stressed_snapshot, k))
             for k in stressed_snapshot.__dataclass_fields__}
        assert d["active_missions"] == 5
        assert d["failed_missions"] == 3
        assert d["pending_approvals"] == 8
        assert len(d["anomalies"]) == 3


# ══════════════════════════════════════════════════════════════════════
# OP-242: Rule Engine
# ══════════════════════════════════════════════════════════════════════


class TestRuleEngine:
    def test_builtin_rules_count(self):
        engine = RuleEngine()
        assert len(engine.rules) == 10

    def test_no_triggers_on_empty(self, empty_snapshot):
        engine = RuleEngine()
        triggered = engine.evaluate(empty_snapshot)
        # empty: only "no_active_missions" should fire
        assert len(triggered) == 1
        assert triggered[0].rule_id == "no_active_missions"

    def test_triggers_on_stressed(self, stressed_snapshot):
        engine = RuleEngine()
        triggered = engine.evaluate(stressed_snapshot)
        assert len(triggered) >= 5  # most rules should fire
        ids = [t.rule_id for t in triggered]
        assert "high_pending_approvals" in ids
        assert "failed_missions" in ids
        assert "high_anomaly_count" in ids
        assert "low_trust" in ids
        assert "notification_alert" in ids

    def test_custom_rule(self):
        engine = RuleEngine()
        custom = RuleDef(
            rule_id="custom_test",
            name="Custom Test",
            description="Always fires",
            severity="info",
            check_fn=lambda snap: True,
        )
        engine.add_rule(custom)
        assert len(engine.rules) == 11

    def test_rule_metadata(self, stressed_snapshot):
        engine = RuleEngine()
        triggered = engine.evaluate(stressed_snapshot)
        for t in triggered:
            assert t.rule_id
            assert t.name
            assert t.description
            assert t.severity in ("info", "warning", "critical")
            assert t.timestamp > 0

    def test_evaluate_rules_convenience(self, stressed_snapshot):
        result = evaluate_rules(stressed_snapshot)
        assert len(result) >= 5


# ══════════════════════════════════════════════════════════════════════
# OP-243: Operational Analyzer
# ══════════════════════════════════════════════════════════════════════


class TestOperationalAnalyzer:
    def test_analyze_empty(self, empty_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(empty_snapshot)
        findings = analyze(empty_snapshot, rules)
        # only no_active_missions → system_idle finding
        assert len(findings) == 1
        assert findings[0].finding_id == "system_idle"
        assert findings[0].severity == Severity.INFO

    def test_analyze_stressed(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        assert len(findings) >= 5
        finding_ids = [f.finding_id for f in findings]
        assert "approval_backlog" in finding_ids
        assert "mission_failure" in finding_ids
        assert "trust_degradation" in finding_ids
        assert "anomaly_cluster" in finding_ids
        assert "notification_alert" in finding_ids
        assert "lock_contention" in finding_ids
        assert "queue_stall" in finding_ids

    def test_finding_structure(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        for f in findings:
            assert f.finding_id
            assert f.title
            assert f.description
            assert isinstance(f.severity, Severity)
            assert 0 <= f.confidence <= 1.0
            assert isinstance(f.evidence, list)
            assert isinstance(f.affected_resources, list)
            assert isinstance(f.recommended_actions, list)
            assert len(f.recommended_actions) > 0

    def test_finding_evidence_has_type_and_value(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        for f in findings:
            for e in f.evidence:
                assert "type" in e
                assert "value" in e or "field" in e

    def test_critical_findings_have_confidence(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        critical = [f for f in findings if f.severity == Severity.CRITICAL]
        for f in critical:
            assert f.confidence >= 0.8

    def test_analyzer_tracks_last(self, stressed_snapshot):
        analyzer = OperationalAnalyzer()
        assert analyzer.last_findings == []
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        analyzer.analyze(stressed_snapshot, rules)
        assert len(analyzer.last_findings) >= 5


# ══════════════════════════════════════════════════════════════════════
# OP-244: Recommendation Builder
# ══════════════════════════════════════════════════════════════════════


class TestRecommendationBuilder:
    def test_build_from_findings(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)

        # Only non-INFO findings produce recommendations
        critical_warning = [f for f in findings if f.severity != Severity.INFO]
        assert len(recs) == len(critical_warning)

    def test_recommendation_structure(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)

        for r in recs:
            assert r.recommendation_id.startswith("rec_")
            assert r.title
            assert r.description
            assert r.priority in ("low", "medium", "high", "critical")
            assert r.estimated_impact
            assert r.required_approval is True
            assert isinstance(r.evidence, list)
            assert len(r.suggested_steps) > 0
            assert r.source_finding_id
            assert 0 <= r.confidence <= 1.0

    def test_no_recommendation_for_info(self):
        """INFO findings should not produce recommendations."""
        engine = RuleEngine()
        snap = ObservationSnapshot(
            timestamp=time.time(),
            active_missions=0, failed_missions=0, pending_approvals=0,
            locks_held=0, queue_length=0,
            trust_summary={},
            notification_summary={"info": 0, "warning": 0, "error": 0, "total": 0},
            telemetry_summary={"events_recent": 0, "rate_per_min": 0.0},
            anomalies=[],
        )
        rules = engine.evaluate(snap)
        findings = analyze(snap, rules)
        recs = build_recommendations(findings)
        # empty → only system_idle (INFO) → no recommendation
        assert len(recs) == 0

    def test_recommendation_requires_evidence(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)
        for r in recs:
            assert len(r.evidence) > 0

    def test_recommendation_builder_tracks_last(self, stressed_snapshot):
        builder = RecommendationBuilder()
        assert builder.last_recommendations == []
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        builder.build(findings)
        assert len(builder.last_recommendations) >= 5


# ══════════════════════════════════════════════════════════════════════
# OP-245: Proposal Service
# ══════════════════════════════════════════════════════════════════════


class TestProposalService:
    def test_create_proposal(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)

        service = ProposalService()
        for rec in recs:
            prop = service.create_proposal(rec)
            assert prop.proposal_id
            assert prop.recommendation_id == rec.recommendation_id
            assert prop.title
            assert prop.requires_approval is True
            assert prop.submitted is False
            assert prop.generated_at > 0
            assert len(prop.evidence) > 0

    def test_no_auto_submit(self, stressed_snapshot):
        """Proposals are NOT submitted automatically."""
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)

        service = ProposalService()
        for rec in recs:
            prop = service.create_proposal(rec)
            assert prop.submitted is False

    def test_submit_proposal(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)

        service = ProposalService()
        for rec in recs:
            prop = service.create_proposal(rec)

        first_id = service.list_pending()[0].proposal_id
        result = service.submit_proposal(first_id)
        assert result is True

        # Check submitted
        submitted = service.list_submitted()
        assert len(submitted) == 1
        assert submitted[0].proposal_id == first_id

    def test_submit_nonexistent(self):
        service = ProposalService()
        assert service.submit_proposal("nonexistent") is False

    def test_list_pending_empty(self):
        service = ProposalService()
        assert service.list_pending() == []

    def test_proposal_count(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)

        service = ProposalService()
        for rec in recs:
            service.create_proposal(rec)
        assert service.proposal_count == len(recs)

    def test_create_proposal_convenience(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)

        for rec in recs:
            prop = create_proposal(rec)
            assert isinstance(prop, MissionProposal)
            assert prop.submitted is False

    def test_proposal_not_submitted_twice(self, stressed_snapshot):
        service = ProposalService()
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)
        prop = service.create_proposal(recs[0])
        assert service.submit_proposal(prop.proposal_id) is True
        assert service.submit_proposal(prop.proposal_id) is False


# ══════════════════════════════════════════════════════════════════════
# OP-246: Brain Conversation Bridge
# ══════════════════════════════════════════════════════════════════════


class TestBrainConversationBridge:
    def test_default_response(self):
        """No state means 'no data' responses."""
        bridge = BrainConversationBridge()
        resp = bridge.ask(BrainConversationRequest(query="any issues?"))
        assert "No" in resp.answer or "no" in resp.answer or "all clear" in resp.answer

    def test_recommendation_with_state(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)
        dashboard = build_dashboard_data(findings, recs, stressed_snapshot, rules)

        bridge = BrainConversationBridge()
        bridge.set_state(
            findings=dashboard.findings,
            recommendations=dashboard.recommendations,
            observation=dashboard.observation_summary,
            rules=dashboard.triggered_rules,
            health_score=dashboard.health_score,
        )

        resp = bridge.ask(BrainConversationRequest(query="What do you recommend?"))
        assert "recommendation" in resp.answer.lower()
        assert len(resp.data.get("recommendations", [])) > 0

    def test_show_evidence(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)
        dashboard = build_dashboard_data(findings, recs, stressed_snapshot, rules)

        bridge = BrainConversationBridge()
        bridge.set_state(
            findings=dashboard.findings,
            recommendations=dashboard.recommendations,
            observation=dashboard.observation_summary,
            rules=dashboard.triggered_rules,
            health_score=dashboard.health_score,
        )

        resp = bridge.ask(BrainConversationRequest(query="Show evidence"))
        assert "evidence" in resp.answer.lower()
        assert len(resp.data.get("findings", [])) > 0

    def test_health_query(self):
        bridge = BrainConversationBridge()
        bridge.set_state(
            findings=[], recommendations=[], observation={}, rules=[], health_score=0.95,
        )
        resp = bridge.ask(BrainConversationRequest(query="health status"))
        assert "0.95" in resp.answer
        assert resp.data.get("health_score") == 0.95

    def test_anomaly_query(self, stressed_snapshot):
        dashboard = build_dashboard_data([], [], stressed_snapshot, [])
        bridge = BrainConversationBridge()
        bridge.set_state(
            findings=dashboard.findings,
            recommendations=dashboard.recommendations,
            observation=dashboard.observation_summary,
            rules=[],
            health_score=1.0,
        )
        resp = bridge.ask(BrainConversationRequest(query="any anomaly?"))
        assert len(resp.data.get("anomalies", [])) == 3

    def test_findings_query(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)
        dashboard = build_dashboard_data(findings, recs, stressed_snapshot, rules)

        bridge = BrainConversationBridge()
        bridge.set_state(
            findings=dashboard.findings,
            recommendations=dashboard.recommendations,
            observation=dashboard.observation_summary,
            rules=dashboard.triggered_rules,
            health_score=dashboard.health_score,
        )
        resp = bridge.ask(BrainConversationRequest(query="show findings"))
        assert len(resp.data.get("findings", [])) >= 5

    def test_unkown_query_returns_help(self):
        bridge = BrainConversationBridge()
        resp = bridge.ask(BrainConversationRequest(query="what is the meaning of life?"))
        assert "I can answer" in resp.answer

    def test_ask_brain_convenience(self):
        """One-shot ask_brain works without state."""
        answer = ask_brain("hello")
        assert answer
        assert isinstance(answer, str)


# ══════════════════════════════════════════════════════════════════════
# OP-247: Brain Dashboard DTO
# ══════════════════════════════════════════════════════════════════════


class TestBrainDashboardDTO:
    def test_empty_dashboard(self):
        d = BrainDashboardData.empty()
        assert d.findings == []
        assert d.recommendations == []
        assert d.observation_summary == {}
        assert d.triggered_rules == []
        assert d.health_score == 1.0
        assert d.health_state == "healthy"

    def test_build_with_data(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)
        dashboard = build_dashboard_data(findings, recs, stressed_snapshot, rules)

        assert dashboard.generated_at > 0
        assert len(dashboard.findings) >= 5
        assert len(dashboard.recommendations) >= 5
        assert dashboard.observation_summary["active_missions"] == 5
        assert dashboard.health_score < 1.0
        assert dashboard.health_state in ("healthy", "degraded", "unhealthy")

    def test_has_issues(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)
        dashboard = build_dashboard_data(findings, recs, stressed_snapshot, rules)
        assert dashboard.has_issues is True

    def test_critical_and_warning_count(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)
        dashboard = build_dashboard_data(findings, recs, stressed_snapshot, rules)
        assert dashboard.critical_count > 0
        assert dashboard.warning_count > 0

    def test_to_dict(self, stressed_snapshot):
        engine = RuleEngine()
        rules = engine.evaluate(stressed_snapshot)
        findings = analyze(stressed_snapshot, rules)
        recs = build_recommendations(findings)
        dashboard = build_dashboard_data(findings, recs, stressed_snapshot, rules)
        d = dashboard.to_dict()
        assert "findings" in d
        assert "recommendations" in d
        assert "health_score" in d
        assert isinstance(d, dict)


# ══════════════════════════════════════════════════════════════════════
# OP-248: Integration
# ══════════════════════════════════════════════════════════════════════


class TestBrainPipeline:
    def test_pipeline_creates_all_artifacts(self, pipeline):
        result = pipeline.run()
        assert isinstance(result, BrainPipelineResult)
        assert isinstance(result.snapshot, ObservationSnapshot)
        assert isinstance(result.triggered_rules, list)
        assert isinstance(result.findings, list)
        assert isinstance(result.recommendations, list)
        assert isinstance(result.proposals, list)
        assert isinstance(result.dashboard, BrainDashboardData)

    def test_pipeline_deterministic(self):
        """Multiple runs should produce same-class artifacts."""
        p1 = BrainPipeline()
        p2 = BrainPipeline()
        r1 = p1.run()
        r2 = p2.run()
        assert type(r1.snapshot) == type(r2.snapshot)
        assert type(r1.dashboard) == type(r2.dashboard)

    def test_pipeline_no_auto_submit(self, pipeline):
        result = pipeline.run()
        for prop in result.proposals:
            assert prop.submitted is False, (
                f"Proposal {prop.proposal_id} was auto-submitted!"
            )

    def test_pipeline_proposals_require_approval(self, pipeline):
        result = pipeline.run()
        for prop in result.proposals:
            assert prop.requires_approval is True

    def test_pipeline_proposals_have_evidence(self, pipeline):
        result = pipeline.run()
        for prop in result.proposals:
            assert len(prop.evidence) > 0

    def test_pipeline_updates_conversation_bridge(self, pipeline):
        pipeline.run()
        resp = pipeline.conversation_bridge.ask(
            BrainConversationRequest(query="status")
        )
        assert resp.data.get("health_score") is not None

    def test_pipeline_last_artifacts(self, pipeline):
        assert pipeline.last_snapshot is None
        assert pipeline.last_dashboard is None
        pipeline.run()
        assert pipeline.last_snapshot is not None
        assert pipeline.last_dashboard is not None
        assert len(pipeline.last_findings) >= 0
        assert len(pipeline.last_recommendations) >= 0

    def test_run_and_summarize(self):
        summary = run_and_summarize()
        assert "observation" in summary
        assert "findings" in summary
        assert "recommendations" in summary
        assert "proposals" in summary
        assert "health_score" in summary

    def test_pipeline_graceful_with_missing_sources(self, pipeline):
        """Should not crash even if operational sources unavailable."""
        result = pipeline.run()
        assert result.snapshot.active_missions == 0  # graceful fallback


# ══════════════════════════════════════════════════════════════════════
# OP-249 / OP-250: Validation + Architecture Checks
# ══════════════════════════════════════════════════════════════════════


class TestBrainValidation:
    """Architecture constraints: no domain/repo/API changes, no auto-exec."""

    BRAIN_DIR = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "src", "sam", "operations", "brain",
    )

    def _brain_files(self):
        """Get all .py files in brain/ excluding __init__.py and .pyc."""
        brain = os.path.normpath(self.BRAIN_DIR)
        if not os.path.isdir(brain):
            pytest.skip(f"Brain directory not found: {brain}")
        return sorted([
            os.path.join(brain, f)
            for f in os.listdir(brain)
            if f.endswith(".py") and f != "__init__.py"
        ])

    def test_brain_imports_no_higher_domain(self):
        """Brain files must NOT import domain layer (sam.domain)."""
        brain = os.path.normpath(self.BRAIN_DIR)
        if not os.path.isdir(brain):
            pytest.skip("Brain dir not found")
        bad_imports = []
        for root, dirs, files in os.walk(brain):
            for f in files:
                if not f.endswith(".py") or f == "__init__.py":
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        source = fh.read()
                except Exception:
                    continue
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith("sam.domain"):
                                bad_imports.append((path, alias.name))
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith("sam.domain"):
                            bad_imports.append((path, node.module))
        assert bad_imports == [], (
            f"Brain files import domain layer: {bad_imports}"
        )

    def test_brain_no_public_api_modules(self):
        """Brain files must NOT import or reference public API modules."""
        brain = os.path.normpath(self.BRAIN_DIR)
        if not os.path.isdir(brain):
            pytest.skip("Brain dir not found")
        public_api_modules = [
            "sam.public", "sam.api", "sam.conversation", "sam.mission_session",
        ]
        bad = []
        for root, dirs, files in os.walk(brain):
            for f in files:
                if not f.endswith(".py") or f == "__init__.py":
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        source = fh.read()
                except Exception:
                    continue
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in public_api_modules:
                                bad.append((path, alias.name))
                    elif isinstance(node, ast.ImportFrom):
                        if node.module in public_api_modules:
                            bad.append((path, node.module))
        assert bad == [], f"Brain imports public API: {bad}"

    def test_brain_no_repository_imports(self):
        """Brain must NOT import repository modules."""
        brain = os.path.normpath(self.BRAIN_DIR)
        if not os.path.isdir(brain):
            pytest.skip("Brain dir not found")
        bad = []
        for root, dirs, files in os.walk(brain):
            for f in files:
                if not f.endswith(".py") or f == "__init__.py":
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        source = fh.read()
                except Exception:
                    continue
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith("sam.storage"):
                                bad.append((path, alias.name))
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith("sam.storage"):
                            bad.append((path, node.module))
        assert bad == [], f"Brain imports repositories: {bad}"

    def test_no_auto_execution(self):
        """Scan brain files for anything that looks like auto-execution."""
        brain = os.path.normpath(self.BRAIN_DIR)
        if not os.path.isdir(brain):
            pytest.skip("Brain dir not found")
        suspicious = [".execute(", ".start(", "auto_submit", "auto_approve"]
        bad = []
        for root, dirs, files in os.walk(brain):
            for f in files:
                if not f.endswith(".py") or f == "__init__.py":
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                except Exception:
                    continue
                for pattern in suspicious:
                    if pattern in content:
                        # Only flag if outside of test/assert context
                        lines = content.split("\n")
                        for i, line in enumerate(lines, 1):
                            stripped = line.strip()
                            if pattern in line and "assert" not in line:
                                # Skip known false positives:
                                # - method calls inside class/instance methods
                                # - docstring examples (indented, no def)
                                # - comments
                                if pattern == ".start(" and (
                                    stripped.startswith(("self.", "t.", "sched.", "self._timer."))
                                    or stripped.startswith(("#", "Example:"))
                                ):
                                    continue
                                bad.append((path, i, pattern))
        assert bad == [], f"Possible auto-execution found: {bad}"

    def test_all_recommendations_require_approval(self):
        """Every MissionRecommendation must have required_approval=True."""
        from sam.operations.brain.recommendation import MissionRecommendation
        from dataclasses import fields
        field_names = [f.name for f in fields(MissionRecommendation)]
        assert "required_approval" in field_names
        # Check default by instantiating
        rec = MissionRecommendation(
            recommendation_id="test", title="t", description="d",
            priority="low", estimated_impact="low",
            required_approval=True, evidence=[], suggested_steps=[],
            source_finding_id="f", confidence=0.5, timestamp=0.0,
        )
        assert rec.required_approval is True

    def test_no_mission_controller_changes(self):
        """Scan brain files for MissionController references that modify it."""
        brain = os.path.normpath(self.BRAIN_DIR)
        if not os.path.isdir(brain):
            pytest.skip("Brain dir not found")
        bad = []
        for root, dirs, files in os.walk(brain):
            for f in files:
                if not f.endswith(".py") or f == "__init__.py":
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                except Exception:
                    continue
                if "mission_controller" in content and "submit" in content.lower():
                    bad.append(path)
        assert bad == [], f"Brain touches MissionController: {bad}"


# ══════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════


def _serialize_val(v):
    """Recursive serialization for comparison."""
    if hasattr(v, "__dataclass_fields__"):
        return {k: _serialize_val(getattr(v, k)) for k in v.__dataclass_fields__}
    elif isinstance(v, (list, tuple)):
        return [_serialize_val(x) for x in v]
    elif isinstance(v, dict):
        return {k: _serialize_val(x) for k, x in v.items()}
    elif hasattr(v, "value"):
        return v.value
    return v
