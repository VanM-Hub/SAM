import pytest, os, sys
from dataclasses import FrozenInstanceError
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.approval.delegation import DelegationRule
from sam.approval.delegation_engine import DelegationEngine

def test_frozen():
    with pytest.raises(FrozenInstanceError):
        DelegationRule(rule_id="d1").__setattr__("rule_id","x")

def test_engine():
    e = DelegationEngine()
    assert e.rule_count == 0

def test_add():
    e = DelegationEngine()
    e.add(DelegationRule(rule_id="d1",from_user="alice",to_user="bob"))
    assert e.rule_count == 1

def test_resolve():
    e = DelegationEngine()
    e.add(DelegationRule(rule_id="d1",from_user="alice",to_user="bob"))
    assert e.resolve("alice") == "bob"
    assert e.resolve("carol") == "carol"

def test_deactivate():
    e = DelegationEngine()
    e.add(DelegationRule(rule_id="d1",from_user="alice",to_user="bob"))
    e.deactivate("d1")
    assert len(e.list_active()) == 0

def test_conversation():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().conversation_delegation.query_count == 6

def test_dashboard():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().dashboard_delegation.card_count == 1
