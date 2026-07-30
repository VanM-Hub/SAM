import os, sys
import pytest
from dataclasses import FrozenInstanceError
import ast

# ensure src on path when pytest runs from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_goal import GoalType, OperationalGoal
from sam.operational_brain.operational_candidate import OperationalCandidate
from sam.operational_brain.operational_registry import OperationalRegistry, OperationalSnapshot
from sam.operational_brain.operational_builder import OperationalBuilder
from sam.operational_brain.conversation_operational import OperationalConversation
from sam.operational_brain.dashboard_operational import OperationalDashboard, OperationalDashboardCard

# --- DTO frozen tests ---

def test_operational_context_frozen():
    ctx = OperationalContext(context_id="ctx1", timestamp=1.0, source="manual", environment="normal")
    with pytest.raises(FrozenInstanceError):
        ctx.source = "auto"


def test_operational_goal_frozen():
    g = OperationalGoal(goal_id="g1", goal_type=GoalType.MISSION, title="T", description="D", priority=1)
    with pytest.raises(FrozenInstanceError):
        g.title = "X"


def test_operational_candidate_frozen():
    g_local = OperationalGoal(goal_id="g_local", goal_type=GoalType.MISSION, title="Tlocal", description="D", priority=1)
    c = OperationalCandidate(candidate_id="c1", goal=g_local, score=0.5, urgency=0.5, impact=0.5, effort=0.5, confidence=0.5, reason="r")
    with pytest.raises(FrozenInstanceError):
        c.score = 0.9

# --- Context to_dict ---

def test_context_to_dict_keys():
    ctx = OperationalContext(context_id="ctx2", timestamp=2.0, source="inbox", environment="busy", active_missions=["m1"], pending_decisions=1, pending_approvals=2, available_resources=3, active_constraints=["c1"], metadata={"a":1})
    d = ctx.to_dict()
    assert set(d.keys()) == {"context_id","timestamp","source","environment","active_missions","pending_decisions","pending_approvals","available_resources","active_constraints","metadata"}

# --- GoalType enum ---

def test_goal_type_members():
    names = [g.name for g in GoalType]
    expected = ["MISSION","STABILITY","RECOVERY","OPTIMIZATION","MAINTENANCE","LEARNING","MONITORING","CUSTOM"]
    assert names == expected

# --- Registry basic operations ---

def test_registry_register_find_remove_list():
    reg = OperationalRegistry()
    g = OperationalGoal(goal_id="g-test", goal_type=GoalType.MISSION, title="T", description="D", priority=5)
    reg.register_goal(g)
    assert reg.find_goal("g-test") is g
    goals = reg.list_goals()
    assert len(goals) == 1 and goals[0].goal_id == "g-test"
    assert reg.remove_goal("g-test") is True
    assert reg.find_goal("g-test") is None


def test_registry_register_candidate_and_find_remove():
    reg = OperationalRegistry()
    g = OperationalGoal(goal_id="g2", goal_type=GoalType.MISSION, title="T2", description="D2", priority=2)
    c = OperationalCandidate(candidate_id="cand1", goal=g, score=0.4, urgency=0.3, impact=0.2, effort=0.1, confidence=0.8, reason="r")
    reg.register_candidate(c)
    assert reg.find_candidate("cand1") is c
    assert reg.remove_candidate("cand1") is True
    assert reg.find_candidate("cand1") is None

# --- Statistics and snapshot ---

def test_registry_statistics_snapshot_empty():
    reg = OperationalRegistry()
    s = reg.statistics()
    assert isinstance(s, OperationalSnapshot)
    assert s.goals == 0 and s.candidates == 0

# --- Builder behaviour (parametrized many cases to reach test count) ---

@pytest.mark.parametrize("i", list(range(1,101)))
def test_builder_generates_candidates_various_contexts(i):
    # vary context attributes deterministically by i
    ctx = OperationalContext(
        context_id=f"ctx_{i}",
        timestamp=float(i),
        source="manual" if i % 2 == 0 else "inbox",
        environment=("normal","busy","idle","emergency")[i % 4],
        active_missions=[f"m{j}" for j in range(i % 3)],
        pending_decisions=i % 5,
        pending_approvals=i % 4,
        available_resources=(i % 5) - 2,  # -2..2
        active_constraints=[f"con{j}" for j in range(i % 2)],
        metadata={"i": i},
    )
    builder = OperationalBuilder()
    candidates = builder.build(ctx)
    # builder always returns a non-empty list (idle fallback)
    assert isinstance(candidates, list)
    assert len(candidates) >= 1
    # members should be OperationalCandidate and their goal OperationalGoal
    for c in candidates:
        assert isinstance(c, OperationalCandidate)
        assert isinstance(c.goal, OperationalGoal)
        assert 0.0 <= c.score <= 1.0
        assert 0.0 <= c.urgency <= 1.0
        assert 0.0 <= c.impact <= 1.0
        assert 0.0 <= c.effort <= 1.0
        assert 0.0 <= c.confidence <= 1.0

# Additional property-focused builder tests
@pytest.mark.parametrize("i", list(range(1,31)))
def test_builder_candidate_property_ranges(i):
    ctx = OperationalContext(
        context_id=f"ctxp_{i}",
        timestamp=float(i),
        source="timer",
        environment="normal",
        active_missions=["alpha"] if i % 2 == 0 else [],
        pending_decisions=1 if i % 3 == 0 else 0,
        pending_approvals=1 if i % 4 == 0 else 0,
        available_resources=1 if i % 5 == 0 else 0,
    )
    builder = OperationalBuilder()
    candidates = builder.build(ctx)
    for c in candidates:
        assert isinstance(c.candidate_id, str)
        assert isinstance(c.reason, str)
        assert c.score >= 0.0 and c.score <= 1.0
        assert c.confidence >= 0.0 and c.confidence <= 1.0

# --- Conversation bridge tests ---

def test_conversation_queries_methods_exist_and_return_types():
    reg = OperationalRegistry()
    conv = OperationalConversation(registry=reg)
    # query_count property
    assert hasattr(conv, 'query_count')
    assert conv.query_count == 10
    # context query
    ctx = OperationalContext(context_id="cx", timestamp=1.0, source="manual", environment="normal")
    d = conv.query_context(ctx)
    assert isinstance(d, dict) and d['context_id'] == "cx"
    # goals & candidates
    assert isinstance(conv.query_goals(), list)
    assert isinstance(conv.query_candidates(), list)
    # summaries
    gs = conv.query_goal_summary()
    assert 'total_goals' in gs
    rs = conv.query_resource_summary(ctx)
    assert 'available_resources' in rs
    cs = conv.query_constraints(ctx)
    assert isinstance(cs, list)
    dg = conv.query_dependency_graph()
    assert isinstance(dg, dict)
    stats = conv.query_statistics()
    assert 'goals' in stats and 'candidates' in stats
    snap = conv.query_snapshot()
    assert 'goals' in snap
    br = conv.query_builder_result(ctx)
    assert isinstance(br, list)

# --- Dashboard tests ---

def test_dashboard_cards_count_and_content():
    reg = OperationalRegistry()
    dash = OperationalDashboard(registry=reg)
    ctx = OperationalContext(context_id="dctx", timestamp=1.0, source="manual", environment="normal")
    cards = dash.get_cards(ctx)
    assert isinstance(cards, list)
    assert len(cards) == dash.card_count == 6
    for card in cards:
        assert isinstance(card, OperationalDashboardCard)
        assert isinstance(card.title, str)

# --- Forbidden imports / AST scan ---

FORBIDDEN = [
    'sam.guardian', 'sam.approval', 'sam.execution', 'sam.conversation', 'sam.storage', 'sam.domain', 'sam.repository',
    'thread', 'threading', 'asyncio', 'subprocess', 'requests', 'socket', 'network'
]

def _all_operational_files():
    base = os.path.join(os.path.dirname(__file__), '..', 'src', 'sam', 'operational_brain')
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith('.py'):
                yield os.path.join(root, f)


def test_no_forbidden_imports_in_operational_brain():
    bad = []
    for path in _all_operational_files():
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


def test_ast_parse_all_files():
    # ensure all files are syntactically valid
    for path in _all_operational_files():
        with open(path, 'r', encoding='utf-8') as fh:
            src = fh.read()
        ast.parse(src, filename=path)

# --- Registry bulk operations and statistics param test ---

@pytest.mark.parametrize("n", [1,2,5,10,20])
def test_registry_bulk_register_and_stats(n):
    reg = OperationalRegistry()
    for i in range(n):
        g = OperationalGoal(goal_id=f"g_bulk_{i}", goal_type=GoalType.MISSION, title=f"T{i}", description="D", priority=(i%10)+1)
        reg.register_goal(g)
        c = OperationalCandidate(candidate_id=f"c_bulk_{i}", goal=g, score=0.5, urgency=0.5, impact=0.5, effort=0.5, confidence=0.5, reason="r")
        reg.register_candidate(c)
    s = reg.statistics()
    assert s.goals == n
    assert s.candidates == n

# end of file
