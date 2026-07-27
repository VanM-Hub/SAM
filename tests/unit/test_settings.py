"""
Unit tests for Settings Engine (OP-8).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import datetime
import pytest
from sam.experience.models.settings import (
    SettingsItem, SettingsSection, SettingsModel, SettingsCategory,
)
from sam.operations.engine.settings import SettingsEngine


# ============================================================================
# 1. SettingsCategory Enum
# ============================================================================

class TestSettingsCategory:
    def test_all_categories_exist(self):
        assert SettingsCategory.RUNTIME.value == "runtime"
        assert SettingsCategory.MISSION.value == "mission"
        assert SettingsCategory.AUTONOMY.value == "autonomy"

    def test_seven_categories(self):
        assert len(list(SettingsCategory)) == 7


# ============================================================================
# 2. SettingsItem
# ============================================================================

class TestSettingsItem:
    def test_minimal_item(self):
        item = SettingsItem(
            key="test.key",
            value="test_value",
            category=SettingsCategory.RUNTIME,
        )
        assert item.key == "test.key"
        assert item.editable is True
        assert item.sensitive is False

    def test_full_item(self):
        item = SettingsItem(
            key="secret.key",
            value="api_key_123",
            default=None,
            description="API key",
            category=SettingsCategory.POLICY,
            editable=False,
            sensitive=True,
        )
        assert item.editable is False
        assert item.sensitive is True

    def test_numeric_value(self):
        item = SettingsItem(
            key="number", value=42, category=SettingsCategory.RUNTIME,
        )
        assert item.value == 42

    def test_bool_value(self):
        item = SettingsItem(
            key="flag", value=True, category=SettingsCategory.POLICY,
        )
        assert item.value is True


# ============================================================================
# 3. SettingsSection
# ============================================================================

class TestSettingsSection:
    def test_section(self):
        item = SettingsItem(key="k", value="v", category=SettingsCategory.RUNTIME)
        section = SettingsSection(
            category=SettingsCategory.RUNTIME,
            name="Runtime",
            items=[item],
        )
        assert section.category == SettingsCategory.RUNTIME
        assert len(section.items) == 1


# ============================================================================
# 4. SettingsModel
# ============================================================================

class TestSettingsModel:
    def test_minimal_model(self):
        model = SettingsModel(sections=[])
        assert len(model.sections) == 0

    def test_model_with_sections(self):
        item = SettingsItem(key="k", value="v", category=SettingsCategory.RUNTIME)
        section = SettingsSection(category=SettingsCategory.RUNTIME, name="R", items=[item])
        model = SettingsModel(sections=[section])
        assert len(model.sections) == 1

    def test_model_is_frozen(self):
        model = SettingsModel(sections=[])
        with pytest.raises((TypeError, Exception)):
            model.sections = []


# ============================================================================
# 5. SettingsEngine
# ============================================================================

class TestSettingsEngine:
    def test_get_settings_returns_model(self):
        engine = SettingsEngine(workspace_path="/tmp/nonexistent")
        model = engine.get_settings()
        assert isinstance(model, SettingsModel)
        assert len(model.sections) > 0

    def test_runtime_section_exists(self):
        engine = SettingsEngine()
        model = engine.get_settings()
        sections = {s.category.value: s for s in model.sections}
        assert "runtime" in sections

    def test_mission_section_exists(self):
        engine = SettingsEngine()
        model = engine.get_settings()
        sections = {s.category.value: s for s in model.sections}
        assert "mission" in sections

    def test_autonomy_section_exists(self):
        engine = SettingsEngine()
        model = engine.get_settings()
        sections = {s.category.value: s for s in model.sections}
        assert "autonomy" in sections

    def test_policy_section_exists(self):
        engine = SettingsEngine()
        model = engine.get_settings()
        sections = {s.category.value: s for s in model.sections}
        assert "policy" in sections

    def test_plugin_section_exists(self):
        engine = SettingsEngine()
        model = engine.get_settings()
        sections = {s.category.value: s for s in model.sections}
        assert "plugin" in sections

    def test_hosting_section_exists(self):
        engine = SettingsEngine()
        model = engine.get_settings()
        sections = {s.category.value: s for s in model.sections}
        assert "hosting" in sections

    def test_runtime_state_not_editable(self):
        engine = SettingsEngine()
        model = engine.get_settings()
        for section in model.sections:
            if section.category == SettingsCategory.RUNTIME:
                for item in section.items:
                    if item.key == "runtime.state":
                        assert item.editable is False

    def test_mission_name_editable(self):
        engine = SettingsEngine()
        model = engine.get_settings()
        for section in model.sections:
            if section.category == SettingsCategory.MISSION:
                for item in section.items:
                    if item.key == "mission.name":
                        assert item.editable is True

    def test_update_setting_returns_true(self):
        engine = SettingsEngine()
        result = engine.update_setting("test.key", "test_value")
        assert result is True
