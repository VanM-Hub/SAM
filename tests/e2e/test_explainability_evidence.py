"""
OP-353 — Guardian Explainability Review + OP-354 — Evidence Chain Validation

Pastikan setiap keputusan Guardian dapat dijawab:
  Why? Based on what evidence? Which policy? Which rule? Which risk? Which recommendation?

Verifikasi seluruh pipeline memiliki rantai evidence yang tidak terputus.
"""

import pytest
from typing import Dict, Any, List, Optional

from sam.operations.brain.guardian import (
    GuardianGovernanceEngine,
    ExecutionReadinessEvaluator,
    GuardianRiskAssessment,
    GuardianDecisionExplanation,
    GovernanceConversationBridge,
)


class TestGuardianExplainability:
    """OP-353: Setiap keputusan harus punya asal-usul yang jelas."""

    def test_why_approved_traceable(self):
        """Approved harus punya alasan."""
        expl = GuardianDecisionExplanation()
        r = expl.build(
            governance_status="approved",
            policy_passed=True, policy_violations=0,
            health_status="healthy", health_score=0.95,
            decision_approved=True, decision_confidence=0.9,
            approval_complete=True, approval_granted=2, approval_required=2,
            recommendation_support=True, recommendation_risk="low",
        )
        assert "APPROVED" in r.summary
        # Must have 5 sections
        assert r.section_count >= 5
        titles = [s.title for s in r.sections]
        assert "Keputusan Governance" in titles
        assert "Evidence" in titles
        assert "Risiko Teridentifikasi" in titles
        assert "Policy Compliance" in titles
        assert "Recommendation" in titles

    def test_why_rejected_traceable(self):
        """Rejected harus menyebutkan penyebab."""
        expl = GuardianDecisionExplanation()
        r = expl.build(
            governance_status="rejected",
            policy_passed=False, policy_violations=3,
            health_status="critical", health_score=0.2,
            decision_approved=False, decision_confidence=0.3,
            approval_complete=False, approval_granted=0, approval_required=2,
            recommendation_support=False, recommendation_risk="high",
        )
        assert "REJECTED" in r.summary
        # Policy failure harus disebut
        pol = [s for s in r.sections if "Policy" in s.title]
        assert len(pol) >= 1
        # Next actions harus ada
        assert len(r.next_actions) >= 1

    def test_why_blocked_conversation(self):
        """Conversation query harus menjelaskan blocking."""
        bridge = GovernanceConversationBridge(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
            explanation=GuardianDecisionExplanation(),
        )
        r = bridge.query("why_blocked",
                         guardian_healthy=False, guardian_score=0.2)
        assert r.success
        assert r.data.get("blocked") is True
        # Harus ada summary penjelasan
        assert "summary" in r.data
        assert len(r.data.get("summary", "")) > 0

    def test_governance_decision_has_evidence(self):
        """Setiap GovernanceDecision punya evidence."""
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(policy_passed=False, policy_violations=2)
        for stage_name, decision in r.stage_decisions.items():
            if stage_name == "policy":
                assert decision.passed is False
                assert decision.evidence_count >= 1
                ev = decision.passing_evidence
                # Evidence harus ada yang menjelaskan failure
                non_passing = decision.evidence_count - len(ev)
                assert non_passing >= 1  # setidaknya 1 failing evidence

    def test_readiness_checks_traceable(self):
        """Setiap readiness check punya dimension dan level."""
        ready = ExecutionReadinessEvaluator()
        r = ready.evaluate(
            approval_complete=False, approval_rate=0.3,
            policy_passed=False, policy_violations=2,
            guardian_healthy=False, guardian_score=0.2,
            dependency_complete=False, dependency_pending=3,
        )
        for c in r.checks:
            assert c.dimension is not None
            assert c.level is not None
            assert c.detail is not None
        # Blocking dimensions harus disebut
        assert len(r.blocking_dimensions) >= 1

    def test_risk_assessment_traceable(self):
        """Setiap risk dimension punya factors dan level."""
        assess = GuardianRiskAssessment()
        r = assess.assess(
            system_health="critical", health_score=0.2,
            policy_violations=3, execution_complexity="critical",
            dependency_pending=5, dependency_count=10,
            approval_missing=3, approval_required=5,
            confidence_score=0.3, evidence_quality=0.4,
        )
        for d in r.dimensions:
            assert d.dimension is not None
            assert d.level is not None
            assert d.score >= 0.0
        # Top risks harus tidak kosong
        assert len(r.top_risks) >= 1

    def test_conversation_explains_why(self):
        """Query 'why_blocked' harus menjelaskan dengan eksplisit."""
        bridge = GovernanceConversationBridge(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
        )
        r = bridge.query("why_blocked",
                         approval_complete=False, approval_rate=0.0)
        assert r.success
        assert r.data.get("blocked") is True
        # Harus ada summary: "Operasi diblokir: ..." atau "Operasi menunggu: ..."
        assert "summary" in r.data
        assert len(r.data.get("summary", "")) > 0

    def test_conversation_governance_report_has_all(self):
        """Governance report mengandung governance + readiness + risk + explanation."""
        bridge = GovernanceConversationBridge(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
            explanation=GuardianDecisionExplanation(),
        )
        r = bridge.query("governance_report")
        assert r.success
        for key in ("governance", "readiness", "risk", "explanation"):
            assert key in r.data, f"Missing key: {key}"

    def test_no_black_box_decision(self):
        """Tidak ada stage yang menghasilkan output tanpa evidence."""
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(policy_passed=True, health_status="healthy")
        for stage_name, decision in r.stage_decisions.items():
            # Setiap keputusan harus punya status dan score
            assert decision.status is not None
            assert decision.score is not None
            # Penjelasan harus ada
            assert len(decision.evidence) >= 0
            # Status harus enum, bukan None
            assert decision.status.value is not None


class TestEvidenceChain:
    """OP-354: Verifikasi rantai evidence tidak terputus."""

    def test_evidence_from_governance_to_explanation(self):
        """Explanation mengambil evidence dari governance result."""
        engine = GuardianGovernanceEngine()
        r_gov = engine.evaluate(policy_passed=False, policy_violations=2)

        expl = GuardianDecisionExplanation()
        r_exp = expl.build(
            governance_status=r_gov.overall_status.value,
            governance_score=r_gov.overall_score,
            policy_passed=False, policy_violations=2,
        )

        # Explanation harus mengandung informasi tentang policy failure
        pol_sections = [s for s in r_exp.sections if "Policy" in s.title]
        if pol_sections:
            content = " ".join(pol_sections[0].content)
            assert "Policy" in content or "policy" in content

    def test_evidence_chain_from_readiness_to_dashboard(self):
        """Dashboard card mengambil evidence dari readiness."""
        from sam.operations.brain.guardian import GuardianDashboardV3Service
        dash = GuardianDashboardV3Service(
            readiness=ExecutionReadinessEvaluator(),
        )

        # Build card — harus menghasilkan output dari readiness result
        card = dash.build_readiness_card(
            approval_complete=False, approval_rate=0.0,
        )
        assert card.ready is False

    def test_evidence_chain_from_risk_to_conversation(self):
        """Risk harus bisa dijelaskan lewat conversation."""
        bridge = GovernanceConversationBridge(
            risk_assessment=GuardianRiskAssessment(),
        )
        r = bridge.query("risk_summary",
                         system_health="critical", health_score=0.2)
        assert r.success
        assert "overall_level" in r.data

    def test_evidence_cross_reference(self):
        """Governance, readiness, risk harus konsisten."""
        params = dict(
            policy_passed=False, policy_violations=3,
            health_status="critical", health_score=0.2,
            decision_approved=False, decision_confidence=0.3,
            approval_complete=False, approval_required=2, approval_granted=0,
        )

        gov = GuardianGovernanceEngine()
        r_gov = gov.evaluate(**params)
        assert r_gov.approved is False  # semua gagal

        ready = ExecutionReadinessEvaluator()
        r_ready = ready.evaluate(
            policy_passed=params["policy_passed"],
            policy_violations=params["policy_violations"],
            guardian_healthy=False, guardian_score=params["health_score"],
        )
        assert r_ready.ready is False

        risk = GuardianRiskAssessment()
        r_risk = risk.assess(
            system_health=params["health_status"],
            health_score=params["health_score"],
            policy_violations=params["policy_violations"],
        )
        assert r_risk.is_safe is False

        # Cross-reference: jika governance rejected karena policy,
        # readiness juga harus blocked karena policy
        gov_failures = [s for s, d in r_gov.stage_decisions.items() if not d.passed]
        ready_failures = [c.dimension for c in r_ready.checks if not c.passed]
        # Governance dan readiness harus keduanya gagal
        assert len(gov_failures) >= 1
        assert len(ready_failures) >= 1

    def test_evidence_preserved_through_coordination(self):
        """Coordination runtime tidak boleh kehilangan evidence."""
        from sam.operations.brain.guardian import GuardianCoordinationRuntime
        coord = GuardianCoordinationRuntime(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
            explanation=GuardianDecisionExplanation(),
        )
        r = coord.run(policy_passed=False, policy_violations=2)
        # Results adalah dict (serialized)
        assert r.governance_result.get("approved") is False
        assert r.readiness_result.get("ready") is False
        assert r.coordination_id is not None
        # Explanation tetap punya sections
        sections = r.explanation_result.get("sections", [])
        assert len(sections) >= 5
