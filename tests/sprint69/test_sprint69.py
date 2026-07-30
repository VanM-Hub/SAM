import pytest, os, sys
from dataclasses import FrozenInstanceError
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.approval.audit import AuditEntry, AuditLog
from sam.approval.audit_engine import AuditEngine

def test_frozen():
    with pytest.raises(FrozenInstanceError):
        AuditEntry(entry_id="a1").__setattr__("entry_id","x")

def test_engine():
    e = AuditEngine()
    assert e.entry_count == 0

def test_log():
    e = AuditEngine()
    e.log("test","system","t1")
    assert e.entry_count == 1

def test_filter_action():
    e = AuditEngine()
    e.log("a","u1","t1");e.log("b","u1","t2");e.log("a","u2","t3")
    assert len(e.filter_by_action("a")) == 2

def test_filter_actor():
    e = AuditEngine()
    e.log("a","u1","t1");e.log("b","u1","t2")
    assert len(e.filter_by_actor("u1")) == 2

def test_conversation():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().conversation_audit.query_count == 6

def test_dashboard():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().dashboard_audit.card_count == 1
