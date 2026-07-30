import pytest, os, sys
from dataclasses import FrozenInstanceError
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.approval.multilevel import ApprovalLevel, MultiLevelApproval
from sam.approval.multilevel_engine import MultiLevelEngine
from sam.approval.multilevel_builder import MultiLevelBuilder
from sam.approval.multilevel_validator import MultiLevelValidator

def test_multilevel_frozen():
    with pytest.raises(FrozenInstanceError):
        ApprovalLevel(level_id="L1").__setattr__("level_id","x")

def test_engine_create():
    e = MultiLevelEngine()
    e.create("a1","w1",[ApprovalLevel(level_id="L1",order=0,required_approvers=1)])
    assert e.approval_count == 1

def test_current_level():
    e = MultiLevelEngine()
    e.create("a1","w1",[ApprovalLevel(level_id="L1",order=0),ApprovalLevel(level_id="L2",order=1)])
    assert e.current_level("a1").level_id == "L1"

def test_advance():
    e = MultiLevelEngine()
    e.create("a1","w1",[ApprovalLevel(level_id="L1",order=0),ApprovalLevel(level_id="L2",order=1)])
    m = e.advance_level("a1")
    assert m.current_level_index == 1
    m2 = e.advance_level("a1")
    assert m2.completed is True

def test_status():
    e = MultiLevelEngine()
    e.create("a1","w1",[ApprovalLevel(level_id="L1",order=0)])
    s = e.get_status("a1")
    assert s is not None and len(s) == 1

def test_builder():
    e = MultiLevelEngine()
    m = MultiLevelBuilder.build_default("a1","w1",e)
    assert len(m.levels) == 3

def test_validator_valid():
    l = [ApprovalLevel(level_id="L1",order=0,required_approvers=1),ApprovalLevel(level_id="L2",order=1,required_approvers=1)]
    v, errs = MultiLevelValidator.validate(MultiLevelApproval(approval_id="a1",workflow_id="w1",levels=l))
    assert v is True

def test_validator_invalid():
    v, errs = MultiLevelValidator.validate(MultiLevelApproval(approval_id="",workflow_id="",levels=[]))
    assert v is False

def test_conversation():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().conversation_multilevel.query_count == 10

def test_dashboard():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().dashboard_multilevel.card_count == 2
