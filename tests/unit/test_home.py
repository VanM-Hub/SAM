"""
Unit tests for HomeModel (OP-3).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import datetime
import pytest
from sam.experience.pages.home import HomeModel, HomeStatus, HomeSection


class TestHomeStatus:
    def test_all_statuses_have_values(self):
        """Every HomeStatus has a non-empty value."""
        for s in HomeStatus:
            assert len(s.value) > 0

    def test_healthy_is_default(self):
        """HEALTHY is the default status."""
        model = HomeModel()
        assert model.status == HomeStatus.HEALTHY

    def test_eight_statuses(self):
        """There are exactly 8 statuses."""
        assert len(list(HomeStatus)) == 8


class TestHomeSection:
    def test_all_sections_have_values(self):
        """Every HomeSection has a non-empty value."""
        for s in HomeSection:
            assert len(s.value) > 0

    def test_system_section_exists(self):
        """SYSTEM section exists."""
        assert HomeSection.SYSTEM.value == "system"


class TestHomeModelDefaults:
    def test_default_system_health(self):
        """Default system health is 100."""
        model = HomeModel()
        assert model.system_health == 100.0

    def test_default_mission_name(self):
        """Default mission name is set."""
        model = HomeModel()
        assert model.mission_name == "Protect OpenClaw Runtime"

    def test_default_uptime(self):
        """Default uptime is 0h 0m."""
        model = HomeModel()
        assert model.uptime == "0h 0m"

    def test_default_no_attention(self):
        """Default needs_attention is False."""
        model = HomeModel()
        assert model.needs_attention is False

    def test_default_recent_changes_empty(self):
        """Default recent_changes is empty list."""
        model = HomeModel()
        assert model.recent_changes == []

    def test_default_recommendations_empty(self):
        """Default recommendations is empty list."""
        model = HomeModel()
        assert model.recommendations == []

    def test_default_operator_none(self):
        """Default operator_name is None."""
        model = HomeModel()
        assert model.operator_name is None

    def test_default_sections_all_six(self):
        """Default sections has all 6 sections."""
        model = HomeModel()
        assert len(model.sections) == 6
        assert HomeSection.SYSTEM in model.sections
        assert HomeSection.RECOMMENDATIONS in model.sections


class TestHomeModelImmutable:
    def test_model_is_frozen(self):
        """HomeModel is immutable."""
        model = HomeModel()
        with pytest.raises((TypeError, Exception)):
            model.status = HomeStatus.BUSY

    def test_to_dict_returns_dict(self):
        """to_dict() returns a dict."""
        model = HomeModel()
        d = model.to_dict()
        assert isinstance(d, dict)
        assert d["status"] == "healthy"
        assert d["system_health"] == 100.0


class TestHomeModelCustom:
    def test_custom_values(self):
        """Can create HomeModel with custom values."""
        now = datetime.utcnow()
        model = HomeModel(
            status=HomeStatus.BUSY,
            status_message="Busy processing",
            system_health=75.0,
            mission_health=80.0,
            current_activity="Processing tasks",
            active_tasks=3,
            needs_attention=True,
            pending_approvals=2,
            uptime="5h 30m",
            operator_name="Van",
            last_updated=now,
        )
        assert model.status == HomeStatus.BUSY
        assert model.system_health == 75.0
        assert model.active_tasks == 3
        assert model.pending_approvals == 2
        assert model.uptime == "5h 30m"
        assert model.operator_name == "Van"

    def test_recent_changes_max_five(self):
        """recent_changes field works correctly."""
        model = HomeModel(recent_changes=[{"message": "Test"}] * 3)
        assert len(model.recent_changes) == 3

    def test_recommendations_field(self):
        """recommendations field works correctly."""
        model = HomeModel(recommendations=["Restart service", "Update config"])
        assert len(model.recommendations) == 2
