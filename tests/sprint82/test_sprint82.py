import os, sys
import pytest
from dataclasses import FrozenInstanceError
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.activation.activation_context import ActivationContext
from sam.activation.activation_request import ActivationRequest
from sam.activation.activation_candidate import ActivationCandidate
from sam.activation.activation_registry import ActivationRegistry, ActivationSnapshot
from sam.activation.activation_builder import ActivationBuilder
from sam.activation.activation_draft import ActivationDraft
from sam.activation.conversation_activation import ConversationActivation
from sam.activation.dashboard_activation import DashboardActivation, ActivationCard
from sam.activation.runtime import ActivationRuntime


# --- Helpers ---

def _ctx(env="normal", candidates=3, goals=2):
    return ActivationContext(
        context_id="act_ctx_01", timestamp=600.0, source_plan="plan_01",
        environment=env, total_candidates=candidates, total_goals=goals,
        decision_id="dec_01", approval_id="app_01",
    )


def _req(priority="normal"):
    return ActivationRequest(
        request_id="req_01", plan_id="plan_01", timestamp=600.0,
        requester="system", priority=priority,
    )


# --- DTO frozen ---

def test_activation_context_frozen():
    ctx = _ctx()
    with pytest.raises(FrozenInstanceError):
        ctx.context_id = "x"


def test_activation_request_frozen():
    req = _req()
    with pytest.raises(FrozenInstanceError):
        req.request_id = "x"


def test_activation_candidate_frozen():
    c = ActivationCandidate(candidate_id="c1", name="T", candidate_type="immediate")
    with pytest.raises(FrozenInstanceError):
        c.candidate_id = "x"


def test_activation_draft_frozen():
    d = ActivationDraft(draft_id="d1", context_id="c1")
    with pytest.raises(FrozenInstanceError):
        d.draft_id = "x"


def test_activation_snapshot_frozen():
    s = ActivationSnapshot()
    with pytest.raises(FrozenInstanceError):
        s.status = "x"


def test_activation_card_frozen():
    c = ActivationCard(card_type="t", title="T")
    with pytest.raises(FrozenInstanceError):
        c.card_type = "x"


# --- ActivationContext ---

def test_context_to_dict():
    ctx = _ctx()
    d = ctx.to_dict()
    assert d["context_id"] == "act_ctx_01"
    assert d["environment"] == "normal"
    assert d["total_candidates"] == 3
    assert d["total_goals"] == 2
    assert d["decision_id"] == "dec_01"


# --- ActivationRegistry ---

def test_registry_initial():
    reg = ActivationRegistry()
    assert reg.context_count == 0
    assert reg.request_count == 0
    assert reg.candidate_count == 0


def test_registry_context_crud():
    reg = ActivationRegistry()
    ctx = _ctx()
    reg.register_context(ctx)
    assert reg.context_count == 1
    assert reg.get_context("act_ctx_01") is ctx
    assert reg.get_context("nonexistent") is None
    assert len(reg.list_contexts()) == 1


def test_registry_request_crud():
    reg = ActivationRegistry()
    req = _req()
    reg.register_request(req)
    assert reg.request_count == 1
    assert reg.get_request("req_01") is req


def test_registry_candidate_crud():
    reg = ActivationRegistry()
    c = ActivationCandidate(candidate_id="c1", name="T", candidate_type="immediate")
    reg.register_candidate(c)
    assert reg.candidate_count == 1
    assert reg.get_candidate("c1") is c
    assert reg.get_candidate("x") is None


def test_registry_candidates_by_type():
    reg = ActivationRegistry()
    reg.register_candidate(ActivationCandidate("c1", "T1", "immediate"))
    reg.register_candidate(ActivationCandidate("c2", "T2", "scheduled"))
    reg.register_candidate(ActivationCandidate("c3", "T3", "immediate"))
    imm = reg.list_candidates_by_type("immediate")
    assert len(imm) == 2
    assert len(reg.list_candidates_by_type("batch")) == 0


def test_registry_snapshot_empty():
    reg = ActivationRegistry()
    snap = reg.snapshot()
    assert snap.status == "empty"
    assert snap.contexts == 0


def test_registry_snapshot_active():
    reg = ActivationRegistry()
    reg.register_context(_ctx())
    snap = reg.snapshot()
    assert snap.status == "active"


def test_registry_clear():
    reg = ActivationRegistry()
    reg.register_context(_ctx())
    reg.register_request(_req())
    reg.clear()
    assert reg.context_count == 0
    assert reg.request_count == 0
    assert reg.candidate_count == 0


# --- ActivationBuilder ---

def test_builder_build_normal():
    builder = ActivationBuilder()
    ctx = _ctx(env="normal", candidates=3, goals=2)
    req = _req()
    candidates = builder.build(ctx, req)
    assert len(candidates) >= 3  # imm + sch + cond
    ids = [c.candidate_id for c in candidates]
    assert any("_imm" in i for i in ids)
    assert any("_sch" in i for i in ids)


def test_builder_build_emergency():
    builder = ActivationBuilder()
    ctx = _ctx(env="emergency")
    req = _req()
    candidates = builder.build(ctx, req)
    # no scheduled in emergency
    ids = [c.candidate_type for c in candidates]
    assert "scheduled" not in ids
    assert "immediate" in ids


def test_builder_build_idle():
    builder = ActivationBuilder()
    ctx = _ctx(env="idle")
    req = _req()
    candidates = builder.build(ctx, req)
    types = [c.candidate_type for c in candidates]
    assert "manual" in types


def test_builder_build_batch():
    builder = ActivationBuilder()
    ctx = _ctx(env="normal", candidates=5)
    req = _req()
    candidates = builder.build(ctx, req)
    types = [c.candidate_type for c in candidates]
    assert "batch" in types


def test_builder_build_types_list():
    builder = ActivationBuilder()
    types = builder.build_types_list()
    assert len(types) == 5
    assert "immediate" in types
    assert "batch" in types


# --- ActivationRuntime ---

def test_runtime_initial():
    rt = ActivationRuntime()
    assert rt.registry.context_count == 0
    snap = rt.snapshot()
    assert snap["status"] == "empty"


def test_runtime_run():
    rt = ActivationRuntime()
    ctx = _ctx()
    req = _req()
    draft = rt.run(ctx, req)
    assert isinstance(draft, ActivationDraft)
    assert draft.candidates >= 1
    assert draft.top_candidate != ""
    assert "Generated" in draft.summary
    assert rt.registry.context_count == 1
    assert rt.registry.request_count == 1
    assert rt.registry.candidate_count >= 1


def test_runtime_conversation():
    rt = ActivationRuntime()
    ctx = _ctx()
    req = _req()
    rt.run(ctx, req)
    conv = rt.conversation
    assert conv.query_count == 10
    snap = conv.query_snapshot()
    assert snap["status"] == "active"
    assert snap["contexts"] == 1
    ctx_dict = conv.query_context("act_ctx_01")
    assert ctx_dict is not None
    assert ctx_dict["environment"] == "normal"
    assert conv.query_context("x") is None


def test_runtime_dashboard():
    rt = ActivationRuntime()
    ctx = _ctx()
    req = _req()
    rt.run(ctx, req)
    dash = rt.dashboard
    assert dash.card_count == 6
    cards = dash.get_cards(rt.builder, ctx, req)
    assert len(cards) == 6
    for card in cards:
        assert isinstance(card, ActivationCard)


# --- ConversationActivation ---

def test_conversation_10_queries():
    reg = ActivationRegistry()
    conv = ConversationActivation(reg)
    assert conv.query_count == 10


def test_conversation_query_all_empty():
    reg = ActivationRegistry()
    conv = ConversationActivation(reg)
    assert conv.query_all_contexts() == []
    assert conv.query_all_requests() == []
    assert conv.query_all_candidates() == []


def test_conversation_with_data():
    reg = ActivationRegistry()
    builder = ActivationBuilder()
    ctx = _ctx()
    req = _req()
    reg.register_context(ctx)
    reg.register_request(req)
    for c in builder.build(ctx, req):
        reg.register_candidate(c)
    conv = ConversationActivation(reg)

    # queries
    assert len(conv.query_all_contexts()) == 1
    assert len(conv.query_all_requests()) == 1
    assert len(conv.query_all_candidates()) >= 3

    # by type
    imm = conv.query_candidates_by_type("immediate")
    assert len(imm) >= 1

    # builder types
    assert len(conv.query_builder_types(builder)) == 5

    # builder preview
    preview = conv.query_builder_preview(builder, ctx, req)
    assert preview["total_candidates_generated"] >= 3


# --- DashboardActivation ---

def test_dashboard_card_frozen():
    c = ActivationCard(card_type="t", title="T")
    with pytest.raises(FrozenInstanceError):
        c.title = "X"


def test_dashboard_6_cards():
    reg = ActivationRegistry()
    builder = ActivationBuilder()
    ctx = _ctx()
    req = _req()
    dash = DashboardActivation(reg)
    cards = dash.get_cards(builder, ctx, req)
    assert len(cards) == 6


def test_dashboard_with_registered_data():
    reg = ActivationRegistry()
    builder = ActivationBuilder()
    ctx = _ctx()
    req = _req()
    reg.register_context(ctx)
    reg.register_request(req)
    for c in builder.build(ctx, req):
        reg.register_candidate(c)
    dash = DashboardActivation(reg)
    cards = dash.get_cards(builder, ctx, req)
    types = [c.card_type for c in cards]
    assert "overview" in types
    assert "candidates" in types
    assert "registry" in types
    assert "preview" in types
    assert "requests" in types
    assert "contexts" in types

    reg_card = [c for c in cards if c.card_type == "registry"][0]
    assert "Status: active" in str(reg_card.items)


# --- Parametrized ---

@pytest.mark.parametrize("i", list(range(1, 61)))
def test_builder_various_contexts(i):
    builder = ActivationBuilder()
    envs = ["normal", "busy", "idle", "emergency"]
    ctx = _ctx(
        env=envs[i % 4],
        candidates=i % 6,
        goals=i % 4,
    )
    req = _req(priority=["low", "normal", "high", "critical"][i % 4])
    candidates = builder.build(ctx, req)
    assert len(candidates) >= 1
    for c in candidates:
        assert c.candidate_type in ("immediate", "scheduled", "conditional", "manual", "batch")
        assert 0.0 <= c.confidence <= 1.0
        assert c.context_id == "act_ctx_01"


@pytest.mark.parametrize("i", list(range(1, 41)))
def test_runtime_various_scenarios(i):
    rt = ActivationRuntime()
    ctx = _ctx(
        env=["normal", "busy", "idle", "emergency"][i % 4],
        candidates=i % 5,
        goals=i % 3,
    )
    req = _req(priority=["low", "normal", "high", "critical"][i % 4])
    draft = rt.run(ctx, req)
    assert draft.candidates >= 1
    assert draft.top_candidate != ""
    assert draft.context_id == "act_ctx_01"


# --- Forbidden imports ---

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
