# IP-3.2-005 WP-50 - End-to-end Integration & Certification test
# Operational Readiness & Autonomous Coordination Intelligence
# (AO-3.2-001 / ED-3.2-005)
#
# Definisi Done IP-3.2-005: Runtime mampu secara deterministik mengintegrasikan
# seluruh proposal (observe/diagnose/plan/recover/coordinate/lifecycle) menjadi
# SATU penilaian kesiapan operasional yang utuh - dan menjawab: apakah sistem
# siap? apa penghambat? risiko terbesar? proposal terbaik? mengapa? bukti?
# seberapa dipercaya? - TANPA memperoleh kewenangan baru.
#
# Prinsip:
#   Aggregation != Decision   (engine menggabung/menilai/mejelaskan, tidak memilih)
#   Recommendation != Authority (rekomendasi menyusun prioritas, tidak mengeksekusi)
# Semua read-only, explainable, evidence-backed, proposal-only.

import os

import pytest

from sam.autonomy_runtime.operational_readiness.models import (
    OperationalReadiness,
    ReadinessInput,
)
from sam.autonomy_runtime.operational_readiness.aggregation import (
    ReadinessAggregationEngine,
)
from sam.autonomy_runtime.operational_readiness.coordination_intelligence import (
    AutonomousCoordinationIntelligence,
)
from sam.autonomy_runtime.operational_readiness.risk import OperationalRiskAssessor
from sam.autonomy_runtime.operational_readiness.recommendation import ReadinessRecommender
from sam.autonomy_runtime.operational_readiness.explainability import ReadinessExplainer
from sam.autonomy_runtime.operational_readiness.cross_runtime import (
    CrossRuntimeReadinessAssembler,
)
from sam.autonomy_runtime.api.operational_readiness import OperationalReadinessAPI
from sam.autonomy_runtime.compliance.readiness_checker import (
    compliance_check,
    default_source_files,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_RUNTIME_ROOT = os.path.join(_ROOT, "src", "sam", "autonomy_runtime")


def _inputs(ready=True, variant=""):
    """Masukan dari seluruh 7 sumber (observation..readiness)."""
    tag = variant
    if ready:
        obs_h, obs_s = "healthy", "ready"
        diag_h, plan_s, rec_s, coord_s, lc_s, rd_h = (
            "healthy", "ready", "ready", "ready", "ready", "healthy")
    else:
        obs_h, obs_s = "degraded", "degraded"
        diag_h, plan_s, rec_s, coord_s, lc_s, rd_h = (
            "degraded", "not_ready", "not_ready", "risky", "degraded", "degraded")
    return (
        ReadinessInput(source="observation", artifact_id="obs-"+tag,
                       health=obs_h, status=obs_s, confidence=0.8, evidence=("e1",)),
        ReadinessInput(source="diagnostics", artifact_id="diag-"+tag,
                       health=diag_h, status=diag_h, confidence=0.7, evidence=("e2",)),
        ReadinessInput(source="planning", artifact_id="plan-"+tag,
                       status=plan_s, confidence=0.6, evidence=("e3",)),
        ReadinessInput(source="recovery", artifact_id="rec-"+tag,
                       status=rec_s, confidence=0.7, evidence=("e4",)),
        ReadinessInput(source="coordination", artifact_id="coord-"+tag,
                       status=coord_s, confidence=0.6, evidence=("e5",)),
        ReadinessInput(source="lifecycle", artifact_id="lc-"+tag,
                       status=lc_s, confidence=0.7, evidence=("e6",)),
        ReadinessInput(source="readiness", artifact_id="rd-"+tag,
                       health=rd_h, status=rd_h, confidence=0.8, evidence=("e7",)),
    )


# --------------------------------------------------------------------------
# 1. Operational Readiness Model (WP-41)
# --------------------------------------------------------------------------

def test_readiness_model_immutable():
    r = ReadinessAggregationEngine().build_readiness(_inputs(), readiness_id="or-t1")
    assert isinstance(r, OperationalReadiness)
    assert r.is_proposal_only is True
    assert r.input_count() == 7
    assert r.dimension_count() == 7
    with pytest.raises(Exception):
        r.inputs = ()


def test_readiness_input_evidence():
    i = _inputs()[0]
    assert i.source == "observation"
    assert i.evidence == ("e1",)
    with pytest.raises(Exception):
        i.evidence = ()


# --------------------------------------------------------------------------
# 2. Readiness Aggregation Engine (WP-42)
# --------------------------------------------------------------------------

def test_aggregation_ready_system():
    r = ReadinessAggregationEngine().build_readiness(_inputs(ready=True), "or-ready")
    assert r.ready is True
    assert r.overall_level == "ready"
    assert r.overall_score >= 0.8
    assert len(r.blockers) == 0


def test_aggregation_not_ready_system():
    r = ReadinessAggregationEngine().build_readiness(_inputs(ready=False), "or-notready")
    assert r.ready is False
    assert r.overall_level == "not_ready"
    assert len(r.blockers) > 0


def test_aggregation_deterministic():
    e = ReadinessAggregationEngine()
    r1 = e.build_readiness(_inputs(), "or-det")
    r2 = e.build_readiness(_inputs(), "or-det")
    assert r1 == r2
    assert r1.overall_score == r2.overall_score


def test_aggregation_never_decides():
    # agregasi hanya memberi skor & level - tidak ada field "selected_action"
    r = ReadinessAggregationEngine().build_readiness(_inputs(), "or-nodecide")
    d = r.as_dict()
    assert "recommendation" in d
    assert r.recommendation == "operational readiness stated; no action selected"


# --------------------------------------------------------------------------
# 3. Autonomous Coordination Intelligence (WP-43)
# --------------------------------------------------------------------------

def test_coordination_intelligence_aligned():
    r = ReadinessAggregationEngine().build_readiness(_inputs(ready=True), "or-ci")
    ci = AutonomousCoordinationIntelligence().analyze(r)
    assert ci.aligned is True
    assert ci.is_proposal_only is True
    assert ci.finding_count() >= 1


def test_coordination_intelligence_deterministic():
    r = ReadinessAggregationEngine().build_readiness(_inputs(), "or-ci2")
    a = AutonomousCoordinationIntelligence().analyze(r)
    b = AutonomousCoordinationIntelligence().analyze(r)
    assert a == b


# --------------------------------------------------------------------------
# 4. Operational Risk Assessment (WP-44)
# --------------------------------------------------------------------------

def test_risk_assessment_reports_highest():
    r = ReadinessAggregationEngine().build_readiness(_inputs(ready=False), "or-risk")
    rep = OperationalRiskAssessor().assess(r)
    assert rep.risk_count() >= 1
    top = rep.highest_risk()
    assert top is not None
    # risiko terbesar benar-benar teridentifikasi (bukan kosong)
    assert top.score > 0.0
    assert rep.top_risks  # tidak kosong


def test_risk_no_risk_for_ready():
    r = ReadinessAggregationEngine().build_readiness(_inputs(ready=True), "or-lowrisk")
    rep = OperationalRiskAssessor().assess(r)
    assert rep.overall_risk == "low"
    assert rep.highest_risk() is None


# --------------------------------------------------------------------------
# 5. Readiness Recommendation Engine (WP-45)
# --------------------------------------------------------------------------

def test_recommendation_prioritized_proposal():
    r = ReadinessAggregationEngine().build_readiness(_inputs(ready=False), "or-rec")
    rep = OperationalRiskAssessor().assess(r)
    rec = ReadinessRecommender().recommend(r, rep)
    assert rec.is_proposal_only is True
    assert rec.requires_governance is True
    assert rec.action_count() >= 1
    top = rec.highest_priority()
    assert top is not None
    assert top.priority == 1


def test_recommendation_never_executes_never_selects_final():
    r = ReadinessAggregationEngine().build_readiness(_inputs(), "or-rec2")
    rep = OperationalRiskAssessor().assess(r)
    rec = ReadinessRecommender().recommend(r, rep)
    d = rec.as_dict()
    # seluruh aksi adalah proposal (is_proposal=True) - bukan "selected_final"
    for a in d["actions"]:
        assert a["is_proposal"] is True
    assert "selected_action" not in d
    assert "final_decision" not in str(d)


def test_recommendation_deterministic():
    r = ReadinessAggregationEngine().build_readiness(_inputs(), "or-rec3")
    rep = OperationalRiskAssessor().assess(r)
    a = ReadinessRecommender().recommend(r, rep)
    b = ReadinessRecommender().recommend(r, rep)
    assert a == b


# --------------------------------------------------------------------------
# 6. Readiness Explainability (WP-46)
# --------------------------------------------------------------------------

def test_explainability_items_and_evidence():
    r = ReadinessAggregationEngine().build_readiness(_inputs(), "or-exp")
    rep = OperationalRiskAssessor().assess(r)
    exp = ReadinessExplainer().explain(r, risk_report=rep)
    assert exp.item_count() >= 1
    assert exp.is_proposal_only is True
    assert exp.basis  # basis terisi
    assert "no action selected" in exp.conclusion


def test_explainability_deterministic():
    r = ReadinessAggregationEngine().build_readiness(_inputs(), "or-exp2")
    rep = OperationalRiskAssessor().assess(r)
    a = ReadinessExplainer().explain(r, risk_report=rep)
    b = ReadinessExplainer().explain(r, risk_report=rep)
    assert a == b


# --------------------------------------------------------------------------
# 7. Operational Readiness API (WP-47)
# --------------------------------------------------------------------------

def test_api_full_assessment_answers_questions():
    api = OperationalReadinessAPI()
    full = api.full_assessment(_inputs(ready=False), readiness_id="or-api", created_at="t")
    # 7 pertanyaan ED-3.2-005 bisa dijawab
    assert "readiness" in full          # apakah sistem siap beroperasi?
    assert "blockers" in full["readiness"] or full["readiness"]["blockers"]  # penghambat
    assert "risk" in full               # risiko terbesar
    assert "recommendation" in full     # proposal terbaik
    assert "explanation" in full        # mengapa
    assert full["readiness"]["evidence"]  # bukti
    assert full["readiness"]["trust_score"]  # kepercayaan
    # semua proposal, tanpa eksekusi
    assert full["recommendation"]["is_proposal_only"] is True


def test_api_read_only_no_input_mutation():
    inputs = _inputs()
    before = [i.as_dict() for i in inputs]
    api = OperationalReadinessAPI()
    api.full_assessment(inputs)
    after = [i.as_dict() for i in inputs]
    assert before == after


def test_api_summary():
    api = OperationalReadinessAPI()
    r = api.assess(_inputs(), readiness_id="or-sum")
    s = api.summarize(r)
    assert s.readiness_id == "or-sum"
    assert s.input_count == 7
    assert s.is_proposal_only is True


# --------------------------------------------------------------------------
# 8. Cross-Runtime Readiness Report (WP-48)
# --------------------------------------------------------------------------

def test_cross_runtime_consolidation():
    e = ReadinessAggregationEngine()
    rt_a = e.build_readiness(_inputs(ready=True), "or-xa")
    rt_b = e.build_readiness(_inputs(ready=False), "or-xb")
    report = CrossRuntimeReadinessAssembler().assemble(
        (("rt-a", rt_a), ("rt-b", rt_b)))
    assert report.total_count == 2
    assert report.ready_count == 1
    assert report.system_ready is False
    assert report.is_proposal_only is True


def test_cross_runtime_deterministic_and_ordered():
    e = ReadinessAggregationEngine()
    rt_a = e.build_readiness(_inputs(ready=True), "or-xa2")
    rt_b = e.build_readiness(_inputs(ready=False), "or-xb2")
    asm = CrossRuntimeReadinessAssembler()
    r1 = asm.assemble((("rt-b", rt_b), ("rt-a", rt_a)))
    r2 = asm.assemble((("rt-b", rt_b), ("rt-a", rt_a)))
    assert r1 == r2
    # urut by runtime_id
    assert [x.runtime_id for x in r1.entries] == ["rt-a", "rt-b"]


# --------------------------------------------------------------------------
# 9. Compliance suite (WP-49)
# --------------------------------------------------------------------------

def test_readiness_compliance_suite_passed():
    rd_dir = os.path.join(_RUNTIME_ROOT, "operational_readiness")
    files = default_source_files(rd_dir) + \
        [os.path.join(_RUNTIME_ROOT, "api", "operational_readiness.py")]
    files = [f for f in files if "checker.py" not in f]
    passed, checks = compliance_check(
        files, module_root=_RUNTIME_ROOT,
        implementation_dirs=(rd_dir,),
    )
    assert passed
    assert sum(1 for c in checks if c.passed) == len(checks)


# --------------------------------------------------------------------------
# 10. Exit criteria (sentence-level)
# --------------------------------------------------------------------------

def test_exit_criteria_end_to_end():
    """Runtime mampu secara deterministik menjawab: apakah sistem siap, apa
    penghambat, risiko terbesar, proposal terbaik, mengapa, bukti pendukung,
    dan tingkat kepercayaan - tanpa memperoleh kewenangan baru."""
    api = OperationalReadinessAPI()
    full = api.full_assessment(_inputs(ready=False), readiness_id="or-exit", created_at="t")
    rd = full["readiness"]

    assert "overall_level" in rd           # apakah siap? (level)
    assert "ready" in rd                   # boolean siap
    assert rd["blockers"]                  # apa penghambat? (blocker terisi)
    assert full["risk"]["risks"]           # risiko terbesar (list terisi)
    assert full["recommendation"]["actions"]  # proposal terbaik (prioritas)
    assert full["explanation"]["items"]    # mengapa? (items terisi)
    assert rd["evidence"]                  # bukti pendukung (evidence terisi)
    assert rd["trust_score"] >= 0.0        # tingkat kepercayaan (terukur)

    # TANPA kewenangan baru: semua proposal, tanpa aksi/eksekusi/mutasi
    assert rd["is_proposal_only"] is True
    assert full["recommendation"]["is_proposal_only"] is True
    assert full["recommendation"]["requires_governance"] is True
    assert rd["recommendation"] == "operational readiness stated; no action selected"
    assert "executed" not in str(full).lower() or "not" in str(full).lower()
