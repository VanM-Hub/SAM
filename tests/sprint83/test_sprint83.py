import os, sys, pytest
from dataclasses import FrozenInstanceError
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.activation.activation_validator import ActivationValidator, ValidationReport, ValidationError
from sam.activation.activation_rules import ActivationRules, ActivationRule
from sam.activation.activation_constraints import ActivationConstraints, ConstraintResult
from sam.activation.activation_readiness import ActivationReadiness, ReadinessCheck
from sam.activation.activation_report import ActivationReport, ActivationReportBuilder
from sam.activation.conversation_validation import ConversationValidation
from sam.activation.dashboard_validation import DashboardValidation, ValidationCard
from sam.activation.activation_draft import ActivationDraft
from sam.activation.activation_candidate import ActivationCandidate
from sam.activation.activation_context import ActivationContext
from sam.activation.activation_registry import ActivationRegistry
from sam.activation.runtime import ActivationRuntime


# Helpers
def _draft(candidates=2, _id="draft_01"):
    return ActivationDraft(draft_id=_id, context_id="ctx_01", candidates=candidates,
                           types_used=["immediate"], top_candidate="c1",
                           summary="test draft")


def _candidates():
    return [
        ActivationCandidate("c1", "C1", "immediate", 0.9, "ctx_01", 0.8),
        ActivationCandidate("c2", "C2", "scheduled", 0.7, "ctx_01", 0.6),
        ActivationCandidate("c3", "C3", "conditional", 0.5, "ctx_01", 0.4),
    ]


def _ctx():
    return ActivationContext("ctx_01", 100.0)


# --- Frozen DTOs ---

def test_validation_error_frozen():
    with pytest.raises(FrozenInstanceError):
        ValidationError().field = "x"


def test_validation_report_frozen():
    with pytest.raises(FrozenInstanceError):
        ValidationReport(draft_id="d").draft_id = "x"


def test_constraint_result_frozen():
    with pytest.raises(FrozenInstanceError):
        ConstraintResult().constraint_id = "x"


def test_readiness_check_frozen():
    with pytest.raises(FrozenInstanceError):
        ReadinessCheck().check_id = "x"


def test_activation_report_frozen():
    with pytest.raises(FrozenInstanceError):
        ActivationReport().report_id = "x"


def test_rule_frozen():
    r = ActivationRule("n", "d")
    with pytest.raises(FrozenInstanceError):
        r.name = "x"


def test_validation_card_frozen():
    c = ValidationCard("t", "T")
    with pytest.raises(FrozenInstanceError):
        c.card_type = "x"


# --- ActivationValidator ---

def test_validator_valid():
    v = ActivationValidator()
    draft = _draft()
    report = v.validate(draft, _candidates())
    assert report.valid
    assert report.total_errors == 0


def test_validator_empty_draft():
    v = ActivationValidator()
    draft = ActivationDraft(draft_id="", context_id="ctx_01", candidates=2)
    report = v.validate(draft, _candidates())
    assert not report.valid


def test_validator_no_candidates():
    v = ActivationValidator()
    draft = ActivationDraft(draft_id="d1", context_id="ctx_01", candidates=0)
    report = v.validate(draft, [])
    assert not report.valid
    assert report.total_errors > 0


def test_validator_invalid_type():
    v = ActivationValidator()
    bad = ActivationCandidate("c_bad", "Bad", "invalid_type", 0.5)
    draft = _draft()
    report = v.validate(draft, [bad])
    assert not report.valid
    assert report.total_errors >= 1


def test_validator_warning_on_empty_top():
    v = ActivationValidator()
    draft = ActivationDraft(draft_id="d1", context_id="ctx_01", candidates=2)
    report = v.validate(draft, _candidates())
    assert report.total_warnings >= 1


# --- ActivationRules ---

def test_rules_default():
    rules = ActivationRules()
    assert len(rules.list_rules()) >= 6


def test_rules_by_scope():
    rules = ActivationRules()
    draft_rules = rules.list_by_scope("draft")
    assert len(draft_rules) >= 2


def test_rules_get():
    rules = ActivationRules()
    r = rules.get_rule("no_empty_draft")
    assert r is not None
    assert r.priority == 10
    assert r.applies_to == "all"


def test_rules_all_scopes():
    rules = ActivationRules()
    scopes = rules.all_scopes()
    assert "candidate" in scopes
    assert "draft" in scopes


# --- ActivationConstraints ---

def test_constraint_environment():
    c = ActivationConstraints()
    r = c.check_environment("normal")
    assert r.passed
    r2 = c.check_environment("invalid_xyz")
    assert not r2.passed


def test_constraint_min_candidates():
    c = ActivationConstraints()
    assert c.check_candidates_min(5).passed
    assert not c.check_candidates_min(0).passed


def test_constraint_confidence():
    c = ActivationConstraints()
    r = c.check_confidence(_candidates())
    assert r.passed
    r2 = c.check_confidence([])
    assert not r2.passed


def test_constraint_check_all():
    c = ActivationConstraints()
    results = c.check_all("normal", 3, _candidates())
    assert len(results) == 3
    passed = sum(1 for r in results if r.passed)
    assert passed >= 2


# --- ActivationReadiness ---

def test_readiness_all_pass():
    r = ActivationReadiness()
    results = r.check(True, True, True, True, True)
    assert len(results) == 5
    assert all(r.passed for r in results)


def test_readiness_fail():
    r = ActivationReadiness()
    results = r.check(False, False, True, True, True)
    assert not results[0].passed
    assert not results[1].passed


def test_readiness_overall():
    r = ActivationReadiness()
    results = r.check(True, True, True, True, True)
    assert r.overall(results) == 1.0
    assert r.overall([]) == 0.0


def test_readiness_all_checks():
    r = ActivationReadiness()
    chk = r.all_checks()
    assert len(chk) == 5


# --- ActivationReport ---

def test_report_builder():
    v = ActivationValidator()
    draft = _draft()
    c = ActivationConstraints()
    r = ActivationReadiness()
    builder = ActivationReportBuilder()

    val = v.validate(draft, _candidates())
    constraints = c.check_all("normal", draft.candidates, _candidates())
    readiness = r.check(True, True, True, True, True)
    report = builder.build("rep_01", val, constraints, readiness)
    assert report.report_id == "rep_01"
    assert report.valid
    assert report.ready_score == 1.0


def test_report_builder_fail():
    builder = ActivationReportBuilder()
    draft = ActivationDraft(draft_id="", context_id="", candidates=0)
    v = ActivationValidator()
    val = v.validate(draft, [])
    c = ActivationConstraints()
    constraints = c.check_all("normal", 0, [])
    r = ActivationReadiness()
    readiness = r.check(False, False, False, False, False)
    report = builder.build("rep_fail", val, constraints, readiness)
    assert not report.valid


# --- ConversationValidation ---

def test_conversation_validation_queries():
    reg = ActivationRegistry()
    conv = ConversationValidation(reg)
    assert conv.query_count == 8


def test_conversation_validation_full():
    reg = ActivationRegistry()
    draft = _draft()
    for c in _candidates():
        reg.register_candidate(c)
    conv = ConversationValidation(reg)
    v = ActivationValidator()
    info = conv.query_validator_info(v)
    assert "immediate" in info["valid_types"]


def test_conversation_rules():
    reg = ActivationRegistry()
    conv = ConversationValidation(reg)
    rules = ActivationRules()
    lst = conv.query_rules_list(rules)
    assert len(lst) >= 6


# --- DashboardValidation ---

def test_dashboard_validation_cards():
    reg = ActivationRegistry()
    for c in _candidates():
        reg.register_candidate(c)
    dash = DashboardValidation(reg)
    assert dash.card_count == 5
    v = ActivationValidator()
    draft = _draft()
    rules = ActivationRules()
    cards = dash.get_cards(v, draft, rules)
    assert len(cards) == 5
    types = [c.card_type for c in cards]
    assert "validation" in types
    assert "rules" in types
    assert "constraints" in types
    assert "readiness" in types
    assert "summary" in types


# --- Runtime integration ---

def test_runtime_validation():
    rt = ActivationRuntime()
    ctx = ActivationContext("ctx_rt", 200.0, environment="normal",
                            total_candidates=3, total_goals=2)
    req = type("Req", (), {"request_id": "req_rt", "plan_id": "p1",
                           "timestamp": 200.0, "requester": "system",
                           "priority": "normal", "context_ref": None,
                           "tags": {}})()
    from sam.activation.activation_request import ActivationRequest
    req = ActivationRequest("req_rt", "p1", 200.0, "system", "normal")
    draft = rt.run(ctx, req)
    assert draft.candidates > 0

    report = rt.run_validation()
    assert isinstance(report, ActivationReport)
    assert report.report_id != ""
    assert report.ready_score >= 0.0


# --- Parametrized ---

@pytest.mark.parametrize("i", list(range(1, 71)))
def test_validator_various(i):
    v = ActivationValidator()
    draft = ActivationDraft(
        draft_id=f"d{i}" if i % 3 != 0 else "",
        context_id=f"ctx{i % 5}",
        candidates=i % 4,
        types_used=["immediate"],
        top_candidate=f"c{i}" if i % 2 == 0 else "",
    )
    cands = [ActivationCandidate(f"c{j}", f"C{j}", "immediate", 0.5 + (j * 0.1))
             for j in range(i % 4)]
    report = v.validate(draft, cands)
    assert report.draft_id == draft.draft_id
    assert report.total_errors >= 0


@pytest.mark.parametrize("i", list(range(1, 35)))
def test_constraints_various(i):
    c = ActivationConstraints()
    envs = ["normal", "busy", "idle", "emergency", "invalid!"]
    cands = [ActivationCandidate(f"c{j}", f"C{j}", "immediate", 0.1 * (j + 1))
             for j in range(i % 5)]
    results = c.check_all(envs[i % 5], len(cands), cands)
    assert len(results) == 3


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
