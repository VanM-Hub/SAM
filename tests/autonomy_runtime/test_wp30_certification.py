# IP-3.2-003 WP-30 - End-to-end Integration & Certification test
# Runtime Recovery & Self-Healing Strategy (AO-3.2-001 / ED-3.2-003)
#
# Definisi Done IP-3.2-003: Runtime mampu secara deterministik:
#   menganalisis penyebab kegagalan,
#   memilih strategi recovery yang sesuai,
#   menyusun proposal self-healing,
#   menjelaskan alasan strategi tersebut,
#   memperkirakan dampak recovery,
#   menghasilkan rekomendasi berbasis evidence dan trust,
# TANPA pernah melakukan aksi recovery terhadap sistem.
#
# Prinsip: Recover by strategy, never by authority.

import os

import pytest

from sam.autonomy_runtime.recovery.models import (
    RecoveryContext,
    RecoveryMetadata,
)
from sam.autonomy_runtime.recovery.failure_analysis import FailureAnalyzer
from sam.autonomy_runtime.recovery.strategy import RecoveryStrategyEngine
from sam.autonomy_runtime.recovery.impact import RecoveryImpactAnalyzer
from sam.autonomy_runtime.recovery.recommendation import RecoveryRecommender
from sam.autonomy_runtime.recovery.explainability import RecoveryExplainer
from sam.autonomy_runtime.healing.planner import SelfHealingPlanner
from sam.autonomy_runtime.api.recovery import RecoveryAPI
from sam.autonomy_runtime.compliance.recovery_checker import (
    compliance_check,
    default_source_files,
)
from sam.autonomy_runtime.diagnostics.failure import (
    FailureClassification,
    FailureClass,
)

_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_RUNTIME_ROOT = os.path.join(_ROOT, "src", "sam", "autonomy_runtime")


def _context() -> RecoveryContext:
    return RecoveryContext(
        state_id="rt-7",
        overall_health="unhealthy",
        readiness_level="degraded",
        failed_components=("gateway",),
        degraded_components=("provider",),
        healthy_components=("kernel", "db"),
        dependency_edges=(("kernel", "provider"), ("provider", "gateway")),
    )


def _classification() -> FailureClassification:
    return FailureClassification(
        state_id="rt-7",
        observed_at="t",
        classifications={
            "gateway": FailureClass.CONNECTIVITY,
            "provider": FailureClass.DEPENDENCY,
        },
    )


def _analysis():
    return FailureAnalyzer().analyze(
        _classification(), _context(), created_at="t"
    )


# --------------------------------------------------------------------------
# 1. Deterministic failure analysis
# --------------------------------------------------------------------------

def test_failure_analysis_deterministic():
    a1 = FailureAnalyzer().analyze(_classification(), _context(), created_at="t1")
    a2 = FailureAnalyzer().analyze(_classification(), _context(), created_at="t2")
    assert a1.analysis_id == a2.analysis_id
    assert a1.as_dict() == a2.as_dict()


def test_failure_analysis_identifies_root():
    a = _analysis()
    # provider (degraded) adalah prereq gateway -> root candidate
    assert "provider" in a.root_candidates
    assert a.overall_severity >= 2


def test_recovery_context_immutable():
    ctx = _context()
    with pytest.raises(Exception):
        ctx.state_id = "x"
    with pytest.raises(Exception):
        ctx.failed_components = ()
    assert ctx.failed_components_count() == 1


# --------------------------------------------------------------------------
# 2. Recovery strategy selection
# --------------------------------------------------------------------------

def test_strategy_by_evidence():
    a = _analysis()
    strat = RecoveryStrategyEngine().build_strategy(a, _context(), created_at="t")
    # gateway (connectivity) -> replicate; provider (dependency) -> restore
    actions = {s.target: s.action for s in strat.actions}
    assert "gateway" in actions
    assert "provider" in actions
    assert strat.evidence_basis


def test_strategy_deterministic_and_proposal():
    s1 = RecoveryStrategyEngine().build_strategy(_analysis(), _context(), created_at="t1")
    s2 = RecoveryStrategyEngine().build_strategy(_analysis(), _context(), created_at="t2")
    assert s1 == s2
    assert s1.strategy_id == s2.strategy_id
    assert s1.is_proposal_only()


def test_strategy_immutable():
    s = RecoveryStrategyEngine().build_strategy(_analysis(), _context())
    with pytest.raises(Exception):
        s.actions = ()


# --------------------------------------------------------------------------
# 3. Self-healing proposal (dependency-aware)
# --------------------------------------------------------------------------

def test_self_healing_plan_dependency_order():
    strat = RecoveryStrategyEngine().build_strategy(_analysis(), _context())
    plan = SelfHealingPlanner().build_plan(strat, _context())
    # provider (prereq gateway) harus diusulkan sebelum gateway
    targets = [s.target for s in plan.steps]
    assert targets.index("provider") < targets.index("gateway")
    assert plan.is_proposal_only()


def test_self_healing_plan_deterministic():
    strat = RecoveryStrategyEngine().build_strategy(_analysis(), _context())
    p1 = SelfHealingPlanner().build_plan(strat, _context())
    p2 = SelfHealingPlanner().build_plan(strat, _context())
    assert p1 == p2


# --------------------------------------------------------------------------
# 4. Recovery impact estimation
# --------------------------------------------------------------------------

def test_impact_report_estimates_risk():
    strat = RecoveryStrategyEngine().build_strategy(_analysis(), _context())
    plan = SelfHealingPlanner().build_plan(strat, _context())
    impact = RecoveryImpactAnalyzer().analyze(strat, plan, _context())
    assert impact.overall_risk in ("low", "medium", "high")
    assert impact.item_count() >= 1
    assert "simulated" in impact.summary


def test_impact_deterministic():
    strat = RecoveryStrategyEngine().build_strategy(_analysis(), _context())
    plan = SelfHealingPlanner().build_plan(strat, _context())
    r1 = RecoveryImpactAnalyzer().analyze(strat, plan, _context())
    r2 = RecoveryImpactAnalyzer().analyze(strat, plan, _context())
    assert r1 == r2


# --------------------------------------------------------------------------
# 5. Recovery recommendation (evidence & trust)
# --------------------------------------------------------------------------

def test_recommendation_prefers_higher_trust():
    a = _analysis()
    ctx = _context()
    strat = RecoveryStrategyEngine().build_strategy(a, ctx)
    rec = RecoveryRecommender().recommend(a, ctx, (strat,))
    assert rec.preferred == strat.strategy_id
    assert rec.option_count() >= 1
    if rec.options:
        top = rec.options[0]
        assert top.trust_score >= 0


def test_recommendation_deterministic():
    a = _analysis()
    ctx = _context()
    strat = RecoveryStrategyEngine().build_strategy(a, ctx)
    r1 = RecoveryRecommender().recommend(a, ctx, (strat,))
    r2 = RecoveryRecommender().recommend(a, ctx, (strat,))
    assert r1 == r2


# --------------------------------------------------------------------------
# 6. Recovery explainability
# --------------------------------------------------------------------------

def test_explainability_explains_strategy():
    a = _analysis()
    ctx = _context()
    strat = RecoveryStrategyEngine().build_strategy(a, ctx)
    plan = SelfHealingPlanner().build_plan(strat, ctx)
    impact = RecoveryImpactAnalyzer().analyze(strat, plan, ctx)
    rec = RecoveryRecommender().recommend(a, ctx, (strat,))
    expl = RecoveryExplainer().explain(a, strat, rec, impact, ctx)
    assert expl.is_proposal_only is True
    assert expl.preferred_strategy == strat.strategy_id
    assert expl.item_count() >= 1


# --------------------------------------------------------------------------
# 7. Recovery API facade (read-only)
# --------------------------------------------------------------------------

def test_recovery_api_pipeline_readonly():
    api = RecoveryAPI()
    ana = api.analyze(_classification(), _context(), created_at="t")
    strat, plan, impact = api.recover_plan(ana, _context(), created_at="t")
    rec = api.recommend(ana, _context(), (strat,))
    assert ana.failure_count() >= 1
    assert plan.step_count() >= 1
    assert impact.overall_risk
    assert rec.preferred


def test_recovery_api_no_mutation_of_input():
    ctx = _context()
    before = ctx.as_dict()
    api = RecoveryAPI()
    ana = api.analyze(_classification(), ctx, created_at="t")
    strat, plan, impact = api.recover_plan(ana, ctx, created_at="t")
    api.recommend(ana, ctx, (strat,))
    assert ctx.as_dict() == before


# --------------------------------------------------------------------------
# 8. Compliance suite "recovery without execution"
# --------------------------------------------------------------------------

def test_recovery_compliance_suite_passed():
    recovery_dir = os.path.join(_RUNTIME_ROOT, "recovery")
    healing_dir = os.path.join(_RUNTIME_ROOT, "healing")
    files = default_source_files(recovery_dir) + default_source_files(healing_dir)
    files += [os.path.join(_RUNTIME_ROOT, "api", "recovery.py")]
    files = [f for f in files if "_check" not in f and "checker.py" not in f]
    passed, checks = compliance_check(
        files, module_root=_RUNTIME_ROOT,
        implementation_dirs=(recovery_dir, healing_dir),
    )
    assert passed
    assert sum(1 for c in checks if c.passed) == len(checks)


# --------------------------------------------------------------------------
# 9. Exit criteria (sentence-level)
# --------------------------------------------------------------------------

def test_exit_criteria_end_to_end():
    """Runtime mampu: menganalisis kegagalan, pilih strategi, usul self-heal,
    jelaskan alasan, perkirakan dampak, rekomendasi evidence+trust - tanpa aksi."""
    ctx = _context()
    api = RecoveryAPI()
    ana = api.analyze(_classification(), ctx, created_at="t")
    strat, plan, impact = api.recover_plan(ana, ctx, created_at="t")
    rec = api.recommend(ana, ctx, (strat,))
    expl = RecoveryExplainer().explain(ana, strat, rec, impact, ctx)

    assert ana.failure_count() >= 1          # analisis penyebab kegagalan
    assert strat.is_proposal_only()          # pilih strategi (proposal)
    assert plan.is_proposal_only()           # proposal self-healing
    assert expl.item_count() >= 1            # jelaskan alasan strategi
    assert impact.item_count() >= 1          # perkirakan dampak
    assert rec.option_count() >= 1           # rekomendasi evidence+trust

    # tanpa aksi: seluruh label adalah proposal
    for step in plan.steps:
        assert step.action.startswith("recover_") or step.action.startswith("heal_")


# --------------------------------------------------------------------------
# 10. RecoveryMetadata phase guard
# --------------------------------------------------------------------------

def test_recovery_metadata_is_strategic():
    md = RecoveryMetadata(recovery_id="r1", created_at="t", basis="gateway down")
    assert md.phase == "strategic"
    assert md.deterministic is True
    assert md.engine == "runtime_recovery"
