"""Test IP-4.5-001 - Autonomous Investigation (MISSION-4.5).

Coverage: WP-01..WP-10 - trigger, autonomous engine, context collection,
runtime/provider verification, planning, API, explainability, compliance, e2e.
"""
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.autonomous_operations.investigation_trigger import (
    TriggerEvaluationEngine,
    TriggerPolicy,
)
from sam.autonomous_operations.autonomous_investigation import (
    AutonomousInvestigationEngine,
    InvestigationState,
)
from sam.autonomous_operations.context_collection import ContextCollector
from sam.autonomous_operations.verification import (
    ProviderVerificationEngine,
    RuntimeVerificationEngine,
)
from sam.autonomous_operations.investigation_planning import InvestigationPlanner
from sam.autonomous_operations.autonomous_investigation_api import (
    AutonomousInvestigationAPI,
)
from sam.autonomous_operations.autonomous_explainability import (
    AutonomousInvestigationExplainer,
)
from sam.autonomous_operations.autonomous_compliance import (
    AutonomousComplianceChecker,
)


# ---------------------------------------------------------------------------
# WP-01 Investigation Trigger
# ---------------------------------------------------------------------------

class TestInvestigationTrigger:
    def test_trigger_evaluated_deterministically(self):
        engine = TriggerEvaluationEngine()
        policy = TriggerPolicy(policy_id="p1", condition="health == critical", severity="critical")
        event = engine.evaluate(policy, target_id="runtime-1", observed_value="critical")
        assert event is not None
        assert event.severity == "critical"

    def test_trigger_no_match(self):
        engine = TriggerEvaluationEngine()
        policy = TriggerPolicy(policy_id="p1", condition="health == critical")
        event = engine.evaluate(policy, target_id="r", observed_value="healthy")
        assert event is None

    def test_trigger_generates_request(self):
        engine = TriggerEvaluationEngine()
        policy = TriggerPolicy(policy_id="p1", condition="health == critical")
        event = engine.evaluate(policy, target_id="r", observed_value="critical")
        request = engine.create_request(event, "critical health")
        assert request.reason == "critical health"
        assert request.source_event_id == event.event_id

    def test_trigger_audit(self):
        engine = TriggerEvaluationEngine()
        policy = TriggerPolicy(policy_id="p1", condition="health == critical")
        engine.evaluate(policy, target_id="r", observed_value="critical")
        assert len(engine.audit()) == 1


# ---------------------------------------------------------------------------
# WP-03 Operational Context Collection
# ---------------------------------------------------------------------------

class TestContextCollection:
    def test_collect_context(self):
        collector = ContextCollector()
        collector.register_probe("runtime", "r1", lambda: {"health": "healthy"})
        collector.register_probe("provider", "p1", lambda: {"available": True})
        snapshot = collector.collect()
        assert snapshot.runtimes() == (("r1", {"health": "healthy"}),)
        assert snapshot.providers() == (("p1", {"available": True}),)
        assert snapshot.missions() == ()

    def test_context_immutable(self):
        collector = ContextCollector()
        collector.register_probe("runtime", "r1", lambda: {"cpu": 50})
        s1 = collector.collect()
        s2 = collector.collect()
        assert len(collector.all_snapshots()) == 2


# ---------------------------------------------------------------------------
# WP-04/05 Runtime & Provider Verification
# ---------------------------------------------------------------------------

class TestVerification:
    def test_runtime_verification(self):
        engine = RuntimeVerificationEngine()
        engine.register_probe("r1", lambda: {"health": "healthy"})
        ev = engine.verify("r1")
        assert ev.validated is True
        assert ev.health == "healthy"

    def test_runtime_no_mutation(self):
        engine = RuntimeVerificationEngine()
        engine.register_probe("r1", lambda: {"health": "critical", "detail": "x"})
        ev = engine.verify("r1")
        assert ev.validated is False

    def test_provider_verification(self):
        engine = ProviderVerificationEngine()
        engine.register_probe("p1", lambda: {"health": "healthy", "available": True})
        ev = engine.verify("p1")
        assert ev.available is True
        assert ev.validated is True

    def test_runtime_metrics(self):
        engine = RuntimeVerificationEngine()
        engine.register_probe("r1", lambda: {"health": "healthy"})
        engine.verify("r1")
        assert engine.metrics()["validated"] == 1


# ---------------------------------------------------------------------------
# WP-06 Investigation Planning
# ---------------------------------------------------------------------------

class TestInvestigationPlanning:
    def test_plan_generated(self):
        planner = InvestigationPlanner()
        plan = planner.plan("inv-1", severity="warning", evidence_count=2)
        assert plan.plan_id
        assert plan.priority == "medium"
        assert len(plan.steps) == 5

    def test_priority_high_on_critical(self):
        planner = InvestigationPlanner()
        plan = planner.plan("inv-1", severity="critical", critical_findings=1)
        assert plan.priority == "high"

    def test_plan_explainable(self):
        planner = InvestigationPlanner()
        plan = planner.plan("inv-1", severity="critical")
        expl = planner.explain(plan)
        assert expl.priority_reason
        assert len(expl.step_rationale) == 5


# ---------------------------------------------------------------------------
# WP-02 Autonomous Investigation Engine
# ---------------------------------------------------------------------------

class TestAutonomousInvestigation:
    def test_start_without_manual(self):
        engine = AutonomousInvestigationEngine()
        from sam.autonomous_operations.investigation_trigger import InvestigationRequest
        request = InvestigationRequest(request_id="req-1", reason="auto", target_ids=("r1",))
        inv = engine.start(request)
        assert inv.state == InvestigationState.PENDING
        assert engine.count() == 1

    def test_workflow_transitions(self):
        engine = AutonomousInvestigationEngine()
        from sam.autonomous_operations.investigation_trigger import InvestigationRequest
        inv = engine.start(InvestigationRequest(request_id="r", reason="x", target_ids=("r1",)))
        inv = inv.transition(InvestigationState.PLANNED)
        inv = inv.transition(InvestigationState.COLLECTING)
        done = inv.complete({"conclusion": "ok"})
        assert done.state == InvestigationState.COMPLETED
        assert done.result["conclusion"] == "ok"


# ---------------------------------------------------------------------------
# WP-07 Autonomous Investigation API
# ---------------------------------------------------------------------------

class TestAutonomousInvestigationAPI:
    def _build(self):
        engine = AutonomousInvestigationEngine()
        trigger = TriggerEvaluationEngine()
        context = ContextCollector()
        runtime = RuntimeVerificationEngine()
        provider = ProviderVerificationEngine()
        planner = InvestigationPlanner()

        from sam.autonomous_operations.investigation_trigger import (
            TriggerPolicy,
        )
        policy = TriggerPolicy(policy_id="p", condition="health == critical")
        event = trigger.evaluate(policy, target_id="r1", observed_value="critical")
        request = trigger.create_request(event, "auto investigation")
        engine.start(request)

        api = AutonomousInvestigationAPI(
            engine=engine, trigger=trigger, context=context,
            runtime_verify=runtime, provider_verify=provider, planner=planner,
        )
        return api

    def test_list_investigations(self):
        api = self._build()
        assert len(api.list_investigations()) == 1

    def test_trigger_audit_via_api(self):
        api = self._build()
        assert len(api.trigger.audit()) == 1

    def test_metrics(self):
        api = self._build()
        assert api.metrics()["total"] == 1


# ---------------------------------------------------------------------------
# WP-08 Investigation Explainability
# ---------------------------------------------------------------------------

class TestAutonomousExplainability:
    def test_explain_has_chain(self):
        engine = AutonomousInvestigationEngine()
        from sam.autonomous_operations.investigation_trigger import InvestigationRequest
        inv = engine.start(InvestigationRequest(request_id="r", reason="why", target_ids=("r1",)))
        planner = InvestigationPlanner()
        plan = planner.plan(inv.investigation_id, severity="critical")
        explainer = AutonomousInvestigationExplainer()
        expl = explainer.explain(inv, plan)
        assert expl.evidence_chain
        assert expl.planning.priority == "high"
        assert "trigger" in expl.evidence_chain


# ---------------------------------------------------------------------------
# WP-09 Autonomous Compliance
# ---------------------------------------------------------------------------

class TestAutonomousCompliance:
    def test_certify_clean(self):
        checker = AutonomousComplianceChecker()
        assert checker.certify()["certified"] is True

    def test_detects_execution(self):
        assert not AutonomousComplianceChecker().certify(execution=True)["certified"]

    def test_detects_approval_bypass(self):
        assert not AutonomousComplianceChecker().certify(approval_bypass=True)["certified"]

    def test_detects_forbidden_pattern(self):
        assert not AutonomousComplianceChecker().certify(source="provider.execute(")["certified"]


# ---------------------------------------------------------------------------
# WP-10 Integration & Certification (end-to-end)
# ---------------------------------------------------------------------------

class TestAutonomousInvestigationEndToEnd:
    def test_end_to_end_autonomous(self):
        engine = AutonomousInvestigationEngine()
        trigger = TriggerEvaluationEngine()
        context = ContextCollector()
        runtime = RuntimeVerificationEngine()
        provider = ProviderVerificationEngine()
        planner = InvestigationPlanner()

        # 1. Trigger otomatis
        policy = TriggerPolicy(policy_id="p1", condition="health == critical", severity="critical")
        event = trigger.evaluate(policy, target_id="runtime-core", observed_value="critical")
        assert event is not None
        request = trigger.create_request(event, "runtime critical")

        # 2. Investigasi dimulai tanpa intervensi
        inv = engine.start(request)
        assert inv.state == InvestigationState.PENDING

        # 3. Context dikumpulkan
        context.register_probe("runtime", "runtime-core", lambda: {"health": "critical"})
        context.register_probe("provider", "provider-a", lambda: {"available": True})
        snapshot = context.collect()
        assert snapshot.runtimes()

        # 4. Verifikasi runtime & provider
        runtime.register_probe("runtime-core", lambda: {"health": "critical"})
        provider.register_probe("provider-a", lambda: {"health": "healthy", "available": True})
        runtime.verify("runtime-core")
        provider.verify("provider-a")

        # 5. Planning
        plan = planner.plan(inv.investigation_id, severity="critical", critical_findings=1)
        assert plan.priority == "high"

        # 6. API + explainability + compliance
        api = AutonomousInvestigationAPI(
            engine=engine, trigger=trigger, context=context,
            runtime_verify=runtime, provider_verify=provider, planner=planner,
        )
        assert len(api.list_investigations()) == 1
        assert len(api.trigger.audit()) == 1
        assert len(api.verification.runtime_report()) == 1

        explainer = AutonomousInvestigationExplainer()
        expl = explainer.explain(inv, plan)
        assert expl.evidence_chain

        checker = AutonomousComplianceChecker()
        assert checker.certify()["certified"] is True
        assert checker.certify(source="context.collect()")["certified"] is True
