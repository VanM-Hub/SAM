import pytest, os, sys
from dataclasses import FrozenInstanceError
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.approval.workflow import ApprovalWorkflow, WorkflowPhase, WorkflowTransition, PHASE_TRANSITIONS
from sam.approval.workflow_engine import WorkflowEngine, WorkflowTransitionError
from sam.approval.workflow_builder import WorkflowBuilder
from sam.approval.workflow_rules import WorkflowRules
from sam.approval.intake_normalizer import NormalizedApprovalRecord
from sam.approval.runtime_v1 import ApprovalRuntimeV1, ApprovalRuntimeResult
from sam.approval.intake_record import ApprovalIntakeRecord

# --- DTO frozen ---
def test_workflow_frozen():
    w = ApprovalWorkflow(workflow_id="w1")
    with pytest.raises(FrozenInstanceError):
        w.workflow_id = "x"

def test_transition_frozen():
    t = WorkflowTransition()
    with pytest.raises(FrozenInstanceError):
        t.reason = "x"

# --- Phase transitions ---
def test_valid_transitions():
    assert WorkflowPhase.PENDING in PHASE_TRANSITIONS
    assert WorkflowPhase.IN_REVIEW in PHASE_TRANSITIONS[WorkflowPhase.PENDING]
    assert WorkflowPhase.CANCELLED in PHASE_TRANSITIONS[WorkflowPhase.PENDING]

def test_terminal_phases():
    assert WorkflowRules.is_terminal(WorkflowPhase.COMPLETED)
    assert WorkflowRules.is_terminal(WorkflowPhase.REJECTED)
    assert WorkflowRules.is_terminal(WorkflowPhase.CANCELLED)
    assert not WorkflowRules.is_terminal(WorkflowPhase.PENDING)

def test_active_phases():
    assert WorkflowRules.is_active(WorkflowPhase.PENDING)
    assert WorkflowRules.is_active(WorkflowPhase.IN_REVIEW)
    assert not WorkflowRules.is_active(WorkflowPhase.REJECTED)
    assert not WorkflowRules.is_active(WorkflowPhase.CANCELLED)

# --- WorkflowEngine ---
def test_engine_init():
    assert WorkflowEngine() is not None

def test_engine_create():
    e = WorkflowEngine()
    w = e.create("w1", "n1")
    assert w.workflow_id == "w1"
    assert e.workflow_count == 1

def test_engine_get():
    e = WorkflowEngine()
    e.create("w1", "n1")
    assert e.get("w1") is not None
    assert e.get("nonexistent") is None

def test_can_transition():
    e = WorkflowEngine()
    w = e.create("w1", "n1")
    assert e.can_transition(w, WorkflowPhase.IN_REVIEW) is True
    assert e.can_transition(w, WorkflowPhase.COMPLETED) is False

def test_transition():
    e = WorkflowEngine()
    e.create("w1", "n1")
    w = e.transition("w1", WorkflowPhase.IN_REVIEW, "start review")
    assert w.phase == WorkflowPhase.IN_REVIEW
    assert len(w.history) == 1

def test_transition_error_nonexistent():
    e = WorkflowEngine()
    with pytest.raises(WorkflowTransitionError):
        e.transition("nonexistent", WorkflowPhase.IN_REVIEW)

def test_transition_error_invalid():
    e = WorkflowEngine()
    e.create("w1", "n1")
    with pytest.raises(WorkflowTransitionError):
        e.transition("w1", WorkflowPhase.COMPLETED)  # PENDING can't go to COMPLETED

def test_full_lifecycle():
    e = WorkflowEngine()
    e.create("w1", "n1")
    e.transition("w1", WorkflowPhase.IN_REVIEW, "review")
    e.transition("w1", WorkflowPhase.AWAITING_APPROVAL, "ready")
    e.transition("w1", WorkflowPhase.APPROVED, "approved")
    e.transition("w1", WorkflowPhase.COMPLETED, "done")
    w = e.get("w1")
    assert w.phase == WorkflowPhase.COMPLETED
    assert len(w.history) == 4

def test_reject_flow():
    e = WorkflowEngine()
    e.create("w1", "n1")
    e.transition("w1", WorkflowPhase.IN_REVIEW, "review")
    e.transition("w1", WorkflowPhase.REJECTED, "rejected")
    w = e.get("w1")
    assert w.phase == WorkflowPhase.REJECTED

# --- WorkflowBuilder ---
def test_builder_init():
    e = WorkflowEngine()
    b = WorkflowBuilder(e)
    assert b is not None

def test_builder_build():
    e = WorkflowEngine()
    b = WorkflowBuilder(e)
    n = NormalizedApprovalRecord(normalized_id="norm_r1", category="manual")
    w = b.build(n)
    assert w.normalized_id == "norm_r1"
    assert w.phase == WorkflowPhase.PENDING

# --- Integration with Runtime ---
def test_runtime_with_workflow():
    rt = ApprovalRuntimeV1()
    from sam.approval.intake_record import ApprovalIntakeRecord
    r = ApprovalIntakeRecord(record_id="r1", timestamp=100.0, decision_record_id="d1",
                              pipeline_version="5.20.0", readiness_score=0.9, certified=True)
    result = rt.process(r)
    assert result.success is True
    assert result.workflow is not None
    assert result.workflow.phase == WorkflowPhase.PENDING

def test_runtime_workflow_counts():
    rt = ApprovalRuntimeV1()
    for i in range(5):
        r = ApprovalIntakeRecord(record_id=f"r{i}", timestamp=float(i+1), decision_record_id=f"d{i}",
                                  pipeline_version="5.20.0", readiness_score=0.8)
        rt.process(r)
    status = rt.get_status()
    assert status["workflow_count"] == 5
    assert status["intake_count"] == 5

# --- Conversation ---
def test_conversation_workflow_query_count():
    rt = ApprovalRuntimeV1()
    assert rt.conversation_workflow.query_count == 10

def test_conversation_active():
    rt = ApprovalRuntimeV1()
    from sam.approval.intake_record import ApprovalIntakeRecord
    r = ApprovalIntakeRecord(record_id="r1", timestamp=1.0, decision_record_id="d1",
                              pipeline_version="5.20.0", readiness_score=0.8)
    rt.process(r)
    result = rt.conversation_workflow.active_workflows()
    assert result["count"] == 1

def test_conversation_phase_summary():
    rt = ApprovalRuntimeV1()
    for i in range(3):
        r = ApprovalIntakeRecord(record_id=f"r{i}", timestamp=float(i+1), decision_record_id=f"d{i}",
                                  pipeline_version="5.20.0", readiness_score=0.8)
        rt.process(r)
    s = rt.conversation_workflow.phase_summary()
    assert s["total"] == 3
    assert s["phases"]["PENDING"] == 3

# --- Dashboard ---
def test_dashboard_workflow_card_count():
    rt = ApprovalRuntimeV1()
    assert rt.dashboard_workflow.card_count == 6

def test_dashboard_engine_card():
    rt = ApprovalRuntimeV1()
    card = rt.dashboard_workflow.get_engine_card()
    assert card.has_workflows is False

def test_dashboard_distribution():
    rt = ApprovalRuntimeV1()
    from sam.approval.intake_record import ApprovalIntakeRecord
    for i in range(3):
        rt.process(ApprovalIntakeRecord(record_id=f"r{i}", timestamp=float(i+1), decision_record_id=f"d{i}",
                                          pipeline_version="5.20.0", readiness_score=0.8))
    card = rt.dashboard_workflow.get_distribution_card()
    assert card.total == 3

# --- Forbidden imports ---
def test_forbidden():
    dp = os.path.join("src", "sam", "approval")
    for pat in ["import threading", "import asyncio", "async def", "await ", "import socket"]:
        for fn in ["workflow.py","workflow_engine.py","workflow_builder.py",
                    "workflow_rules.py","conversation_workflow.py","dashboard_workflow.py"]:
            p = os.path.join(dp, fn)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    assert pat not in f.read(), f"{pat} in {fn}"

def test_no_async():
    dp = os.path.join("src", "sam", "approval")
    for fn in ["workflow.py","workflow_engine.py","workflow_builder.py",
                "workflow_rules.py","conversation_workflow.py","dashboard_workflow.py"]:
        p = os.path.join(dp, fn)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                t = f.read()
                assert "async def" not in t
                assert "await " not in t

# --- Deterministic ---
@pytest.mark.parametrize("i", range(100))
def test_deterministic_workflow(i):
    e = WorkflowEngine()
    e.create(f"w{i}", f"n{i}", owner="test")
    t = e.transition(f"w{i}", WorkflowPhase.IN_REVIEW, "auto")
    assert t.phase == WorkflowPhase.IN_REVIEW
