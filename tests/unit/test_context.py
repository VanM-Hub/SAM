"""
Unit tests for ContextEngine (OP-3).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from sam.operations.engine.context import ContextEngine, RuntimeContext


class TestRuntimeContext:
    def test_context_is_frozen_dataclass(self):
        """RuntimeContext is frozen."""
        ctx = RuntimeContext(
            mission_name="Test",
            workspace="default",
            cluster=None,
            operator=None,
            mode="production"
        )
        with pytest.raises((TypeError, Exception)):
            ctx.mission_name = "Changed"

    def test_context_has_all_fields(self):
        """RuntimeContext has all required fields."""
        ctx = RuntimeContext(
            mission_name="Protect",
            workspace="dev",
            cluster="cluster-1",
            operator="Van",
            mode="development"
        )
        assert ctx.mission_name == "Protect"
        assert ctx.workspace == "dev"
        assert ctx.cluster == "cluster-1"
        assert ctx.operator == "Van"
        assert ctx.mode == "development"


class TestContextEngine:
    def test_default_context(self):
        """Default context has expected values."""
        engine = ContextEngine()
        ctx = engine.get_context()
        assert ctx.mission_name == "Protect OpenClaw Runtime"
        assert ctx.workspace == "default"
        assert ctx.cluster is None
        assert ctx.operator is None
        assert ctx.mode == "production"

    def test_update_mission(self):
        """update_mission changes mission name."""
        engine = ContextEngine()
        engine.update_mission("New Mission")
        ctx = engine.get_context()
        assert ctx.mission_name == "New Mission"

    def test_update_mission_preserves_other_fields(self):
        """update_mission keeps workspace, cluster, operator, mode."""
        engine = ContextEngine()
        engine.update_mission("New Mission")
        ctx = engine.get_context()
        assert ctx.mission_name == "New Mission"
        assert ctx.workspace == "default"
        assert ctx.cluster is None
        assert ctx.operator is None
        assert ctx.mode == "production"

    def test_update_operator(self):
        """update_operator changes operator name."""
        engine = ContextEngine()
        engine.update_operator("Van")
        ctx = engine.get_context()
        assert ctx.operator == "Van"
        assert ctx.mission_name == "Protect OpenClaw Runtime"

    def test_to_dict(self):
        """to_dict() returns correct dict."""
        engine = ContextEngine()
        d = engine.to_dict()
        assert d["mission_name"] == "Protect OpenClaw Runtime"
        assert d["workspace"] == "default"
        assert d["cluster"] is None
        assert d["operator"] is None
        assert d["mode"] == "production"

    def test_update_operator_then_mission(self):
        """Multiple updates work sequentially."""
        engine = ContextEngine()
        engine.update_operator("Van")
        engine.update_mission("Mission Alpha")
        ctx = engine.get_context()
        assert ctx.operator == "Van"
        assert ctx.mission_name == "Mission Alpha"

    def test_multiple_contexts_isolated(self):
        """Different engines don't share state."""
        e1 = ContextEngine()
        e2 = ContextEngine()
        e1.update_operator("Van")
        assert e2.get_context().operator is None

    def test_update_mission_empty_string(self):
        """update_mission with empty string."""
        engine = ContextEngine()
        engine.update_mission("")
        assert engine.get_context().mission_name == ""
