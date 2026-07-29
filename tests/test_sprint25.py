import ast
import os
import inspect
import pytest
from dataclasses import FrozenInstanceError

BASE = os.path.join(os.path.dirname(__file__), "..", "src", "sam", "operations", "brain", "decision")
BASE = os.path.abspath(BASE)

FILES = [
    os.path.join(BASE, f)
    for f in os.listdir(BASE)
    if f.endswith(".py")
]


def test_no_domain_imports():
    """0 domain import: files must not import 'sam' top-level modules."""
    for path in FILES:
        with open(path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("sam."), f"Domain import found in {path}: from {mod}"
            if isinstance(node, ast.Import):
                for n in node.names:
                    assert not n.name.startswith("sam."), f"Domain import found in {path}: import {n.name}"


def test_no_repository_imports():
    """0 repository import: files must not import modules containing 'repo' or 'storage'."""
    forbid = ("repo", "storage", "database")
    for path in FILES:
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        for token in forbid:
            assert token not in src.lower(), f"Repository/storage token '{token}' found in {path}"


def test_no_provider_calls_in_code():
    """0 provider call. Reject occurrences of the word 'provider' in source (decision layer must be provider-agnostic)."""
    for path in FILES:
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        assert "provider" not in src.lower(), f"Provider token found in {path}"


def test_no_top_level_execution():
    """0 auto execution: no top-level Call expressions or if __name__ == '__main__'."""
    for path in FILES:
        with open(path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        for node in tree.body:
            # disallow top-level calls like foo()
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                pytest.fail(f"Top-level call expression found in {path}")
            # disallow if __name__ == '__main__'
            if isinstance(node, ast.If):
                src = ast.get_source_segment(open(path, "r", encoding="utf-8").read(), node)
                if src and "__name__" in src and "__main__" in src:
                    pytest.fail(f"Top-level __main__ execution found in {path}")


def test_dataclasses_immutable_and_package_is_frozen():
    """Check DecisionPackage, ApprovalRequestDTO, DecisionAlternative, DecisionEvaluation frozen dataclasses where applicable."""
    # import via package
    from sam.operations.brain.decision import (
        DecisionPackage,
        ApprovalRequestDTO,
        DecisionAlternative,
        DecisionEvaluation,
    )

    # DecisionPackage should be frozen
    pkg = DecisionPackage(
        package_id="p-1",
        operator_question="Q",
        session_id="s-1",
        summary="sum",
        findings=("f1",),
        evidence_summary="ev",
        alternatives=(),
        selected_alternative="do_nothing",
        recommendation="rec",
        requires_approval=False,
        estimated_impact="low",
        estimated_confidence=0.5,
        risk_summary="low",
        evaluation_score=0.5,
        next_steps=("step1",),
        created_at="now",
    )
    with pytest.raises(FrozenInstanceError):
        pkg.summary = "changed"

    # ApprovalRequestDTO frozen
    ar = ApprovalRequestDTO(
        package_id="p-1",
        title="t",
        description="d",
        alternative_name="a",
        risk_level="low",
        impact="low",
        confidence=0.5,
        evidence_count=1,
        evidence_ids=("e1",),
        recommendation="r",
        requires_approval=False,
        prepared_at="now",
    )
    with pytest.raises(FrozenInstanceError):
        ar.title = "changed"

    # DecisionAlternative frozen
    alt = DecisionAlternative(
        name="n",
        label="L",
        description="d",
        evidence_basis=("e1",),
        estimated_impact="low",
        estimated_confidence=0.5,
        risk_level="low",
    )
    with pytest.raises(FrozenInstanceError):
        alt.label = "x"

    # DecisionEvaluation frozen
    de = DecisionEvaluation(
        score=0.5,
        confidence=0.5,
        evidence_coverage=0.5,
        operational_impact="low",
        urgency="low",
        reversibility="reversible",
        risk_level="low",
        recommendation_quality=0.5,
    )
    with pytest.raises(FrozenInstanceError):
        de.score = 0.7


def test_alternatives_minimum_and_evidence_flow():
    """Functional smoke test covering generation pipeline with evidence present."""
    from sam.operations.brain.decision import (
        DecisionContextBuilder,
        DecisionEvaluator,
        AlternativeGenerator,
        DecisionPackageBuilder,
        ApprovalRequestBuilder,
        DecisionConversation,
        DecisionDashboardService,
        EvidenceItem,
        EvidenceSet,
    )

    # Build context with evidence ids
    builder = DecisionContextBuilder()
    ctx = builder.build(
        operator_question="Why is service failing?",
        observation=None,
        findings=None,
        recommendation=None,
        mission=None,
        timeline=None,
        trust=None,
        health=None,
        active_approvals=None,
        current_session=None,
        evidence_ids=("e-1", "e-2"),
    )

    # Prepare evidence set
    ev1 = EvidenceItem(evidence_id="e-1", content="log1", source="sys", relevance=0.9)
    ev2 = EvidenceItem(evidence_id="e-2", content="metric spike", source="monitor", relevance=0.8)
    evset = EvidenceSet(items=(ev1, ev2), total_items=2, average_relevance=0.85)

    # Evaluate
    evaluator = DecisionEvaluator()
    eval_res = evaluator.evaluate(
        response=None,
        evidence_set=evset,
        context=ctx,
        reasoning_confidence=0.6,
        reasoning_evidence_ids=("e-1", "e-2"),
        supported_claims=2,
        total_claims=2,
        recommendation_summary="Restart service",
    )

    # Generate alternatives
    gen = AlternativeGenerator()
    alts = gen.generate(ctx, eval_res, evidence_ids=ctx.evidence_ids)
    assert len(alts) >= 4
    names = [a.name for a in alts]
    for expected in ("do_nothing", "recommended", "conservative", "aggressive"):
        assert expected in names

    # Build package
    pkg_builder = DecisionPackageBuilder()
    pkg = pkg_builder.build(
        operator_question=ctx.operator_question,
        session_id="s-1",
        context=ctx,
        evaluation=eval_res,
        alternatives=alts,
        selected_alternative="recommended",
        evidence_summary="Based on logs and metrics",
        findings=("f1", "f2"),
    )

    # Approval prepare
    arb = ApprovalRequestBuilder()
    ar = arb.build(pkg)
    assert isinstance(ar.evidence_ids, tuple)
    assert ar.evidence_count >= 1

    # Conversation read-only
    conv = DecisionConversation(pkg)
    before = pkg.to_dict()
    r = conv.explain_decision()
    assert hasattr(r, "answer")
    after = pkg.to_dict()
    assert before == after

    # Dashboard read-only
    dash = DecisionDashboardService(session=None, package=pkg, approval_request=ar)
    db = dash.get_dashboard()
    assert db.package_id == pkg.package_id
