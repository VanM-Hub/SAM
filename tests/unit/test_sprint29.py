"""Sprint 29 — Guardian Governance & Execution Coordination Tests."""

import pytest
from datetime import datetime
from sam.operations.brain.guardian import (
    # OP-341
    GuardianGovernanceEngine, GovernanceResult, GovernanceDecision,
    GovernanceEvidence, GovernanceStatus, GovernanceStage,
    # OP-342
    ExecutionReadinessEvaluator, ExecutionReadiness, ReadinessCheck, ReadinessLevel,
    # OP-343
    GuardianRiskAssessment, RiskAssessment, RiskDimension, RiskLevel,
    # OP-344
    GuardianDecisionExplanation, GovernanceExplanation, ExplanationSection,
    # OP-345
    GuardianCoordinationRuntime, CoordinationResult,
    # OP-346
    GovernanceConversationBridge, GovernanceConversationResponse,
    # OP-347
    GuardianDashboardV3Service, GovernanceCard, RiskCard, ReadinessCard,
    PolicyCard, GuardianSummaryCard, BlockedMissionsCard,
    PendingApprovalCard, OperationalStatusCard,
    # OP-348
    GuardianRuntimeV3Integration, V3IntegrationResult,
)


# ══════════════════════════════════════════════════════════════════
# OP-341: GuardianGovernanceEngine
# ══════════════════════════════════════════════════════════════════

class TestGuardianGovernanceEngine:
    """15 test untuk governance engine."""

    def test_all_approved(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate()
        assert r.approved is True
        assert r.overall_status == GovernanceStatus.APPROVED

    def test_policy_rejected(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(policy_passed=False, policy_violations=2)
        assert r.approved is False
        assert r.overall_status == GovernanceStatus.REJECTED
        assert "policy" in r.failed_stages

    def test_health_critical(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(health_status="critical", health_score=0.2)
        assert r.approved is False
        assert r.overall_status == GovernanceStatus.DEFERRED

    def test_decision_not_approved(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(decision_approved=False)
        assert r.approved is False
        assert r.overall_status == GovernanceStatus.REJECTED

    def test_approval_incomplete(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(approval_complete=False, approval_required=3, approval_granted=1)
        assert r.approved is False
        assert r.overall_status == GovernanceStatus.DEFERRED

    def test_recommendation_high_risk(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(recommendation_risk="high")
        assert r.approved is False
        assert r.overall_status == GovernanceStatus.ESCALATED

    def test_all_failing(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(
            policy_passed=False, policy_violations=3,
            health_status="critical", health_score=0.1,
            decision_approved=False, decision_confidence=0.3,
            approval_complete=False, approval_required=2, approval_granted=0,
            recommendation_support=False, recommendation_risk="high",
        )
        assert r.approved is False
        assert r.stage_count == 5

    def test_governance_id(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(governance_id="test-gov-1")
        assert r.governance_id == "test-gov-1"

    def test_evaluation_count(self):
        engine = GuardianGovernanceEngine()
        assert engine.evaluation_count == 0
        engine.evaluate()
        assert engine.evaluation_count == 1
        engine.evaluate()
        assert engine.evaluation_count == 2

    def test_stage_decisions_dict(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate()
        d = r.stage_decisions
        assert "policy" in d
        assert "health" in d
        assert "decision" in d
        assert "approval" in d
        assert "recommendation" in d

    def test_governance_decision_properties(self):
        d = GovernanceDecision(
            stage=GovernanceStage.POLICY,
            status=GovernanceStatus.APPROVED,
            score=1.0,
        )
        assert d.passed is True
        assert d.evidence_count == 0
        assert d.passing_evidence == []

    def test_governance_evidence(self):
        e = GovernanceEvidence("policy", "test", True, True, "OK")
        assert e.stage == "policy"
        assert e.is_passing is True
        ed = e.to_dict()
        assert ed["key"] == "test"

    def test_governance_result_to_dict(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate()
        d = r.to_dict()
        assert "governance_id" in d
        assert "overall_status" in d
        assert "stage_count" in d

    def test_mixed_statuses(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(
            policy_passed=True,
            health_status="degraded", health_score=0.6,
            decision_approved=True, decision_confidence=0.9,
            approval_complete=True,
            recommendation_support=True, recommendation_risk="low",
        )
        assert r.approved is True  # degraded masih pass

    def test_engine_immutable(self):
        engine = GuardianGovernanceEngine()
        r = engine.evaluate()
        with pytest.raises(AttributeError):
            r.overall_status = GovernanceStatus.REJECTED  # frozen


# ══════════════════════════════════════════════════════════════════
# OP-342: ExecutionReadinessEvaluator
# ══════════════════════════════════════════════════════════════════

class TestExecutionReadinessEvaluator:
    """15 test untuk readiness evaluator."""

    def test_ready_all_green(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate()
        assert r.ready is True
        assert r.overall_level == ReadinessLevel.READY

    def test_blocked_guardian_health(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate(guardian_healthy=False, guardian_score=0.3)
        assert r.ready is False
        assert ReadinessLevel.BLOCKED in (r.overall_level,)

    def test_denied_policy(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate(policy_passed=False, policy_violations=2)
        assert r.ready is False
        assert r.overall_level == ReadinessLevel.DENIED

    def test_waiting_approval(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate(approval_complete=False, approval_rate=0.5)
        assert r.ready is False
        assert r.overall_level == ReadinessLevel.WAITING

    def test_waiting_evidence(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate(evidence_count=0, evidence_minimum=2)
        assert r.ready is False
        assert r.overall_level == ReadinessLevel.WAITING

    def test_review_confidence(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate(confidence_score=0.5, confidence_threshold=0.7)
        assert r.ready is False
        assert r.overall_level == ReadinessLevel.REVIEW

    def test_blocked_conflict(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate(conflict_detected=True, conflict_count=2)
        assert r.ready is False

    def test_waiting_dependency(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate(dependency_complete=False, dependency_pending=3)
        assert r.ready is False
        assert r.overall_level == ReadinessLevel.WAITING

    def test_evaluation_count(self):
        evalr = ExecutionReadinessEvaluator()
        assert evalr.evaluation_count == 0
        evalr.evaluate()
        assert evalr.evaluation_count == 1

    def test_blocking_dimensions(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate(
            approval_complete=False,
            policy_passed=False,
            guardian_healthy=False,
        )
        assert len(r.blocking_dimensions) >= 1

    def test_readiness_check_properties(self):
        c = ReadinessCheck("test", True, ReadinessLevel.READY, 1.0, "OK")
        assert c.passed is True
        d = c.to_dict()
        assert d["dimension"] == "test"

    def test_execution_readiness_properties(self):
        c1 = ReadinessCheck("a", True, ReadinessLevel.READY, 1.0, "OK")
        c2 = ReadinessCheck("b", False, ReadinessLevel.BLOCKED, 0.0, "Fail")
        r = ExecutionReadiness("er-1", ReadinessLevel.BLOCKED, checks=(c1, c2))
        assert r.ready is False
        assert r.check_count == 2
        assert len(r.passed_checks) == 1
        assert len(r.failed_checks) == 1

    def test_readiness_id(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate(readiness_id="er-test")
        assert r.readiness_id == "er-test"

    def test_recommendations_generated(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate(approval_complete=False)
        assert len(r.recommendations) >= 1

    def test_all_dimensions_present(self):
        evalr = ExecutionReadinessEvaluator()
        r = evalr.evaluate()
        dims = [c.dimension for c in r.checks]
        for d in ["approval", "policy", "confidence", "evidence",
                   "guardian_health", "conflict", "dependency"]:
            assert d in dims, f"Missing dimension: {d}"

    def test_frozen_dto(self):
        r = ExecutionReadiness("er-1", ReadinessLevel.READY)
        with pytest.raises(AttributeError):
            r.overall_level = ReadinessLevel.BLOCKED


# ══════════════════════════════════════════════════════════════════
# OP-343: GuardianRiskAssessment
# ══════════════════════════════════════════════════════════════════

class TestGuardianRiskAssessment:
    """12 test untuk risk assessment."""

    def test_no_risk(self):
        assess = GuardianRiskAssessment()
        r = assess.assess()
        assert r.is_safe is True

    def test_health_critical(self):
        assess = GuardianRiskAssessment()
        r = assess.assess(system_health="critical", health_score=0.2)
        assert r.is_safe is False

    def test_policy_violations(self):
        assess = GuardianRiskAssessment()
        r = assess.assess(policy_violations=3)
        assert r.is_safe is False
        assert "policy" in r.top_risks

    def test_high_complexity(self):
        assess = GuardianRiskAssessment()
        r = assess.assess(execution_complexity="critical")
        assert r.is_safe is False
        assert "execution" in r.top_risks

    def test_missing_approvals(self):
        assess = GuardianRiskAssessment()
        r = assess.assess(approval_missing=3, approval_required=5)
        assert r.is_safe is False
        # approval risk score = 3/5 = 0.6 → medium
        assert "approval" in r.top_risks or r.overall_level.value in ("medium", "high", "critical")

    def test_low_confidence(self):
        assess = GuardianRiskAssessment()
        r = assess.assess(confidence_score=0.3, evidence_quality=0.4)
        assert r.is_safe is False
        assert "confidence" in r.top_risks

    def test_all_high_risk(self):
        assess = GuardianRiskAssessment()
        r = assess.assess(
            system_health="critical", health_score=0.1,
            policy_violations=5, execution_complexity="critical",
            dependency_pending=10, dependency_count=10,
            approval_missing=5, approval_required=5,
            confidence_score=0.1, evidence_quality=0.1,
        )
        assert r.is_safe is False
        assert r.overall_level == RiskLevel.CRITICAL

    def test_assessment_id(self):
        assess = GuardianRiskAssessment()
        r = assess.assess(assessment_id="ra-test")
        assert r.assessment_id == "ra-test"

    def test_assessment_count(self):
        assess = GuardianRiskAssessment()
        assert assess.assessment_count == 0
        assess.assess()
        assert assess.assessment_count == 1

    def test_all_six_dimensions(self):
        assess = GuardianRiskAssessment()
        r = assess.assess()
        dims = [d.dimension for d in r.dimensions]
        for d in ["operational", "policy", "execution",
                   "dependency", "approval", "confidence"]:
            assert d in dims, f"Missing dimension: {d}"

    def test_risk_dimension_properties(self):
        d = RiskDimension("test", RiskLevel.HIGH, 0.8, ("factor1",), "Desc")
        assert d.is_significant is True
        d2 = RiskDimension("test", RiskLevel.LOW, 0.2)
        assert d2.is_significant is False
        dd = d.to_dict()
        assert dd["level"] == "high"

    def test_frozen_dto(self):
        r = RiskAssessment("ra-1", RiskLevel.LOW)
        with pytest.raises(AttributeError):
            r.overall_level = RiskLevel.HIGH


# ══════════════════════════════════════════════════════════════════
# OP-344: GuardianDecisionExplanation
# ══════════════════════════════════════════════════════════════════

class TestGuardianDecisionExplanation:
    """10 test untuk explanation engine."""

    def test_approved_explanation(self):
        expl = GuardianDecisionExplanation()
        r = expl.build(governance_status="approved", governance_score=1.0)
        assert r.decision == "approved"
        assert "APPROVED" in r.summary
        assert r.section_count >= 1

    def test_rejected_explanation(self):
        expl = GuardianDecisionExplanation()
        r = expl.build(
            governance_status="rejected",
            policy_passed=False, policy_violations=3,
        )
        assert r.decision == "rejected"
        assert "REJECTED" in r.summary
        assert len(r.next_actions) >= 1

    def test_deferred_explanation(self):
        expl = GuardianDecisionExplanation()
        r = expl.build(
            governance_status="deferred",
            approval_complete=False, approval_granted=1, approval_required=3,
        )
        assert r.decision == "deferred"
        assert "DEFERRED" in r.summary

    def test_escalated_explanation(self):
        expl = GuardianDecisionExplanation()
        r = expl.build(governance_status="escalated")
        assert r.decision == "escalated"
        assert "ESCALATED" in r.summary

    def test_explanation_id(self):
        expl = GuardianDecisionExplanation()
        r = expl.build(governance_status="approved", explanation_id="exp-1")
        assert r.explanation_id == "exp-1"

    def test_build_count(self):
        expl = GuardianDecisionExplanation()
        assert expl.build_count == 0
        expl.build()
        assert expl.build_count == 1

    def test_sections_present(self):
        expl = GuardianDecisionExplanation()
        r = expl.build(governance_status="approved")
        titles = [s.title for s in r.sections]
        assert "Keputusan Governance" in titles
        assert "Evidence" in titles
        assert "Risiko Teridentifikasi" in titles
        assert "Policy Compliance" in titles
        assert "Recommendation" in titles

    def test_next_actions_for_approved(self):
        expl = GuardianDecisionExplanation()
        r = expl.build(governance_status="approved")
        assert any("siap dijalankan" in a for a in r.next_actions)

    def test_next_actions_for_rejected(self):
        expl = GuardianDecisionExplanation()
        r = expl.build(governance_status="rejected", policy_passed=False)
        assert any("policy violations" in a for a in r.next_actions)

    def test_frozen_dto(self):
        s = ExplanationSection("Test", ("line1",), "info")
        assert s.title == "Test"
        with pytest.raises(AttributeError):
            s.title = "Changed"


# ══════════════════════════════════════════════════════════════════
# OP-345: GuardianCoordinationRuntime
# ══════════════════════════════════════════════════════════════════

class TestGuardianCoordinationRuntime:
    """8 test untuk coordination runtime."""

    def test_no_engines(self):
        coord = GuardianCoordinationRuntime()
        r = coord.run()
        assert r.success is True
        assert r.all_passed is False  # semua False

    @pytest.fixture
    def full_coordination(self):
        gov = GuardianGovernanceEngine()
        ready = ExecutionReadinessEvaluator()
        risk = GuardianRiskAssessment()
        expl = GuardianDecisionExplanation()
        return GuardianCoordinationRuntime(
            governance=gov, readiness=ready,
            risk_assessment=risk, explanation=expl,
        )

    def test_with_all_engines(self, full_coordination):
        r = full_coordination.run()
        assert r.governance_ok is True
        assert r.readiness_ok is True
        assert r.risk_ok is True
        assert r.explanation_ok is True

    def test_with_results(self, full_coordination):
        r = full_coordination.run(
            policy_passed=False, policy_violations=2,
        )
        assert r.success is True
        assert r.governance_result is not None
        assert r.readiness_result is not None
        assert r.risk_result is not None
        assert r.explanation_result is not None

    def test_coordination_count(self):
        coord = GuardianCoordinationRuntime()
        assert coord.coordination_count == 0
        coord.run()
        assert coord.coordination_count == 1

    def test_with_runtime_v2(self):
        from sam.operations.brain.guardian.runtime_v2 import GuardianRuntimeV2
        runtime_v2 = GuardianRuntimeV2()
        coord = GuardianCoordinationRuntime(runtime_v2=runtime_v2)
        r = coord.run()
        assert r.runtime_ok is True

    def test_frozen_dto(self):
        r = CoordinationResult("c-1", True)
        with pytest.raises(AttributeError):
            r.success = False

    def test_all_passed_property(self):
        r = CoordinationResult("c-1", True,
                               runtime_ok=True, governance_ok=True,
                               readiness_ok=True, risk_ok=True,
                               explanation_ok=True)
        assert r.all_passed is True

    def test_to_dict(self):
        r = CoordinationResult("c-1", True)
        d = r.to_dict()
        assert d["coordination_id"] == "c-1"


# ══════════════════════════════════════════════════════════════════
# OP-346: GovernanceConversationBridge
# ══════════════════════════════════════════════════════════════════

class TestGovernanceConversationBridge:
    """12 test untuk conversation bridge."""

    @pytest.fixture
    def bridge(self):
        return GovernanceConversationBridge(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
            explanation=GuardianDecisionExplanation(),
        )

    def test_unknown_query(self, bridge):
        r = bridge.query("unknown_type")
        assert r.success is False

    def test_why_blocked_not_blocked(self, bridge):
        r = bridge.query("why_blocked")
        assert r.success is True
        assert r.data["blocked"] is False

    def test_why_blocked_blocked(self, bridge):
        r = bridge.query("why_blocked",
                         guardian_healthy=False, guardian_score=0.2)
        assert r.success is True
        assert r.data["blocked"] is True

    def test_why_approved(self, bridge):
        r = bridge.query("why_approved")
        assert r.success is True
        assert "approved" in r.data

    def test_execution_readiness(self, bridge):
        r = bridge.query("execution_readiness")
        assert r.success is True
        assert "readiness_level" in r.data

    def test_risk_summary(self, bridge):
        r = bridge.query("risk_summary")
        assert r.success is True
        assert "overall_level" in r.data

    def test_policy_summary(self, bridge):
        r = bridge.query("policy_summary")
        assert r.success is True
        assert "governance_policy_status" in r.data

    def test_guardian_summary(self, bridge):
        r = bridge.query("guardian_summary")
        assert r.success is True
        assert "guardian_engine" in r.data

    def test_pending_requirements(self, bridge):
        r = bridge.query("pending_requirements",
                         approval_complete=False, approval_rate=0.5)
        assert r.success is True
        assert r.data["pending_count"] >= 1

    def test_missing_approvals(self, bridge):
        r = bridge.query("missing_approvals",
                         approval_missing=2, approval_required=5)
        assert r.success is True
        assert r.data["approval_missing"] == 2

    def test_governance_report(self, bridge):
        r = bridge.query("governance_report")
        assert r.success is True
        assert "governance" in r.data
        assert "readiness" in r.data
        assert "risk" in r.data
        assert "explanation" in r.data

    def test_query_count(self, bridge):
        assert bridge.query_count == 0
        bridge.query("why_blocked")
        assert bridge.query_count == 1


# ══════════════════════════════════════════════════════════════════
# OP-347: GuardianDashboardV3Service
# ══════════════════════════════════════════════════════════════════

class TestGuardianDashboardV3Service:
    """12 test untuk dashboard V3."""

    @pytest.fixture
    def dash(self):
        return GuardianDashboardV3Service(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
            explanation=GuardianDecisionExplanation(),
        )

    def test_governance_card(self, dash):
        c = dash.build_governance_card()
        assert isinstance(c, GovernanceCard)
        assert c.approved is True

    def test_risk_card(self, dash):
        c = dash.build_risk_card()
        assert isinstance(c, RiskCard)
        assert c.is_safe is True

    def test_readiness_card(self, dash):
        c = dash.build_readiness_card()
        assert isinstance(c, ReadinessCard)
        assert c.ready is True

    def test_policy_card(self, dash):
        c = dash.build_policy_card()
        assert isinstance(c, PolicyCard)
        assert c.policy_passed is True

    def test_guardian_summary_card(self, dash):
        c = dash.build_guardian_summary_card()
        assert isinstance(c, GuardianSummaryCard)
        assert c.guardian_healthy is True
        assert c.coordination_engines == 4

    def test_blocked_missions_card(self, dash):
        c = dash.build_blocked_missions_card()
        assert isinstance(c, BlockedMissionsCard)
        assert c.blocked_count == 0

    def test_pending_approval_card(self, dash):
        c = dash.build_pending_approval_card(approval_required=3, approval_granted=1)
        assert isinstance(c, PendingApprovalCard)
        assert c.pending_count == 2

    def test_operational_status_card_ready(self, dash):
        c = dash.build_operational_status_card()
        assert isinstance(c, OperationalStatusCard)
        assert c.system_ready is True

    def test_operational_status_card_not_ready(self, dash):
        # Buat readiness dengan blocking
        dash2 = GuardianDashboardV3Service(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
        )
        c = dash2.build_operational_status_card(
            guardian_healthy=False, guardian_score=0.2)
        assert c.system_ready is False

    def test_empty_engine(self):
        dash = GuardianDashboardV3Service()
        c = dash.build_governance_card()
        assert c.overall_status == "unknown"

    def test_governance_card_to_dict(self, dash):
        c = dash.build_governance_card()
        d = c.to_dict()
        assert "governance_id" in d
        assert "overall_status" in d

    def test_all_cards_frozen(self, dash):
        c = dash.build_governance_card()
        with pytest.raises(AttributeError):
            c.overall_status = "changed"


# ══════════════════════════════════════════════════════════════════
# OP-348: GuardianRuntimeV3Integration
# ══════════════════════════════════════════════════════════════════

class TestGuardianRuntimeV3Integration:
    """9 test untuk runtime V3 integration."""

    def test_no_engines(self):
        v3 = GuardianRuntimeV3Integration()
        r = v3.run()
        assert r.success is True
        # Tanpa engine, default semua True
        assert r.all_passed is True
        assert r.governance_ok is True

    def test_with_governance_only(self):
        v3 = GuardianRuntimeV3Integration(
            governance=GuardianGovernanceEngine(),
        )
        r = v3.run()
        assert r.governance_ok is True

    def test_with_all_engines(self):
        v3 = GuardianRuntimeV3Integration(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
        )
        r = v3.run()
        assert r.governance_ok is True
        assert r.readiness_ok is True

    def test_pipeline_count(self):
        v3 = GuardianRuntimeV3Integration()
        assert v3.pipeline_count == 0
        v3.run()
        assert v3.pipeline_count == 1

    def test_with_guardian_runtime_v2(self):
        from sam.operations.brain.guardian.runtime_v2 import GuardianRuntimeV2
        from sam.operations.brain.guardian.health import GuardianHealthEngine
        health = GuardianHealthEngine()
        v3 = GuardianRuntimeV3Integration(
            guardian=GuardianRuntimeV2(health_engine=health),
        )
        r = v3.run()
        assert r.guardian_ok is True

    def test_with_dashboard_v3(self):
        dash = GuardianDashboardV3Service(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
        )
        v3 = GuardianRuntimeV3Integration(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            dashboard_v3=dash,
        )
        r = v3.run()
        assert r.dashboard_ok is True

    def test_with_conversation_governance(self):
        conv = GovernanceConversationBridge(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
        )
        v3 = GuardianRuntimeV3Integration(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            conversation_governance=conv,
        )
        r = v3.run()
        assert r.conversation_ok is True

    def test_all_passed_property(self):
        r = V3IntegrationResult("v3-1", True,
                                 observation_ok=True, reasoning_ok=True,
                                 decision_ok=True, guardian_ok=True,
                                 governance_ok=True, readiness_ok=True,
                                 dashboard_ok=True, conversation_ok=True)
        assert r.all_passed is True

    def test_frozen_dto(self):
        r = V3IntegrationResult("v3-1", True)
        with pytest.raises(AttributeError):
            r.success = False
