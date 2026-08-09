"""Test IP-4.2-001 - Investigation Foundation (MISSION-4.2).

Coverage: WP-01..WP-10 - model, session, evidence, observation, timeline,
API, explainability, compliance, integration end-to-end.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.operational_intelligence.investigation_model import (
    Investigation,
    InvestigationMetadata,
    InvestigationResult,
    InvestigationScope,
    InvestigationState,
    InvestigationTarget,
)
from sam.operational_intelligence.investigation_session import (
    InvestigationSession,
    InvestigationSessionManager,
    SessionContext,
    SessionState,
)
from sam.operational_intelligence.evidence_collection import (
    EvidenceCollector,
    EvidenceModel,
    EvidenceRepository,
    EvidenceSource,
    EvidenceValidation,
)
from sam.operational_intelligence.runtime_observation import (
    RuntimeObserver,
    RuntimeObservationReporter,
)
from sam.operational_intelligence.provider_observation import (
    ProviderAvailabilityEvaluator,
    ProviderHealth,
    ProviderObserver,
    ProviderSnapshot,
)
from sam.operational_intelligence.investigation_timeline import (
    TimelineBuilder,
    TimelineViewer,
)
from sam.operational_intelligence.investigation_api import (
    InvestigationAPI,
    InvestigationQuery,
)
from sam.operational_intelligence.investigation_explainability import (
    InvestigationExplainer,
)
from sam.operational_intelligence.investigation_compliance import (
    InvestigationComplianceChecker,
    ForbiddenPatternCheck,
)


# ---------------------------------------------------------------------------
# WP-01 Investigation Model
# ---------------------------------------------------------------------------

class TestInvestigationModel:
    def test_create_has_unique_id_and_created_state(self):
        inv = Investigation.create()
        assert inv.investigation_id
        assert inv.state == InvestigationState.CREATED
        assert inv.as_dict()["state"] == InvestigationState.CREATED

    def test_two_investigations_unique_id(self):
        a = Investigation.create()
        b = Investigation.create()
        assert a.investigation_id != b.investigation_id

    def test_set_scope_transitions_to_scope_set(self):
        target = InvestigationTarget("runtime", "runtime-1", "Main Runtime")
        scope = InvestigationScope("cpu high", (target,))
        inv = Investigation.create().with_scope(scope)
        assert inv.state == InvestigationState.SCOPE_SET
        assert inv.scope_hash

    def test_scope_contains_target(self):
        target = InvestigationTarget("runtime", "runtime-1")
        scope = InvestigationScope("r", (target,))
        assert scope.contains("runtime-1")
        assert not scope.contains("other")

    def test_invalid_scope_transition_raises(self):
        inv = Investigation.create()
        with pytest.raises(ValueError):
            inv.with_result(
                InvestigationResult(
                    investigation_id=inv.investigation_id,
                    status="done",
                    summary="",
                    created_at="",
                )
            )

    def test_result_immutable_after_completed(self):
        target = InvestigationTarget("runtime", "r1")
        scope = InvestigationScope("s", (target,))
        inv = Investigation.create().with_scope(scope).with_state(
            InvestigationState.ANALYZING
        )
        result = InvestigationResult(
            investigation_id=inv.investigation_id,
            status="completed",
            summary="all good",
            created_at="now",
            evidence_count=2,
        )
        done = inv.with_result(result)
        assert done.state == InvestigationState.COMPLETED
        assert done.result.summary == "all good"


# ---------------------------------------------------------------------------
# WP-02 Investigation Session
# ---------------------------------------------------------------------------

class TestInvestigationSession:
    def test_create_session_active(self):
        manager = InvestigationSessionManager()
        ctx = SessionContext(investigation_id="inv-1", operator="op")
        session = manager.create_session(ctx)
        assert session.state == SessionState.ACTIVE
        assert manager.get(session.session_id) is session

    def test_session_add_investigation(self):
        manager = InvestigationSessionManager()
        ctx = SessionContext(investigation_id="inv-1")
        session = manager.create_session(ctx).add_investigation("inv-1")
        assert "inv-1" in session.investigations

    def test_complete_session_immutable(self):
        session = InvestigationSession.create(
            context=SessionContext(investigation_id="inv-1")
        ).complete()
        assert session.is_immutable
        assert session.state == SessionState.COMPLETED

    def test_session_history_auditable(self):
        session = InvestigationSession.create(
            context=SessionContext(investigation_id="inv-1")
        )
        assert len(session.history) >= 1
        assert any(h.event == "created" for h in session.history)

    def test_session_manager_snapshot(self):
        manager = InvestigationSessionManager()
        session = manager.create_session(
            SessionContext(investigation_id="inv-1")
        )
        snap = manager.snapshot(session.session_id)
        assert snap is not None
        assert snap.session_id == session.session_id
        assert snap.state == SessionState.ACTIVE


# ---------------------------------------------------------------------------
# WP-03 Evidence Collection
# ---------------------------------------------------------------------------

class TestEvidenceCollection:
    def test_evidence_model_has_metadata(self):
        src = EvidenceSource("runtime", "runtime-1", "Runtime 1")
        ev = EvidenceModel(
            evidence_id="e1",
            investigation_id="inv-1",
            source=src,
            category="health",
            data=(("cpu", 90),),
            metadata=(("source", "runtime-1"),),
        )
        assert ev.as_dict()["source"]["source_id"] == "runtime-1"
        assert ev.metadata

    def test_validation_rejects_no_metadata(self):
        src = EvidenceSource("runtime", "runtime-1")
        ev = EvidenceModel(
            evidence_id="e1",
            investigation_id="inv-1",
            source=src,
            category="health",
        )
        result = EvidenceValidation.validate(ev)
        assert not result.valid
        assert result.reason == "no metadata"

    def test_collector_collects_from_registered_sources(self):
        collector = EvidenceCollector()

        def probe(investigation_id=""):
            return [
                EvidenceModel(
                    evidence_id="e-a",
                    investigation_id=investigation_id,
                    source=EvidenceSource("runtime", "a"),
                    category="health",
                    metadata=(("k", "v"),),
                )
            ]

        collector.register_source("a", probe)
        collected = collector.collect("inv-1")
        assert len(collected) == 1
        assert collected[0].investigation_id == "inv-1"

    def test_repository_append_only(self):
        repo = EvidenceRepository()
        src = EvidenceSource("runtime", "r")
        ev1 = repo.build(
            "inv-1", src, "health", {"cpu": 10}, {"src": "r"}
        )
        ev2 = repo.build(
            "inv-1", src, "health", {"cpu": 20}, {"src": "r"}
        )
        repo.save("inv-1", (ev1,))
        repo.save("inv-1", (ev2,))
        assert len(repo.get("inv-1")) == 2


# ---------------------------------------------------------------------------
# WP-04 Runtime Observation
# ---------------------------------------------------------------------------

class TestRuntimeObservation:
    def test_observe_read_only(self):
        observer = RuntimeObserver()
        observer.register_probe("cpu", lambda: {"cpu_percent": 85, "health": "warning"})
        snapshot = observer.observe("runtime-1")
        assert snapshot.runtime_id == "runtime-1"
        assert snapshot.health == "warning"
        assert snapshot.snapshot_hash

    def test_snapshot_immutable(self):
        observer = RuntimeObserver()
        observer.register_probe("cpu", lambda: {"cpu_percent": 50})
        s1 = observer.observe("r")
        s2 = observer.observe("r")
        # Setiap observe menghasilkan snapshot baru (append history), immutable.
        assert len(observer.all_snapshots()) == 2
        assert len(observer.last_snapshot().metrics) == 1

    def test_observation_to_evidence(self):
        observer = RuntimeObserver()
        observer.register_probe("cpu", lambda: {"cpu_percent": 90})
        snapshot = observer.observe("r")
        ev = RuntimeObservationReporter.to_evidence(snapshot, "inv-1")
        assert ev.category == "runtime_observation"
        assert ev.validated


# ---------------------------------------------------------------------------
# WP-05 Provider Observation
# ---------------------------------------------------------------------------

class TestProviderObservation:
    def test_observe_provider_without_execution(self):
        observer = ProviderObserver()
        observer.register_probe(
            "provider-a", lambda: {"health": ProviderHealth.HEALTHY, "latency_ms": 30}
        )
        snapshot = observer.observe("provider-a")
        assert snapshot is not None
        assert snapshot.health == ProviderHealth.HEALTHY

    def test_unreachable_provider(self):
        observer = ProviderObserver()

        def boom():
            raise RuntimeError("unreachable")

        observer.register_probe("provider-b", boom)
        snapshot = observer.observe("provider-b")
        assert snapshot.health == ProviderHealth.UNREACHABLE
        assert snapshot.available is False

    def test_availability_evaluator(self):
        snap = ProviderSnapshot(
            provider_id="p", captured_at="", health=ProviderHealth.HEALTHY
        )
        assert ProviderAvailabilityEvaluator.evaluate(snap) is True
        snap2 = ProviderSnapshot(
            provider_id="p", captured_at="", health=ProviderHealth.UNREACHABLE
        )
        assert ProviderAvailabilityEvaluator.evaluate(snap2) is False

    def test_provider_observation_auditable(self):
        observer = ProviderObserver()
        observer.register_probe("p", lambda: {"health": ProviderHealth.HEALTHY})
        observer.observe("p")
        obs = observer.observation("p")
        assert obs is not None
        assert obs.as_dict()["auditable"] is True


# ---------------------------------------------------------------------------
# WP-06 Investigation Timeline
# ---------------------------------------------------------------------------

class TestInvestigationTimeline:
    def test_build_ordered_timeline(self):
        builder = TimelineBuilder("inv-1")
        builder.record("scope", "set scope")
        builder.record("evidence", "add ev")
        timeline = builder.build()
        assert timeline.event_count == 2
        assert timeline.events[0].sequence < timeline.events[1].sequence

    def test_timeline_immutable(self):
        builder = TimelineBuilder("inv-1")
        builder.record("created")
        t1 = builder.build()
        builder.record("evidence")
        t2 = builder.build()
        assert t1.event_count == 1
        assert t2.event_count == 2

    def test_viewer_by_type(self):
        builder = TimelineBuilder("inv-1")
        builder.record("evidence")
        builder.record("analysis")
        timeline = builder.build()
        evs = TimelineViewer.by_type(timeline, "evidence")
        assert len(evs) == 1


# ---------------------------------------------------------------------------
# WP-07 Investigation API
# ---------------------------------------------------------------------------

class TestInvestigationAPI:
    def _build(self):
        manager = InvestigationSessionManager()
        repo = EvidenceRepository()
        investigations = {}
        timelines = {}

        inv = Investigation.create(
            metadata=InvestigationMetadata(purpose="test")
        )
        target = InvestigationTarget("runtime", "r1")
        scope = InvestigationScope("reason", (target,))
        inv = inv.with_scope(scope)
        investigations[inv.investigation_id] = inv

        builder = TimelineBuilder(inv.investigation_id)
        builder.record("scope")
        timelines[inv.investigation_id] = builder.build()

        api = InvestigationAPI(
            sessions=manager,
            evidences=repo,
            investigations=investigations,
            timelines=timelines,
        )
        return api, inv

    def test_query_all(self):
        api, inv = self._build()
        results = api.query_investigations()
        assert len(results) == 1
        assert results[0]["investigation_id"] == inv.investigation_id

    def test_query_by_target(self):
        api, inv = self._build()
        results = api.query_investigations(
            InvestigationQuery(target_id="r1")
        )
        assert len(results) == 1
        no = api.query_investigations(
            InvestigationQuery(target_id="nope")
        )
        assert len(no) == 0

    def test_get_evidence(self):
        api, inv = self._build()
        src = EvidenceSource("runtime", "r1")
        repo = api._evidences
        ev = repo.build(inv.investigation_id, src, "health", {"cpu": 5}, {"k": "v"})
        repo.save(inv.investigation_id, (ev,))
        found = api.get_evidence(ev.evidence_id)
        assert found is not None
        assert found["category"] == "health"


# ---------------------------------------------------------------------------
# WP-08 Investigation Explainability
# ---------------------------------------------------------------------------

class TestInvestigationExplainability:
    def test_explanation_has_evidence_chain(self):
        inv = Investigation.create()
        target = InvestigationTarget("runtime", "r1")
        inv = inv.with_scope(InvestigationScope("s", (target,)))
        src = EvidenceSource("runtime", "r1")
        ev = EvidenceModel(
            evidence_id="e1",
            investigation_id=inv.investigation_id,
            source=src,
            category="health",
            data=(("health", "critical"),),
            metadata=(("k", "v"),),
        )
        builder = TimelineBuilder(inv.investigation_id)
        builder.record("created")
        timeline = builder.build()
        explainer = InvestigationExplainer()
        expl = explainer.explain(inv, (ev,), timeline)
        assert expl.evidence_chain.length == 1
        assert expl.evidence_chain.attributions[0].source_id == "r1"
        assert expl.timeline.summary

    def test_source_attribution_present(self):
        inv = Investigation.create()
        src = EvidenceSource("provider", "p1")
        ev = EvidenceModel(
            evidence_id="e2",
            investigation_id=inv.investigation_id,
            source=src,
            category="provider_observation",
            metadata=(("k", "v"),),
        )
        explainer = InvestigationExplainer()
        expl = explainer.explain(inv, (ev,), None)
        attr = expl.evidence_chain.attributions[0]
        assert attr.source_type == "provider"
        assert attr.source_id == "p1"


# ---------------------------------------------------------------------------
# WP-09 Investigation Compliance
# ---------------------------------------------------------------------------

class TestInvestigationCompliance:
    def test_no_mutation_in_source(self):
        source = """
def observe(runtime):
    return runtime.snapshot()
"""
        result = ForbiddenPatternCheck.check(source)
        assert result.passed

    def test_execution_pattern_detected(self):
        source = "def run():\n    provider.execute()\n"
        result = ForbiddenPatternCheck.check(source)
        assert not result.passed
        assert any(f.code == "FORBIDDEN_PATTERN" for f in result.findings)

    def test_forbidden_import_detected(self):
        source = "import requests\n"
        result = ForbiddenPatternCheck.check(source)
        assert not result.passed
        assert any(f.code == "FORBIDDEN_IMPORT" for f in result.findings)

    def test_read_only_verify(self):
        checker = InvestigationComplianceChecker()
        assert checker.check_read_only().passed
        assert not checker.check_read_only(execution=True).passed
        assert not checker.check_read_only(runtime_mutation=True).passed
        assert not checker.check_read_only(approval=True).passed

    def test_certify_clean(self):
        checker = InvestigationComplianceChecker()
        cert = checker.certify()
        assert cert["certified"] is True


# ---------------------------------------------------------------------------
# WP-10 Integration & Certification (end-to-end)
# ---------------------------------------------------------------------------

class TestInvestigationEndToEnd:
    def test_end_to_end_investigation(self):
        # 1. Session + investigation
        manager = InvestigationSessionManager()
        ctx = SessionContext(investigation_id="", operator="op-1")
        core_inv = Investigation.create(
            metadata=InvestigationMetadata(purpose="e2e")
        )

        # 2. Scope
        target = InvestigationTarget("runtime", "runtime-core")
        core_inv = core_inv.with_scope(
            InvestigationScope("investigate health", (target,))
        )
        ctx = SessionContext(
            investigation_id=core_inv.investigation_id, operator="op-1"
        )
        session = manager.create_session(ctx).add_investigation(
            core_inv.investigation_id
        )

        # 3. Evidence
        repo = EvidenceRepository()
        observer = RuntimeObserver()
        observer.register_probe("cpu", lambda: {"cpu_percent": 92, "health": "critical"})
        snapshot = observer.observe("runtime-core")
        ev = RuntimeObservationReporter.to_evidence(
            snapshot, core_inv.investigation_id
        )
        repo.save(core_inv.investigation_id, (ev,))

        # 4. Timeline
        builder = TimelineBuilder(core_inv.investigation_id)
        builder.record("scope", "set scope")
        builder.record("evidence", "collected runtime evidence")
        timeline = builder.build()

        # 5. API + explainability + compliance
        investigations = {core_inv.investigation_id: core_inv}
        timelines = {core_inv.investigation_id: timeline}
        api = InvestigationAPI(
            sessions=manager,
            evidences=repo,
            investigations=investigations,
            timelines=timelines,
        )
        assert len(api.query_investigations()) == 1
        assert len(api.list_evidence(core_inv.investigation_id)) == 1
        assert api.get_timeline(core_inv.investigation_id) is not None

        explainer = InvestigationExplainer()
        expl = explainer.explain(core_inv, repo.get(core_inv.investigation_id), timeline)
        assert expl.observation_summary.observations == 1

        checker = InvestigationComplianceChecker()
        assert checker.check_source(
            "runtime.snapshot()", "runtime_observer"
        ).passed
        assert checker.check_evidence(repo.get(core_inv.investigation_id)).passed
        assert checker.certify()["certified"] is True
