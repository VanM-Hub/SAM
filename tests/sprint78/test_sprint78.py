import os, sys
import pytest
from dataclasses import FrozenInstanceError
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_goal import GoalType, OperationalGoal
from sam.operational_brain.operational_candidate import OperationalCandidate
from sam.operational_brain.operational_builder import OperationalBuilder
from sam.operational_brain.operational_planner import PlanEntry, PriorityTier, OperationalPlanner
from sam.operational_brain.operational_scheduler import (
    ScheduledItem, Schedule, OperationalScheduler,
)
from sam.operational_brain.dependency_resolver import (
    DependencyNode, DependencyGraph, CycleError, DependencyResolver,
)
from sam.operational_brain.conversation_scheduling import ConversationScheduling
from sam.operational_brain.dashboard_scheduling import DashboardScheduling, SchedulingCard


# --- Helpers ---

def _ctx(env="normal", decisions=0, missions=None):
    return OperationalContext(
        context_id="sc_ctx", timestamp=200.0, source="manual",
        environment=env, active_missions=missions or [],
        pending_decisions=decisions, pending_approvals=0, available_resources=1,
    )


def _plan_entries(ctx=None):
    if ctx is None:
        ctx = _ctx("busy", decisions=2, missions=["m1"])
    builder = OperationalBuilder()
    cands = builder.build(ctx)
    planner = OperationalPlanner()
    return planner.plan(cands, ctx)


# --- DependencyResolver ---

def test_resolver_add_remove_goal():
    r = DependencyResolver()
    g = OperationalGoal(goal_id="g1", goal_type=GoalType.MISSION, title="T1", description="D", priority=1)
    r.add_goal(g)
    assert "g1" in r.goal_ids
    assert r.has_dependencies("g1") is False
    r.remove_goal("g1")
    assert "g1" not in r.goal_ids


def test_resolver_dependencies():
    r = DependencyResolver()
    g1 = OperationalGoal(goal_id="g1", goal_type=GoalType.MISSION, title="T1", description="D", priority=1)
    g2 = OperationalGoal(goal_id="g2", goal_type=GoalType.MISSION, title="T2", description="D", priority=2, dependencies=["g1"])
    r.add_goal(g1)
    r.add_goal(g2)
    assert r.dependencies_of("g2") == ["g1"]
    assert r.dependents_of("g1") == ["g2"]


def test_resolver_no_cycles():
    r = DependencyResolver()
    for i in range(5):
        deps = [f"g{j}" for j in range(i)]
        g = OperationalGoal(goal_id=f"g{i}", goal_type=GoalType.MISSION, title=f"T{i}", description="D", priority=i, dependencies=deps)
        r.add_goal(g)
    cycles = r.find_cycles()
    assert not cycles
    topo = r.topological_sort()
    assert len(topo) == 5
    assert topo[0] == "g0"


def test_resolver_cycle_detection():
    r = DependencyResolver()
    g1 = OperationalGoal(goal_id="c1", goal_type=GoalType.MISSION, title="C1", description="D", priority=1, dependencies=["c2"])
    g2 = OperationalGoal(goal_id="c2", goal_type=GoalType.MISSION, title="C2", description="D", priority=2, dependencies=["c3"])
    g3 = OperationalGoal(goal_id="c3", goal_type=GoalType.MISSION, title="C3", description="D", priority=3, dependencies=["c1"])
    r.add_goal(g1)
    r.add_goal(g2)
    r.add_goal(g3)
    cycles = r.find_cycles()
    assert cycles
    with pytest.raises(CycleError):
        r.topological_sort()


def test_resolver_build_graph():
    r = DependencyResolver()
    g1 = OperationalGoal(goal_id="a", goal_type=GoalType.MISSION, title="Alpha", description="D", priority=1)
    g2 = OperationalGoal(goal_id="b", goal_type=GoalType.MISSION, title="Beta", description="D", priority=2, dependencies=["a"])
    r.add_goal(g1)
    r.add_goal(g2)
    dg = r.build_graph()
    assert isinstance(dg, DependencyGraph)
    assert dg.has_cycles is False
    assert len(dg.nodes) == 2


def test_resolver_clear():
    r = DependencyResolver()
    g = OperationalGoal(goal_id="x", goal_type=GoalType.MISSION, title="X", description="D", priority=1)
    r.add_goal(g)
    r.clear()
    assert "x" not in r.goal_ids


def test_dependency_node_frozen():
    n = DependencyNode(goal_id="id1", title="T1", depends_on=("a", "b"), depended_by=("c",))
    with pytest.raises(FrozenInstanceError):
        n.title = "X"


def test_dependency_graph_frozen():
    dg = DependencyGraph(nodes=(DependencyNode(goal_id="a", title="A"),))
    with pytest.raises(FrozenInstanceError):
        dg.nodes = ()


# --- Scheduler ---

def test_scheduler_basic():
    entries = _plan_entries()
    sched = OperationalScheduler()
    ctx = _ctx()
    items = sched.schedule_from_plan(entries, ctx)
    assert isinstance(items, list)
    assert len(items) >= 1
    for item in items:
        assert isinstance(item, ScheduledItem)
        assert item.position >= 1


def test_scheduler_frozen():
    entries = _plan_entries()
    sched = OperationalScheduler()
    items = sched.schedule_from_plan(entries, _ctx())
    if items:
        with pytest.raises(FrozenInstanceError):
            items[0].position = 99


def test_schedule_frozen():
    s = Schedule(items=[], total_items=3, estimated_duration=10.0)
    with pytest.raises(FrozenInstanceError):
        s.total_items = 5


def test_scheduler_summary():
    entries = _plan_entries()
    sched = OperationalScheduler()
    sched.schedule_from_plan(entries, _ctx())
    s = sched.summary()
    assert s["total_items"] >= 1
    assert s["estimated_duration"] > 0


def test_scheduler_dict():
    entries = _plan_entries()
    sched = OperationalScheduler()
    sched.schedule_from_plan(entries, _ctx())
    d = sched.schedule_dict()
    assert "items" in d
    assert d["total_items"] >= 1


def test_scheduler_clear():
    entries = _plan_entries()
    sched = OperationalScheduler()
    sched.schedule_from_plan(entries, _ctx())
    assert sched.schedule
    sched.clear()
    assert not sched.schedule


def test_scheduler_empty_plan():
    sched = OperationalScheduler()
    items = sched.schedule_from_plan([], _ctx())
    assert items == []
    s = sched.summary()
    assert s["total_items"] == 0


def test_scheduler_properties():
    entries = _plan_entries()
    sched = OperationalScheduler()
    sched.schedule_from_plan(entries, _ctx())
    prop = sched.schedule
    dg = sched.dependency_graph
    assert isinstance(prop, list)
    assert isinstance(dg, DependencyGraph)


# --- ConversationScheduling ---

def test_conversation_scheduling_count():
    sched = OperationalScheduler()
    conv = ConversationScheduling(sched)
    assert conv.query_count == 7


def test_conversation_scheduling_summary():
    entries = _plan_entries()
    sched = OperationalScheduler()
    sched.schedule_from_plan(entries, _ctx())
    conv = ConversationScheduling(sched)
    d = conv.query_schedule_summary()
    assert "total_items" in d


def test_conversation_scheduling_full_schedule():
    entries = _plan_entries()
    sched = OperationalScheduler()
    sched.schedule_from_plan(entries, _ctx())
    conv = ConversationScheduling(sched)
    items = conv.query_full_schedule()
    assert isinstance(items, list)
    for item in items:
        assert "schedule_id" in item
        assert "position" in item


def test_conversation_scheduling_topology():
    entries = _plan_entries()
    sched = OperationalScheduler()
    sched.schedule_from_plan(entries, _ctx())
    conv = ConversationScheduling(sched)
    topo = conv.query_topology()
    assert isinstance(topo, list)


def test_conversation_scheduling_dep_graph():
    entries = _plan_entries()
    sched = OperationalScheduler()
    sched.schedule_from_plan(entries, _ctx())
    conv = ConversationScheduling(sched)
    dg = conv.query_dependency_graph()
    assert "nodes" in dg
    assert "topological_order" in dg


def test_conversation_scheduling_blocked():
    sched = OperationalScheduler()
    conv = ConversationScheduling(sched)
    res = conv.query_schedule_conflicts()
    assert "conflict_count" in res


# --- DashboardScheduling ---

def test_dashboard_scheduling_card_count():
    sched = OperationalScheduler()
    dash = DashboardScheduling(sched)
    cards = dash.get_cards()
    assert len(cards) == dash.card_count == 5
    for card in cards:
        assert isinstance(card, SchedulingCard)


def test_dashboard_scheduling_card_types():
    sched = OperationalScheduler()
    dash = DashboardScheduling(sched)
    cards = dash.get_cards()
    types = [c.card_type for c in cards]
    assert "overview" in types
    assert "tiers" in types
    assert "blocked" in types
    assert "duration" in types
    assert "sequence" in types


def test_dashboard_scheduling_with_data():
    entries = _plan_entries()
    sched = OperationalScheduler()
    sched.schedule_from_plan(entries, _ctx())
    dash = DashboardScheduling(sched)
    cards = dash.get_cards()
    assert len(cards) == 5
    overview = [c for c in cards if c.card_type == "overview"][0]
    assert overview.value["total_items"] >= 1


# --- Parametrized ---

@pytest.mark.parametrize("i", list(range(1, 21)))
def test_scheduler_various_contexts(i):
    ctx = _ctx(env=["normal", "busy", "idle", "emergency"][i % 4],
               decisions=i % 3, missions=[f"m{j}" for j in range(i % 4)])
    builder = OperationalBuilder()
    cands = builder.build(ctx)
    planner = OperationalPlanner()
    entries = planner.plan(cands, ctx)
    sched = OperationalScheduler()
    items = sched.schedule_from_plan(entries, ctx)
    assert isinstance(items, list)
    for item in items:
        assert isinstance(item.entry, PlanEntry)
        assert 0.0 <= item.entry.priority_score <= 1.0


@pytest.mark.parametrize("n", [1, 2, 5, 10])
def test_scheduler_dependency_ordering(n):
    r = DependencyResolver()
    for i in range(n):
        deps = [f"g{j}" for j in range(i)]
        g = OperationalGoal(goal_id=f"g{i}", goal_type=GoalType.MISSION, title=f"T{i}", description="D", priority=i, dependencies=deps)
        r.add_goal(g)
    topo = r.topological_sort()
    assert len(topo) == n
    if n > 1:
        assert topo[0] == "g0"


@pytest.mark.parametrize("cycle_size", [2, 3, 5])
def test_resolver_small_cycles(cycle_size):
    r = DependencyResolver()
    ids = [f"c{i}" for i in range(cycle_size)]
    for idx, gid in enumerate(ids):
        deps = [ids[(idx + 1) % cycle_size]]
        g = OperationalGoal(goal_id=gid, goal_type=GoalType.MISSION, title=f"C{idx}", description="D", priority=1, dependencies=deps)
        r.add_goal(g)
    cycles = r.find_cycles()
    assert cycles


# --- Frozen edge cases ---

def test_scheduled_item_frozen():
    g = OperationalGoal(goal_id="sfg", goal_type=GoalType.MISSION, title="T", description="D", priority=1)
    c = OperationalCandidate(candidate_id="sfc", goal=g, score=0.5, urgency=0.5, impact=0.5, effort=0.5, confidence=0.5, reason="r")
    e = PlanEntry(entry_id="sfe", candidate=c, priority_tier=PriorityTier.HIGH, priority_score=0.5, rank=1, reason="r")
    si = ScheduledItem(schedule_id="si1", entry=e, position=1)
    with pytest.raises(FrozenInstanceError):
        si.position = 2


def test_scheduling_card_frozen():
    c = SchedulingCard(title="S", value=1)
    with pytest.raises(FrozenInstanceError):
        c.title = "X"


# --- Forbidden imports ---

FORBIDDEN = [
    'sam.guardian', 'sam.approval', 'sam.execution', 'sam.conversation', 'sam.storage', 'sam.domain', 'sam.repository',
    'thread', 'threading', 'asyncio', 'subprocess', 'requests', 'socket', 'network'
]


def _all_files():
    base = os.path.join(os.path.dirname(__file__), "..", "src", "sam", "operational_brain")
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith('.py'):
                yield os.path.join(root, f)


def test_no_forbidden_imports():
    bad = []
    for path in _all_files():
        with open(path, 'r', encoding='utf-8') as fh:
            tree = ast.parse(fh.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    for f in FORBIDDEN:
                        if f in n.name:
                            bad.append((path, n.name))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ''
                for f in FORBIDDEN:
                    if f in mod:
                        bad.append((path, mod))
    assert not bad, f"Found forbidden imports: {bad}"


def test_ast_parse_all():
    for path in _all_files():
        with open(path, 'r', encoding='utf-8') as fh:
            src = fh.read()
        ast.parse(src, filename=path)
