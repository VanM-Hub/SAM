import os, sys
import pytest
from dataclasses import FrozenInstanceError
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_goal import GoalType, OperationalGoal
from sam.operational_brain.operational_candidate import OperationalCandidate
from sam.operational_brain.operational_builder import OperationalBuilder
from sam.operational_brain.operational_planner import (
    PriorityTier,
    PlanEntry,
    PlanSummary,
    OperationalPrioritizer,
    OperationalPlanner,
)
from sam.operational_brain.operational_planning import OperationalPlanning
from sam.operational_brain.conversation_planning import ConversationPlanning
from sam.operational_brain.dashboard_planning import DashboardPlanning, PlanningCard


# --- Helper ---

def _make_ctx(eid="ctx_test", env="normal", src="manual", missions=None,
              decisions=0, approvals=0, resources=1):
    return OperationalContext(
        context_id=eid,
        timestamp=100.0,
        source=src,
        environment=env,
        active_missions=missions or [],
        pending_decisions=decisions,
        pending_approvals=approvals,
        available_resources=resources,
    )


def _basic_candidates():
    """Return 4 deterministic candidates for testing."""
    builder = OperationalBuilder()
    ctx = _make_ctx("bc", env="busy", decisions=2, approvals=1, missions=["m1", "m2"])
    return builder.build(ctx)


# --- PlanEntry & PlanSummary frozen ---

def test_plan_entry_frozen():
    g = OperationalGoal(goal_id="pg", goal_type=GoalType.MISSION, title="T", description="D", priority=1)
    c = OperationalCandidate(candidate_id="pc", goal=g, score=0.5, urgency=0.5, impact=0.5, effort=0.5, confidence=0.5, reason="r")
    e = PlanEntry(entry_id="pe", candidate=c, priority_tier=PriorityTier.HIGH, priority_score=0.7, rank=1, reason="r")
    with pytest.raises(FrozenInstanceError):
        e.rank = 5


def test_plan_summary_frozen():
    s = PlanSummary(total_entries=5, critical=2, high=1, medium=1, low=1, background=0, top_score=0.9, bottom_score=0.1)
    with pytest.raises(FrozenInstanceError):
        s.total_entries = 10


def test_planning_card_frozen():
    c = PlanningCard(title="Test", value=42)
    with pytest.raises(FrozenInstanceError):
        c.title = "X"


# --- PriorityTier enum ---

def test_priority_tier_members():
    names = [t.name for t in PriorityTier]
    assert names == ["CRITICAL", "HIGH", "MEDIUM", "LOW", "BACKGROUND"]


# --- Prioritizer ---

def test_prioritizer_gives_sorted_entries():
    candidates = _basic_candidates()
    prio = OperationalPrioritizer()
    ctx = _make_ctx("prio1")
    entries = prio.prioritize(candidates, ctx)
    assert len(entries) >= 1
    for i in range(len(entries) - 1):
        assert entries[i].priority_score >= entries[i + 1].priority_score
    assert entries[0].rank == 1
    assert entries[-1].rank == len(entries)


def test_prioritizer_score_range():
    candidates = _basic_candidates()
    prio = OperationalPrioritizer()
    ctx = _make_ctx("prio2")
    entries = prio.prioritize(candidates, ctx)
    for e in entries:
        assert 0.0 <= e.priority_score <= 1.0


def test_prioritizer_tier_for_recovery_critical():
    builder = OperationalBuilder()
    ctx = _make_ctx("rec", env="emergency", resources=-1)
    cands = builder.build(ctx)
    prio = OperationalPrioritizer()
    entries = prio.prioritize(cands, ctx)
    for e in entries:
        if e.candidate.candidate_id == "c_rec":
            assert e.priority_tier == PriorityTier.CRITICAL
            break
    else:
        pytest.fail("c_rec not found")


def test_prioritizer_tier_by_score():
    prio = OperationalPrioritizer()
    g = OperationalGoal(goal_id="g_t", goal_type=GoalType.MISSION, title="T", description="D", priority=1)
    cases = [
        (0.75, PriorityTier.HIGH),
        (0.50, PriorityTier.MEDIUM),
        (0.30, PriorityTier.LOW),
        (0.10, PriorityTier.BACKGROUND),
    ]
    for score, expected_tier in cases:
        c = OperationalCandidate(candidate_id=f"ct_{score}", goal=g, score=score, urgency=score,
                                  impact=score, effort=0.0, confidence=score, reason="r")
        ctx = _make_ctx("tier_test")
        entries = prio.prioritize([c], ctx)
        assert entries[0].priority_tier == expected_tier, f"score={score} expected={expected_tier} got={entries[0].priority_tier}"


# --- Planner ---

def test_planner_plan_and_summary():
    planner = OperationalPlanner()
    candidates = _basic_candidates()
    ctx = _make_ctx("pl1")
    entries = planner.plan(candidates, ctx)
    assert len(entries) >= 1
    assert len(entries) == len(planner.entries)
    s = planner.summary()
    assert isinstance(s, PlanSummary)
    assert s.total_entries == len(entries)


def test_planner_summary_empty():
    planner = OperationalPlanner()
    s = planner.summary()
    assert s.total_entries == 0


def test_planner_plan_dict():
    planner = OperationalPlanner()
    candidates = _basic_candidates()
    ctx = _make_ctx("pd")
    planner.plan(candidates, ctx)
    d = planner.plan_dict()
    assert "total_entries" in d
    assert d["total_entries"] >= 1


# --- OperationalPlanning orchestrator ---

def test_planning_run():
    planning = OperationalPlanning()
    ctx = _make_ctx("run1", env="busy", decisions=1)
    plan = planning.run(ctx)
    assert len(plan) >= 1
    assert len(planning.last_plan) >= 1
    s = planning.summary()
    assert s.total_entries >= 1


def test_planning_find_entry():
    planning = OperationalPlanning()
    ctx = _make_ctx("find")
    planning.run(ctx)
    plan = planning.last_plan
    if plan:
        found = planning.find_entry(plan[0].entry_id)
        assert found is not None
    assert planning.find_entry("nonexistent") is None


def test_planning_entries_by_tier():
    planning = OperationalPlanning()
    ctx = _make_ctx("tier", env="emergency", resources=-1)
    planning.run(ctx)
    crit = planning.entries_by_tier(PriorityTier.CRITICAL)
    assert len(crit) >= 1


# --- ConversationPlanning ---

def test_conversation_planning_query_count():
    planning = OperationalPlanning()
    conv = ConversationPlanning(planning)
    assert conv.query_count == 8


def test_conversation_planning_summary():
    planning = OperationalPlanning()
    ctx = _make_ctx("conv1", env="busy", decisions=2)
    conv = ConversationPlanning(planning)
    d = conv.query_planning_summary(ctx)
    assert d["source"] == "manual"
    assert d["entries"] >= 1


def test_conversation_planning_last_plan():
    planning = OperationalPlanning()
    ctx = _make_ctx("conv2")
    planning.run(ctx)
    conv = ConversationPlanning(planning)
    lst = conv.query_last_plan()
    assert isinstance(lst, list)
    for item in lst:
        assert "entry_id" in item
        assert "rank" in item
        assert "tier" in item


def test_conversation_planning_top_n():
    planning = OperationalPlanning()
    ctx = _make_ctx("topn", env="busy", decisions=1)
    planning.run(ctx)
    conv = ConversationPlanning(planning)
    lst = conv.query_top_n(999)
    assert len(lst) <= len(planning.last_plan)
    lst2 = conv.query_top_n(2)
    assert len(lst2) <= 2


def test_conversation_planning_entry_by_id():
    planning = OperationalPlanning()
    ctx = _make_ctx("eid1")
    planning.run(ctx)
    conv = ConversationPlanning(planning)
    if planning.last_plan:
        entry_id = planning.last_plan[0].entry_id
        d = conv.query_entry_by_id(entry_id)
        assert "error" not in d
        assert d["entry_id"] == entry_id
    d2 = conv.query_entry_by_id("fake_id")
    assert "error" in d2


def test_conversation_planning_health():
    planning = OperationalPlanning()
    ctx = _make_ctx("health", env="busy", decisions=1)
    planning.run(ctx)
    conv = ConversationPlanning(planning)
    h = conv.query_plan_health()
    assert "total_entries" in h
    assert "critical_pct" in h


# --- DashboardPlanning ---

def test_dashboard_planning_card_count():
    planning = OperationalPlanning()
    dash = DashboardPlanning(planning)
    ctx = _make_ctx("d1", env="busy", decisions=1)
    planning.run(ctx)
    cards = dash.get_cards(ctx)
    assert len(cards) == dash.card_count == 5
    for card in cards:
        assert isinstance(card, PlanningCard)


def test_dashboard_planning_types():
    planning = OperationalPlanning()
    dash = DashboardPlanning(planning)
    ctx = _make_ctx("d2")
    planning.run(ctx)
    cards = dash.get_cards(ctx)
    types = [c.card_type for c in cards]
    assert "summary" in types
    assert "top" in types
    assert "critical" in types
    assert "range" in types
    assert "distribution" in types


def test_dashboard_planning_no_plan():
    """Dashboard should handle empty plan gracefully."""
    planning = OperationalPlanning()
    dash = DashboardPlanning(planning)
    ctx = _make_ctx("empty")
    cards = dash.get_cards(ctx)
    assert len(cards) == 5


def test_dashboard_planning_full_pipeline():
    planning = OperationalPlanning()
    dash = DashboardPlanning(planning)
    ctx = _make_ctx("full", env="emergency", decisions=3, approvals=2, missions=["m1", "m2", "m3"], resources=0)
    planning.run(ctx)
    cards = dash.get_cards(ctx)
    s = planning.summary()
    assert s.total_entries >= 1
    # top-entry card must have a value if plan exists
    top_card = [c for c in cards if c.card_type == "top"][0]
    assert top_card.value != {"msg": "No plan"}


# --- Parametrized tests for robustness ---

@pytest.mark.parametrize("n", [1, 2, 4, 8, 16])
def test_planner_sorted_entries_param(n):
    planner = OperationalPlanner()
    ctx = _make_ctx(f"param_{n}", env="busy", decisions=n % 5, missions=[f"m{i}" for i in range(n % 4)])
    builder = OperationalBuilder()
    candidates = builder.build(ctx)
    planner.plan(candidates, ctx)
    entries = planner.entries
    for i in range(len(entries) - 1):
        assert entries[i].priority_score >= entries[i + 1].priority_score


@pytest.mark.parametrize("n", list(range(1, 21)))
def test_planner_various_contexts(n):
    enums = ["normal", "busy", "idle", "emergency"]
    ctx = _make_ctx(f"vc{n}", env=enums[n % 4], src="manual", decisions=n % 3, approvals=n % 2, resources=[-1, 0, 1, 2][n % 4])
    builder = OperationalBuilder()
    planner = OperationalPlanner()
    candidates = builder.build(ctx)
    entries = planner.plan(candidates, ctx)
    assert len(entries) >= 1
    s = planner.summary()
    assert s.total_entries == len(entries)
    # cumulative counts should match
    assert s.critical + s.high + s.medium + s.low + s.background == s.total_entries


# --- Forbidden imports ---

FORBIDDEN = [
    'sam.guardian', 'sam.approval', 'sam.execution', 'sam.conversation', 'sam.storage', 'sam.domain', 'sam.repository',
    'thread', 'threading', 'asyncio', 'subprocess', 'requests', 'socket', 'network'
]


def _all_planning_files():
    base = os.path.join(os.path.dirname(__file__), "..", "src", "sam", "operational_brain")
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith('.py'):
                yield os.path.join(root, f)


def test_no_forbidden_imports_in_planning_files():
    bad = []
    for path in _all_planning_files():
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


def test_ast_parse_all_planning_files():
    for path in _all_planning_files():
        with open(path, 'r', encoding='utf-8') as fh:
            src = fh.read()
        ast.parse(src, filename=path)


# --- Edge cases ---

def test_planning_with_empty_candidates():
    planner = OperationalPlanner()
    entries = planner.plan([], _make_ctx("empty"))
    assert entries == []
    s = planner.summary()
    assert s.total_entries == 0


def test_prioritizer_handles_all_same_score():
    g = OperationalGoal(goal_id="g_eq", goal_type=GoalType.MISSION, title="T", description="D", priority=1)
    cands = [
        OperationalCandidate(candidate_id=f"eq_{i}", goal=g, score=0.5, urgency=0.5, impact=0.5, effort=0.5, confidence=0.5, reason="r")
        for i in range(5)
    ]
    prio = OperationalPrioritizer()
    ctx = _make_ctx("eq_ctx")
    entries = prio.prioritize(cands, ctx)
    # All should have same score
    scores = [e.priority_score for e in entries]
    assert len(set(scores)) == 1
    # Ranks should be sequential
    ranks = [e.rank for e in entries]
    assert ranks == list(range(1, len(entries) + 1))


def test_planning_card_frozen_attr():
    c = PlanningCard(title="Attr", value="x")
    with pytest.raises(FrozenInstanceError):
        c.title = "new"
    with pytest.raises(FrozenInstanceError):
        c.value = "y"


def test_plan_summary_default():
    s = PlanSummary()
    assert s.total_entries == 0
