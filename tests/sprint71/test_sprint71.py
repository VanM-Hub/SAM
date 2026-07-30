import pytest, os, sys
from dataclasses import FrozenInstanceError
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.approval.analytics import AnalyticsMetric, AnalyticsReport
from sam.approval.analytics_engine import AnalyticsEngine

def test_frozen():
    with pytest.raises(FrozenInstanceError):
        AnalyticsMetric(name="t",value=1.0).__setattr__("name","x")

def test_engine():
    e = AnalyticsEngine()
    e.record("total",5.0);e.record("approved",3.0)
    assert len(e.report().metrics) == 2

def test_get():
    e = AnalyticsEngine()
    e.record("x",10.0)
    assert e.get("x") == 10.0
    assert e.get("y") == 0.0

def test_conversation():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().conversation_analytics.query_count == 4

def test_dashboard():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().dashboard_analytics.card_count == 1
