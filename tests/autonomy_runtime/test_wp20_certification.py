# IP-3.2-002 WP-20 - End-to-end Integration & Certification test
# Runtime Planning & Scheduling (AO-3.2-001 / ED-3.2-002)
#
# Definisi Done IP-3.2-002: Runtime mampu secara deterministik:
#   membangun rencana operasional,
#   menyusun urutan kerja,
#   menjelaskan alasan sequencing,
#   mengoptimalkan urutan berdasarkan observation,
#   mempertimbangkan dependency dan readiness,
# TANPA pernah melakukan aksi terhadap Runtime maupun Governance.
#
# Prinsip: Plan, never decide.

import pytest

from sam.autonomy_runtime.planning.models import (
    PlanStep,
    PlanningContext,
    PlanningMetadata,
    RuntimePlan,
)
from sam.autonomy_runtime.planning.engine import PlanningEngine
from sam.autonomy_runtime.planning.dependency_planner import DependencyPlanner
from sam.autonomy_runtime.planning.readiness_planner import ReadinessBasedPlanner
from sam.autonomy_runtime.planning.explainability import PlanningExplainer
from sam.autonomy_runtime.scheduling.engine import SchedulingEngine
from sam.autonomy_runtime.optimization.engine import PlanningOptimizer
from sam.autonomy_runtime.api.planning import PlanningAPI
from sam.autonomy_runtime.compliance.planning_checker import (
    compliance_check,
    default_source_files,
)

import os

_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_RUNTIME_ROOT = os.path.join(_ROOT, "src", "sam", "autonomy_runtime")


def _context() -> PlanningContext:
    return PlanningContext(
        source="observation",
        runtime_state_id="rt-1",
        overall_health="degraded",
        readiness_level="degraded",
        healthy_components=("kernel", "db"),
        degraded_components=("provider",),
        unavailable_components=("gateway",),
        dependency_edges=(("provider", "gateway"), ("kernel", "provider")),
    )


def _plan() -> RuntimePlan:
    return PlanningEngine().build_plan(_context(), created_at="t")


# --------------------------------------------------------------------------
# 1. Deterministic planning
# --------------------------------------------------------------------------

def test_planning_deterministic():
    p1 = PlanningEngine().build_plan(_context(), created_at="t1")
    p2 = PlanningEngine().build_plan(_context(), created_at="t2")
    assert p1.plan_id == p2.plan_id
    assert p1.as_dict()["steps"] == p2.as_dict()["steps"]


def test_plan_is_immutable():
    plan = _plan()
    with pytest.raises(Exception):
        plan.steps = ()
    with pytest.raises(Exception):
        plan.context.overall_health = "healthy"


def test_plan_proposal_only_no_execution_actions():
    plan = _plan()
    for step in plan.steps:
        assert step.action.startswith("plan_"), step.action


# --------------------------------------------------------------------------
# 2. Dependency-aware sequencing
# --------------------------------------------------------------------------

def test_dependency_planner_orders_prerequisite_first():
    ctx = _context()
    dp = DependencyPlanner(ctx)
    steps = (
        PlanStep(step_id="1", action="plan_x", target="gateway", priority=3),
        PlanStep(step_id="2", action="plan_x", target="provider", priority=2),
    )
    ordered = dp.dependency_ordered_steps(steps)
    targets = [s.target for s in ordered]
    assert targets.index("provider") < targets.index("gateway")


def test_dependency_planner_transitive():
    dp = DependencyPlanner(_context())
    assert dp.transitive_dependencies("gateway") == {"provider", "kernel"}


def test_dependency_cycle_detected():
    ctx = PlanningContext(source="c", dependency_edges=(("a", "b"), ("b", "a")))
    assert DependencyPlanner(ctx).has_cycle() is True


# --------------------------------------------------------------------------
# 3. Readiness-aware prioritization
# --------------------------------------------------------------------------

def test_readiness_based_prioritization():
    steps = _plan().steps
    result = ReadinessBasedPlanner(_context()).prioritize(steps)
    # db (healthy) / provider (degraded) harus sebelum gateway (unavailable)
    order = result.ordered_step_ids
    targets = {s.step_id: s.target for s in steps}
    by_target = [targets[i] for i in order]
    assert by_target.index("provider") < by_target.index("gateway")


def test_readiness_not_ready_targets():
    result = ReadinessBasedPlanner(_context()).prioritize(_plan().steps)
    assert "gateway" in result.not_ready_targets
    assert "provider" in result.ready_targets


# --------------------------------------------------------------------------
# 4. Optimize ordering (deterministic heuristic)
# --------------------------------------------------------------------------

def test_optimizer_reorders_and_explains():
    ctx = _context()
    steps = (
        PlanStep(step_id="1", action="plan_restore", target="gateway", priority=3),
        PlanStep(step_id="2", action="plan_optimize", target="provider", priority=2),
    )
    result = PlanningOptimizer(ctx).optimize(steps, plan_id="p")
    assert result.changed is True
    assert result.optimized_order[0] == "2"  # provider (prerequisite) dulu
    assert result.improvements


def test_optimizer_deterministic():
    ctx = _context()
    r1 = PlanningOptimizer(ctx).optimize(_plan().steps, plan_id="p")
    r2 = PlanningOptimizer(ctx).optimize(_plan().steps, plan_id="p")
    assert r1.optimized_order == r2.optimized_order
    assert r1.as_dict()["improvements"] == r2.as_dict()["improvements"]


# --------------------------------------------------------------------------
# 5. Scheduling proposal (no execution)
# --------------------------------------------------------------------------

def test_schedule_proposal_status_by_availability():
    plan = _plan()
    eng = SchedulingEngine()
    blocked = eng.build_schedule(plan, available=("kernel",))
    assert blocked.status == "blocked"
    ready = eng.build_schedule(plan, available=("kernel", "provider", "gateway"))
    assert ready.status == "ready"
    assert ready.total_ready == plan.step_count()


def test_schedule_is_proposal_not_action():
    plan = _plan()
    sched = SchedulingEngine().build_schedule(plan, available=("kernel", "provider"))
    for st in sched.steps:
        assert st.action.startswith("plan_")


def test_schedule_immutable():
    sched = SchedulingEngine().build_schedule(_plan(), available=("kernel",))
    with pytest.raises(Exception):
        sched.steps = ()


# --------------------------------------------------------------------------
# 6. Explainability (why)
# --------------------------------------------------------------------------

def test_explainability_explains_why():
    expl = PlanningExplainer().explain_plan(_plan())
    assert expl.plan_id == _plan().plan_id
    assert expl.conditions
    assert expl.is_proposal_only is True
    # alasan per step menyebut kondisi
    joined = " ".join(expl.priorities)
    assert "plan_" in joined or "propose" in joined


def test_explainability_multi_aligned():
    plan = _plan()
    expl = PlanningExplainer().explain_plan(plan)
    assert len(expl.priorities) == plan.step_count()


# --------------------------------------------------------------------------
# 7. Planning API facade (read-only)
# --------------------------------------------------------------------------

def test_planning_api_full_pipeline_readonly():
    api = PlanningAPI()
    plan, sched, opt = api.full_pipeline(_context(), available=("kernel", "provider"))
    assert plan.plan_id
    assert sched.schedule_id
    assert opt is not None


def test_planning_api_summary_shape():
    api = PlanningAPI()
    plan, sched, opt = api.full_pipeline(_context(), available=("kernel", "provider"))
    summary = api.summarize(plan, sched, opt)
    d = summary.as_dict()
    for key in (
        "plan_id", "step_count", "plan_state", "schedule_status",
        "ready_steps", "blocked_steps", "optimized",
        "plan_ordered_ids", "optimized_ordered_ids",
    ):
        assert key in d


# --------------------------------------------------------------------------
# 8. Read-only: no runtime/plan mutation across all planning calls
# --------------------------------------------------------------------------

def test_planning_pipeline_does_not_mutate_runtime():
    ctx = _context()
    before = ctx.as_dict()
    api = PlanningAPI()
    api.plan(ctx, created_at="t")
    api.schedule(_plan(), available=("kernel",))
    api.optimize(ctx, _plan().steps)
    api.full_pipeline(ctx, available=("kernel",))
    assert ctx.as_dict() == before


# --------------------------------------------------------------------------
# 9. Compliance suite "planning without authority"
# --------------------------------------------------------------------------

def test_planning_compliance_suite_passed():
    impl_dirs = (
        os.path.join(_RUNTIME_ROOT, "planning"),
        os.path.join(_RUNTIME_ROOT, "scheduling"),
        os.path.join(_RUNTIME_ROOT, "optimization"),
    )
    files = []
    for d in impl_dirs:
        if os.path.isdir(d):
            files += default_source_files(d)
    files += [
        os.path.join(_RUNTIME_ROOT, "api", "planning.py"),
    ]
    # checker yang memuat pola terlarang literal di-exclude (pola IP-3.2-001)
    files = [f for f in files if "checker.py" not in f]
    passed, checks = compliance_check(
        files, module_root=_RUNTIME_ROOT, implementation_dirs=impl_dirs
    )
    assert passed
    assert sum(1 for c in checks if c.passed) == len(checks)


# --------------------------------------------------------------------------
# 10. Exit criteria: exit criteria sentence-level
# --------------------------------------------------------------------------

def test_exit_criteria_end_to_end():
    """Runtime mampu: plan, urutkan kerja, jelaskan alasan, optimasi,
    pertimbangkan dependency & readiness - tanpa aksi terhadap Runtime."""
    ctx = _context()
    api = PlanningAPI()
    plan = api.plan(ctx, created_at="t")
    # membangun rencana operasional + urutan kerja
    assert plan.step_count() >= 2
    # jelaskan alasan sequencing (dependency)
    one = next(s for s in plan.steps if s.target == "gateway")
    diff = next(s for s in plan.steps if s.target == "provider")
    assert "gateway" in diff.prerequisite_ids or "provider" in one.prerequisite_ids
    # optimize urutan berdasarkan observation
    opt = api.optimize(ctx, plan.steps, plan_id=plan.plan_id)
    assert opt is not None
    # tanpa aksi: semua action bermula plan_
    assert all(s.action.startswith("plan_") for s in plan.steps)
