import pytest, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from sam.approval.runtime_v1 import ApprovalRuntimeV1
from sam.approval.intake_record import ApprovalIntakeRecord

def test_runtime_init():
    rt = ApprovalRuntimeV1()
    s = rt.get_status()
    assert s["version"] == "6.11.0"

def test_runtime_process():
    rt = ApprovalRuntimeV1()
    r = ApprovalIntakeRecord(record_id="r1",timestamp=100.0,decision_record_id="d1",
                              pipeline_version="5.20.0",readiness_score=0.9,certified=True)
    assert rt.process(r).success is True

def test_runtime_invalid():
    rt = ApprovalRuntimeV1()
    r = ApprovalIntakeRecord(record_id="",timestamp=0.0,decision_record_id="",
                              pipeline_version="",readiness_score=-1.0)
    assert rt.process(r).success is False

def test_runtime_bulk():
    rt = ApprovalRuntimeV1()
    count = 20
    for i in range(count):
        rt.process(ApprovalIntakeRecord(record_id=f"r{i}",timestamp=float(i+1),
            decision_record_id=f"d{i}",pipeline_version="5.20.0",readiness_score=0.7))
    s = rt.get_status()
    assert s["intake_count"] == count
    assert s["workflow_count"] == count
    assert s["audit_entries"] >= count

def test_all_bridges():
    rt = ApprovalRuntimeV1()
    assert rt.conversation_intake.query_count == 10
    assert rt.conversation_workflow.query_count == 10
    assert rt.conversation_policy.query_count == 10
    assert rt.conversation_multilevel.query_count == 10
    assert rt.conversation_delegation.query_count == 6
    assert rt.conversation_audit.query_count == 6
    assert rt.conversation_history.query_count == 6
    assert rt.conversation_analytics.query_count == 4

def test_all_dashboards():
    rt = ApprovalRuntimeV1()
    assert rt.dashboard_intake.card_count == 6
    assert rt.dashboard_workflow.card_count == 6
    assert rt.dashboard_policy.card_count == 3
    assert rt.dashboard_multilevel.card_count == 2
    assert rt.dashboard_delegation.card_count == 1
    assert rt.dashboard_audit.card_count == 1
    assert rt.dashboard_history.card_count == 1
    assert rt.dashboard_analytics.card_count == 1
