"""Tests for C-Phase 3: Observation Recommendation Engine.

Memverifikasi bahwa engine menghasilkan rekomendasi OPERASIONAL dari analisis
observasi (bukan aksi governance), dan bersifat read-only murni.

Domain: Observation -> Analytics -> Recommendation.
Constraints enforced: source = PublicationRegistry saja; output = recommendation
observasi saja; tidak ada mutate/execute/approve.
"""
from __future__ import annotations
import pytest

from sam.observation.publication import (
    PublicationAdapter,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.recommendation import (
    ObservationRecommendation,
    ObservationRecommendationEngine,
    OperationalRecommendationReport,
)


# ── Test Helpers (sama dengan test_gap_resolution.py) ──

def _make_adapter(runtime_id: str, health="healthy", readiness="operational",
                  metrics=5, dashboards=3, health_checks=3, snapshots=5,
                  timeline=10, has_preview=True, has_metadata=True,
                  has_lifecycle=True, operational="running") -> PublicationAdapter:
    pub = RuntimePublication(
        runtime_id=runtime_id,
        health_state=health,
        readiness_level=readiness,
        operational_state=operational,
        metric_count=metrics,
        dashboard_count=dashboards,
        health_check_count=health_checks,
        snapshot_count=snapshots,
        timeline_events=timeline,
        has_preview=has_preview,
        has_metadata=has_metadata,
        has_lifecycle=has_lifecycle,
    )
    return _adapter_for(pub)


def _adapter_for(publication: RuntimePublication) -> PublicationAdapter:
    class _A(PublicationAdapter):
        def runtime_id(self) -> str:
            return publication.runtime_id
        def observe(self) -> RuntimePublication:
            return publication
    return _A()


def _registry_with(*adapters: PublicationAdapter) -> PublicationRegistry:
    reg = PublicationRegistry()
    for a in adapters:
        reg.register(a)
    return reg


def _healthy_registry() -> PublicationRegistry:
    # Semua runtime sehat & lengkap -> tidak boleh ada rekomendasi
    return _registry_with(
        _make_adapter("mission"),
        _make_adapter("policy"),
        _make_adapter("workflow"),
    )


# ═══════════════════════════════════════════════════════════════════════
# Observation Recommendation Engine
# ═══════════════════════════════════════════════════════════════════════

class TestRecommendationEngineBasics:
    def test_empty_registry_returns_platform_recommendation(self):
        reg = _registry_with()
        report = ObservationRecommendationEngine(reg).recommend()
        assert isinstance(report, OperationalRecommendationReport)
        assert report.total_recommendations == 1
        r = report.recommendations[0]
        assert r.category == "missing_publication"
        assert r.severity == "critical"
        assert r.runtime_id == ""

    def test_healthy_full_registry_no_recommendations(self):
        reg = _healthy_registry()
        report = ObservationRecommendationEngine(reg).recommend()
        assert report.total_recommendations == 0
        assert report.by_severity == {
            "critical": 0, "high": 0, "medium": 0, "low": 0,
        }

    def test_report_is_immutable(self):
        reg = _registry_with(_make_adapter("mission", health="unhealthy"))
        report = ObservationRecommendationEngine(reg).recommend()
        with pytest.raises(Exception):
            report.total_recommendations = 99  # frozen dataclass
        with pytest.raises(Exception):
            report.recommendations = ()  # frozen dataclass

    def test_recommendation_is_immutable(self):
        reg = _registry_with(_make_adapter("mission", health="unhealthy"))
        report = ObservationRecommendationEngine(reg).recommend()
        rec = report.recommendations[0]
        with pytest.raises(Exception):
            rec.title = "changed"  # frozen dataclass

    def test_as_dict_output(self):
        reg = _registry_with(_make_adapter("mission", health="unhealthy"))
        d = ObservationRecommendationEngine(reg).recommend().as_dict()
        assert d["status"] == "ok"
        assert d["total_recommendations"] >= 1
        assert "by_severity" in d
        assert "by_category" in d
        assert isinstance(d["recommendations"], list)
        assert all(isinstance(r, dict) for r in d["recommendations"])


class TestRecommendationCategories:
    def test_capability_degradation_unhealthy(self):
        reg = _registry_with(_make_adapter("mission", health="unhealthy"))
        report = ObservationRecommendationEngine(reg).recommend()
        cats = {r.category for r in report.recommendations}
        assert "capability_degradation" in cats
        cr = next(r for r in report.recommendations
                  if r.category == "capability_degradation")
        assert cr.severity == "critical"
        assert cr.runtime_id == "mission"
        assert cr.evidence

    def test_capability_degradation_degraded(self):
        reg = _registry_with(_make_adapter("policy", health="degraded"))
        report = ObservationRecommendationEngine(reg).recommend()
        cr = next(r for r in report.recommendations
                  if r.category == "capability_degradation")
        assert cr.severity == "high"

    def test_readiness_regression(self):
        reg = _registry_with(_make_adapter("mission", readiness="planned"))
        report = ObservationRecommendationEngine(reg).recommend()
        assert any(r.category == "readiness_regression"
                   for r in report.recommendations)

    def test_stale_timeline(self):
        reg = _registry_with(_make_adapter("workflow", timeline=0))
        report = ObservationRecommendationEngine(reg).recommend()
        assert any(r.category == "stale_timeline"
                   for r in report.recommendations)

    def test_missing_metadata(self):
        reg = _registry_with(_make_adapter("audit", has_preview=False,
                                           has_metadata=False))
        report = ObservationRecommendationEngine(reg).recommend()
        assert any(r.category == "missing_metadata"
                   for r in report.recommendations)

    def test_metric_insufficiency(self):
        reg = _registry_with(_make_adapter("knowledge", metrics=0))
        report = ObservationRecommendationEngine(reg).recommend()
        assert any(r.category == "metric_insufficiency"
                   for r in report.recommendations)

    def test_all_seven_categories_coverable(self):
        # Runtime dengan banyak masalah menghasilkan banyak kategori berbeda
        reg = _registry_with(_make_adapter(
            "mission", health="unhealthy", readiness="planned",
            timeline=0, has_preview=False, has_metadata=False, metrics=0,
        ))
        report = ObservationRecommendationEngine(reg).recommend()
        cats = {r.category for r in report.recommendations}
        assert cats == {
            "capability_degradation",
            "readiness_regression",
            "stale_timeline",
            "missing_metadata",
            "metric_insufficiency",
        }


class TestReadOnlyConstraint:
    def test_engine_never_prepends_governance_actions(self):
        # Rekomendasi TIDAK boleh berisi aksi governance/eksekusi
        forbidden = {
            "execute", "approve", "rerun", "restart", "publish",
            "submit", "transition", "finalize",
        }
        reg = _registry_with(_make_adapter(
            "mission", health="unhealthy", readiness="planned",
            timeline=0, has_preview=False, metrics=0,
        ))
        report = ObservationRecommendationEngine(reg).recommend()
        joined = " ".join(r.title.lower() for r in report.recommendations)
        for word in forbidden:
            assert word not in joined, f"Rekomendasi memuat aksi governance: {word}"

    def test_engine_only_reads_registry(self):
        # Registry tidak berubah setelah recommend()
        reg = _registry_with(_make_adapter("mission", health="unhealthy"),
                             _make_adapter("policy"))
        before = reg.registered_runtimes()
        before_obs = reg.observe_all().runtime_count
        ObservationRecommendationEngine(reg).recommend()
        after = reg.registered_runtimes()
        after_obs = reg.observe_all().runtime_count
        assert before == after
        assert before_obs == after_obs

    def test_report_contains_no_execution_fields(self):
        # Output murni rekomendasi observasi - tidak ada field eksekusi
        reg = _registry_with(_make_adapter("mission", health="unhealthy"))
        d = ObservationRecommendationEngine(reg).recommend().as_dict()
        forbidden = {"execution_id", "action_hint_execute", "approved"}
        assert not (forbidden & set(d.keys()))
        for rec in d["recommendations"]:
            assert "action" not in rec  # bukan aksi, tapi rekomendasi observasi
            assert "category" in rec


class TestSeverityAndAggregation:
    def test_severity_ordering(self):
        reg = _registry_with(
            _make_adapter("mission", health="unhealthy"),   # critical
            _make_adapter("policy", health="degraded"),      # high
            _make_adapter("artifact", timeline=0),           # medium
            _make_adapter("audit", metrics=0),               # low
        )
        report = ObservationRecommendationEngine(reg).recommend()
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sevs = [sev_order[r.severity] for r in report.recommendations]
        assert sevs == sorted(sevs)

    def test_by_severity_counts(self):
        reg = _registry_with(
            _make_adapter("mission", health="unhealthy"),
            _make_adapter("policy", health="degraded"),
        )
        report = ObservationRecommendationEngine(reg).recommend()
        assert report.by_severity["critical"] >= 1
        assert report.by_severity["high"] >= 1

    def test_by_category_counts(self):
        reg = _registry_with(_make_adapter("mission", health="unhealthy",
                                           timeline=0, metrics=0))
        report = ObservationRecommendationEngine(reg).recommend()
        assert report.by_category["capability_degradation"] >= 1
        assert report.by_category["stale_timeline"] >= 1
        assert report.by_category["metric_insufficiency"] >= 1
        assert sum(report.by_category.values()) == report.total_recommendations

    def test_multi_runtime_not_cross_contaminated(self):
        reg = _registry_with(
            _make_adapter("mission", health="unhealthy"),
            _make_adapter("policy", health="healthy"),
        )
        report = ObservationRecommendationEngine(reg).recommend()
        # Recommendation sehat policy tidak boleh ada
        assert not any(r.runtime_id == "policy"
                       for r in report.recommendations)


class TestPublicWiring:
    """Verifikasi C-Phase 3 public wiring (get_recommendation_engine)."""

    def test_wiring_exposes_engine(self):
        from sam.runtime_service.api.observation_wiring import (
            get_recommendation_engine,
            recommend_observations,
        )
        engine = get_recommendation_engine()
        assert isinstance(engine, ObservationRecommendationEngine)
        report = recommend_observations()
        assert isinstance(report, OperationalRecommendationReport)

    def test_observation_init_exports(self):
        from sam.observation import (
            ObservationRecommendation,
            ObservationRecommendationEngine,
            OperationalRecommendationReport,
        )
        assert ObservationRecommendation is not None
        assert ObservationRecommendationEngine is not None
        assert OperationalRecommendationReport is not None
