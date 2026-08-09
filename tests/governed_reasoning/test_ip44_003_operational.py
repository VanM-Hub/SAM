"""Test IP-4.4-003 - Operational AI (MISSION-4.4).

Coverage: WP-21..WP-30 - investigation/diagnosis/recommendation/learning/
conversation reasoning, operational explainability, governed AI API,
compliance, end-to-end, baseline.
"""
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.governed_reasoning.structured_reasoning import (
    EvidenceRef,
    ReasoningStep,
    StructuredReasoningEngine,
)
from sam.governed_reasoning.operational_ai import (
    ConversationReasoning,
    DiagnosisReasoning,
    InvestigationReasoning,
    LearningAssistedReasoning,
    RecommendationReasoning,
)
from sam.governed_reasoning.governed_ai_api import GovernedAIAPI
from sam.governed_reasoning.operational_ai_compliance import (
    OperationalAIComplianceChecker,
)


def _ev(evidence_id):
    return EvidenceRef(evidence_id=evidence_id, source_type="runtime", source_id=evidence_id)


def _engine():
    def reason(context, evidences):
        steps = []
        for i, ev in enumerate(evidences or ((EvidenceRef("e", "runtime", "e"),),), start=1):
            steps.append(
                ReasoningStep(
                    step_id=f"s{i}",
                    kind="premise" if i < len(evidences) else "conclusion",
                    content=f"obs {ev.evidence_id}",
                    evidence_refs=(ev.evidence_id,),
                )
            )
        conclusion = f"{context.scope} conclusion for {context.question}"
        return steps, conclusion

    return StructuredReasoningEngine(reason)


def _api():
    eng = _engine()
    return GovernedAIAPI(
        investigation=InvestigationReasoning(eng),
        diagnosis=DiagnosisReasoning(eng),
        recommendation=RecommendationReasoning(eng),
        learning=LearningAssistedReasoning(eng),
        conversation=ConversationReasoning(eng),
    )


# ---------------------------------------------------------------------------
# WP-21..24 Domain Reasoning
# ---------------------------------------------------------------------------

class TestDomainReasoning:
    def test_investigation_reasoning(self):
        api = _api()
        resp = api.investigate("why cpu high?", (_ev("e1"),), investigation_id="inv-1")
        assert resp.domain == "investigation"
        assert resp.reasoning.conclusion

    def test_diagnosis_reasoning(self):
        api = _api()
        resp = api.diagnose("what is wrong?", (_ev("e1"),), investigation_id="inv-1")
        assert resp.domain == "diagnosis"
        assert resp.reasoning.evidence_refs

    def test_recommendation_reasoning(self):
        api = _api()
        resp = api.recommend("what to do?", (_ev("e1"),), investigation_id="inv-1")
        assert resp.domain == "recommendation"

    def test_learning_reasoning(self):
        api = _api()
        resp = api.learn("what worked before?", (_ev("e1"),), investigation_id="inv-1")
        assert resp.domain == "learning"


# ---------------------------------------------------------------------------
# WP-25 Conversation Reasoning
# ---------------------------------------------------------------------------

class TestConversationReasoning:
    def test_conversation_response(self):
        api = _api()
        resp = api.converse("explain the failure", (_ev("e1"),))
        assert resp.domain == "conversation"
        assert resp.reasoning.contextual_input == "explain the failure"


# ---------------------------------------------------------------------------
# WP-26 Operational Explainability
# ---------------------------------------------------------------------------

class TestOperationalExplainability:
    def test_explanation_has_chain(self):
        api = _api()
        resp = api.diagnose("what?", (_ev("e1"),))
        assert resp.reasoning.evidence_refs == ("e1",)
        assert resp.explanation["domain"] == "diagnosis"
        assert len(resp.explanation["step_chain"]) >= 1

    def test_explanation_evidence_chain(self):
        api = _api()
        resp = api.investigate("q", (_ev("e1"),))
        assert resp.explanation["evidence_chain"] == ["e1"]


# ---------------------------------------------------------------------------
# WP-27 Governed AI API
# ---------------------------------------------------------------------------

class TestGovernedAIAPI:
    def test_all_domains_available(self):
        api = _api()
        domains = [
            api.investigate("q", (_ev("e1"),)).domain,
            api.diagnose("q", (_ev("e1"),)).domain,
            api.recommend("q", (_ev("e1"),)).domain,
            api.learn("q", (_ev("e1"),)).domain,
            api.converse("q", (_ev("e1"),)).domain,
        ]
        assert domains == [
            "investigation",
            "diagnosis",
            "recommendation",
            "learning",
            "conversation",
        ]

    def test_response_structured(self):
        api = _api()
        resp = api.diagnose("q", (_ev("e1"),))
        d = resp.as_dict()
        assert d["reasoning"]["reasoning_id"]
        assert d["explanation"]["conclusion"]


# ---------------------------------------------------------------------------
# WP-28 Operational Compliance
# ---------------------------------------------------------------------------

class TestOperationalAICompliance:
    def test_certify_clean(self):
        checker = OperationalAIComplianceChecker()
        assert checker.certify()["certified"] is True

    def test_assistance_only(self):
        checker = OperationalAIComplianceChecker()
        assert not checker.certify(assistance_only=False)["certified"]

    def test_no_autonomous_decision(self):
        checker = OperationalAIComplianceChecker()
        assert not checker.certify(no_autonomous_decision=False)["certified"]

    def test_no_bypass(self):
        assert not OperationalAIComplianceChecker().certify(no_bypass=False)["certified"]


# ---------------------------------------------------------------------------
# WP-29/30 End-to-End + Baseline
# ---------------------------------------------------------------------------

class TestOperationalAIEndToEnd:
    def test_end_to_end_governed_ai(self):
        api = _api()
        common_evidence = (_ev("e1"), _ev("e2"))

        inv = api.investigate("why failure?", common_evidence, investigation_id="inv-10")
        diag = api.diagnose("what root cause?", common_evidence, investigation_id="inv-10")
        rec = api.recommend("which action?", common_evidence, investigation_id="inv-10")
        chat = api.converse("explain", common_evidence)

        assert inv.reasoning.evidence_refs
        assert diag.explanation["evidence_chain"]
        assert rec.reasoning.conclusion
        assert chat.reasoning.conclusion

        # Semua reasoning evidence-backed
        checker = OperationalAIComplianceChecker()
        assert checker.certify()["certified"] is True
        assert checker.check(evidence_based=True).passed
