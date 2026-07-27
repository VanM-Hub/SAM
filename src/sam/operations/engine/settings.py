"""
Settings Engine — membaca dan menulis konfigurasi.
"""

import structlog
from pathlib import Path
from typing import Optional, List, Dict, Any

from ...experience.models.settings import (
    SettingsModel, SettingsSection, SettingsItem, SettingsCategory,
)

logger = structlog.get_logger()


class SettingsEngine:
    """Engine untuk mengelola konfigurasi SAM."""

    def __init__(self, workspace_path=None):
        if workspace_path is None:
            workspace_path = "./workspace"
        self.workspace_path = Path(workspace_path)
        self.mission_path = self.workspace_path / "mission.yaml"
        self.dos_path = self.workspace_path / "desired-state.yaml"

    def get_settings(self):
        """Get all settings."""
        sections = [
            self._get_runtime_section(),
            self._get_mission_section(),
            self._get_autonomy_section(),
            self._get_policy_section(),
            self._get_plugin_section(),
            self._get_hosting_section(),
        ]
        return SettingsModel(sections=sections)

    def _get_runtime_section(self):
        items = [
            SettingsItem(
                key="runtime.state",
                value="RUNNING",
                default="RUNNING",
                description="Current runtime state",
                category=SettingsCategory.RUNTIME,
                editable=False,
            ),
            SettingsItem(
                key="runtime.workspace",
                value=str(self.workspace_path),
                default="./workspace",
                description="Workspace path",
                category=SettingsCategory.RUNTIME,
                editable=False,
            ),
            SettingsItem(
                key="runtime.hosting",
                value="desktop",
                default="desktop",
                description="Hosting mode",
                category=SettingsCategory.RUNTIME,
                editable=True,
            ),
        ]
        return SettingsSection(
            category=SettingsCategory.RUNTIME,
            name="Runtime",
            items=items,
        )

    def _get_mission_section(self):
        mission_name = "Protect OpenClaw Runtime"
        mission_priority = "1"
        if self.mission_path.exists():
            try:
                import yaml
                with open(str(self.mission_path)) as f:
                    data = yaml.safe_load(f)
                    mission_name = data.get("name", mission_name)
                    mission_priority = str(data.get("priority", 1))
            except Exception as e:
                logger.warning("mission_load_failed", error=str(e))

        items = [
            SettingsItem(
                key="mission.name",
                value=mission_name,
                default="Protect OpenClaw Runtime",
                description="Mission name",
                category=SettingsCategory.MISSION,
                editable=True,
            ),
            SettingsItem(
                key="mission.priority",
                value=mission_priority,
                default="1",
                description="Mission priority (1-10)",
                category=SettingsCategory.MISSION,
                editable=True,
            ),
        ]
        return SettingsSection(
            category=SettingsCategory.MISSION,
            name="Mission",
            items=items,
        )

    def _get_autonomy_section(self):
        autonomy_mode = "autonomous"
        if self.dos_path.exists():
            try:
                import yaml
                with open(str(self.dos_path)) as f:
                    data = yaml.safe_load(f)
                    autonomy_mode = data.get("guardian_mode", autonomy_mode)
            except Exception:
                pass

        items = [
            SettingsItem(
                key="autonomy.mode",
                value=autonomy_mode,
                default="autonomous",
                description="Autonomy mode (autonomous, supervised, manual)",
                category=SettingsCategory.AUTONOMY,
                editable=True,
            ),
            SettingsItem(
                key="autonomy.level",
                value="3",
                default="3",
                description="Autonomy level (0-5)",
                category=SettingsCategory.AUTONOMY,
                editable=True,
            ),
        ]
        return SettingsSection(
            category=SettingsCategory.AUTONOMY,
            name="Autonomy",
            items=items,
        )

    def _get_policy_section(self):
        items = [
            SettingsItem(
                key="policy.safety",
                value="enabled",
                default="enabled",
                description="Safety policy (enabled/disabled)",
                category=SettingsCategory.POLICY,
                editable=True,
            ),
            SettingsItem(
                key="policy.auto_approve_low_risk",
                value="true",
                default="true",
                description="Auto-approve low-risk actions",
                category=SettingsCategory.POLICY,
                editable=True,
            ),
        ]
        return SettingsSection(
            category=SettingsCategory.POLICY,
            name="Policy",
            items=items,
        )

    def _get_plugin_section(self):
        items = [
            SettingsItem(
                key="plugin.enabled",
                value="true",
                default="true",
                description="Enable plugins",
                category=SettingsCategory.PLUGIN,
                editable=True,
            ),
            SettingsItem(
                key="plugin.auto_load",
                value="true",
                default="true",
                description="Auto-load plugins",
                category=SettingsCategory.PLUGIN,
                editable=True,
            ),
        ]
        return SettingsSection(
            category=SettingsCategory.PLUGIN,
            name="Plugin",
            items=items,
        )

    def _get_hosting_section(self):
        items = [
            SettingsItem(
                key="hosting.mode",
                value="desktop",
                default="desktop",
                description="Hosting mode (desktop, service, docker)",
                category=SettingsCategory.HOSTING,
                editable=False,
            ),
            SettingsItem(
                key="hosting.auto_start",
                value="false",
                default="false",
                description="Auto-start on boot",
                category=SettingsCategory.HOSTING,
                editable=True,
            ),
        ]
        return SettingsSection(
            category=SettingsCategory.HOSTING,
            name="Hosting",
            items=items,
        )

    def update_setting(self, key, value):
        """Update a setting."""
        logger.info("setting_updated", key=key, value=value)
        return True
