"""Sprint 243 — Reasoning Model.

Program B — Model Runtime Integration.
Tidak melakukan reasoning. Hanya struktur reasoning.
"""
from __future__ import annotations
import pytest

from sam.model_runtime.reasoning_model import ReasoningModel
from sam.model_runtime.reasoning_step import ReasoningStep
from sam.model_runtime.reasoning_plan import ReasoningPlan
from sam.model_runtime.reasoning_summary import ReasoningSummary
from sam.model_runtime.reasoning_preview import ReasoningPreviewEngine, ReasoningPreview
from sam.model_runtime.reasoning_validator import ReasoningValidator
from sam.model_runtime.conversation_reasoning import ConversationReasoning
from sam.model_runtime.dashboard_reasoning import DashboardReasoning


def test_reasoning_model_immutable():
    m = ReasoningModel(reasoning_id="r1", name="reasoner")
    assert m.external_calls == 0
    assert m.preview_only is True
    with pytest.raises(Exception):
        m.name = "x"


def test_reasoning_step_structure():
    s = ReasoningStep(step_index=0, kind="thought", content="think")
    assert s.as_dict()["kind"] == "thought"
    assert "no reasoning" in s.as_dict()["note"]


def test_reasoning_plan():
    p = ReasoningPlan(plan_id="p1", goal="solve", steps=[
        ReasoningStep(0, "thought", "a"),
        ReasoningStep(1, "decision", "b"),
    ])
    assert p.step_count() == 2
    assert p.external_calls == 0
    assert p.as_dict()["preview_only"] is True


def test_reasoning_summary():
    s = ReasoningSummary(summary_id="s1", goal="g", conclusion="done")
    assert s.external_calls == 0
    assert s.conclusion == "done"


def test_reasoning_preview_no_inference():
    eng = ReasoningPreviewEngine()
    pv = eng.preview("goal", planned_steps=5)
    assert isinstance(pv, ReasoningPreview)
    assert pv.planned_steps == 5
    assert pv.external_calls == 0
    assert "no reasoning" in pv.note
    plan = eng.build_plan("goal", steps=["s1", "s2"])
    assert plan.step_count() == 2
    assert plan.external_calls == 0


def test_reasoning_validator():
    v = ReasoningValidator()
    good = ReasoningPlan(plan_id="p", goal="g", steps=[ReasoningStep(0, "thought", "x")])
    assert v.validate_plan(good).valid is True
    bad = ReasoningPlan(plan_id="p", goal="", steps=[])
    assert v.validate_plan(bad).valid is False
    summ = ReasoningSummary(summary_id="s", goal="g")
    assert v.validate_summary(summ).valid is True


def test_conversation_reasoning_bridge():
    conv = ConversationReasoning()
    out = conv.plan("conv-1", "analyze")
    assert out.external_calls == 0
    assert out.plan.goal == "analyze"
    assert out.plan.external_calls == 0


def test_dashboard_reasoning_rows():
    dash = DashboardReasoning()
    p = ReasoningPlan(plan_id="p1", goal="g", steps=[ReasoningStep(0, "thought", "x")])
    dash.add(p)
    assert len(dash.rows()) == 1
    assert dash.rows()[0].steps == 1
    assert dash.summary()["external_calls"] == 0


def test_no_forbidden_imports():
    import inspect
    import sam.model_runtime.reasoning_preview as rp
    src = inspect.getsource(rp)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
