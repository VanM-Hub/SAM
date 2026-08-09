"""Test IP-5.1-004 - Reasoning & Context Management (MISSION-5.1).

Coverage: WP-31..WP-40 - context model, evidence, operational, experience,
resolution, request, response, explainability, compliance, integration.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.universal_ai import (
    ContextResolutionEngine,
    EvidenceContextEntry,
    EvidenceContextProvider,
    ExperienceContextProvider,
    ExperienceEntry,
    OperationalContext,
    OperationalContextProvider,
    ReasoningComplianceChecker,
    ReasoningContext,
    ReasoningExplanation,
    ReasoningExplainer,
    ReasoningRequest,
    ReasoningResponse,
)


# ---------------------------------------------------------------------------
# WP-31 Reasoning Context Model
# ---------------------------------------------------------------------------

class TestReasoningContext:
    def test_provenance(self):
        ctx = ReasoningContext(request_id="r1", objective="why slow?", provenance=("src1",))
        assert ctx.has_provenance is True
        assert ctx.as_dict()["objective"] == "why slow?"


# ---------------------------------------------------------------------------
# WP-32 Evidence Context
# ---------------------------------------------------------------------------

class TestEvidenceContext:
    def test_retrieve_with_source(self):
        provider = EvidenceContextProvider()
        provider.add(EvidenceContextEntry(evidence_id="e1", source_type="log", source_id="l1", content="c"))
        found = provider.retrieve(("e1",))
        assert len(found) == 1
        assert found[0].has_source is True

    def test_filter_provenance_drops_missing_source(self):
        provider = EvidenceContextProvider()
        provider.add(EvidenceContextEntry(evidence_id="e1", source_type="", source_id=""))
        assert provider.filter_provenance(("e1",)) == ()


# ---------------------------------------------------------------------------
# WP-33 Operational Context
# ---------------------------------------------------------------------------

class TestOperationalContext:
    def test_snapshot(self):
        provider = OperationalContextProvider()
        ctx = provider.snapshot(readiness="ready", provider_state=(("openai", "ok"),))
        assert isinstance(ctx, OperationalContext)
        assert ctx.as_dict()["readiness"] == "ready"


# ---------------------------------------------------------------------------
# WP-34 Experience Context
# ---------------------------------------------------------------------------

class TestExperienceContext:
    def test_store_retrieve(self):
        provider = ExperienceContextProvider()
        provider.store(ExperienceEntry(experience_id="x1", kind="investigation", summary="s", outcome="o", relevance=0.9))
        assert len(provider.retrieve(("x1",))) == 1
        similar = provider.discover_similar("investigation")
        assert len(similar) == 1


# ---------------------------------------------------------------------------
# WP-35 Context Resolution
# ---------------------------------------------------------------------------

class TestContextResolution:
    def _engine(self):
        ev = EvidenceContextProvider()
        ev.add(EvidenceContextEntry(evidence_id="e1", source_type="log", source_id="l1"))
        ex = ExperienceContextProvider()
        return ContextResolutionEngine(ev, ex)

    def test_detects_missing_objective(self):
        engine = self._engine()
        ctx = ReasoningContext(request_id="r1")
        resolved = engine.resolve(ctx, OperationalContext())
        assert resolved.complete is False
        assert any(m.field_name == "objective" for m in resolved.missing)

    def test_complete_with_objective(self):
        engine = self._engine()
        ctx = ReasoningContext(request_id="r1", objective="diagnose")
        resolved = engine.resolve(ctx, OperationalContext())
        assert resolved.complete is True


# ---------------------------------------------------------------------------
# WP-36/37 Request & Response
# ---------------------------------------------------------------------------

class TestRequestResponse:
    def test_request_immutable(self):
        req = ReasoningRequest(request_id="r1")
        assert req.is_immutable is True

    def test_response_provenance(self):
        resp = ReasoningResponse(request_id="r1", conclusion="c", evidence_refs=("e1",), provider_id="openai")
        assert resp.has_provenance is True


# ---------------------------------------------------------------------------
# WP-38 Reasoning Explainability
# ---------------------------------------------------------------------------

class TestExplainability:
    def test_builds_explanation(self):
        req = ReasoningRequest(request_id="r1", objective="why?")
        resp = ReasoningResponse(request_id="r1", conclusion="c", confidence=0.8, evidence_refs=("e1",), provider_id="openai", model_id="gpt")
        explanation = ReasoningExplainer().explain(req, resp)
        assert isinstance(explanation, ReasoningExplanation)
        assert explanation.provider_model == "openai:gpt"
        assert explanation.evidence_lineage == ("e1",)


# ---------------------------------------------------------------------------
# WP-39 Reasoning Compliance
# ---------------------------------------------------------------------------

class TestReasoningCompliance:
    def test_certify_passes(self):
        assert ReasoningComplianceChecker().certify()["certified"] is True

    def test_fails_on_authority(self):
        assert ReasoningComplianceChecker().certify(no_authority=False)["certified"] is False


# ---------------------------------------------------------------------------
# WP-40 Integration
# ---------------------------------------------------------------------------

class TestReasoningIntegration:
    def test_end_to_end(self):
        ev = EvidenceContextProvider()
        ev.add(EvidenceContextEntry(evidence_id="e1", source_type="log", source_id="l1"))
        engine = ContextResolutionEngine(ev, ExperienceContextProvider())
        ctx = ReasoningContext(request_id="r1", objective="diagnose", evidence_refs=("e1",))
        resolved = engine.resolve(ctx, OperationalContext())
        assert resolved.evidence_used == ("e1",)
        assert resolved.complete is True
        cert = ReasoningComplianceChecker().certify()
        assert cert["certified"] is True
