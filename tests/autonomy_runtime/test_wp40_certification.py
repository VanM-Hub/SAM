# IP-3.2-004 WP-40 - End-to-end Integration & Certification test
# Runtime Coordination & Lifecycle Management (AO-3.2-001 / ED-3.2-004)
#
# Definisi Done IP-3.2-004: Runtime mampu secara deterministik, sebanyak
# beberapa runtime bekerja sebagai SISTEM TUNGGAL (collective coordination),
# dengan memahami:
#   topology runtime, graph koordinasi, dependency koordinasi,
#   state lifecycle, analisis lifecycle, readiness lifecycle,
#   proposal transisi lifecycle,
# TANPA pernah melakukan orchestration, dispatch, start/stop/restart,
# approval, maupun mutasi governance, atau mutasi lifecycle aktual.
#
# Prinsip: Coordinate by model, never by orchestration.
#         Lifecycle proposal, never lifecycle mutation.

import os

import pytest

from sam.autonomy_runtime.coordination.models import (
    RuntimeNode,
    RuntimeTopology,
)
from sam.autonomy_runtime.coordination.engine import (
    CoordinationProposal,
    RuntimeCoordinationEngine,
)
from sam.autonomy_runtime.coordination.dependency import DependencyCoordinator
from sam.autonomy_runtime.coordination.explainability import CoordinationExplainer
from sam.autonomy_runtime.lifecycle.models import (
    LifecycleStage,
    LifecycleState,
    LifecycleTransition,
)
from sam.autonomy_runtime.lifecycle.analyzer import LifecycleAnalyzer
from sam.autonomy_runtime.lifecycle.planner import LifecyclePlanner
from sam.autonomy_runtime.api.coordination import CoordinationAPI
from sam.autonomy_runtime.compliance.coordination_checker import (
    compliance_check,
    default_source_files,
)

_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_RUNTIME_ROOT = os.path.join(_ROOT, "src", "sam", "autonomy_runtime")


def _topology() -> RuntimeTopology:
    return RuntimeTopology(
        topology_id="topo-cert-1",
        created_at="t",
        nodes=(
            RuntimeNode(runtime_id="rt-a", role="coordinator", readiness="healthy"),
            RuntimeNode(runtime_id="rt-b", role="worker", readiness="healthy"),
            RuntimeNode(runtime_id="rt-c", role="worker", readiness="unavailable"),
        ),
        edges=(("rt-a", "rt-b"), ("rt-b", "rt-c")),
    )


def _states():
    return (
        LifecycleState(runtime_id="rt-a", stage=LifecycleStage.RUNNING,
                       observed_at="t", readiness="healthy", health_trend="stable"),
        LifecycleState(runtime_id="rt-b", stage=LifecycleStage.RUNNING,
                       observed_at="t", readiness="healthy", health_trend="stable"),
        LifecycleState(runtime_id="rt-c", stage=LifecycleStage.PROVISIONING,
                       observed_at="t", readiness="degraded", health_trend="improving"),
    )


# --------------------------------------------------------------------------
# 1. Runtime topology (WP-31)
# --------------------------------------------------------------------------

def test_topology_model():
    t = _topology()
    assert t.node_count() == 3
    assert t.edge_count() == 2
    assert t.get_node("rt-a").role == "coordinator"
    assert t.get_node("missing") is None
    assert t.runtime_ids() == ("rt-a", "rt-b", "rt-c")


def test_topology_immutable():
    t = _topology()
    with pytest.raises(Exception):
        t.nodes = ()
    with pytest.raises(Exception):
        t.edges = ()
    assert t.get_node("rt-b").is_available() is True   # healthy
    assert t.get_node("rt-c").is_available() is False  # unavailable


# --------------------------------------------------------------------------
# 2. Coordination engine (WP-32)
# --------------------------------------------------------------------------

def test_coordination_graph_edges():
    g = RuntimeCoordinationEngine().build_graph(_topology())
    assert g.edge_count() == 2
    assert g.dependencies_of("rt-b") == ("rt-a",)
    assert g.dependencies_of("rt-c") == ("rt-b",)
    assert g.dependents_of("rt-a") == ("rt-b",)


def test_coordination_proposal_proposal_only():
    p = RuntimeCoordinationEngine().build_proposal(_topology(), "align")
    assert isinstance(p, CoordinationProposal)
    assert p.is_proposal_only is True
    assert p.step_count() == 3
    # semua aksi ber-label proposal coordinate_
    for rid, action in p.steps:
        assert action.startswith("coordinate_")


def test_coordination_deterministic():
    eng = RuntimeCoordinationEngine()
    p1 = eng.build_proposal(_topology(), "align")
    p2 = eng.build_proposal(_topology(), "align")
    assert p1 == p2
    assert p1.proposal_id == p2.proposal_id


# --------------------------------------------------------------------------
# 3. Dependency coordination (WP-33)
# --------------------------------------------------------------------------

def test_dependency_coordination_plan():
    t = _topology()
    g = RuntimeCoordinationEngine().build_graph(t)
    plan = DependencyCoordinator().build_plan(t, g)
    assert plan.is_proposal_only is True
    assert plan.ordered_count() == 3
    # pastikan ordered mempertahankan dependensi: rt-a sebelum rt-b sebelum rt-c
    assert plan.ordered.index("rt-a") < plan.ordered.index("rt-b")
    assert plan.ordered.index("rt-b") < plan.ordered.index("rt-c")


def test_dependency_blocker_on_unavailable_prereq():
    t = RuntimeTopology(
        topology_id="topo-block",
        created_at="t",
        nodes=(
            RuntimeNode(runtime_id="rt-a", role="coordinator", readiness="healthy"),
            RuntimeNode(runtime_id="rt-b", role="worker", readiness="unavailable"),
            RuntimeNode(runtime_id="rt-c", role="worker", readiness="healthy"),
        ),
        edges=(("rt-a", "rt-b"), ("rt-b", "rt-c")),
    )
    g = RuntimeCoordinationEngine().build_graph(t)
    plan = DependencyCoordinator().build_plan(t, g)
    assert plan.is_blocked() is True
    assert any(b.missing_prereq == "rt-b" for b in plan.blockers)


# --------------------------------------------------------------------------
# 4. Lifecycle state model (WP-34)
# --------------------------------------------------------------------------

def test_lifecycle_stage_constants():
    assert LifecycleStage.RUNNING == "running"
    assert LifecycleStage.PROVISIONING == "provisioning"
    assert LifecycleStage.STOPPED == "stopped"


def test_lifecycle_transition_is_proposal():
    tr = LifecycleTransition(runtime_id="rt-a", from_stage="running",
                             to_stage="draining", reason="maintenance")
    assert tr.is_proposal is True


# --------------------------------------------------------------------------
# 5. Lifecycle analyzer (WP-35)
# --------------------------------------------------------------------------

def test_lifecycle_analyzer_degrading():
    st = LifecycleState(runtime_id="rt-a", stage=LifecycleStage.DEGRADING,
                        observed_at="t", readiness="degraded")
    a = LifecycleAnalyzer().analyze(st)
    assert a.readiness == "degraded"
    assert a.issue_count() >= 1
    assert a.is_healthy() is False
    assert a.suggestion.startswith("proposal:")


def test_lifecycle_analyzer_healthy_running():
    st = LifecycleState(runtime_id="rt-a", stage=LifecycleStage.RUNNING,
                        observed_at="t", readiness="healthy")
    a = LifecycleAnalyzer().analyze(st)
    assert a.is_healthy() is True
    assert a.issue_count() == 0


def test_lifecycle_analyzer_deterministic():
    st = LifecycleState(runtime_id="rt-a", stage=LifecycleStage.RUNNING,
                        observed_at="t", readiness="healthy")
    a1 = LifecycleAnalyzer().analyze(st)
    a2 = LifecycleAnalyzer().analyze(st)
    assert a1 == a2


# --------------------------------------------------------------------------
# 6. Lifecycle planner (WP-36)
# --------------------------------------------------------------------------

def test_lifecycle_plan_proposal_transitions():
    plan = LifecyclePlanner().plan(_states())
    assert plan.is_proposal_only is True
    assert plan.transition_count() >= 1
    # semua transisi merupakan proposal
    for tr in plan.transitions:
        assert tr.is_proposal is True


def test_lifecycle_readiness_deterministic():
    p1 = LifecyclePlanner().plan(_states(), "rt-a")
    p2 = LifecyclePlanner().plan(_states(), "rt-a")
    assert p1 == p2
    assert p1.health_trend in ("improving", "stable", "declining")


def test_lifecycle_running_to_stopping_allowed():
    # running -> stopping adalah transisi yang diusulkan (proposal, bukan eksekusi)
    plan = LifecyclePlanner().plan(_states(), "rt-a")
    tos = {tr.to_stage for tr in plan.transitions}
    assert "stopping" in tos


# --------------------------------------------------------------------------
# 7. Coordination API facade (WP-37)
# --------------------------------------------------------------------------

def test_coordination_api_readonly():
    api = CoordinationAPI()
    topo = api.topologize(_topology().nodes, _topology().edges, created_at="t")
    assert topo.node_count() == 3
    prop = api.coordinate(topo)
    assert prop.is_proposal_only is True
    dep = api.dependency_plan(topo)
    assert dep.is_proposal_only is True
    lp = api.lifecycle_plan(_states(), "rt-a")
    assert lp.is_proposal_only is True


def test_coordination_api_no_mutation_of_input():
    topo = _topology()
    before = topo.as_dict()
    api = CoordinationAPI()
    api.coordinate(topo)
    api.dependency_plan(topo)
    assert topo.as_dict() == before


# --------------------------------------------------------------------------
# 8. Coordination explainability (WP-38)
# --------------------------------------------------------------------------

def test_coordination_explainability():
    t = _topology()
    g = RuntimeCoordinationEngine().build_graph(t)
    p = RuntimeCoordinationEngine().build_proposal(t, "align")
    dep = DependencyCoordinator().build_plan(t, g)
    expl = CoordinationExplainer().explain_coordination(t, p, dep)
    assert expl.is_proposal_only is True
    assert expl.coordination_count() >= 3


def test_lifecycle_explainability():
    plan = LifecyclePlanner().plan(_states(), "rt-b")
    expl = CoordinationExplainer().explain_lifecycle(plan)
    assert expl.lifecycle_count() >= 1
    assert expl.is_proposal_only is True


# --------------------------------------------------------------------------
# 9. Compliance suite (WP-39)
# --------------------------------------------------------------------------

def test_coordination_compliance_suite_passed():
    coordination_dir = os.path.join(_RUNTIME_ROOT, "coordination")
    lifecycle_dir = os.path.join(_RUNTIME_ROOT, "lifecycle")
    files = default_source_files(coordination_dir) + \
        default_source_files(lifecycle_dir) + \
        [os.path.join(_RUNTIME_ROOT, "api", "coordination.py")]
    files = [f for f in files if "checker.py" not in f]
    passed, checks = compliance_check(
        files, module_root=_RUNTIME_ROOT,
        implementation_dirs=(coordination_dir, lifecycle_dir),
    )
    assert passed
    assert sum(1 for c in checks if c.passed) == len(checks)


# --------------------------------------------------------------------------
# 10. Exit criteria (sentence-level)
# --------------------------------------------------------------------------

def test_exit_criteria_end_to_end():
    """Runtime mampu (sebagai sistem kolektif) secara deterministik memahami
    topology, graph koordinasi, dependency koordinasi, kondisi & readiness
    lifecycle, dan menyusun proposal transisi - tanpa orchestration atau
    mutasi lifecycle."""
    api = CoordinationAPI()
    topo = api.topologize(_topology().nodes, _topology().edges, created_at="t")
    prop = api.coordinate(topo)
    dep = api.dependency_plan(topo)
    lp = api.lifecycle_plan(_states(), "rt-a")

    assert prop.step_count() >= 1      # memahami topology & proposal koordinasi
    assert dep.ordered_count() >= 1    # memahami dependency koordinasi
    assert lp.transition_count() >= 1  # memahami lifecycle & proposal transisi

    # tanpa orchestration / mutasi
    assert prop.is_proposal_only is True
    assert dep.is_proposal_only is True
    assert lp.is_proposal_only is True
    for rid, action in prop.steps:
        assert action.startswith("coordinate_")  # proposal, bukan dispatch
    for tr in lp.transitions:
        assert tr.is_proposal is True            # proposal, bukan mutasi
