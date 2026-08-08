# IP-3.4-004 WP-40 - End-to-end Federation Operational Coordination &
# Ecosystem Readiness Certification test (AO-3.4-001, paket keempat)
#
# Definisi Done IP-3.4-004: federation mampu mengetahui apakah kolaborasi
# lintas-ekosistem LAYAK dilakukan, tetapi TIDAK pernah memulai kolaborasi
# tersebut secara otomatis.
#
# BUKAN distributed execution. BUKAN distributed scheduling.
# Yang dibangun = Operational COORDINATION INTELLIGENCE.
#
# Output = assessment, explanation, recommendation, readiness - bukan aksi.
#
# Guardrail IP-3.4-004 dikunci:
#   Readiness != Execution (OR-01)
#   Coordination != Orchestration (OR-02)
#   Recommendation != Command (OR-03)
#   Aggregation != Authority (OR-04)
#   Federation Health != Runtime Control (OR-05)
#   Local sovereignty preserved (OR-06)
#   Registry remains authoritative (OR-07)
#   Evidence-first readiness (OR-08)
#   Deterministic aggregation (OR-09)
#   Read-only operational API (OR-10)

import os

import pytest

from sam.citizen.federation.aggregation import (
    FederationReadinessAggregator,
)
from sam.citizen.federation.coordination_intelligence import (
    CoordinationIntelligence,
)
from sam.citizen.federation.explainability import (
    FederationOperationalExplainer,
)
from sam.citizen.federation.operational_api import FederationOperationalAPI
from sam.citizen.federation.operational_readiness import (
    FederationOperationalModel,
    FederationReadiness,
)
from sam.citizen.federation.recommendation import (
    CoordinationRecommendationResult,
    CoordinationRecommendationEngine,
)
from sam.citizen.federation.risk import (
    FederationRiskAssessment,
    FederationRiskAssessor,
)
from sam.citizen.federation.compliance import (
    compliance_check,
    default_source_files,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FED_ROOT = os.path.join(_ROOT, "src", "sam", "citizen", "federation")

# anggota Federation siap penuh di 5 dimensi
READY = {
    "foundation": 0.9, "trust": 0.85, "compatibility": 0.8,
    "collaboration": 0.9, "intelligence": 0.85,
}
# anggota sebagian siap
PARTIAL = {
    "foundation": 0.9, "trust": 0.6, "compatibility": 0.5,
    "collaboration": 0.7, "intelligence": 0.6,
}
# anggota belum siap
NOT_READY = {
    "foundation": 0.3, "trust": 0.2, "compatibility": 0.1,
    "collaboration": 0.2, "intelligence": 0.2,
}


@pytest.fixture
def api():
    return FederationOperationalAPI()


@pytest.fixture
def model():
    return FederationOperationalModel()


@pytest.fixture
def ready_federation(api, model):
    """Federation dengan 2 anggota ready + 1 partial."""
    m = (model.assess("eco-a", READY, ("audited",)),
         model.assess("eco-b", READY, ("audited",)),
         model.assess("eco-c", PARTIAL, ("reviewed",)))
    agg = api.aggregate_readiness(m)
    return agg


# --------------------------------------------------------------------------
# WP-31 Federation Operational Model
# --------------------------------------------------------------------------

def test_readiness_assess_ready(api, model):
    r = api.assess_readiness("eco-a", READY, ("audited",))
    assert isinstance(r, FederationReadiness)
    assert r.member_id == "eco-a"
    assert r.overall >= 0.7
    assert r.level == "ready"
    assert r.evidence == ("audited",)


def test_readiness_assess_partial(model):
    r = model.assess("eco-c", PARTIAL)
    assert 0.4 <= r.overall < 0.7
    assert r.level == "partial"


def test_readiness_assess_not_ready(model):
    r = model.assess("eco-d", NOT_READY)
    assert r.overall < 0.4
    assert r.level == "not-ready"


def test_readiness_score_per_dimension(model):
    r = model.assess("eco-a", READY)
    assert r.score("trust") == pytest.approx(0.85)
    assert r.score("nonexistent") is None


def test_readiness_score_clamped(model):
    r = model.assess("eco-a", {"foundation": 5.0})  # >1 diklamp
    assert r.score("foundation") == 1.0


def test_readiness_not_execution(api, model):
    # OR-01: readiness hanya assessment, tanpa aksi
    r = api.assess_readiness("eco-a", READY)
    assert r.as_dict()["overall"] >= 0.7
    assert not hasattr(api, "run_workflow")
    assert not hasattr(api, "start_collaboration")


# --------------------------------------------------------------------------
# WP-32 Readiness Aggregation Engine
# --------------------------------------------------------------------------

def test_aggregate_overall(api, ready_federation):
    assert ready_federation.overall >= 0.5
    assert len(ready_federation.members) == 3


def test_aggregate_level_distribution(api, ready_federation):
    d = ready_federation.level_distribution
    assert d["ready"] == 2
    assert d["partial"] == 1
    assert d["not-ready"] == 0


def test_aggregate_dimension_averages(api, ready_federation):
    av = ready_federation.dimension_averages
    assert "trust" in av
    assert 0.0 < av["trust"] <= 1.0


def test_aggregate_deterministic(api, model):
    # OR-09 deterministik
    m1 = (model.assess("eco-a", READY), model.assess("eco-b", PARTIAL))
    m2 = (model.assess("eco-a", READY), model.assess("eco-b", PARTIAL))
    a1 = api.aggregate_readiness(m1).as_dict()
    a2 = api.aggregate_readiness(m2).as_dict()
    assert a1 == a2


def test_aggregate_not_authority(api, ready_federation):
    # OR-04: agregasi hanya ringkasan; tidak ada otoritas terbentuk
    assert ready_federation.level in ("ready", "partial", "not-ready")
    assert not hasattr(api, "global_authority")
    assert not hasattr(api, "override_member")


# --------------------------------------------------------------------------
# WP-33 Coordination Intelligence
# --------------------------------------------------------------------------

def test_coordination_insight_aligned(api, model):
    m = (model.assess("eco-a", READY), model.assess("eco-b", READY))
    agg = api.aggregate_readiness(m)
    insights = api.coordination_insights(agg)
    overall = next(i for i in insights if i.focus == "overall")
    assert overall.pattern == "aligned"
    assert "seluruh anggota" in overall.assessment


def test_coordination_insight_gapped(api, model):
    m = (model.assess("eco-a", NOT_READY), model.assess("eco-b", NOT_READY))
    agg = api.aggregate_readiness(m)
    insights = api.coordination_insights(agg)
    overall = next(i for i in insights if i.focus == "overall")
    assert overall.pattern == "gapped"


def test_coordination_insight_weakest_dimension(api, ready_federation):
    insights = api.coordination_insights(ready_federation)
    dim = next(i for i in insights if i.focus == "dimensions")
    assert dim.weakest_dimension is not None
    assert dim.weakest_member is None  # fokus dimensi


def test_coordination_not_orchestration(api, ready_federation):
    # OR-02: insight, bukan orchestration
    insights = api.coordination_insights(ready_federation)
    assert insights
    assert not hasattr(api, "orchestrate")
    assert not hasattr(api, "distributed_schedule")


# --------------------------------------------------------------------------
# WP-34 Federation Risk Assessment
# --------------------------------------------------------------------------

def test_risk_all_ready(api, model):
    m = (model.assess("eco-a", READY), model.assess("eco-b", READY))
    agg = api.aggregate_readiness(m)
    risk = api.federation_risk(agg)
    assert isinstance(risk, FederationRiskAssessment)
    assert risk.level == "low"
    assert all(r.severity != "high" for r in risk.risks)


def test_risk_identifies_bottleneck(api, ready_federation):
    risk = api.federation_risk(ready_federation)
    kinds = {r.kind for r in risk.risks}
    # eco-c partial -> tidak under 0.4; mungkin tanpa bottleneck dimensi
    assert isinstance(risk, FederationRiskAssessment)
    assert risk.level in ("low", "medium", "high")


def test_risk_bottleneck_detected(api, model):
    m = (model.assess("eco-d", NOT_READY),)
    agg = api.aggregate_readiness(m)
    risk = api.federation_risk(agg)
    assert any(r.kind == "member-not-ready" for r in risk.risks)
    assert risk.level == "high"


def test_risk_not_failover(api, ready_federation):
    # OR-05: health/risk observasional; bukan failover/load balancing
    risk = api.federation_risk(ready_federation)
    assert not hasattr(api, "failover")
    assert not hasattr(api, "load_balance")
    assert not any("failover" in r.kind for r in risk.risks)


# --------------------------------------------------------------------------
# WP-35 Coordination Recommendation
# --------------------------------------------------------------------------

def test_recommend_not_ready(api, model):
    m = (model.assess("eco-d", NOT_READY),)
    agg = api.aggregate_readiness(m)
    res = api.recommend_coordination(agg)
    assert isinstance(res, CoordinationRecommendationResult)
    assert res.is_command is False  # OR-03
    assert any(r.focus == "federation-readiness" for r in res.recommendations)
    # semua rekomendasi advisory
    assert all(not r.is_command for r in res.recommendations)


def test_recommend_ready_eligible(api, ready_federation):
    res = api.recommend_coordination(ready_federation)
    assert res.is_command is False
    foci = {r.focus for r in res.recommendations}
    assert "collaboration-eligible" in foci


def test_recommendation_not_command(api, ready_federation):
    result = api.recommend_coordination(ready_federation)
    for r in result.recommendations:
        assert r.is_command is False
        assert r.basis  # evidence-first OR-08


# --------------------------------------------------------------------------
# WP-36 Federation Explainability
# --------------------------------------------------------------------------

def test_explain_readiness(api, ready_federation):
    ex = api.explain_readiness(ready_federation)
    assert ex.focus == "federation-readiness"
    assert "Kesiapan" in ex.summary or "readiness" in ex.summary.lower()
    assert ex.basis


def test_explain_coordination(api, ready_federation):
    exs = api.explain_coordination(ready_federation)
    assert exs
    for e in exs:
        assert e.is_command is False  # OR-03
        assert e.basis


def test_explain_aggregate_members(api, ready_federation):
    ex = api.explain_readiness(ready_federation)
    assert len(ex.member_contributions) == 3


# --------------------------------------------------------------------------
# WP-37 Federation Operational API (read-only)
# --------------------------------------------------------------------------

def test_api_read_only(api):
    assert api.has_authority_action() is False
    assert api.allowed_actions()


def test_api_no_authority_verbs(api):
    for bad in ("connect", "execute", "authorize", "approve", "failover",
                "load_balance", "schedule", "select_leader", "activate",
                "sync_state", "run_workflow", "elect_leader",
                "start_collaboration"):
        assert not hasattr(api, bad), "API tidak boleh punya {}".format(bad)


def test_api_health_observational(api, ready_federation):
    h = api.federation_health(ready_federation)
    assert "overall" in h
    assert "level" in h
    assert h["ready"] is (ready_federation.level == "ready")
    # health hanya pengamatan, tidak mengirim perintah kontrol
    assert all(not hasattr(api, x) for x in ("restart", "stop", "start"))


# --------------------------------------------------------------------------
# WP-38 Federation Compliance
# --------------------------------------------------------------------------

def test_compliance_suite_39_passed():
    files = default_source_files(_FED_ROOT)
    passed, checks = compliance_check(files, module_root=_FED_ROOT)
    assert passed
    ids = {c.check_id for c in checks}
    assert {"FED-01", "TRUST-01", "DGI-01", "OR-01"} <= ids
    assert len(checks) == 39
    assert sum(1 for c in checks if c.passed) == 39


def test_compliance_or_group_present():
    files = default_source_files(_FED_ROOT)
    _, checks = compliance_check(files, module_root=_FED_ROOT)
    or_ids = {c.check_id for c in checks if c.check_id.startswith("OR-")}
    assert or_ids == {"OR-01", "OR-02", "OR-03", "OR-04", "OR-05",
                      "OR-06", "OR-07", "OR-08", "OR-09", "OR-10"}


# --------------------------------------------------------------------------
# WP-40 Exit criteria
# --------------------------------------------------------------------------

def test_exit_criteria_knows_readiness_without_acting():
    """Federation tahu kesiapan operasional kolektif, namun TIDAK pernah
    memulai kolaborasi secara otomatis."""
    api = FederationOperationalAPI()
    model = FederationOperationalModel()

    # kumpulkan readiness seluruh anggota (foundation/trust/compat/collab/intel)
    members = (model.assess("eco-a", READY, ("audited-1",)),
               model.assess("eco-b", READY, ("audited-2",)),
               model.assess("eco-c", PARTIAL, ("reviewed",)))

    # 1) gambaran kesiapan kolektif
    agg = api.aggregate_readiness(members)
    assert len(agg.members) == 3
    assert agg.overall > 0

    # 2) insight koordinasi (bukan orchestration, OR-02)
    insights = api.coordination_insights(agg)
    assert insights

    # 3) identifikasi bottleneck (OR-01: assessment, bukan aksi)
    risk = api.federation_risk(agg)
    assert isinstance(risk, FederationRiskAssessment)

    # 4) rekomendasi koordinasi (OR-03: saran, bukan perintah)
    recs = api.recommend_coordination(agg)
    assert all(not r.is_command for r in recs.recommendations)

    # 5) penjelasan (OR-08 evidence-first)
    ex = api.explain_readiness(agg)
    assert ex.basis

    # 6) federation TIDAK memulai kolaborasi otomatis - tidak ada aksi apa pun
    for bad in ("run_workflow", "start_collaboration", "failover",
                "load_balance", "select_leader", "distributed_schedule",
                "sync_state", "activate_remote", "authorize", "execute"):
        assert not hasattr(api, bad)

    # 7) health observasional (OR-05), bukan kontrol runtime
    h = api.federation_health(agg)
    assert "overall" in h

    # 8) kedaulatan lokal (OR-06): tidak ada otoritas yang menimpa anggota
    assert not hasattr(api, "override_member")
    assert not hasattr(api, "elect_leader")
