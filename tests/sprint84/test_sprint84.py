import os, sys, pytest
from dataclasses import FrozenInstanceError
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.activation.activation_strategy import ActivationStrategyEngine, ActivationStrategy
from sam.activation.activation_alternative import AlternativeGenerator, ActivationAlternative
from sam.activation.activation_priority import ActivationPriority, PriorityAssignment
from sam.activation.activation_window import ActivationWindowManager, ActivationWindow
from sam.activation.activation_sequence import SequenceBuilder, ActivationSequence, ActivationStep
from sam.activation.conversation_strategy import ConversationStrategy
from sam.activation.dashboard_strategy import DashboardStrategy, StrategyCard
from sam.activation.activation_candidate import ActivationCandidate
from sam.activation.activation_registry import ActivationRegistry


# Helpers
def _candidates():
    return [
        ActivationCandidate("c1", "C1", "immediate", 0.9, "ctx_01", 0.8),
        ActivationCandidate("c2", "C2", "scheduled", 0.7, "ctx_01", 0.6),
        ActivationCandidate("c3", "C3", "conditional", 0.5, "ctx_01", 0.4),
    ]


def _reg():
    r = ActivationRegistry()
    for c in _candidates():
        r.register_candidate(c)
    return r


# --- Frozen DTOs ---

def test_strategy_frozen():
    s = ActivationStrategy("s1", "S1", "sequential", 0.9)
    with pytest.raises(FrozenInstanceError):
        s.name = "x"


def test_alternative_frozen():
    a = ActivationAlternative("a1", "A1", "direct")
    with pytest.raises(FrozenInstanceError):
        a.alt_id = "x"


def test_priority_frozen():
    a = PriorityAssignment("c1", 1, "test")
    with pytest.raises(FrozenInstanceError):
        a.candidate_id = "x"


def test_window_frozen():
    w = ActivationWindow("w1", "W1", 0, 10, 10)
    with pytest.raises(FrozenInstanceError):
        w.window_id = "x"


def test_step_frozen():
    s = ActivationStep("s1", 1, "c1")
    with pytest.raises(FrozenInstanceError):
        s.step_id = "x"


def test_sequence_frozen():
    s = ActivationSequence("s1")
    with pytest.raises(FrozenInstanceError):
        s.sequence_id = "x"


def test_strategy_card_frozen():
    c = StrategyCard("t", "T")
    with pytest.raises(FrozenInstanceError):
        c.card_type = "x"


# --- ActivationStrategyEngine ---

def test_strategy_engine_select_direct():
    e = ActivationStrategyEngine()
    s = e.select("emergency", 3, 0.8)
    assert s.strategy_id == "direct"


def test_strategy_engine_select_parallel():
    e = ActivationStrategyEngine()
    s = e.select("busy", 3, 0.7)
    assert s.strategy_id == "parallel"


def test_strategy_engine_select_fallback():
    e = ActivationStrategyEngine()
    s = e.select("idle", 1, 0.3)
    assert s.strategy_id == "fallback"


def test_strategy_engine_select_staged():
    e = ActivationStrategyEngine()
    s = e.select("normal", 6, 0.5)
    assert s.strategy_id == "staged"


def test_strategy_engine_select_direct_high_conf():
    e = ActivationStrategyEngine()
    s = e.select("normal", 2, 0.8)
    assert s.strategy_id == "direct"


def test_strategy_engine_select_conditional():
    e = ActivationStrategyEngine()
    s = e.select("normal", 2, 0.5)
    assert s.strategy_id == "conditional"


def test_strategy_engine_list():
    e = ActivationStrategyEngine()
    assert len(e.list_strategies()) == 5


def test_strategy_engine_get():
    e = ActivationStrategyEngine()
    s = e.get_strategy("direct")
    assert s is not None
    assert s.mode == "sequential"
    assert e.get_strategy("nonexistent") is None


# --- AlternativeGenerator ---

def test_alt_generator():
    g = AlternativeGenerator()
    alts = g.generate("normal", _candidates())
    assert len(alts) >= 3


def test_alt_generator_emergency():
    g = AlternativeGenerator()
    alts = g.generate("emergency", _candidates())
    assert len(alts) >= 4  # ada emergency override


def test_alt_best():
    g = AlternativeGenerator()
    alts = g.generate("normal", _candidates())
    best = g.best(alts)
    assert best is not None
    assert best.viability > 0


def test_alt_best_empty():
    g = AlternativeGenerator()
    assert g.best([]) is None


# --- ActivationPriority ---

def test_priority_assign():
    p = ActivationPriority()
    assign = p.assign(_candidates())
    assert len(assign) == 3
    assert assign[0].priority == 1  # c1 (0.9, 0.8)
    assert assign[1].priority == 2  # c2
    assert assign[2].priority == 3  # c3


def test_priority_top_n():
    p = ActivationPriority()
    assign = p.assign(_candidates())
    top = p.top_n(assign, 2)
    assert len(top) == 2
    assert top[0].priority == 1


# --- ActivationWindow ---

def test_window_create():
    wm = ActivationWindowManager()
    w = wm.create("normal", 60.0, 1000.0)
    assert w.urgency == "normal"
    assert w.duration == 60.0


def test_window_emergency():
    wm = ActivationWindowManager()
    w = wm.create("emergency", 60.0, 1000.0)
    assert w.urgency == "critical"
    assert w.duration == 30.0  # 60 * 0.5


def test_window_expired():
    wm = ActivationWindowManager()
    w = wm.create("normal", 10.0, 0.0)
    assert wm.is_expired(w, 20.0)
    assert not wm.is_expired(w, 5.0)


def test_window_remaining():
    wm = ActivationWindowManager()
    w = wm.create("normal", 60.0, 100.0)
    assert wm.remaining(w, 110.0) == 50.0
    assert wm.remaining(w, 200.0) == 0.0


# --- SequenceBuilder ---

def test_sequence_builder():
    engine = ActivationStrategyEngine()
    priority = ActivationPriority()
    builder = SequenceBuilder()
    s = engine.select("normal", 3, 0.7)
    assign = priority.assign(_candidates())
    seq = builder.build(s, assign, _candidates())
    assert seq.total_steps == 3
    assert seq.strategy_ref == s.strategy_id


# --- ConversationStrategy ---

def test_conversation_strategy_queries():
    conv = ConversationStrategy(_reg())
    assert conv.query_count == 8


def test_conversation_strategies():
    conv = ConversationStrategy(_reg())
    engine = ActivationStrategyEngine()
    lst = conv.query_strategies(engine)
    assert len(lst) == 5


def test_conversation_selected():
    conv = ConversationStrategy(_reg())
    engine = ActivationStrategyEngine()
    s = conv.query_selected_strategy(engine, "normal")
    assert "strategy_id" in s


def test_conversation_alternatives():
    conv = ConversationStrategy(_reg())
    gen = AlternativeGenerator()
    alts = conv.query_alternatives(gen, "normal")
    assert len(alts) >= 3


def test_conversation_best_alt():
    conv = ConversationStrategy(_reg())
    gen = AlternativeGenerator()
    best = conv.query_best_alternative(gen, "normal")
    assert "id" in best
    assert best["id"] != ""


def test_conversation_priorities():
    conv = ConversationStrategy(_reg())
    prio = ActivationPriority()
    lst = conv.query_priorities(prio)
    assert len(lst) == 3


def test_conversation_window():
    conv = ConversationStrategy(_reg())
    wm = ActivationWindowManager()
    w = conv.query_window(wm, "normal", 60.0, 0.0)
    assert w["urgency"] == "normal"


def test_conversation_all_infos():
    conv = ConversationStrategy(_reg())
    engine = ActivationStrategyEngine()
    gen = AlternativeGenerator()
    prio = ActivationPriority()
    info = conv.query_all_strategy_infos(engine, gen, prio, "normal")
    assert info["strategy"] != ""
    assert info["alternatives"] >= 3
    assert info["priorities"] == 3


# --- DashboardStrategy ---

def test_dashboard_cards():
    reg = _reg()
    dash = DashboardStrategy(reg)
    assert dash.card_count == 5
    engine = ActivationStrategyEngine()
    gen = AlternativeGenerator()
    prio = ActivationPriority()
    wm = ActivationWindowManager()
    builder = SequenceBuilder()
    cards = dash.get_cards(engine, gen, prio, wm, builder, "normal")
    assert len(cards) == 5
    types = [c.card_type for c in cards]
    assert "strategy" in types
    assert "alternatives" in types
    assert "priority" in types
    assert "window" in types
    assert "sequence" in types


# --- Parametrized ---

@pytest.mark.parametrize("i", list(range(1, 36)))
def test_strategy_engine_various(i):
    e = ActivationStrategyEngine()
    envs = ["normal", "busy", "idle", "emergency"]
    env = envs[i % 4]
    cnt = i % 7
    conf = (i % 10) / 10.0
    s = e.select(env, cnt, conf)
    assert s.strategy_id in ("direct", "staged", "parallel", "conditional", "fallback")
    assert s.confidence >= 0.0


@pytest.mark.parametrize("i", list(range(1, 25)))
def test_alternatives_various(i):
    g = AlternativeGenerator()
    envs = ["normal", "busy", "idle", "emergency"]
    cands = [
        ActivationCandidate(f"c{j}", f"C{j}", "immediate", 0.1 + (j * 0.1))
        for j in range(i % 5 + 1)
    ]
    alts = g.generate(envs[i % 4], cands)
    assert len(alts) >= 3
    best = g.best(alts)
    assert best is not None


@pytest.mark.parametrize("i", list(range(1, 25)))
def test_priority_various(i):
    p = ActivationPriority()
    cands = [
        ActivationCandidate(f"c{j}", f"C{j}", "immediate",
                            0.5 + (j * 0.1), priority_score=j * 0.1)
        for j in range(i % 5 + 1)
    ]
    assign = p.assign(cands)
    assert len(assign) <= 5
    # priority harus unik
    priorities = [a.priority for a in assign]
    assert len(set(priorities)) == len(priorities)


@pytest.mark.parametrize("i", list(range(1, 15)))
def test_window_various(i):
    wm = ActivationWindowManager()
    envs = ["normal", "busy", "idle", "emergency"]
    env = envs[i % 4]
    w = wm.create(env, i * 10.0, i * 100.0)
    assert w.duration > 0
    assert w.urgency in ("normal", "high", "low", "critical")
    # validasi expired
    assert wm.is_expired(w, w.end + 1)
    assert not wm.is_expired(w, w.start)


# --- Forbidden imports & AST ---

FORBIDDEN = [
    'sam.guardian', 'sam.approval', 'sam.execution', 'sam.conversation',
    'sam.storage', 'sam.domain', 'sam.repository',
    'sam.operational_brain',
    'thread', 'threading', 'asyncio', 'subprocess', 'requests', 'socket', 'network'
]


def _all_activation_files():
    base = os.path.join(os.path.dirname(__file__), "..", "src", "sam", "activation")
    if not os.path.isdir(base):
        return
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith('.py'):
                yield os.path.join(root, f)


def test_no_forbidden_imports():
    bad = []
    for path in _all_activation_files():
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
    assert not bad, f"Forbidden imports found: {bad}"


def test_ast_parse_all():
    for path in _all_activation_files():
        with open(path, 'r', encoding='utf-8') as fh:
            src = fh.read()
        ast.parse(src, filename=path)
