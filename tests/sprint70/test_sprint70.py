import pytest, os, sys
from dataclasses import FrozenInstanceError
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.approval.history import HistoryEntry, ApprovalHistory
from sam.approval.history_engine import HistoryEngine

def test_frozen():
    with pytest.raises(FrozenInstanceError):
        HistoryEntry(entry_id="h1").__setattr__("entry_id","x")

def test_engine():
    e = HistoryEngine()
    assert e.entry_count == 0

def test_record():
    e = HistoryEngine()
    e.record("a1","PENDING","system")
    assert e.entry_count == 1

def test_get_history():
    e = HistoryEngine()
    e.record("a1","PENDING","sys");e.record("a2","APPROVED","sys")
    h = e.get_history("a1")
    assert len(h.entries) == 1

def test_get_all():
    e = HistoryEngine()
    e.record("a1","PENDING","sys");e.record("a2","APPROVED","sys")
    assert len(e.get_all().entries) == 2

def test_conversation():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().conversation_history.query_count == 6

def test_dashboard():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().dashboard_history.card_count == 1
