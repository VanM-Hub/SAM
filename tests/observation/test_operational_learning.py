"""Tests for C-Phase 4 (Workstream C10): Operational Learning.

Memverifikasi observer Operational Learning menghasilkan tren operasional,
pusat rekomendasi (dari Recommendation Engine C-Phase 3), ringkasan historis,
dan evidence learning - secara read-only, BUKAN AI/governance/autonomous decision.
"""
from __future__ import annotations
import dataclasses
import pytest

from sam.observation.publication import (
    PublicationAdapter,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.operational_learning import (
    HistoricalObservationSummary,
    LearningEvidence,
    LearningEvidenceReport,
    OperationalLearningObserver,
    OperationalRecommendation,
    OperationalRecommendationCenter,
    OperationalTrendEntry,
    OperationalTrendReport,
)


def _adapter_for(publication: RuntimePublication) -> PublicationAdapter:
    class _A(PublicationAdapter):
        def runtime_id(self) -> str:
            return publication.runtime_id
        def observe(self) -> RuntimePublication:
            return publication
    return _A()


def _registry() -> PublicationRegistry:
    reg = PublicationRegistry()
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="mission", health_state="healthy", readiness_level="operational",
        operational_state="ready", metric_count=5, health_check_count=2, timeline_events=8,
    )))
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="workflow", health_state="healthy", readiness_level="operational",
        operational_state="running", metric_count=3, health_check_count=1, timeline_events=4,
    )))
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="execution", health_state="degraded", readiness_level="operational",
        operational_state="degraded", metric_count=1, health_check_count=2, timeline_events=2,
    )))
    return reg


def _observer() -> OperationalLearningObserver:
    return OperationalLearningObserver(_registry())


class TestOperationalTrend:
    def test_trend_report(self):
        o = _observer()
        tr = o.trend_report()
        assert isinstance(tr, OperationalTrendReport)
        assert len(tr.entries) >= 3
        assert all(isinstance(e, OperationalTrendEntry) for e in tr.entries)

    def test_trend_dimensions(self):
        o = _observer()
        tr = o.trend_report()
        dims = {e.dimension for e in tr.entries}
        assert "health" in dims and "readiness" in dims and "operational" in dims

    def test_by_dimension(self):
        o = _observer()
        tr = o.trend_report()
        health = tr.by_dimension("health")
        assert health is not None
        assert 0.0 <= health.current <= 1.0


class TestOperationalRecommendationCenter:
    def test_uses_recommendation_engine(self):
        """Pusat rekomendasi memanfaatkan Recommendation Engine (C-Phase 3)."""
        # tanam engine palsu utk mastikan observasi tanpa runtime engine
        class _FakeEngine:
            def recommend(self):
                from sam.observation.recommendation import (
                    OperationalRecommendationReport, ObservationRecommendation,
                )
                return OperationalRecommendationReport(
                    status="ok", total_recommendations=1,
                    recommendations=(
                        ObservationRecommendation(
                            category="missing_publication", severity="medium",
                            runtime_id="x", title="Publikasi kurang", description="",
                            evidence=(), timestamp="now",
                        ),
                    ),
                )
        ob = OperationalLearningObserver(_registry(), recommendation_engine=_FakeEngine())
        rc = ob.recommendation_center()
        assert isinstance(rc, OperationalRecommendationCenter)
        assert rc.total_recommendations == 1
        assert rc.high_severity_count == 0  # medium tidak dihitung high

    def test_recommendation_center_readonly(self):
        """Rekomendasi = informasi, bukan keputusan/aksi governance."""
        o = _observer()
        rc = o.recommendation_center()
        assert isinstance(rc, OperationalRecommendationCenter)
        assert all(isinstance(r, OperationalRecommendation) for r in rc.recommendations)


class TestHistoricalSummary:
    def test_historical_summary(self):
        o = _observer()
        h = o.historical_summary()
        assert isinstance(h, HistoricalObservationSummary)
        assert h.total_runtimes == 3
        assert h.healthy_count == 2
        assert h.degraded_count == 1
        # total_observations = health_check_count sum (2+1+2)
        assert h.total_observations == 5


class TestLearningEvidence:
    def test_learning_evidence_ready(self):
        o = _observer()
        ev = o.learning_evidence()
        assert isinstance(ev, LearningEvidenceReport)
        assert ev.ready_to_learn is True
        categories = {e.category for e in ev.evidence}
        assert {"observation", "analytics", "readiness"} <= categories

    def test_evidence_entry(self):
        o = _observer()
        ev = o.learning_evidence()
        assert all(isinstance(e, LearningEvidence) for e in ev.evidence)


class TestLearningObserverReadOnly:
    def test_no_mutation_learning(self):
        """Read-only: learning TIDAK mengeksekusi/menyetujui/ubah apa pun.
        (dipindai pola pemanggilan aksi, bukan kata di docstring)."""
        import inspect
        from sam.observation import operational_learning as m
        src = inspect.getsource(m)
        # tidak ada pemanggilan aksi governance sebagai method execution
        assert ".execute(" not in src
        assert ".approve(" not in src
        assert ".reject(" not in src
        assert ".invoke(" not in src
        assert ".transition(" not in src
        assert ".finalize(" not in src
        assert ".publish(" not in src

    def test_no_governance_runtime_import(self):
        """C10 tidak import governance/runtime engine di level modul (stdlib-only)."""
        import inspect
        from sam.observation import operational_learning as m
        src = inspect.getsource(m)
        # hanya import standar + observasi (bukan runtime engine)
        assert "from sam.governance" not in src
        assert "from sam.execution" not in src
        assert "from sam.workflow" not in src
        assert "from sam.approval_runtime" not in src
        assert "BaseProvider" not in src

    def test_dto_are_immutable(self):
        for cls in (OperationalTrendEntry, OperationalTrendReport,
                    OperationalRecommendation, OperationalRecommendationCenter,
                    HistoricalObservationSummary, LearningEvidence,
                    LearningEvidenceReport):
            assert dataclasses.is_dataclass(cls)
            assert cls.__dataclass_params__.frozen


class TestOperationalLearningWiring:
    def test_wiring_getters_shortcuts(self):
        from sam.runtime_service.api.observation_wiring import (
            get_operational_learning_observer,
            observe_operational_trends,
            observe_operational_recommendations,
            observe_observation_history,
            observe_learning_evidence,
        )
        assert isinstance(get_operational_learning_observer(), OperationalLearningObserver)
        assert isinstance(observe_operational_trends(), OperationalTrendReport)
        assert isinstance(observe_operational_recommendations(), OperationalRecommendationCenter)
        assert isinstance(observe_observation_history(), HistoricalObservationSummary)
        assert isinstance(observe_learning_evidence(), LearningEvidenceReport)
