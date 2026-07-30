import pytest, os, sys
from dataclasses import FrozenInstanceError
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.approval.dashboard import DashboardWidget, DashboardLayout
from sam.approval.dashboard_engine import ApprovalDashboardEngine

def test_frozen():
    with pytest.raises(FrozenInstanceError):
        DashboardWidget(widget_id="w1").__setattr__("widget_id","x")

def test_engine():
    e = ApprovalDashboardEngine()
    assert e.layout_count >= 1

def test_get_layout():
    e = ApprovalDashboardEngine()
    assert e.get_layout("default") is not None
    assert e.get_layout("nonexistent") is None

def test_list():
    e = ApprovalDashboardEngine()
    assert len(e.list_layouts()) >= 1
