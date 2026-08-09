"""Test IP-4.4-002 - Structured Reasoning (MISSION-4.4).

Coverage: WP-11..WP-20 - reasoning engine, evidence-backed, context,
confidence, verification, explainability, API, compliance, baseline.
"""
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.governed_reasoning.structured_reasoning import (
    EvidenceRef,
    ReasoningStep,
    StructuredReasoning,
    StructuredReasoningEngine,
)
from sam.governed_reasoning.confidence_assessment import ConfidenceAssessor
from sam.governed_reasoning.reasoning_verification import ReasoningVerifier
from sam.governed_reasoning.reasoning_explainability import ReasoningExplainer
from sam.governed_reasoning.reasoning_api import ReasoningAPI
from sam.governed_reasoning.reasoning_compliance import (
    ReasoningComplianceChecker,
)


def _ev(evidence_id, source_type="runtime"):
    return EvidenceRef(evidence_id=evidence_id, source_type=source_type, source_id=evidence_id)


def _engine():
    def reason(context, evidences):
        steps = []
        for i, ev in enumerate(evidences, start=1):
            steps.append(
                ReasoningStep(
                    step_id=f"s{i}",
                    kind="premise" if i < len(evidences) else "conclusion",
                    content=f"observed {ev.evidence_id}",
                    evidence_refs=(ev.evidence_id,),
                )
            )
        conclusion = "conclusion from " + str(len(evidences)) + " evidence"
        return steps, conclusion

    return StructuredReasoningEngine(reason)


# ---------------------------------------------------------------------------
# WP-11 Structured Reasoning Engine
# ---------------------------------------------------------------------------

class TestStructuredReasoning:
    def test_reason_has_steps_and_conclusion(self):
        engine = _engine()
        reasoning = engine.reason("why high cpu?", (_ev("e1"), _ev("e2")))
        assert reasoning.steps
        assert reasoning.conclusion
        assert reasoning.reasoning_id

    def test_evidence_backed(self):
        engine = _engine()
        reasoning = engine.reason("why?", (_ev("e1"), _ev("e2")))
        assert reasoning.is_evidence_backed is True
        assert reasoning.total_evidence == 2


# ---------------------------------------------------------------------------
# WP-13 Context Resolution
# ---------------------------------------------------------------------------

class TestContextResolution:
    def test_resolve_context(self):
        engine = _engine()
        reasoning = engine.reason(
            "why?", (_ev("e1"),), investigation_id="inv-1", provider_id="p"
        )
        assert reasoning.context.investigation_id == "inv-1"
        assert reasoning.context.provider_id == "p"

    def test_context_scope(self):
        engine = _engine()
        reasoning = engine.reason("why?", (_ev("e1"),), scope="deep")
        assert reasoning.context.scope == "deep"


# ---------------------------------------------------------------------------
# WP-12 Evidence-backed + WP-14 Confidence
# ---------------------------------------------------------------------------

class TestConfidence:
    def test_confidence_high_with_all_evidence(self):
        engine = _engine()
        reasoning = engine.reason("why?", (_ev("e1"), _ev("e2")))
        conf = ConfidenceAssessor.assess(reasoning)
        assert conf.value > 0.8
        assert conf.level == "high"

    def test_confidence_zero_no_steps(self):
        reasoning = StructuredReasoning(
            reasoning_id="r1",
            context=_engine().reason("q", ()).context,
            steps=(),
            conclusion="",
        )
        conf = ConfidenceAssessor.assess(reasoning)
        assert conf.value == 0.0
        assert conf.level == "none"


# ---------------------------------------------------------------------------
# WP-15 Reasoning Verification
# ---------------------------------------------------------------------------

class TestReasoningVerification:
    def test_verify_evidence_backed(self):
        engine = _engine()
        reasoning = engine.reason("why?", (_ev("e1"),))
        verification = ReasoningVerifier.verify(reasoning)
        assert verification.passed is True

    def test_verify_no_authority(self):
        engine = _engine()
        reasoning = engine.reason("why?", (_ev("e1"),))
        verification = ReasoningVerifier.verify(reasoning, no_authority=False)
        assert not verification.passed


# ---------------------------------------------------------------------------
# WP-16 Reasoning Explainability
# ---------------------------------------------------------------------------

class TestReasoningExplainability:
    def test_explain_has_chain(self):
        engine = _engine()
        reasoning = engine.reason("why?", (_ev("e1"), _ev("e2")))
        explainer = ReasoningExplainer()
        trace = explainer.explain(reasoning)
        assert trace.evidence_chain == ("e1", "e2")
        assert len(trace.step_chain) == 2


# ---------------------------------------------------------------------------
# WP-17 Reasoning API
# ---------------------------------------------------------------------------

class TestReasoningAPI:
    def test_reason_result_complete(self):
        api = ReasoningAPI(_engine())
        result = api.reason("why?", (_ev("e1"), _ev("e2")))
        assert result.confidence["level"] == "high"
        assert result.verification["passed"] is True
        assert result.explanation["evidence_chain"] == ["e1", "e2"]


# ---------------------------------------------------------------------------
# WP-18 Reasoning Compliance
# ---------------------------------------------------------------------------

class TestReasoningCompliance:
    def test_certify_clean(self):
        checker = ReasoningComplianceChecker()
        assert checker.certify()["certified"] is True

    def test_detects_authority(self):
        checker = ReasoningComplianceChecker()
        assert not checker.certify(no_authority=False)["certified"]

    def test_detects_execution(self):
        checker = ReasoningComplianceChecker()
        assert not checker.certify(no_execution=False)["certified"]


# ---------------------------------------------------------------------------
# WP-19/20 Integration & Baseline
# ---------------------------------------------------------------------------

class TestStructuredReasoningEndToEnd:
    def test_end_to_end_reasoning(self):
        api = ReasoningAPI(_engine())
        evidence = (_ev("e1"), _ev("e2"), _ev("e3"))
        result = api.reason(
            "diagnose failure", evidence, investigation_id="inv-9"
        )
        assert result.reasoning.reasoning_id
        assert result.confidence["level"] in ("high", "medium")
        assert result.verification["passed"] is True
        assert len(result.explanation["step_chain"]) == 3

        # Compliance terkait reasoning tak hasilkan authority
        checker = ReasoningComplianceChecker()
        assert checker.certify()["certified"] is True
